"""add match moment detection

Revision ID: a478b20260530
Revises: a477b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a478b20260530"
down_revision: str | Sequence[str] | None = "a477b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_match_moments",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("tracking_run_id", GUID(), nullable=False),
        sa.Column("video_asset_id", GUID(), nullable=False),
        sa.Column("created_by_person_id", GUID(), nullable=True),
        sa.Column("action_type", sa.String(length=80), nullable=False),
        sa.Column("moment_category", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("start_seconds", sa.Float(), nullable=False),
        sa.Column("end_seconds", sa.Float(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("moment_score", sa.Float(), nullable=False),
        sa.Column("technical_quality", sa.Float(), nullable=False),
        sa.Column("tactical_importance", sa.Float(), nullable=False),
        sa.Column("emotional_impact", sa.Float(), nullable=False),
        sa.Column("rarity_difficulty", sa.Float(), nullable=False),
        sa.Column("game_context", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("primary_track_id", sa.String(length=120), nullable=True),
        sa.Column("secondary_track_id", sa.String(length=120), nullable=True),
        sa.Column("team_label", sa.String(length=120), nullable=True),
        sa.Column("player_label", sa.String(length=180), nullable=True),
        sa.Column("jersey_number", sa.String(length=20), nullable=True),
        sa.Column("zone", sa.String(length=80), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("coaching_note", sa.Text(), nullable=False),
        sa.Column("tags_json", sa.Text(), server_default="[]", nullable=False),
        sa.Column("source_event_json", sa.Text(), server_default="{}", nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("model_policy", sa.String(length=180), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["tracking_run_id"], ["performance_match_tracking_runs.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_match_moments")),
    )
    for column in [
        "organization_id",
        "tracking_run_id",
        "video_asset_id",
        "created_by_person_id",
        "action_type",
        "moment_category",
        "title",
        "moment_score",
        "primary_track_id",
        "secondary_track_id",
        "team_label",
        "player_label",
        "jersey_number",
        "zone",
        "status",
        "detected_at",
    ]:
        op.create_index(op.f(f"ix_performance_match_moments_{column}"), "performance_match_moments", [column])


def downgrade() -> None:
    for column in [
        "detected_at",
        "status",
        "zone",
        "jersey_number",
        "player_label",
        "team_label",
        "secondary_track_id",
        "primary_track_id",
        "moment_score",
        "title",
        "moment_category",
        "action_type",
        "created_by_person_id",
        "video_asset_id",
        "tracking_run_id",
        "organization_id",
    ]:
        op.drop_index(op.f(f"ix_performance_match_moments_{column}"), table_name="performance_match_moments")
    op.drop_table("performance_match_moments")
