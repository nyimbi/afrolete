"""add performance hardware kits

Revision ID: a464b20260530
Revises: a463b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a464b20260530"
down_revision: str | None = "a463b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_hardware_kits",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("kit_type", sa.String(length=80), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("sport", sa.String(length=80), nullable=False),
        sa.Column("level", sa.String(length=80), nullable=False),
        sa.Column("recommended_camera_count", sa.Integer(), nullable=False),
        sa.Column("recommended_gps_unit_count", sa.Integer(), nullable=False),
        sa.Column("supported_metrics_json", sa.Text(), nullable=False),
        sa.Column("setup_steps_json", sa.Text(), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["kit_type", "level", "name", "organization_id", "provider", "sport", "status"]:
        op.create_index(op.f(f"ix_performance_hardware_kits_{column}"), "performance_hardware_kits", [column])

    op.create_table(
        "performance_hardware_devices",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("kit_id", GUID(), nullable=True),
        sa.Column("team_id", GUID(), nullable=True),
        sa.Column("facility_id", GUID(), nullable=True),
        sa.Column("device_type", sa.String(length=80), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("device_label", sa.String(length=180), nullable=False),
        sa.Column("external_device_id", sa.String(length=180), nullable=False),
        sa.Column("firmware_version", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("api_key_secret_path", sa.String(length=500), nullable=True),
        sa.Column("api_key_hash", sa.String(length=64), nullable=True),
        sa.Column("custody_mode", sa.String(length=40), nullable=False),
        sa.Column("metrics_supported_json", sa.Text(), nullable=False),
        sa.Column("calibration_id", GUID(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("battery_percent", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["calibration_id"], ["performance_match_pitch_calibrations.id"]),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"]),
        sa.ForeignKeyConstraint(["kit_id"], ["performance_hardware_kits.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "provider",
            "external_device_id",
            name="uq_performance_hardware_devices_external_device",
        ),
    )
    for column in [
        "calibration_id",
        "custody_mode",
        "device_type",
        "external_device_id",
        "facility_id",
        "kit_id",
        "last_seen_at",
        "organization_id",
        "provider",
        "status",
        "team_id",
    ]:
        op.create_index(op.f(f"ix_performance_hardware_devices_{column}"), "performance_hardware_devices", [column])

    op.create_table(
        "performance_hardware_sync_runs",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("device_id", GUID(), nullable=False),
        sa.Column("video_asset_id", GUID(), nullable=True),
        sa.Column("tracking_run_id", GUID(), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("sync_mode", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metrics_ingested", sa.Integer(), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["performance_hardware_devices.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["tracking_run_id"], ["performance_match_tracking_runs.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "device_id",
        "organization_id",
        "payload_hash",
        "provider",
        "started_at",
        "status",
        "sync_mode",
        "tracking_run_id",
        "video_asset_id",
    ]:
        op.create_index(op.f(f"ix_performance_hardware_sync_runs_{column}"), "performance_hardware_sync_runs", [column])


def downgrade() -> None:
    op.drop_table("performance_hardware_sync_runs")
    op.drop_table("performance_hardware_devices")
    op.drop_table("performance_hardware_kits")
