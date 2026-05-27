"""add training readiness feedback

Revision ID: 7b4c0a9e21d3
Revises: 289c8a99ccde
Create Date: 2026-05-27 18:20:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "7b4c0a9e21d3"
down_revision: str | None = "289c8a99ccde"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "training_session_feedback",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("session_plan_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=True),
        sa.Column("recorded_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("readiness_score", sa.Integer(), nullable=False),
        sa.Column("soreness_score", sa.Integer(), nullable=False),
        sa.Column("sleep_quality", sa.Integer(), nullable=False),
        sa.Column("mood_score", sa.Integer(), nullable=False),
        sa.Column("actual_rpe", sa.Integer(), nullable=True),
        sa.Column("actual_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("coach_notes", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_training_session_feedback_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_training_session_feedback_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by_person_id"],
            ["persons.id"],
            name=op.f("fk_training_session_feedback_recorded_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["session_plan_id"],
            ["training_session_plans.id"],
            name=op.f("fk_training_session_feedback_session_plan_id_training_session_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_training_session_feedback")),
    )
    op.create_index(
        op.f("ix_training_session_feedback_athlete_profile_id"),
        "training_session_feedback",
        ["athlete_profile_id"],
        unique=False,
    )
    op.create_index(op.f("ix_training_session_feedback_completed"), "training_session_feedback", ["completed"], unique=False)
    op.create_index(
        op.f("ix_training_session_feedback_organization_id"),
        "training_session_feedback",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_training_session_feedback_readiness_score"),
        "training_session_feedback",
        ["readiness_score"],
        unique=False,
    )
    op.create_index(op.f("ix_training_session_feedback_recorded_at"), "training_session_feedback", ["recorded_at"], unique=False)
    op.create_index(
        op.f("ix_training_session_feedback_session_plan_id"),
        "training_session_feedback",
        ["session_plan_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_training_session_feedback_session_plan_id"), table_name="training_session_feedback")
    op.drop_index(op.f("ix_training_session_feedback_recorded_at"), table_name="training_session_feedback")
    op.drop_index(op.f("ix_training_session_feedback_readiness_score"), table_name="training_session_feedback")
    op.drop_index(op.f("ix_training_session_feedback_organization_id"), table_name="training_session_feedback")
    op.drop_index(op.f("ix_training_session_feedback_completed"), table_name="training_session_feedback")
    op.drop_index(op.f("ix_training_session_feedback_athlete_profile_id"), table_name="training_session_feedback")
    op.drop_table("training_session_feedback")
