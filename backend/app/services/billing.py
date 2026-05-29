import hmac
import time
from calendar import monthrange
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from urllib.parse import quote
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
    BillingPlanChangeCreate,
    BillingDunningRunCreate,
    BillingDunningRunRead,
    BillingLateFeeRunCreate,
    BillingLateFeeRunRead,
    BillingPaymentWebhookCreate,
    BillingPaymentRetryRunCreate,
    BillingPaymentRetryRunRead,
    BillingPlanCreate,
    BillingRecurringInvoiceRunCreate,
    BillingRecurringInvoiceRunRead,
    BillingSubscriptionLifecycleCreate,
    BillingSubscriptionLifecycleRead,
    SaaSInvoiceCheckoutLinkRead,
    SaaSInvoiceCheckoutSettlementCreate,
    SaaSInvoiceCheckoutSettlementRead,
    SaaSInvoiceCreate,
    SaaSInvoiceHostedCheckoutRead,
    SaaSPaymentCreate,
    SubscriptionCreate,
    UsageMeterCreate,
    UsageRecordCreate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.secrets import resolve_secret


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


async def run_recurring_invoice_scheduler(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: BillingRecurringInvoiceRunCreate,
    authz: AuthorizationService,
) -> BillingRecurringInvoiceRunRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_billing(authz, identity, payload.organization_id)
    return await run_recurring_invoice_worker(
        db,
        organization_id=payload.organization_id,
        bill_on=payload.bill_on,
        due_in_days=payload.due_in_days,
        limit=payload.limit,
        dry_run=payload.dry_run,
        invoice_prefix=payload.invoice_prefix,
    )


async def run_recurring_invoice_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    *,
    bill_on: date | None = None,
    due_in_days: int = 14,
    limit: int = 100,
    dry_run: bool = False,
    invoice_prefix: str = "SAAS",
) -> BillingRecurringInvoiceRunRead:
    effective_bill_on = bill_on or date.today()
    subscriptions = await subscriptions_due_for_recurring_invoice(
        db,
        organization_id=organization_id,
        bill_on=effective_bill_on,
        limit=limit,
    )
    invoice_ids: list[UUID] = []
    subscription_ids: list[UUID] = []
    skipped_count = 0
    failed_count = 0
    total_invoiced = Decimal("0")

    for subscription in subscriptions:
        if dry_run:
            skipped_count += 1
            continue
        try:
            if await has_invoice_for_subscription_period(db, subscription):
                skipped_count += 1
                continue
            plan = await get_plan(db, subscription.billing_plan_id)
            invoice = await create_recurring_invoice_for_subscription(
                db,
                subscription,
                plan,
                bill_on=effective_bill_on,
                due_in_days=due_in_days,
                invoice_prefix=invoice_prefix,
            )
            advance_subscription_period(subscription)
            await db.commit()
            await db.refresh(invoice)
            invoice_ids.append(invoice.id)
            subscription_ids.append(subscription.id)
            total_invoiced += invoice.total
        except Exception:
            failed_count += 1
            await db.rollback()

    return BillingRecurringInvoiceRunRead(
        organization_id=organization_id,
        bill_on=effective_bill_on,
        eligible_count=len(subscriptions),
        executed_count=len(subscriptions) - skipped_count,
        invoiced_count=len(invoice_ids),
        skipped_count=skipped_count,
        failed_count=failed_count,
        dry_run=dry_run,
        invoice_ids=invoice_ids,
        subscription_ids=subscription_ids,
        total_invoiced=money(total_invoiced),
    )


async def subscriptions_due_for_recurring_invoice(
    db: AsyncSession,
    *,
    organization_id: UUID | None,
    bill_on: date,
    limit: int,
) -> list[TenantSubscription]:
    statement = (
        select(TenantSubscription)
        .where(TenantSubscription.next_billing_on.is_not(None))
        .where(TenantSubscription.next_billing_on <= bill_on)
        .where(TenantSubscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]))
        .order_by(TenantSubscription.next_billing_on.asc(), TenantSubscription.created_at.asc())
        .limit(limit)
    )
    if organization_id is not None:
        statement = statement.where(TenantSubscription.organization_id == organization_id)
    rows = list((await db.scalars(statement)).all())
    return [
        subscription
        for subscription in rows
        if subscription.trial_ends_on is None or subscription.trial_ends_on < bill_on
    ]


async def has_invoice_for_subscription_period(
    db: AsyncSession,
    subscription: TenantSubscription,
) -> bool:
    existing = await db.scalar(
        select(SaaSInvoice.id)
        .where(SaaSInvoice.subscription_id == subscription.id)
        .where(SaaSInvoice.period_start == subscription.current_period_start)
        .where(SaaSInvoice.period_end == subscription.current_period_end)
        .limit(1)
    )
    return existing is not None


async def create_recurring_invoice_for_subscription(
    db: AsyncSession,
    subscription: TenantSubscription,
    plan: BillingPlan,
    *,
    bill_on: date,
    due_in_days: int,
    invoice_prefix: str,
) -> SaaSInvoice:
    usage_by_meter = await recurring_usage_by_meter(db, subscription)
    meters = {meter.id: meter for meter in await list_usage_meters(db)}
    usage_total = Decimal("0")
    base_price = subscription.negotiated_price or plan.base_price
    line_parts = [
        (
            f"Recurring {enum_value(subscription.billing_cycle)} subscription {plan.name}: "
            f"{money(base_price)} {plan.currency}"
        )
    ]
    for meter_id, quantity in usage_by_meter.items():
        meter = meters.get(meter_id)
        if meter is None:
            continue
        overage_quantity = max(quantity - meter.included_quantity, 0)
        overage = money(Decimal(overage_quantity) * meter.overage_price)
        usage_total += overage
        line_parts.append(
            f"{meter.name}: {quantity} {meter.unit.value}, included {meter.included_quantity}, overage {overage}"
        )

    subtotal = money(base_price + usage_total)
    invoice = SaaSInvoice(
        organization_id=subscription.organization_id,
        subscription_id=subscription.id,
        invoice_number=recurring_invoice_number(invoice_prefix, subscription, bill_on),
        period_start=subscription.current_period_start,
        period_end=subscription.current_period_end,
        subtotal=subtotal,
        tax_amount=Decimal("0"),
        discount_amount=Decimal("0"),
        total=subtotal,
        amount_paid=Decimal("0"),
        currency=plan.currency,
        due_on=bill_on + timedelta(days=due_in_days),
        status=BillingInvoiceStatus.OPEN,
        line_items="\n".join(line_parts),
    )
    db.add(invoice)
    return invoice


