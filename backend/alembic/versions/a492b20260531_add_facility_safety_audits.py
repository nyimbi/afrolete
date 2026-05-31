"""add facility safety audits

Revision ID: a492b20260531
Revises: a491b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.models.base import GUID


revision: str = "a492b20260531"
down_revision: str | None = "a491b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


AUDIT_INDEXES = [
    "organization_id",
    "facility_id",
    "equipment_item_id",
    "facility_maintenance_schedule_id",
    "auditor_person_id",
    "audit_type",
    "standard_ref",
    "status",
    "risk_level",
    "scheduled_for",
    "started_at",
    "completed_at",
]

FINDING_INDEXES = [
    "organization_id",
    "audit_id",
    "work_order_id",
    "checklist_section",
    "result",
    "severity",
    "status",
    "assigned_to_person_id",
    "due_at",
    "closed_at",
]


def create_indexes(table_name: str, columns: list[str]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table_name}_{column}"), table_name, [column])


def drop_indexes(table_name: str, columns: list[str]) -> None:
    for column in reversed(columns):
        op.drop_index(op.f(f"ix_{table_name}_{column}"), table_name=table_name)


def upgrade() -> None:
    op.create_table(
        "facility_safety_audits",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("facility_id", GUID(), nullable=True),
        sa.Column("equipment_item_id", GUID(), nullable=True),
        sa.Column("facility_maintenance_schedule_id", GUID(), nullable=True),
        sa.Column("auditor_person_id", GUID(), nullable=True),
        sa.Column("audit_type", sa.String(length=100), nullable=False),
        sa.Column("standard_ref", sa.String(length=240), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("pass_count", sa.Integer(), nullable=False),
        sa.Column("warning_count", sa.Integer(), nullable=False),
        sa.Column("fail_count", sa.Integer(), nullable=False),
        sa.Column("corrective_action_count", sa.Integer(), nullable=False),
        sa.Column("location_detail", sa.String(length=240), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_facility_safety_audits_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["facility_id"],
            ["facilities.id"],
            name=op.f("fk_facility_safety_audits_facility_id_facilities"),
        ),
        sa.ForeignKeyConstraint(
            ["equipment_item_id"],
            ["equipment_items.id"],
            name=op.f("fk_facility_safety_audits_equipment_item_id_equipment_items"),
        ),
        sa.ForeignKeyConstraint(
            ["facility_maintenance_schedule_id"],
            ["facility_maintenance_schedules.id"],
            name=op.f("fk_facility_safety_audits_facility_maintenance_schedule_id_facility_maintenance_schedules"),
        ),
        sa.ForeignKeyConstraint(
            ["auditor_person_id"],
            ["persons.id"],
            name=op.f("fk_facility_safety_audits_auditor_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_safety_audits")),
    )
    create_indexes("facility_safety_audits", AUDIT_INDEXES)

    op.create_table(
        "facility_safety_audit_findings",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("audit_id", GUID(), nullable=False),
        sa.Column("work_order_id", GUID(), nullable=True),
        sa.Column("checklist_section", sa.String(length=160), nullable=False),
        sa.Column("checklist_item", sa.String(length=240), nullable=False),
        sa.Column("result", sa.String(length=40), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("risk_rating", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("corrective_action", sa.Text(), nullable=True),
        sa.Column("assigned_to_person_id", GUID(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_facility_safety_audit_findings_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["audit_id"],
            ["facility_safety_audits.id"],
            name=op.f("fk_facility_safety_audit_findings_audit_id_facility_safety_audits"),
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            name=op.f("fk_facility_safety_audit_findings_work_order_id_maintenance_work_orders"),
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to_person_id"],
            ["persons.id"],
            name=op.f("fk_facility_safety_audit_findings_assigned_to_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_safety_audit_findings")),
        sa.UniqueConstraint(
            "audit_id",
            "checklist_section",
            "checklist_item",
            name=op.f("uq_safety_audit_finding_item"),
        ),
    )
    create_indexes("facility_safety_audit_findings", FINDING_INDEXES)


def downgrade() -> None:
    drop_indexes("facility_safety_audit_findings", FINDING_INDEXES)
    op.drop_table("facility_safety_audit_findings")
    drop_indexes("facility_safety_audits", AUDIT_INDEXES)
    op.drop_table("facility_safety_audits")
