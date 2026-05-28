"""add wearable provider pull config

Revision ID: af56cd78ef90
Revises: ae45bf67cd89
Create Date: 2026-05-28 14:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "af56cd78ef90"
down_revision: str | None = "ae45bf67cd89"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("performance_wearable_provider_connections", sa.Column("provider_pull_url", sa.String(length=800), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("provider_pull_cursor_param", sa.String(length=80), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("provider_pull_since_param", sa.String(length=80), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("provider_pull_until_param", sa.String(length=80), nullable=True))
    op.add_column("performance_wearable_provider_sync_runs", sa.Column("provider_status_code", sa.Integer(), nullable=True))
    op.add_column("performance_wearable_provider_sync_runs", sa.Column("provider_response_hash", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("performance_wearable_provider_sync_runs", "provider_response_hash")
    op.drop_column("performance_wearable_provider_sync_runs", "provider_status_code")
    op.drop_column("performance_wearable_provider_connections", "provider_pull_until_param")
    op.drop_column("performance_wearable_provider_connections", "provider_pull_since_param")
    op.drop_column("performance_wearable_provider_connections", "provider_pull_cursor_param")
    op.drop_column("performance_wearable_provider_connections", "provider_pull_url")
