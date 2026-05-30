"""add player guidance publish audits

Revision ID: a471b20260530
Revises: a470b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID, enum_type
from app.models.enums import CommunicationChannel


revision: str = "a471b20260530"
down_revision: str | Sequence[str] | None = "a470b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_match_player_guidance_publish_audits",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("tracking_run_id", GUID(), nullable=False),
        sa.Column("video_asset_id", GUID(), nullable=False),
        sa.Column("message_id", GUID(), nullable=False),
        sa.Column("player_person_id", GUID(), nullable=False),
        sa.Column("track_id", sa.String(length=120), nullable=False),
        sa.Column("player_label", sa.String(length=180), nullable=False),
        sa.Column("channel", enum_type(CommunicationChannel), nullable=False),
        sa.Column("recipient_count", sa.Integer(), nullable=False),
        sa.Column("published_by_person_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["communication_messages.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["player_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["published_by_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["tracking_run_id"], ["performance_match_tracking_runs.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tracking_run_id",
            "message_id",
            name="uq_performance_match_player_guidance_publish_audits_message",
        ),
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_publish_audits_channel"),
        "performance_match_player_guidance_publish_audits",
        ["channel"],
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_publish_audits_message_id"),
        "performance_match_player_guidance_publish_audits",
        ["message_id"],
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_publish_audits_organization_id"),
        "performance_match_player_guidance_publish_audits",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_publish_audits_player_label"),
        "performance_match_player_guidance_publish_audits",
        ["player_label"],
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_publish_audits_player_person_id"),
        "performance_match_player_guidance_publish_audits",
        ["player_person_id"],
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_publish_audits_published_at"),
        "performance_match_player_guidance_publish_audits",
        ["published_at"],
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_publish_audits_published_by_person_id"),
        "performance_match_player_guidance_publish_audits",
        ["published_by_person_id"],
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_publish_audits_status"),
        "performance_match_player_guidance_publish_audits",
        ["status"],
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_publish_audits_track_id"),
        "performance_match_player_guidance_publish_audits",
        ["track_id"],
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_publish_audits_tracking_run_id"),
        "performance_match_player_guidance_publish_audits",
        ["tracking_run_id"],
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_publish_audits_video_asset_id"),
        "performance_match_player_guidance_publish_audits",
        ["video_asset_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_performance_match_player_guidance_publish_audits_video_asset_id"),
        table_name="performance_match_player_guidance_publish_audits",
    )
    op.drop_index(
        op.f("ix_performance_match_player_guidance_publish_audits_tracking_run_id"),
        table_name="performance_match_player_guidance_publish_audits",
    )
    op.drop_index(
        op.f("ix_performance_match_player_guidance_publish_audits_track_id"),
        table_name="performance_match_player_guidance_publish_audits",
    )
    op.drop_index(
        op.f("ix_performance_match_player_guidance_publish_audits_status"),
        table_name="performance_match_player_guidance_publish_audits",
    )
    op.drop_index(
        op.f("ix_performance_match_player_guidance_publish_audits_published_by_person_id"),
        table_name="performance_match_player_guidance_publish_audits",
    )
    op.drop_index(
        op.f("ix_performance_match_player_guidance_publish_audits_published_at"),
        table_name="performance_match_player_guidance_publish_audits",
    )
    op.drop_index(
        op.f("ix_performance_match_player_guidance_publish_audits_player_person_id"),
        table_name="performance_match_player_guidance_publish_audits",
    )
    op.drop_index(
        op.f("ix_performance_match_player_guidance_publish_audits_player_label"),
        table_name="performance_match_player_guidance_publish_audits",
    )
    op.drop_index(
        op.f("ix_performance_match_player_guidance_publish_audits_organization_id"),
        table_name="performance_match_player_guidance_publish_audits",
    )
    op.drop_index(
        op.f("ix_performance_match_player_guidance_publish_audits_message_id"),
        table_name="performance_match_player_guidance_publish_audits",
    )
    op.drop_index(
        op.f("ix_performance_match_player_guidance_publish_audits_channel"),
        table_name="performance_match_player_guidance_publish_audits",
    )
    op.drop_table("performance_match_player_guidance_publish_audits")
