"""add multicamera match analysis

Revision ID: a477b20260530
Revises: a476b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a477b20260530"
down_revision: str | Sequence[str] | None = "a476b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_multi_camera_analyses",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("team_id", GUID(), nullable=True),
        sa.Column("event_id", GUID(), nullable=True),
        sa.Column("competition_id", GUID(), nullable=True),
        sa.Column("primary_video_asset_id", GUID(), nullable=False),
        sa.Column("created_by_person_id", GUID(), nullable=True),
        sa.Column("analysis_label", sa.String(length=180), nullable=False),
        sa.Column("sport", sa.String(length=80), nullable=False),
        sa.Column("synchronization_policy", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("camera_count", sa.Integer(), nullable=False),
        sa.Column("tracking_run_count", sa.Integer(), nullable=False),
        sa.Column("fused_player_count", sa.Integer(), nullable=False),
        sa.Column("fused_sample_count", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("camera_package_json", sa.Text(), server_default="[]", nullable=False),
        sa.Column("fused_summary_json", sa.Text(), server_default="{}", nullable=False),
        sa.Column("recommendations_json", sa.Text(), server_default="[]", nullable=False),
        sa.Column("model_policy", sa.String(length=180), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"], name=op.f("fk_performance_multi_camera_analyses_competition_id_competitions")),
        sa.ForeignKeyConstraint(["created_by_person_id"], ["persons.id"], name=op.f("fk_performance_multi_camera_analyses_created_by_person_id_persons")),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name=op.f("fk_performance_multi_camera_analyses_event_id_events")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_performance_multi_camera_analyses_organization_id_organizations")),
        sa.ForeignKeyConstraint(["primary_video_asset_id"], ["opposition_scouting_video_assets.id"], name=op.f("fk_performance_multi_camera_analyses_primary_video_asset_id_opposition_scouting_video_assets")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_performance_multi_camera_analyses_team_id_teams")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_multi_camera_analyses")),
    )
    for column in [
        "organization_id",
        "team_id",
        "event_id",
        "competition_id",
        "primary_video_asset_id",
        "created_by_person_id",
        "sport",
        "status",
        "analyzed_at",
    ]:
        op.create_index(
            op.f(f"ix_performance_multi_camera_analyses_{column}"),
            "performance_multi_camera_analyses",
            [column],
        )


def downgrade() -> None:
    for column in [
        "analyzed_at",
        "status",
        "sport",
        "created_by_person_id",
        "primary_video_asset_id",
        "competition_id",
        "event_id",
        "team_id",
        "organization_id",
    ]:
        op.drop_index(op.f(f"ix_performance_multi_camera_analyses_{column}"), table_name="performance_multi_camera_analyses")
    op.drop_table("performance_multi_camera_analyses")
