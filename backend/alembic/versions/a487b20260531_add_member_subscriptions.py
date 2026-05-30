"""add member subscriptions

Revision ID: a487b20260531
Revises: a486b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.models.base import GUID


revision: str = "a487b20260531"
down_revision: str | None = "a486b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "member_subscription_plans",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("member_role", sa.String(length=80), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("billing_interval", sa.String(length=40), nullable=False),
        sa.Column("due_day", sa.Integer(), nullable=True),
        sa.Column("grace_period_days", sa.Integer(), nullable=False),
        sa.Column("benefits", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_member_subscription_plans_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_subscription_plans")),
        sa.UniqueConstraint("organization_id", "name", name=op.f("uq_member_subscription_plans_organization_id")),
    )
    op.create_index(op.f("ix_member_subscription_plans_organization_id"), "member_subscription_plans", ["organization_id"])
    op.create_index(op.f("ix_member_subscription_plans_name"), "member_subscription_plans", ["name"])
    op.create_index(op.f("ix_member_subscription_plans_member_role"), "member_subscription_plans", ["member_role"])
    op.create_index(op.f("ix_member_subscription_plans_billing_interval"), "member_subscription_plans", ["billing_interval"])
    op.create_index(op.f("ix_member_subscription_plans_status"), "member_subscription_plans", ["status"])

    op.create_table(
        "member_subscriptions",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("plan_id", GUID(), nullable=False),
        sa.Column("membership_id", GUID(), nullable=True),
        sa.Column("subject_type", sa.String(length=12), nullable=False),
        sa.Column("subject_id", GUID(), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("current_period_start", sa.Date(), nullable=False),
        sa.Column("current_period_end", sa.Date(), nullable=False),
        sa.Column("next_due_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("balance_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("external_reference", sa.String(length=180), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["membership_id"], ["memberships.id"], name=op.f("fk_member_subscriptions_membership_id_memberships")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_member_subscriptions_organization_id_organizations")),
        sa.ForeignKeyConstraint(["plan_id"], ["member_subscription_plans.id"], name=op.f("fk_member_subscriptions_plan_id_member_subscription_plans")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_subscriptions")),
        sa.UniqueConstraint(
            "organization_id",
            "plan_id",
            "subject_type",
            "subject_id",
            name="uq_member_subscriptions_org_plan_subject",
        ),
    )
    op.create_index(op.f("ix_member_subscriptions_organization_id"), "member_subscriptions", ["organization_id"])
    op.create_index(op.f("ix_member_subscriptions_plan_id"), "member_subscriptions", ["plan_id"])
    op.create_index(op.f("ix_member_subscriptions_membership_id"), "member_subscriptions", ["membership_id"])
    op.create_index(op.f("ix_member_subscriptions_subject_type"), "member_subscriptions", ["subject_type"])
    op.create_index(op.f("ix_member_subscriptions_subject_id"), "member_subscriptions", ["subject_id"])
    op.create_index(op.f("ix_member_subscriptions_starts_on"), "member_subscriptions", ["starts_on"])
    op.create_index(op.f("ix_member_subscriptions_current_period_start"), "member_subscriptions", ["current_period_start"])
    op.create_index(op.f("ix_member_subscriptions_current_period_end"), "member_subscriptions", ["current_period_end"])
    op.create_index(op.f("ix_member_subscriptions_next_due_on"), "member_subscriptions", ["next_due_on"])
    op.create_index(op.f("ix_member_subscriptions_status"), "member_subscriptions", ["status"])
    op.create_index(op.f("ix_member_subscriptions_external_reference"), "member_subscriptions", ["external_reference"])

    op.create_table(
        "member_subscription_payments",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("subscription_id", GUID(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("method", sa.String(length=80), nullable=False),
        sa.Column("external_payment_id", sa.String(length=180), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("raw_reference", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_member_subscription_payments_organization_id_organizations")),
        sa.ForeignKeyConstraint(["subscription_id"], ["member_subscriptions.id"], name=op.f("fk_member_subscription_payments_subscription_id_member_subscriptions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_subscription_payments")),
    )
    op.create_index(op.f("ix_member_subscription_payments_organization_id"), "member_subscription_payments", ["organization_id"])
    op.create_index(op.f("ix_member_subscription_payments_subscription_id"), "member_subscription_payments", ["subscription_id"])
    op.create_index(op.f("ix_member_subscription_payments_provider"), "member_subscription_payments", ["provider"])
    op.create_index(op.f("ix_member_subscription_payments_method"), "member_subscription_payments", ["method"])
    op.create_index(op.f("ix_member_subscription_payments_external_payment_id"), "member_subscription_payments", ["external_payment_id"])
    op.create_index(op.f("ix_member_subscription_payments_received_at"), "member_subscription_payments", ["received_at"])
    op.create_index(op.f("ix_member_subscription_payments_status"), "member_subscription_payments", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_member_subscription_payments_status"), table_name="member_subscription_payments")
    op.drop_index(op.f("ix_member_subscription_payments_received_at"), table_name="member_subscription_payments")
    op.drop_index(op.f("ix_member_subscription_payments_external_payment_id"), table_name="member_subscription_payments")
    op.drop_index(op.f("ix_member_subscription_payments_method"), table_name="member_subscription_payments")
    op.drop_index(op.f("ix_member_subscription_payments_provider"), table_name="member_subscription_payments")
    op.drop_index(op.f("ix_member_subscription_payments_subscription_id"), table_name="member_subscription_payments")
    op.drop_index(op.f("ix_member_subscription_payments_organization_id"), table_name="member_subscription_payments")
    op.drop_table("member_subscription_payments")

    op.drop_index(op.f("ix_member_subscriptions_external_reference"), table_name="member_subscriptions")
    op.drop_index(op.f("ix_member_subscriptions_status"), table_name="member_subscriptions")
    op.drop_index(op.f("ix_member_subscriptions_next_due_on"), table_name="member_subscriptions")
    op.drop_index(op.f("ix_member_subscriptions_current_period_end"), table_name="member_subscriptions")
    op.drop_index(op.f("ix_member_subscriptions_current_period_start"), table_name="member_subscriptions")
    op.drop_index(op.f("ix_member_subscriptions_starts_on"), table_name="member_subscriptions")
    op.drop_index(op.f("ix_member_subscriptions_subject_id"), table_name="member_subscriptions")
    op.drop_index(op.f("ix_member_subscriptions_subject_type"), table_name="member_subscriptions")
    op.drop_index(op.f("ix_member_subscriptions_membership_id"), table_name="member_subscriptions")
    op.drop_index(op.f("ix_member_subscriptions_plan_id"), table_name="member_subscriptions")
    op.drop_index(op.f("ix_member_subscriptions_organization_id"), table_name="member_subscriptions")
    op.drop_table("member_subscriptions")

    op.drop_index(op.f("ix_member_subscription_plans_status"), table_name="member_subscription_plans")
    op.drop_index(op.f("ix_member_subscription_plans_billing_interval"), table_name="member_subscription_plans")
    op.drop_index(op.f("ix_member_subscription_plans_member_role"), table_name="member_subscription_plans")
    op.drop_index(op.f("ix_member_subscription_plans_name"), table_name="member_subscription_plans")
    op.drop_index(op.f("ix_member_subscription_plans_organization_id"), table_name="member_subscription_plans")
    op.drop_table("member_subscription_plans")
