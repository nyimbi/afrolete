"""add carpool geocoding fields

Revision ID: a7f3c9e2d1b6
Revises: e6c4a2d9b813
Create Date: 2026-05-28 07:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "a7f3c9e2d1b6"
down_revision: str | None = "e6c4a2d9b813"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("event_travel_carpool_rides", sa.Column("pickup_latitude", sa.Numeric(9, 6), nullable=True))
    op.add_column("event_travel_carpool_rides", sa.Column("pickup_longitude", sa.Numeric(9, 6), nullable=True))
    op.add_column("event_travel_carpool_rides", sa.Column("dropoff_latitude", sa.Numeric(9, 6), nullable=True))
    op.add_column("event_travel_carpool_rides", sa.Column("dropoff_longitude", sa.Numeric(9, 6), nullable=True))


def downgrade() -> None:
    op.drop_column("event_travel_carpool_rides", "dropoff_longitude")
    op.drop_column("event_travel_carpool_rides", "dropoff_latitude")
    op.drop_column("event_travel_carpool_rides", "pickup_longitude")
    op.drop_column("event_travel_carpool_rides", "pickup_latitude")
