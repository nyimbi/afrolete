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
    CommercialInvoiceProviderCheckoutCreate,
    CommercialInvoiceProviderCheckoutRead,
    CommercialRefundCreate,
    CommercialRefundRead,
    CommercialSettlementPayoutCallbackCreate,
    CommercialSettlementPayoutCallbackRead,
    CommercialSettlementPayoutRead,
    CommercialTaxFilingRead,
    DonationCreate,
    DonationRead,
    FinanceInvoiceCreate,
    FinanceInvoiceRead,
    FinancePaymentCreate,
    FinancePaymentRead,
    FundraisingCampaignCreate,
    FundraisingCampaignRead,
    GrantApplicationCreate,
    GrantApplicationRead,
    GrantDashboardRead,
    GrantOpportunityCreate,
    GrantOpportunityRead,
    GrantReportCreate,
    GrantReportRead,
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
    create_grant_application,
    create_grant_opportunity,
    create_grant_report,
    create_invoice,
    create_commercial_invoice_provider_checkout,
    create_sponsor,
    create_sponsorship,
    create_ticket_order,
    create_ticket_product,
    deliver_commercial_tax_filing,
    execute_payment_settlement_payout,
    get_commercial_invoice_hosted_checkout,
    ingest_commercial_invoice_payment_webhook,
    list_commercial_settlement_payouts,
    list_campaigns,
    list_grant_applications,
    list_grant_opportunities,
    list_grant_reports,
    list_invoices,
    list_commercial_payment_sessions,
    list_sponsors,
    list_sponsorships,
    list_ticket_products,
    list_tickets,
    grant_dashboard,
    payment_settlement,
    record_donation,
    record_payment,
    reconcile_commercial_settlement_payout_callback,
    refund_invoice,
    refund_ticket,
    settle_commercial_invoice_checkout,
    sponsor_portal,
    sponsorship_dashboard,
    sync_accounting_export,
    tax_quote,
    validate_commercial_payout_callback_signature,
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


def grant_opportunity_read(opportunity) -> GrantOpportunityRead:
    return GrantOpportunityRead(**fields(opportunity, GrantOpportunityRead))


def grant_application_read(application, opportunity=None) -> GrantApplicationRead:
    return GrantApplicationRead(
        **fields(application, GrantApplicationRead),
        funder_name=opportunity.funder_name if opportunity else None,
        program_name=opportunity.program_name if opportunity else None,
    )


def grant_report_read(report, application=None) -> GrantReportRead:
    return GrantReportRead(
        **fields(report, GrantReportRead),
        project_title=application.project_title if application else None,
    )


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
    return {name: getattr(model, name) for name in schema_type.model_fields if hasattr(model, name)}


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


@router.post("/grants/opportunities", response_model=GrantOpportunityRead, status_code=status.HTTP_201_CREATED)
async def create_grant_opportunity_route(
    payload: GrantOpportunityCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GrantOpportunityRead:
    return grant_opportunity_read(await create_grant_opportunity(db, identity, payload, authz))


@router.get("/grants/opportunities", response_model=list[GrantOpportunityRead])
async def list_grant_opportunities_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[GrantOpportunityRead]:
    return [
        grant_opportunity_read(opportunity)
        for opportunity in await list_grant_opportunities(db, organization_id)
    ]


@router.post("/grants/applications", response_model=GrantApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_grant_application_route(
    payload: GrantApplicationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GrantApplicationRead:
    application = await create_grant_application(db, identity, payload, authz)
    opportunity = await list_grant_opportunities(db, payload.organization_id)
    opportunity_by_id = {item.id: item for item in opportunity}
    return grant_application_read(application, opportunity_by_id.get(application.grant_opportunity_id))


@router.get("/grants/applications", response_model=list[GrantApplicationRead])
async def list_grant_applications_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[GrantApplicationRead]:
    return [
        grant_application_read(application, opportunity)
        for application, opportunity in await list_grant_applications(db, organization_id)
    ]


@router.post("/grants/reports", response_model=GrantReportRead, status_code=status.HTTP_201_CREATED)
async def create_grant_report_route(
    payload: GrantReportCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GrantReportRead:
    report = await create_grant_report(db, identity, payload, authz)
    applications = await list_grant_applications(db, payload.organization_id)
    application_by_id = {application.id: application for application, _ in applications}
    return grant_report_read(report, application_by_id.get(report.grant_application_id))


@router.get("/grants/reports", response_model=list[GrantReportRead])
async def list_grant_reports_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[GrantReportRead]:
    return [
        grant_report_read(report, application)
        for report, application in await list_grant_reports(db, organization_id)
    ]


@router.get("/grants/dashboard", response_model=GrantDashboardRead)
async def grant_dashboard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> GrantDashboardRead:
    return await grant_dashboard(db, organization_id)


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
    "/invoice-checkout-sessions/{session_id}/provider-session",
    response_model=CommercialInvoiceProviderCheckoutRead,
)
async def create_commercial_invoice_provider_checkout_route(
    session_id: str,
    payload: CommercialInvoiceProviderCheckoutCreate,
    invoice_id: UUID = Query(),
    provider: str = Query(default="manual_gateway"),
    db: AsyncSession = Depends(get_db),
) -> CommercialInvoiceProviderCheckoutRead:
    return await create_commercial_invoice_provider_checkout(db, session_id, invoice_id, provider, payload)


@router.get("/payment-sessions", response_model=list[CommercialInvoiceProviderCheckoutRead])
async def list_commercial_payment_sessions_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[CommercialInvoiceProviderCheckoutRead]:
    return await list_commercial_payment_sessions(db, organization_id)


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


@router.post("/settlements/payout", response_model=CommercialSettlementPayoutRead)
async def execute_payment_settlement_payout_route(
    organization_id: UUID = Query(),
    provider: str = Query(default="manual_gateway"),
    fee_rate: Decimal = Query(default=Decimal("2.90"), ge=0, le=100),
    fixed_fee: Decimal = Query(default=Decimal("0.30"), ge=0),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommercialSettlementPayoutRead:
    return await execute_payment_settlement_payout(db, identity, organization_id, provider, fee_rate, fixed_fee, authz)


@router.get("/settlements/payouts", response_model=list[CommercialSettlementPayoutRead])
async def list_commercial_settlement_payouts_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[CommercialSettlementPayoutRead]:
    return await list_commercial_settlement_payouts(db, organization_id)


@router.post("/settlements/payout-callbacks", response_model=CommercialSettlementPayoutCallbackRead)
async def commercial_settlement_payout_callback_route(
    request: Request,
    payload: CommercialSettlementPayoutCallbackCreate,
    x_afrolete_commercial_payout_timestamp: str | None = Header(
        default=None,
        alias="X-Afrolete-Commercial-Payout-Timestamp",
    ),
    x_afrolete_commercial_payout_signature: str | None = Header(
        default=None,
        alias="X-Afrolete-Commercial-Payout-Signature",
    ),
    db: AsyncSession = Depends(get_db),
) -> CommercialSettlementPayoutCallbackRead:
    signature_required, signature_validated = await validate_commercial_payout_callback_signature(
        await request.body(),
        x_afrolete_commercial_payout_timestamp,
        x_afrolete_commercial_payout_signature,
    )
    return await reconcile_commercial_settlement_payout_callback(
        db,
        payload,
        signature_required=signature_required,
        signature_validated=signature_validated,
    )


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
