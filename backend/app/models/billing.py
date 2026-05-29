from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import BillingCycle, BillingInvoiceStatus, SubscriptionStatus, UsageUnit


class BillingPlan(IdMixin, TimestampMixin, Base):
    __tablename__ = "billing_plans"
    __table_args__ = (UniqueConstraint("code"),)

    code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    billing_cycle: Mapped[BillingCycle] = mapped_column(
        enum_type(BillingCycle),
        default=BillingCycle.MONTHLY,
        nullable=False,
        index=True,
    )
    included_athletes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    included_teams: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    included_agent_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    included_storage_gb: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    per_athlete_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    per_agent_task_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    features: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class TenantSubscription(IdMixin, TimestampMixin, Base):
    __tablename__ = "tenant_subscriptions"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    billing_plan_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("billing_plans.id"), index=True)
    status: Mapped[SubscriptionStatus] = mapped_column(
        enum_type(SubscriptionStatus),
        default=SubscriptionStatus.TRIALING,
        nullable=False,
        index=True,
    )
    billing_cycle: Mapped[BillingCycle] = mapped_column(
        enum_type(BillingCycle),
        default=BillingCycle.MONTHLY,
        nullable=False,
        index=True,
    )
    current_period_start: Mapped[date] = mapped_column(nullable=False, index=True)
    current_period_end: Mapped[date] = mapped_column(nullable=False, index=True)
    trial_ends_on: Mapped[date | None] = mapped_column(index=True)
    next_billing_on: Mapped[date | None] = mapped_column(index=True)
    seats_purchased: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    negotiated_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    discount_code: Mapped[str | None] = mapped_column(String(80), index=True)
    external_customer_id: Mapped[str | None] = mapped_column(String(180), index=True)
    external_subscription_id: Mapped[str | None] = mapped_column(String(180), index=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class UsageMeter(IdMixin, TimestampMixin, Base):
    __tablename__ = "usage_meters"
    __table_args__ = (UniqueConstraint("code"),)

    code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    unit: Mapped[UsageUnit] = mapped_column(enum_type(UsageUnit), nullable=False, index=True)
    included_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overage_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"), nullable=False)
    aggregation: Mapped[str] = mapped_column(String(40), default="sum", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class UsageRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "usage_records"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    subscription_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("tenant_subscriptions.id"), index=True)
    usage_meter_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("usage_meters.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(120), default="manual", nullable=False, index=True)
    external_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class SaaSInvoice(IdMixin, TimestampMixin, Base):
    __tablename__ = "saas_invoices"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    subscription_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("tenant_subscriptions.id"), index=True)
    invoice_number: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(nullable=False, index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    due_on: Mapped[date | None] = mapped_column(index=True)
    status: Mapped[BillingInvoiceStatus] = mapped_column(
        enum_type(BillingInvoiceStatus),
        default=BillingInvoiceStatus.OPEN,
        nullable=False,
        index=True,
    )
    line_items: Mapped[str | None] = mapped_column(Text)
    external_invoice_id: Mapped[str | None] = mapped_column(String(180), index=True)
    dunning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dunning_last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    dunning_last_severity: Mapped[str | None] = mapped_column(String(40), index=True)
    late_fee_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    late_fee_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    late_fee_last_applied_on: Mapped[date | None] = mapped_column(index=True)


class SaaSPayment(IdMixin, TimestampMixin, Base):
    __tablename__ = "saas_payments"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    invoice_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("saas_invoices.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    external_payment_id: Mapped[str | None] = mapped_column(String(180), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="succeeded", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class BillingEntitlement(IdMixin, TimestampMixin, Base):
    __tablename__ = "billing_entitlements"
    __table_args__ = (UniqueConstraint("subscription_id", "feature_key"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    subscription_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("tenant_subscriptions.id"), index=True)
    feature_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    limit_value: Mapped[int | None] = mapped_column(Integer)
    used_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    resets_on: Mapped[date | None] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
