from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
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
