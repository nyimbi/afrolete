"""add athlete development hub

Revision ID: a448b20260530
Revises: a447b20260530
Create Date: 2026-05-30 11:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a448b20260530"
down_revision: str | None = "a447b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "athlete_wellness_check_ins",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("submitted_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mood_score", sa.Integer(), nullable=False),
        sa.Column("stress_score", sa.Integer(), nullable=False),
        sa.Column("sleep_hours", sa.Float(), nullable=False),
        sa.Column("energy_score", sa.Integer(), nullable=False),
        sa.Column("soreness_score", sa.Integer(), nullable=False),
        sa.Column("resilience_score", sa.Integer(), nullable=True),
        sa.Column("support_requested", sa.Boolean(), nullable=False),
        sa.Column("risk_band", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["athlete_profile_id"], ["athlete_profiles.id"], name=op.f("fk_athlete_wellness_check_ins_athlete_profile_id_athlete_profiles")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_athlete_wellness_check_ins_organization_id_organizations")),
        sa.ForeignKeyConstraint(["submitted_by_person_id"], ["persons.id"], name=op.f("fk_athlete_wellness_check_ins_submitted_by_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_athlete_wellness_check_ins")),
    )
    op.create_index(op.f("ix_athlete_wellness_check_ins_athlete_profile_id"), "athlete_wellness_check_ins", ["athlete_profile_id"])
    op.create_index(op.f("ix_athlete_wellness_check_ins_check_in_at"), "athlete_wellness_check_ins", ["check_in_at"])
    op.create_index(op.f("ix_athlete_wellness_check_ins_mood_score"), "athlete_wellness_check_ins", ["mood_score"])
    op.create_index(op.f("ix_athlete_wellness_check_ins_organization_id"), "athlete_wellness_check_ins", ["organization_id"])
    op.create_index(op.f("ix_athlete_wellness_check_ins_risk_band"), "athlete_wellness_check_ins", ["risk_band"])
    op.create_index(op.f("ix_athlete_wellness_check_ins_stress_score"), "athlete_wellness_check_ins", ["stress_score"])
    op.create_index(op.f("ix_athlete_wellness_check_ins_submitted_by_person_id"), "athlete_wellness_check_ins", ["submitted_by_person_id"])
    op.create_index(op.f("ix_athlete_wellness_check_ins_support_requested"), "athlete_wellness_check_ins", ["support_requested"])

    op.create_table(
        "athlete_academic_records",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("recorded_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("school_name", sa.String(length=180), nullable=True),
        sa.Column("term_label", sa.String(length=120), nullable=False),
        sa.Column("grade_level", sa.String(length=80), nullable=True),
        sa.Column("gpa", sa.Float(), nullable=True),
        sa.Column("attendance_rate", sa.Float(), nullable=True),
        sa.Column("study_hours_weekly", sa.Float(), nullable=True),
        sa.Column("missing_assignment_count", sa.Integer(), nullable=False),
        sa.Column("eligibility_status", sa.String(length=60), nullable=False),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("next_review_on", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["athlete_profile_id"], ["athlete_profiles.id"], name=op.f("fk_athlete_academic_records_athlete_profile_id_athlete_profiles")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_athlete_academic_records_organization_id_organizations")),
        sa.ForeignKeyConstraint(["recorded_by_person_id"], ["persons.id"], name=op.f("fk_athlete_academic_records_recorded_by_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_athlete_academic_records")),
        sa.UniqueConstraint("organization_id", "athlete_profile_id", "term_label", name="uq_athlete_academic_records_term"),
    )
    op.create_index(op.f("ix_athlete_academic_records_athlete_profile_id"), "athlete_academic_records", ["athlete_profile_id"])
    op.create_index(op.f("ix_athlete_academic_records_eligibility_status"), "athlete_academic_records", ["eligibility_status"])
    op.create_index(op.f("ix_athlete_academic_records_grade_level"), "athlete_academic_records", ["grade_level"])
    op.create_index(op.f("ix_athlete_academic_records_next_review_on"), "athlete_academic_records", ["next_review_on"])
    op.create_index(op.f("ix_athlete_academic_records_organization_id"), "athlete_academic_records", ["organization_id"])
    op.create_index(op.f("ix_athlete_academic_records_recorded_by_person_id"), "athlete_academic_records", ["recorded_by_person_id"])
    op.create_index(op.f("ix_athlete_academic_records_risk_level"), "athlete_academic_records", ["risk_level"])
    op.create_index(op.f("ix_athlete_academic_records_school_name"), "athlete_academic_records", ["school_name"])
    op.create_index(op.f("ix_athlete_academic_records_term_label"), "athlete_academic_records", ["term_label"])

    op.create_table(
        "athlete_life_skill_assignments",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("assigned_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("module_code", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("level", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_person_id"], ["persons.id"], name=op.f("fk_athlete_life_skill_assignments_assigned_by_person_id_persons")),
        sa.ForeignKeyConstraint(["athlete_profile_id"], ["athlete_profiles.id"], name=op.f("fk_athlete_life_skill_assignments_athlete_profile_id_athlete_profiles")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_athlete_life_skill_assignments_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_athlete_life_skill_assignments")),
        sa.UniqueConstraint("organization_id", "athlete_profile_id", "module_code", name="uq_athlete_life_skill_assignments_module"),
    )
    op.create_index(op.f("ix_athlete_life_skill_assignments_assigned_by_person_id"), "athlete_life_skill_assignments", ["assigned_by_person_id"])
    op.create_index(op.f("ix_athlete_life_skill_assignments_athlete_profile_id"), "athlete_life_skill_assignments", ["athlete_profile_id"])
    op.create_index(op.f("ix_athlete_life_skill_assignments_category"), "athlete_life_skill_assignments", ["category"])
    op.create_index(op.f("ix_athlete_life_skill_assignments_completed_at"), "athlete_life_skill_assignments", ["completed_at"])
    op.create_index(op.f("ix_athlete_life_skill_assignments_due_on"), "athlete_life_skill_assignments", ["due_on"])
    op.create_index(op.f("ix_athlete_life_skill_assignments_level"), "athlete_life_skill_assignments", ["level"])
    op.create_index(op.f("ix_athlete_life_skill_assignments_module_code"), "athlete_life_skill_assignments", ["module_code"])
    op.create_index(op.f("ix_athlete_life_skill_assignments_organization_id"), "athlete_life_skill_assignments", ["organization_id"])
    op.create_index(op.f("ix_athlete_life_skill_assignments_status"), "athlete_life_skill_assignments", ["status"])

    op.create_table(
        "athlete_scholarship_applications",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("created_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("program_name", sa.String(length=220), nullable=False),
        sa.Column("scholarship_type", sa.String(length=80), nullable=False),
        sa.Column("donor_or_fund", sa.String(length=220), nullable=True),
        sa.Column("amount_requested", sa.Float(), nullable=False),
        sa.Column("amount_awarded", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("eligibility_score", sa.Integer(), nullable=False),
        sa.Column("committee_recommendation", sa.Text(), nullable=False),
        sa.Column("deadline_on", sa.Date(), nullable=True),
        sa.Column("submitted_on", sa.Date(), nullable=True),
        sa.Column("decided_on", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["athlete_profile_id"], ["athlete_profiles.id"], name=op.f("fk_athlete_scholarship_applications_athlete_profile_id_athlete_profiles")),
        sa.ForeignKeyConstraint(["created_by_person_id"], ["persons.id"], name=op.f("fk_athlete_scholarship_applications_created_by_person_id_persons")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_athlete_scholarship_applications_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_athlete_scholarship_applications")),
    )
    op.create_index(op.f("ix_athlete_scholarship_applications_athlete_profile_id"), "athlete_scholarship_applications", ["athlete_profile_id"])
    op.create_index(op.f("ix_athlete_scholarship_applications_created_by_person_id"), "athlete_scholarship_applications", ["created_by_person_id"])
    op.create_index(op.f("ix_athlete_scholarship_applications_deadline_on"), "athlete_scholarship_applications", ["deadline_on"])
    op.create_index(op.f("ix_athlete_scholarship_applications_decided_on"), "athlete_scholarship_applications", ["decided_on"])
    op.create_index(op.f("ix_athlete_scholarship_applications_donor_or_fund"), "athlete_scholarship_applications", ["donor_or_fund"])
    op.create_index(op.f("ix_athlete_scholarship_applications_eligibility_score"), "athlete_scholarship_applications", ["eligibility_score"])
    op.create_index(op.f("ix_athlete_scholarship_applications_organization_id"), "athlete_scholarship_applications", ["organization_id"])
    op.create_index(op.f("ix_athlete_scholarship_applications_program_name"), "athlete_scholarship_applications", ["program_name"])
    op.create_index(op.f("ix_athlete_scholarship_applications_scholarship_type"), "athlete_scholarship_applications", ["scholarship_type"])
    op.create_index(op.f("ix_athlete_scholarship_applications_status"), "athlete_scholarship_applications", ["status"])
    op.create_index(op.f("ix_athlete_scholarship_applications_submitted_on"), "athlete_scholarship_applications", ["submitted_on"])


def downgrade() -> None:
    op.drop_index(op.f("ix_athlete_scholarship_applications_submitted_on"), table_name="athlete_scholarship_applications")
    op.drop_index(op.f("ix_athlete_scholarship_applications_status"), table_name="athlete_scholarship_applications")
    op.drop_index(op.f("ix_athlete_scholarship_applications_scholarship_type"), table_name="athlete_scholarship_applications")
    op.drop_index(op.f("ix_athlete_scholarship_applications_program_name"), table_name="athlete_scholarship_applications")
    op.drop_index(op.f("ix_athlete_scholarship_applications_organization_id"), table_name="athlete_scholarship_applications")
    op.drop_index(op.f("ix_athlete_scholarship_applications_eligibility_score"), table_name="athlete_scholarship_applications")
    op.drop_index(op.f("ix_athlete_scholarship_applications_donor_or_fund"), table_name="athlete_scholarship_applications")
    op.drop_index(op.f("ix_athlete_scholarship_applications_decided_on"), table_name="athlete_scholarship_applications")
    op.drop_index(op.f("ix_athlete_scholarship_applications_deadline_on"), table_name="athlete_scholarship_applications")
    op.drop_index(op.f("ix_athlete_scholarship_applications_created_by_person_id"), table_name="athlete_scholarship_applications")
    op.drop_index(op.f("ix_athlete_scholarship_applications_athlete_profile_id"), table_name="athlete_scholarship_applications")
    op.drop_table("athlete_scholarship_applications")

    op.drop_index(op.f("ix_athlete_life_skill_assignments_status"), table_name="athlete_life_skill_assignments")
    op.drop_index(op.f("ix_athlete_life_skill_assignments_organization_id"), table_name="athlete_life_skill_assignments")
    op.drop_index(op.f("ix_athlete_life_skill_assignments_module_code"), table_name="athlete_life_skill_assignments")
    op.drop_index(op.f("ix_athlete_life_skill_assignments_level"), table_name="athlete_life_skill_assignments")
    op.drop_index(op.f("ix_athlete_life_skill_assignments_due_on"), table_name="athlete_life_skill_assignments")
    op.drop_index(op.f("ix_athlete_life_skill_assignments_completed_at"), table_name="athlete_life_skill_assignments")
    op.drop_index(op.f("ix_athlete_life_skill_assignments_category"), table_name="athlete_life_skill_assignments")
    op.drop_index(op.f("ix_athlete_life_skill_assignments_athlete_profile_id"), table_name="athlete_life_skill_assignments")
    op.drop_index(op.f("ix_athlete_life_skill_assignments_assigned_by_person_id"), table_name="athlete_life_skill_assignments")
    op.drop_table("athlete_life_skill_assignments")

    op.drop_index(op.f("ix_athlete_academic_records_term_label"), table_name="athlete_academic_records")
    op.drop_index(op.f("ix_athlete_academic_records_school_name"), table_name="athlete_academic_records")
    op.drop_index(op.f("ix_athlete_academic_records_risk_level"), table_name="athlete_academic_records")
    op.drop_index(op.f("ix_athlete_academic_records_recorded_by_person_id"), table_name="athlete_academic_records")
    op.drop_index(op.f("ix_athlete_academic_records_organization_id"), table_name="athlete_academic_records")
    op.drop_index(op.f("ix_athlete_academic_records_next_review_on"), table_name="athlete_academic_records")
    op.drop_index(op.f("ix_athlete_academic_records_grade_level"), table_name="athlete_academic_records")
    op.drop_index(op.f("ix_athlete_academic_records_eligibility_status"), table_name="athlete_academic_records")
    op.drop_index(op.f("ix_athlete_academic_records_athlete_profile_id"), table_name="athlete_academic_records")
    op.drop_table("athlete_academic_records")

    op.drop_index(op.f("ix_athlete_wellness_check_ins_support_requested"), table_name="athlete_wellness_check_ins")
    op.drop_index(op.f("ix_athlete_wellness_check_ins_submitted_by_person_id"), table_name="athlete_wellness_check_ins")
    op.drop_index(op.f("ix_athlete_wellness_check_ins_stress_score"), table_name="athlete_wellness_check_ins")
    op.drop_index(op.f("ix_athlete_wellness_check_ins_risk_band"), table_name="athlete_wellness_check_ins")
    op.drop_index(op.f("ix_athlete_wellness_check_ins_organization_id"), table_name="athlete_wellness_check_ins")
    op.drop_index(op.f("ix_athlete_wellness_check_ins_mood_score"), table_name="athlete_wellness_check_ins")
    op.drop_index(op.f("ix_athlete_wellness_check_ins_check_in_at"), table_name="athlete_wellness_check_ins")
    op.drop_index(op.f("ix_athlete_wellness_check_ins_athlete_profile_id"), table_name="athlete_wellness_check_ins")
    op.drop_table("athlete_wellness_check_ins")
