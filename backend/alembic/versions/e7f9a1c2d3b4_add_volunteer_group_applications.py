"""add volunteer group applications

Revision ID: e7f9a1c2d3b4
Revises: d6e8f0a2b4c7
Create Date: 2026-05-29 17:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "e7f9a1c2d3b4"
down_revision: str | None = "d6e8f0a2b4c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "volunteer_group_applications",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("opportunity_id", app.models.base.GUID(), nullable=False),
        sa.Column("company_name", sa.String(length=240), nullable=False),
        sa.Column("coordinator_name", sa.String(length=240), nullable=False),
        sa.Column("coordinator_email", sa.String(length=320), nullable=False),
        sa.Column("coordinator_phone", sa.String(length=64), nullable=True),
        sa.Column("group_size", sa.Integer(), nullable=False),
        sa.Column("requested_slots", sa.Integer(), nullable=False),
        sa.Column("approved_slots", sa.Integer(), nullable=False),
        sa.Column("skills_json", sa.Text(), nullable=False),
        sa.Column("availability_json", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("reviewed_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["volunteer_opportunities.id"],
            name=op.f("fk_volunteer_group_applications_opportunity_id_volunteer_opportunities"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_volunteer_group_applications_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_person_id"],
            ["persons.id"],
            name=op.f("fk_volunteer_group_applications_reviewed_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_volunteer_group_applications")),
    )
    for column in [
        "company_name",
        "coordinator_email",
        "coordinator_name",
        "opportunity_id",
        "organization_id",
        "reviewed_at",
        "reviewed_by_person_id",
        "status",
    ]:
        op.create_index(op.f(f"ix_volunteer_group_applications_{column}"), "volunteer_group_applications", [column])


def downgrade() -> None:
    for column in [
        "status",
        "reviewed_by_person_id",
        "reviewed_at",
        "organization_id",
        "opportunity_id",
        "coordinator_name",
        "coordinator_email",
        "company_name",
    ]:
        op.drop_index(op.f(f"ix_volunteer_group_applications_{column}"), table_name="volunteer_group_applications")
    op.drop_table("volunteer_group_applications")
