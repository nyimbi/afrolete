"""add wearable oauth token lifecycle

Revision ID: ae45bf67cd89
Revises: ad34ef56ab78
Create Date: 2026-05-28 14:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "ae45bf67cd89"
down_revision: str | None = "ad34ef56ab78"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("performance_wearable_provider_connections", sa.Column("access_token_hash", sa.String(length=64), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("refresh_token_hash", sa.String(length=64), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("refresh_token_family_id", sa.String(length=80), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("refresh_token_rotated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("token_last_refreshed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("token_type", sa.String(length=40), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("token_scope", sa.Text(), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("oauth_client_secret_path", sa.String(length=500), nullable=True))
    op.create_index(
        op.f("ix_performance_wearable_provider_connections_refresh_token_family_id"),
        "performance_wearable_provider_connections",
        ["refresh_token_family_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_wearable_provider_connections_refresh_token_rotated_at"),
        "performance_wearable_provider_connections",
        ["refresh_token_rotated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_wearable_provider_connections_token_last_refreshed_at"),
        "performance_wearable_provider_connections",
        ["token_last_refreshed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_performance_wearable_provider_connections_token_last_refreshed_at"),
        table_name="performance_wearable_provider_connections",
    )
    op.drop_index(
        op.f("ix_performance_wearable_provider_connections_refresh_token_rotated_at"),
        table_name="performance_wearable_provider_connections",
    )
    op.drop_index(
        op.f("ix_performance_wearable_provider_connections_refresh_token_family_id"),
        table_name="performance_wearable_provider_connections",
    )
    op.drop_column("performance_wearable_provider_connections", "oauth_client_secret_path")
    op.drop_column("performance_wearable_provider_connections", "token_scope")
    op.drop_column("performance_wearable_provider_connections", "token_type")
    op.drop_column("performance_wearable_provider_connections", "token_last_refreshed_at")
    op.drop_column("performance_wearable_provider_connections", "refresh_token_rotated_at")
    op.drop_column("performance_wearable_provider_connections", "refresh_token_family_id")
    op.drop_column("performance_wearable_provider_connections", "refresh_token_hash")
    op.drop_column("performance_wearable_provider_connections", "access_token_hash")
