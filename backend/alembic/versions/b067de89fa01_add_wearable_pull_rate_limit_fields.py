"""add wearable pull rate limit fields

Revision ID: b067de89fa01
Revises: af56cd78ef90
Create Date: 2026-05-28 15:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "b067de89fa01"
down_revision: str | None = "af56cd78ef90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "performance_wearable_provider_sync_runs",
        sa.Column("provider_page_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "performance_wearable_provider_sync_runs",
        sa.Column("provider_rate_limited", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "performance_wearable_provider_sync_runs",
        sa.Column("provider_retry_after_seconds", sa.Integer(), nullable=True),
    )
    op.alter_column("performance_wearable_provider_sync_runs", "provider_page_count", server_default=None)
    op.alter_column("performance_wearable_provider_sync_runs", "provider_rate_limited", server_default=None)


def downgrade() -> None:
    op.drop_column("performance_wearable_provider_sync_runs", "provider_retry_after_seconds")
    op.drop_column("performance_wearable_provider_sync_runs", "provider_rate_limited")
    op.drop_column("performance_wearable_provider_sync_runs", "provider_page_count")
