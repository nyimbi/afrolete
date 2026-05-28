from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
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
    AccountingExportRead,
    AccountingExportRow,
    CommercialSummaryRead,
    CommercialRefundCreate,
    CommercialRefundRead,
    DonationCreate,
    FinanceInvoiceCreate,
    FinancePaymentCreate,
    FundraisingCampaignCreate,
    PaymentSettlementRead,
    SponsorCreate,
    SponsorPortalAgreementRead,
    SponsorPortalInvoiceRead,
    SponsorPortalRead,
    SponsorPortalSponsorRead,
    SponsorPortalSummaryRead,
    SponsorshipDashboardRead,
    SponsorshipAgreementCreate,
    TaxQuoteRead,
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


async def refund_ticket(
    db: AsyncSession,
    identity: CurrentIdentity,
    ticket_id: UUID,
    payload: CommercialRefundCreate,
    authz: AuthorizationService,
) -> CommercialRefundRead:
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    await ensure_manage_commercial(authz, identity, ticket.organization_id)
    if ticket.status == TicketStatus.REFUNDED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket already refunded")
    order = await db.get(TicketOrder, ticket.ticket_order_id)
    product = await db.get(TicketProduct, ticket.ticket_product_id)
    if order is None or product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket order not found")

    refund_amount = payload.amount or product.price
    ticket.status = TicketStatus.REFUNDED
    product.sold_count = max(product.sold_count - 1, 0)
    remaining_issued = await tickets_remaining_in_order(db, order.id, excluding_ticket_id=ticket.id)
    order.status = CommercialStatus.CANCELLED if remaining_issued == 0 else CommercialStatus.PARTIAL
    await db.commit()
    await db.refresh(ticket)
    return CommercialRefundRead(
        refund_id=f"refund_{uuid4().hex}",
        organization_id=ticket.organization_id,
        target_type="ticket",
        target_id=ticket.id,
        amount=refund_amount,
        currency=order.currency,
        reason=payload.reason,
        status="processed",
        external_reference=payload.external_reference,
    )


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


async def refund_invoice(
    db: AsyncSession,
    identity: CurrentIdentity,
    invoice_id: UUID,
    payload: CommercialRefundCreate,
    authz: AuthorizationService,
) -> CommercialRefundRead:
    invoice = await get_invoice_for_organization_by_id(db, invoice_id)
    await ensure_manage_commercial(authz, identity, invoice.organization_id)
    refund_amount = payload.amount or invoice.amount_paid
    if refund_amount <= 0 or refund_amount > invoice.amount_paid:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid refund amount")
    invoice.amount_paid -= refund_amount
    invoice.status = (
        CommercialStatus.PAID
        if invoice.amount_paid >= invoice.amount_due
        else CommercialStatus.PARTIAL
        if invoice.amount_paid > 0
        else CommercialStatus.ACTIVE
    )
    await db.commit()
    await db.refresh(invoice)
    return CommercialRefundRead(
        refund_id=f"refund_{uuid4().hex}",
        organization_id=invoice.organization_id,
        target_type="invoice",
        target_id=invoice.id,
        amount=refund_amount,
        currency=invoice.currency,
        reason=payload.reason,
        status="processed",
        external_reference=payload.external_reference,
    )


async def tax_quote(
    db: AsyncSession,
    organization_id: UUID,
    subtotal: Decimal,
    tax_rate: Decimal,
    jurisdiction: str,
    reverse_charge: bool = False,
) -> TaxQuoteRead:
    await get_organization(db, organization_id)
    effective_rate = Decimal("0") if reverse_charge else tax_rate
    tax_amount = (subtotal * effective_rate / Decimal("100")).quantize(Decimal("0.01"))
    return TaxQuoteRead(
        organization_id=organization_id,
        jurisdiction=jurisdiction,
        subtotal=subtotal.quantize(Decimal("0.01")),
        tax_rate=effective_rate,
        tax_amount=tax_amount,
        total=(subtotal + tax_amount).quantize(Decimal("0.01")),
        reverse_charge=reverse_charge,
        rationale="Tax estimate for checkout, invoicing, and donation receipt review.",
    )


