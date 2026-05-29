"""add saas invoice dunning state

Revision ID: a4c3d2e1f0b9
Revises: e13b8f2d4a0c
Create Date: 2026-05-29 13:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "a4c3d2e1f0b9"
down_revision: str | None = "e13b8f2d4a0c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "saas_invoices",
        sa.Column("dunning_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "saas_invoices",
        sa.Column("dunning_last_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "saas_invoices",
        sa.Column("dunning_last_severity", sa.String(length=40), nullable=True),
    )
    op.create_index(
        op.f("ix_saas_invoices_dunning_last_sent_at"),
        "saas_invoices",
        ["dunning_last_sent_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_saas_invoices_dunning_last_severity"),
        "saas_invoices",
        ["dunning_last_severity"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_saas_invoices_dunning_last_severity"), table_name="saas_invoices")
    op.drop_index(op.f("ix_saas_invoices_dunning_last_sent_at"), table_name="saas_invoices")
    op.drop_column("saas_invoices", "dunning_last_severity")
    op.drop_column("saas_invoices", "dunning_last_sent_at")
    op.drop_column("saas_invoices", "dunning_count")
