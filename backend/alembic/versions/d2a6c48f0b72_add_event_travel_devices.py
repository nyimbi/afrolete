"""add event travel devices

Revision ID: d2a6c48f0b72
Revises: c0a4d72e9b31
Create Date: 2026-05-28 05:35:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d2a6c48f0b72"
down_revision: str | None = "c0a4d72e9b31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_travel_devices",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("travel_plan_id", app.models.base.GUID(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False, server_default="hardware-gps"),
        sa.Column("device_id", sa.String(length=120), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("assigned_vehicle", sa.String(length=180), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_location_update_id", app.models.base.GUID(), nullable=True),
        sa.Column("last_battery_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("last_accuracy_meters", sa.Numeric(8, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["last_location_update_id"],
            ["event_travel_location_updates.id"],
            name=op.f("fk_event_travel_devices_last_location_update_id_event_travel_location_updates"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_travel_devices_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["travel_plan_id"],
            ["event_travel_plans.id"],
            name=op.f("fk_event_travel_devices_travel_plan_id_event_travel_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_travel_devices")),
        sa.UniqueConstraint(
            "travel_plan_id",
            "provider",
            "device_id",
            name=op.f("uq_event_travel_devices_travel_plan_id_provider_device_id"),
        ),
    )
    for column in [
        "assigned_vehicle",
        "device_id",
        "installed_at",
        "label",
        "last_location_update_id",
        "last_seen_at",
        "organization_id",
        "provider",
        "status",
        "travel_plan_id",
    ]:
        op.create_index(op.f(f"ix_event_travel_devices_{column}"), "event_travel_devices", [column], unique=False)


def downgrade() -> None:
    for column in [
        "travel_plan_id",
        "status",
        "provider",
        "organization_id",
        "last_seen_at",
        "last_location_update_id",
        "label",
        "installed_at",
        "device_id",
        "assigned_vehicle",
    ]:
        op.drop_index(op.f(f"ix_event_travel_devices_{column}"), table_name="event_travel_devices")
    op.drop_table("event_travel_devices")