async def recurring_usage_by_meter(
    db: AsyncSession,
    subscription: TenantSubscription,
) -> dict[UUID, int]:
    records = [
        record
        for record in await list_usage_records(db, subscription.organization_id)
        if record.subscription_id == subscription.id
        and subscription.current_period_start <= record.recorded_at.date() <= subscription.current_period_end
    ]
    totals: dict[UUID, int] = {}
    for record in records:
        totals[record.usage_meter_id] = totals.get(record.usage_meter_id, 0) + record.quantity
    return totals


def advance_subscription_period(subscription: TenantSubscription) -> None:
    if subscription.cancel_at_period_end:
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.next_billing_on = None
        subscription.notes = append_note(subscription.notes, "Cancelled at period end after final recurring invoice.")
        return
    next_start = subscription.current_period_end + timedelta(days=1)
    next_end = period_end_for_cycle(next_start, subscription.billing_cycle)
    subscription.current_period_start = next_start
    subscription.current_period_end = next_end
    subscription.next_billing_on = next_end
    if subscription.status == SubscriptionStatus.TRIALING:
        subscription.status = SubscriptionStatus.ACTIVE


def period_end_for_cycle(period_start: date, cycle) -> date:
    months = {"monthly": 1, "quarterly": 3, "annual": 12}[enum_value(cycle)]
    end_month_index = period_start.month + months
    end_year = period_start.year + (end_month_index - 1) // 12
    end_month = ((end_month_index - 1) % 12) + 1
    day = min(period_start.day, monthrange(end_year, end_month)[1])
    return date(end_year, end_month, day) - timedelta(days=1)


def recurring_invoice_number(
    prefix: str,
    subscription: TenantSubscription,
    bill_on: date,
) -> str:
    normalized_prefix = "".join(character for character in prefix.upper() if character.isalnum() or character == "-")
    return f"{normalized_prefix}-{bill_on.strftime('%Y%m%d')}-{str(subscription.id)[:8]}"


def append_note(existing: str | None, note: str) -> str:
    return f"{existing}\n{note}" if existing else note


def enum_value(value) -> str:
    return getattr(value, "value", value)


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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


async def prepare_saas_invoice_checkout_link(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    invoice_id: UUID,
    provider: str,
    checkout_base_url: str,
    authz: AuthorizationService,
) -> SaaSInvoiceCheckoutLinkRead:
    await ensure_manage_billing(authz, identity, organization_id)
    invoice = await get_invoice_for_organization(db, invoice_id, organization_id)
    session_id = saas_invoice_checkout_session_id(invoice, provider)
    return SaaSInvoiceCheckoutLinkRead(
        invoice_id=invoice.id,
        provider=provider,
        session_id=session_id,
        checkout_url=saas_invoice_checkout_session_url(checkout_base_url, session_id, invoice, provider),
        hosted_checkout=saas_invoice_hosted_checkout_read(invoice, provider, session_id),
    )


