"""add event travel carpools

Revision ID: b8e41a0d2c6f
Revises: 8d13b7f4c2a9
Create Date: 2026-05-28 04:40:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "b8e41a0d2c6f"
down_revision: str | None = "8d13b7f4c2a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_travel_carpool_rides",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("travel_plan_id", app.models.base.GUID(), nullable=False),
        sa.Column("ride_type", sa.String(length=40), nullable=False, server_default="request"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="open"),
        sa.Column("rider_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("driver_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("pickup_location", sa.String(length=240), nullable=False),
        sa.Column("dropoff_location", sa.String(length=240), nullable=True),
        sa.Column("seats_requested", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("seats_available", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("departure_window_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("departure_window_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("match_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["driver_person_id"],
            ["persons.id"],
            name=op.f("fk_event_travel_carpool_rides_driver_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_travel_carpool_rides_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["rider_person_id"],
            ["persons.id"],
            name=op.f("fk_event_travel_carpool_rides_rider_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["travel_plan_id"],
            ["event_travel_plans.id"],
            name=op.f("fk_event_travel_carpool_rides_travel_plan_id_event_travel_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_travel_carpool_rides")),
    )
    for column in [
        "departure_window_end",
        "departure_window_start",
        "driver_person_id",
        "matched_at",
        "organization_id",
        "pickup_location",
        "ride_type",
        "rider_person_id",
        "status",
        "travel_plan_id",
    ]:
        op.create_index(
            op.f(f"ix_event_travel_carpool_rides_{column}"),
            "event_travel_carpool_rides",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "travel_plan_id",
        "status",
        "rider_person_id",
        "ride_type",
        "pickup_location",
        "organization_id",
        "matched_at",
        "driver_person_id",
        "departure_window_start",
        "departure_window_end",
    ]:
        op.drop_index(op.f(f"ix_event_travel_carpool_rides_{column}"), table_name="event_travel_carpool_rides")
    op.drop_table("event_travel_carpool_rides")
