"""add event travel location updates

Revision ID: 6b8f0d4e12a7
Revises: 3c27e8f91b04
Create Date: 2026-05-28 04:05:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "6b8f0d4e12a7"
down_revision: str | None = "3c27e8f91b04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_travel_location_updates",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("travel_plan_id", app.models.base.GUID(), nullable=False),
        sa.Column("phase", sa.String(length=40), nullable=False, server_default="en_route"),
        sa.Column("source", sa.String(length=80), nullable=False, server_default="manual"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("speed_kph", sa.Numeric(6, 2), nullable=True),
        sa.Column("heading_degrees", sa.Numeric(6, 2), nullable=True),
        sa.Column("notification_message_id", app.models.base.GUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["notification_message_id"],
            ["communication_messages.id"],
            name=op.f("fk_event_travel_location_updates_notification_message_id_communication_messages"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_travel_location_updates_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by_person_id"],
            ["persons.id"],
            name=op.f("fk_event_travel_location_updates_recorded_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["travel_plan_id"],
            ["event_travel_plans.id"],
            name=op.f("fk_event_travel_location_updates_travel_plan_id_event_travel_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_travel_location_updates")),
    )
    for column in [
        "notification_message_id",
        "organization_id",
        "phase",
        "recorded_at",
        "recorded_by_person_id",
        "source",
        "travel_plan_id",
    ]:
        op.create_index(
            op.f(f"ix_event_travel_location_updates_{column}"),
            "event_travel_location_updates",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "travel_plan_id",
        "source",
        "recorded_by_person_id",
        "recorded_at",
        "phase",
        "organization_id",
        "notification_message_id",
    ]:
        op.drop_index(op.f(f"ix_event_travel_location_updates_{column}"), table_name="event_travel_location_updates")
    op.drop_table("event_travel_location_updates")
