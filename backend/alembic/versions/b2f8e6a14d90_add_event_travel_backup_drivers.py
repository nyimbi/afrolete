"""add event travel backup drivers

Revision ID: b2f8e6a14d90
Revises: a7d9c3e5b621
Create Date: 2026-05-28 06:55:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "b2f8e6a14d90"
down_revision: str | None = "a7d9c3e5b621"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_travel_backup_drivers",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("travel_plan_id", app.models.base.GUID(), nullable=False),
        sa.Column("driver_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("driver_name", sa.String(length=160), nullable=False),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("vehicle_label", sa.String(length=180), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("license_status", sa.String(length=80), nullable=False, server_default="unverified"),
        sa.Column("background_check_status", sa.String(length=80), nullable=False, server_default="unverified"),
        sa.Column("availability_status", sa.String(length=40), nullable=False, server_default="standby"),
        sa.Column("response_minutes", sa.Integer(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["driver_person_id"],
            ["persons.id"],
            name=op.f("fk_event_travel_backup_drivers_driver_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_travel_backup_drivers_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["travel_plan_id"],
            ["event_travel_plans.id"],
            name=op.f("fk_event_travel_backup_drivers_travel_plan_id_event_travel_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_travel_backup_drivers")),
    )
    for column in [
        "availability_status",
        "background_check_status",
        "driver_name",
        "driver_person_id",
        "license_status",
        "organization_id",
        "phone",
        "priority",
        "travel_plan_id",
        "vehicle_label",
    ]:
        op.create_index(
            op.f(f"ix_event_travel_backup_drivers_{column}"),
            "event_travel_backup_drivers",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "vehicle_label",
        "travel_plan_id",
        "priority",
        "phone",
        "organization_id",
        "license_status",
        "driver_person_id",
        "driver_name",
        "background_check_status",
        "availability_status",
    ]:
        op.drop_index(op.f(f"ix_event_travel_backup_drivers_{column}"), table_name="event_travel_backup_drivers")
    op.drop_table("event_travel_backup_drivers")
