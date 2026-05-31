"""add member charge allocation fields

Revision ID: a509b20260531
Revises: a508b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a509b20260531"
down_revision: str | Sequence[str] | None = "a508b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "member_subscription_charges",
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "member_subscription_charges",
        sa.Column("balance_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "member_subscription_charges",
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "member_subscription_charges",
        sa.Column("last_payment_id", GUID(), nullable=True),
    )
    op.execute(
        "UPDATE member_subscription_charges "
        "SET balance_amount = amount, amount_paid = 0 "
        "WHERE balance_amount = 0 AND status IN ('open', 'partial')"
    )
    op.execute(
        "UPDATE member_subscription_charges "
        "SET balance_amount = 0, amount_paid = amount "
        "WHERE status = 'paid'"
    )
    op.create_foreign_key(
        op.f("fk_member_subscription_charges_last_payment_id_member_subscription_payments"),
        "member_subscription_charges",
        "member_subscription_payments",
        ["last_payment_id"],
        ["id"],
    )
    for column in ("paid_at", "last_payment_id"):
        op.create_index(op.f(f"ix_member_subscription_charges_{column}"), "member_subscription_charges", [column])
    op.alter_column("member_subscription_charges", "amount_paid", server_default=None)
    op.alter_column("member_subscription_charges", "balance_amount", server_default=None)


def downgrade() -> None:
    for column in ("last_payment_id", "paid_at"):
        op.drop_index(op.f(f"ix_member_subscription_charges_{column}"), table_name="member_subscription_charges")
    op.drop_constraint(
        op.f("fk_member_subscription_charges_last_payment_id_member_subscription_payments"),
        "member_subscription_charges",
        type_="foreignkey",
    )
    op.drop_column("member_subscription_charges", "last_payment_id")
    op.drop_column("member_subscription_charges", "paid_at")
    op.drop_column("member_subscription_charges", "balance_amount")
    op.drop_column("member_subscription_charges", "amount_paid")
