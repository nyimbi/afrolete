"""add saas payment retry state

Revision ID: c2d4f6a8b901
Revises: b6d4e2f8a913
Create Date: 2026-05-29 14:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "c2d4f6a8b901"
down_revision: str | None = "b6d4e2f8a913"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "saas_invoices",
        sa.Column("payment_retry_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "saas_invoices",
        sa.Column("payment_retry_last_attempted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "saas_invoices",
        sa.Column("payment_retry_next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "saas_invoices",
        sa.Column("payment_retry_last_status", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "saas_invoices",
        sa.Column("payment_retry_last_failure_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "saas_invoices",
        sa.Column("payment_retry_last_provider_reference", sa.String(length=180), nullable=True),
    )
    op.create_index(
        op.f("ix_saas_invoices_payment_retry_last_attempted_at"),
        "saas_invoices",
        ["payment_retry_last_attempted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_saas_invoices_payment_retry_next_attempt_at"),
        "saas_invoices",
        ["payment_retry_next_attempt_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_saas_invoices_payment_retry_last_status"),
        "saas_invoices",
        ["payment_retry_last_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_saas_invoices_payment_retry_last_provider_reference"),
        "saas_invoices",
        ["payment_retry_last_provider_reference"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_saas_invoices_payment_retry_last_provider_reference"), table_name="saas_invoices")
    op.drop_index(op.f("ix_saas_invoices_payment_retry_last_status"), table_name="saas_invoices")
    op.drop_index(op.f("ix_saas_invoices_payment_retry_next_attempt_at"), table_name="saas_invoices")
    op.drop_index(op.f("ix_saas_invoices_payment_retry_last_attempted_at"), table_name="saas_invoices")
    op.drop_column("saas_invoices", "payment_retry_last_provider_reference")
    op.drop_column("saas_invoices", "payment_retry_last_failure_reason")
    op.drop_column("saas_invoices", "payment_retry_last_status")
    op.drop_column("saas_invoices", "payment_retry_next_attempt_at")
    op.drop_column("saas_invoices", "payment_retry_last_attempted_at")
    op.drop_column("saas_invoices", "payment_retry_count")
