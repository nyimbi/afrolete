"""add volunteer substitute pool

Revision ID: fa2b3c4d5e6a
Revises: f8a2c3d4e5b6
Create Date: 2026-05-29 20:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "fa2b3c4d5e6a"
down_revision: str | None = "f8a2c3d4e5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "volunteer_substitute_pool_members",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("volunteer_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("team_id", app.models.base.GUID(), nullable=True),
        sa.Column("role_type", sa.String(length=80), nullable=False),
        sa.Column("availability_json", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("max_dispatches_per_month", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_volunteer_substitute_pool_members_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["teams.id"],
            name=op.f("fk_volunteer_substitute_pool_members_team_id_teams"),
        ),
        sa.ForeignKeyConstraint(
            ["volunteer_profile_id"],
            ["volunteer_profiles.id"],
            name=op.f("fk_volunteer_substitute_pool_members_volunteer_profile_id_volunteer_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_volunteer_substitute_pool_members")),
        sa.UniqueConstraint(
            "organization_id",
            "volunteer_profile_id",
            "team_id",
            "role_type",
            name="uq_volunteer_substitute_pool_org_profile_team_role",
        ),
    )
    for column in [
        "last_contacted_at",
        "organization_id",
        "priority",
        "role_type",
        "status",
        "team_id",
        "volunteer_profile_id",
    ]:
        op.create_index(
            op.f(f"ix_volunteer_substitute_pool_members_{column}"),
            "volunteer_substitute_pool_members",
            [column],
        )


def downgrade() -> None:
    for column in [
        "volunteer_profile_id",
        "team_id",
        "status",
        "role_type",
        "priority",
        "organization_id",
        "last_contacted_at",
    ]:
        op.drop_index(
            op.f(f"ix_volunteer_substitute_pool_members_{column}"),
            table_name="volunteer_substitute_pool_members",
        )
    op.drop_table("volunteer_substitute_pool_members")
