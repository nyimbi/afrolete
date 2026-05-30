from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin


class CoachVoiceCommandSession(IdMixin, TimestampMixin, Base):
    __tablename__ = "coach_voice_command_sessions"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    session_label: Mapped[str] = mapped_column(String(180), nullable=False)
    context_type: Mapped[str] = mapped_column(String(40), default="match", nullable=False, index=True)
    input_device: Mapped[str] = mapped_column(String(120), default="coach_headset", nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    listening_mode: Mapped[str] = mapped_column(String(40), default="push_to_talk", nullable=False, index=True)
    consent_recorded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_audio_retention_policy: Mapped[str] = mapped_column(
        String(120),
        default="delete_raw_audio_after_transcription",
        nullable=False,
    )
    command_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    model_policy: Mapped[str] = mapped_column(
        String(140),
        default="afrolete-coach-voice-command-v1",
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    last_command_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class CoachVoiceCommand(IdMixin, TimestampMixin, Base):
    __tablename__ = "coach_voice_commands"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    session_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("coach_voice_command_sessions.id"),
        index=True,
    )
    issued_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    reviewed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    command_status: Mapped[str] = mapped_column(String(60), default="captured", nullable=False, index=True)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    entities_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    action_result_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    safety_flags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    review_result_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    permission_scope: Mapped[str] = mapped_column(String(80), default="training_operations", nullable=False)
    requires_confirmation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    review_decision: Mapped[str | None] = mapped_column(String(40), index=True)
    review_notes: Mapped[str | None] = mapped_column(Text)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    source_device: Mapped[str | None] = mapped_column(String(120))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    model_policy: Mapped[str] = mapped_column(
        String(140),
        default="afrolete-coach-voice-command-v1",
        nullable=False,
    )
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class CoachVoiceCommandShortcut(IdMixin, TimestampMixin, Base):
    __tablename__ = "coach_voice_command_shortcuts"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    phrase: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    intent: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    action_sequence_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    parameters_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    notification_policy: Mapped[str] = mapped_column(String(80), default="coach_confirmation", nullable=False)
    auto_log: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trained_sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sensitivity: Mapped[float] = mapped_column(Float, default=0.72, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
