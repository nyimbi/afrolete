"""add developer api key quota windows

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-05-28 04:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "d3e4f5a6b7c8"
down_revision: str | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "developer_api_keys",
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "developer_api_keys",
        sa.Column("window_request_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "developer_api_keys",
        sa.Column("last_rate_limited_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_developer_api_keys_window_started_at"),
        "developer_api_keys",
        ["window_started_at"],
    )
    op.create_index(
        op.f("ix_developer_api_keys_last_rate_limited_at"),
        "developer_api_keys",
        ["last_rate_limited_at"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_developer_api_keys_last_rate_limited_at"), table_name="developer_api_keys")
    op.drop_index(op.f("ix_developer_api_keys_window_started_at"), table_name="developer_api_keys")
    op.drop_column("developer_api_keys", "last_rate_limited_at")
    op.drop_column("developer_api_keys", "window_request_count")
    op.drop_column("developer_api_keys", "window_started_at")