async def payment_settlement(
    db: AsyncSession,
    organization_id: UUID,
    provider: str,
    fee_rate: Decimal,
    fixed_fee: Decimal,
) -> PaymentSettlementRead:
    await get_organization(db, organization_id)
    ticket_products = await list_ticket_products(db, organization_id)
    payments = await list_payments(db, organization_id)
    donations = await list_donations(db, organization_id)
    gross_ticket_revenue = sum((item.price * item.sold_count for item in ticket_products), Decimal("0"))
    gross_invoice_payments = sum((payment.amount for payment in payments), Decimal("0"))
    gross_donations = sum((donation.amount for donation in donations), Decimal("0"))
    gross_amount = gross_ticket_revenue + gross_invoice_payments + gross_donations
    line_count = len(ticket_products) + len(payments) + len(donations)
    fee_amount = ((gross_amount * fee_rate / Decimal("100")) + (fixed_fee * line_count)).quantize(Decimal("0.01"))
    return PaymentSettlementRead(
        organization_id=organization_id,
        provider=provider,
        currency="USD",
        gross_ticket_revenue=gross_ticket_revenue.quantize(Decimal("0.01")),
        gross_invoice_payments=gross_invoice_payments.quantize(Decimal("0.01")),
        gross_donations=gross_donations.quantize(Decimal("0.01")),
        gross_amount=gross_amount.quantize(Decimal("0.01")),
        fee_amount=fee_amount,
        net_amount=(gross_amount - fee_amount).quantize(Decimal("0.01")),
        payout_reference=f"SETTLE-{datetime.now(UTC).strftime('%Y%m%d')}-{str(organization_id)[:8]}",
        line_count=line_count,
    )


async def accounting_export(
    db: AsyncSession,
    organization_id: UUID,
    system: str,
    basis: str,
) -> AccountingExportRead:
    await get_organization(db, organization_id)
    rows: list[AccountingExportRow] = []
    for payment in await list_payments(db, organization_id):
        rows.append(
            AccountingExportRow(
                row_type="invoice_payment",
                source_id=payment.id,
                account_code="1000:cash",
                memo=payment.notes or payment.method,
                debit=payment.amount,
                credit=Decimal("0"),
                currency=payment.currency,
                external_reference=payment.external_reference,
            )
        )
        rows.append(
            AccountingExportRow(
                row_type="invoice_revenue",
                source_id=payment.id,
                account_code="4100:program_revenue",
                memo=payment.notes or payment.method,
                debit=Decimal("0"),
                credit=payment.amount,
                currency=payment.currency,
                external_reference=payment.external_reference,
            )
        )
    for donation in await list_donations(db, organization_id):
        rows.append(
            AccountingExportRow(
                row_type="donation_revenue",
                source_id=donation.id,
                account_code="4200:donations",
                memo=donation.message or donation.donor_name,
                debit=Decimal("0"),
                credit=donation.amount,
                currency=donation.currency,
                external_reference=donation.external_reference,
            )
        )
    debit_total = sum((row.debit for row in rows), Decimal("0"))
    credit_total = sum((row.credit for row in rows), Decimal("0"))
    return AccountingExportRead(
        organization_id=organization_id,
        basis=basis,
        system=system,
        rows=rows,
        debit_total=debit_total.quantize(Decimal("0.01")),
        credit_total=credit_total.quantize(Decimal("0.01")),
    )


