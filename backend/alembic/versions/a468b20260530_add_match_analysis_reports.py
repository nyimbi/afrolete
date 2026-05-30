"""add match analysis reports

Revision ID: a468b20260530
Revises: a467b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a468b20260530"
down_revision: str | Sequence[str] | None = "a467b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_match_analysis_reports",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("tracking_run_id", GUID(), nullable=False),
        sa.Column("video_asset_id", GUID(), nullable=False),
        sa.Column("created_by_person_id", GUID(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("audience", sa.String(length=80), nullable=False),
        sa.Column("report_scope", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("model_policy", sa.String(length=180), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("player_cards_json", sa.Text(), nullable=False),
        sa.Column("team_shape_json", sa.Text(), nullable=False),
        sa.Column("recommendations_json", sa.Text(), nullable=False),
        sa.Column("artifact_format", sa.String(length=40), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("storage_url", sa.String(length=800), nullable=False),
        sa.Column("storage_path", sa.String(length=1000), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["tracking_run_id"], ["performance_match_tracking_runs.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "artifact_format",
        "audience",
        "checksum",
        "created_by_person_id",
        "generated_at",
        "organization_id",
        "report_scope",
        "status",
        "title",
        "tracking_run_id",
        "video_asset_id",
    ):
        op.create_index(
            op.f(f"ix_performance_match_analysis_reports_{column}"),
            "performance_match_analysis_reports",
            [column],
        )


def downgrade() -> None:
    op.drop_table("performance_match_analysis_reports")
