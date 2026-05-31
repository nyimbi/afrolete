"""add financial statement packages

Revision ID: a498b20260531
Revises: a497b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a498b20260531"
down_revision: str | Sequence[str] | None = "a497b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "financial_statement_packages",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("statement_type", sa.String(length=80), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("basis", sa.String(length=40), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("prepared_by_name", sa.String(length=180), nullable=True),
        sa.Column("profit_loss_json", sa.Text(), nullable=False),
        sa.Column("balance_sheet_json", sa.Text(), nullable=False),
        sa.Column("cash_flow_json", sa.Text(), nullable=False),
        sa.Column("highlights_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_financial_statement_packages_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_financial_statement_packages")),
    )
    for column in (
        "basis",
        "generated_at",
        "organization_id",
        "period_end",
        "period_start",
        "prepared_by_name",
        "statement_type",
        "status",
    ):
        op.create_index(op.f(f"ix_financial_statement_packages_{column}"), "financial_statement_packages", [column], unique=False)


def downgrade() -> None:
    for column in (
        "status",
        "statement_type",
        "prepared_by_name",
        "period_start",
        "period_end",
        "organization_id",
        "generated_at",
        "basis",
    ):
        op.drop_index(op.f(f"ix_financial_statement_packages_{column}"), table_name="financial_statement_packages")
    op.drop_table("financial_statement_packages")
