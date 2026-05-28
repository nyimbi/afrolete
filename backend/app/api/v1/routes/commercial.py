from typing import Any
from datetime import date
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.commercial import (
    AccountingExportRead,
    AccountingSyncRead,
    CommercialInvoiceCheckoutSettlementCreate,
    CommercialInvoiceCheckoutSettlementRead,
    CommercialInvoiceHostedCheckoutRead,
    CommercialSummaryRead,
    CommercialRefundCreate,
    CommercialRefundRead,
    CommercialTaxFilingRead,
    DonationCreate,
    DonationRead,
    FinanceInvoiceCreate,
    FinanceInvoiceRead,
    FinancePaymentCreate,
    FinancePaymentRead,
    FundraisingCampaignCreate,
    FundraisingCampaignRead,
    PaymentSettlementRead,
    SponsorCreate,
    SponsorPortalRead,
    SponsorRead,
    SponsorshipDashboardRead,
    SponsorshipAgreementCreate,
    SponsorshipAgreementRead,
    TaxQuoteRead,
    TicketCheckIn,
    TicketOrderCreate,
    TicketOrderRead,
    TicketProductCreate,
    TicketProductRead,
    TicketRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.commercial import (
    accounting_export,
    check_in_ticket,
    commercial_summary,
    create_campaign,
    create_invoice,
    create_sponsor,
    create_sponsorship,
    create_ticket_order,
    create_ticket_product,
    deliver_commercial_tax_filing,
    get_commercial_invoice_hosted_checkout,
    ingest_commercial_invoice_payment_webhook,
    list_campaigns,
    list_invoices,
    list_sponsors,
    list_sponsorships,
    list_ticket_products,
    list_tickets,
    payment_settlement,
    record_donation,
    record_payment,
    refund_invoice,
    refund_ticket,
    settle_commercial_invoice_checkout,
    sponsor_portal,
    sponsorship_dashboard,
    sync_accounting_export,
    tax_quote,
    validate_commercial_invoice_payment_webhook_signature,
)

router = APIRouter(prefix="/commercial", tags=["commercial"])


def sponsor_read(sponsor) -> SponsorRead:
    return SponsorRead(**fields(sponsor, SponsorRead))


def sponsorship_read(agreement) -> SponsorshipAgreementRead:
    return SponsorshipAgreementRead(**fields(agreement, SponsorshipAgreementRead))


def campaign_read(campaign) -> FundraisingCampaignRead:
    return FundraisingCampaignRead(**fields(campaign, FundraisingCampaignRead))


def donation_read(donation) -> DonationRead:
    return DonationRead(**fields(donation, DonationRead))


def ticket_product_read(product) -> TicketProductRead:
    return TicketProductRead(**fields(product, TicketProductRead))


def ticket_read(ticket) -> TicketRead:
    return TicketRead(**fields(ticket, TicketRead))


def invoice_read(invoice) -> FinanceInvoiceRead:
    return FinanceInvoiceRead(**fields(invoice, FinanceInvoiceRead))


def payment_read(payment) -> FinancePaymentRead:
    return FinancePaymentRead(**fields(payment, FinancePaymentRead))


def order_read(order, tickets) -> TicketOrderRead:
    return TicketOrderRead(
        id=order.id,
        organization_id=order.organization_id,
        ticket_product_id=order.ticket_product_id,
        buyer_name=order.buyer_name,
        buyer_email=order.buyer_email,
        quantity=order.quantity,
        total_amount=order.total_amount,
        currency=order.currency,
        external_payment_reference=order.external_payment_reference,
        status=order.status,
        ticket_ids=[ticket.id for ticket in tickets],
    )


def fields(model, schema_type) -> dict:
    return {name: getattr(model, name) for name in schema_type.model_fields}


@router.post("/sponsors", response_model=SponsorRead, status_code=status.HTTP_201_CREATED)
async def create_sponsor_route(
    payload: SponsorCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorRead:
    return sponsor_read(await create_sponsor(db, identity, payload, authz))


@router.get("/sponsors", response_model=list[SponsorRead])
async def list_sponsors_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorRead]:
    return [sponsor_read(sponsor) for sponsor in await list_sponsors(db, organization_id)]


@router.post("/sponsorships", response_model=SponsorshipAgreementRead, status_code=status.HTTP_201_CREATED)
async def create_sponsorship_route(
    payload: SponsorshipAgreementCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SponsorshipAgreementRead:
    return sponsorship_read(await create_sponsorship(db, identity, payload, authz))


@router.get("/sponsorships", response_model=list[SponsorshipAgreementRead])
async def list_sponsorships_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorshipAgreementRead]:
    return [
        sponsorship_read(agreement)
        for agreement in await list_sponsorships(db, organization_id)
    ]


@router.post("/campaigns", response_model=FundraisingCampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign_route(
    payload: FundraisingCampaignCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FundraisingCampaignRead:
    return campaign_read(await create_campaign(db, identity, payload, authz))


@router.get("/campaigns", response_model=list[FundraisingCampaignRead])
async def list_campaigns_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[FundraisingCampaignRead]:
    return [campaign_read(campaign) for campaign in await list_campaigns(db, organization_id)]


@router.post("/donations", response_model=DonationRead, status_code=status.HTTP_201_CREATED)
async def record_donation_route(
    payload: DonationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DonationRead:
    return donation_read(await record_donation(db, identity, payload, authz))


@router.post("/tickets/products", response_model=TicketProductRead, status_code=status.HTTP_201_CREATED)
async def create_ticket_product_route(
    payload: TicketProductCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TicketProductRead:
    return ticket_product_read(await create_ticket_product(db, identity, payload, authz))


@router.get("/tickets/products", response_model=list[TicketProductRead])
async def list_ticket_products_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[TicketProductRead]:
    return [
        ticket_product_read(product)
        for product in await list_ticket_products(db, organization_id)
    ]


@router.post("/tickets/orders", response_model=TicketOrderRead, status_code=status.HTTP_201_CREATED)
async def create_ticket_order_route(
    payload: TicketOrderCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TicketOrderRead:
    order, tickets = await create_ticket_order(db, identity, payload, authz)
    return order_read(order, tickets)


@router.get("/tickets", response_model=list[TicketRead])
async def list_tickets_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[TicketRead]:
    return [ticket_read(ticket) for ticket in await list_tickets(db, organization_id)]


@router.patch("/tickets/{ticket_id}/check-in", response_model=TicketRead)
async def check_in_ticket_route(
    ticket_id: UUID,
    payload: TicketCheckIn,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TicketRead:
    return ticket_read(await check_in_ticket(db, identity, ticket_id, payload, authz))


@router.post("/tickets/{ticket_id}/refund", response_model=CommercialRefundRead)
async def refund_ticket_route(
    ticket_id: UUID,
    payload: CommercialRefundCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommercialRefundRead:
    return await refund_ticket(db, identity, ticket_id, payload, authz)


@router.post("/invoices", response_model=FinanceInvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice_route(
    payload: FinanceInvoiceCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FinanceInvoiceRead:
    return invoice_read(await create_invoice(db, identity, payload, authz))


@router.get("/invoices", response_model=list[FinanceInvoiceRead])
async def list_invoices_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[FinanceInvoiceRead]:
    return [invoice_read(invoice) for invoice in await list_invoices(db, organization_id)]


@router.get(
    "/invoice-checkout-sessions/{session_id}",
    response_model=CommercialInvoiceHostedCheckoutRead,
)
async def get_commercial_invoice_checkout_session_route(
    session_id: str,
    invoice_id: UUID = Query(),
    provider: str = Query(default="manual_gateway"),
    db: AsyncSession = Depends(get_db),
) -> CommercialInvoiceHostedCheckoutRead:
    return await get_commercial_invoice_hosted_checkout(db, session_id, invoice_id, provider)


@router.post(
    "/invoice-checkout-sessions/{session_id}/settle",
    response_model=CommercialInvoiceCheckoutSettlementRead,
)
async def settle_commercial_invoice_checkout_route(
    session_id: str,
    payload: CommercialInvoiceCheckoutSettlementCreate,
    db: AsyncSession = Depends(get_db),
) -> CommercialInvoiceCheckoutSettlementRead:
    return await settle_commercial_invoice_checkout(db, session_id, payload)


@router.post(
    "/invoice-payment-webhooks",
    response_model=CommercialInvoiceCheckoutSettlementRead,
)
async def commercial_invoice_payment_webhook_route(
    request: Request,
    payload: dict[str, Any],
    provider: str | None = Query(default=None),
    x_afrolete_commercial_timestamp: str | None = Header(
        default=None,
        alias="X-Afrolete-Commercial-Timestamp",
    ),
    x_afrolete_commercial_signature: str | None = Header(
        default=None,
        alias="X-Afrolete-Commercial-Signature",
    ),
    db: AsyncSession = Depends(get_db),
) -> CommercialInvoiceCheckoutSettlementRead:
    signature_required, signature_validated = await validate_commercial_invoice_payment_webhook_signature(
        await request.body(),
        x_afrolete_commercial_timestamp,
        x_afrolete_commercial_signature,
    )
    return await ingest_commercial_invoice_payment_webhook(
        db,
        payload,
        provider_hint=provider,
        signature_required=signature_required,
        signature_validated=signature_validated,
    )


@router.post("/invoices/{invoice_id}/refund", response_model=CommercialRefundRead)
async def refund_invoice_route(
    invoice_id: UUID,
    payload: CommercialRefundCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommercialRefundRead:
    return await refund_invoice(db, identity, invoice_id, payload, authz)


@router.post("/payments", response_model=FinancePaymentRead, status_code=status.HTTP_201_CREATED)
async def record_payment_route(
    payload: FinancePaymentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FinancePaymentRead:
    return payment_read(await record_payment(db, identity, payload, authz))


@router.get("/tax-quote", response_model=TaxQuoteRead)
async def tax_quote_route(
    organization_id: UUID = Query(),
    subtotal: Decimal = Query(ge=0),
    tax_rate: Decimal = Query(default=Decimal("0"), ge=0, le=100),
    jurisdiction: str = Query(default="local"),
    reverse_charge: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> TaxQuoteRead:
    return await tax_quote(db, organization_id, subtotal, tax_rate, jurisdiction, reverse_charge)


@router.post("/tax-filing/deliver", response_model=CommercialTaxFilingRead)
async def deliver_commercial_tax_filing_route(
    organization_id: UUID = Query(),
    period_start: date = Query(),
    period_end: date = Query(),
    jurisdiction: str = Query(default="KE", min_length=2, max_length=8),
    tax_rate: Decimal = Query(default=Decimal("0"), ge=0, le=100),
    reverse_charge: bool = Query(default=False),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommercialTaxFilingRead:
    return await deliver_commercial_tax_filing(
        db,
        identity,
        organization_id,
        period_start,
        period_end,
        jurisdiction,
        tax_rate,
        reverse_charge,
        authz,
    )


@router.get("/settlements", response_model=PaymentSettlementRead)
async def payment_settlement_route(
    organization_id: UUID = Query(),
    provider: str = Query(default="manual"),
    fee_rate: Decimal = Query(default=Decimal("2.90"), ge=0, le=100),
    fixed_fee: Decimal = Query(default=Decimal("0.30"), ge=0),
    db: AsyncSession = Depends(get_db),
) -> PaymentSettlementRead:
    return await payment_settlement(db, organization_id, provider, fee_rate, fixed_fee)


@router.get("/accounting-export", response_model=AccountingExportRead)
async def accounting_export_route(
    organization_id: UUID = Query(),
    system: str = Query(default="generic"),
    basis: str = Query(default="cash"),
    db: AsyncSession = Depends(get_db),
) -> AccountingExportRead:
    return await accounting_export(db, organization_id, system, basis)


@router.post("/accounting-export/sync", response_model=AccountingSyncRead)
async def sync_accounting_export_route(
    organization_id: UUID = Query(),
    system: str = Query(default="generic"),
    basis: str = Query(default="cash"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AccountingSyncRead:
    return await sync_accounting_export(db, identity, organization_id, system, basis, authz)


@router.get("/sponsorship-dashboard", response_model=list[SponsorshipDashboardRead])
async def sponsorship_dashboard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SponsorshipDashboardRead]:
    return await sponsorship_dashboard(db, organization_id)


@router.get("/sponsor-portal", response_model=SponsorPortalRead)
async def sponsor_portal_route(
    organization_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> SponsorPortalRead:
    return await sponsor_portal(db, identity, organization_id)


@router.get("/summary", response_model=CommercialSummaryRead)
async def commercial_summary_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> CommercialSummaryRead:
    return await commercial_summary(db, organization_id)
