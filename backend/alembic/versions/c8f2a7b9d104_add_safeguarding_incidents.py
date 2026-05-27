"""add safeguarding incidents

Revision ID: c8f2a7b9d104
Revises: a9b23c5d7e41
Create Date: 2026-05-28 00:45:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "c8f2a7b9d104"
down_revision: str | None = "a9b23c5d7e41"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


incident_type = sa.Enum(
    "injury",
    "medical",
    "safeguarding",
    "misconduct",
    "facility",
    "transport",
    "weather",
    "other",
    name="safeguardingincidenttype",
    native_enum=False,
    create_constraint=True,
)
incident_severity = sa.Enum(
    "low",
    "medium",
    "high",
    "critical",
    name="safeguardingincidentseverity",
    native_enum=False,
    create_constraint=True,
)
incident_status = sa.Enum(
    "open",
    "triaged",
    "investigating",
    "resolved",
    "closed",
    name="safeguardingincidentstatus",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "safeguarding_incidents",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_id", app.models.base.GUID(), nullable=True),
        sa.Column("team_id", app.models.base.GUID(), nullable=True),
        sa.Column("athlete_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("reported_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("assigned_to_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("incident_type", incident_type, nullable=False),
        sa.Column("severity", incident_severity, nullable=False),
        sa.Column("status", incident_status, nullable=False, server_default="open"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=240), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("immediate_action", sa.Text(), nullable=True),
        sa.Column("parent_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("medical_follow_up_required", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("regulatory_report_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["assigned_to_person_id"],
            ["persons.id"],
            name=op.f("fk_safeguarding_incidents_assigned_to_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["athlete_person_id"],
            ["persons.id"],
            name=op.f("fk_safeguarding_incidents_athlete_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name=op.f("fk_safeguarding_incidents_event_id_events")),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_safeguarding_incidents_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["reported_by_person_id"],
            ["persons.id"],
            name=op.f("fk_safeguarding_incidents_reported_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_safeguarding_incidents_team_id_teams")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_safeguarding_incidents")),
    )
    for column in [
        "assigned_to_person_id",
        "athlete_person_id",
        "event_id",
        "incident_type",
        "medical_follow_up_required",
        "occurred_at",
        "organization_id",
        "regulatory_report_required",
        "reported_by_person_id",
        "resolved_at",
        "severity",
        "status",
        "team_id",
        "title",
    ]:
        op.create_index(op.f(f"ix_safeguarding_incidents_{column}"), "safeguarding_incidents", [column], unique=False)


def downgrade() -> None:
    for column in [
        "title",
        "team_id",
        "status",
        "severity",
        "resolved_at",
        "reported_by_person_id",
        "regulatory_report_required",
        "organization_id",
        "occurred_at",
        "medical_follow_up_required",
        "incident_type",
        "event_id",
        "athlete_person_id",
        "assigned_to_person_id",
    ]:
        op.drop_index(op.f(f"ix_safeguarding_incidents_{column}"), table_name="safeguarding_incidents")
    op.drop_table("safeguarding_incidents")
