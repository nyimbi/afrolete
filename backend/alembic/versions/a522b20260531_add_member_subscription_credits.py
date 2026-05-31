"""add member subscription credits

Revision ID: a522b20260531
Revises: a521b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a522b20260531"
down_revision: str | Sequence[str] | None = "a521b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "member_subscription_credits",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("subscription_id", GUID(), nullable=False),
        sa.Column("source_payment_id", GUID(), nullable=True),
        sa.Column("source_callback_id", GUID(), nullable=True),
        sa.Column("original_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("remaining_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_by_person_id", GUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_person_id"],
            ["persons.id"],
            name=op.f("fk_member_subscription_credits_created_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_member_subscription_credits_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["source_callback_id"],
            ["member_dues_payment_callbacks.id"],
            name=op.f("fk_member_subscription_credits_source_callback_id_member_dues_payment_callbacks"),
        ),
        sa.ForeignKeyConstraint(
            ["source_payment_id"],
            ["member_subscription_payments.id"],
            name=op.f("fk_member_subscription_credits_source_payment_id_member_subscription_payments"),
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["member_subscriptions.id"],
            name=op.f("fk_member_subscription_credits_subscription_id_member_subscriptions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_subscription_credits")),
    )
    for column in [
        "organization_id",
        "subscription_id",
        "source_payment_id",
        "source_callback_id",
        "remaining_amount",
        "source",
        "status",
        "created_by_person_id",
    ]:
        op.create_index(op.f(f"ix_member_subscription_credits_{column}"), "member_subscription_credits", [column])


def downgrade() -> None:
    for column in [
        "created_by_person_id",
        "status",
        "source",
        "remaining_amount",
        "source_callback_id",
        "source_payment_id",
        "subscription_id",
        "organization_id",
    ]:
        op.drop_index(op.f(f"ix_member_subscription_credits_{column}"), table_name="member_subscription_credits")
    op.drop_table("member_subscription_credits")
