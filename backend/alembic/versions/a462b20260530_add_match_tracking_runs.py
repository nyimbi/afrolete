"""add match tracking runs

Revision ID: a462b20260530
Revises: a461b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a462b20260530"
down_revision: str | None = "a461b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_match_tracking_runs",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("video_asset_id", GUID(), nullable=False),
        sa.Column("team_id", GUID(), nullable=True),
        sa.Column("event_id", GUID(), nullable=True),
        sa.Column("created_by_person_id", GUID(), nullable=True),
        sa.Column("source_provider", sa.String(length=80), nullable=False),
        sa.Column("model_policy", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("pitch_length_m", sa.Float(), nullable=False),
        sa.Column("pitch_width_m", sa.Float(), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("player_count", sa.Integer(), nullable=False),
        sa.Column("total_distance_m", sa.Float(), nullable=False),
        sa.Column("max_speed_mps", sa.Float(), nullable=False),
        sa.Column("high_speed_distance_m", sa.Float(), nullable=False),
        sa.Column("sprint_count", sa.Integer(), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_performance_match_tracking_runs_completed_at"),
        "performance_match_tracking_runs",
        ["completed_at"],
    )
    op.create_index(
        op.f("ix_performance_match_tracking_runs_created_by_person_id"),
        "performance_match_tracking_runs",
        ["created_by_person_id"],
    )
    op.create_index(op.f("ix_performance_match_tracking_runs_event_id"), "performance_match_tracking_runs", ["event_id"])
    op.create_index(
        op.f("ix_performance_match_tracking_runs_organization_id"),
        "performance_match_tracking_runs",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_performance_match_tracking_runs_source_provider"),
        "performance_match_tracking_runs",
        ["source_provider"],
    )
    op.create_index(op.f("ix_performance_match_tracking_runs_started_at"), "performance_match_tracking_runs", ["started_at"])
    op.create_index(op.f("ix_performance_match_tracking_runs_status"), "performance_match_tracking_runs", ["status"])
    op.create_index(op.f("ix_performance_match_tracking_runs_team_id"), "performance_match_tracking_runs", ["team_id"])
    op.create_index(
        op.f("ix_performance_match_tracking_runs_video_asset_id"),
        "performance_match_tracking_runs",
        ["video_asset_id"],
    )

    op.create_table(
        "performance_match_tracking_samples",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("tracking_run_id", GUID(), nullable=False),
        sa.Column("video_asset_id", GUID(), nullable=False),
        sa.Column("track_id", sa.String(length=120), nullable=False),
        sa.Column("person_id", GUID(), nullable=True),
        sa.Column("team_label", sa.String(length=120), nullable=True),
        sa.Column("player_label", sa.String(length=180), nullable=True),
        sa.Column("jersey_number", sa.String(length=20), nullable=True),
        sa.Column("frame_index", sa.Integer(), nullable=True),
        sa.Column("timestamp_seconds", sa.Float(), nullable=False),
        sa.Column("x_percent", sa.Float(), nullable=False),
        sa.Column("y_percent", sa.Float(), nullable=False),
        sa.Column("x_meters", sa.Float(), nullable=False),
        sa.Column("y_meters", sa.Float(), nullable=False),
        sa.Column("speed_mps", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["tracking_run_id"], ["performance_match_tracking_runs.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_performance_match_tracking_samples_frame_index"),
        "performance_match_tracking_samples",
        ["frame_index"],
    )
    op.create_index(
        op.f("ix_performance_match_tracking_samples_jersey_number"),
        "performance_match_tracking_samples",
        ["jersey_number"],
    )
    op.create_index(
        op.f("ix_performance_match_tracking_samples_organization_id"),
        "performance_match_tracking_samples",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_performance_match_tracking_samples_person_id"),
        "performance_match_tracking_samples",
        ["person_id"],
    )
    op.create_index(
        op.f("ix_performance_match_tracking_samples_player_label"),
        "performance_match_tracking_samples",
        ["player_label"],
    )
    op.create_index(op.f("ix_performance_match_tracking_samples_source"), "performance_match_tracking_samples", ["source"])
    op.create_index(
        op.f("ix_performance_match_tracking_samples_team_label"),
        "performance_match_tracking_samples",
        ["team_label"],
    )
    op.create_index(
        op.f("ix_performance_match_tracking_samples_timestamp_seconds"),
        "performance_match_tracking_samples",
        ["timestamp_seconds"],
    )
    op.create_index(
        op.f("ix_performance_match_tracking_samples_track_id"),
        "performance_match_tracking_samples",
        ["track_id"],
    )
    op.create_index(
        op.f("ix_performance_match_tracking_samples_tracking_run_id"),
        "performance_match_tracking_samples",
        ["tracking_run_id"],
    )
    op.create_index(
        op.f("ix_performance_match_tracking_samples_video_asset_id"),
        "performance_match_tracking_samples",
        ["video_asset_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_performance_match_tracking_samples_video_asset_id"), table_name="performance_match_tracking_samples")
    op.drop_index(op.f("ix_performance_match_tracking_samples_tracking_run_id"), table_name="performance_match_tracking_samples")
    op.drop_index(op.f("ix_performance_match_tracking_samples_track_id"), table_name="performance_match_tracking_samples")
    op.drop_index(op.f("ix_performance_match_tracking_samples_timestamp_seconds"), table_name="performance_match_tracking_samples")
    op.drop_index(op.f("ix_performance_match_tracking_samples_team_label"), table_name="performance_match_tracking_samples")
    op.drop_index(op.f("ix_performance_match_tracking_samples_source"), table_name="performance_match_tracking_samples")
    op.drop_index(op.f("ix_performance_match_tracking_samples_player_label"), table_name="performance_match_tracking_samples")
    op.drop_index(op.f("ix_performance_match_tracking_samples_person_id"), table_name="performance_match_tracking_samples")
    op.drop_index(op.f("ix_performance_match_tracking_samples_organization_id"), table_name="performance_match_tracking_samples")
    op.drop_index(op.f("ix_performance_match_tracking_samples_jersey_number"), table_name="performance_match_tracking_samples")
    op.drop_index(op.f("ix_performance_match_tracking_samples_frame_index"), table_name="performance_match_tracking_samples")
    op.drop_table("performance_match_tracking_samples")
    op.drop_index(op.f("ix_performance_match_tracking_runs_video_asset_id"), table_name="performance_match_tracking_runs")
    op.drop_index(op.f("ix_performance_match_tracking_runs_team_id"), table_name="performance_match_tracking_runs")
    op.drop_index(op.f("ix_performance_match_tracking_runs_status"), table_name="performance_match_tracking_runs")
    op.drop_index(op.f("ix_performance_match_tracking_runs_started_at"), table_name="performance_match_tracking_runs")
    op.drop_index(op.f("ix_performance_match_tracking_runs_source_provider"), table_name="performance_match_tracking_runs")
    op.drop_index(op.f("ix_performance_match_tracking_runs_organization_id"), table_name="performance_match_tracking_runs")
    op.drop_index(op.f("ix_performance_match_tracking_runs_event_id"), table_name="performance_match_tracking_runs")
    op.drop_index(op.f("ix_performance_match_tracking_runs_created_by_person_id"), table_name="performance_match_tracking_runs")
    op.drop_index(op.f("ix_performance_match_tracking_runs_completed_at"), table_name="performance_match_tracking_runs")
    op.drop_table("performance_match_tracking_runs")