async def get_saas_invoice_hosted_checkout(
    db: AsyncSession,
    session_id: str,
    invoice_id: UUID,
    provider: str,
) -> SaaSInvoiceHostedCheckoutRead:
    invoice = await db.get(SaaSInvoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SaaS invoice checkout session not found")
    expected_session_id = saas_invoice_checkout_session_id(invoice, provider)
    if not hmac.compare_digest(expected_session_id, session_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid checkout session")
    return saas_invoice_hosted_checkout_read(invoice, provider, session_id)


async def settle_saas_invoice_checkout(
    db: AsyncSession,
    session_id: str,
    payload: SaaSInvoiceCheckoutSettlementCreate,
    signature_required: bool = False,
    signature_validated: bool = False,
) -> SaaSInvoiceCheckoutSettlementRead:
    invoice = await db.get(SaaSInvoice, payload.invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SaaS invoice checkout session not found")
    expected_session_id = saas_invoice_checkout_session_id(invoice, payload.provider)
    if not hmac.compare_digest(expected_session_id, session_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid checkout session")
    if payload.currency is not None and payload.currency.upper() != invoice.currency:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Payment currency mismatch")

    open_amount = saas_invoice_open_amount(invoice)
    accepted = payload.status == "succeeded" and open_amount > 0
    payment: SaaSPayment | None = None
    message = "Checkout event recorded as non-settling."
    if accepted:
        amount = money(payload.amount or open_amount)
        if amount > open_amount:
            amount = open_amount
        external_reference = payload.external_payment_id or f"{payload.provider}:{session_id}"
        existing_payment = await db.scalar(
            select(SaaSPayment).where(
                SaaSPayment.organization_id == invoice.organization_id,
                SaaSPayment.provider == payload.provider,
                SaaSPayment.external_payment_id == external_reference,
            )
        )
        if existing_payment is not None:
            payment = existing_payment
            message = "Payment event was already applied."
        else:
            payment = SaaSPayment(
                organization_id=invoice.organization_id,
                invoice_id=invoice.id,
                amount=amount,
                currency=invoice.currency,
                provider=payload.provider,
                external_payment_id=external_reference,
                received_at=datetime.now(UTC),
                status="succeeded",
                notes=payload.raw_reference or f"SaaS invoice checkout settled via {payload.provider}.",
            )
            invoice.amount_paid = money(invoice.amount_paid + amount)
            invoice.status = (
                BillingInvoiceStatus.PAID
                if invoice.amount_paid >= invoice.total
                else BillingInvoiceStatus.PARTIAL
            )
            invoice.line_items = append_note(
                invoice.line_items,
                f"Hosted checkout payment {amount} {invoice.currency} via {payload.provider}.",
            )
            db.add(payment)
            await db.commit()
            await db.refresh(payment)
            await db.refresh(invoice)
            message = "SaaS invoice payment applied."

    return SaaSInvoiceCheckoutSettlementRead(
        invoice_id=invoice.id,
        provider=payload.provider,
        accepted=accepted,
        signature_required=signature_required,
        signature_validated=signature_validated,
        payment_id=payment.id if payment is not None else None,
        invoice_status=invoice.status,
        amount_paid=invoice.amount_paid,
        open_amount=saas_invoice_open_amount(invoice),
        session_status=saas_invoice_checkout_session_status(invoice),
        message=message,
    )


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


async def deliver_tax_filing(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    period_start: date,
    period_end: date,
    jurisdiction: str,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> dict:
    await ensure_manage_billing(authz, identity, organization_id)
    if period_end < period_start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="period_end must be on or after period_start")
    selected_settings = settings or get_settings()
    invoices = [
        invoice
        for invoice in await list_invoices(db, organization_id)
        if invoice.period_start <= period_end and invoice.period_end >= period_start
    ]
    currency = filing_currency(invoices)
    filed_at = datetime.now(UTC)
    result = {
        "organization_id": organization_id,
        "jurisdiction": jurisdiction.upper(),
        "period_start": period_start,
        "period_end": period_end,
        "invoice_count": len(invoices),
        "taxable_subtotal": money(sum((invoice.subtotal for invoice in invoices), Decimal("0"))),
        "tax_amount": money(sum((invoice.tax_amount for invoice in invoices), Decimal("0"))),
        "gross_total": money(sum((invoice.total for invoice in invoices), Decimal("0"))),
        "outstanding_total": money(
            sum((invoice.total - invoice.amount_paid for invoice in invoices), Decimal("0"))
        ),
        "currency": currency,
        "filing_reference": tax_filing_reference(organization_id, jurisdiction, period_start, period_end),
        "delivery_mode": selected_settings.billing_tax_filing_delivery_mode,
        "delivery_attempted": False,
        "delivered": False,
        "destination": selected_settings.billing_tax_filing_webhook_url or None,
        "provider_status_code": None,
        "failure_reason": None,
        "filed_at": filed_at,
    }
    if selected_settings.billing_tax_filing_delivery_mode == "record_only":
        result["failure_reason"] = "Record-only filing mode; tax package prepared for manual submission."
        return result
    if not selected_settings.billing_tax_filing_webhook_url:
        result["failure_reason"] = "Tax filing webhook mode is enabled but no webhook URL is configured."
        return result

    result["delivery_attempted"] = True
    payload = {
        "event_type": "billing.tax_filing",
        "organization_id": str(organization_id),
        "jurisdiction": result["jurisdiction"],
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "invoice_count": result["invoice_count"],
        "taxable_subtotal": str(result["taxable_subtotal"]),
        "tax_amount": str(result["tax_amount"]),
        "gross_total": str(result["gross_total"]),
        "outstanding_total": str(result["outstanding_total"]),
        "currency": currency,
        "filing_reference": result["filing_reference"],
        "filed_at": filed_at.isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=selected_settings.billing_tax_filing_timeout_seconds) as client:
            response = await client.post(
                selected_settings.billing_tax_filing_webhook_url,
                json=payload,
                headers=await billing_tax_filing_headers(selected_settings),
            )
        result["provider_status_code"] = response.status_code
        result["delivered"] = 200 <= response.status_code < 300
        if not result["delivered"]:
            result["failure_reason"] = f"Tax filing webhook returned {response.status_code}: {response.text[:500]}"
    except httpx.HTTPError as error:
        result["failure_reason"] = f"Tax filing webhook failed: {error}"
    return result


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


async def apply_plan_change(
    db: AsyncSession,
    identity: CurrentIdentity,
    subscription_id: UUID,
    payload: BillingPlanChangeCreate,
    authz: AuthorizationService,
) -> dict:
    await ensure_manage_billing(authz, identity, payload.organization_id)
    subscription = await get_subscription_for_organization(db, subscription_id, payload.organization_id)
    previous_plan = await get_plan(subscription.billing_plan_id)
    previous_price = money(subscription.negotiated_price or previous_plan.base_price)
    quote = await proration_quote(
        db,
        identity,
        payload.organization_id,
        subscription_id,
        payload.new_price,
        payload.effective_on,
        authz,
    )
    new_plan = await get_plan(payload.new_billing_plan_id) if payload.new_billing_plan_id else previous_plan
    subscription.billing_plan_id = new_plan.id
    subscription.billing_cycle = new_plan.billing_cycle
    subscription.negotiated_price = money(payload.new_price)
    if subscription.status in {SubscriptionStatus.TRIALING, SubscriptionStatus.PAST_DUE, SubscriptionStatus.PAUSED}:
        subscription.status = SubscriptionStatus.ACTIVE
    subscription.notes = subscription_plan_change_notes(
        subscription.notes,
        previous_plan.id,
        new_plan.id,
        previous_price,
        money(payload.new_price),
        quote["net_amount"],
        payload.effective_on,
        payload.note,
    )
    await db.commit()
    await db.refresh(subscription)
    return {
        **quote,
        "previous_billing_plan_id": previous_plan.id,
        "new_billing_plan_id": new_plan.id,
        "previous_price": previous_price,
        "applied_price": subscription.negotiated_price or money(payload.new_price),
        "subscription_status": subscription.status,
        "applied_at": datetime.now(UTC),
    }


async def update_subscription_lifecycle(
    db: AsyncSession,
    identity: CurrentIdentity,
    subscription_id: UUID,
    payload: BillingSubscriptionLifecycleCreate,
    authz: AuthorizationService,
) -> BillingSubscriptionLifecycleRead:
    await ensure_manage_billing(authz, identity, payload.organization_id)
    subscription = await get_subscription_for_organization(db, subscription_id, payload.organization_id)
    previous_status = subscription.status
    effective_on = payload.effective_on or date.today()
    action = payload.action
    if action == "cancel_at_period_end":
        if subscription.status == SubscriptionStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cancelled subscriptions cannot be scheduled for cancellation",
            )
        subscription.cancel_at_period_end = True
        message = "Subscription will cancel at the current period end."
    elif action == "cancel_now":
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancel_at_period_end = False
        subscription.next_billing_on = None
        message = "Subscription cancelled immediately."
    elif action == "undo_cancel":
        if not subscription.cancel_at_period_end and subscription.status != SubscriptionStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Subscription is not pending cancellation",
            )
        subscription.cancel_at_period_end = False
        if subscription.status == SubscriptionStatus.CANCELLED:
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.next_billing_on = subscription.current_period_end
        message = "Subscription cancellation removed."
    elif action == "pause":
        if subscription.status == SubscriptionStatus.CANCELLED:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cancelled subscriptions cannot be paused")
        subscription.status = SubscriptionStatus.PAUSED
        subscription.cancel_at_period_end = False
        message = "Subscription paused."
    else:
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.cancel_at_period_end = False
        if subscription.next_billing_on is None:
            subscription.next_billing_on = subscription.current_period_end
        message = "Subscription resumed."

    subscription.notes = subscription_lifecycle_note(
        subscription.notes,
        action,
        previous_status,
        subscription.status,
        effective_on,
        payload.reason,
        subscription.cancel_at_period_end,
    )
    await db.commit()
    await db.refresh(subscription)
    return BillingSubscriptionLifecycleRead(
        organization_id=subscription.organization_id,
        subscription_id=subscription.id,
        action=action,
        previous_status=previous_status,
        status=subscription.status,
        cancel_at_period_end=subscription.cancel_at_period_end,
        effective_on=effective_on,
        message=message,
        subscription=subscription_read(subscription),
    )


async def dunning_notice(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    invoice_id: UUID,
    authz: AuthorizationService,
) -> dict:
    await ensure_manage_billing(authz, identity, organization_id)
    invoice = await get_invoice_for_organization(db, invoice_id, organization_id)
    return dunning_notice_for_invoice(invoice, organization_id, date.today())


def dunning_notice_for_invoice(
    invoice: SaaSInvoice,
    organization_id: UUID,
    as_of: date,
) -> dict:
    amount_due = money(max(invoice.total - invoice.amount_paid, Decimal("0")))
    days_overdue = max((as_of - invoice.due_on).days, 0) if invoice.due_on else 0
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
    await ensure_manage_billing(authz, identity, organization_id)
    invoice = await get_invoice_for_organization(db, invoice_id, organization_id)
    return await deliver_dunning_notice_for_invoice(
        invoice,
        organization_id,
        selected_settings,
        as_of=date.today(),
    )


async def deliver_dunning_notice_for_invoice(
    invoice: SaaSInvoice,
    organization_id: UUID,
    settings: Settings,
    *,
    as_of: date,
) -> dict:
    notice = dunning_notice_for_invoice(invoice, organization_id, as_of)
    result = {
        **notice,
        "delivery_mode": settings.billing_dunning_delivery_mode,
        "delivery_attempted": False,
        "delivered": False,
        "destination": settings.billing_dunning_webhook_url or None,
        "provider_status_code": None,
        "failure_reason": None,
        "delivered_at": datetime.now(UTC),
    }
    if settings.billing_dunning_delivery_mode == "record_only":
        result["failure_reason"] = "Record-only delivery mode; notice prepared for manual follow-up."
        return result
    if not settings.billing_dunning_webhook_url:
        result["failure_reason"] = "Billing dunning webhook mode is enabled but no webhook URL is configured."
        return result

    result["delivery_attempted"] = True
    payload = {
        "event_type": "billing.dunning_notice",
        "organization_id": str(organization_id),
        "invoice_id": str(invoice.id),
        "invoice_number": notice["invoice_number"],
        "severity": notice["severity"],
        "channel": notice["channel"],
        "amount_due": str(notice["amount_due"]),
        "days_overdue": notice["days_overdue"],
        "message": notice["message"],
        "next_action": notice["next_action"],
        "created_at": result["delivered_at"].isoformat(),
    }
    headers = await billing_dunning_headers(settings)
    try:
        async with httpx.AsyncClient(timeout=settings.billing_dunning_timeout_seconds) as client:
            response = await client.post(
                settings.billing_dunning_webhook_url,
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


async def run_dunning_scheduler(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: BillingDunningRunCreate,
    authz: AuthorizationService,
) -> BillingDunningRunRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_billing(authz, identity, payload.organization_id)
    return await run_dunning_worker(
        db,
        organization_id=payload.organization_id,
        overdue_as_of=payload.overdue_as_of,
        overdue_after_days=payload.overdue_after_days,
        repeat_after_days=payload.repeat_after_days,
        limit=payload.limit,
        dry_run=payload.dry_run,
    )


async def run_dunning_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    *,
    overdue_as_of: date | None = None,
    overdue_after_days: int = 0,
    repeat_after_days: int = 7,
    limit: int = 100,
    dry_run: bool = False,
    settings: Settings | None = None,
) -> BillingDunningRunRead:
    effective_as_of = overdue_as_of or date.today()
    selected_settings = settings or get_settings()
    invoices = await invoices_due_for_dunning(
        db,
        organization_id=organization_id,
        overdue_as_of=effective_as_of,
        overdue_after_days=overdue_after_days,
        repeat_after_days=repeat_after_days,
        limit=limit,
    )
    invoice_ids: list[UUID] = []
    subscription_ids: list[UUID] = []
    delivered_count = 0
    record_only_count = 0
    past_due_count = 0
    skipped_count = 0
    failed_count = 0
    severity_counts: dict[str, int] = {}
    total_outstanding = Decimal("0")

    for invoice in invoices:
        total_outstanding += money(max(invoice.total - invoice.amount_paid, Decimal("0")))
        if dry_run:
            skipped_count += 1
            continue
        try:
            delivery = await deliver_dunning_notice_for_invoice(
                invoice,
                invoice.organization_id,
                selected_settings,
                as_of=effective_as_of,
            )
            invoice_ids.append(invoice.id)
            subscription_ids.append(invoice.subscription_id)
            severity = str(delivery["severity"])
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            invoice.dunning_count = (invoice.dunning_count or 0) + 1
            invoice.dunning_last_sent_at = delivery["delivered_at"]
            invoice.dunning_last_severity = severity
            if delivery["delivered"]:
                delivered_count += 1
            elif delivery["delivery_mode"] == "record_only":
                record_only_count += 1
            elif delivery["delivery_attempted"]:
                failed_count += 1
            subscription = await db.get(TenantSubscription, invoice.subscription_id)
            if subscription and subscription.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}:
                subscription.status = SubscriptionStatus.PAST_DUE
                subscription.notes = append_note(
                    subscription.notes,
                    f"Marked past_due after {severity} dunning notice for invoice {invoice.invoice_number}.",
                )
                past_due_count += 1
            await db.commit()
        except Exception:
            failed_count += 1
            await db.rollback()

    return BillingDunningRunRead(
        organization_id=organization_id,
        overdue_as_of=effective_as_of,
        eligible_count=len(invoices),
        executed_count=len(invoices) - skipped_count,
        notice_count=len(invoice_ids),
        delivered_count=delivered_count,
        record_only_count=record_only_count,
        past_due_count=past_due_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        dry_run=dry_run,
        invoice_ids=invoice_ids,
        subscription_ids=list(dict.fromkeys(subscription_ids)),
        total_outstanding=money(total_outstanding),
        severity_counts=severity_counts,
    )


async def invoices_due_for_dunning(
    db: AsyncSession,
    *,
    organization_id: UUID | None,
    overdue_as_of: date,
    overdue_after_days: int,
    repeat_after_days: int,
    limit: int,
) -> list[SaaSInvoice]:
    cutoff = overdue_as_of - timedelta(days=overdue_after_days)
    statement = (
        select(SaaSInvoice)
        .where(SaaSInvoice.status.in_([BillingInvoiceStatus.OPEN, BillingInvoiceStatus.PARTIAL]))
        .where(SaaSInvoice.due_on.is_not(None))
        .where(SaaSInvoice.due_on <= cutoff)
        .order_by(SaaSInvoice.due_on.asc(), SaaSInvoice.created_at.asc())
        .limit(limit)
    )
    if organization_id is not None:
        statement = statement.where(SaaSInvoice.organization_id == organization_id)
    rows = list((await db.scalars(statement)).all())
    repeat_cutoff = overdue_as_of - timedelta(days=repeat_after_days)
    return [
        invoice
        for invoice in rows
        if invoice.total > invoice.amount_paid
        and (
            invoice.dunning_last_sent_at is None
            or normalize_datetime(invoice.dunning_last_sent_at).date() <= repeat_cutoff
        )
    ]


async def run_late_fee_scheduler(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: BillingLateFeeRunCreate,
    authz: AuthorizationService,
) -> BillingLateFeeRunRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_billing(authz, identity, payload.organization_id)
    return await run_late_fee_worker(
        db,
        organization_id=payload.organization_id,
        apply_on=payload.apply_on,
        overdue_after_days=payload.overdue_after_days,
        repeat_after_days=payload.repeat_after_days,
        fixed_fee=payload.fixed_fee,
        percentage_rate=payload.percentage_rate,
        max_fee=payload.max_fee,
        limit=payload.limit,
        dry_run=payload.dry_run,
    )


async def run_late_fee_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    *,
    apply_on: date | None = None,
    overdue_after_days: int = 0,
    repeat_after_days: int = 30,
    fixed_fee: Decimal = Decimal("0"),
    percentage_rate: Decimal = Decimal("0"),
    max_fee: Decimal | None = None,
    limit: int = 100,
    dry_run: bool = False,
) -> BillingLateFeeRunRead:
    effective_apply_on = apply_on or date.today()
    invoices = await invoices_due_for_late_fee(
        db,
        organization_id=organization_id,
        apply_on=effective_apply_on,
        overdue_after_days=overdue_after_days,
        repeat_after_days=repeat_after_days,
        limit=limit,
    )
    invoice_ids: list[UUID] = []
    subscription_ids: list[UUID] = []
    skipped_count = 0
    failed_count = 0
    total_late_fees = Decimal("0")

    for invoice in invoices:
        fee = calculate_late_fee(
            invoice,
            fixed_fee=fixed_fee,
            percentage_rate=percentage_rate,
            max_fee=max_fee,
        )
        if fee <= 0:
            skipped_count += 1
            continue
        if dry_run:
            skipped_count += 1
            total_late_fees += fee
            continue
        try:
            invoice.total = money(invoice.total + fee)
            invoice.late_fee_total = money((invoice.late_fee_total or Decimal("0")) + fee)
            invoice.late_fee_count = (invoice.late_fee_count or 0) + 1
            invoice.late_fee_last_applied_on = effective_apply_on
            invoice.line_items = append_note(
                invoice.line_items,
                f"Late fee {fee} {invoice.currency} applied on {effective_apply_on.isoformat()}.",
            )
            subscription = await db.get(TenantSubscription, invoice.subscription_id)
            if subscription and subscription.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}:
                subscription.status = SubscriptionStatus.PAST_DUE
                subscription.notes = append_note(
                    subscription.notes,
                    f"Marked past_due after late fee on invoice {invoice.invoice_number}.",
                )
            await db.commit()
            invoice_ids.append(invoice.id)
            subscription_ids.append(invoice.subscription_id)
            total_late_fees += fee
        except Exception:
            failed_count += 1
            await db.rollback()

    return BillingLateFeeRunRead(
        organization_id=organization_id,
        apply_on=effective_apply_on,
        eligible_count=len(invoices),
        executed_count=len(invoices) - skipped_count,
        fee_count=len(invoice_ids),
        skipped_count=skipped_count,
        failed_count=failed_count,
        dry_run=dry_run,
        invoice_ids=invoice_ids,
        subscription_ids=list(dict.fromkeys(subscription_ids)),
        total_late_fees=money(total_late_fees),
    )


