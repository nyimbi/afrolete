"""add travel device ingest secrets

Revision ID: e4b91c0f2a63
Revises: d2a6c48f0b72
Create Date: 2026-05-28 06:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "e4b91c0f2a63"
down_revision: str | None = "d2a6c48f0b72"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("event_travel_devices", sa.Column("ingest_secret_key", sa.String(length=160), nullable=True))
    op.add_column("event_travel_devices", sa.Column("secret_rotated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        op.f("ix_event_travel_devices_secret_rotated_at"),
        "event_travel_devices",
        ["secret_rotated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_event_travel_devices_secret_rotated_at"), table_name="event_travel_devices")
    op.drop_column("event_travel_devices", "secret_rotated_at")
    op.drop_column("event_travel_devices", "ingest_secret_key")
