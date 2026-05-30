"""add tracking identity reviews

Revision ID: a467b20260530
Revises: a466b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a467b20260530"
down_revision: str | None = "a466b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_match_tracking_identity_reviews",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("tracking_run_id", GUID(), nullable=False),
        sa.Column("video_asset_id", GUID(), nullable=False),
        sa.Column("track_id", sa.String(length=120), nullable=False),
        sa.Column("reviewer_person_id", GUID(), nullable=True),
        sa.Column("person_id", GUID(), nullable=True),
        sa.Column("team_label", sa.String(length=120), nullable=True),
        sa.Column("player_label", sa.String(length=180), nullable=True),
        sa.Column("jersey_number", sa.String(length=20), nullable=True),
        sa.Column("decision", sa.String(length=40), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("before_json", sa.Text(), nullable=False),
        sa.Column("after_json", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["reviewer_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["tracking_run_id"], ["performance_match_tracking_runs.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "decision",
        "jersey_number",
        "organization_id",
        "person_id",
        "player_label",
        "reviewed_at",
        "reviewer_person_id",
        "team_label",
        "track_id",
        "tracking_run_id",
        "video_asset_id",
    ]:
        op.create_index(
            op.f(f"ix_performance_match_tracking_identity_reviews_{column}"),
            "performance_match_tracking_identity_reviews",
            [column],
        )


def downgrade() -> None:
    op.drop_table("performance_match_tracking_identity_reviews")
