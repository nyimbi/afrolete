"""add saas invoice late fee state

Revision ID: b6d4e2f8a913
Revises: a4c3d2e1f0b9
Create Date: 2026-05-29 13:35:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "b6d4e2f8a913"
down_revision: str | None = "a4c3d2e1f0b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "saas_invoices",
        sa.Column("late_fee_total", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
    )
    op.add_column(
        "saas_invoices",
        sa.Column("late_fee_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "saas_invoices",
        sa.Column("late_fee_last_applied_on", sa.Date(), nullable=True),
    )
    op.create_index(
        op.f("ix_saas_invoices_late_fee_last_applied_on"),
        "saas_invoices",
        ["late_fee_last_applied_on"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_saas_invoices_late_fee_last_applied_on"), table_name="saas_invoices")
    op.drop_column("saas_invoices", "late_fee_last_applied_on")
    op.drop_column("saas_invoices", "late_fee_count")
    op.drop_column("saas_invoices", "late_fee_total")
