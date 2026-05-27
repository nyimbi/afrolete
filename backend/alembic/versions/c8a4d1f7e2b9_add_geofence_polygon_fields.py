"""add geofence polygon fields

Revision ID: c8a4d1f7e2b9
Revises: a7f3c9e2d1b6
Create Date: 2026-05-28 08:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "c8a4d1f7e2b9"
down_revision: str | None = "a7f3c9e2d1b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("event_travel_geofence_zones", sa.Column("polygon_coordinates", sa.Text(), nullable=True))
    op.add_column("event_travel_geofence_zones", sa.Column("provider", sa.String(length=80), nullable=True))
    op.add_column("event_travel_geofence_zones", sa.Column("provider_zone_id", sa.String(length=180), nullable=True))
    op.add_column("event_travel_geofence_zones", sa.Column("provider_revision", sa.String(length=80), nullable=True))
    op.create_index(op.f("ix_event_travel_geofence_zones_provider"), "event_travel_geofence_zones", ["provider"])
    op.create_index(
        op.f("ix_event_travel_geofence_zones_provider_zone_id"),
        "event_travel_geofence_zones",
        ["provider_zone_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_event_travel_geofence_zones_provider_zone_id"), table_name="event_travel_geofence_zones")
    op.drop_index(op.f("ix_event_travel_geofence_zones_provider"), table_name="event_travel_geofence_zones")
    op.drop_column("event_travel_geofence_zones", "provider_revision")
    op.drop_column("event_travel_geofence_zones", "provider_zone_id")
    op.drop_column("event_travel_geofence_zones", "provider")
    op.drop_column("event_travel_geofence_zones", "polygon_coordinates")
