"""add supporter alumni engagement

Revision ID: e4f5a6b7c8da
Revises: e3f4a5b6c7d8
Create Date: 2026-05-30 03:20:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "e4f5a6b7c8da"
down_revision: str | None = "e3f4a5b6c7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "supporter_membership_tiers",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("monthly_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("benefits", sa.Text(), nullable=False),
        sa.Column("voting_weight", sa.Integer(), nullable=False),
        sa.Column("trial_days", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_supporter_membership_tiers_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_supporter_membership_tiers")),
        sa.UniqueConstraint("organization_id", "slug", name=op.f("uq_supporter_membership_tiers_organization_id")),
    )
    op.create_index(op.f("ix_supporter_membership_tiers_name"), "supporter_membership_tiers", ["name"])
    op.create_index(op.f("ix_supporter_membership_tiers_organization_id"), "supporter_membership_tiers", ["organization_id"])
    op.create_index(op.f("ix_supporter_membership_tiers_slug"), "supporter_membership_tiers", ["slug"])
    op.create_index(op.f("ix_supporter_membership_tiers_status"), "supporter_membership_tiers", ["status"])

    op.create_table(
        "supporter_profiles",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=True),
        sa.Column("tier_id", app.models.base.GUID(), nullable=True),
        sa.Column("display_name", sa.String(length=180), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("engagement_points", sa.Integer(), nullable=False),
        sa.Column("lifetime_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_engagement_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_supporter_profiles_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_supporter_profiles_person_id_persons")),
        sa.ForeignKeyConstraint(["tier_id"], ["supporter_membership_tiers.id"], name=op.f("fk_supporter_profiles_tier_id_supporter_membership_tiers")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_supporter_profiles")),
        sa.UniqueConstraint("organization_id", "email", name=op.f("uq_supporter_profiles_organization_id")),
    )
    op.create_index(op.f("ix_supporter_profiles_display_name"), "supporter_profiles", ["display_name"])
    op.create_index(op.f("ix_supporter_profiles_email"), "supporter_profiles", ["email"])
    op.create_index(op.f("ix_supporter_profiles_engagement_points"), "supporter_profiles", ["engagement_points"])
    op.create_index(op.f("ix_supporter_profiles_joined_at"), "supporter_profiles", ["joined_at"])
    op.create_index(op.f("ix_supporter_profiles_last_engagement_at"), "supporter_profiles", ["last_engagement_at"])
    op.create_index(op.f("ix_supporter_profiles_organization_id"), "supporter_profiles", ["organization_id"])
    op.create_index(op.f("ix_supporter_profiles_person_id"), "supporter_profiles", ["person_id"])
    op.create_index(op.f("ix_supporter_profiles_status"), "supporter_profiles", ["status"])
    op.create_index(op.f("ix_supporter_profiles_tier_id"), "supporter_profiles", ["tier_id"])

    op.create_table(
        "supporter_engagement_activities",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("supporter_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("activity_type", sa.String(length=80), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("value_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_supporter_engagement_activities_organization_id_organizations")),
        sa.ForeignKeyConstraint(["supporter_profile_id"], ["supporter_profiles.id"], name=op.f("fk_supporter_engagement_activities_supporter_profile_id_supporter_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_supporter_engagement_activities")),
    )
    op.create_index(op.f("ix_supporter_engagement_activities_activity_type"), "supporter_engagement_activities", ["activity_type"])
    op.create_index(op.f("ix_supporter_engagement_activities_occurred_at"), "supporter_engagement_activities", ["occurred_at"])
    op.create_index(op.f("ix_supporter_engagement_activities_organization_id"), "supporter_engagement_activities", ["organization_id"])
    op.create_index(op.f("ix_supporter_engagement_activities_source"), "supporter_engagement_activities", ["source"])
    op.create_index(op.f("ix_supporter_engagement_activities_supporter_profile_id"), "supporter_engagement_activities", ["supporter_profile_id"])

    op.create_table(
        "supporter_rewards",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("supporter_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("reward_type", sa.String(length=80), nullable=False),
        sa.Column("threshold_points", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_supporter_rewards_organization_id_organizations")),
        sa.ForeignKeyConstraint(["supporter_profile_id"], ["supporter_profiles.id"], name=op.f("fk_supporter_rewards_supporter_profile_id_supporter_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_supporter_rewards")),
    )
    op.create_index(op.f("ix_supporter_rewards_organization_id"), "supporter_rewards", ["organization_id"])
    op.create_index(op.f("ix_supporter_rewards_redeemed_at"), "supporter_rewards", ["redeemed_at"])
    op.create_index(op.f("ix_supporter_rewards_reward_type"), "supporter_rewards", ["reward_type"])
    op.create_index(op.f("ix_supporter_rewards_status"), "supporter_rewards", ["status"])
    op.create_index(op.f("ix_supporter_rewards_supporter_profile_id"), "supporter_rewards", ["supporter_profile_id"])
    op.create_index(op.f("ix_supporter_rewards_title"), "supporter_rewards", ["title"])

    op.create_table(
        "alumni_profiles",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=True),
        sa.Column("display_name", sa.String(length=180), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("sports_history", sa.Text(), nullable=False),
        sa.Column("career_industry", sa.String(length=120), nullable=True),
        sa.Column("current_company", sa.String(length=180), nullable=True),
        sa.Column("current_role", sa.String(length=180), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("engagement_level", sa.String(length=40), nullable=False),
        sa.Column("lifetime_donations", sa.Numeric(12, 2), nullable=False),
        sa.Column("privacy_status", sa.String(length=40), nullable=False),
        sa.Column("last_engagement_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_alumni_profiles_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_alumni_profiles_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alumni_profiles")),
        sa.UniqueConstraint("organization_id", "email", name=op.f("uq_alumni_profiles_organization_id")),
    )
    op.create_index(op.f("ix_alumni_profiles_career_industry"), "alumni_profiles", ["career_industry"])
    op.create_index(op.f("ix_alumni_profiles_display_name"), "alumni_profiles", ["display_name"])
    op.create_index(op.f("ix_alumni_profiles_email"), "alumni_profiles", ["email"])
    op.create_index(op.f("ix_alumni_profiles_engagement_level"), "alumni_profiles", ["engagement_level"])
    op.create_index(op.f("ix_alumni_profiles_graduation_year"), "alumni_profiles", ["graduation_year"])
    op.create_index(op.f("ix_alumni_profiles_last_engagement_at"), "alumni_profiles", ["last_engagement_at"])
    op.create_index(op.f("ix_alumni_profiles_organization_id"), "alumni_profiles", ["organization_id"])
    op.create_index(op.f("ix_alumni_profiles_person_id"), "alumni_profiles", ["person_id"])
    op.create_index(op.f("ix_alumni_profiles_privacy_status"), "alumni_profiles", ["privacy_status"])

    op.create_table(
        "mentorship_programs",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("goals", sa.Text(), nullable=False),
        sa.Column("industry_focus", sa.String(length=120), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=True),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_mentorship_programs_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mentorship_programs")),
    )
    op.create_index(op.f("ix_mentorship_programs_ends_on"), "mentorship_programs", ["ends_on"])
    op.create_index(op.f("ix_mentorship_programs_industry_focus"), "mentorship_programs", ["industry_focus"])
    op.create_index(op.f("ix_mentorship_programs_name"), "mentorship_programs", ["name"])
    op.create_index(op.f("ix_mentorship_programs_organization_id"), "mentorship_programs", ["organization_id"])
    op.create_index(op.f("ix_mentorship_programs_starts_on"), "mentorship_programs", ["starts_on"])
    op.create_index(op.f("ix_mentorship_programs_status"), "mentorship_programs", ["status"])

    op.create_table(
        "mentorship_matches",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("program_id", app.models.base.GUID(), nullable=False),
        sa.Column("alumni_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("mentee_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("mentee_name", sa.String(length=180), nullable=False),
        sa.Column("mentee_interest", sa.String(length=180), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("goals", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("next_meeting_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("feedback_notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["alumni_profile_id"], ["alumni_profiles.id"], name=op.f("fk_mentorship_matches_alumni_profile_id_alumni_profiles")),
        sa.ForeignKeyConstraint(["mentee_person_id"], ["persons.id"], name=op.f("fk_mentorship_matches_mentee_person_id_persons")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_mentorship_matches_organization_id_organizations")),
        sa.ForeignKeyConstraint(["program_id"], ["mentorship_programs.id"], name=op.f("fk_mentorship_matches_program_id_mentorship_programs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mentorship_matches")),
    )
    op.create_index(op.f("ix_mentorship_matches_alumni_profile_id"), "mentorship_matches", ["alumni_profile_id"])
    op.create_index(op.f("ix_mentorship_matches_match_score"), "mentorship_matches", ["match_score"])
    op.create_index(op.f("ix_mentorship_matches_mentee_interest"), "mentorship_matches", ["mentee_interest"])
    op.create_index(op.f("ix_mentorship_matches_mentee_name"), "mentorship_matches", ["mentee_name"])
    op.create_index(op.f("ix_mentorship_matches_mentee_person_id"), "mentorship_matches", ["mentee_person_id"])
    op.create_index(op.f("ix_mentorship_matches_next_meeting_at"), "mentorship_matches", ["next_meeting_at"])
    op.create_index(op.f("ix_mentorship_matches_organization_id"), "mentorship_matches", ["organization_id"])
    op.create_index(op.f("ix_mentorship_matches_program_id"), "mentorship_matches", ["program_id"])
    op.create_index(op.f("ix_mentorship_matches_status"), "mentorship_matches", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_mentorship_matches_status"), table_name="mentorship_matches")
    op.drop_index(op.f("ix_mentorship_matches_program_id"), table_name="mentorship_matches")
    op.drop_index(op.f("ix_mentorship_matches_organization_id"), table_name="mentorship_matches")
    op.drop_index(op.f("ix_mentorship_matches_next_meeting_at"), table_name="mentorship_matches")
    op.drop_index(op.f("ix_mentorship_matches_mentee_person_id"), table_name="mentorship_matches")
    op.drop_index(op.f("ix_mentorship_matches_mentee_name"), table_name="mentorship_matches")
    op.drop_index(op.f("ix_mentorship_matches_mentee_interest"), table_name="mentorship_matches")
    op.drop_index(op.f("ix_mentorship_matches_match_score"), table_name="mentorship_matches")
    op.drop_index(op.f("ix_mentorship_matches_alumni_profile_id"), table_name="mentorship_matches")
    op.drop_table("mentorship_matches")

    op.drop_index(op.f("ix_mentorship_programs_status"), table_name="mentorship_programs")
    op.drop_index(op.f("ix_mentorship_programs_starts_on"), table_name="mentorship_programs")
    op.drop_index(op.f("ix_mentorship_programs_organization_id"), table_name="mentorship_programs")
    op.drop_index(op.f("ix_mentorship_programs_name"), table_name="mentorship_programs")
    op.drop_index(op.f("ix_mentorship_programs_industry_focus"), table_name="mentorship_programs")
    op.drop_index(op.f("ix_mentorship_programs_ends_on"), table_name="mentorship_programs")
    op.drop_table("mentorship_programs")

    op.drop_index(op.f("ix_alumni_profiles_privacy_status"), table_name="alumni_profiles")
    op.drop_index(op.f("ix_alumni_profiles_person_id"), table_name="alumni_profiles")
    op.drop_index(op.f("ix_alumni_profiles_organization_id"), table_name="alumni_profiles")
    op.drop_index(op.f("ix_alumni_profiles_last_engagement_at"), table_name="alumni_profiles")
    op.drop_index(op.f("ix_alumni_profiles_graduation_year"), table_name="alumni_profiles")
    op.drop_index(op.f("ix_alumni_profiles_engagement_level"), table_name="alumni_profiles")
    op.drop_index(op.f("ix_alumni_profiles_email"), table_name="alumni_profiles")
    op.drop_index(op.f("ix_alumni_profiles_display_name"), table_name="alumni_profiles")
    op.drop_index(op.f("ix_alumni_profiles_career_industry"), table_name="alumni_profiles")
    op.drop_table("alumni_profiles")

    op.drop_index(op.f("ix_supporter_rewards_title"), table_name="supporter_rewards")
    op.drop_index(op.f("ix_supporter_rewards_supporter_profile_id"), table_name="supporter_rewards")
    op.drop_index(op.f("ix_supporter_rewards_status"), table_name="supporter_rewards")
    op.drop_index(op.f("ix_supporter_rewards_reward_type"), table_name="supporter_rewards")
    op.drop_index(op.f("ix_supporter_rewards_redeemed_at"), table_name="supporter_rewards")
    op.drop_index(op.f("ix_supporter_rewards_organization_id"), table_name="supporter_rewards")
    op.drop_table("supporter_rewards")

    op.drop_index(op.f("ix_supporter_engagement_activities_supporter_profile_id"), table_name="supporter_engagement_activities")
    op.drop_index(op.f("ix_supporter_engagement_activities_source"), table_name="supporter_engagement_activities")
    op.drop_index(op.f("ix_supporter_engagement_activities_organization_id"), table_name="supporter_engagement_activities")
    op.drop_index(op.f("ix_supporter_engagement_activities_occurred_at"), table_name="supporter_engagement_activities")
    op.drop_index(op.f("ix_supporter_engagement_activities_activity_type"), table_name="supporter_engagement_activities")
    op.drop_table("supporter_engagement_activities")

    op.drop_index(op.f("ix_supporter_profiles_tier_id"), table_name="supporter_profiles")
    op.drop_index(op.f("ix_supporter_profiles_status"), table_name="supporter_profiles")
    op.drop_index(op.f("ix_supporter_profiles_person_id"), table_name="supporter_profiles")
    op.drop_index(op.f("ix_supporter_profiles_organization_id"), table_name="supporter_profiles")
    op.drop_index(op.f("ix_supporter_profiles_last_engagement_at"), table_name="supporter_profiles")
    op.drop_index(op.f("ix_supporter_profiles_joined_at"), table_name="supporter_profiles")
    op.drop_index(op.f("ix_supporter_profiles_engagement_points"), table_name="supporter_profiles")
    op.drop_index(op.f("ix_supporter_profiles_email"), table_name="supporter_profiles")
    op.drop_index(op.f("ix_supporter_profiles_display_name"), table_name="supporter_profiles")
    op.drop_table("supporter_profiles")

    op.drop_index(op.f("ix_supporter_membership_tiers_status"), table_name="supporter_membership_tiers")
    op.drop_index(op.f("ix_supporter_membership_tiers_slug"), table_name="supporter_membership_tiers")
    op.drop_index(op.f("ix_supporter_membership_tiers_organization_id"), table_name="supporter_membership_tiers")
    op.drop_index(op.f("ix_supporter_membership_tiers_name"), table_name="supporter_membership_tiers")
    op.drop_table("supporter_membership_tiers")
