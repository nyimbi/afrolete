import hmac
import time
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.billing import (
    BillingEntitlement,
    BillingPlan,
    SaaSInvoice,
    SaaSPayment,
    TenantSubscription,
    UsageMeter,
    UsageRecord,
)
from app.models.enums import BillingInvoiceStatus, SubscriptionStatus
from app.models.organization import Organization
from app.schemas.billing import (
    BillingEntitlementCreate,
    BillingPaymentWebhookCreate,
    BillingPlanCreate,
    SaaSInvoiceCreate,
    SaaSPaymentCreate,
    SubscriptionCreate,
    UsageMeterCreate,
    UsageRecordCreate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService


async def ensure_manage_billing(
    authz: AuthorizationService,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> None:
    allowed = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def create_plan(db: AsyncSession, payload: BillingPlanCreate) -> BillingPlan:
    plan = BillingPlan(**payload.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def list_plans(db: AsyncSession) -> list[BillingPlan]:
    return list((await db.scalars(select(BillingPlan).order_by(BillingPlan.base_price, BillingPlan.name))).all())


async def create_subscription(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SubscriptionCreate,
    authz: AuthorizationService,
) -> TenantSubscription:
    await get_organization(db, payload.organization_id)
    await ensure_manage_billing(authz, identity, payload.organization_id)
    await get_plan(db, payload.billing_plan_id)
    subscription = TenantSubscription(status=SubscriptionStatus.ACTIVE, **payload.model_dump())
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription


async def list_subscriptions(db: AsyncSession, organization_id: UUID) -> list[TenantSubscription]:
    return list(
        (
            await db.scalars(
                select(TenantSubscription)
                .where(TenantSubscription.organization_id == organization_id)
                .order_by(TenantSubscription.created_at.desc())
            )
        ).all()
    )


async def create_usage_meter(db: AsyncSession, payload: UsageMeterCreate) -> UsageMeter:
    meter = UsageMeter(**payload.model_dump())
    db.add(meter)
    await db.commit()
    await db.refresh(meter)
    return meter


async def list_usage_meters(db: AsyncSession) -> list[UsageMeter]:
    return list((await db.scalars(select(UsageMeter).order_by(UsageMeter.name))).all())


async def record_usage(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: UsageRecordCreate,
    authz: AuthorizationService,
) -> UsageRecord:
    await ensure_manage_billing(authz, identity, payload.organization_id)
    await get_subscription_for_organization(db, payload.subscription_id, payload.organization_id)
    await get_usage_meter(db, payload.usage_meter_id)
    record = UsageRecord(recorded_at=datetime.now(UTC), **payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def list_usage_records(db: AsyncSession, organization_id: UUID) -> list[UsageRecord]:
    return list(
        (
            await db.scalars(
                select(UsageRecord)
                .where(UsageRecord.organization_id == organization_id)
                .order_by(UsageRecord.recorded_at.desc())
            )
        ).all()
    )


async def create_invoice(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SaaSInvoiceCreate,
    authz: AuthorizationService,
) -> SaaSInvoice:
    await ensure_manage_billing(authz, identity, payload.organization_id)
    subscription = await get_subscription_for_organization(db, payload.subscription_id, payload.organization_id)
    plan = await get_plan(db, subscription.billing_plan_id)
    usage_records = await list_usage_records(db, payload.organization_id)
    meters = {meter.id: meter for meter in await list_usage_meters(db)}
    usage_total = Decimal("0")
    line_parts = [f"Base plan {plan.name}: {plan.base_price}"]
    for record in usage_records:
        if record.subscription_id != subscription.id:
            continue
        meter = meters.get(record.usage_meter_id)
        if meter is None:
            continue
        overage_qty = max(record.quantity - meter.included_quantity, 0)
        overage = Decimal(overage_qty) * meter.overage_price
        usage_total += overage
        line_parts.append(f"{meter.name}: {record.quantity} {meter.unit.value}, overage {overage}")
    subtotal = (subscription.negotiated_price or plan.base_price) + usage_total
    total = subtotal + payload.tax_amount - payload.discount_amount
    invoice = SaaSInvoice(
        subtotal=subtotal,
        total=max(total, Decimal("0")),
        currency=plan.currency,
        line_items="\n".join(line_parts),
        **payload.model_dump(),
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


async def list_invoices(db: AsyncSession, organization_id: UUID) -> list[SaaSInvoice]:
    return list(
        (
            await db.scalars(
                select(SaaSInvoice)
                .where(SaaSInvoice.organization_id == organization_id)
                .order_by(SaaSInvoice.created_at.desc())
            )
        ).all()
    )


async def record_payment(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SaaSPaymentCreate,
    authz: AuthorizationService,
) -> SaaSPayment:
    await ensure_manage_billing(authz, identity, payload.organization_id)
    invoice = await get_invoice_for_organization(db, payload.invoice_id, payload.organization_id)
    payment = SaaSPayment(
        currency=invoice.currency,
        received_at=datetime.now(UTC),
        **payload.model_dump(),
    )
    invoice.amount_paid += payload.amount
    invoice.status = BillingInvoiceStatus.PAID if invoice.amount_paid >= invoice.total else BillingInvoiceStatus.PARTIAL
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def billing_tax_quote(
    organization_id: UUID,
    subtotal: Decimal,
    jurisdiction: str,
    reverse_charge: bool,
) -> dict:
    normalized = jurisdiction.upper()
    tax_rate = Decimal("0") if reverse_charge else localized_tax_rate(normalized)
    tax_amount = money(subtotal * tax_rate / Decimal("100"))
    return {
        "organization_id": organization_id,
        "jurisdiction": normalized,
        "subtotal": money(subtotal),
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "total": money(subtotal + tax_amount),
        "reverse_charge": reverse_charge,
        "filing_hint": filing_hint(normalized, reverse_charge),
    }


async def proration_quote(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    subscription_id: UUID,
    new_price: Decimal,
    effective_on: date,
    authz: AuthorizationService,
) -> dict:
    await ensure_manage_billing(authz, identity, organization_id)
    subscription = await get_subscription_for_organization(db, subscription_id, organization_id)
    plan = await get_plan(db, subscription.billing_plan_id)
    current_price = subscription.negotiated_price or plan.base_price
    period_days = max((subscription.current_period_end - subscription.current_period_start).days + 1, 1)
    bounded_effective = min(max(effective_on, subscription.current_period_start), subscription.current_period_end)
    remaining_days = max((subscription.current_period_end - bounded_effective).days + 1, 0)
    ratio = Decimal(remaining_days) / Decimal(period_days)
    unused_credit = money(current_price * ratio)
    new_charge = money(new_price * ratio)
    net_amount = money(new_charge - unused_credit)
    return {
        "organization_id": organization_id,
        "subscription_id": subscription.id,
        "current_price": money(current_price),
        "new_price": money(new_price),
        "effective_on": bounded_effective,
        "period_start": subscription.current_period_start,
        "period_end": subscription.current_period_end,
        "remaining_days": remaining_days,
        "total_days": period_days,
        "unused_credit": unused_credit,
        "new_charge": new_charge,
        "net_amount": net_amount,
        "recommendation": proration_recommendation(net_amount),
    }


async def dunning_notice(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    invoice_id: UUID,
    authz: AuthorizationService,
) -> dict:
    await ensure_manage_billing(authz, identity, organization_id)
    invoice = await get_invoice_for_organization(db, invoice_id, organization_id)
    amount_due = money(max(invoice.total - invoice.amount_paid, Decimal("0")))
    today = date.today()
    days_overdue = max((today - invoice.due_on).days, 0) if invoice.due_on else 0
    severity = "final" if days_overdue >= 30 else "urgent" if days_overdue >= 14 else "reminder"
    channel = "email+in_app" if severity == "reminder" else "email+sms+in_app"
    next_action = "pause_nonessential_entitlements" if severity == "final" else "retry_payment"
    return {
        "organization_id": organization_id,
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "days_overdue": days_overdue,
        "amount_due": amount_due,
        "severity": severity,
        "channel": channel,
        "message": (
            f"Invoice {invoice.invoice_number} has {amount_due} {invoice.currency} outstanding. "
            f"Please settle to keep AfroLete services active."
        ),
        "next_action": next_action,
    }


async def deliver_dunning_notice(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    invoice_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> dict:
    selected_settings = settings or get_settings()
    notice = await dunning_notice(db, identity, organization_id, invoice_id, authz)
    result = {
        **notice,
        "delivery_mode": selected_settings.billing_dunning_delivery_mode,
        "delivery_attempted": False,
        "delivered": False,
        "destination": selected_settings.billing_dunning_webhook_url or None,
        "provider_status_code": None,
        "failure_reason": None,
        "delivered_at": datetime.now(UTC),
    }
    if selected_settings.billing_dunning_delivery_mode == "record_only":
        result["failure_reason"] = "Record-only delivery mode; notice prepared for manual follow-up."
        return result
    if not selected_settings.billing_dunning_webhook_url:
        result["failure_reason"] = "Billing dunning webhook mode is enabled but no webhook URL is configured."
        return result

    result["delivery_attempted"] = True
    payload = {
        "event_type": "billing.dunning_notice",
        "organization_id": str(organization_id),
        "invoice_id": str(invoice_id),
        "invoice_number": notice["invoice_number"],
        "severity": notice["severity"],
        "channel": notice["channel"],
        "amount_due": str(notice["amount_due"]),
        "days_overdue": notice["days_overdue"],
        "message": notice["message"],
        "next_action": notice["next_action"],
        "created_at": result["delivered_at"].isoformat(),
    }
    headers = billing_dunning_headers(selected_settings)
    try:
        async with httpx.AsyncClient(timeout=selected_settings.billing_dunning_timeout_seconds) as client:
            response = await client.post(
                selected_settings.billing_dunning_webhook_url,
                json=payload,
                headers=headers,
            )
        result["provider_status_code"] = response.status_code
        result["delivered"] = 200 <= response.status_code < 300
        if not result["delivered"]:
            result["failure_reason"] = f"Dunning webhook returned {response.status_code}: {response.text[:500]}"
    except httpx.HTTPError as error:
        result["failure_reason"] = f"Dunning webhook failed: {error}"
    return result


def billing_dunning_headers(settings: Settings) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if settings.billing_dunning_webhook_key:
        headers["X-Afrolete-Billing-Dunning-Key"] = settings.billing_dunning_webhook_key
    return headers


async def ingest_payment_webhook(
    db: AsyncSession,
    payload: BillingPaymentWebhookCreate,
    signature_required: bool = False,
    signature_validated: bool = False,
) -> dict:
    invoice = await get_invoice_for_organization(db, payload.invoice_id, payload.organization_id)
    accepted = payload.status == "succeeded" and payload.event_type in {
        "payment.succeeded",
        "invoice.paid",
        "charge.succeeded",
    }
    payment: SaaSPayment | None = None
    if accepted:
        payment = SaaSPayment(
            organization_id=payload.organization_id,
            invoice_id=payload.invoice_id,
            amount=payload.amount,
            currency=invoice.currency,
            provider=payload.provider,
            external_payment_id=payload.external_payment_id,
            received_at=datetime.now(UTC),
            status="succeeded",
            notes=payload.raw_reference,
        )
        invoice.amount_paid += payload.amount
        invoice.status = (
            BillingInvoiceStatus.PAID
            if invoice.amount_paid >= invoice.total
            else BillingInvoiceStatus.PARTIAL
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
    return {
        "organization_id": payload.organization_id,
        "invoice_id": payload.invoice_id,
        "provider": payload.provider,
        "event_type": payload.event_type,
        "accepted": accepted,
        "signature_required": signature_required,
        "signature_validated": signature_validated,
        "payment_id": payment.id if payment else None,
        "invoice_status": invoice.status,
        "amount_paid": invoice.amount_paid,
        "message": "Payment applied." if accepted else "Webhook event recorded as non-settling.",
    }


def validate_payment_webhook_signature(
    raw_body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
    settings: Settings | None = None,
) -> tuple[bool, bool]:
    selected_settings = settings or get_settings()
    signing_key = selected_settings.billing_payment_webhook_signing_key
    if not signing_key:
        return False, False
    if not timestamp_header or not signature_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing webhook signature")
    try:
        timestamp = int(timestamp_header)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook timestamp") from exc
    age = abs(int(time.time()) - timestamp)
    if age > selected_settings.billing_payment_webhook_tolerance_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Stale webhook signature")
    expected = hmac.new(
        signing_key.encode(),
        timestamp_header.encode() + b"." + raw_body,
        sha256,
    ).hexdigest()
    submitted = signature_header.removeprefix("sha256=")
    if not hmac.compare_digest(expected, submitted):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")
    return True, True


async def create_entitlement(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: BillingEntitlementCreate,
    authz: AuthorizationService,
) -> BillingEntitlement:
    await ensure_manage_billing(authz, identity, payload.organization_id)
    await get_subscription_for_organization(db, payload.subscription_id, payload.organization_id)
    entitlement = BillingEntitlement(**payload.model_dump())
    db.add(entitlement)
    await db.commit()
    await db.refresh(entitlement)
    return entitlement


async def list_entitlements(db: AsyncSession, organization_id: UUID) -> list[BillingEntitlement]:
    return list(
        (
            await db.scalars(
                select(BillingEntitlement)
                .where(BillingEntitlement.organization_id == organization_id)
                .order_by(BillingEntitlement.feature_key)
            )
        ).all()
    )


async def billing_summary(db: AsyncSession, organization_id: UUID) -> dict:
    plans = await list_plans(db)
    subscriptions = await list_subscriptions(db, organization_id)
    meters = await list_usage_meters(db)
    records = await list_usage_records(db, organization_id)
    invoices = await list_invoices(db, organization_id)
    entitlements = await list_entitlements(db, organization_id)
    plan_by_id = {plan.id: plan for plan in plans}
    mrr = sum(
        subscription.negotiated_price
        or (
            plan_by_id[subscription.billing_plan_id].base_price
            if subscription.billing_plan_id in plan_by_id
            else Decimal("0")
        )
        for subscription in subscriptions
        if subscription.status == SubscriptionStatus.ACTIVE
    )
    outstanding = sum(
        invoice.total - invoice.amount_paid
        for invoice in invoices
        if invoice.status in {BillingInvoiceStatus.OPEN, BillingInvoiceStatus.PARTIAL}
    )
    return {
        "organization_id": organization_id,
        "active_subscriptions": sum(1 for sub in subscriptions if sub.status == SubscriptionStatus.ACTIVE),
        "plans": len(plans),
        "usage_meters": len(meters),
        "usage_records": len(records),
        "open_invoices": sum(1 for invoice in invoices if invoice.status in {BillingInvoiceStatus.OPEN, BillingInvoiceStatus.PARTIAL}),
        "monthly_recurring_revenue": mrr,
        "invoice_outstanding": outstanding,
        "entitlements": len(entitlements),
    }


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def get_plan(db: AsyncSession, plan_id: UUID) -> BillingPlan:
    plan = await db.get(BillingPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing plan not found")
    return plan


async def get_usage_meter(db: AsyncSession, meter_id: UUID) -> UsageMeter:
    meter = await db.get(UsageMeter, meter_id)
    if meter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usage meter not found")
    return meter


async def get_subscription_for_organization(db: AsyncSession, subscription_id: UUID, organization_id: UUID) -> TenantSubscription:
    subscription = await db.get(TenantSubscription, subscription_id)
    if subscription is None or subscription.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription


async def get_invoice_for_organization(db: AsyncSession, invoice_id: UUID, organization_id: UUID) -> SaaSInvoice:
    invoice = await db.get(SaaSInvoice, invoice_id)
    if invoice is None or invoice.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def localized_tax_rate(jurisdiction: str) -> Decimal:
    return {
        "KE": Decimal("16.00"),
        "NG": Decimal("7.50"),
        "ZA": Decimal("15.00"),
        "EU": Decimal("20.00"),
        "GB": Decimal("20.00"),
        "US": Decimal("0.00"),
    }.get(jurisdiction, Decimal("0.00"))


def filing_hint(jurisdiction: str, reverse_charge: bool) -> str:
    if reverse_charge:
        return "Customer reverse-charge treatment; retain tax evidence with the invoice."
    if jurisdiction == "KE":
        return "Apply Kenyan VAT handling and prepare tax invoice evidence."
    if jurisdiction in {"EU", "GB"}:
        return "Validate buyer tax location before filing VAT return lines."
    if jurisdiction == "US":
        return "Sales tax not applied by this generic quote; configure state rules before filing."
    return "No localized rule configured; review jurisdiction settings before filing."


def proration_recommendation(net_amount: Decimal) -> str:
    if net_amount > 0:
        return "Charge the prorated upgrade amount on the next invoice."
    if net_amount < 0:
        return "Apply the prorated credit to the next invoice."
    return "No prorated balance is due for this period."
