"""add wearable oauth metadata

Revision ID: ad34ef56ab78
Revises: ac23de45fa67
Create Date: 2026-05-28 13:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "ad34ef56ab78"
down_revision: str | None = "ac23de45fa67"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("performance_wearable_provider_connections", sa.Column("oauth_client_id", sa.String(length=180), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("oauth_authorization_url", sa.String(length=800), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("oauth_token_url", sa.String(length=800), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("oauth_redirect_uri", sa.String(length=800), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("oauth_state_hash", sa.String(length=64), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("oauth_state_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("performance_wearable_provider_connections", sa.Column("oauth_authorized_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_performance_wearable_provider_connections_oauth_client_id"), "performance_wearable_provider_connections", ["oauth_client_id"], unique=False)
    op.create_index(op.f("ix_performance_wearable_provider_connections_oauth_state_expires_at"), "performance_wearable_provider_connections", ["oauth_state_expires_at"], unique=False)
    op.create_index(op.f("ix_performance_wearable_provider_connections_oauth_authorized_at"), "performance_wearable_provider_connections", ["oauth_authorized_at"], unique=False)
    op.create_unique_constraint(
        op.f("uq_performance_wearable_provider_connections_oauth_state_hash"),
        "performance_wearable_provider_connections",
        ["oauth_state_hash"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("uq_performance_wearable_provider_connections_oauth_state_hash"),
        "performance_wearable_provider_connections",
        type_="unique",
    )
    op.drop_index(op.f("ix_performance_wearable_provider_connections_oauth_authorized_at"), table_name="performance_wearable_provider_connections")
    op.drop_index(op.f("ix_performance_wearable_provider_connections_oauth_state_expires_at"), table_name="performance_wearable_provider_connections")
    op.drop_index(op.f("ix_performance_wearable_provider_connections_oauth_client_id"), table_name="performance_wearable_provider_connections")
    op.drop_column("performance_wearable_provider_connections", "oauth_authorized_at")
    op.drop_column("performance_wearable_provider_connections", "oauth_state_expires_at")
    op.drop_column("performance_wearable_provider_connections", "oauth_state_hash")
    op.drop_column("performance_wearable_provider_connections", "oauth_redirect_uri")
    op.drop_column("performance_wearable_provider_connections", "oauth_token_url")
    op.drop_column("performance_wearable_provider_connections", "oauth_authorization_url")
    op.drop_column("performance_wearable_provider_connections", "oauth_client_id")
