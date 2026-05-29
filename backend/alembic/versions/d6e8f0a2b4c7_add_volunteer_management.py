"""add volunteer management

Revision ID: d6e8f0a2b4c7
Revises: c5f7a9b1d3e6
Create Date: 2026-05-29 16:20:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d6e8f0a2b4c7"
down_revision: str | None = "c5f7a9b1d3e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


MEMBERSHIP_ROLES = "'owner','admin','coach','staff','athlete','guardian','volunteer','viewer','agent'"
OLD_MEMBERSHIP_ROLES = "'owner','admin','coach','staff','athlete','guardian','viewer','agent'"


def upgrade() -> None:
    op.drop_constraint("membershiprole", "memberships", type_="check")
    op.create_check_constraint("membershiprole", "memberships", f"role IN ({MEMBERSHIP_ROLES})")

    op.create_table(
        "volunteer_profiles",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=False),
        sa.Column("volunteer_type", sa.String(length=80), nullable=False),
        sa.Column("certification_level", sa.String(length=120), nullable=True),
        sa.Column("availability_json", sa.Text(), nullable=False),
        sa.Column("skills_json", sa.Text(), nullable=False),
        sa.Column("background_check_status", sa.String(length=40), nullable=False),
        sa.Column("background_check_expires_on", sa.Date(), nullable=True),
        sa.Column("training_status", sa.String(length=40), nullable=False),
        sa.Column("onboarding_status", sa.String(length=40), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.Column("emergency_contact", sa.String(length=240), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_volunteer_profiles_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_volunteer_profiles_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_volunteer_profiles")),
        sa.UniqueConstraint("organization_id", "person_id", name="uq_volunteer_profiles_org_person"),
    )
    for column in [
        "background_check_expires_on",
        "background_check_status",
        "certification_level",
        "onboarding_status",
        "organization_id",
        "person_id",
        "status",
        "training_status",
        "volunteer_type",
    ]:
        op.create_index(op.f(f"ix_volunteer_profiles_{column}"), "volunteer_profiles", [column])

    op.create_table(
        "volunteer_opportunities",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("team_id", app.models.base.GUID(), nullable=True),
        sa.Column("event_id", app.models.base.GUID(), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("role_type", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("required_skills_json", sa.Text(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location", sa.String(length=240), nullable=True),
        sa.Column("slots_required", sa.Integer(), nullable=False),
        sa.Column("min_age", sa.Integer(), nullable=True),
        sa.Column("background_check_required", sa.Boolean(), nullable=False),
        sa.Column("training_required", sa.Boolean(), nullable=False),
        sa.Column("public_signup", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name=op.f("fk_volunteer_opportunities_event_id_events")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_volunteer_opportunities_organization_id_organizations")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_volunteer_opportunities_team_id_teams")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_volunteer_opportunities")),
    )
    for column in ["ends_at", "event_id", "organization_id", "priority", "role_type", "starts_at", "status", "team_id", "title"]:
        op.create_index(op.f(f"ix_volunteer_opportunities_{column}"), "volunteer_opportunities", [column])

    op.create_table(
        "volunteer_assignments",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("opportunity_id", app.models.base.GUID(), nullable=False),
        sa.Column("volunteer_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=False),
        sa.Column("assigned_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hours_logged", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_person_id"], ["persons.id"], name=op.f("fk_volunteer_assignments_assigned_by_person_id_persons")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["volunteer_opportunities.id"], name=op.f("fk_volunteer_assignments_opportunity_id_volunteer_opportunities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_volunteer_assignments_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_volunteer_assignments_person_id_persons")),
        sa.ForeignKeyConstraint(["volunteer_profile_id"], ["volunteer_profiles.id"], name=op.f("fk_volunteer_assignments_volunteer_profile_id_volunteer_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_volunteer_assignments")),
        sa.UniqueConstraint("opportunity_id", "volunteer_profile_id", name="uq_volunteer_assignments_opportunity_profile"),
    )
    for column in ["assigned_by_person_id", "opportunity_id", "organization_id", "person_id", "status", "volunteer_profile_id"]:
        op.create_index(op.f(f"ix_volunteer_assignments_{column}"), "volunteer_assignments", [column])

    op.create_table(
        "volunteer_training_records",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("volunteer_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("module_name", sa.String(length=200), nullable=False),
        sa.Column("role_type", sa.String(length=80), nullable=True),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("certificate_url", sa.String(length=500), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_volunteer_training_records_organization_id_organizations")),
        sa.ForeignKeyConstraint(["volunteer_profile_id"], ["volunteer_profiles.id"], name=op.f("fk_volunteer_training_records_volunteer_profile_id_volunteer_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_volunteer_training_records")),
    )
    for column in ["assigned_at", "completed_at", "expires_on", "module_name", "organization_id", "role_type", "status", "volunteer_profile_id"]:
        op.create_index(op.f(f"ix_volunteer_training_records_{column}"), "volunteer_training_records", [column])

    op.create_table(
        "volunteer_recognitions",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("volunteer_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("recognition_type", sa.String(length=80), nullable=False),
        sa.Column("badge_code", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("awarded_on", sa.Date(), nullable=False),
        sa.Column("source_summary", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_volunteer_recognitions_organization_id_organizations")),
        sa.ForeignKeyConstraint(["volunteer_profile_id"], ["volunteer_profiles.id"], name=op.f("fk_volunteer_recognitions_volunteer_profile_id_volunteer_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_volunteer_recognitions")),
    )
    for column in ["awarded_on", "badge_code", "organization_id", "recognition_type", "volunteer_profile_id"]:
        op.create_index(op.f(f"ix_volunteer_recognitions_{column}"), "volunteer_recognitions", [column])


def downgrade() -> None:
    for table, columns in [
        ("volunteer_recognitions", ["volunteer_profile_id", "recognition_type", "organization_id", "badge_code", "awarded_on"]),
        ("volunteer_training_records", ["volunteer_profile_id", "status", "role_type", "organization_id", "module_name", "expires_on", "completed_at", "assigned_at"]),
        ("volunteer_assignments", ["volunteer_profile_id", "status", "person_id", "organization_id", "opportunity_id", "assigned_by_person_id"]),
        ("volunteer_opportunities", ["title", "team_id", "status", "starts_at", "role_type", "priority", "organization_id", "event_id", "ends_at"]),
        ("volunteer_profiles", ["volunteer_type", "training_status", "status", "person_id", "organization_id", "onboarding_status", "certification_level", "background_check_status", "background_check_expires_on"]),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)

    op.drop_constraint("membershiprole", "memberships", type_="check")
    op.create_check_constraint("membershiprole", "memberships", f"role IN ({OLD_MEMBERSHIP_ROLES})")
