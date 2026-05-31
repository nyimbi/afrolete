"""add member dues payment plans

Revision ID: a511b20260531
Revises: a510b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a511b20260531"
down_revision: str | Sequence[str] | None = "a510b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "member_subscription_payment_plans",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("subscription_id", GUID(), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("plan_type", sa.String(80), nullable=False, server_default="installment"),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
        sa.Column("principal_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("remaining_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="KES"),
        sa.Column("installment_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("installment_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("paid_installment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("installment_frequency", sa.String(40), nullable=False, server_default="monthly"),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("next_due_on", sa.Date(), nullable=True),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("approved_by_person_id", GUID(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["approved_by_person_id"], ["persons.id"], name=op.f("fk_member_subscription_payment_plans_approved_by_person_id_persons")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_member_subscription_payment_plans_organization_id_organizations")),
        sa.ForeignKeyConstraint(["subscription_id"], ["member_subscriptions.id"], name=op.f("fk_member_subscription_payment_plans_subscription_id_member_subscriptions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_subscription_payment_plans")),
    )
    for column in (
        "organization_id",
        "subscription_id",
        "name",
        "plan_type",
        "status",
        "installment_frequency",
        "starts_on",
        "next_due_on",
        "ends_on",
        "approved_by_person_id",
        "approved_at",
    ):
        op.create_index(
            op.f(f"ix_member_subscription_payment_plans_{column}"),
            "member_subscription_payment_plans",
            [column],
        )
    for column in (
        "plan_type",
        "status",
        "amount_paid",
        "currency",
        "installment_count",
        "paid_installment_count",
        "installment_frequency",
    ):
        op.alter_column("member_subscription_payment_plans", column, server_default=None)

    op.add_column("member_subscription_payments", sa.Column("payment_plan_id", GUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_member_subscription_payments_payment_plan_id_member_subscription_payment_plans"),
        "member_subscription_payments",
        "member_subscription_payment_plans",
        ["payment_plan_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_member_subscription_payments_payment_plan_id"),
        "member_subscription_payments",
        ["payment_plan_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_member_subscription_payments_payment_plan_id"), table_name="member_subscription_payments")
    op.drop_constraint(
        op.f("fk_member_subscription_payments_payment_plan_id_member_subscription_payment_plans"),
        "member_subscription_payments",
        type_="foreignkey",
    )
    op.drop_column("member_subscription_payments", "payment_plan_id")
    for column in (
        "approved_at",
        "approved_by_person_id",
        "ends_on",
        "next_due_on",
        "starts_on",
        "installment_frequency",
        "status",
        "plan_type",
        "name",
        "subscription_id",
        "organization_id",
    ):
        op.drop_index(op.f(f"ix_member_subscription_payment_plans_{column}"), table_name="member_subscription_payment_plans")
    op.drop_table("member_subscription_payment_plans")
