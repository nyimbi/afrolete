"""add facility maintenance schedules

Revision ID: a453b20260530
Revises: a452b20260530
Create Date: 2026-05-30 17:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a453b20260530"
down_revision: str | None = "a452b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "facility_maintenance_schedules",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("equipment_item_id", app.models.base.GUID(), nullable=True),
        sa.Column("assigned_to_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("frequency", sa.String(length=40), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vendor", sa.String(length=180), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("safety_related", sa.Boolean(), nullable=False),
        sa.Column("compliance_reference", sa.String(length=240), nullable=True),
        sa.Column("condition_metric", sa.String(length=120), nullable=True),
        sa.Column("condition_threshold", sa.String(length=120), nullable=True),
        sa.Column("warranty_expires_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to_person_id"], ["persons.id"], name=op.f("fk_facility_maintenance_schedules_assigned_to_person_id_persons")),
        sa.ForeignKeyConstraint(["equipment_item_id"], ["equipment_items.id"], name=op.f("fk_facility_maintenance_schedules_equipment_item_id_equipment_items")),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_facility_maintenance_schedules_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_facility_maintenance_schedules_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_maintenance_schedules")),
    )
    for column in [
        "assigned_to_person_id",
        "category",
        "equipment_item_id",
        "facility_id",
        "frequency",
        "last_completed_at",
        "last_generated_at",
        "next_due_at",
        "organization_id",
        "safety_related",
        "status",
        "title",
        "vendor",
        "warranty_expires_on",
    ]:
        op.create_index(op.f(f"ix_facility_maintenance_schedules_{column}"), "facility_maintenance_schedules", [column])
    op.add_column(
        "maintenance_work_orders",
        sa.Column("facility_maintenance_schedule_id", app.models.base.GUID(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_maintenance_work_orders_facility_maintenance_schedule_id_facility_maintenance_schedules"),
        "maintenance_work_orders",
        "facility_maintenance_schedules",
        ["facility_maintenance_schedule_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_maintenance_work_orders_facility_maintenance_schedule_id"),
        "maintenance_work_orders",
        ["facility_maintenance_schedule_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_maintenance_work_orders_facility_maintenance_schedule_id"), table_name="maintenance_work_orders")
    op.drop_constraint(
        op.f("fk_maintenance_work_orders_facility_maintenance_schedule_id_facility_maintenance_schedules"),
        "maintenance_work_orders",
        type_="foreignkey",
    )
    op.drop_column("maintenance_work_orders", "facility_maintenance_schedule_id")
    for column in [
        "warranty_expires_on",
        "vendor",
        "title",
        "status",
        "safety_related",
        "organization_id",
        "next_due_at",
        "last_generated_at",
        "last_completed_at",
        "frequency",
        "facility_id",
        "equipment_item_id",
        "category",
        "assigned_to_person_id",
    ]:
        op.drop_index(op.f(f"ix_facility_maintenance_schedules_{column}"), table_name="facility_maintenance_schedules")
    op.drop_table("facility_maintenance_schedules")