async def invoices_due_for_late_fee(
    db: AsyncSession,
    *,
    organization_id: UUID | None,
    apply_on: date,
    overdue_after_days: int,
    repeat_after_days: int,
    limit: int,
) -> list[SaaSInvoice]:
    cutoff = apply_on - timedelta(days=overdue_after_days)
    statement = (
        select(SaaSInvoice)
        .where(SaaSInvoice.status.in_([BillingInvoiceStatus.OPEN, BillingInvoiceStatus.PARTIAL]))
        .where(SaaSInvoice.due_on.is_not(None))
        .where(SaaSInvoice.due_on <= cutoff)
        .order_by(SaaSInvoice.due_on.asc(), SaaSInvoice.created_at.asc())
        .limit(limit)
    )
    if organization_id is not None:
        statement = statement.where(SaaSInvoice.organization_id == organization_id)
    rows = list((await db.scalars(statement)).all())
    repeat_cutoff = apply_on - timedelta(days=repeat_after_days)
    return [
        invoice
        for invoice in rows
        if invoice.total > invoice.amount_paid
        and (
            invoice.late_fee_last_applied_on is None
            or invoice.late_fee_last_applied_on <= repeat_cutoff
        )
    ]


def calculate_late_fee(
    invoice: SaaSInvoice,
    *,
    fixed_fee: Decimal,
    percentage_rate: Decimal,
    max_fee: Decimal | None,
) -> Decimal:
    outstanding = money(max(invoice.total - invoice.amount_paid, Decimal("0")))
    percentage_fee = money(outstanding * percentage_rate / Decimal("100"))
    fee = money(fixed_fee + percentage_fee)
    if max_fee is not None:
        fee = min(fee, money(max_fee))
    return money(fee)


