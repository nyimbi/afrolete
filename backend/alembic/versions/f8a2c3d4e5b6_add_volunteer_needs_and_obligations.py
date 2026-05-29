"""add volunteer needs and obligations

Revision ID: f8a2c3d4e5b6
Revises: e7f9a1c2d3b4
Create Date: 2026-05-29 17:35:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "f8a2c3d4e5b6"
down_revision: str | None = "e7f9a1c2d3b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "volunteer_need_requests",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("team_id", app.models.base.GUID(), nullable=True),
        sa.Column("event_id", app.models.base.GUID(), nullable=True),
        sa.Column("requested_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("role_type", sa.String(length=80), nullable=False),
        sa.Column("needed_count", sa.Integer(), nullable=False),
        sa.Column("required_skills_json", sa.Text(), nullable=False),
        sa.Column("needed_by", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("opportunity_id", app.models.base.GUID(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name=op.f("fk_volunteer_need_requests_event_id_events")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["volunteer_opportunities.id"], name=op.f("fk_volunteer_need_requests_opportunity_id_volunteer_opportunities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_volunteer_need_requests_organization_id_organizations")),
        sa.ForeignKeyConstraint(["requested_by_person_id"], ["persons.id"], name=op.f("fk_volunteer_need_requests_requested_by_person_id_persons")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_volunteer_need_requests_team_id_teams")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_volunteer_need_requests")),
    )
    for column in ["event_id", "needed_by", "opportunity_id", "organization_id", "priority", "requested_by_person_id", "role_type", "status", "team_id", "title"]:
        op.create_index(op.f(f"ix_volunteer_need_requests_{column}"), "volunteer_need_requests", [column])

    op.create_table(
        "volunteer_obligations",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=False),
        sa.Column("team_id", app.models.base.GUID(), nullable=True),
        sa.Column("season_label", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("required_hours", sa.Float(), nullable=False),
        sa.Column("completed_hours", sa.Float(), nullable=False),
        sa.Column("waived_hours", sa.Float(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_volunteer_obligations_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_volunteer_obligations_person_id_persons")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_volunteer_obligations_team_id_teams")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_volunteer_obligations")),
        sa.UniqueConstraint("organization_id", "person_id", "season_label", "category", name="uq_volunteer_obligations_org_person_season_category"),
    )
    for column in ["category", "due_on", "organization_id", "person_id", "season_label", "status", "team_id"]:
        op.create_index(op.f(f"ix_volunteer_obligations_{column}"), "volunteer_obligations", [column])


def downgrade() -> None:
    for column in ["team_id", "status", "season_label", "person_id", "organization_id", "due_on", "category"]:
        op.drop_index(op.f(f"ix_volunteer_obligations_{column}"), table_name="volunteer_obligations")
    op.drop_table("volunteer_obligations")
    for column in ["title", "team_id", "status", "role_type", "requested_by_person_id", "priority", "organization_id", "opportunity_id", "needed_by", "event_id"]:
        op.drop_index(op.f(f"ix_volunteer_need_requests_{column}"), table_name="volunteer_need_requests")
    op.drop_table("volunteer_need_requests")
