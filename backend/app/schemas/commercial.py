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


class CommercialRefundCreate(BaseModel):
    amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    reason: str = Field(min_length=2, max_length=500)
    external_reference: str | None = Field(default=None, max_length=240)


class CommercialRefundRead(BaseModel):
    refund_id: str
    organization_id: UUID
    target_type: str
    target_id: UUID
    amount: Decimal
    currency: str
    reason: str
    status: str
    external_reference: str | None


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


class TaxQuoteRead(BaseModel):
    organization_id: UUID
    jurisdiction: str
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    reverse_charge: bool = False
    rationale: str


class PaymentSettlementRead(BaseModel):
    organization_id: UUID
    provider: str
    currency: str
    gross_ticket_revenue: Decimal
    gross_invoice_payments: Decimal
    gross_donations: Decimal
    gross_amount: Decimal
    fee_amount: Decimal
    net_amount: Decimal
    payout_reference: str
    line_count: int


class AccountingExportRow(BaseModel):
    row_type: str
    source_id: UUID
    account_code: str
    memo: str
    debit: Decimal
    credit: Decimal
    currency: str
    external_reference: str | None


class AccountingExportRead(BaseModel):
    organization_id: UUID
    basis: str
    system: str
    rows: list[AccountingExportRow]
    debit_total: Decimal
    credit_total: Decimal


class SponsorshipDashboardRead(BaseModel):
    sponsor_id: UUID
    sponsor_name: str
    agreement_count: int
    contracted_value: Decimal
    active_value: Decimal
    deliverable_count: int
    activation_count: int
    roi_score: int
    recommendation: str


class SponsorPortalSponsorRead(BaseModel):
    id: UUID
    organization_id: UUID
    organization_name: str
    organization_slug: str
    sponsor_name: str
    industry: str | None
    contact_name: str | None
    contact_email: str | None
    website_url: str | None
    brand_assets_url: str | None
    public_site_path: str


class SponsorPortalAgreementRead(BaseModel):
    id: UUID
    organization_id: UUID
    organization_name: str
    sponsor_id: UUID
    sponsor_name: str
    event_id: UUID | None
    event_title: str | None
    event_starts_at: datetime | None
    event_venue_name: str | None
    name: str
    tier: str
    value_amount: Decimal
    currency: str
    starts_on: date | None
    ends_on: date | None
    deliverables: list[str] = Field(default_factory=list)
    activation_notes: str | None
    roi_notes: str | None
    status: CommercialStatus


class SponsorPortalInvoiceRead(BaseModel):
    id: UUID
    organization_id: UUID
    organization_name: str
    sponsor_id: UUID
    invoice_number: str
    title: str
    amount_due: Decimal
    amount_paid: Decimal
    outstanding_amount: Decimal
    currency: str
    due_on: date | None
    status: CommercialStatus
    memo: str | None


class SponsorPortalSummaryRead(BaseModel):
    sponsor_count: int
    agreement_count: int
    active_value: Decimal
    outstanding_invoice_amount: Decimal
    deliverable_count: int
    activation_count: int
    upcoming_event_count: int
    recommendation: str


class SponsorPortalRead(BaseModel):
    identity_email: str
    sponsors: list[SponsorPortalSponsorRead]
    agreements: list[SponsorPortalAgreementRead]
    invoices: list[SponsorPortalInvoiceRead]
    summary: SponsorPortalSummaryRead


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
