from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin


class VoiceCoachProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "voice_coach_profiles"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    athlete_profile_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    sport: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    voice_style: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    feedback_frequency: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    terminology_level: Mapped[str] = mapped_column(String(40), default="intermediate", nullable=False)
    preferred_device: Mapped[str | None] = mapped_column(String(120))
    safety_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class VoiceCoachingSession(IdMixin, TimestampMixin, Base):
    __tablename__ = "voice_coaching_sessions"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    profile_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("voice_coach_profiles.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    athlete_profile_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    activity_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    intensity: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    elapsed_seconds: Mapped[int | None] = mapped_column(Integer)
    distance_m: Mapped[float | None] = mapped_column(Float)
    heart_rate_bpm: Mapped[int | None] = mapped_column(Integer)
    speed_mps: Mapped[float | None] = mapped_column(Float)
    context_note: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    debrief: Mapped[str] = mapped_column(Text, nullable=False)
    next_actions_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    safety_flags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    suppressed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    model_policy: Mapped[str] = mapped_column(
        String(120),
        default="afrolete-context-aware-voice-coach-v1",
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class VoiceCoachingCue(IdMixin, TimestampMixin, Base):
    __tablename__ = "voice_coaching_cues"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    session_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("voice_coaching_sessions.id"), index=True)
    profile_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("voice_coach_profiles.id"), index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    audio_layer: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    trigger: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_mode: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    suppressed_reason: Mapped[str | None] = mapped_column(Text)
