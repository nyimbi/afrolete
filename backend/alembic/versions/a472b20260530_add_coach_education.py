"""add coach education

Revision ID: a472b20260530
Revises: a471b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a472b20260530"
down_revision: str | Sequence[str] | None = "a471b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "coach_education_enrollments",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("person_id", GUID(), nullable=False),
        sa.Column("program_key", sa.String(length=120), nullable=False),
        sa.Column("program_title", sa.String(length=220), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=False),
        sa.Column("skill_level", sa.String(length=80), nullable=False),
        sa.Column("learning_style", sa.String(length=80), nullable=False),
        sa.Column("xp_points", sa.Integer(), nullable=False),
        sa.Column("current_module_key", sa.String(length=120), nullable=True),
        sa.Column("completed_modules_json", sa.Text(), nullable=False),
        sa.Column("badges_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("certification_expires_on", sa.Date(), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "person_id",
            "program_key",
            name="uq_coach_education_enrollments_org_person_program",
        ),
    )
    for column in [
        "certification_expires_on",
        "current_module_key",
        "last_activity_at",
        "level",
        "organization_id",
        "person_id",
        "program_key",
        "role",
        "status",
        "xp_points",
    ]:
        op.create_index(op.f(f"ix_coach_education_enrollments_{column}"), "coach_education_enrollments", [column])

    op.create_table(
        "coach_education_activities",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("enrollment_id", GUID(), nullable=False),
        sa.Column("person_id", GUID(), nullable=False),
        sa.Column("activity_type", sa.String(length=80), nullable=False),
        sa.Column("module_key", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("xp_awarded", sa.Integer(), nullable=False),
        sa.Column("evidence_ref", sa.String(length=500), nullable=True),
        sa.Column("score_percent", sa.Float(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["enrollment_id"], ["coach_education_enrollments.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "activity_type",
        "completed_at",
        "enrollment_id",
        "module_key",
        "organization_id",
        "person_id",
    ]:
        op.create_index(op.f(f"ix_coach_education_activities_{column}"), "coach_education_activities", [column])


def downgrade() -> None:
    for column in [
        "person_id",
        "organization_id",
        "module_key",
        "enrollment_id",
        "completed_at",
        "activity_type",
    ]:
        op.drop_index(op.f(f"ix_coach_education_activities_{column}"), table_name="coach_education_activities")
    op.drop_table("coach_education_activities")
    for column in [
        "xp_points",
        "status",
        "role",
        "program_key",
        "person_id",
        "organization_id",
        "level",
        "last_activity_at",
        "current_module_key",
        "certification_expires_on",
    ]:
        op.drop_index(op.f(f"ix_coach_education_enrollments_{column}"), table_name="coach_education_enrollments")
    op.drop_table("coach_education_enrollments")
