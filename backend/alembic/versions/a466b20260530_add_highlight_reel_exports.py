"""add highlight reel exports

Revision ID: a466b20260530
Revises: a465b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a466b20260530"
down_revision: str | None = "a465b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_highlight_reel_exports",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("highlight_reel_id", GUID(), nullable=False),
        sa.Column("video_asset_id", GUID(), nullable=False),
        sa.Column("tracking_run_id", GUID(), nullable=True),
        sa.Column("requested_by_person_id", GUID(), nullable=True),
        sa.Column("export_format", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("renderer_policy", sa.String(length=180), nullable=False),
        sa.Column("filename", sa.String(length=220), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("storage_url", sa.String(length=800), nullable=False),
        sa.Column("storage_path", sa.String(length=1000), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("manifest_json", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["highlight_reel_id"], ["performance_highlight_reels.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["requested_by_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["tracking_run_id"], ["performance_match_tracking_runs.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "checksum",
        "export_format",
        "generated_at",
        "highlight_reel_id",
        "organization_id",
        "requested_by_person_id",
        "status",
        "tracking_run_id",
        "video_asset_id",
    ]:
        op.create_index(
            op.f(f"ix_performance_highlight_reel_exports_{column}"),
            "performance_highlight_reel_exports",
            [column],
        )


def downgrade() -> None:
    op.drop_table("performance_highlight_reel_exports")
