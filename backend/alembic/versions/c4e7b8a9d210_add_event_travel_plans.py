"""add event travel plans

Revision ID: c4e7b8a9d210
Revises: b6d91f3a2c47
Create Date: 2026-05-28 05:05:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "c4e7b8a9d210"
down_revision: str | None = "b6d91f3a2c47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


travel_plan_status = sa.Enum(
    "draft",
    "ready",
    "in_progress",
    "completed",
    "cancelled",
    name="travelplanstatus",
    native_enum=False,
    create_constraint=True,
)
travel_risk_level = sa.Enum(
    "low",
    "medium",
    "high",
    "critical",
    name="travelrisklevel",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "event_travel_plans",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_id", app.models.base.GUID(), nullable=False),
        sa.Column("status", travel_plan_status, nullable=False, server_default="draft"),
        sa.Column("destination", sa.String(length=240), nullable=False),
        sa.Column("travel_mode", sa.String(length=80), nullable=False),
        sa.Column("departure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("return_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("route_summary", sa.Text(), nullable=True),
        sa.Column("vehicle_details", sa.Text(), nullable=True),
        sa.Column("driver_details", sa.Text(), nullable=True),
        sa.Column("staff_manifest", sa.Text(), nullable=True),
        sa.Column("passenger_manifest", sa.Text(), nullable=True),
        sa.Column("lodging_details", sa.Text(), nullable=True),
        sa.Column("meal_plan", sa.Text(), nullable=True),
        sa.Column("equipment_manifest", sa.Text(), nullable=True),
        sa.Column("emergency_contacts", sa.Text(), nullable=True),
        sa.Column("medical_access_plan", sa.Text(), nullable=True),
        sa.Column("route_weather_risk", sa.String(length=80), nullable=True),
        sa.Column("driver_certification_status", sa.String(length=80), nullable=True),
        sa.Column("vehicle_inspection_status", sa.String(length=80), nullable=True),
        sa.Column("consent_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("consent_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("cost_per_participant", sa.Numeric(12, 2), nullable=True),
        sa.Column("risk_level", travel_risk_level, nullable=False, server_default="medium"),
        sa.Column("risk_assessment", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_event_travel_plans_event_id_events"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_travel_plans_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_travel_plans")),
    )
    for column in [
        "consent_due_at",
        "consent_required",
        "departure_at",
        "destination",
        "driver_certification_status",
        "event_id",
        "organization_id",
        "return_at",
        "risk_level",
        "route_weather_risk",
        "status",
        "travel_mode",
        "vehicle_inspection_status",
    ]:
        op.create_index(op.f(f"ix_event_travel_plans_{column}"), "event_travel_plans", [column])


def downgrade() -> None:
    for column in [
        "vehicle_inspection_status",
        "travel_mode",
        "status",
        "route_weather_risk",
        "risk_level",
        "return_at",
        "organization_id",
        "event_id",
        "driver_certification_status",
        "destination",
        "departure_at",
        "consent_required",
        "consent_due_at",
    ]:
        op.drop_index(op.f(f"ix_event_travel_plans_{column}"), table_name="event_travel_plans")
    op.drop_table("event_travel_plans")
