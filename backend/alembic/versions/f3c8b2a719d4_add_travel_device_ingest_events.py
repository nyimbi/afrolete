"""add travel device ingest events

Revision ID: f3c8b2a719d4
Revises: e4b91c0f2a63
Create Date: 2026-05-28 06:20:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "f3c8b2a719d4"
down_revision: str | None = "e4b91c0f2a63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_travel_device_ingest_events",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("travel_plan_id", app.models.base.GUID(), nullable=False),
        sa.Column("travel_device_id", app.models.base.GUID(), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("device_id", sa.String(length=120), nullable=False),
        sa.Column("external_event_id", sa.String(length=160), nullable=False),
        sa.Column("location_update_id", app.models.base.GUID(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signature_validated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["location_update_id"],
            ["event_travel_location_updates.id"],
            name=op.f("fk_event_travel_device_ingest_events_location_update_id_event_travel_location_updates"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_travel_device_ingest_events_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["travel_device_id"],
            ["event_travel_devices.id"],
            name=op.f("fk_event_travel_device_ingest_events_travel_device_id_event_travel_devices"),
        ),
        sa.ForeignKeyConstraint(
            ["travel_plan_id"],
            ["event_travel_plans.id"],
            name=op.f("fk_event_travel_device_ingest_events_travel_plan_id_event_travel_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_travel_device_ingest_events")),
        sa.UniqueConstraint(
            "travel_plan_id",
            "provider",
            "device_id",
            "external_event_id",
            name=op.f("uq_event_travel_device_ingest_events_travel_plan_id_provider_device_id_external_event_id"),
        ),
    )
    for column in [
        "device_id",
        "external_event_id",
        "location_update_id",
        "organization_id",
        "provider",
        "received_at",
        "signature_validated",
        "travel_device_id",
        "travel_plan_id",
    ]:
        op.create_index(
            op.f(f"ix_event_travel_device_ingest_events_{column}"),
            "event_travel_device_ingest_events",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "travel_plan_id",
        "travel_device_id",
        "signature_validated",
        "received_at",
        "provider",
        "organization_id",
        "location_update_id",
        "external_event_id",
        "device_id",
    ]:
        op.drop_index(op.f(f"ix_event_travel_device_ingest_events_{column}"), table_name="event_travel_device_ingest_events")
    op.drop_table("event_travel_device_ingest_events")
