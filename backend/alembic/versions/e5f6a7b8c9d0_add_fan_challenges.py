"""add fan challenges

Revision ID: e5f6a7b8c9d0
Revises: e4f5a6b7c8da
Create Date: 2026-05-30 04:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "e4f5a6b7c8da"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fan_engagement_challenges",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("challenge_type", sa.String(length=80), nullable=False),
        sa.Column("target_activity_type", sa.String(length=80), nullable=False),
        sa.Column("target_count", sa.Integer(), nullable=False),
        sa.Column("points_reward", sa.Integer(), nullable=False),
        sa.Column("badge_name", sa.String(length=160), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_fan_engagement_challenges_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fan_engagement_challenges")),
    )
    op.create_index(op.f("ix_fan_engagement_challenges_badge_name"), "fan_engagement_challenges", ["badge_name"])
    op.create_index(op.f("ix_fan_engagement_challenges_challenge_type"), "fan_engagement_challenges", ["challenge_type"])
    op.create_index(op.f("ix_fan_engagement_challenges_ends_at"), "fan_engagement_challenges", ["ends_at"])
    op.create_index(op.f("ix_fan_engagement_challenges_organization_id"), "fan_engagement_challenges", ["organization_id"])
    op.create_index(op.f("ix_fan_engagement_challenges_starts_at"), "fan_engagement_challenges", ["starts_at"])
    op.create_index(op.f("ix_fan_engagement_challenges_status"), "fan_engagement_challenges", ["status"])
    op.create_index(op.f("ix_fan_engagement_challenges_target_activity_type"), "fan_engagement_challenges", ["target_activity_type"])
    op.create_index(op.f("ix_fan_engagement_challenges_title"), "fan_engagement_challenges", ["title"])

    op.create_table(
        "fan_challenge_progress",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("challenge_id", app.models.base.GUID(), nullable=False),
        sa.Column("supporter_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("progress_count", sa.Integer(), nullable=False),
        sa.Column("points_awarded", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["fan_engagement_challenges.id"], name=op.f("fk_fan_challenge_progress_challenge_id_fan_engagement_challenges")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_fan_challenge_progress_organization_id_organizations")),
        sa.ForeignKeyConstraint(["supporter_profile_id"], ["supporter_profiles.id"], name=op.f("fk_fan_challenge_progress_supporter_profile_id_supporter_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fan_challenge_progress")),
        sa.UniqueConstraint("challenge_id", "supporter_profile_id", name=op.f("uq_fan_challenge_progress_challenge_id")),
    )
    op.create_index(op.f("ix_fan_challenge_progress_challenge_id"), "fan_challenge_progress", ["challenge_id"])
    op.create_index(op.f("ix_fan_challenge_progress_completed_at"), "fan_challenge_progress", ["completed_at"])
    op.create_index(op.f("ix_fan_challenge_progress_organization_id"), "fan_challenge_progress", ["organization_id"])
    op.create_index(op.f("ix_fan_challenge_progress_status"), "fan_challenge_progress", ["status"])
    op.create_index(op.f("ix_fan_challenge_progress_supporter_profile_id"), "fan_challenge_progress", ["supporter_profile_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_fan_challenge_progress_supporter_profile_id"), table_name="fan_challenge_progress")
    op.drop_index(op.f("ix_fan_challenge_progress_status"), table_name="fan_challenge_progress")
    op.drop_index(op.f("ix_fan_challenge_progress_organization_id"), table_name="fan_challenge_progress")
    op.drop_index(op.f("ix_fan_challenge_progress_completed_at"), table_name="fan_challenge_progress")
    op.drop_index(op.f("ix_fan_challenge_progress_challenge_id"), table_name="fan_challenge_progress")
    op.drop_table("fan_challenge_progress")

    op.drop_index(op.f("ix_fan_engagement_challenges_title"), table_name="fan_engagement_challenges")
    op.drop_index(op.f("ix_fan_engagement_challenges_target_activity_type"), table_name="fan_engagement_challenges")
    op.drop_index(op.f("ix_fan_engagement_challenges_status"), table_name="fan_engagement_challenges")
    op.drop_index(op.f("ix_fan_engagement_challenges_starts_at"), table_name="fan_engagement_challenges")
    op.drop_index(op.f("ix_fan_engagement_challenges_organization_id"), table_name="fan_engagement_challenges")
    op.drop_index(op.f("ix_fan_engagement_challenges_ends_at"), table_name="fan_engagement_challenges")
    op.drop_index(op.f("ix_fan_engagement_challenges_challenge_type"), table_name="fan_engagement_challenges")
    op.drop_index(op.f("ix_fan_engagement_challenges_badge_name"), table_name="fan_engagement_challenges")
    op.drop_table("fan_engagement_challenges")
