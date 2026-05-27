from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import TrainingPlanStatus, TrainingSessionStatus


class TrainingDrill(IdMixin, TimestampMixin, Base):
    __tablename__ = "training_drills"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    sport: Mapped[str | None] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    focus_area: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    min_age: Mapped[int | None] = mapped_column(Integer)
    max_age: Mapped[int | None] = mapped_column(Integer)
    equipment: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    coaching_points: Mapped[str | None] = mapped_column(Text)
    default_duration_minutes: Mapped[int] = mapped_column(Integer, default=15)
    default_intensity: Mapped[int] = mapped_column(Integer, default=5)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)


class TrainingPlan(IdMixin, TimestampMixin, Base):
    __tablename__ = "training_plans"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    athlete_profile_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    title: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    focus_area: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(nullable=False, index=True)
    status: Mapped[TrainingPlanStatus] = mapped_column(
        enum_type(TrainingPlanStatus),
        default=TrainingPlanStatus.DRAFT,
        nullable=False,
        index=True,
    )
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    source_summary: Mapped[str | None] = mapped_column(Text)
    load_guidance: Mapped[str | None] = mapped_column(Text)
    recovery_protocol: Mapped[str | None] = mapped_column(Text)
    progress_checkpoints: Mapped[str | None] = mapped_column(Text)


class TrainingPlanItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "training_plan_items"

    plan_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("training_plans.id"), index=True)
    drill_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("training_drills.id"))
    sequence: Mapped[int] = mapped_column(Integer, default=1, index=True)
    day_label: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    focus_area: Mapped[str] = mapped_column(String(120), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    intensity: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class TrainingSessionPlan(IdMixin, TimestampMixin, Base):
    __tablename__ = "training_session_plans"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    team_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    plan_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("training_plans.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    rpe_target: Mapped[int] = mapped_column(Integer, nullable=False)
    load_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    objectives: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TrainingSessionStatus] = mapped_column(
        enum_type(TrainingSessionStatus),
        default=TrainingSessionStatus.PLANNED,
        nullable=False,
        index=True,
    )


class TrainingSessionFeedback(IdMixin, TimestampMixin, Base):
    __tablename__ = "training_session_feedback"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    session_plan_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("training_session_plans.id"), index=True
    )
    athlete_profile_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    recorded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    readiness_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    soreness_score: Mapped[int] = mapped_column(Integer, nullable=False)
    sleep_quality: Mapped[int] = mapped_column(Integer, nullable=False)
    mood_score: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_rpe: Mapped[int | None] = mapped_column(Integer)
    actual_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    feedback: Mapped[str | None] = mapped_column(Text)
    coach_notes: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
