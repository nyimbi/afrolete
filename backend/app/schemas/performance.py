from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import CommunicationChannel, MetricCategory, MetricSource, MetricVerificationStatus


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
    source_provider: str | None = Field(default=None, max_length=80)
    evidence_ref: str = Field(min_length=2, max_length=500)
    evidence_text: str | None = Field(default=None, max_length=8000)
    extracted_value: float | None = None
    observed_at: datetime | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class PerformanceIngestionRead(BaseModel):
    observation: PerformanceObservationRead
    evidence_ref: str
    source_provider: str | None
    extractor: str
    confidence: float
    review_required: bool
    summary: str
    parser_method: str
    parser_confidence_reason: str
    parser_warnings: list[str]
    parsed_fields: dict[str, str]
    model_assisted: bool
    model_policy: str | None
    model_confidence: float | None
    model_summary: str | None
    model_evaluation: dict[str, str]


class PerformanceWearableWebhookCreate(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID
    source_provider: str = Field(min_length=2, max_length=80)
    external_event_id: str = Field(min_length=2, max_length=180)
    payload: dict[str, Any]
    event_id: UUID | None = None
    metric_definition_ids: list[UUID] | None = None


class PerformanceWearableWebhookRead(BaseModel):
    ingest_event_id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    source_provider: str
    external_event_id: str
    replayed: bool
    signature_required: bool
    signature_validated: bool
    observation_count: int
    skipped_metric_count: int
    observation_ids: list[UUID]
    payload_hash: str
    received_at: datetime


class PerformanceWearableConnectionCreate(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID
    provider: str = Field(min_length=2, max_length=80)
    display_name: str = Field(min_length=2, max_length=180)
    external_athlete_ref: str = Field(min_length=2, max_length=180)
    status: str = Field(default="configured", max_length=40)
    auth_type: str = Field(default="oauth2", max_length=40)
    scopes: list[str] = Field(default_factory=list)
    access_token_secret_path: str | None = Field(default=None, max_length=500)
    refresh_token_secret_path: str | None = Field(default=None, max_length=500)
    webhook_secret_path: str | None = Field(default=None, max_length=500)
    token_expires_at: datetime | None = None
    provider_pull_url: str | None = Field(default=None, max_length=800)
    provider_pull_cursor_param: str | None = Field(default="cursor", max_length=80)
    provider_pull_since_param: str | None = Field(default="since", max_length=80)
    provider_pull_until_param: str | None = Field(default="until", max_length=80)
    sync_cursor: str | None = Field(default=None, max_length=240)
    webhook_registered: bool = False
    provider_webhook_registration_url: str | None = Field(default=None, max_length=800)
    provider_webhook_callback_url: str | None = Field(default=None, max_length=800)
    provider_webhook_event_types: list[str] = Field(default_factory=list)
    default_metric_definition_ids: list[UUID] = Field(default_factory=list)


class PerformanceWearableConnectionRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    provider: str
    display_name: str
    external_athlete_ref: str
    status: str
    auth_type: str
    scopes: list[str]
    access_token_configured: bool
    refresh_token_configured: bool
    webhook_secret_configured: bool
    access_token_recorded: bool
    refresh_token_recorded: bool
    refresh_token_family_id: str | None
    refresh_token_rotated_at: datetime | None
    token_last_refreshed_at: datetime | None
    token_type: str | None
    token_scope: list[str]
    token_expires_at: datetime | None
    oauth_client_id: str | None
    oauth_client_secret_configured: bool
    oauth_authorization_url: str | None
    oauth_token_url: str | None
    oauth_redirect_uri: str | None
    oauth_state_pending: bool
    oauth_state_expires_at: datetime | None
    oauth_authorized_at: datetime | None
    provider_pull_url: str | None
    provider_pull_cursor_param: str | None
    provider_pull_since_param: str | None
    provider_pull_until_param: str | None
    provider_pull_configured: bool
    sync_cursor: str | None
    last_sync_at: datetime | None
    webhook_registered: bool
    provider_webhook_registration_url: str | None
    provider_webhook_callback_url: str | None
    provider_webhook_event_types: list[str]
    provider_webhook_registration_status_code: int | None
    provider_webhook_registration_hash: str | None
    provider_webhook_registered_at: datetime | None
    provider_webhook_registration_error: str | None
    default_metric_definition_ids: list[UUID]


class PerformanceWearableSyncRunCreate(BaseModel):
    external_event_id: str | None = Field(default=None, max_length=180)
    payload: dict[str, Any] | None = None
    metric_definition_ids: list[UUID] | None = None
    sync_mode: str = Field(default="pull", max_length=40)
    since: datetime | None = None
    until: datetime | None = None
    max_pages: int = Field(default=3, ge=1, le=10)


class PerformanceWearableSyncRunRead(BaseModel):
    id: UUID
    organization_id: UUID
    connection_id: UUID
    athlete_profile_id: UUID
    provider: str
    external_event_id: str | None
    status: str
    sync_mode: str
    started_at: datetime
    completed_at: datetime | None
    observation_count: int
    skipped_metric_count: int
    replayed: bool
    provider_status_code: int | None
    provider_response_hash: str | None
    provider_page_count: int
    provider_rate_limited: bool
    provider_retry_after_seconds: int | None
    message: str | None


class PerformanceWearablePullRetryWorkerRunRead(BaseModel):
    organization_id: UUID | None
    eligible_count: int
    retried_count: int
    skipped_count: int
    failed_count: int
    rate_limited_count: int
    provider_retry_after_seconds: dict[str, int]
    provider_max_pages: dict[str, int]
    provider_policy_matches: dict[str, int]
    connection_ids: list[UUID]
    sync_run_ids: list[UUID]


class PerformanceWearableWebhookRegistrationCreate(BaseModel):
    callback_url: str = Field(min_length=8, max_length=800)
    registration_url: str | None = Field(default=None, max_length=800)
    event_types: list[str] = Field(default_factory=list)
    signing_secret_path: str | None = Field(default=None, max_length=500)
    provider_payload: dict[str, Any] = Field(default_factory=dict)


class PerformanceWearableWebhookRegistrationRead(BaseModel):
    connection: PerformanceWearableConnectionRead
    status: str
    registered: bool
    provider_status_code: int | None
    registration_payload_hash: str
    message: str


class PerformanceWearableOAuthStartCreate(BaseModel):
    client_id: str = Field(min_length=2, max_length=180)
    client_secret_path: str | None = Field(default=None, max_length=500)
    authorization_url: str = Field(min_length=8, max_length=800)
    redirect_uri: str = Field(min_length=8, max_length=800)
    token_url: str | None = Field(default=None, max_length=800)
    scopes: list[str] | None = None
    state_ttl_seconds: int = Field(default=600, ge=60, le=3600)


class PerformanceWearableOAuthStartRead(BaseModel):
    connection_id: UUID
    provider: str
    authorization_url: str
    state: str
    expires_at: datetime
    scopes: list[str]


class PerformanceWearableProviderTokenResponse(BaseModel):
    access_token: str | None = Field(default=None, max_length=8000)
    refresh_token: str | None = Field(default=None, max_length=8000)
    expires_in: int | None = Field(default=None, ge=1, le=31_536_000)
    token_type: str | None = Field(default=None, max_length=40)
    scope: str | list[str] | None = None


class PerformanceWearableOAuthCallbackCreate(BaseModel):
    state: str = Field(min_length=16, max_length=500)
    code: str = Field(min_length=2, max_length=1000)
    access_token_secret_path: str | None = Field(default=None, max_length=500)
    refresh_token_secret_path: str | None = Field(default=None, max_length=500)
    token_expires_at: datetime | None = None
    provider_token_response: PerformanceWearableProviderTokenResponse | None = None


class PerformanceWearableOAuthCallbackRead(BaseModel):
    connection: PerformanceWearableConnectionRead
    status: str
    message: str
    authorization_code_ref: str


class PerformanceWearableTokenRefreshCreate(BaseModel):
    access_token_secret_path: str | None = Field(default=None, max_length=500)
    refresh_token_secret_path: str | None = Field(default=None, max_length=500)
    token_expires_at: datetime | None = None
    provider_token_response: PerformanceWearableProviderTokenResponse | None = None


class PerformanceWearableTokenRefreshRead(BaseModel):
    connection: PerformanceWearableConnectionRead
    status: str
    message: str
    access_token_ref: str | None
    refresh_token_rotated: bool


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
    perceived_exertion: float | None = Field(default=None, ge=0, le=10)
    effort_rating: float | None = Field(default=None, ge=0, le=10)
    summary: str | None = Field(default=None, max_length=4000)
    recommendations: str | None = Field(default=None, max_length=4000)
    verification_status: MetricVerificationStatus = MetricVerificationStatus.VERIFIED


class PlayerSelfAssessmentCreate(BaseModel):
    organization_id: UUID
    event_id: UUID | None = None
    assessed_at: datetime | None = None
    physical_score: float = Field(ge=0, le=100)
    technical_score: float = Field(ge=0, le=100)
    tactical_score: float = Field(ge=0, le=100)
    mental_score: float = Field(ge=0, le=100)
    perceived_exertion: float = Field(ge=0, le=10)
    effort_rating: float = Field(ge=0, le=10)
    summary: str | None = Field(default=None, max_length=4000)


class AthleteAssessmentReviewCreate(BaseModel):
    verification_status: MetricVerificationStatus
    physical_score: float | None = Field(default=None, ge=0, le=100)
    technical_score: float | None = Field(default=None, ge=0, le=100)
    tactical_score: float | None = Field(default=None, ge=0, le=100)
    mental_score: float | None = Field(default=None, ge=0, le=100)
    perceived_exertion: float | None = Field(default=None, ge=0, le=10)
    effort_rating: float | None = Field(default=None, ge=0, le=10)
    summary: str | None = Field(default=None, max_length=4000)
    recommendations: str | None = Field(default=None, max_length=4000)


class AthleteAssessmentReviewAssignmentUpdate(BaseModel):
    assign_to_self: bool = False
    clear_assignment: bool = False
    assigned_to_person_id: UUID | None = None
    review_due_at: datetime | None = None
    review_priority: str | None = Field(default=None, pattern="^(low|normal|high|urgent)$")
    review_notes: str | None = Field(default=None, max_length=4000)


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
    perceived_exertion: float | None
    effort_rating: float | None
    summary: str | None
    recommendations: str | None
    review_assigned_to_person_id: UUID | None
    review_due_at: datetime | None
    review_priority: str
    review_notes: str | None
    reviewed_by_person_id: UUID | None
    reviewed_at: datetime | None
    review_last_escalated_at: datetime | None
    review_escalation_count: int
    review_escalation_message_id: UUID | None
    verification_status: MetricVerificationStatus


class AthleteAssessmentReviewQueueItemRead(BaseModel):
    assessment: AthleteAssessmentRead
    athlete_person_id: UUID
    athlete_name: str
    review_assigned_to_name: str | None
    review_sla_state: str
    review_age_hours: int


class AssessmentReviewLoadRead(BaseModel):
    reviewer_person_id: UUID | None
    reviewer_name: str
    open_count: int
    overdue_count: int
    urgent_count: int
    escalated_count: int
    oldest_age_hours: int


class AssessmentReviewQueueSummaryRead(BaseModel):
    organization_id: UUID
    open_count: int
    unassigned_count: int
    assigned_count: int
    overdue_count: int
    due_soon_count: int
    on_track_count: int
    unscheduled_count: int
    urgent_count: int
    escalated_count: int
    average_age_hours: int
    oldest_age_hours: int
    priority_counts: dict[str, int]
    reviewer_loads: list[AssessmentReviewLoadRead]


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
    cohort_scope: str
    cohort_label: str
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


class PerformanceCohortComparisonRead(BaseModel):
    cohort_scope: str
    cohort_label: str
    metric_count: int
    sample_size_total: int
    average_percentile: float | None
    watch_count: int
    top_metric_name: str | None
    top_percentile: float | None
    recommendation: str
    benchmarks: list[PerformanceMetricBenchmarkRead]


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


class PerformanceMetricTrendPointRead(BaseModel):
    observation_id: UUID
    observed_at: datetime
    value: float
    normalized_value: float
    source: MetricSource
    verification_status: MetricVerificationStatus


class PerformanceMetricTrendSeriesRead(BaseModel):
    metric_definition_id: UUID
    metric_code: str
    metric_name: str
    sport: str | None
    category: MetricCategory
    unit: str | None
    higher_is_better: bool
    sample_size: int
    latest_value: float | None
    forecast_next_value: float | None
    trend_direction: str
    recommendation: str
    points: list[PerformanceMetricTrendPointRead]


class PerformanceForecastScenarioRead(BaseModel):
    metric_definition_id: UUID
    metric_code: str
    metric_name: str
    sport: str | None
    category: MetricCategory
    unit: str | None
    higher_is_better: bool
    sample_size: int
    latest_value: float | None
    forecast_next_value: float | None
    forecast_low: float | None
    forecast_high: float | None
    confidence: float
    data_quality: str
    risk_level: str
    trend_direction: str
    model_policy: str
    projected_points: list[float]
    recommendation: str


class PerformanceForecastWhatIfRead(PerformanceForecastScenarioRead):
    scenario_label: str
    training_adjustment_percent: float
    readiness_score: int
    horizon: int


class PerformanceInjuryRiskRead(BaseModel):
    athlete_profile_id: UUID
    generated_at: datetime
    model_policy: str
    score: int
    risk_band: str
    confidence: float
    latest_readiness_score: int | None
    average_readiness_score: float | None
    average_soreness_score: float | None
    average_sleep_quality: float | None
    latest_load: float | None
    average_load: float | None
    acute_load: float | None
    chronic_load: float | None
    acute_chronic_ratio: float | None
    load_delta: float | None
    open_incident_count: int
    declining_metric_count: int
    latest_weather_alert_level: str | None
    latest_weather_decision: str | None
    weather_alert_count: int
    hazardous_surface_count: int
    environmental_risk_count: int
    surface_risk_labels: list[str]
    wearable_observation_count: int
    biomarker_risk_count: int
    latest_hrv: float | None
    latest_resting_heart_rate: float | None
    latest_recovery_score: float | None
    latest_hydration_score: float | None
    wearable_risk_labels: list[str]
    drivers: list[str]
    recommendation: str


class PerformanceInjuryRiskAlertRead(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID
    score: int
    risk_band: str
    threshold_score: int
    sent: bool
    dry_run: bool = False
    channels: list[CommunicationChannel]
    channel_count: int
    recipient_count: int
    message_id: UUID | None
    message_ids: list[UUID]
    skipped_reason: str | None
    risk: PerformanceInjuryRiskRead


class PerformanceInjuryRiskAlertRunRead(BaseModel):
    organization_id: UUID | None
    threshold_score: int
    repeat_after_hours: int
    dry_run: bool = False
    channels: list[CommunicationChannel]
    channel_count: int
    eligible_count: int
    scanned_count: int
    alerted_count: int
    skipped_count: int
    failed_count: int
    high_risk_count: int
    highest_score: int | None
    athlete_profile_ids: list[UUID]
    message_ids: list[UUID]
    skipped_reasons: dict[str, int]


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


class PerformanceAssessmentReviewEscalationRunRead(BaseModel):
    organization_id: UUID | None
    eligible_count: int
    escalated_count: int
    skipped_count: int
    failed_count: int
    overdue_count: int
    due_soon_count: int
    assessment_ids: list[UUID]
    message_ids: list[UUID]
    dry_run: bool = False


class PlayerPerformanceProfileRead(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID
    athlete_person_id: UUID
    athlete_name: str
    latest_overall_score: float | None
    observation_count: int
    assessment_count: int
    latest_assessment_id: UUID | None
    latest_assessment: AthleteAssessmentRead | None
    rating: str | None
    active_goal_count: int
    achieved_goal_count: int
    award_count: int
    observations: list[PerformanceObservationRead]
    goals: list[PerformanceGoalRead]
    awards: list[PerformanceAchievementAwardRead]
    trends: list[PerformanceMetricTrendRead]
    trend_series: list[PerformanceMetricTrendSeriesRead]
    forecast_scenarios: list[PerformanceForecastScenarioRead]
    benchmarks: list[PerformanceMetricBenchmarkRead]
    cohort_comparisons: list[PerformanceCohortComparisonRead]