async def sponsorship_dashboard(db: AsyncSession, organization_id: UUID) -> list[SponsorshipDashboardRead]:
    sponsors = await list_sponsors(db, organization_id)
    agreements = await list_sponsorships(db, organization_id)
    dashboards = []
    for sponsor in sponsors:
        sponsor_agreements = [agreement for agreement in agreements if agreement.sponsor_id == sponsor.id]
        contracted_value = sum((agreement.value_amount for agreement in sponsor_agreements), Decimal("0"))
        active_value = sum(
            (agreement.value_amount for agreement in sponsor_agreements if agreement.status == CommercialStatus.ACTIVE),
            Decimal("0"),
        )
        deliverable_count = sum(count_deliverables(agreement.deliverables) for agreement in sponsor_agreements)
        activation_count = sum(1 for agreement in sponsor_agreements if agreement.activation_notes)
        roi_score = min(100, int((active_value / contracted_value * 70) if contracted_value else 0) + min(deliverable_count * 5, 20) + min(activation_count * 10, 10))
        dashboards.append(
            SponsorshipDashboardRead(
                sponsor_id=sponsor.id,
                sponsor_name=sponsor.name,
                agreement_count=len(sponsor_agreements),
                contracted_value=contracted_value.quantize(Decimal("0.01")),
                active_value=active_value.quantize(Decimal("0.01")),
                deliverable_count=deliverable_count,
                activation_count=activation_count,
                roi_score=roi_score,
                recommendation=sponsorship_recommendation(roi_score),
            )
        )
    return dashboards


async def sponsor_portal(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID | None = None,
) -> SponsorPortalRead:
    email = identity.email.strip().casefold()
    if not email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sponsor email required")

    sponsor_query = select(Sponsor).where(func.lower(Sponsor.contact_email) == email)
    if organization_id is not None:
        sponsor_query = sponsor_query.where(Sponsor.organization_id == organization_id)
    sponsors = list((await db.scalars(sponsor_query.order_by(Sponsor.name))).all())
    if not sponsors:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor portal not found")

    organization_ids = {sponsor.organization_id for sponsor in sponsors}
    organizations = {
        organization.id: organization
        for organization in (
            await db.scalars(select(Organization).where(Organization.id.in_(organization_ids)))
        ).all()
    }
    sponsor_ids = [sponsor.id for sponsor in sponsors]
    agreements = list(
        (
            await db.scalars(
                select(SponsorshipAgreement)
                .where(SponsorshipAgreement.sponsor_id.in_(sponsor_ids))
                .order_by(SponsorshipAgreement.created_at.desc())
            )
        ).all()
    )
    invoices = list(
        (
            await db.scalars(
                select(FinanceInvoice)
                .where(FinanceInvoice.sponsor_id.in_(sponsor_ids))
                .order_by(FinanceInvoice.due_on.is_(None), FinanceInvoice.due_on, FinanceInvoice.created_at.desc())
            )
        ).all()
    )
    event_ids = {agreement.event_id for agreement in agreements if agreement.event_id is not None}
    events = {
        event.id: event
        for event in (
            await db.scalars(select(Event).where(Event.id.in_(event_ids)))
        ).all()
    } if event_ids else {}
    sponsors_by_id = {sponsor.id: sponsor for sponsor in sponsors}

    active_value = sum(
        (agreement.value_amount for agreement in agreements if agreement.status == CommercialStatus.ACTIVE),
        Decimal("0"),
    )
    outstanding_invoice_amount = sum(
        (invoice.amount_due - invoice.amount_paid for invoice in invoices),
        Decimal("0"),
    )
    deliverable_count = sum(count_deliverables(agreement.deliverables) for agreement in agreements)
    activation_count = sum(1 for agreement in agreements if agreement.activation_notes)
    upcoming_event_count = sum(
        1
        for agreement in agreements
        if agreement.event_id in events and utc_datetime(events[agreement.event_id].starts_at) >= datetime.now(UTC)
    )
    roi_score = min(
        100,
        (60 if active_value > 0 else 0)
        + min(deliverable_count * 5, 25)
        + min(activation_count * 10, 15),
    )

    return SponsorPortalRead(
        identity_email=email,
        sponsors=[
            SponsorPortalSponsorRead(
                id=sponsor.id,
                organization_id=sponsor.organization_id,
                organization_name=organizations[sponsor.organization_id].name,
                organization_slug=organizations[sponsor.organization_id].slug,
                sponsor_name=sponsor.name,
                industry=sponsor.industry,
                contact_name=sponsor.contact_name,
                contact_email=sponsor.contact_email,
                website_url=sponsor.website_url,
                brand_assets_url=sponsor.brand_assets_url,
                public_site_path=f"/site/{organizations[sponsor.organization_id].slug}",
            )
            for sponsor in sponsors
            if sponsor.organization_id in organizations
        ],
        agreements=[
            SponsorPortalAgreementRead(
                id=agreement.id,
                organization_id=agreement.organization_id,
                organization_name=organizations[agreement.organization_id].name,
                sponsor_id=agreement.sponsor_id,
                sponsor_name=sponsors_by_id[agreement.sponsor_id].name,
                event_id=agreement.event_id,
                event_title=events[agreement.event_id].title if agreement.event_id in events else None,
                event_starts_at=events[agreement.event_id].starts_at if agreement.event_id in events else None,
                event_venue_name=events[agreement.event_id].venue_name if agreement.event_id in events else None,
                name=agreement.name,
                tier=agreement.tier,
                value_amount=agreement.value_amount,
                currency=agreement.currency,
                starts_on=agreement.starts_on,
                ends_on=agreement.ends_on,
                deliverables=split_deliverables(agreement.deliverables),
                activation_notes=agreement.activation_notes,
                roi_notes=agreement.roi_notes,
                status=agreement.status,
            )
            for agreement in agreements
            if agreement.organization_id in organizations and agreement.sponsor_id in sponsors_by_id
        ],
        invoices=[
            SponsorPortalInvoiceRead(
                id=invoice.id,
                organization_id=invoice.organization_id,
                organization_name=organizations[invoice.organization_id].name,
                sponsor_id=invoice.sponsor_id,
                invoice_number=invoice.invoice_number,
                title=invoice.title,
                amount_due=invoice.amount_due,
                amount_paid=invoice.amount_paid,
                outstanding_amount=max(invoice.amount_due - invoice.amount_paid, Decimal("0")),
                currency=invoice.currency,
                due_on=invoice.due_on,
                status=invoice.status,
                memo=invoice.memo,
            )
            for invoice in invoices
            if invoice.organization_id in organizations and invoice.sponsor_id is not None
        ],
        summary=SponsorPortalSummaryRead(
            sponsor_count=len(sponsors),
            agreement_count=len(agreements),
            active_value=active_value.quantize(Decimal("0.01")),
            outstanding_invoice_amount=max(outstanding_invoice_amount, Decimal("0")).quantize(Decimal("0.01")),
            deliverable_count=deliverable_count,
            activation_count=activation_count,
            upcoming_event_count=upcoming_event_count,
            recommendation=sponsorship_recommendation(roi_score),
        ),
    )


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


