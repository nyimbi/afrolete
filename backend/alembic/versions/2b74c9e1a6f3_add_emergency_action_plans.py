"""add emergency action plans

Revision ID: 2b74c9e1a6f3
Revises: 1a6fb90d2e4c
Create Date: 2026-05-28 03:35:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "2b74c9e1a6f3"
down_revision: str | None = "1a6fb90d2e4c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


plan_status = sa.Enum(
    "draft",
    "active",
    "under_review",
    "retired",
    name="emergencyactionplanstatus",
    native_enum=False,
    create_constraint=True,
)
activation_status = sa.Enum(
    "active",
    "resolved",
    "cancelled",
    "reviewed",
    name="emergencyactivationstatus",
    native_enum=False,
    create_constraint=True,
)
emergency_type = sa.Enum(
    "medical",
    "fire",
    "weather",
    "security",
    "evacuation",
    "missing_person",
    "other",
    name="emergencytype",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "emergency_action_plans",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("emergency_type", emergency_type, nullable=False),
        sa.Column("status", plan_status, nullable=False, server_default="draft"),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("review_due_on", sa.Date(), nullable=True),
        sa.Column("emergency_contacts", sa.Text(), nullable=False),
        sa.Column("evacuation_routes", sa.Text(), nullable=True),
        sa.Column("medical_protocols", sa.Text(), nullable=True),
        sa.Column("weather_protocols", sa.Text(), nullable=True),
        sa.Column("communication_protocols", sa.Text(), nullable=True),
        sa.Column("equipment_locations", sa.Text(), nullable=True),
        sa.Column("assembly_points", sa.Text(), nullable=True),
        sa.Column("special_needs_plan", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["facility_id"],
            ["facilities.id"],
            name=op.f("fk_emergency_action_plans_facility_id_facilities"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_emergency_action_plans_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_emergency_action_plans")),
    )
    for column in [
        "effective_from",
        "emergency_type",
        "facility_id",
        "organization_id",
        "review_due_on",
        "status",
        "title",
    ]:
        op.create_index(op.f(f"ix_emergency_action_plans_{column}"), "emergency_action_plans", [column])

    op.create_table(
        "emergency_plan_activations",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("plan_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=True),
        sa.Column("incident_id", app.models.base.GUID(), nullable=True),
        sa.Column("activated_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("closed_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("emergency_type", emergency_type, nullable=False),
        sa.Column("status", activation_status, nullable=False, server_default="active"),
        sa.Column("location_detail", sa.String(length=240), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_responders", sa.Text(), nullable=True),
        sa.Column("guidance_steps", sa.Text(), nullable=True),
        sa.Column("communication_log", sa.Text(), nullable=True),
        sa.Column("outcome_summary", sa.Text(), nullable=True),
        sa.Column("response_time_seconds", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["activated_by_person_id"],
            ["persons.id"],
            name=op.f("fk_emergency_plan_activations_activated_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["closed_by_person_id"],
            ["persons.id"],
            name=op.f("fk_emergency_plan_activations_closed_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["facility_id"],
            ["facilities.id"],
            name=op.f("fk_emergency_plan_activations_facility_id_facilities"),
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["safeguarding_incidents.id"],
            name=op.f("fk_emergency_plan_activations_incident_id_safeguarding_incidents"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_emergency_plan_activations_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["emergency_action_plans.id"],
            name=op.f("fk_emergency_plan_activations_plan_id_emergency_action_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_emergency_plan_activations")),
    )
    for column in [
        "activated_at",
        "activated_by_person_id",
        "closed_at",
        "closed_by_person_id",
        "emergency_type",
        "facility_id",
        "incident_id",
        "organization_id",
        "plan_id",
        "status",
    ]:
        op.create_index(
            op.f(f"ix_emergency_plan_activations_{column}"),
            "emergency_plan_activations",
            [column],
        )


def downgrade() -> None:
    for column in [
        "status",
        "plan_id",
        "organization_id",
        "incident_id",
        "facility_id",
        "emergency_type",
        "closed_by_person_id",
        "closed_at",
        "activated_by_person_id",
        "activated_at",
    ]:
        op.drop_index(op.f(f"ix_emergency_plan_activations_{column}"), table_name="emergency_plan_activations")
    op.drop_table("emergency_plan_activations")

    for column in [
        "title",
        "status",
        "review_due_on",
        "organization_id",
        "facility_id",
        "emergency_type",
        "effective_from",
    ]:
        op.drop_index(op.f(f"ix_emergency_action_plans_{column}"), table_name="emergency_action_plans")
    op.drop_table("emergency_action_plans")