async def run_payment_retry_scheduler(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: BillingPaymentRetryRunCreate,
    authz: AuthorizationService,
) -> BillingPaymentRetryRunRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_billing(authz, identity, payload.organization_id)
    return await run_payment_retry_worker(
        db,
        organization_id=payload.organization_id,
        retry_at=payload.retry_at,
        overdue_after_days=payload.overdue_after_days,
        repeat_after_hours=payload.repeat_after_hours,
        max_attempts=payload.max_attempts,
        provider=payload.provider,
        limit=payload.limit,
        dry_run=payload.dry_run,
    )


async def run_payment_retry_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    *,
    retry_at: datetime | None = None,
    overdue_after_days: int = 0,
    repeat_after_hours: int = 24,
    max_attempts: int = 3,
    provider: str = "billing_provider",
    limit: int = 100,
    dry_run: bool = False,
    settings: Settings | None = None,
) -> BillingPaymentRetryRunRead:
    selected_settings = settings or get_settings()
    effective_retry_at = normalize_datetime(retry_at or datetime.now(UTC))
    invoices = await invoices_due_for_payment_retry(
        db,
        organization_id=organization_id,
        retry_at=effective_retry_at,
        overdue_after_days=overdue_after_days,
        max_attempts=max_attempts,
        limit=limit,
    )
    invoice_ids: list[UUID] = []
    subscription_ids: list[UUID] = []
    skipped_count = 0
    failed_count = 0
    succeeded_count = 0
    submitted_count = 0
    total_attempted = Decimal("0")
    total_collected = Decimal("0")
    status_counts: dict[str, int] = {}

    for invoice in invoices:
        outstanding = money(max(invoice.total - invoice.amount_paid, Decimal("0")))
        if outstanding <= 0:
            skipped_count += 1
            continue
        if dry_run:
            skipped_count += 1
            total_attempted += outstanding
            continue
        try:
            subscription = await db.get(TenantSubscription, invoice.subscription_id)
            result = await deliver_payment_retry_for_invoice(
                selected_settings,
                invoice,
                subscription,
                provider=provider,
                outstanding=outstanding,
                attempted_at=effective_retry_at,
            )
            status_label = str(result["status"])
            status_counts[status_label] = status_counts.get(status_label, 0) + 1
            collected = min(money(result["amount_collected"]), outstanding)
            if collected > 0:
                payment = SaaSPayment(
                    organization_id=invoice.organization_id,
                    invoice_id=invoice.id,
                    amount=collected,
                    currency=invoice.currency,
                    provider=provider,
                    external_payment_id=str(result["provider_reference"]) if result["provider_reference"] else None,
                    received_at=effective_retry_at,
                    status="succeeded",
                    notes=f"Automated payment retry collected via {result['delivery_mode']}.",
                )
                db.add(payment)
                invoice.amount_paid = money(invoice.amount_paid + collected)
                invoice.status = (
                    BillingInvoiceStatus.PAID
                    if invoice.amount_paid >= invoice.total
                    else BillingInvoiceStatus.PARTIAL
                )
                succeeded_count += 1
                total_collected += collected
            elif result["delivered"]:
                submitted_count += 1
            else:
                failed_count += 1

            invoice.payment_retry_count = (invoice.payment_retry_count or 0) + 1
            invoice.payment_retry_last_attempted_at = effective_retry_at
            invoice.payment_retry_next_attempt_at = effective_retry_at + timedelta(hours=repeat_after_hours)
            invoice.payment_retry_last_status = status_label
            invoice.payment_retry_last_failure_reason = result["failure_reason"]
            invoice.payment_retry_last_provider_reference = result["provider_reference"]
            invoice.line_items = append_note(
                invoice.line_items,
                (
                    f"Payment retry {status_label} for {outstanding} {invoice.currency} "
                    f"via {provider} on {effective_retry_at.isoformat()}."
                ),
            )
            if subscription and subscription.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}:
                subscription.status = SubscriptionStatus.PAST_DUE
                subscription.notes = append_note(
                    subscription.notes,
                    f"Marked past_due after automated payment retry on invoice {invoice.invoice_number}.",
                )
            await db.commit()
            invoice_ids.append(invoice.id)
            subscription_ids.append(invoice.subscription_id)
            total_attempted += outstanding
        except Exception:
            failed_count += 1
            await db.rollback()

    return BillingPaymentRetryRunRead(
        organization_id=organization_id,
        retry_at=effective_retry_at,
        eligible_count=len(invoices),
        executed_count=len(invoices) - skipped_count,
        retry_count=len(invoice_ids),
        succeeded_count=succeeded_count,
        submitted_count=submitted_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        dry_run=dry_run,
        delivery_mode=selected_settings.billing_payment_retry_delivery_mode,
        invoice_ids=invoice_ids,
        subscription_ids=list(dict.fromkeys(subscription_ids)),
        total_attempted=money(total_attempted),
        total_collected=money(total_collected),
        status_counts=status_counts,
    )