async def list_donations(db: AsyncSession, organization_id: UUID) -> list[Donation]:
    return list(
        (
            await db.scalars(
                select(Donation)
                .where(Donation.organization_id == organization_id)
                .order_by(Donation.created_at.desc())
            )
        ).all()
    )


async def list_payments(db: AsyncSession, organization_id: UUID) -> list[FinancePayment]:
    return list(
        (
            await db.scalars(
                select(FinancePayment)
                .where(FinancePayment.organization_id == organization_id)
                .order_by(FinancePayment.received_at.desc())
            )
        ).all()
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


async def get_invoice_for_organization_by_id(db: AsyncSession, invoice_id: UUID) -> FinanceInvoice:
    invoice = await db.get(FinanceInvoice, invoice_id)
    if invoice is None:
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


async def tickets_remaining_in_order(
    db: AsyncSession,
    order_id: UUID,
    excluding_ticket_id: UUID,
) -> int:
    tickets = list(
        (
            await db.scalars(
                select(Ticket).where(
                    Ticket.ticket_order_id == order_id,
                    Ticket.id != excluding_ticket_id,
                    Ticket.status != TicketStatus.REFUNDED,
                )
            )
        ).all()
    )
    return len(tickets)


def count_deliverables(deliverables: str | None) -> int:
    return len(split_deliverables(deliverables))


def split_deliverables(deliverables: str | None) -> list[str]:
    if not deliverables:
        return []
    return [part.strip() for part in deliverables.replace("\n", ",").split(",") if part.strip()]


def utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def sponsorship_recommendation(roi_score: int) -> str:
    if roi_score >= 85:
        return "Renew and expand; activation is performing well."
    if roi_score >= 60:
        return "Keep active; add measurable deliverables and conversion tracking."
    return "Needs activation plan and sponsor-facing proof of value."
