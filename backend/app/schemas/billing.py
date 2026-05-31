from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import BillingCycle, BillingInvoiceStatus, SubscriptionStatus, UsageUnit


class BillingPlanCreate(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(
        default=None,
        max_length=4000,
        description="AfroLete hosting plan description for tenant organizations, not member dues.",
    )
    base_price: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Base hosting amount charged to the club, school, association, or tenant organization.",
    )
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
    organization_id: UUID = Field(
        description="Tenant organization that pays AfroLete for platform hosting."
    )
    billing_plan_id: UUID
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    current_period_start: date
    current_period_end: date
    trial_ends_on: date | None = None
    next_billing_on: date | None = None
    seats_purchased: int = Field(
        default=0,
        ge=0,
        description="Tenant-paid platform seats or capacity; this is not a member receivable.",
    )
    negotiated_price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Negotiated AfroLete hosting price paid by the tenant organization.",
    )
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
    organization_id: UUID = Field(description="Tenant organization responsible for this AfroLete hosting invoice.")
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
    dunning_count: int
    dunning_last_sent_at: datetime | None
    dunning_last_severity: str | None
    late_fee_total: Decimal
    late_fee_count: int
    late_fee_last_applied_on: date | None
    payment_retry_count: int
    payment_retry_last_attempted_at: datetime | None
    payment_retry_next_attempt_at: datetime | None
    payment_retry_last_status: str | None
    payment_retry_last_failure_reason: str | None
    payment_retry_last_provider_reference: str | None


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


class SaaSInvoiceHostedCheckoutRead(BaseModel):
    invoice_id: UUID
    invoice_number: str
    organization_id: UUID
    subscription_id: UUID
    title: str
    memo: str | None
    due_on: date | None
    amount_due: Decimal
    amount_paid: Decimal
    open_amount: Decimal
    currency: str
    status: str
    provider: str
    session_id: str
    session_status: str
    client_reference: str
    payment_methods: list[str]
    settlement_endpoint: str
    checkout_summary: str


class SaaSInvoiceCheckoutLinkRead(BaseModel):
    invoice_id: UUID
    provider: str
    session_id: str
    checkout_url: str
    hosted_checkout: SaaSInvoiceHostedCheckoutRead


class SaaSInvoiceCheckoutSettlementCreate(BaseModel):
    invoice_id: UUID
    provider: str = Field(default="manual_gateway", min_length=2, max_length=80)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    method: str = Field(default="hosted_payment_page", min_length=2, max_length=80)
    external_payment_id: str | None = Field(default=None, max_length=240)
    status: str = Field(default="succeeded", pattern="^(succeeded|pending|failed|cancelled)$")
    raw_reference: str | None = Field(default=None, max_length=2000)


class SaaSInvoiceCheckoutSettlementRead(BaseModel):
    invoice_id: UUID
    provider: str
    accepted: bool
    signature_required: bool = False
    signature_validated: bool = False
    payment_id: UUID | None
    invoice_status: BillingInvoiceStatus
    amount_paid: Decimal
    open_amount: Decimal
    session_status: str
    message: str


class BillingTaxQuoteRead(BaseModel):
    organization_id: UUID
    jurisdiction: str
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    reverse_charge: bool
    filing_hint: str


class BillingTaxFilingRead(BaseModel):
    organization_id: UUID
    jurisdiction: str
    period_start: date
    period_end: date
    invoice_count: int
    taxable_subtotal: Decimal
    tax_amount: Decimal
    gross_total: Decimal
    outstanding_total: Decimal
    currency: str
    filing_reference: str
    delivery_mode: str
    delivery_attempted: bool
    delivered: bool
    destination: str | None
    provider_status_code: int | None
    failure_reason: str | None
    filed_at: datetime


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


class BillingPlanChangeCreate(BaseModel):
    organization_id: UUID
    new_billing_plan_id: UUID | None = None
    new_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    effective_on: date
    note: str | None = Field(default=None, max_length=1000)


class BillingPlanChangeRead(BillingProrationQuoteRead):
    previous_billing_plan_id: UUID
    new_billing_plan_id: UUID
    previous_price: Decimal
    applied_price: Decimal
    subscription_status: SubscriptionStatus
    applied_at: datetime


class BillingSubscriptionLifecycleCreate(BaseModel):
    organization_id: UUID
    action: Literal["cancel_at_period_end", "cancel_now", "undo_cancel", "pause", "resume"]
    effective_on: date | None = None
    reason: str | None = Field(default=None, max_length=1000)