async def invoices_due_for_payment_retry(
    db: AsyncSession,
    *,
    organization_id: UUID | None,
    retry_at: datetime,
    overdue_after_days: int,
    max_attempts: int,
    limit: int,
) -> list[SaaSInvoice]:
    cutoff = retry_at.date() - timedelta(days=overdue_after_days)
    statement = (
        select(SaaSInvoice)
        .where(SaaSInvoice.status.in_([BillingInvoiceStatus.OPEN, BillingInvoiceStatus.PARTIAL]))
        .where(SaaSInvoice.due_on.is_not(None))
        .where(SaaSInvoice.due_on <= cutoff)
        .order_by(SaaSInvoice.due_on.asc(), SaaSInvoice.created_at.asc())
        .limit(limit)
    )
    if organization_id is not None:
        statement = statement.where(SaaSInvoice.organization_id == organization_id)
    rows = list((await db.scalars(statement)).all())
    return [
        invoice
        for invoice in rows
        if invoice.total > invoice.amount_paid
        and (invoice.payment_retry_count or 0) < max_attempts
        and (
            invoice.payment_retry_next_attempt_at is None
            or normalize_datetime(invoice.payment_retry_next_attempt_at) <= retry_at
        )
    ]


async def deliver_payment_retry_for_invoice(
    settings: Settings,
    invoice: SaaSInvoice,
    subscription: TenantSubscription | None,
    *,
    provider: str,
    outstanding: Decimal,
    attempted_at: datetime,
) -> dict[str, object]:
    result: dict[str, object] = {
        "delivery_mode": settings.billing_payment_retry_delivery_mode,
        "delivered": False,
        "status": "recorded",
        "amount_collected": Decimal("0"),
        "provider_reference": None,
        "provider_status_code": None,
        "failure_reason": None,
    }
    payload = {
        "event_type": "billing.payment_retry",
        "provider": provider,
        "invoice_id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "organization_id": str(invoice.organization_id),
        "subscription_id": str(invoice.subscription_id),
        "external_customer_id": subscription.external_customer_id if subscription else None,
        "external_subscription_id": subscription.external_subscription_id if subscription else None,
        "currency": invoice.currency,
        "amount_due": str(outstanding),
        "attempted_at": attempted_at.isoformat(),
    }
    if settings.billing_payment_retry_delivery_mode == "record_only":
        result["delivered"] = True
        return result
    if not settings.billing_payment_retry_webhook_url:
        result["status"] = "failed"
        result["failure_reason"] = "Billing payment retry webhook mode is enabled but no webhook URL is configured."
        return result

    headers = await billing_payment_retry_headers(settings)
    try:
        async with httpx.AsyncClient(timeout=settings.billing_payment_retry_timeout_seconds) as client:
            response = await client.post(settings.billing_payment_retry_webhook_url, json=payload, headers=headers)
        result["provider_status_code"] = response.status_code
        result["delivered"] = 200 <= response.status_code < 300
        if result["delivered"]:
            body = response.json() if response.content else {}
            result["status"] = str(body.get("status") or "submitted")
            result["amount_collected"] = money(body.get("amount_collected") or body.get("amount") or Decimal("0"))
            result["provider_reference"] = (
                body.get("external_payment_id")
                or body.get("provider_reference")
                or body.get("session_id")
            )
        else:
            result["status"] = "failed"
            result["failure_reason"] = f"Payment retry webhook returned {response.status_code}: {response.text[:500]}"
    except Exception as error:  # pragma: no cover - network failure shape depends on provider
        result["status"] = "failed"
        result["failure_reason"] = f"Payment retry webhook failed: {error}"
    return result


