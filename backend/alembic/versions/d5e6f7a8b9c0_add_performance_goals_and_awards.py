"""add performance goals and awards

Revision ID: d5e6f7a8b9c0
Revises: c2d3e4f5a6b8
Create Date: 2026-05-28 12:40:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d5e6f7a8b9c0"
down_revision: str | None = "c2d3e4f5a6b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_goals",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("metric_definition_id", app.models.base.GUID(), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=False),
        sa.Column("baseline_value", sa.Float(), nullable=True),
        sa.Column("current_value", sa.Float(), nullable=True),
        sa.Column("direction", sa.String(length=40), nullable=False),
        sa.Column("starts_at", sa.Date(), nullable=False),
        sa.Column("due_at", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("reward_badge", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["athlete_profile_id"], ["athlete_profiles.id"], name=op.f("fk_performance_goals_athlete_profile_id_athlete_profiles")),
        sa.ForeignKeyConstraint(["metric_definition_id"], ["performance_metric_definitions.id"], name=op.f("fk_performance_goals_metric_definition_id_performance_metric_definitions")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_performance_goals_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_goals")),
    )
    op.create_index(op.f("ix_performance_goals_athlete_profile_id"), "performance_goals", ["athlete_profile_id"])
    op.create_index(op.f("ix_performance_goals_due_at"), "performance_goals", ["due_at"])
    op.create_index(op.f("ix_performance_goals_metric_definition_id"), "performance_goals", ["metric_definition_id"])
    op.create_index(op.f("ix_performance_goals_organization_id"), "performance_goals", ["organization_id"])
    op.create_index(op.f("ix_performance_goals_starts_at"), "performance_goals", ["starts_at"])
    op.create_index(op.f("ix_performance_goals_status"), "performance_goals", ["status"])
    op.create_index(op.f("ix_performance_goals_title"), "performance_goals", ["title"])

    op.create_table(
        "performance_achievement_awards",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("goal_id", app.models.base.GUID(), nullable=True),
        sa.Column("metric_definition_id", app.models.base.GUID(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("badge_code", sa.String(length=160), nullable=False),
        sa.Column("achievement_type", sa.String(length=80), nullable=False),
        sa.Column("achieved_value", sa.Float(), nullable=True),
        sa.Column("threshold_value", sa.Float(), nullable=True),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_summary", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["athlete_profile_id"], ["athlete_profiles.id"], name=op.f("fk_performance_achievement_awards_athlete_profile_id_athlete_profiles")),
        sa.ForeignKeyConstraint(["goal_id"], ["performance_goals.id"], name=op.f("fk_performance_achievement_awards_goal_id_performance_goals")),
        sa.ForeignKeyConstraint(["metric_definition_id"], ["performance_metric_definitions.id"], name=op.f("fk_performance_achievement_awards_metric_definition_id_performance_metric_definitions")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_performance_achievement_awards_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_achievement_awards")),
        sa.UniqueConstraint("organization_id", "athlete_profile_id", "badge_code", name="uq_performance_achievement_awards_badge"),
    )
    op.create_index(op.f("ix_performance_achievement_awards_achievement_type"), "performance_achievement_awards", ["achievement_type"])
    op.create_index(op.f("ix_performance_achievement_awards_athlete_profile_id"), "performance_achievement_awards", ["athlete_profile_id"])
    op.create_index(op.f("ix_performance_achievement_awards_awarded_at"), "performance_achievement_awards", ["awarded_at"])
    op.create_index(op.f("ix_performance_achievement_awards_badge_code"), "performance_achievement_awards", ["badge_code"])
    op.create_index(op.f("ix_performance_achievement_awards_goal_id"), "performance_achievement_awards", ["goal_id"])
    op.create_index(op.f("ix_performance_achievement_awards_metric_definition_id"), "performance_achievement_awards", ["metric_definition_id"])
    op.create_index(op.f("ix_performance_achievement_awards_organization_id"), "performance_achievement_awards", ["organization_id"])
    op.create_index(op.f("ix_performance_achievement_awards_title"), "performance_achievement_awards", ["title"])


def downgrade() -> None:
    op.drop_index(op.f("ix_performance_achievement_awards_title"), table_name="performance_achievement_awards")
    op.drop_index(op.f("ix_performance_achievement_awards_organization_id"), table_name="performance_achievement_awards")
    op.drop_index(op.f("ix_performance_achievement_awards_metric_definition_id"), table_name="performance_achievement_awards")
    op.drop_index(op.f("ix_performance_achievement_awards_goal_id"), table_name="performance_achievement_awards")
    op.drop_index(op.f("ix_performance_achievement_awards_badge_code"), table_name="performance_achievement_awards")
    op.drop_index(op.f("ix_performance_achievement_awards_awarded_at"), table_name="performance_achievement_awards")
    op.drop_index(op.f("ix_performance_achievement_awards_athlete_profile_id"), table_name="performance_achievement_awards")
    op.drop_index(op.f("ix_performance_achievement_awards_achievement_type"), table_name="performance_achievement_awards")
    op.drop_table("performance_achievement_awards")
    op.drop_index(op.f("ix_performance_goals_title"), table_name="performance_goals")
    op.drop_index(op.f("ix_performance_goals_status"), table_name="performance_goals")
    op.drop_index(op.f("ix_performance_goals_starts_at"), table_name="performance_goals")
    op.drop_index(op.f("ix_performance_goals_organization_id"), table_name="performance_goals")
    op.drop_index(op.f("ix_performance_goals_metric_definition_id"), table_name="performance_goals")
    op.drop_index(op.f("ix_performance_goals_due_at"), table_name="performance_goals")
    op.drop_index(op.f("ix_performance_goals_athlete_profile_id"), table_name="performance_goals")
    op.drop_table("performance_goals")
