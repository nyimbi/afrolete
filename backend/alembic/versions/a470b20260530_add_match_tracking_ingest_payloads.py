"""add match tracking ingest payloads

Revision ID: a470b20260530
Revises: a469b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "a470b20260530"
down_revision: str | Sequence[str] | None = "a469b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "performance_match_tracking_provider_ingest_events",
        sa.Column("payload_json", sa.Text(), server_default="{}", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("performance_match_tracking_provider_ingest_events", "payload_json")
