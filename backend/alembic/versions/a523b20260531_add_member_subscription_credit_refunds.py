"""add member subscription credit refunds

Revision ID: a523b20260531
Revises: a522b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a523b20260531"
down_revision: str | Sequence[str] | None = "a522b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "member_subscription_credit_refunds",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("subscription_id", GUID(), nullable=False),
        sa.Column("credit_id", GUID(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("method", sa.String(length=80), nullable=False),
        sa.Column("external_refund_id", sa.String(length=180), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("processed_by_person_id", GUID(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("raw_reference", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["credit_id"],
            ["member_subscription_credits.id"],
            name=op.f("fk_member_subscription_credit_refunds_credit_id_member_subscription_credits"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_member_subscription_credit_refunds_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["processed_by_person_id"],
            ["persons.id"],
            name=op.f("fk_member_subscription_credit_refunds_processed_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["member_subscriptions.id"],
            name=op.f("fk_member_subscription_credit_refunds_subscription_id_member_subscriptions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_subscription_credit_refunds")),
    )
    for column in [
        "organization_id",
        "subscription_id",
        "credit_id",
        "provider",
        "method",
        "external_refund_id",
        "refunded_at",
        "status",
        "processed_by_person_id",
    ]:
        op.create_index(
            op.f(f"ix_member_subscription_credit_refunds_{column}"),
            "member_subscription_credit_refunds",
            [column],
        )


def downgrade() -> None:
    for column in [
        "processed_by_person_id",
        "status",
        "refunded_at",
        "external_refund_id",
        "method",
        "provider",
        "credit_id",
        "subscription_id",
        "organization_id",
    ]:
        op.drop_index(
            op.f(f"ix_member_subscription_credit_refunds_{column}"),
            table_name="member_subscription_credit_refunds",
        )
    op.drop_table("member_subscription_credit_refunds")
