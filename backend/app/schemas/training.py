from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import TrainingPlanStatus, TrainingSessionStatus


class TrainingDrillCreate(BaseModel):
    organization_id: UUID
    sport: str | None = Field(default=None, max_length=80)
    name: str = Field(min_length=2, max_length=180)
    focus_area: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=80)
    min_age: int | None = Field(default=None, ge=3, le=100)
    max_age: int | None = Field(default=None, ge=3, le=100)
    equipment: str | None = Field(default=None, max_length=2000)
    description: str = Field(min_length=8, max_length=4000)
    coaching_points: str | None = Field(default=None, max_length=4000)
    default_duration_minutes: int = Field(default=15, ge=1, le=240)
    default_intensity: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def valid_age_range(self) -> "TrainingDrillCreate":
        if self.min_age is not None and self.max_age is not None and self.max_age < self.min_age:
            raise ValueError("max_age must be greater than or equal to min_age")
        return self


class TrainingDrillRead(BaseModel):
    id: UUID
    organization_id: UUID
    sport: str | None
    name: str
    focus_area: str
    category: str
    min_age: int | None
    max_age: int | None
    equipment: str | None
    description: str
    coaching_points: str | None
    default_duration_minutes: int
    default_intensity: int
    status: str


class TrainingPlanCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    athlete_profile_id: UUID | None = None
    title: str = Field(min_length=2, max_length=240)
    focus_area: str = Field(min_length=2, max_length=160)
    period_start: date
    period_end: date
    ai_generated: bool = False
    source_summary: str | None = Field(default=None, max_length=4000)
    load_guidance: str | None = Field(default=None, max_length=4000)
    recovery_protocol: str | None = Field(default=None, max_length=4000)
    progress_checkpoints: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def valid_period(self) -> "TrainingPlanCreate":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class TrainingPlanRead(BaseModel):
    id: UUID
    organization_id: UUID
    team_id: UUID | None
    athlete_profile_id: UUID | None
    created_by_person_id: UUID | None
    title: str
    focus_area: str
    period_start: date
    period_end: date
    status: TrainingPlanStatus
    ai_generated: bool
    source_summary: str | None
    load_guidance: str | None
    recovery_protocol: str | None
    progress_checkpoints: str | None


class TrainingPlanItemCreate(BaseModel):
    drill_id: UUID | None = None
    sequence: int = Field(default=1, ge=1)
    day_label: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=180)
    focus_area: str = Field(min_length=2, max_length=120)
    duration_minutes: int = Field(ge=1, le=240)
    intensity: int = Field(ge=1, le=10)
    notes: str | None = Field(default=None, max_length=4000)


class TrainingPlanItemRead(BaseModel):
    id: UUID
    plan_id: UUID
    drill_id: UUID | None
    sequence: int
    day_label: str
    title: str
    focus_area: str
    duration_minutes: int
    intensity: int
    notes: str | None


class TrainingPlanGenerateCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    athlete_profile_id: UUID | None = None
    title: str | None = Field(default=None, max_length=240)
    focus_area: str | None = Field(default=None, max_length=160)
    period_start: date
    period_end: date
    weekly_sessions: int = Field(default=3, ge=1, le=7)
    readiness_score: int = Field(default=70, ge=0, le=100)
    upcoming_competition_weight: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def valid_generated_period(self) -> "TrainingPlanGenerateCreate":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class GeneratedTrainingPlanRead(BaseModel):
    plan: TrainingPlanRead
    items: list[TrainingPlanItemRead]
    readiness_score: int
    rationale: str
    load_balance: str
    next_competition_at: datetime | None


class TrainingSessionPlanCreate(BaseModel):
    organization_id: UUID
    team_id: UUID
    plan_id: UUID | None = None
    event_id: UUID | None = None
    title: str = Field(min_length=2, max_length=240)
    scheduled_for: datetime
    duration_minutes: int = Field(ge=1, le=360)
    rpe_target: int = Field(ge=1, le=10)
    objectives: str | None = Field(default=None, max_length=4000)


class TrainingSessionPlanRead(BaseModel):
    id: UUID
    organization_id: UUID
    team_id: UUID
    plan_id: UUID | None
    event_id: UUID | None
    title: str
    scheduled_for: datetime
    duration_minutes: int
    rpe_target: int
    load_score: float
    objectives: str | None
    status: TrainingSessionStatus


class TrainingSessionFeedbackCreate(BaseModel):
    athlete_profile_id: UUID | None = None
    readiness_score: int = Field(ge=0, le=100)
    soreness_score: int = Field(default=0, ge=0, le=10)
    sleep_quality: int = Field(default=7, ge=0, le=10)
    mood_score: int = Field(default=7, ge=0, le=10)
    actual_rpe: int | None = Field(default=None, ge=1, le=10)
    actual_duration_minutes: int | None = Field(default=None, ge=1, le=360)
    completed: bool = False
    feedback: str | None = Field(default=None, max_length=4000)
    coach_notes: str | None = Field(default=None, max_length=4000)


class TrainingSessionFeedbackRead(BaseModel):
    id: UUID
    organization_id: UUID
    session_plan_id: UUID
    athlete_profile_id: UUID | None
    recorded_by_person_id: UUID | None
    readiness_score: int
    soreness_score: int
    sleep_quality: int
    mood_score: int
    actual_rpe: int | None
    actual_duration_minutes: int | None
    completed: bool
    feedback: str | None
    coach_notes: str | None
    recorded_at: datetime
    readiness_band: str
    load_delta: float | None
    recommendation: str