class BillingSubscriptionLifecycleRead(BaseModel):
    organization_id: UUID
    subscription_id: UUID
    action: str
    previous_status: SubscriptionStatus
    status: SubscriptionStatus
    cancel_at_period_end: bool
    effective_on: date
    message: str
    subscription: SubscriptionRead


class BillingEntitlementEnforcementCreate(BaseModel):
    organization_id: UUID
    subscription_id: UUID | None = None
    as_of: date | None = None
    dry_run: bool = False


class BillingEntitlementEnforcementItemRead(BaseModel):
    entitlement_id: UUID
    subscription_id: UUID
    feature_key: str
    previous_status: str
    status: str
    limit_value: int | None
    used_value: int
    remaining_value: int | None
    subscription_status: SubscriptionStatus
    action: str
    reason: str
    changed: bool


class BillingEntitlementEnforcementRead(BaseModel):
    organization_id: UUID
    subscription_id: UUID | None
    as_of: date
    dry_run: bool
    checked_count: int
    would_update_count: int
    updated_count: int
    blocked_count: int
    over_limit_count: int
    active_count: int
    items: list[BillingEntitlementEnforcementItemRead]


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


class BillingDunningRunCreate(BaseModel):
    organization_id: UUID
    overdue_as_of: date | None = None
    overdue_after_days: int = Field(default=0, ge=0, le=365)
    repeat_after_days: int = Field(default=7, ge=0, le=365)
    limit: int = Field(default=100, ge=1, le=1000)
    dry_run: bool = False


class BillingDunningRunRead(BaseModel):
    organization_id: UUID | None
    overdue_as_of: date
    eligible_count: int
    executed_count: int
    notice_count: int
    delivered_count: int
    record_only_count: int
    past_due_count: int
    skipped_count: int
    failed_count: int
    dry_run: bool = False
    invoice_ids: list[UUID]
    subscription_ids: list[UUID]
    total_outstanding: Decimal
    severity_counts: dict[str, int]


class BillingLateFeeRunCreate(BaseModel):
    organization_id: UUID
    apply_on: date | None = None
    overdue_after_days: int = Field(default=0, ge=0, le=365)
    repeat_after_days: int = Field(default=30, ge=1, le=365)
    fixed_fee: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    percentage_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100, max_digits=6, decimal_places=2)
    max_fee: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    limit: int = Field(default=100, ge=1, le=1000)
    dry_run: bool = False

    @model_validator(mode="after")
    def has_fee_rule(self) -> "BillingLateFeeRunCreate":
        if self.fixed_fee == 0 and self.percentage_rate == 0:
            raise ValueError("fixed_fee or percentage_rate must be greater than zero")
        return self


class BillingLateFeeRunRead(BaseModel):
    organization_id: UUID | None
    apply_on: date
    eligible_count: int
    executed_count: int
    fee_count: int
    skipped_count: int
    failed_count: int
    dry_run: bool = False
    invoice_ids: list[UUID]
    subscription_ids: list[UUID]
    total_late_fees: Decimal


class BillingPaymentRetryRunCreate(BaseModel):
    organization_id: UUID
    retry_at: datetime | None = None
    overdue_after_days: int = Field(default=0, ge=0, le=365)
    repeat_after_hours: int = Field(default=24, ge=0, le=24 * 365)
    max_attempts: int = Field(default=3, ge=1, le=20)
    provider: str = Field(default="billing_provider", min_length=2, max_length=80)
    limit: int = Field(default=100, ge=1, le=1000)
    dry_run: bool = False


class BillingPaymentRetryRunRead(BaseModel):
    organization_id: UUID | None
    retry_at: datetime
    eligible_count: int
    executed_count: int
    retry_count: int
    succeeded_count: int
    submitted_count: int
    skipped_count: int
    failed_count: int
    dry_run: bool = False
    delivery_mode: str
    invoice_ids: list[UUID]
    subscription_ids: list[UUID]
    total_attempted: Decimal
    total_collected: Decimal
    status_counts: dict[str, int]


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


class BillingRecurringInvoiceRunCreate(BaseModel):
    organization_id: UUID
    bill_on: date | None = None
    due_in_days: int = Field(default=14, ge=0, le=120)
    limit: int = Field(default=100, ge=1, le=1000)
    dry_run: bool = False
    invoice_prefix: str = Field(default="SAAS", min_length=2, max_length=20)


class BillingRecurringInvoiceRunRead(BaseModel):
    organization_id: UUID | None
    bill_on: date
    eligible_count: int
    executed_count: int
    invoiced_count: int
    skipped_count: int
    failed_count: int
    dry_run: bool = False
    invoice_ids: list[UUID]
    subscription_ids: list[UUID]
    total_invoiced: Decimal


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