async def billing_payment_retry_headers(settings: Settings) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    key = await resolve_billing_secret(
        settings,
        env_value=settings.billing_payment_retry_webhook_key,
        path=settings.billing_payment_retry_webhook_key_secret_path,
        field_name=settings.billing_payment_retry_webhook_key_secret_field,
        label="billing payment retry webhook key",
    )
    if key:
        headers["X-Afrolete-Billing-Retry-Key"] = key
    return headers


async def billing_dunning_headers(settings: Settings) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    key = await resolve_billing_secret(
        settings,
        env_value=settings.billing_dunning_webhook_key,
        path=settings.billing_dunning_webhook_key_secret_path,
        field_name=settings.billing_dunning_webhook_key_secret_field,
        label="billing dunning webhook key",
    )
    if key:
        headers["X-Afrolete-Billing-Dunning-Key"] = key
    return headers


async def billing_tax_filing_headers(settings: Settings) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    key = await resolve_billing_secret(
        settings,
        env_value=settings.billing_tax_filing_webhook_key,
        path=settings.billing_tax_filing_webhook_key_secret_path,
        field_name=settings.billing_tax_filing_webhook_key_secret_field,
        label="billing tax filing webhook key",
    )
    if key:
        headers["X-Afrolete-Billing-Tax-Filing-Key"] = key
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


