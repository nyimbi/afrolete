"""add backup driver dispatch fields

Revision ID: d4b7c1a8f2e3
Revises: b2f8e6a14d90
Create Date: 2026-05-28 07:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d4b7c1a8f2e3"
down_revision: str | None = "b2f8e6a14d90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("event_travel_backup_drivers", sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "event_travel_backup_drivers",
        sa.Column("dispatched_by_person_id", app.models.base.GUID(), nullable=True),
    )
    op.add_column(
        "event_travel_backup_drivers",
        sa.Column("dispatch_message_id", app.models.base.GUID(), nullable=True),
    )
    op.add_column("event_travel_backup_drivers", sa.Column("dispatch_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        op.f("fk_event_travel_backup_drivers_dispatched_by_person_id_persons"),
        "event_travel_backup_drivers",
        "persons",
        ["dispatched_by_person_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_event_travel_backup_drivers_dispatch_message_id_communication_messages"),
        "event_travel_backup_drivers",
        "communication_messages",
        ["dispatch_message_id"],
        ["id"],
    )
    for column in ["dispatch_message_id", "dispatched_at", "dispatched_by_person_id"]:
        op.create_index(
            op.f(f"ix_event_travel_backup_drivers_{column}"),
            "event_travel_backup_drivers",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in ["dispatched_by_person_id", "dispatched_at", "dispatch_message_id"]:
        op.drop_index(op.f(f"ix_event_travel_backup_drivers_{column}"), table_name="event_travel_backup_drivers")
    op.drop_constraint(
        op.f("fk_event_travel_backup_drivers_dispatch_message_id_communication_messages"),
        "event_travel_backup_drivers",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_event_travel_backup_drivers_dispatched_by_person_id_persons"),
        "event_travel_backup_drivers",
        type_="foreignkey",
    )
    op.drop_column("event_travel_backup_drivers", "dispatch_reason")
    op.drop_column("event_travel_backup_drivers", "dispatch_message_id")
    op.drop_column("event_travel_backup_drivers", "dispatched_by_person_id")
    op.drop_column("event_travel_backup_drivers", "dispatched_at")
