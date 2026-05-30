"""add coach voice commands

Revision ID: a475b20260530
Revises: a474b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a475b20260530"
down_revision: str | Sequence[str] | None = "a474b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "coach_voice_command_sessions",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("person_id", GUID(), nullable=True),
        sa.Column("team_id", GUID(), nullable=True),
        sa.Column("event_id", GUID(), nullable=True),
        sa.Column("session_label", sa.String(length=180), nullable=False),
        sa.Column("context_type", sa.String(length=40), nullable=False),
        sa.Column("input_device", sa.String(length=120), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("listening_mode", sa.String(length=40), nullable=False),
        sa.Column("consent_recorded", sa.Boolean(), nullable=False),
        sa.Column("raw_audio_retention_policy", sa.String(length=120), nullable=False),
        sa.Column("command_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("model_policy", sa.String(length=140), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_command_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "context_type",
        "event_id",
        "last_command_at",
        "listening_mode",
        "organization_id",
        "person_id",
        "started_at",
        "status",
        "team_id",
    ]:
        op.create_index(
            op.f(f"ix_coach_voice_command_sessions_{column}"),
            "coach_voice_command_sessions",
            [column],
        )

    op.create_table(
        "coach_voice_commands",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("session_id", GUID(), nullable=False),
        sa.Column("issued_by_person_id", GUID(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("normalized_transcript", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=80), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("command_status", sa.String(length=60), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("entities_json", sa.Text(), nullable=False),
        sa.Column("action_result_json", sa.Text(), nullable=False),
        sa.Column("safety_flags_json", sa.Text(), nullable=False),
        sa.Column("permission_scope", sa.String(length=80), nullable=False),
        sa.Column("requires_confirmation", sa.Boolean(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_device", sa.String(length=120), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("model_policy", sa.String(length=140), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["issued_by_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["coach_voice_command_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "command_status",
        "confirmed_at",
        "intent",
        "issued_by_person_id",
        "organization_id",
        "processed_at",
        "session_id",
    ]:
        op.create_index(op.f(f"ix_coach_voice_commands_{column}"), "coach_voice_commands", [column])

    op.create_table(
        "coach_voice_command_shortcuts",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("created_by_person_id", GUID(), nullable=True),
        sa.Column("phrase", sa.String(length=240), nullable=False),
        sa.Column("intent", sa.String(length=80), nullable=False),
        sa.Column("action_sequence_json", sa.Text(), nullable=False),
        sa.Column("parameters_json", sa.Text(), nullable=False),
        sa.Column("notification_policy", sa.String(length=80), nullable=False),
        sa.Column("auto_log", sa.Boolean(), nullable=False),
        sa.Column("trained_sample_count", sa.Integer(), nullable=False),
        sa.Column("sensitivity", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "created_by_person_id",
        "intent",
        "organization_id",
        "phrase",
        "status",
    ]:
        op.create_index(
            op.f(f"ix_coach_voice_command_shortcuts_{column}"),
            "coach_voice_command_shortcuts",
            [column],
        )


def downgrade() -> None:
    for column in ["status", "phrase", "organization_id", "intent", "created_by_person_id"]:
        op.drop_index(
            op.f(f"ix_coach_voice_command_shortcuts_{column}"),
            table_name="coach_voice_command_shortcuts",
        )
    op.drop_table("coach_voice_command_shortcuts")
    for column in [
        "session_id",
        "processed_at",
        "organization_id",
        "issued_by_person_id",
        "intent",
        "confirmed_at",
        "command_status",
    ]:
        op.drop_index(op.f(f"ix_coach_voice_commands_{column}"), table_name="coach_voice_commands")
    op.drop_table("coach_voice_commands")
    for column in [
        "team_id",
        "status",
        "started_at",
        "person_id",
        "organization_id",
        "listening_mode",
        "last_command_at",
        "event_id",
        "context_type",
    ]:
        op.drop_index(
            op.f(f"ix_coach_voice_command_sessions_{column}"),
            table_name="coach_voice_command_sessions",
        )
    op.drop_table("coach_voice_command_sessions")
