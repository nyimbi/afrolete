"""add performance video assets

Revision ID: d4e8f6a2b913
Revises: c2d4f6a8b901
Create Date: 2026-05-29 04:20:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d4e8f6a2b913"
down_revision: str | None = "c2d4f6a8b901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_video_assets",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_id", app.models.base.GUID(), nullable=True),
        sa.Column("uploaded_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("sport", sa.String(length=80), nullable=False, server_default="athletics"),
        sa.Column("filename", sa.String(length=240), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("storage_url", sa.String(length=800), nullable=False),
        sa.Column("storage_path", sa.String(length=1000), nullable=False),
        sa.Column("video_uri", sa.String(length=900), nullable=False),
        sa.Column("clip_label", sa.String(length=180), nullable=True),
        sa.Column("analysis_focus", sa.String(length=1000), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("frame_rate", sa.Float(), nullable=True),
        sa.Column("frame_width", sa.Integer(), nullable=True),
        sa.Column("frame_height", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="uploaded"),
        sa.Column("analysis_model_policy", sa.String(length=180), nullable=True),
        sa.Column("pose_analysis_json", sa.Text(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_performance_video_assets_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_performance_video_assets_event_id_events"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_performance_video_assets_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_person_id"],
            ["persons.id"],
            name=op.f("fk_performance_video_assets_uploaded_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_video_assets")),
        sa.UniqueConstraint(
            "organization_id",
            "checksum",
            name="uq_performance_video_assets_org_checksum",
        ),
    )
    for column in [
        "analysis_model_policy",
        "analyzed_at",
        "athlete_profile_id",
        "checksum",
        "event_id",
        "organization_id",
        "sport",
        "status",
        "uploaded_by_person_id",
        "video_uri",
    ]:
        op.create_index(
            op.f(f"ix_performance_video_assets_{column}"),
            "performance_video_assets",
            [column],
        )

    op.create_table(
        "performance_video_annotations",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("video_asset_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_id", app.models.base.GUID(), nullable=True),
        sa.Column("author_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("timestamp_seconds", sa.Float(), nullable=False),
        sa.Column("playback_rate", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("annotation_type", sa.String(length=80), nullable=False, server_default="coach_note"),
        sa.Column("label", sa.String(length=180), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("body_region", sa.String(length=80), nullable=True),
        sa.Column("x_percent", sa.Float(), nullable=True),
        sa.Column("y_percent", sa.Float(), nullable=True),
        sa.Column("width_percent", sa.Float(), nullable=True),
        sa.Column("height_percent", sa.Float(), nullable=True),
        sa.Column("tags_json", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_performance_video_annotations_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["author_person_id"],
            ["persons.id"],
            name=op.f("fk_performance_video_annotations_author_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_performance_video_annotations_event_id_events"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_performance_video_annotations_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["video_asset_id"],
            ["performance_video_assets.id"],
            name=op.f("fk_performance_video_annotations_video_asset_id_performance_video_assets"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_video_annotations")),
    )
    for column in [
        "annotation_type",
        "athlete_profile_id",
        "author_person_id",
        "body_region",
        "event_id",
        "organization_id",
        "timestamp_seconds",
        "video_asset_id",
    ]:
        op.create_index(
            op.f(f"ix_performance_video_annotations_{column}"),
            "performance_video_annotations",
            [column],
        )


def downgrade() -> None:
    for column in [
        "video_asset_id",
        "timestamp_seconds",
        "organization_id",
        "event_id",
        "body_region",
        "author_person_id",
        "athlete_profile_id",
        "annotation_type",
    ]:
        op.drop_index(
            op.f(f"ix_performance_video_annotations_{column}"),
            table_name="performance_video_annotations",
        )
    op.drop_table("performance_video_annotations")

    for column in [
        "video_uri",
        "uploaded_by_person_id",
        "status",
        "sport",
        "organization_id",
        "event_id",
        "checksum",
        "athlete_profile_id",
        "analyzed_at",
        "analysis_model_policy",
    ]:
        op.drop_index(
            op.f(f"ix_performance_video_assets_{column}"),
            table_name="performance_video_assets",
        )
    op.drop_table("performance_video_assets")
