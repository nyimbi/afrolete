"""add organization financial aid programs

Revision ID: a512b20260531
Revises: a511b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a512b20260531"
down_revision: str | Sequence[str] | None = "a511b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_financial_aid_programs",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("program_type", sa.String(80), nullable=False, server_default="need_based"),
        sa.Column("sport", sa.String(80), nullable=True),
        sa.Column("age_group", sa.String(80), nullable=True),
        sa.Column("fund_source", sa.String(180), nullable=True),
        sa.Column("annual_budget", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("budget_awarded", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="KES"),
        sa.Column("awards_available", sa.Integer(), nullable=True),
        sa.Column("awards_made", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("minimum_score", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("application_opens_on", sa.Date(), nullable=True),
        sa.Column("application_deadline_on", sa.Date(), nullable=True),
        sa.Column("awards_announced_on", sa.Date(), nullable=True),
        sa.Column("eligibility_criteria", sa.Text(), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_organization_financial_aid_programs_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_financial_aid_programs")),
        sa.UniqueConstraint("organization_id", "name", name=op.f("uq_organization_financial_aid_programs_organization_id")),
    )
    for column in (
        "organization_id",
        "name",
        "program_type",
        "sport",
        "age_group",
        "fund_source",
        "application_opens_on",
        "application_deadline_on",
        "awards_announced_on",
        "status",
    ):
        op.create_index(op.f(f"ix_organization_financial_aid_programs_{column}"), "organization_financial_aid_programs", [column])

    op.create_table(
        "organization_financial_aid_applications",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("program_id", GUID(), nullable=False),
        sa.Column("applicant_person_id", GUID(), nullable=True),
        sa.Column("athlete_profile_id", GUID(), nullable=True),
        sa.Column("member_subscription_id", GUID(), nullable=True),
        sa.Column("household_income", sa.Numeric(12, 2), nullable=True),
        sa.Column("household_size", sa.Integer(), nullable=True),
        sa.Column("government_assistance", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("academic_summary", sa.Text(), nullable=True),
        sa.Column("athletic_summary", sa.Text(), nullable=True),
        sa.Column("financial_need_summary", sa.Text(), nullable=True),
        sa.Column("personal_statement", sa.Text(), nullable=True),
        sa.Column("amount_requested", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_awarded", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("amount_applied", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="KES"),
        sa.Column("eligibility_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_score", sa.Integer(), nullable=True),
        sa.Column("committee_recommendation", sa.Text(), nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="submitted"),
        sa.Column("submitted_on", sa.Date(), nullable=True),
        sa.Column("decided_on", sa.Date(), nullable=True),
        sa.Column("decided_by_person_id", GUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["applicant_person_id"], ["persons.id"], name=op.f("fk_organization_financial_aid_applications_applicant_person_id_persons")),
        sa.ForeignKeyConstraint(["athlete_profile_id"], ["athlete_profiles.id"], name=op.f("fk_organization_financial_aid_applications_athlete_profile_id_athlete_profiles")),
        sa.ForeignKeyConstraint(["decided_by_person_id"], ["persons.id"], name=op.f("fk_organization_financial_aid_applications_decided_by_person_id_persons")),
        sa.ForeignKeyConstraint(["member_subscription_id"], ["member_subscriptions.id"], name=op.f("fk_organization_financial_aid_applications_member_subscription_id_member_subscriptions")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_organization_financial_aid_applications_organization_id_organizations")),
        sa.ForeignKeyConstraint(["program_id"], ["organization_financial_aid_programs.id"], name=op.f("fk_organization_financial_aid_applications_program_id_organization_financial_aid_programs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_financial_aid_applications")),
    )
    for column in (
        "organization_id",
        "program_id",
        "applicant_person_id",
        "athlete_profile_id",
        "member_subscription_id",
        "government_assistance",
        "eligibility_score",
        "status",
        "submitted_on",
        "decided_on",
        "decided_by_person_id",
    ):
        op.create_index(op.f(f"ix_organization_financial_aid_applications_{column}"), "organization_financial_aid_applications", [column])


def downgrade() -> None:
    for column in (
        "decided_by_person_id",
        "decided_on",
        "submitted_on",
        "status",
        "eligibility_score",
        "government_assistance",
        "member_subscription_id",
        "athlete_profile_id",
        "applicant_person_id",
        "program_id",
        "organization_id",
    ):
        op.drop_index(op.f(f"ix_organization_financial_aid_applications_{column}"), table_name="organization_financial_aid_applications")
    op.drop_table("organization_financial_aid_applications")
    for column in (
        "status",
        "awards_announced_on",
        "application_deadline_on",
        "application_opens_on",
        "fund_source",
        "age_group",
        "sport",
        "program_type",
        "name",
        "organization_id",
    ):
        op.drop_index(op.f(f"ix_organization_financial_aid_programs_{column}"), table_name="organization_financial_aid_programs")
    op.drop_table("organization_financial_aid_programs")
