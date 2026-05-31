"""add member dues collection rails

Revision ID: a515b20260531
Revises: a514b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a515b20260531"
down_revision: str | Sequence[str] | None = "a514b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "member_dues_collection_rails",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False, server_default="mpesa"),
        sa.Column("method", sa.String(80), nullable=False, server_default="mobile_money"),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="KES"),
        sa.Column("paybill_number", sa.String(80), nullable=True),
        sa.Column("till_number", sa.String(80), nullable=True),
        sa.Column("account_number", sa.String(120), nullable=True),
        sa.Column("account_name", sa.String(180), nullable=True),
        sa.Column("bank_name", sa.String(180), nullable=True),
        sa.Column("branch_name", sa.String(180), nullable=True),
        sa.Column("phone_number", sa.String(80), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("settlement_reference_prefix", sa.String(80), nullable=True),
        sa.Column("checkout_priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("supports_stk_push", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("supports_manual_reconciliation", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_member_dues_collection_rails_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_dues_collection_rails")),
        sa.UniqueConstraint("organization_id", "name", name=op.f("uq_member_dues_collection_rails_organization_id")),
    )
    for column in (
        "organization_id",
        "name",
        "provider",
        "method",
        "status",
        "country_code",
        "paybill_number",
        "till_number",
        "account_number",
        "settlement_reference_prefix",
        "checkout_priority",
    ):
        op.create_index(op.f(f"ix_member_dues_collection_rails_{column}"), "member_dues_collection_rails", [column])


def downgrade() -> None:
    for column in (
        "checkout_priority",
        "settlement_reference_prefix",
        "account_number",
        "till_number",
        "paybill_number",
        "country_code",
        "status",
        "method",
        "provider",
        "name",
        "organization_id",
    ):
        op.drop_index(op.f(f"ix_member_dues_collection_rails_{column}"), table_name="member_dues_collection_rails")
    op.drop_table("member_dues_collection_rails")
