"""add performance highlight reels

Revision ID: a465b20260530
Revises: a464b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a465b20260530"
down_revision: str | None = "a464b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_highlight_reels",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("video_asset_id", GUID(), nullable=False),
        sa.Column("tracking_run_id", GUID(), nullable=True),
        sa.Column("athlete_profile_id", GUID(), nullable=True),
        sa.Column("created_by_person_id", GUID(), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("audience", sa.String(length=80), nullable=False),
        sa.Column("purpose", sa.String(length=120), nullable=False),
        sa.Column("model_policy", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("clip_count", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("clips_json", sa.Text(), nullable=False),
        sa.Column("tags_json", sa.Text(), nullable=False),
        sa.Column("distribution_json", sa.Text(), nullable=False),
        sa.Column("branding_json", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["athlete_profile_id"], ["athlete_profiles.id"]),
        sa.ForeignKeyConstraint(["created_by_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["tracking_run_id"], ["performance_match_tracking_runs.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "athlete_profile_id",
        "audience",
        "created_by_person_id",
        "generated_at",
        "organization_id",
        "purpose",
        "status",
        "title",
        "tracking_run_id",
        "video_asset_id",
    ]:
        op.create_index(op.f(f"ix_performance_highlight_reels_{column}"), "performance_highlight_reels", [column])


def downgrade() -> None:
    op.drop_table("performance_highlight_reels")
