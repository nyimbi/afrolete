from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commercial import (
    Donation,
    FinanceInvoice,
    FinancePayment,
    FundraisingCampaign,
    Sponsor,
    SponsorshipAgreement,
    Ticket,
    TicketOrder,
    TicketProduct,
)
from app.models.enums import CommercialStatus, TicketStatus
from app.models.event import Event
from app.models.organization import Organization
from app.models.team import Team
from app.schemas.commercial import (
    CommercialSummaryRead,
    DonationCreate,
    FinanceInvoiceCreate,
    FinancePaymentCreate,
    FundraisingCampaignCreate,
    SponsorCreate,
    SponsorshipAgreementCreate,
    TicketCheckIn,
    TicketOrderCreate,
    TicketProductCreate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService


async def ensure_manage_commercial(
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
    ) or await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage_roster",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def create_sponsor(db: AsyncSession, identity: CurrentIdentity, payload: SponsorCreate, authz: AuthorizationService) -> Sponsor:
    await get_organization(db, payload.organization_id)
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    sponsor = Sponsor(**payload.model_dump())
    db.add(sponsor)
    await db.commit()
    await db.refresh(sponsor)
    return sponsor


async def list_sponsors(db: AsyncSession, organization_id: UUID) -> list[Sponsor]:
    return list((await db.scalars(select(Sponsor).where(Sponsor.organization_id == organization_id).order_by(Sponsor.name))).all())


async def create_sponsorship(db: AsyncSession, identity: CurrentIdentity, payload: SponsorshipAgreementCreate, authz: AuthorizationService) -> SponsorshipAgreement:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    await get_sponsor_for_organization(db, payload.sponsor_id, payload.organization_id)
    if payload.event_id is not None:
        await get_event_for_organization(db, payload.event_id, payload.organization_id)
    agreement = SponsorshipAgreement(**payload.model_dump())
    db.add(agreement)
    await db.commit()
    await db.refresh(agreement)
    return agreement


async def list_sponsorships(db: AsyncSession, organization_id: UUID) -> list[SponsorshipAgreement]:
    return list((await db.scalars(select(SponsorshipAgreement).where(SponsorshipAgreement.organization_id == organization_id).order_by(SponsorshipAgreement.created_at.desc()))).all())


async def create_campaign(db: AsyncSession, identity: CurrentIdentity, payload: FundraisingCampaignCreate, authz: AuthorizationService) -> FundraisingCampaign:
    await get_organization(db, payload.organization_id)
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    campaign = FundraisingCampaign(**payload.model_dump())
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def list_campaigns(db: AsyncSession, organization_id: UUID) -> list[FundraisingCampaign]:
    return list((await db.scalars(select(FundraisingCampaign).where(FundraisingCampaign.organization_id == organization_id).order_by(FundraisingCampaign.created_at.desc()))).all())


async def record_donation(db: AsyncSession, identity: CurrentIdentity, payload: DonationCreate, authz: AuthorizationService) -> Donation:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    campaign = await get_campaign_for_organization(db, payload.campaign_id, payload.organization_id)
    donation = Donation(**payload.model_dump())
    campaign.raised_amount += payload.amount
    if campaign.raised_amount >= campaign.goal_amount:
        campaign.status = CommercialStatus.COMPLETED
    db.add(donation)
    await db.commit()
    await db.refresh(donation)
    return donation


async def create_ticket_product(db: AsyncSession, identity: CurrentIdentity, payload: TicketProductCreate, authz: AuthorizationService) -> TicketProduct:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    await get_event_for_organization(db, payload.event_id, payload.organization_id)
    ticket_product = TicketProduct(**payload.model_dump())
    db.add(ticket_product)
    await db.commit()
    await db.refresh(ticket_product)
    return ticket_product


async def list_ticket_products(db: AsyncSession, organization_id: UUID) -> list[TicketProduct]:
    return list((await db.scalars(select(TicketProduct).where(TicketProduct.organization_id == organization_id).order_by(TicketProduct.created_at.desc()))).all())


async def create_ticket_order(db: AsyncSession, identity: CurrentIdentity, payload: TicketOrderCreate, authz: AuthorizationService) -> tuple[TicketOrder, list[Ticket]]:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    ticket_product = await get_ticket_product_for_organization(db, payload.ticket_product_id, payload.organization_id)
    if ticket_product.sold_count + payload.quantity > ticket_product.capacity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket capacity exceeded")
    order = TicketOrder(
        organization_id=payload.organization_id,
        ticket_product_id=payload.ticket_product_id,
        buyer_name=payload.buyer_name,
        buyer_email=payload.buyer_email,
        quantity=payload.quantity,
        total_amount=ticket_product.price * payload.quantity,
        currency=ticket_product.currency,
        external_payment_reference=payload.external_payment_reference,
    )
    db.add(order)
    await db.flush()
    tickets = [
        Ticket(
            organization_id=payload.organization_id,
            ticket_order_id=order.id,
            ticket_product_id=ticket_product.id,
            holder_name=payload.buyer_name,
            qr_token=f"tkt_{uuid4().hex}",
        )
        for _ in range(payload.quantity)
    ]
    ticket_product.sold_count += payload.quantity
    db.add_all(tickets)
    await db.commit()
    await db.refresh(order)
    return order, tickets


async def list_tickets(db: AsyncSession, organization_id: UUID) -> list[Ticket]:
    return list((await db.scalars(select(Ticket).where(Ticket.organization_id == organization_id).order_by(Ticket.created_at.desc()))).all())


async def check_in_ticket(db: AsyncSession, identity: CurrentIdentity, ticket_id: UUID, payload: TicketCheckIn, authz: AuthorizationService) -> Ticket:
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    await ensure_manage_commercial(authz, identity, ticket.organization_id)
    if ticket.status != TicketStatus.ISSUED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket cannot be checked in")
    ticket.status = TicketStatus.CHECKED_IN
    ticket.checked_in_at = datetime.now(UTC)
    ticket.gate = payload.gate
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def create_invoice(db: AsyncSession, identity: CurrentIdentity, payload: FinanceInvoiceCreate, authz: AuthorizationService) -> FinanceInvoice:
    await get_organization(db, payload.organization_id)
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    if payload.sponsor_id is not None:
        await get_sponsor_for_organization(db, payload.sponsor_id, payload.organization_id)
    invoice = FinanceInvoice(**payload.model_dump())
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


async def list_invoices(db: AsyncSession, organization_id: UUID) -> list[FinanceInvoice]:
    return list((await db.scalars(select(FinanceInvoice).where(FinanceInvoice.organization_id == organization_id).order_by(FinanceInvoice.created_at.desc()))).all())


async def record_payment(db: AsyncSession, identity: CurrentIdentity, payload: FinancePaymentCreate, authz: AuthorizationService) -> FinancePayment:
    await ensure_manage_commercial(authz, identity, payload.organization_id)
    invoice = await get_invoice_for_organization(db, payload.invoice_id, payload.organization_id)
    payment = FinancePayment(received_at=datetime.now(UTC), **payload.model_dump())
    invoice.amount_paid += payload.amount
    invoice.status = CommercialStatus.PAID if invoice.amount_paid >= invoice.amount_due else CommercialStatus.PARTIAL
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def commercial_summary(db: AsyncSession, organization_id: UUID) -> CommercialSummaryRead:
    sponsors = await list_sponsors(db, organization_id)
    sponsorships = await list_sponsorships(db, organization_id)
    campaigns = await list_campaigns(db, organization_id)
    ticket_products = await list_ticket_products(db, organization_id)
    tickets = await list_tickets(db, organization_id)
    invoices = await list_invoices(db, organization_id)
    return CommercialSummaryRead(
        organization_id=organization_id,
        sponsorship_value=sum((item.value_amount for item in sponsorships), Decimal("0")),
        fundraising_goal=sum((item.goal_amount for item in campaigns), Decimal("0")),
        fundraising_raised=sum((item.raised_amount for item in campaigns), Decimal("0")),
        ticket_revenue=sum((item.price * item.sold_count for item in ticket_products), Decimal("0")),
        invoice_outstanding=sum((item.amount_due - item.amount_paid for item in invoices), Decimal("0")),
        active_sponsors=len(sponsors),
        active_campaigns=sum(1 for item in campaigns if item.status == CommercialStatus.ACTIVE),
        tickets_sold=len(tickets),
        tickets_checked_in=sum(1 for ticket in tickets if ticket.status == TicketStatus.CHECKED_IN),
    )


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def get_sponsor_for_organization(db: AsyncSession, sponsor_id: UUID, organization_id: UUID) -> Sponsor:
    sponsor = await db.get(Sponsor, sponsor_id)
    if sponsor is None or sponsor.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor not found")
    return sponsor


async def get_campaign_for_organization(db: AsyncSession, campaign_id: UUID, organization_id: UUID) -> FundraisingCampaign:
    campaign = await db.get(FundraisingCampaign, campaign_id)
    if campaign is None or campaign.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


async def get_ticket_product_for_organization(db: AsyncSession, ticket_product_id: UUID, organization_id: UUID) -> TicketProduct:
    ticket_product = await db.get(TicketProduct, ticket_product_id)
    if ticket_product is None or ticket_product.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket product not found")
    return ticket_product


async def get_invoice_for_organization(db: AsyncSession, invoice_id: UUID, organization_id: UUID) -> FinanceInvoice:
    invoice = await db.get(FinanceInvoice, invoice_id)
    if invoice is None or invoice.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


async def get_team_for_organization(db: AsyncSession, team_id: UUID, organization_id: UUID) -> Team:
    team = await db.get(Team, team_id)
    if team is None or team.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


async def get_event_for_organization(db: AsyncSession, event_id: UUID, organization_id: UUID) -> Event:
    event = await db.get(Event, event_id)
    if event is None or event.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event
