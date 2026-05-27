from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
