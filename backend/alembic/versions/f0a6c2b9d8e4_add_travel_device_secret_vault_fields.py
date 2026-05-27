"""add travel device secret vault fields

Revision ID: f0a6c2b9d8e4
Revises: d9f1b7a4c6e8
Create Date: 2026-05-28 08:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "f0a6c2b9d8e4"
down_revision: str | None = "d9f1b7a4c6e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "event_travel_devices",
        sa.Column("secret_storage_mode", sa.String(length=40), nullable=False, server_default="database"),
    )
    op.add_column("event_travel_devices", sa.Column("secret_vault_provider", sa.String(length=80), nullable=True))
    op.add_column("event_travel_devices", sa.Column("secret_vault_reference", sa.String(length=360), nullable=True))
    op.create_index(op.f("ix_event_travel_devices_secret_storage_mode"), "event_travel_devices", ["secret_storage_mode"])
    op.create_index(
        op.f("ix_event_travel_devices_secret_vault_provider"),
        "event_travel_devices",
        ["secret_vault_provider"],
    )
    op.create_index(
        op.f("ix_event_travel_devices_secret_vault_reference"),
        "event_travel_devices",
        ["secret_vault_reference"],
    )
    op.alter_column("event_travel_devices", "secret_storage_mode", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_event_travel_devices_secret_vault_reference"), table_name="event_travel_devices")
    op.drop_index(op.f("ix_event_travel_devices_secret_vault_provider"), table_name="event_travel_devices")
    op.drop_index(op.f("ix_event_travel_devices_secret_storage_mode"), table_name="event_travel_devices")
    op.drop_column("event_travel_devices", "secret_vault_reference")
    op.drop_column("event_travel_devices", "secret_vault_provider")
    op.drop_column("event_travel_devices", "secret_storage_mode")
