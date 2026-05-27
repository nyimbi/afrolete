from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import CommercialStatus, TicketStatus


class SponsorCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    industry: str | None = Field(default=None, max_length=120)
    contact_name: str | None = Field(default=None, max_length=180)
    contact_email: str | None = Field(default=None, max_length=320)
    website_url: str | None = Field(default=None, max_length=500)
    brand_assets_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)


class SponsorRead(SponsorCreate):
    id: UUID


class SponsorshipAgreementCreate(BaseModel):
    organization_id: UUID
    sponsor_id: UUID
    event_id: UUID | None = None
    name: str = Field(min_length=2, max_length=220)
    tier: str = Field(min_length=2, max_length=80)
    value_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    starts_on: date | None = None
    ends_on: date | None = None
    deliverables: str | None = Field(default=None, max_length=4000)
    activation_notes: str | None = Field(default=None, max_length=4000)
    roi_notes: str | None = Field(default=None, max_length=4000)


class SponsorshipAgreementRead(SponsorshipAgreementCreate):
    id: UUID
    status: CommercialStatus


class FundraisingCampaignCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    name: str = Field(min_length=2, max_length=220)
    purpose: str = Field(min_length=2, max_length=240)
    goal_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    starts_on: date | None = None
    ends_on: date | None = None
    public_url: str | None = Field(default=None, max_length=500)


class FundraisingCampaignRead(FundraisingCampaignCreate):
    id: UUID
    raised_amount: Decimal
    status: CommercialStatus


class DonationCreate(BaseModel):
    organization_id: UUID
    campaign_id: UUID
    donor_name: str = Field(min_length=2, max_length=180)
    donor_email: str | None = Field(default=None, max_length=320)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    external_reference: str | None = Field(default=None, max_length=240)
    message: str | None = Field(default=None, max_length=4000)


class DonationRead(DonationCreate):
    id: UUID
    status: CommercialStatus


class TicketProductCreate(BaseModel):
    organization_id: UUID
    event_id: UUID
    name: str = Field(min_length=2, max_length=180)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    capacity: int = Field(ge=1)
    access_zone: str | None = Field(default=None, max_length=120)


class TicketProductRead(TicketProductCreate):
    id: UUID
    sold_count: int
    status: CommercialStatus


class TicketOrderCreate(BaseModel):
    organization_id: UUID
    ticket_product_id: UUID
    buyer_name: str = Field(min_length=2, max_length=180)
    buyer_email: str = Field(min_length=3, max_length=320)
    quantity: int = Field(ge=1, le=100)
    external_payment_reference: str | None = Field(default=None, max_length=240)


class TicketOrderRead(BaseModel):
    id: UUID
    organization_id: UUID
    ticket_product_id: UUID
    buyer_name: str
    buyer_email: str
    quantity: int
    total_amount: Decimal
    currency: str
    external_payment_reference: str | None
    status: CommercialStatus
    ticket_ids: list[UUID]


class TicketRead(BaseModel):
    id: UUID
    organization_id: UUID
    ticket_order_id: UUID
    ticket_product_id: UUID
    holder_name: str | None
    qr_token: str
    status: TicketStatus
    checked_in_at: datetime | None
    gate: str | None


class TicketCheckIn(BaseModel):
    gate: str | None = Field(default=None, max_length=80)


class FinanceInvoiceCreate(BaseModel):
    organization_id: UUID
    person_id: UUID | None = None
    team_id: UUID | None = None
    sponsor_id: UUID | None = None
    invoice_number: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=220)
    amount_due: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    due_on: date | None = None
    memo: str | None = Field(default=None, max_length=4000)


class FinanceInvoiceRead(FinanceInvoiceCreate):
    id: UUID
    amount_paid: Decimal
    status: CommercialStatus


class FinancePaymentCreate(BaseModel):
    organization_id: UUID
    invoice_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    method: str = Field(min_length=2, max_length=80)
    external_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)


class FinancePaymentRead(FinancePaymentCreate):
    id: UUID
    received_at: datetime


class CommercialSummaryRead(BaseModel):
    organization_id: UUID
    sponsorship_value: Decimal
    fundraising_goal: Decimal
    fundraising_raised: Decimal
    ticket_revenue: Decimal
    invoice_outstanding: Decimal
    active_sponsors: int
    active_campaigns: int
    tickets_sold: int
    tickets_checked_in: int
