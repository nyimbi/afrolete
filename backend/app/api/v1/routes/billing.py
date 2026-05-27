from uuid import UUID
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.billing import (
    BillingEntitlementCreate,
    BillingEntitlementRead,
    BillingDunningDeliveryRead,
    BillingDunningNoticeRead,
    BillingPlanChangeCreate,
    BillingPlanChangeRead,
    BillingPaymentWebhookCreate,
    BillingPaymentWebhookRead,
    BillingPlanCreate,
    BillingPlanRead,
    BillingProrationQuoteRead,
    BillingSummaryRead,
    BillingTaxFilingRead,
    BillingTaxQuoteRead,
    SaaSInvoiceCreate,
    SaaSInvoiceRead,
    SaaSPaymentCreate,
    SaaSPaymentRead,
    SubscriptionCreate,
    SubscriptionRead,
    UsageMeterCreate,
    UsageMeterRead,
    UsageRecordCreate,
    UsageRecordRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.billing import (
    billing_summary,
    billing_tax_quote,
    apply_plan_change,
    create_entitlement,
    create_invoice,
    create_plan,
    create_subscription,
    create_usage_meter,
    deliver_dunning_notice,
    deliver_tax_filing,
    dunning_notice,
    ingest_payment_webhook,
    list_entitlements,
    list_invoices,
    list_plans,
    list_subscriptions,
    list_usage_meters,
    list_usage_records,
    record_payment,
    record_usage,
    proration_quote,
    validate_payment_webhook_signature,
)

router = APIRouter(prefix="/billing", tags=["billing"])


def read(model, schema_type):
    return schema_type(**{name: getattr(model, name) for name in schema_type.model_fields})


@router.post("/plans", response_model=BillingPlanRead, status_code=status.HTTP_201_CREATED)
async def create_plan_route(payload: BillingPlanCreate, db: AsyncSession = Depends(get_db)) -> BillingPlanRead:
    return read(await create_plan(db, payload), BillingPlanRead)


@router.get("/plans", response_model=list[BillingPlanRead])
async def list_plans_route(db: AsyncSession = Depends(get_db)) -> list[BillingPlanRead]:
    return [read(plan, BillingPlanRead) for plan in await list_plans(db)]


@router.post("/subscriptions", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_subscription_route(
    payload: SubscriptionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SubscriptionRead:
    return read(await create_subscription(db, identity, payload, authz), SubscriptionRead)


@router.get("/subscriptions", response_model=list[SubscriptionRead])
async def list_subscriptions_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SubscriptionRead]:
    return [read(subscription, SubscriptionRead) for subscription in await list_subscriptions(db, organization_id)]


@router.get("/subscriptions/{subscription_id}/proration", response_model=BillingProrationQuoteRead)
async def proration_route(
    subscription_id: UUID,
    organization_id: UUID = Query(),
    new_price: Decimal = Query(ge=0),
    effective_on: date = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> BillingProrationQuoteRead:
    return BillingProrationQuoteRead(
        **await proration_quote(db, identity, organization_id, subscription_id, new_price, effective_on, authz)
    )


@router.post("/subscriptions/{subscription_id}/plan-change", response_model=BillingPlanChangeRead)
async def apply_plan_change_route(
    subscription_id: UUID,
    payload: BillingPlanChangeCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> BillingPlanChangeRead:
    return BillingPlanChangeRead(
        **await apply_plan_change(db, identity, subscription_id, payload, authz)
    )


@router.post("/meters", response_model=UsageMeterRead, status_code=status.HTTP_201_CREATED)
async def create_meter_route(payload: UsageMeterCreate, db: AsyncSession = Depends(get_db)) -> UsageMeterRead:
    return read(await create_usage_meter(db, payload), UsageMeterRead)


@router.get("/meters", response_model=list[UsageMeterRead])
async def list_meters_route(db: AsyncSession = Depends(get_db)) -> list[UsageMeterRead]:
    return [read(meter, UsageMeterRead) for meter in await list_usage_meters(db)]


@router.post("/usage", response_model=UsageRecordRead, status_code=status.HTTP_201_CREATED)
async def record_usage_route(
    payload: UsageRecordCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> UsageRecordRead:
    return read(await record_usage(db, identity, payload, authz), UsageRecordRead)


@router.get("/usage", response_model=list[UsageRecordRead])
async def list_usage_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[UsageRecordRead]:
    return [read(record, UsageRecordRead) for record in await list_usage_records(db, organization_id)]


@router.post("/invoices", response_model=SaaSInvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice_route(
    payload: SaaSInvoiceCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SaaSInvoiceRead:
    return read(await create_invoice(db, identity, payload, authz), SaaSInvoiceRead)


@router.get("/invoices", response_model=list[SaaSInvoiceRead])
async def list_invoices_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SaaSInvoiceRead]:
    return [read(invoice, SaaSInvoiceRead) for invoice in await list_invoices(db, organization_id)]


@router.post("/invoices/{invoice_id}/dunning", response_model=BillingDunningNoticeRead)
async def dunning_route(
    invoice_id: UUID,
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> BillingDunningNoticeRead:
    return BillingDunningNoticeRead(
        **await dunning_notice(db, identity, organization_id, invoice_id, authz)
    )


@router.post("/invoices/{invoice_id}/dunning/deliver", response_model=BillingDunningDeliveryRead)
async def deliver_dunning_route(
    invoice_id: UUID,
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> BillingDunningDeliveryRead:
    return BillingDunningDeliveryRead(
        **await deliver_dunning_notice(db, identity, organization_id, invoice_id, authz)
    )


@router.post("/payments", response_model=SaaSPaymentRead, status_code=status.HTTP_201_CREATED)
async def record_payment_route(
    payload: SaaSPaymentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SaaSPaymentRead:
    return read(await record_payment(db, identity, payload, authz), SaaSPaymentRead)


@router.post("/webhooks/payments", response_model=BillingPaymentWebhookRead)
async def payment_webhook_route(
    request: Request,
    payload: BillingPaymentWebhookCreate,
    x_afrolete_billing_timestamp: str | None = Header(
        default=None,
        alias="X-Afrolete-Billing-Timestamp",
    ),
    x_afrolete_billing_signature: str | None = Header(
        default=None,
        alias="X-Afrolete-Billing-Signature",
    ),
    db: AsyncSession = Depends(get_db),
) -> BillingPaymentWebhookRead:
    signature_required, signature_validated = await validate_payment_webhook_signature(
        await request.body(),
        x_afrolete_billing_timestamp,
        x_afrolete_billing_signature,
    )
    return BillingPaymentWebhookRead(
        **await ingest_payment_webhook(
            db,
            payload,
            signature_required=signature_required,
            signature_validated=signature_validated,
        )
    )


@router.post("/entitlements", response_model=BillingEntitlementRead, status_code=status.HTTP_201_CREATED)
async def create_entitlement_route(
    payload: BillingEntitlementCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> BillingEntitlementRead:
    return read(await create_entitlement(db, identity, payload, authz), BillingEntitlementRead)


@router.get("/entitlements", response_model=list[BillingEntitlementRead])
async def list_entitlements_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[BillingEntitlementRead]:
    return [read(entitlement, BillingEntitlementRead) for entitlement in await list_entitlements(db, organization_id)]


@router.get("/tax-quote", response_model=BillingTaxQuoteRead)
async def tax_quote_route(
    organization_id: UUID = Query(),
    subtotal: Decimal = Query(ge=0),
    jurisdiction: str = Query(default="KE", min_length=2, max_length=8),
    reverse_charge: bool = Query(default=False),
) -> BillingTaxQuoteRead:
    return BillingTaxQuoteRead(
        **await billing_tax_quote(organization_id, subtotal, jurisdiction, reverse_charge)
    )


@router.post("/tax-filing/deliver", response_model=BillingTaxFilingRead)
async def tax_filing_route(
    organization_id: UUID = Query(),
    period_start: date = Query(),
    period_end: date = Query(),
    jurisdiction: str = Query(default="KE", min_length=2, max_length=8),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> BillingTaxFilingRead:
    return BillingTaxFilingRead(
        **await deliver_tax_filing(
            db,
            identity,
            organization_id,
            period_start,
            period_end,
            jurisdiction,
            authz,
        )
    )


@router.get("/summary", response_model=BillingSummaryRead)
async def summary_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> BillingSummaryRead:
    return BillingSummaryRead(**await billing_summary(db, organization_id))
