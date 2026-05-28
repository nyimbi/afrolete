"""add wearable webhook registration

Revision ID: c178ef90ab12
Revises: b067de89fa01
Create Date: 2026-05-28 15:35:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "c178ef90ab12"
down_revision: str | None = "b067de89fa01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("performance_wearable_provider_connections", sa.Column("provider_webhook_registration_url", sa.String(length=800), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("provider_webhook_callback_url", sa.String(length=800), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("provider_webhook_event_types", sa.Text(), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("provider_webhook_registration_status_code", sa.Integer(), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("provider_webhook_registration_hash", sa.String(length=64), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("provider_webhook_registered_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("provider_webhook_registration_error", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix_performance_wearable_provider_connections_provider_webhook_registered_at"),
        "performance_wearable_provider_connections",
        ["provider_webhook_registered_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_performance_wearable_provider_connections_provider_webhook_registered_at"),
        table_name="performance_wearable_provider_connections",
    )
    op.drop_column("performance_wearable_provider_connections", "provider_webhook_registration_error")
    op.drop_column("performance_wearable_provider_connections", "provider_webhook_registered_at")
    op.drop_column("performance_wearable_provider_connections", "provider_webhook_registration_hash")
    op.drop_column("performance_wearable_provider_connections", "provider_webhook_registration_status_code")
    op.drop_column("performance_wearable_provider_connections", "provider_webhook_event_types")
    op.drop_column("performance_wearable_provider_connections", "provider_webhook_callback_url")
    op.drop_column("performance_wearable_provider_connections", "provider_webhook_registration_url")
