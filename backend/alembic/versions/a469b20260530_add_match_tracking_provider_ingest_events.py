"""add match tracking provider ingest events

Revision ID: a469b20260530
Revises: a468b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a469b20260530"
down_revision: str | Sequence[str] | None = "a468b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_match_tracking_provider_ingest_events",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("video_asset_id", GUID(), nullable=False),
        sa.Column("tracking_run_id", GUID(), nullable=True),
        sa.Column("team_id", GUID(), nullable=True),
        sa.Column("event_id", GUID(), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("external_event_id", sa.String(length=180), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signature_required", sa.Boolean(), nullable=False),
        sa.Column("signature_validated", sa.Boolean(), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("player_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["tracking_run_id"], ["performance_match_tracking_runs.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "video_asset_id",
            "provider",
            "external_event_id",
            name="uq_performance_match_tracking_provider_ingest_events_replay",
        ),
    )
    for column in (
        "event_id",
        "external_event_id",
        "organization_id",
        "payload_hash",
        "provider",
        "received_at",
        "status",
        "team_id",
        "tracking_run_id",
        "video_asset_id",
    ):
        op.create_index(
            op.f(f"ix_performance_match_tracking_provider_ingest_events_{column}"),
            "performance_match_tracking_provider_ingest_events",
            [column],
        )


def downgrade() -> None:
    op.drop_table("performance_match_tracking_provider_ingest_events")
