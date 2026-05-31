"""add member subscription charges

Revision ID: a508b20260531
Revises: a507b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a508b20260531"
down_revision: str | Sequence[str] | None = "a507b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "member_subscription_charges",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("subscription_id", GUID(), nullable=False),
        sa.Column("plan_id", GUID(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_person_id", GUID(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_person_id"],
            ["persons.id"],
            name=op.f("fk_member_subscription_charges_created_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_member_subscription_charges_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["member_subscription_plans.id"],
            name=op.f("fk_member_subscription_charges_plan_id_member_subscription_plans"),
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["member_subscriptions.id"],
            name=op.f("fk_member_subscription_charges_subscription_id_member_subscriptions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_subscription_charges")),
        sa.UniqueConstraint("subscription_id", "period_start", "period_end", name="uq_member_subscription_charges_period"),
    )
    for column in (
        "organization_id",
        "subscription_id",
        "plan_id",
        "period_start",
        "period_end",
        "due_on",
        "status",
        "source",
        "created_by_person_id",
    ):
        op.create_index(op.f(f"ix_member_subscription_charges_{column}"), "member_subscription_charges", [column])


def downgrade() -> None:
    for column in (
        "created_by_person_id",
        "source",
        "status",
        "due_on",
        "period_end",
        "period_start",
        "plan_id",
        "subscription_id",
        "organization_id",
    ):
        op.drop_index(op.f(f"ix_member_subscription_charges_{column}"), table_name="member_subscription_charges")
    op.drop_table("member_subscription_charges")
