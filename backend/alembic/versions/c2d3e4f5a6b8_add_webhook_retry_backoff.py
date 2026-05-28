"""add webhook retry backoff

Revision ID: c2d3e4f5a6b8
Revises: c1d2e3f4a5b6
Create Date: 2026-05-28 08:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "c2d3e4f5a6b8"
down_revision: str | None = "c1d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("developer_webhook_deliveries", sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("developer_webhook_deliveries", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        op.f("ix_developer_webhook_deliveries_last_attempted_at"),
        "developer_webhook_deliveries",
        ["last_attempted_at"],
    )
    op.create_index(
        op.f("ix_developer_webhook_deliveries_next_attempt_at"),
        "developer_webhook_deliveries",
        ["next_attempt_at"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_developer_webhook_deliveries_next_attempt_at"), table_name="developer_webhook_deliveries")
    op.drop_index(op.f("ix_developer_webhook_deliveries_last_attempted_at"), table_name="developer_webhook_deliveries")
    op.drop_column("developer_webhook_deliveries", "next_attempt_at")
    op.drop_column("developer_webhook_deliveries", "last_attempted_at")