async def validate_payment_webhook_signature(
    raw_body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
    settings: Settings | None = None,
) -> tuple[bool, bool]:
    selected_settings = settings or get_settings()
    signing_key = await resolve_billing_secret(
        selected_settings,
        env_value=selected_settings.billing_payment_webhook_signing_key,
        path=selected_settings.billing_payment_webhook_signing_key_secret_path,
        field_name=selected_settings.billing_payment_webhook_signing_key_secret_field,
        label="billing payment webhook signing key",
    )
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


async def resolve_billing_secret(
    settings: Settings,
    *,
    env_value: str,
    path: str,
    field_name: str,
    label: str,
) -> str:
    return await resolve_secret(
        settings,
        env_value=env_value,
        path=path,
        field_name=field_name,
        label=label,
    )


def saas_invoice_checkout_session_id(invoice: SaaSInvoice, provider: str) -> str:
    token = sha256(f"saas-session:{invoice.id}:{invoice.invoice_number}:{invoice.total}:{provider}".encode()).hexdigest()
    provider_token = "".join(character if character.isalnum() else "-" for character in provider.lower()).strip("-")[:24]
    return f"sbcs_{provider_token or 'processor'}_{token[:24]}"


def saas_invoice_checkout_session_url(
    base_url: str,
    session_id: str,
    invoice: SaaSInvoice,
    provider: str,
) -> str:
    provider_token = quote(provider, safe="")
    return f"{base_url.rstrip('/')}/{session_id}?invoice_id={invoice.id}&provider={provider_token}&kind=saas"


def saas_invoice_open_amount(invoice: SaaSInvoice) -> Decimal:
    return money(max(invoice.total - invoice.amount_paid, Decimal("0.00")))


def saas_invoice_checkout_session_status(invoice: SaaSInvoice) -> str:
    return "paid" if saas_invoice_open_amount(invoice) <= 0 else "ready"


def saas_invoice_hosted_checkout_read(
    invoice: SaaSInvoice,
    provider: str,
    session_id: str,
) -> SaaSInvoiceHostedCheckoutRead:
    open_amount = saas_invoice_open_amount(invoice)
    return SaaSInvoiceHostedCheckoutRead(
        invoice_id=invoice.id,
        invoice_number=invoice.invoice_number,
        organization_id=invoice.organization_id,
        subscription_id=invoice.subscription_id,
        title=f"AfroLete subscription invoice {invoice.invoice_number}",
        memo=invoice.line_items,
        due_on=invoice.due_on,
        amount_due=invoice.total,
        amount_paid=invoice.amount_paid,
        open_amount=open_amount,
        currency=invoice.currency,
        status=invoice.status.value,
        provider=provider,
        session_id=session_id,
        session_status=saas_invoice_checkout_session_status(invoice),
        client_reference=f"saas-invoice-checkout:{invoice.id}",
        payment_methods=["card", "mobile_money", "bank_transfer"],
        settlement_endpoint=f"/api/v1/billing/invoice-checkout-sessions/{session_id}/settle",
        checkout_summary=(
            f"{invoice.invoice_number} has {open_amount} {invoice.currency} outstanding."
            if open_amount > 0
            else f"{invoice.invoice_number} is fully paid."
        ),
    )


def subscription_read(subscription: TenantSubscription):
    return {
        "id": subscription.id,
        "organization_id": subscription.organization_id,
        "billing_plan_id": subscription.billing_plan_id,
        "billing_cycle": subscription.billing_cycle,
        "current_period_start": subscription.current_period_start,
        "current_period_end": subscription.current_period_end,
        "trial_ends_on": subscription.trial_ends_on,
        "next_billing_on": subscription.next_billing_on,
        "seats_purchased": subscription.seats_purchased,
        "negotiated_price": subscription.negotiated_price,
        "discount_code": subscription.discount_code,
        "external_customer_id": subscription.external_customer_id,
        "external_subscription_id": subscription.external_subscription_id,
        "notes": subscription.notes,
        "status": subscription.status,
        "cancel_at_period_end": subscription.cancel_at_period_end,
    }


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


def money(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


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


def filing_currency(invoices: list[SaaSInvoice]) -> str:
    currencies = {invoice.currency for invoice in invoices}
    if len(currencies) == 1:
        return next(iter(currencies))
    return "mixed" if currencies else "USD"


def tax_filing_reference(
    organization_id: UUID,
    jurisdiction: str,
    period_start: date,
    period_end: date,
) -> str:
    return (
        f"TAX-{jurisdiction.upper()}-{str(organization_id)[:8]}-"
        f"{period_start.strftime('%Y%m%d')}-{period_end.strftime('%Y%m%d')}"
    )


def proration_recommendation(net_amount: Decimal) -> str:
    if net_amount > 0:
        return "Charge the prorated upgrade amount on the next invoice."
    if net_amount < 0:
        return "Apply the prorated credit to the next invoice."
    return "No prorated balance is due for this period."


def subscription_plan_change_notes(
    existing: str | None,
    previous_plan_id: UUID,
    new_plan_id: UUID,
    previous_price: Decimal,
    new_price: Decimal,
    net_amount: Decimal,
    effective_on: date,
    note: str | None,
) -> str:
    entry = (
        f"{datetime.now(UTC).date()}: plan change effective {effective_on}; "
        f"plan {previous_plan_id} -> {new_plan_id}; price {previous_price} -> {new_price}; "
        f"proration net {net_amount}."
    )
    if note:
        entry = f"{entry} Note: {note}"
    return "\n".join(part for part in [existing, entry] if part)


def subscription_lifecycle_note(
    existing: str | None,
    action: str,
    previous_status: SubscriptionStatus,
    new_status: SubscriptionStatus,
    effective_on: date,
    reason: str | None,
    cancel_at_period_end: bool,
) -> str:
    entry = (
        f"{datetime.now(UTC).date()}: lifecycle {action} effective {effective_on}; "
        f"status {previous_status.value} -> {new_status.value}; "
        f"cancel_at_period_end={cancel_at_period_end}."
    )
    if reason:
        entry = f"{entry} Reason: {reason}"
    return "\n".join(part for part in [existing, entry] if part)
