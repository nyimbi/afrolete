from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import BillingCycle, BillingInvoiceStatus, SubscriptionStatus, UsageUnit


class BillingPlanCreate(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    base_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    included_athletes: int = Field(default=0, ge=0)
    included_teams: int = Field(default=0, ge=0)
    included_agent_tasks: int = Field(default=0, ge=0)
    included_storage_gb: int = Field(default=0, ge=0)
    per_athlete_price: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    per_agent_task_price: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    features: str | None = Field(default=None, max_length=8000)


class BillingPlanRead(BillingPlanCreate):
    id: UUID
    status: str


class SubscriptionCreate(BaseModel):
    organization_id: UUID
    billing_plan_id: UUID
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    current_period_start: date
    current_period_end: date
    trial_ends_on: date | None = None
    next_billing_on: date | None = None
    seats_purchased: int = Field(default=0, ge=0)
    negotiated_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    discount_code: str | None = Field(default=None, max_length=80)
    external_customer_id: str | None = Field(default=None, max_length=180)
    external_subscription_id: str | None = Field(default=None, max_length=180)
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def valid_period(self) -> "SubscriptionCreate":
        if self.current_period_end < self.current_period_start:
            raise ValueError("current_period_end must be on or after current_period_start")
        return self


class SubscriptionRead(SubscriptionCreate):
    id: UUID
    status: SubscriptionStatus
    cancel_at_period_end: bool


class UsageMeterCreate(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=160)
    unit: UsageUnit
    included_quantity: int = Field(default=0, ge=0)
    overage_price: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=4)
    aggregation: str = Field(default="sum", max_length=40)


class UsageMeterRead(UsageMeterCreate):
    id: UUID
    status: str


class UsageRecordCreate(BaseModel):
    organization_id: UUID
    subscription_id: UUID
    usage_meter_id: UUID
    quantity: int = Field(ge=0)
    source: str = Field(default="manual", max_length=120)
    external_reference: str | None = Field(default=None, max_length=180)
    notes: str | None = Field(default=None, max_length=4000)


class UsageRecordRead(UsageRecordCreate):
    id: UUID
    recorded_at: datetime


class SaaSInvoiceCreate(BaseModel):
    organization_id: UUID
    subscription_id: UUID
    invoice_number: str = Field(min_length=2, max_length=80)
    period_start: date
    period_end: date
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    due_on: date | None = None


class SaaSInvoiceRead(BaseModel):
    id: UUID
    organization_id: UUID
    subscription_id: UUID
    invoice_number: str
    period_start: date
    period_end: date
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    amount_paid: Decimal
    currency: str
    due_on: date | None
    status: BillingInvoiceStatus
    line_items: str | None
    external_invoice_id: str | None


class SaaSPaymentCreate(BaseModel):
    organization_id: UUID
    invoice_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    provider: str = Field(default="manual", min_length=2, max_length=80)
    external_payment_id: str | None = Field(default=None, max_length=180)
    notes: str | None = Field(default=None, max_length=4000)


class SaaSPaymentRead(SaaSPaymentCreate):
    id: UUID
    currency: str
    received_at: datetime
    status: str


class BillingTaxQuoteRead(BaseModel):
    organization_id: UUID
    jurisdiction: str
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    reverse_charge: bool
    filing_hint: str


class BillingProrationQuoteRead(BaseModel):
    organization_id: UUID
    subscription_id: UUID
    current_price: Decimal
    new_price: Decimal
    effective_on: date
    period_start: date
    period_end: date
    remaining_days: int
    total_days: int
    unused_credit: Decimal
    new_charge: Decimal
    net_amount: Decimal
    recommendation: str


class BillingDunningNoticeRead(BaseModel):
    organization_id: UUID
    invoice_id: UUID
    invoice_number: str
    days_overdue: int
    amount_due: Decimal
    severity: str
    channel: str
    message: str
    next_action: str


class BillingDunningDeliveryRead(BillingDunningNoticeRead):
    delivery_mode: str
    delivery_attempted: bool
    delivered: bool
    destination: str | None
    provider_status_code: int | None
    failure_reason: str | None
    delivered_at: datetime


class BillingPaymentWebhookCreate(BaseModel):
    organization_id: UUID
    invoice_id: UUID
    provider: str = Field(min_length=2, max_length=80)
    event_type: str = Field(min_length=2, max_length=120)
    status: str = Field(default="succeeded", min_length=2, max_length=40)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    external_payment_id: str = Field(min_length=2, max_length=180)
    raw_reference: str | None = Field(default=None, max_length=500)


class BillingPaymentWebhookRead(BaseModel):
    organization_id: UUID
    invoice_id: UUID
    provider: str
    event_type: str
    accepted: bool
    signature_required: bool
    signature_validated: bool
    payment_id: UUID | None
    invoice_status: BillingInvoiceStatus
    amount_paid: Decimal
    message: str


class BillingEntitlementCreate(BaseModel):
    organization_id: UUID
    subscription_id: UUID
    feature_key: str = Field(min_length=2, max_length=120)
    limit_value: int | None = Field(default=None, ge=0)
    used_value: int = Field(default=0, ge=0)
    resets_on: date | None = None


class BillingEntitlementRead(BillingEntitlementCreate):
    id: UUID
    status: str


class BillingSummaryRead(BaseModel):
    organization_id: UUID
    active_subscriptions: int
    plans: int
    usage_meters: int
    usage_records: int
    open_invoices: int
    monthly_recurring_revenue: Decimal
    invoice_outstanding: Decimal
    entitlements: int
