from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import CommercialStatus, TicketStatus


class Sponsor(IdMixin, TimestampMixin, Base):
    __tablename__ = "sponsors"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(120), index=True)
    contact_name: Mapped[str | None] = mapped_column(String(180))
    contact_email: Mapped[str | None] = mapped_column(String(320), index=True)
    website_url: Mapped[str | None] = mapped_column(String(500))
    brand_assets_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)


class SponsorshipAgreement(IdMixin, TimestampMixin, Base):
    __tablename__ = "sponsorship_agreements"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    sponsor_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("sponsors.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    tier: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    value_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    starts_on: Mapped[date | None] = mapped_column(index=True)
    ends_on: Mapped[date | None] = mapped_column(index=True)
    deliverables: Mapped[str | None] = mapped_column(Text)
    activation_notes: Mapped[str | None] = mapped_column(Text)
    roi_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.ACTIVE,
        nullable=False,
        index=True,
    )


class FundraisingCampaign(IdMixin, TimestampMixin, Base):
    __tablename__ = "fundraising_campaigns"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(240), nullable=False)
    goal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    raised_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    starts_on: Mapped[date | None] = mapped_column(index=True)
    ends_on: Mapped[date | None] = mapped_column(index=True)
    public_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.ACTIVE,
        nullable=False,
        index=True,
    )


class Donation(IdMixin, TimestampMixin, Base):
    __tablename__ = "donations"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    campaign_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("fundraising_campaigns.id"), index=True)
    donor_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    donor_email: Mapped[str | None] = mapped_column(String(320), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.PAID,
        nullable=False,
        index=True,
    )


class GrantOpportunity(IdMixin, TimestampMixin, Base):
    __tablename__ = "grant_opportunities"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    funder_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    program_name: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    impact_area: Mapped[str] = mapped_column(String(220), nullable=False)
    award_ceiling: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    matching_required: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    opens_on: Mapped[date | None] = mapped_column(index=True)
    due_on: Mapped[date | None] = mapped_column(index=True)
    eligibility_summary: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False, index=True)


class GrantApplication(IdMixin, TimestampMixin, Base):
    __tablename__ = "grant_applications"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    grant_opportunity_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("grant_opportunities.id"), index=True)
    project_title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    awarded_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    submitted_on: Mapped[date | None] = mapped_column(index=True)
    decision_on: Mapped[date | None] = mapped_column(index=True)
    reporting_due_on: Mapped[date | None] = mapped_column(index=True)
    lead_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    narrative: Mapped[str | None] = mapped_column(Text)
    budget_summary: Mapped[str | None] = mapped_column(Text)
    impact_metrics: Mapped[str | None] = mapped_column(Text)
    external_reference: Mapped[str | None] = mapped_column(String(240), index=True)


class GrantReport(IdMixin, TimestampMixin, Base):
    __tablename__ = "grant_reports"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    grant_application_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("grant_applications.id"), index=True)
    report_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    due_on: Mapped[date] = mapped_column(index=True)
    submitted_on: Mapped[date | None] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    narrative: Mapped[str | None] = mapped_column(Text)
    metrics_summary: Mapped[str | None] = mapped_column(Text)
    artifact_url: Mapped[str | None] = mapped_column(String(500))
    external_reference: Mapped[str | None] = mapped_column(String(240), index=True)


class TicketProduct(IdMixin, TimestampMixin, Base):
    __tablename__ = "ticket_products"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    event_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    sold_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    access_zone: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.ACTIVE,
        nullable=False,
        index=True,
    )


class TicketOrder(IdMixin, TimestampMixin, Base):
    __tablename__ = "ticket_orders"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    ticket_product_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("ticket_products.id"), index=True)
    buyer_name: Mapped[str] = mapped_column(String(180), nullable=False)
    buyer_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    external_payment_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.PAID,
        nullable=False,
        index=True,
    )


class Ticket(IdMixin, TimestampMixin, Base):
    __tablename__ = "tickets"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    ticket_order_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("ticket_orders.id"), index=True)
    ticket_product_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("ticket_products.id"), index=True)
    holder_name: Mapped[str | None] = mapped_column(String(180))
    qr_token: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    status: Mapped[TicketStatus] = mapped_column(
        enum_type(TicketStatus),
        default=TicketStatus.ISSUED,
        nullable=False,
        index=True,
    )
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    gate: Mapped[str | None] = mapped_column(String(80))


class FinanceInvoice(IdMixin, TimestampMixin, Base):
    __tablename__ = "finance_invoices"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    sponsor_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("sponsors.id"), index=True)
    invoice_number: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    due_on: Mapped[date | None] = mapped_column(index=True)
    status: Mapped[CommercialStatus] = mapped_column(
        enum_type(CommercialStatus),
        default=CommercialStatus.DRAFT,
        nullable=False,
        index=True,
    )
    memo: Mapped[str | None] = mapped_column(Text)


class FinancePayment(IdMixin, TimestampMixin, Base):
    __tablename__ = "finance_payments"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    invoice_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("finance_invoices.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    method: Mapped[str] = mapped_column(String(80), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class CommercialPaymentSession(IdMixin, TimestampMixin, Base):
    __tablename__ = "commercial_payment_sessions"
    __table_args__ = (UniqueConstraint("organization_id", "provider", "local_session_id"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    invoice_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("finance_invoices.id"), index=True)
    sponsor_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("sponsors.id"), index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(40), default="local", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="local_ready", nullable=False, index=True)
    provider_session_id: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    local_session_id: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    client_reference: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    redirect_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    success_url: Mapped[str | None] = mapped_column(String(800))
    cancel_url: Mapped[str | None] = mapped_column(String(800))
    customer_email: Mapped[str | None] = mapped_column(String(320), index=True)
    payment_method: Mapped[str] = mapped_column(String(80), default="card", nullable=False, index=True)
    webhook_configured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    provider_status_code: Mapped[int | None] = mapped_column(Integer)
    provider_response: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)


class CommercialSettlementPayout(IdMixin, TimestampMixin, Base):
    __tablename__ = "commercial_settlement_payouts"
    __table_args__ = (UniqueConstraint("organization_id", "provider", "payout_batch_reference"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    payout_reference: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    payout_batch_reference: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="prepared", nullable=False, index=True)
    delivery_mode: Mapped[str] = mapped_column(String(40), default="record_only", nullable=False, index=True)
    delivery_attempted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False)
    destination: Mapped[str | None] = mapped_column(String(500))
    provider_status_code: Mapped[int | None] = mapped_column(Integer)
    provider_response: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    processed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    external_event_id: Mapped[str | None] = mapped_column(String(180), index=True)
    callback_payload: Mapped[str | None] = mapped_column(Text)
