"""add performance wearable ingest events

Revision ID: ab12cd34ef56
Revises: b3c4d5e6f7a8
Create Date: 2026-05-28 12:30:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "ab12cd34ef56"
down_revision: str | None = "b3c4d5e6f7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_wearable_ingest_events",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_id", app.models.base.GUID(), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("external_event_id", sa.String(length=180), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signature_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("signature_validated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("observation_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("skipped_metric_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_performance_wearable_ingest_events_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_performance_wearable_ingest_events_event_id_events"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_performance_wearable_ingest_events_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_wearable_ingest_events")),
        sa.UniqueConstraint(
            "organization_id",
            "athlete_profile_id",
            "provider",
            "external_event_id",
            name="uq_performance_wearable_ingest_events_replay",
        ),
    )
    for column in [
        "athlete_profile_id",
        "event_id",
        "external_event_id",
        "organization_id",
        "payload_hash",
        "provider",
        "received_at",
    ]:
        op.create_index(
            op.f(f"ix_performance_wearable_ingest_events_{column}"),
            "performance_wearable_ingest_events",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "received_at",
        "provider",
        "payload_hash",
        "organization_id",
        "external_event_id",
        "event_id",
        "athlete_profile_id",
    ]:
        op.drop_index(
            op.f(f"ix_performance_wearable_ingest_events_{column}"),
            table_name="performance_wearable_ingest_events",
        )
    op.drop_table("performance_wearable_ingest_events")
