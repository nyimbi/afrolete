"""add organization programs seasons groups

Revision ID: a488b20260531
Revises: a487b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.models.base import GUID


revision: str = "a488b20260531"
down_revision: str | None = "a487b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_programs",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("program_type", sa.String(length=80), nullable=False),
        sa.Column("sport", sa.String(length=80), nullable=True),
        sa.Column("age_group", sa.String(length=80), nullable=True),
        sa.Column("gender_category", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("starts_on", sa.Date(), nullable=True),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_organization_programs_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_programs")),
        sa.UniqueConstraint("organization_id", "name", name=op.f("uq_organization_programs_organization_id")),
    )
    for column in ["organization_id", "name", "program_type", "sport", "age_group", "gender_category", "starts_on", "ends_on", "status"]:
        op.create_index(op.f(f"ix_organization_programs_{column}"), "organization_programs", [column])

    op.create_table(
        "organization_seasons",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("sport", sa.String(length=80), nullable=True),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("registration_opens_on", sa.Date(), nullable=True),
        sa.Column("registration_closes_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_organization_seasons_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_seasons")),
        sa.UniqueConstraint("organization_id", "name", name=op.f("uq_organization_seasons_organization_id")),
    )
    for column in ["organization_id", "name", "sport", "starts_on", "ends_on", "registration_opens_on", "registration_closes_on", "status"]:
        op.create_index(op.f(f"ix_organization_seasons_{column}"), "organization_seasons", [column])

    op.create_table(
        "organization_groups",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("program_id", GUID(), nullable=True),
        sa.Column("season_id", GUID(), nullable=True),
        sa.Column("team_id", GUID(), nullable=True),
        sa.Column("lead_person_id", GUID(), nullable=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("group_type", sa.String(length=80), nullable=False),
        sa.Column("sport", sa.String(length=80), nullable=True),
        sa.Column("age_group", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["lead_person_id"], ["persons.id"], name=op.f("fk_organization_groups_lead_person_id_persons")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_organization_groups_organization_id_organizations")),
        sa.ForeignKeyConstraint(["program_id"], ["organization_programs.id"], name=op.f("fk_organization_groups_program_id_organization_programs")),
        sa.ForeignKeyConstraint(["season_id"], ["organization_seasons.id"], name=op.f("fk_organization_groups_season_id_organization_seasons")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_organization_groups_team_id_teams")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_groups")),
        sa.UniqueConstraint("organization_id", "name", name=op.f("uq_organization_groups_organization_id")),
    )
    for column in ["organization_id", "program_id", "season_id", "team_id", "lead_person_id", "name", "group_type", "sport", "age_group", "status"]:
        op.create_index(op.f(f"ix_organization_groups_{column}"), "organization_groups", [column])

    op.create_table(
        "organization_group_memberships",
        sa.Column("group_id", GUID(), nullable=False),
        sa.Column("subject_type", sa.String(length=12), nullable=False),
        sa.Column("subject_id", GUID(), nullable=False),
        sa.Column("role", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["organization_groups.id"], name=op.f("fk_organization_group_memberships_group_id_organization_groups")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_group_memberships")),
        sa.UniqueConstraint("group_id", "subject_type", "subject_id", "role", name="uq_organization_group_memberships_subject_role"),
    )
    for column in ["group_id", "subject_type", "subject_id", "role", "status"]:
        op.create_index(op.f(f"ix_organization_group_memberships_{column}"), "organization_group_memberships", [column])


def downgrade() -> None:
    for column in ["status", "role", "subject_id", "subject_type", "group_id"]:
        op.drop_index(op.f(f"ix_organization_group_memberships_{column}"), table_name="organization_group_memberships")
    op.drop_table("organization_group_memberships")

    for column in ["status", "age_group", "sport", "group_type", "name", "lead_person_id", "team_id", "season_id", "program_id", "organization_id"]:
        op.drop_index(op.f(f"ix_organization_groups_{column}"), table_name="organization_groups")
    op.drop_table("organization_groups")

    for column in ["status", "registration_closes_on", "registration_opens_on", "ends_on", "starts_on", "sport", "name", "organization_id"]:
        op.drop_index(op.f(f"ix_organization_seasons_{column}"), table_name="organization_seasons")
    op.drop_table("organization_seasons")

    for column in ["status", "ends_on", "starts_on", "gender_category", "age_group", "sport", "program_type", "name", "organization_id"]:
        op.drop_index(op.f(f"ix_organization_programs_{column}"), table_name="organization_programs")
    op.drop_table("organization_programs")
