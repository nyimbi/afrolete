"""add performance pose samples

Revision ID: e9f2a1c4b6d8
Revises: d4e8f6a2b913
Create Date: 2026-05-29 08:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "e9f2a1c4b6d8"
down_revision: str | None = "d4e8f6a2b913"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_video_pose_samples",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("video_asset_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_id", app.models.base.GUID(), nullable=True),
        sa.Column("created_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("source_provider", sa.String(length=80), nullable=False, server_default="manual_pose"),
        sa.Column("frame_index", sa.Integer(), nullable=True),
        sa.Column("timestamp_seconds", sa.Float(), nullable=False),
        sa.Column("phase", sa.String(length=80), nullable=True),
        sa.Column("contact_foot", sa.String(length=20), nullable=True),
        sa.Column("stride_index", sa.Integer(), nullable=True),
        sa.Column("sample_confidence", sa.Float(), nullable=True),
        sa.Column("keypoints_json", sa.Text(), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_performance_video_pose_samples_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_person_id"],
            ["persons.id"],
            name=op.f("fk_performance_video_pose_samples_created_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_performance_video_pose_samples_event_id_events"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_performance_video_pose_samples_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["video_asset_id"],
            ["performance_video_assets.id"],
            name=op.f("fk_performance_video_pose_samples_video_asset_id_performance_video_assets"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_video_pose_samples")),
    )
    for column in [
        "athlete_profile_id",
        "contact_foot",
        "created_by_person_id",
        "event_id",
        "frame_index",
        "organization_id",
        "phase",
        "source_provider",
        "stride_index",
        "timestamp_seconds",
        "video_asset_id",
    ]:
        op.create_index(
            op.f(f"ix_performance_video_pose_samples_{column}"),
            "performance_video_pose_samples",
            [column],
        )


def downgrade() -> None:
    for column in [
        "video_asset_id",
        "timestamp_seconds",
        "stride_index",
        "source_provider",
        "phase",
        "organization_id",
        "frame_index",
        "event_id",
        "created_by_person_id",
        "contact_foot",
        "athlete_profile_id",
    ]:
        op.drop_index(
            op.f(f"ix_performance_video_pose_samples_{column}"),
            table_name="performance_video_pose_samples",
        )
    op.drop_table("performance_video_pose_samples")
