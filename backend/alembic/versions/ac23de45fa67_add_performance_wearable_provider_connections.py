"""add performance wearable provider connections

Revision ID: ac23de45fa67
Revises: ab12cd34ef56
Create Date: 2026-05-28 13:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "ac23de45fa67"
down_revision: str | None = "ab12cd34ef56"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_wearable_provider_connections",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=180), nullable=False),
        sa.Column("external_athlete_ref", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("auth_type", sa.String(length=40), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("access_token_secret_path", sa.String(length=500), nullable=True),
        sa.Column("refresh_token_secret_path", sa.String(length=500), nullable=True),
        sa.Column("webhook_secret_path", sa.String(length=500), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_cursor", sa.String(length=240), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("webhook_registered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("default_metric_definition_ids", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_performance_wearable_provider_connections_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_performance_wearable_provider_connections_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_wearable_provider_connections")),
        sa.UniqueConstraint(
            "organization_id",
            "athlete_profile_id",
            "provider",
            "external_athlete_ref",
            name="uq_performance_wearable_provider_connections_external_ref",
        ),
    )
    for column in [
        "athlete_profile_id",
        "external_athlete_ref",
        "last_sync_at",
        "organization_id",
        "provider",
        "status",
        "token_expires_at",
    ]:
        op.create_index(
            op.f(f"ix_performance_wearable_provider_connections_{column}"),
            "performance_wearable_provider_connections",
            [column],
            unique=False,
        )

    op.create_table(
        "performance_wearable_provider_sync_runs",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("connection_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("external_event_id", sa.String(length=180), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("sync_mode", sa.String(length=40), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observation_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("skipped_metric_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("replayed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_performance_wearable_provider_sync_runs_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["performance_wearable_provider_connections.id"],
            name=op.f("fk_performance_wearable_provider_sync_runs_connection_id_performance_wearable_provider_connections"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_performance_wearable_provider_sync_runs_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_wearable_provider_sync_runs")),
    )
    for column in [
        "athlete_profile_id",
        "connection_id",
        "external_event_id",
        "organization_id",
        "provider",
        "started_at",
        "status",
        "sync_mode",
    ]:
        op.create_index(
            op.f(f"ix_performance_wearable_provider_sync_runs_{column}"),
            "performance_wearable_provider_sync_runs",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "sync_mode",
        "status",
        "started_at",
        "provider",
        "organization_id",
        "external_event_id",
        "connection_id",
        "athlete_profile_id",
    ]:
        op.drop_index(
            op.f(f"ix_performance_wearable_provider_sync_runs_{column}"),
            table_name="performance_wearable_provider_sync_runs",
        )
    op.drop_table("performance_wearable_provider_sync_runs")
    for column in [
        "token_expires_at",
        "status",
        "provider",
        "organization_id",
        "last_sync_at",
        "external_athlete_ref",
        "athlete_profile_id",
    ]:
        op.drop_index(
            op.f(f"ix_performance_wearable_provider_connections_{column}"),
            table_name="performance_wearable_provider_connections",
        )
    op.drop_table("performance_wearable_provider_connections")
