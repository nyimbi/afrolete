"""add athlete nutrition hub

Revision ID: a449b20260530
Revises: a448b20260530
Create Date: 2026-05-30 12:30:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a449b20260530"
down_revision: str | None = "a448b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "athlete_nutrition_profiles",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("recorded_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("dietary_pattern", sa.String(length=120), nullable=False),
        sa.Column("allergies", sa.Text(), nullable=True),
        sa.Column("medical_notes", sa.Text(), nullable=True),
        sa.Column("hydration_target_liters", sa.Float(), nullable=False),
        sa.Column("daily_calorie_target", sa.Integer(), nullable=False),
        sa.Column("protein_target_grams", sa.Integer(), nullable=False),
        sa.Column("carbohydrate_target_grams", sa.Integer(), nullable=False),
        sa.Column("fat_target_grams", sa.Integer(), nullable=False),
        sa.Column("supplement_policy", sa.Text(), nullable=True),
        sa.Column("travel_food_risk", sa.String(length=40), nullable=False),
        sa.Column("consent_to_share_with_caterers", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_athlete_nutrition_profiles_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_athlete_nutrition_profiles_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by_person_id"],
            ["persons.id"],
            name=op.f("fk_athlete_nutrition_profiles_recorded_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_athlete_nutrition_profiles")),
        sa.UniqueConstraint("organization_id", "athlete_profile_id", name="uq_athlete_nutrition_profiles_athlete"),
    )
    op.create_index(op.f("ix_athlete_nutrition_profiles_athlete_profile_id"), "athlete_nutrition_profiles", ["athlete_profile_id"])
    op.create_index(op.f("ix_athlete_nutrition_profiles_dietary_pattern"), "athlete_nutrition_profiles", ["dietary_pattern"])
    op.create_index(op.f("ix_athlete_nutrition_profiles_organization_id"), "athlete_nutrition_profiles", ["organization_id"])
    op.create_index(op.f("ix_athlete_nutrition_profiles_recorded_by_person_id"), "athlete_nutrition_profiles", ["recorded_by_person_id"])
    op.create_index(op.f("ix_athlete_nutrition_profiles_status"), "athlete_nutrition_profiles", ["status"])
    op.create_index(op.f("ix_athlete_nutrition_profiles_travel_food_risk"), "athlete_nutrition_profiles", ["travel_food_risk"])

    op.create_table(
        "athlete_meal_plans",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("created_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("plan_type", sa.String(length=80), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("daily_calorie_target", sa.Integer(), nullable=False),
        sa.Column("hydration_target_liters", sa.Float(), nullable=False),
        sa.Column("menu_summary", sa.Text(), nullable=False),
        sa.Column("shopping_list", sa.Text(), nullable=True),
        sa.Column("caterer_notes", sa.Text(), nullable=True),
        sa.Column("risk_flags", sa.Text(), nullable=True),
        sa.Column("ai_generated", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_athlete_meal_plans_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_person_id"],
            ["persons.id"],
            name=op.f("fk_athlete_meal_plans_created_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_athlete_meal_plans_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_athlete_meal_plans")),
    )
    op.create_index(op.f("ix_athlete_meal_plans_ai_generated"), "athlete_meal_plans", ["ai_generated"])
    op.create_index(op.f("ix_athlete_meal_plans_athlete_profile_id"), "athlete_meal_plans", ["athlete_profile_id"])
    op.create_index(op.f("ix_athlete_meal_plans_created_by_person_id"), "athlete_meal_plans", ["created_by_person_id"])
    op.create_index(op.f("ix_athlete_meal_plans_organization_id"), "athlete_meal_plans", ["organization_id"])
    op.create_index(op.f("ix_athlete_meal_plans_period_end"), "athlete_meal_plans", ["period_end"])
    op.create_index(op.f("ix_athlete_meal_plans_period_start"), "athlete_meal_plans", ["period_start"])
    op.create_index(op.f("ix_athlete_meal_plans_plan_type"), "athlete_meal_plans", ["plan_type"])
    op.create_index(op.f("ix_athlete_meal_plans_status"), "athlete_meal_plans", ["status"])
    op.create_index(op.f("ix_athlete_meal_plans_title"), "athlete_meal_plans", ["title"])

    op.create_table(
        "athlete_meal_logs",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("meal_plan_id", app.models.base.GUID(), nullable=True),
        sa.Column("logged_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("meal_type", sa.String(length=80), nullable=False),
        sa.Column("calories", sa.Integer(), nullable=False),
        sa.Column("protein_grams", sa.Float(), nullable=False),
        sa.Column("carbohydrate_grams", sa.Float(), nullable=False),
        sa.Column("fat_grams", sa.Float(), nullable=False),
        sa.Column("hydration_liters", sa.Float(), nullable=False),
        sa.Column("perceived_energy_score", sa.Integer(), nullable=False),
        sa.Column("gut_comfort_score", sa.Integer(), nullable=False),
        sa.Column("compliance_status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_athlete_meal_logs_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(["logged_by_person_id"], ["persons.id"], name=op.f("fk_athlete_meal_logs_logged_by_person_id_persons")),
        sa.ForeignKeyConstraint(["meal_plan_id"], ["athlete_meal_plans.id"], name=op.f("fk_athlete_meal_logs_meal_plan_id_athlete_meal_plans")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_athlete_meal_logs_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_athlete_meal_logs")),
    )
    op.create_index(op.f("ix_athlete_meal_logs_athlete_profile_id"), "athlete_meal_logs", ["athlete_profile_id"])
    op.create_index(op.f("ix_athlete_meal_logs_compliance_status"), "athlete_meal_logs", ["compliance_status"])
    op.create_index(op.f("ix_athlete_meal_logs_logged_at"), "athlete_meal_logs", ["logged_at"])
    op.create_index(op.f("ix_athlete_meal_logs_logged_by_person_id"), "athlete_meal_logs", ["logged_by_person_id"])
    op.create_index(op.f("ix_athlete_meal_logs_meal_plan_id"), "athlete_meal_logs", ["meal_plan_id"])
    op.create_index(op.f("ix_athlete_meal_logs_meal_type"), "athlete_meal_logs", ["meal_type"])
    op.create_index(op.f("ix_athlete_meal_logs_organization_id"), "athlete_meal_logs", ["organization_id"])

    op.create_table(
        "nutrition_education_assignments",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("assigned_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("module_code", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["assigned_by_person_id"],
            ["persons.id"],
            name=op.f("fk_nutrition_education_assignments_assigned_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_nutrition_education_assignments_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_nutrition_education_assignments_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_nutrition_education_assignments")),
        sa.UniqueConstraint("organization_id", "athlete_profile_id", "module_code", name="uq_nutrition_education_assignments_module"),
    )
    op.create_index(op.f("ix_nutrition_education_assignments_assigned_by_person_id"), "nutrition_education_assignments", ["assigned_by_person_id"])
    op.create_index(op.f("ix_nutrition_education_assignments_athlete_profile_id"), "nutrition_education_assignments", ["athlete_profile_id"])
    op.create_index(op.f("ix_nutrition_education_assignments_category"), "nutrition_education_assignments", ["category"])
    op.create_index(op.f("ix_nutrition_education_assignments_completed_at"), "nutrition_education_assignments", ["completed_at"])
    op.create_index(op.f("ix_nutrition_education_assignments_due_on"), "nutrition_education_assignments", ["due_on"])
    op.create_index(op.f("ix_nutrition_education_assignments_module_code"), "nutrition_education_assignments", ["module_code"])
    op.create_index(op.f("ix_nutrition_education_assignments_organization_id"), "nutrition_education_assignments", ["organization_id"])
    op.create_index(op.f("ix_nutrition_education_assignments_status"), "nutrition_education_assignments", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_nutrition_education_assignments_status"), table_name="nutrition_education_assignments")
    op.drop_index(op.f("ix_nutrition_education_assignments_organization_id"), table_name="nutrition_education_assignments")
    op.drop_index(op.f("ix_nutrition_education_assignments_module_code"), table_name="nutrition_education_assignments")
    op.drop_index(op.f("ix_nutrition_education_assignments_due_on"), table_name="nutrition_education_assignments")
    op.drop_index(op.f("ix_nutrition_education_assignments_completed_at"), table_name="nutrition_education_assignments")
    op.drop_index(op.f("ix_nutrition_education_assignments_category"), table_name="nutrition_education_assignments")
    op.drop_index(op.f("ix_nutrition_education_assignments_athlete_profile_id"), table_name="nutrition_education_assignments")
    op.drop_index(op.f("ix_nutrition_education_assignments_assigned_by_person_id"), table_name="nutrition_education_assignments")
    op.drop_table("nutrition_education_assignments")

    op.drop_index(op.f("ix_athlete_meal_logs_organization_id"), table_name="athlete_meal_logs")
    op.drop_index(op.f("ix_athlete_meal_logs_meal_type"), table_name="athlete_meal_logs")
    op.drop_index(op.f("ix_athlete_meal_logs_meal_plan_id"), table_name="athlete_meal_logs")
    op.drop_index(op.f("ix_athlete_meal_logs_logged_by_person_id"), table_name="athlete_meal_logs")
    op.drop_index(op.f("ix_athlete_meal_logs_logged_at"), table_name="athlete_meal_logs")
    op.drop_index(op.f("ix_athlete_meal_logs_compliance_status"), table_name="athlete_meal_logs")
    op.drop_index(op.f("ix_athlete_meal_logs_athlete_profile_id"), table_name="athlete_meal_logs")
    op.drop_table("athlete_meal_logs")

    op.drop_index(op.f("ix_athlete_meal_plans_title"), table_name="athlete_meal_plans")
    op.drop_index(op.f("ix_athlete_meal_plans_status"), table_name="athlete_meal_plans")
    op.drop_index(op.f("ix_athlete_meal_plans_plan_type"), table_name="athlete_meal_plans")
    op.drop_index(op.f("ix_athlete_meal_plans_period_start"), table_name="athlete_meal_plans")
    op.drop_index(op.f("ix_athlete_meal_plans_period_end"), table_name="athlete_meal_plans")
    op.drop_index(op.f("ix_athlete_meal_plans_organization_id"), table_name="athlete_meal_plans")
    op.drop_index(op.f("ix_athlete_meal_plans_created_by_person_id"), table_name="athlete_meal_plans")
    op.drop_index(op.f("ix_athlete_meal_plans_athlete_profile_id"), table_name="athlete_meal_plans")
    op.drop_index(op.f("ix_athlete_meal_plans_ai_generated"), table_name="athlete_meal_plans")
    op.drop_table("athlete_meal_plans")

    op.drop_index(op.f("ix_athlete_nutrition_profiles_travel_food_risk"), table_name="athlete_nutrition_profiles")
    op.drop_index(op.f("ix_athlete_nutrition_profiles_status"), table_name="athlete_nutrition_profiles")
    op.drop_index(op.f("ix_athlete_nutrition_profiles_recorded_by_person_id"), table_name="athlete_nutrition_profiles")
    op.drop_index(op.f("ix_athlete_nutrition_profiles_organization_id"), table_name="athlete_nutrition_profiles")
    op.drop_index(op.f("ix_athlete_nutrition_profiles_dietary_pattern"), table_name="athlete_nutrition_profiles")
    op.drop_index(op.f("ix_athlete_nutrition_profiles_athlete_profile_id"), table_name="athlete_nutrition_profiles")
    op.drop_table("athlete_nutrition_profiles")
