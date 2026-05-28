from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import MetricCategory, MetricSource, MetricVerificationStatus


class MetricDefinitionCreate(BaseModel):
    organization_id: UUID
    sport: str | None = Field(default=None, max_length=80)
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=180)
    category: MetricCategory
    unit: str | None = Field(default=None, max_length=40)
    description: str | None = Field(default=None, max_length=2000)
    min_value: float | None = None
    max_value: float | None = None
    weight: float = Field(default=1.0, ge=0)
    higher_is_better: bool = True

    @model_validator(mode="after")
    def valid_range(self) -> "MetricDefinitionCreate":
        if self.min_value is not None and self.max_value is not None and self.max_value <= self.min_value:
            raise ValueError("max_value must be greater than min_value")
        return self


class MetricDefinitionRead(BaseModel):
    id: UUID
    organization_id: UUID
    sport: str | None
    code: str
    name: str
    category: MetricCategory
    unit: str | None
    description: str | None
    min_value: float | None
    max_value: float | None
    weight: float
    higher_is_better: bool
    status: str


class PerformanceObservationCreate(BaseModel):
    organization_id: UUID
    metric_definition_id: UUID
    event_id: UUID | None = None
    value: float
    raw_value: str | None = Field(default=None, max_length=160)
    observed_at: datetime | None = None
    source: MetricSource = MetricSource.COACH_EVALUATION
    confidence: float | None = Field(default=None, ge=0, le=1)
    verification_status: MetricVerificationStatus = MetricVerificationStatus.VERIFIED
    notes: str | None = Field(default=None, max_length=2000)


class PerformanceObservationRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    metric_definition_id: UUID
    event_id: UUID | None
    recorded_by_person_id: UUID | None
    value: float
    raw_value: str | None
    observed_at: datetime
    source: MetricSource
    confidence: float | None
    verification_status: MetricVerificationStatus
    notes: str | None


class PerformanceIngestionCreate(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID
    metric_definition_id: UUID
    event_id: UUID | None = None
    source: MetricSource
    evidence_ref: str = Field(min_length=2, max_length=500)
    evidence_text: str | None = Field(default=None, max_length=8000)
    extracted_value: float | None = None
    observed_at: datetime | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class PerformanceIngestionRead(BaseModel):
    observation: PerformanceObservationRead
    evidence_ref: str
    extractor: str
    confidence: float
    review_required: bool
    summary: str


class PerformanceObservationReviewCreate(BaseModel):
    verification_status: MetricVerificationStatus
    value: float | None = None
    notes: str | None = Field(default=None, max_length=2000)


class AthleteAssessmentCreate(BaseModel):
    organization_id: UUID
    event_id: UUID | None = None
    assessed_at: datetime | None = None
    physical_score: float = Field(ge=0, le=100)
    technical_score: float = Field(ge=0, le=100)
    tactical_score: float = Field(ge=0, le=100)
    mental_score: float = Field(ge=0, le=100)
    overall_score: float | None = Field(default=None, ge=0, le=100)
    summary: str | None = Field(default=None, max_length=4000)
    recommendations: str | None = Field(default=None, max_length=4000)
    verification_status: MetricVerificationStatus = MetricVerificationStatus.VERIFIED


class AthleteAssessmentRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    event_id: UUID | None
    assessed_by_person_id: UUID | None
    assessed_at: datetime
    physical_score: float
    technical_score: float
    tactical_score: float
    mental_score: float
    overall_score: float
    summary: str | None
    recommendations: str | None
    verification_status: MetricVerificationStatus


class AthletePerformanceSummaryRead(BaseModel):
    athlete_profile_id: UUID
    latest_overall_score: float | None
    observation_count: int
    assessment_count: int
    latest_assessment_id: UUID | None
    rating: str | None


class PerformanceMetricBenchmarkRead(BaseModel):
    metric_definition_id: UUID
    metric_code: str
    metric_name: str
    sport: str | None
    category: MetricCategory
    unit: str | None
    higher_is_better: bool
    sample_size: int
    athlete_value: float | None
    cohort_average: float | None
    cohort_min: float | None
    cohort_max: float | None
    delta_to_average: float | None
    percentile_rank: float | None
    cohort_rank: int | None
    benchmark_band: str
    recommendation: str


class PerformanceMetricTrendRead(BaseModel):
    metric_definition_id: UUID
    metric_code: str
    metric_name: str
    sport: str | None
    category: MetricCategory
    unit: str | None
    higher_is_better: bool
    sample_size: int
    first_value: float | None
    previous_value: float | None
    latest_value: float | None
    best_value: float | None
    average_value: float | None
    change_from_previous: float | None
    change_from_first: float | None
    consistency_index: float | None
    forecast_next_value: float | None
    trend_direction: str
    recommendation: str


class PerformanceGoalCreate(BaseModel):
    organization_id: UUID
    metric_definition_id: UUID
    title: str = Field(min_length=2, max_length=220)
    target_value: float
    baseline_value: float | None = None
    direction: str | None = Field(default=None, max_length=40)
    starts_at: date
    due_at: date | None = None
    reward_badge: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)


class PerformanceGoalRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    metric_definition_id: UUID
    title: str
    target_value: float
    baseline_value: float | None
    current_value: float | None
    direction: str
    starts_at: date
    due_at: date | None
    status: str
    reward_badge: str | None
    notes: str | None


class PerformanceAchievementAwardRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    goal_id: UUID | None
    metric_definition_id: UUID | None
    title: str
    badge_code: str
    achievement_type: str
    achieved_value: float | None
    threshold_value: float | None
    awarded_at: datetime
    source_summary: str | None


class PerformanceAchievementRunRead(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID
    evaluated_goals: int
    awarded_count: int
    updated_goals: int
    awards: list[PerformanceAchievementAwardRead]


class PerformanceAchievementWorkerRunRead(BaseModel):
    organization_id: UUID | None
    eligible_count: int
    executed_count: int
    skipped_count: int
    failed_count: int
    athlete_profile_ids: list[UUID]
    awarded_count: int
    updated_goals: int
