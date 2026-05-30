"""add match pitch calibration

Revision ID: a463b20260530
Revises: a462b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a463b20260530"
down_revision: str | None = "a462b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_match_pitch_calibrations",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("video_asset_id", GUID(), nullable=False),
        sa.Column("created_by_person_id", GUID(), nullable=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("calibration_method", sa.String(length=80), nullable=False),
        sa.Column("pitch_length_m", sa.Float(), nullable=False),
        sa.Column("pitch_width_m", sa.Float(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("points_json", sa.Text(), nullable=False),
        sa.Column("transform_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_performance_match_pitch_calibrations_calibration_method"),
        "performance_match_pitch_calibrations",
        ["calibration_method"],
    )
    op.create_index(
        op.f("ix_performance_match_pitch_calibrations_created_by_person_id"),
        "performance_match_pitch_calibrations",
        ["created_by_person_id"],
    )
    op.create_index(
        op.f("ix_performance_match_pitch_calibrations_name"),
        "performance_match_pitch_calibrations",
        ["name"],
    )
    op.create_index(
        op.f("ix_performance_match_pitch_calibrations_organization_id"),
        "performance_match_pitch_calibrations",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_performance_match_pitch_calibrations_status"),
        "performance_match_pitch_calibrations",
        ["status"],
    )
    op.create_index(
        op.f("ix_performance_match_pitch_calibrations_video_asset_id"),
        "performance_match_pitch_calibrations",
        ["video_asset_id"],
    )
    op.add_column("performance_match_tracking_runs", sa.Column("calibration_id", GUID(), nullable=True))
    op.create_foreign_key(
        "fk_performance_match_tracking_runs_calibration_id",
        "performance_match_tracking_runs",
        "performance_match_pitch_calibrations",
        ["calibration_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_performance_match_tracking_runs_calibration_id"),
        "performance_match_tracking_runs",
        ["calibration_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_performance_match_tracking_runs_calibration_id"), table_name="performance_match_tracking_runs")
    op.drop_constraint(
        "fk_performance_match_tracking_runs_calibration_id",
        "performance_match_tracking_runs",
        type_="foreignkey",
    )
    op.drop_column("performance_match_tracking_runs", "calibration_id")
    op.drop_index(
        op.f("ix_performance_match_pitch_calibrations_video_asset_id"),
        table_name="performance_match_pitch_calibrations",
    )
    op.drop_index(op.f("ix_performance_match_pitch_calibrations_status"), table_name="performance_match_pitch_calibrations")
    op.drop_index(
        op.f("ix_performance_match_pitch_calibrations_organization_id"),
        table_name="performance_match_pitch_calibrations",
    )
    op.drop_index(op.f("ix_performance_match_pitch_calibrations_name"), table_name="performance_match_pitch_calibrations")
    op.drop_index(
        op.f("ix_performance_match_pitch_calibrations_created_by_person_id"),
        table_name="performance_match_pitch_calibrations",
    )
    op.drop_index(
        op.f("ix_performance_match_pitch_calibrations_calibration_method"),
        table_name="performance_match_pitch_calibrations",
    )
    op.drop_table("performance_match_pitch_calibrations")
