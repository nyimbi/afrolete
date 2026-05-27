"""add event travel geofence zones

Revision ID: c0a4d72e9b31
Revises: b8e41a0d2c6f
Create Date: 2026-05-28 05:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "c0a4d72e9b31"
down_revision: str | None = "b8e41a0d2c6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_travel_geofence_zones",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("travel_plan_id", app.models.base.GUID(), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("center_latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("center_longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("radius_km", sa.Numeric(8, 3), nullable=False),
        sa.Column("alert_on_breach", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("channel", sa.String(length=40), nullable=False, server_default="push"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_travel_geofence_zones_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["travel_plan_id"],
            ["event_travel_plans.id"],
            name=op.f("fk_event_travel_geofence_zones_travel_plan_id_event_travel_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_travel_geofence_zones")),
        sa.UniqueConstraint(
            "travel_plan_id",
            "label",
            name=op.f("uq_event_travel_geofence_zones_travel_plan_id_label"),
        ),
    )
    for column in ["active", "alert_on_breach", "channel", "label", "organization_id", "travel_plan_id"]:
        op.create_index(
            op.f(f"ix_event_travel_geofence_zones_{column}"),
            "event_travel_geofence_zones",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in ["travel_plan_id", "organization_id", "label", "channel", "alert_on_breach", "active"]:
        op.drop_index(op.f(f"ix_event_travel_geofence_zones_{column}"), table_name="event_travel_geofence_zones")
    op.drop_table("event_travel_geofence_zones")
