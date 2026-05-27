from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.commercial import (
    CommercialSummaryRead,
    DonationCreate,
    DonationRead,
    FinanceInvoiceCreate,
    FinanceInvoiceRead,
    FinancePaymentCreate,
    FinancePaymentRead,
    FundraisingCampaignCreate,
    FundraisingCampaignRead,
    SponsorCreate,
    SponsorRead,
    SponsorshipAgreementCreate,
    SponsorshipAgreementRead,
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
    check_in_ticket,
    commercial_summary,
    create_campaign,
    create_invoice,
    create_sponsor,
    create_sponsorship,
    create_ticket_order,
    create_ticket_product,
    list_campaigns,
    list_invoices,
    list_sponsors,
    list_sponsorships,
    list_ticket_products,
    list_tickets,
    record_donation,
    record_payment,
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


@router.post("/payments", response_model=FinancePaymentRead, status_code=status.HTTP_201_CREATED)
async def record_payment_route(
    payload: FinancePaymentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FinancePaymentRead:
    return payment_read(await record_payment(db, identity, payload, authz))


@router.get("/summary", response_model=CommercialSummaryRead)
async def commercial_summary_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> CommercialSummaryRead:
    return await commercial_summary(db, organization_id)
