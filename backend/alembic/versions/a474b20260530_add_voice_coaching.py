"""add voice coaching

Revision ID: a474b20260530
Revises: a473b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a474b20260530"
down_revision: str | Sequence[str] | None = "a473b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "voice_coach_profiles",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("person_id", GUID(), nullable=True),
        sa.Column("athlete_profile_id", GUID(), nullable=True),
        sa.Column("sport", sa.String(length=80), nullable=False),
        sa.Column("voice_style", sa.String(length=80), nullable=False),
        sa.Column("feedback_frequency", sa.String(length=40), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("terminology_level", sa.String(length=40), nullable=False),
        sa.Column("preferred_device", sa.String(length=120), nullable=True),
        sa.Column("safety_alerts_enabled", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["athlete_profile_id"], ["athlete_profiles.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "athlete_profile_id",
        "feedback_frequency",
        "organization_id",
        "person_id",
        "sport",
        "status",
        "voice_style",
    ]:
        op.create_index(op.f(f"ix_voice_coach_profiles_{column}"), "voice_coach_profiles", [column])

    op.create_table(
        "voice_coaching_sessions",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("profile_id", GUID(), nullable=False),
        sa.Column("team_id", GUID(), nullable=True),
        sa.Column("athlete_profile_id", GUID(), nullable=True),
        sa.Column("created_by_person_id", GUID(), nullable=True),
        sa.Column("activity_type", sa.String(length=120), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=False),
        sa.Column("intensity", sa.Integer(), nullable=False),
        sa.Column("elapsed_seconds", sa.Integer(), nullable=True),
        sa.Column("distance_m", sa.Float(), nullable=True),
        sa.Column("heart_rate_bpm", sa.Integer(), nullable=True),
        sa.Column("speed_mps", sa.Float(), nullable=True),
        sa.Column("context_note", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("debrief", sa.Text(), nullable=False),
        sa.Column("next_actions_json", sa.Text(), nullable=False),
        sa.Column("safety_flags_json", sa.Text(), nullable=False),
        sa.Column("delivered_count", sa.Integer(), nullable=False),
        sa.Column("suppressed_count", sa.Integer(), nullable=False),
        sa.Column("model_policy", sa.String(length=120), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["athlete_profile_id"], ["athlete_profiles.id"]),
        sa.ForeignKeyConstraint(["created_by_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["voice_coach_profiles.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "activity_type",
        "athlete_profile_id",
        "created_by_person_id",
        "intensity",
        "organization_id",
        "profile_id",
        "stage",
        "started_at",
        "team_id",
    ]:
        op.create_index(op.f(f"ix_voice_coaching_sessions_{column}"), "voice_coaching_sessions", [column])

    op.create_table(
        "voice_coaching_cues",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("session_id", GUID(), nullable=False),
        sa.Column("profile_id", GUID(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("priority", sa.String(length=40), nullable=False),
        sa.Column("audio_layer", sa.String(length=80), nullable=False),
        sa.Column("trigger", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("delivery_mode", sa.String(length=40), nullable=False),
        sa.Column("suppressed_reason", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["voice_coach_profiles.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["voice_coaching_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "audio_layer",
        "category",
        "delivery_mode",
        "organization_id",
        "priority",
        "profile_id",
        "session_id",
    ]:
        op.create_index(op.f(f"ix_voice_coaching_cues_{column}"), "voice_coaching_cues", [column])


def downgrade() -> None:
    for column in [
        "session_id",
        "profile_id",
        "priority",
        "organization_id",
        "delivery_mode",
        "category",
        "audio_layer",
    ]:
        op.drop_index(op.f(f"ix_voice_coaching_cues_{column}"), table_name="voice_coaching_cues")
    op.drop_table("voice_coaching_cues")
    for column in [
        "team_id",
        "started_at",
        "stage",
        "profile_id",
        "organization_id",
        "intensity",
        "created_by_person_id",
        "athlete_profile_id",
        "activity_type",
    ]:
        op.drop_index(op.f(f"ix_voice_coaching_sessions_{column}"), table_name="voice_coaching_sessions")
    op.drop_table("voice_coaching_sessions")
    for column in [
        "voice_style",
        "status",
        "sport",
        "person_id",
        "organization_id",
        "feedback_frequency",
        "athlete_profile_id",
    ]:
        op.drop_index(op.f(f"ix_voice_coach_profiles_{column}"), table_name="voice_coach_profiles")
    op.drop_table("voice_coach_profiles")
