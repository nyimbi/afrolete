from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    CommunicationChannel,
    MessageDeliveryStatus,
    MetricCategory,
    MetricSource,
    MetricVerificationStatus,
)


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


class PerformanceModelExtractionReviewQueueItemRead(BaseModel):
    observation: PerformanceObservationRead
    metric_code: str
    metric_name: str
    metric_category: MetricCategory
    unit: str | None
    model_assisted: bool
    model_policy: str | None
    evidence_ref: str | None
    review_priority: str
    confidence_label: str
    recommended_action: str
    review_reason: str
    flags: list[str]
    age_hours: float


class PerformanceModelExtractionReviewQueueRead(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID | None
    pending_count: int
    model_assisted_count: int
    high_priority_count: int
    average_confidence: float | None
    recommendations: list[str]
    items: list[PerformanceModelExtractionReviewQueueItemRead]


class PerformanceModelExtractionBulkReviewCreate(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID | None = None
    observation_ids: list[UUID] = Field(default_factory=list, max_length=100)
    verification_status: MetricVerificationStatus = MetricVerificationStatus.VERIFIED
    max_items: int = Field(default=25, ge=1, le=100)
    min_confidence: float = Field(default=0.0, ge=0, le=1)
    only_model_assisted: bool = True
    notes: str | None = Field(default=None, max_length=1200)


class PerformanceModelExtractionBulkReviewRead(BaseModel):
    organization_id: UUID
    reviewed_count: int
    skipped_count: int
    verification_status: MetricVerificationStatus
    summary: str
    recommendations: list[str]
    observations: list[PerformanceObservationRead]


class PerformanceVideoCoachingCreate(BaseModel):
    organization_id: UUID
    event_id: UUID | None = None
    sport: str = Field(default="athletics", min_length=2, max_length=80)
    video_uri: str = Field(min_length=2, max_length=800)
    clip_label: str | None = Field(default=None, max_length=180)
    analysis_focus: str = Field(
        default="stride mechanics, posture, acceleration, rhythm, and tactical execution",
        max_length=1000,
    )
    evidence_text: str | None = Field(default=None, max_length=12000)
    provider: str = Field(default="afrolete_deterministic_video_coach", max_length=80)
    observed_at: datetime | None = None


class PerformanceVideoCoachingMetricRead(BaseModel):
    metric_definition_id: UUID
    metric_code: str
    metric_name: str
    category: MetricCategory
    value: float
    unit: str | None
    confidence: float
    coaching_cue: str
    evidence_summary: str


class PerformanceVideoCoachingRead(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID
    event_id: UUID | None
    sport: str
    video_uri: str
    clip_label: str | None
    model_policy: str
    confidence: float
    summary: str
    coaching_plan: str
    review_required: bool
    observations: list[PerformanceObservationRead]
    assessment: "AthleteAssessmentRead"
    metrics: list[PerformanceVideoCoachingMetricRead]
    next_actions: list[str]


class PerformanceVideoUploadCreate(BaseModel):
    organization_id: UUID
    event_id: UUID | None = None
    sport: str = Field(default="athletics", min_length=2, max_length=80)
    filename: str = Field(min_length=1, max_length=240)
    content_type: str = Field(default="video/mp4", max_length=120)
    content_base64: str = Field(min_length=1)
    clip_label: str | None = Field(default=None, max_length=180)
    analysis_focus: str = Field(
        default="pose, gait, stride mechanics, posture, arm drive, and movement efficiency",
        max_length=1000,
    )
    duration_seconds: float | None = Field(default=None, ge=0, le=12 * 60 * 60)
    frame_rate: float | None = Field(default=None, ge=1, le=1000)
    frame_width: int | None = Field(default=None, ge=1, le=16384)
    frame_height: int | None = Field(default=None, ge=1, le=16384)


class PerformanceVideoAssetRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    event_id: UUID | None
    uploaded_by_person_id: UUID | None
    sport: str
    filename: str
    content_type: str
    size_bytes: int
    checksum: str
    storage_url: str
    video_uri: str
    clip_label: str | None
    analysis_focus: str | None
    duration_seconds: float | None
    frame_rate: float | None
    frame_width: int | None
    frame_height: int | None
    status: str
    analysis_model_policy: str | None
    analyzed_at: datetime | None
    slow_motion_rates: list[float]
    review_default_rate: float


class OppositionScoutingVideoUploadCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    competition_id: UUID | None = None
    event_id: UUID | None = None
    opponent_name: str = Field(min_length=2, max_length=180)
    sport: str = Field(default="football", min_length=2, max_length=80)
    filename: str = Field(min_length=1, max_length=240)
    content_type: str = Field(default="video/mp4", max_length=120)
    content_base64: str = Field(min_length=1)
    clip_label: str | None = Field(default=None, max_length=180)
    match_context: str | None = Field(default=None, max_length=4000)
    analysis_focus: str = Field(
        default="formation, pressing triggers, transition defense, set pieces, chance creation, and tactical weaknesses",
        max_length=1000,
    )


class OppositionScoutingVideoAssetRead(BaseModel):
    id: UUID
    organization_id: UUID
    team_id: UUID | None
    competition_id: UUID | None
    event_id: UUID | None
    uploaded_by_person_id: UUID | None
    opponent_name: str
    sport: str
    filename: str
    content_type: str
    size_bytes: int
    checksum: str
    storage_url: str
    video_uri: str
    clip_label: str | None
    match_context: str | None
    analysis_focus: str | None
    status: str
    analyzed_at: datetime | None


class OppositionScoutingReportCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    competition_id: UUID | None = None
    event_id: UUID | None = None
    observed_formation: str | None = Field(default=None, max_length=80)
    match_context: str | None = Field(default=None, max_length=4000)
    analysis_focus: str | None = Field(default=None, max_length=1000)
    evidence_text: str | None = Field(default=None, max_length=12000)


class OppositionScoutingFindingRead(BaseModel):
    category: str
    title: str
    severity: str
    evidence: str
    recommendation: str


class OppositionScoutingReportRead(BaseModel):
    id: UUID
    organization_id: UUID
    video_asset_id: UUID
    team_id: UUID | None
    competition_id: UUID | None
    event_id: UUID | None
    created_by_person_id: UUID | None
    opponent_name: str
    sport: str
    match_context: str | None
    analysis_focus: str | None
    model_policy: str
    confidence: float
    formation_detected: str | None
    tactical_summary: str
    weaknesses: list[OppositionScoutingFindingRead]
    threats: list[OppositionScoutingFindingRead]
    recommendations: list[OppositionScoutingFindingRead]
    set_pieces: list[OppositionScoutingFindingRead]
    tracking_evidence: list[OppositionScoutingFindingRead] = Field(default_factory=list)
    status: str
    generated_at: datetime


class PerformanceVideoAnnotationCreate(BaseModel):
    timestamp_seconds: float = Field(ge=0)
    playback_rate: float = Field(default=0.5, ge=0.05, le=2)
    annotation_type: str = Field(default="coach_note", min_length=2, max_length=80)
    label: str = Field(min_length=2, max_length=180)
    notes: str | None = Field(default=None, max_length=4000)
    body_region: str | None = Field(default=None, max_length=80)
    x_percent: float | None = Field(default=None, ge=0, le=100)
    y_percent: float | None = Field(default=None, ge=0, le=100)
    width_percent: float | None = Field(default=None, ge=0, le=100)
    height_percent: float | None = Field(default=None, ge=0, le=100)
    tags: list[str] = Field(default_factory=list, max_length=20)


class PerformanceVideoAnnotationRead(BaseModel):
    id: UUID
    organization_id: UUID
    video_asset_id: UUID
    athlete_profile_id: UUID
    event_id: UUID | None
    author_person_id: UUID | None
    timestamp_seconds: float
    playback_rate: float
    annotation_type: str
    label: str
    notes: str | None
    body_region: str | None
    x_percent: float | None
    y_percent: float | None
    width_percent: float | None
    height_percent: float | None
    tags: list[str]
    created_at: datetime


class PerformancePoseKeypoint(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    x_percent: float = Field(ge=0, le=100)
    y_percent: float = Field(ge=0, le=100)
    z: float | None = Field(default=None, ge=-1000, le=1000)
    confidence: float | None = Field(default=None, ge=0, le=1)


class PerformanceVideoPoseSampleCreate(BaseModel):
    source_provider: str = Field(default="manual_pose", min_length=2, max_length=80)
    frame_index: int | None = Field(default=None, ge=0)
    timestamp_seconds: float = Field(ge=0)
    phase: str | None = Field(default=None, max_length=80)
    contact_foot: str | None = Field(default=None, max_length=20)
    stride_index: int | None = Field(default=None, ge=0)
    sample_confidence: float | None = Field(default=None, ge=0, le=1)
    keypoints: list[PerformancePoseKeypoint] = Field(min_length=4, max_length=80)


class PerformanceVideoPoseSampleBatchCreate(BaseModel):
    organization_id: UUID
    replace_existing: bool = False
    samples: list[PerformanceVideoPoseSampleCreate] = Field(min_length=1, max_length=600)


class PerformanceVideoPoseSampleRead(BaseModel):
    id: UUID
    organization_id: UUID
    video_asset_id: UUID
    athlete_profile_id: UUID
    event_id: UUID | None
    created_by_person_id: UUID | None
    source_provider: str
    frame_index: int | None
    timestamp_seconds: float
    phase: str | None
    contact_foot: str | None
    stride_index: int | None
    sample_confidence: float | None
    keypoints: list[PerformancePoseKeypoint]
    created_at: datetime


class PerformanceVideoPoseSampleBatchRead(BaseModel):
    video_asset: PerformanceVideoAssetRead
    sample_count: int
    source_providers: list[str]
    samples: list[PerformanceVideoPoseSampleRead]


class PerformanceVideoPoseProcessingCreate(BaseModel):
    organization_id: UUID
    replace_existing: bool = True
    max_frames: int = Field(default=45, ge=1, le=600)
    sample_every_seconds: float = Field(default=0.2, ge=0.033, le=10)
    min_detection_confidence: float = Field(default=0.5, ge=0, le=1)
    run_analysis: bool = True
    reference_profile_id: UUID | None = None


class PerformanceVideoPoseProcessingRead(BaseModel):
    video_asset: PerformanceVideoAssetRead
    model_policy: str
    source_provider: str
    processed_frame_count: int
    decoded_frame_count: int
    sample_count: int
    warning_count: int
    warnings: list[str]
    pose_samples: PerformanceVideoPoseSampleBatchRead
    analysis_summary: str | None = None
    analysis_model_policy: str | None = None


class PerformanceMovementReferenceMetricTarget(BaseModel):
    key: str = Field(min_length=2, max_length=80)
    label: str = Field(min_length=2, max_length=180)
    category: MetricCategory = MetricCategory.TECHNICAL
    unit: str = Field(default="score", max_length=40)
    optimal_min: float
    optimal_max: float
    benchmark_label: str | None = Field(default=None, max_length=240)
    coaching_cue: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def valid_target_range(self) -> "PerformanceMovementReferenceMetricTarget":
        if self.optimal_max <= self.optimal_min:
            raise ValueError("optimal_max must be greater than optimal_min")
        return self


class PerformanceMovementReferenceProfileCreate(BaseModel):
    organization_id: UUID
    sport: str = Field(default="athletics", min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=180)
    benchmark_profile: str = Field(default="world_class_sprint", min_length=2, max_length=120)
    performer_name: str | None = Field(default=None, max_length=180)
    source_label: str = Field(min_length=2, max_length=240)
    competition_context: str | None = Field(default=None, max_length=240)
    consent_basis: str | None = Field(default=None, max_length=240)
    visibility: str = Field(default="tenant", max_length=40)
    metric_targets: list[PerformanceMovementReferenceMetricTarget] = Field(min_length=1, max_length=30)
    pose_samples: list[PerformanceVideoPoseSampleCreate] = Field(default_factory=list, max_length=100)
    notes: str | None = Field(default=None, max_length=4000)


class PerformanceMovementReferenceProfileRead(BaseModel):
    id: UUID
    organization_id: UUID
    created_by_person_id: UUID | None
    sport: str
    name: str
    benchmark_profile: str
    performer_name: str | None
    source_label: str
    competition_context: str | None
    consent_basis: str | None
    visibility: str
    status: str
    metric_targets: list[PerformanceMovementReferenceMetricTarget]
    pose_samples: list[PerformanceVideoPoseSampleCreate]
    notes: str | None
    created_at: datetime


class PerformancePoseGaitMetricRead(BaseModel):
    key: str
    label: str
    category: MetricCategory
    observed_value: float
    optimal_min: float
    optimal_max: float
    unit: str
    score: float
    delta_from_optimal: float
    benchmark_label: str
    coaching_cue: str
    source: str = "benchmark_template"


class PerformancePoseGaitPhaseRead(BaseModel):
    phase: str
    timestamp_seconds: float
    playback_rate: float
    focus: str
    finding: str
    benchmark_note: str


class PerformanceOptimalProjectionRead(BaseModel):
    priority: str
    current_score: float
    projected_score: float
    target_change: str
    drill: str


class PerformancePoseGaitAnalysisCreate(BaseModel):
    evidence_text: str | None = Field(default=None, max_length=12000)
    analysis_focus: str | None = Field(default=None, max_length=1000)
    benchmark_profile: str = Field(default="world_class_sprint", max_length=120)
    reference_profile_id: UUID | None = None
    create_coaching_outputs: bool = True


class PerformancePoseGaitAnalysisRead(BaseModel):
    video_asset: PerformanceVideoAssetRead
    model_policy: str
    benchmark_profile: str
    reference_profile_id: UUID | None = None
    reference_profile_name: str | None = None
    reference_profile_source: str | None = None
    confidence: float
    pose_sample_count: int = 0
    pose_sample_source_providers: list[str] = Field(default_factory=list)
    summary: str
    metrics: list[PerformancePoseGaitMetricRead]
    phases: list[PerformancePoseGaitPhaseRead]
    optimal_projections: list[PerformanceOptimalProjectionRead]
    slow_motion_rates: list[float]
    annotations: list[PerformanceVideoAnnotationRead]
    coaching: PerformanceVideoCoachingRead | None


class PerformancePitchCalibrationPoint(BaseModel):
    label: str = Field(min_length=2, max_length=80)
    image_x_percent: float = Field(ge=0, le=100)
    image_y_percent: float = Field(ge=0, le=100)
    pitch_x_meters: float = Field(ge=0, le=130)
    pitch_y_meters: float = Field(ge=0, le=90)


class PerformanceMatchPitchCalibrationCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    calibration_method: str = Field(default="manual_corner_map", min_length=2, max_length=80)
    pitch_length_m: float = Field(default=105.0, ge=80, le=130)
    pitch_width_m: float = Field(default=68.0, ge=45, le=90)
    points: list[PerformancePitchCalibrationPoint] = Field(min_length=4, max_length=12)
    status: str = Field(default="active", pattern="^(active|draft|retired)$")
    notes: str | None = Field(default=None, max_length=4000)


class PerformanceMatchPitchCalibrationRead(BaseModel):
    id: UUID
    organization_id: UUID
    video_asset_id: UUID
    created_by_person_id: UUID | None
    name: str
    calibration_method: str
    pitch_length_m: float
    pitch_width_m: float
    quality_score: float
    points: list[PerformancePitchCalibrationPoint]
    transform: dict[str, float | str]
    status: str
    notes: str | None
    created_at: datetime


class PerformanceMatchTrackingSampleCreate(BaseModel):
    track_id: str = Field(min_length=1, max_length=120)
    person_id: UUID | None = None
    team_label: str | None = Field(default=None, max_length=120)
    player_label: str | None = Field(default=None, max_length=180)
    jersey_number: str | None = Field(default=None, max_length=20)
    frame_index: int | None = Field(default=None, ge=0)
    timestamp_seconds: float = Field(ge=0)
    x_percent: float | None = Field(default=None, ge=0, le=100)
    y_percent: float | None = Field(default=None, ge=0, le=100)
    x_meters: float | None = Field(default=None, ge=0, le=130)
    y_meters: float | None = Field(default=None, ge=0, le=90)
    speed_mps: float | None = Field(default=None, ge=0, le=15)
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: str = Field(default="tracking_sample", min_length=2, max_length=80)

    @model_validator(mode="after")
    def has_position(self) -> "PerformanceMatchTrackingSampleCreate":
        has_percent = self.x_percent is not None and self.y_percent is not None
        has_meters = self.x_meters is not None and self.y_meters is not None
        if not has_percent and not has_meters:
            raise ValueError("Provide either percent coordinates or pitch-meter coordinates")
        return self


class PerformanceMatchTrackingRunCreate(BaseModel):
    organization_id: UUID
    calibration_id: UUID | None = None
    source_provider: str = Field(default="manual_tracking", min_length=2, max_length=80)
    model_policy: str | None = Field(default=None, min_length=2, max_length=160)
    pitch_length_m: float = Field(default=105.0, ge=80, le=130)
    pitch_width_m: float = Field(default=68.0, ge=45, le=90)
    replace_existing: bool = False
    auto_track: bool = False
    max_frames: int = Field(default=120, ge=1, le=2000)
    sample_every_seconds: float = Field(default=0.5, ge=0.04, le=10)
    min_detection_confidence: float = Field(default=0.35, ge=0, le=1)
    samples: list[PerformanceMatchTrackingSampleCreate] = Field(default_factory=list, max_length=5000)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
    quality_warnings: list[str] = Field(default_factory=list, max_length=20)


class PerformanceMatchTrackingProviderDetection(BaseModel):
    track_id: str = Field(min_length=1, max_length=120)
    object_type: str = Field(default="player", pattern="^(player|ball)$")
    person_id: UUID | None = None
    team_label: str | None = Field(default=None, max_length=120)
    player_label: str | None = Field(default=None, max_length=180)
    jersey_number: str | None = Field(default=None, max_length=20)
    x_percent: float | None = Field(default=None, ge=0, le=100)
    y_percent: float | None = Field(default=None, ge=0, le=100)
    x_meters: float | None = Field(default=None, ge=0, le=130)
    y_meters: float | None = Field(default=None, ge=0, le=90)
    bbox_x_percent: float | None = Field(default=None, ge=0, le=100)
    bbox_y_percent: float | None = Field(default=None, ge=0, le=100)
    bbox_width_percent: float | None = Field(default=None, ge=0, le=100)
    bbox_height_percent: float | None = Field(default=None, ge=0, le=100)
    foot_x_percent: float | None = Field(default=None, ge=0, le=100)
    foot_y_percent: float | None = Field(default=None, ge=0, le=100)
    speed_mps: float | None = Field(default=None, ge=0, le=15)
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def has_detection_position(self) -> "PerformanceMatchTrackingProviderDetection":
        has_percent = self.x_percent is not None and self.y_percent is not None
        has_meters = self.x_meters is not None and self.y_meters is not None
        has_foot = self.foot_x_percent is not None and self.foot_y_percent is not None
        has_bbox = (
            self.bbox_x_percent is not None
            and self.bbox_y_percent is not None
            and self.bbox_width_percent is not None
            and self.bbox_height_percent is not None
        )
        if not any([has_percent, has_meters, has_foot, has_bbox]):
            raise ValueError("Provide percent, meter, foot-point, or bounding-box coordinates")
        return self


class PerformanceMatchTrackingProviderFrame(BaseModel):
    timestamp_seconds: float = Field(ge=0)
    frame_index: int | None = Field(default=None, ge=0)
    detections: list[PerformanceMatchTrackingProviderDetection] = Field(min_length=1, max_length=80)


class PerformanceMatchTrackingProviderImportCreate(BaseModel):
    organization_id: UUID
    calibration_id: UUID | None = None
    source_provider: str = Field(default="external_tracking_provider", min_length=2, max_length=80)
    model_policy: str = Field(default="external-tracker-provider-v1", min_length=2, max_length=160)
    pitch_length_m: float = Field(default=105.0, ge=80, le=130)
    pitch_width_m: float = Field(default=68.0, ge=45, le=90)
    replace_existing: bool = True
    frames: list[PerformanceMatchTrackingProviderFrame] = Field(min_length=1, max_length=2000)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
    quality_warnings: list[str] = Field(default_factory=list, max_length=20)


class PerformanceMatchTrackingProviderWebhookCreate(BaseModel):
    organization_id: UUID
    video_asset_id: UUID
    external_event_id: str = Field(min_length=2, max_length=180)
    calibration_id: UUID | None = None
    source_provider: str = Field(default="external_tracking_provider", min_length=2, max_length=80)
    model_policy: str = Field(default="external-tracker-provider-v1", min_length=2, max_length=160)
    pitch_length_m: float = Field(default=105.0, ge=80, le=130)
    pitch_width_m: float = Field(default=68.0, ge=45, le=90)
    replace_existing: bool = True
    frames: list[PerformanceMatchTrackingProviderFrame] = Field(min_length=1, max_length=2000)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
    quality_warnings: list[str] = Field(default_factory=list, max_length=20)


class PerformanceMatchTrackingSampleRead(BaseModel):
    id: UUID
    organization_id: UUID
    tracking_run_id: UUID
    video_asset_id: UUID
    track_id: str
    person_id: UUID | None
    team_label: str | None
    player_label: str | None
    jersey_number: str | None
    frame_index: int | None
    timestamp_seconds: float
    x_percent: float
    y_percent: float
    x_meters: float
    y_meters: float
    speed_mps: float | None
    confidence: float | None
    source: str


class PerformanceMatchTrackingPlayerMetricRead(BaseModel):
    track_id: str
    player_label: str | None
    team_label: str | None
    jersey_number: str | None
    sample_count: int
    duration_seconds: float
    distance_m: float
    average_speed_mps: float
    average_x_percent: float | None = None
    average_y_percent: float | None = None
    max_speed_mps: float
    work_rate_m_per_min: float = 0.0
    high_speed_distance_m: float
    sprint_count: int
    explosive_effort_count: int = 0
    recovery_ratio: float = 0.0
    load_band: str = "unknown"
    fatigue_risk_score: float = 0.0
    substitution_window: str | None = None
    recovery_recommendation: str | None = None
    inferred_role: str = "unknown"
    role_confidence_score: float = 0.0
    role_evidence: list[str] = Field(default_factory=list)
    role_recommendation: str | None = None
    pressure_applied_count: int = 0
    pressure_received_count: int = 0
    average_nearest_opponent_m: float | None = None
    off_ball_run_count: int = 0
    territorial_advance_count: int = 0
    pass_completed_count: int = 0
    pass_received_count: int = 0
    pass_attempt_count: int = 0
    pass_accuracy_percent: float = 0.0
    turnover_involved_count: int = 0
    interception_count: int = 0
    tackle_count: int = 0
    ball_carry_m: float = 0.0
    ball_possession_sample_count: int = 0
    shot_count: int = 0
    shot_on_target_count: int = 0
    expected_goals: float = 0.0
    key_pass_count: int = 0
    expected_assists: float = 0.0
    tracking_quality_score: float = 0.0
    coaching_flags: list[str] = Field(default_factory=list)
    dominant_zone: str
    heatmap: dict[str, int]


class PerformanceMatchTrackingRunRead(BaseModel):
    id: UUID
    organization_id: UUID
    video_asset_id: UUID
    calibration_id: UUID | None
    team_id: UUID | None
    event_id: UUID | None
    created_by_person_id: UUID | None
    source_provider: str
    model_policy: str
    status: str
    pitch_length_m: float
    pitch_width_m: float
    sample_count: int
    player_count: int
    total_distance_m: float
    max_speed_mps: float
    high_speed_distance_m: float
    sprint_count: int
    tracking_quality_score: float = 0.0
    identity_continuity_score: float = 0.0
    calibration_quality_score: float = 0.0
    readiness_level: str = "unknown"
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
    processing_metadata: dict[str, Any] = Field(default_factory=dict)
    quality_warnings: list[str] = Field(default_factory=list)
    coaching_guidance: list[str] = Field(default_factory=list)
    tactical_guidance: list[str] = Field(default_factory=list)
    team_shape_metrics: list[dict[str, Any]] = Field(default_factory=list)
    team_phase_metrics: list[dict[str, Any]] = Field(default_factory=list)
    pressure_events: list[dict[str, Any]] = Field(default_factory=list)
    match_phase_snapshots: list[dict[str, Any]] = Field(default_factory=list)
    ball_tracking_metrics: dict[str, Any] = Field(default_factory=dict)
    possession_estimates: list[dict[str, Any]] = Field(default_factory=list)
    ball_action_events: list[dict[str, Any]] = Field(default_factory=list)
    recognized_action_events: list[dict[str, Any]] = Field(default_factory=list)
    action_recognition_metrics: dict[str, Any] = Field(default_factory=dict)
    shot_events: list[dict[str, Any]] = Field(default_factory=list)
    pass_network: list[dict[str, Any]] = Field(default_factory=list)
    pass_type_metrics: list[dict[str, Any]] = Field(default_factory=list)
    defensive_action_events: list[dict[str, Any]] = Field(default_factory=list)
    chance_creation_metrics: dict[str, Any] = Field(default_factory=dict)
    set_piece_events: list[dict[str, Any]] = Field(default_factory=list)
    set_piece_metrics: dict[str, Any] = Field(default_factory=dict)
    training_prescriptions: list[dict[str, Any]] = Field(default_factory=list)
    formation_snapshots: list[dict[str, Any]] = Field(default_factory=list)
    tactical_role_metrics: list[dict[str, Any]] = Field(default_factory=list)
    player_metrics: list[PerformanceMatchTrackingPlayerMetricRead]
    samples: list[PerformanceMatchTrackingSampleRead]
    calibration: PerformanceMatchPitchCalibrationRead | None = None
    started_at: datetime
    completed_at: datetime | None


class PerformanceMatchTrackingProviderWebhookRead(BaseModel):
    ingest_event_id: UUID
    organization_id: UUID
    video_asset_id: UUID
    tracking_run_id: UUID | None
    source_provider: str
    external_event_id: str
    replayed: bool
    reprocessed: bool = False
    signature_required: bool
    signature_validated: bool
    sample_count: int
    player_count: int
    payload_hash: str
    received_at: datetime
    tracking_run: PerformanceMatchTrackingRunRead | None = None


class PerformanceMatchTrackingProviderIngestEventRead(BaseModel):
    id: UUID
    organization_id: UUID
    video_asset_id: UUID
    tracking_run_id: UUID | None
    team_id: UUID | None
    event_id: UUID | None
    source_provider: str
    external_event_id: str
    payload_hash: str
    received_at: datetime
    signature_required: bool
    signature_validated: bool
    sample_count: int
    player_count: int
    status: str
    payload_available: bool = False
    frame_count: int = 0
    created_at: datetime


class PerformanceMatchTrackingProviderIngestReprocessCreate(BaseModel):
    calibration_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=1000)


class PerformanceMultiCameraVideoCreate(BaseModel):
    video_asset_id: UUID
    tracking_run_id: UUID | None = None
    camera_label: str = Field(min_length=2, max_length=120)
    camera_role: str = Field(
        default="primary",
        pattern="^(primary|tactical|goal|sideline|endline|drone|provider)$",
    )
    sync_offset_seconds: float = Field(default=0.0, ge=-900, le=900)
    angle_confidence: float = Field(default=0.75, ge=0, le=1)


class PerformanceMultiCameraAnalysisCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    event_id: UUID | None = None
    competition_id: UUID | None = None
    analysis_label: str = Field(default="Multi-camera match review", min_length=2, max_length=180)
    sport: str = Field(default="football", min_length=2, max_length=80)
    synchronization_policy: str = Field(default="timestamp_offset", min_length=2, max_length=80)
    camera_videos: list[PerformanceMultiCameraVideoCreate] = Field(min_length=2, max_length=12)


class PerformanceMultiCameraAnalysisRead(BaseModel):
    id: UUID
    organization_id: UUID
    team_id: UUID | None
    event_id: UUID | None
    competition_id: UUID | None
    primary_video_asset_id: UUID
    created_by_person_id: UUID | None
    analysis_label: str
    sport: str
    synchronization_policy: str
    status: str
    camera_count: int
    tracking_run_count: int
    fused_player_count: int
    fused_sample_count: int
    confidence: float
    camera_package: list[dict[str, Any]]
    fused_summary: dict[str, Any]
    recommendations: list[str]
    model_policy: str
    analyzed_at: datetime
    created_at: datetime


class PerformanceMatchTrackingIdentityReviewCreate(BaseModel):
    track_id: str = Field(min_length=1, max_length=120)
    person_id: UUID | None = None
    team_label: str | None = Field(default=None, max_length=120)
    player_label: str | None = Field(default=None, max_length=180)
    jersey_number: str | None = Field(default=None, max_length=20)
    decision: str = Field(default="confirmed", min_length=2, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)


class PerformanceMatchTrackingIdentityReviewRead(BaseModel):
    id: UUID
    organization_id: UUID
    tracking_run_id: UUID
    video_asset_id: UUID
    track_id: str
    reviewer_person_id: UUID | None
    person_id: UUID | None
    team_label: str | None
    player_label: str | None
    jersey_number: str | None
    decision: str
    sample_count: int
    before: dict[str, Any]
    after: dict[str, Any]
    notes: str | None
    reviewed_at: datetime
    created_at: datetime


class PerformanceMatchTrackingIdentityReviewResultRead(BaseModel):
    review: PerformanceMatchTrackingIdentityReviewRead
    tracking_run: PerformanceMatchTrackingRunRead


class PerformanceMatchAnalysisReportCreate(BaseModel):
    organization_id: UUID
    audience: str = Field(default="coach", min_length=2, max_length=80)
    report_scope: str = Field(default="team_match_review", min_length=2, max_length=80)
    title: str | None = Field(default=None, max_length=220)
    include_player_cards: bool = True
    include_tactical_shape: bool = True
    notes: str | None = Field(default=None, max_length=2000)


class PerformanceMatchAnalysisReportRead(BaseModel):
    id: UUID
    organization_id: UUID
    tracking_run_id: UUID
    video_asset_id: UUID
    created_by_person_id: UUID | None
    title: str
    audience: str
    report_scope: str
    status: str
    model_policy: str
    summary: dict[str, Any]
    player_cards: list[dict[str, Any]]
    team_shape: list[dict[str, Any]]
    recommendations: list[str]
    artifact_format: str
    content_type: str
    storage_url: str
    checksum: str
    size_bytes: int
    generated_at: datetime
    created_at: datetime


class PerformanceMatchPlayerGuidanceReviewRead(BaseModel):
    tracking_run_id: UUID
    organization_id: UUID
    video_asset_id: UUID
    publishable: bool
    guidance_status: str
    readiness_level: str
    tracking_quality_score: float
    identity_continuity_score: float
    calibration_quality_score: float
    sample_count: int
    player_count: int
    reviewed_identity_count: int
    unreviewed_track_count: int
    player_card_count: int
    required_actions: list[str]
    review_notes: list[str]
    coach_guidance: list[str]
    player_guidance: list[dict[str, Any]]
    player_cards: list[dict[str, Any]]
    quality_warnings: list[str]
    generated_at: datetime


class PerformanceMatchPlayerGuidancePublishCreate(BaseModel):
    organization_id: UUID
    channel: CommunicationChannel = CommunicationChannel.IN_APP
    include_guardians: bool = True
    require_publishable: bool = True
    subject_prefix: str = Field(default="Match video guidance", min_length=2, max_length=120)
    message_intro: str | None = Field(default=None, max_length=1000)


class PerformanceMatchPlayerGuidancePublishMessageRead(BaseModel):
    message_id: UUID
    player_person_id: UUID
    recipient_person_ids: list[UUID]
    track_id: str
    player_label: str
    subject: str
    channel: CommunicationChannel


class PerformanceMatchPlayerGuidancePublishAuditRead(BaseModel):
    id: UUID
    organization_id: UUID
    tracking_run_id: UUID
    video_asset_id: UUID
    message_id: UUID
    player_person_id: UUID
    track_id: str
    player_label: str
    channel: CommunicationChannel
    recipient_count: int
    queued_count: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    read_count: int = 0
    failed_count: int = 0
    suppressed_count: int = 0
    published_by_person_id: UUID | None
    status: str
    published_at: datetime
    created_at: datetime


class PerformanceMatchPlayerGuidancePublishRead(BaseModel):
    tracking_run_id: UUID
    organization_id: UUID
    video_asset_id: UUID
    publishable: bool
    guidance_status: str
    message_count: int
    recipient_count: int
    player_count: int
    skipped_track_count: int
    skipped_tracks: list[str]
    required_actions: list[str]
    messages: list[PerformanceMatchPlayerGuidancePublishMessageRead]
    audits: list[PerformanceMatchPlayerGuidancePublishAuditRead] = Field(default_factory=list)
    published_at: datetime


class PerformanceMatchMomentDetectionCreate(BaseModel):
    organization_id: UUID
    min_score: float = Field(default=55.0, ge=0, le=100)
    max_moments: int = Field(default=20, ge=1, le=100)
    audience: str = Field(default="coach", min_length=2, max_length=80)
    replace_existing: bool = True


class PerformanceMatchMomentReviewCreate(BaseModel):
    organization_id: UUID
    status: str = Field(pattern="^(detected|needs_review|approved|featured|rejected)$")
    review_notes: str | None = Field(default=None, max_length=2000)


class PerformanceMatchMomentRead(BaseModel):
    id: UUID
    organization_id: UUID
    tracking_run_id: UUID
    video_asset_id: UUID
    created_by_person_id: UUID | None
    action_type: str
    moment_category: str
    title: str
    start_seconds: float
    end_seconds: float
    duration_seconds: float
    moment_score: float
    technical_quality: float
    tactical_importance: float
    emotional_impact: float
    rarity_difficulty: float
    game_context: float
    confidence: float
    primary_track_id: str | None
    secondary_track_id: str | None
    team_label: str | None
    player_label: str | None
    jersey_number: str | None
    zone: str | None
    evidence: str
    coaching_note: str
    tags: list[str]
    source_event: dict[str, Any]
    status: str
    model_policy: str
    detected_at: datetime
    created_at: datetime


class PerformanceHardwareKitCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    kit_type: str = Field(default="hybrid", min_length=2, max_length=80)
    provider: str = Field(default="afrolete", min_length=2, max_length=80)
    sport: str = Field(default="football", min_length=2, max_length=80)
    level: str = Field(default="club", min_length=2, max_length=80)
    recommended_camera_count: int = Field(default=1, ge=0, le=24)
    recommended_gps_unit_count: int = Field(default=0, ge=0, le=200)
    supported_metrics: list[str] = Field(
        default_factory=lambda: ["speed", "distance", "acceleration", "heatmap"],
        max_length=40,
    )
    setup_steps: list[str] = Field(default_factory=list, max_length=30)
    estimated_cost: float | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=10)
    status: str = Field(default="planned", min_length=2, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)


class PerformanceHardwareKitRead(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    kit_type: str
    provider: str
    sport: str
    level: str
    recommended_camera_count: int
    recommended_gps_unit_count: int
    supported_metrics: list[str]
    setup_steps: list[str]
    estimated_cost: float | None
    currency: str
    status: str
    notes: str | None
    created_at: datetime


class PerformanceHardwareDeviceCreate(BaseModel):
    organization_id: UUID
    kit_id: UUID | None = None
    team_id: UUID | None = None
    facility_id: UUID | None = None
    device_type: str = Field(default="camera", min_length=2, max_length=80)
    provider: str = Field(default="veo", min_length=2, max_length=80)
    device_label: str = Field(min_length=2, max_length=180)
    external_device_id: str = Field(min_length=2, max_length=180)
    firmware_version: str | None = Field(default=None, max_length=80)
    status: str = Field(default="provisioned", min_length=2, max_length=40)
    api_key: str | None = Field(default=None, max_length=500)
    api_key_secret_path: str | None = Field(default=None, max_length=500)
    custody_mode: str = Field(default="openbao_reference", min_length=2, max_length=40)
    metrics_supported: list[str] = Field(default_factory=list, max_length=40)
    calibration_id: UUID | None = None
    battery_percent: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=2000)


class PerformanceHardwareDeviceRead(BaseModel):
    id: UUID
    organization_id: UUID
    kit_id: UUID | None
    team_id: UUID | None
    facility_id: UUID | None
    device_type: str
    provider: str
    device_label: str
    external_device_id: str
    firmware_version: str | None
    status: str
    api_key_configured: bool
    api_key_secret_path: str | None
    custody_mode: str
    metrics_supported: list[str]
    calibration_id: UUID | None
    last_seen_at: datetime | None
    battery_percent: int | None
    notes: str | None
    created_at: datetime


class PerformanceHardwareSyncRunCreate(BaseModel):
    video_asset_id: UUID | None = None
    calibration_id: UUID | None = None
    sync_mode: str = Field(default="sample_payload", min_length=2, max_length=80)
    external_event_id: str | None = Field(default=None, max_length=180)
    metrics: dict[str, float] = Field(default_factory=dict)
    tracking_samples: list[PerformanceMatchTrackingSampleCreate] = Field(default_factory=list, max_length=5000)
    replace_existing_tracking: bool = False
    battery_percent: int | None = Field(default=None, ge=0, le=100)
    payload: dict[str, Any] | None = None


class PerformanceHardwareSyncRunRead(BaseModel):
    id: UUID
    organization_id: UUID
    device_id: UUID
    video_asset_id: UUID | None
    tracking_run_id: UUID | None
    provider: str
    sync_mode: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    metrics_ingested: int
    sample_count: int
    payload_hash: str | None
    message: str | None
    tracking_run: PerformanceMatchTrackingRunRead | None = None


class PerformanceHighlightReelCreate(BaseModel):
    organization_id: UUID
    tracking_run_id: UUID | None = None
    athlete_profile_id: UUID | None = None
    audience: str = Field(default="coach", min_length=2, max_length=80)
    purpose: str = Field(default="match_review", min_length=2, max_length=120)
    title: str | None = Field(default=None, max_length=180)
    target_duration_seconds: float = Field(default=90, ge=15, le=600)
    channels: list[str] = Field(default_factory=lambda: ["coach_review"], max_length=12)
    branding: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list, max_length=30)


class PerformanceHighlightClipRead(BaseModel):
    title: str
    start_seconds: float
    end_seconds: float
    duration_seconds: float
    category: str
    player_label: str | None = None
    team_label: str | None = None
    jersey_number: str | None = None
    confidence: float
    evidence: str
    coaching_note: str
    tags: list[str] = Field(default_factory=list)
    source_moment_id: UUID | None = None
    moment_score: float | None = None
    moment_category: str | None = None
    source_policy: str | None = None
    source_moment_status: str | None = None
    source_event: dict[str, Any] = Field(default_factory=dict)


class PerformanceHighlightReelRead(BaseModel):
    id: UUID
    organization_id: UUID
    video_asset_id: UUID
    tracking_run_id: UUID | None
    athlete_profile_id: UUID | None
    created_by_person_id: UUID | None
    title: str
    audience: str
    purpose: str
    model_policy: str
    status: str
    clip_count: int
    duration_seconds: float
    clips: list[PerformanceHighlightClipRead]
    tags: list[str]
    distribution: dict[str, Any]
    branding: dict[str, Any] | None = None
    generated_at: datetime
    created_at: datetime


class PerformanceHighlightReelExportCreate(BaseModel):
    organization_id: UUID
    export_format: str = Field(default="timeline_json", min_length=2, max_length=80)
    delivery_channel: str = Field(default="coach_review", min_length=2, max_length=80)
    include_branding: bool = True
    notes: str | None = Field(default=None, max_length=1000)


class PerformanceHighlightReelExportRead(BaseModel):
    id: UUID
    organization_id: UUID
    highlight_reel_id: UUID
    video_asset_id: UUID
    tracking_run_id: UUID | None
    requested_by_person_id: UUID | None
    export_format: str
    status: str
    renderer_policy: str
    filename: str
    content_type: str
    storage_url: str
    checksum: str
    size_bytes: int
    message: str | None
    manifest: dict[str, Any]
    generated_at: datetime
    created_at: datetime


class PerformanceHighlightReelShareCreate(BaseModel):
    organization_id: UUID
    channel: CommunicationChannel = CommunicationChannel.IN_APP
    include_players: bool = True
    include_guardians: bool = True
    recipient_person_ids: list[UUID] = Field(default_factory=list, max_length=100)
    subject_prefix: str = Field(default="Highlight reel ready", min_length=2, max_length=120)
    message_intro: str | None = Field(default=None, max_length=1000)
    delivery_channel: str = Field(default="coach_review", min_length=2, max_length=80)
    export_format: str = Field(default="timeline_json", min_length=2, max_length=80)
    include_branding: bool = True
    notes: str | None = Field(default=None, max_length=1000)


class PerformanceHighlightReelShareAuditRead(BaseModel):
    id: UUID
    organization_id: UUID
    highlight_reel_id: UUID
    highlight_reel_export_id: UUID | None
    video_asset_id: UUID
    tracking_run_id: UUID | None
    message_id: UUID
    channel: CommunicationChannel
    audience: str
    share_policy: str
    recipient_count: int
    player_recipient_count: int
    guardian_recipient_count: int
    explicit_recipient_count: int
    queued_count: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    read_count: int = 0
    failed_count: int = 0
    suppressed_count: int = 0
    published_by_person_id: UUID | None
    status: str
    published_at: datetime
    created_at: datetime


class PerformanceHighlightReelShareRead(BaseModel):
    highlight_reel_id: UUID
    organization_id: UUID
    video_asset_id: UUID
    highlight_reel_export_id: UUID | None
    message_id: UUID
    channel: CommunicationChannel
    share_policy: str
    recipient_count: int
    player_recipient_count: int
    guardian_recipient_count: int
    explicit_recipient_count: int
    subject: str
    audit: PerformanceHighlightReelShareAuditRead
    published_at: datetime


class PerformanceSharedHighlightReelFeedbackCreate(BaseModel):
    organization_id: UUID
    status: str = Field(default="acknowledged", pattern="^(acknowledged|needs_help|inspired|confused|completed)$")
    rating: int | None = Field(default=None, ge=1, le=5)
    response_text: str | None = Field(default=None, max_length=2000)
    priority_focus: str | None = Field(default=None, max_length=120)
    requested_follow_up: bool = False
    clip_time_seconds: float | None = Field(default=None, ge=0, le=86400)


class PerformanceSharedHighlightReelFeedbackRead(BaseModel):
    id: UUID
    organization_id: UUID
    highlight_reel_id: UUID
    highlight_reel_export_id: UUID | None
    share_audit_id: UUID
    message_id: UUID
    message_recipient_id: UUID
    person_id: UUID
    status: str
    rating: int | None
    response_text: str | None
    priority_focus: str | None
    requested_follow_up: bool
    clip_time_seconds: float | None
    agent_task_id: UUID | None = None
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime


class PerformanceSharedHighlightReelRead(BaseModel):
    organization_id: UUID
    highlight_reel_id: UUID
    highlight_reel_export_id: UUID | None
    video_asset_id: UUID
    tracking_run_id: UUID | None
    message_id: UUID
    recipient_id: UUID
    title: str
    message_subject: str
    message_body_preview: str | None = None
    audience: str
    purpose: str
    model_policy: str
    share_policy: str
    clip_count: int
    duration_seconds: float
    clips: list[PerformanceHighlightClipRead]
    tags: list[str]
    distribution: dict[str, Any]
    export_format: str | None
    export_filename: str | None
    export_content_type: str | None
    export_checksum: str | None
    download_path: str | None
    channel: CommunicationChannel
    delivery_status: MessageDeliveryStatus
    delivered_at: datetime | None
    read_at: datetime | None
    feedback: PerformanceSharedHighlightReelFeedbackRead | None = None
    published_at: datetime
    created_at: datetime


class PerformanceHighlightReelRecipientEngagementRead(BaseModel):
    recipient_id: UUID
    person_id: UUID
    person_name: str
    destination: str | None
    delivery_status: MessageDeliveryStatus
    delivered_at: datetime | None
    read_at: datetime | None
    download_count: int = 0
    last_downloaded_at: datetime | None = None
    feedback_status: str | None = None
    feedback_rating: int | None = None
    feedback_requested_follow_up: bool = False
    feedback_priority_focus: str | None = None
    feedback_response_preview: str | None = None
    feedback_submitted_at: datetime | None = None
    feedback_agent_task_id: UUID | None = None


class PerformanceHighlightReelEngagementRead(BaseModel):
    share_audit_id: UUID
    organization_id: UUID
    highlight_reel_id: UUID
    highlight_reel_export_id: UUID | None
    message_id: UUID
    title: str
    audience: str
    share_policy: str
    channel: CommunicationChannel
    recipient_count: int
    queued_count: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    read_count: int = 0
    failed_count: int = 0
    suppressed_count: int = 0
    read_rate_percent: float = 0.0
    download_count: int = 0
    unique_download_count: int = 0
    download_rate_percent: float = 0.0
    feedback_count: int = 0
    follow_up_request_count: int = 0
    average_feedback_rating: float | None = None
    last_engagement_at: datetime | None = None
    recipients: list[PerformanceHighlightReelRecipientEngagementRead]
    published_at: datetime


class PerformanceHighlightReelReminderCreate(BaseModel):
    organization_id: UUID
    channel: CommunicationChannel = CommunicationChannel.IN_APP
    subject_prefix: str = Field(default="Reminder: highlight reel ready", min_length=2, max_length=120)
    message_intro: str | None = Field(default=None, max_length=1000)
    include_download_link: bool = True


class PerformanceHighlightReelReminderRecipientRead(BaseModel):
    recipient_id: UUID
    person_id: UUID
    person_name: str
    delivery_status: MessageDeliveryStatus
    download_count: int = 0


class PerformanceHighlightReelReminderRead(BaseModel):
    share_audit_id: UUID
    organization_id: UUID
    highlight_reel_id: UUID
    highlight_reel_export_id: UUID | None
    original_message_id: UUID
    message_id: UUID | None
    channel: CommunicationChannel
    recipient_count: int
    skipped_read_count: int = 0
    skipped_downloaded_count: int = 0
    subject: str | None
    recipients: list[PerformanceHighlightReelReminderRecipientRead]
    created_at: datetime


class PerformanceHighlightReelReminderRunCreate(BaseModel):
    organization_id: UUID
    channel: CommunicationChannel = CommunicationChannel.IN_APP
    shared_before_hours: int = Field(default=24, ge=0, le=8760)
    repeat_after_hours: int = Field(default=24, ge=0, le=8760)
    limit: int = Field(default=50, ge=1, le=500)
    dry_run: bool = False
    subject_prefix: str = Field(default="Reminder: highlight reel ready", min_length=2, max_length=120)
    message_intro: str | None = Field(default=None, max_length=1000)
    include_download_link: bool = True


class PerformanceHighlightReelReminderRunRead(BaseModel):
    organization_id: UUID | None
    eligible_count: int
    reminded_count: int
    skipped_count: int
    failed_count: int
    dry_run: bool
    stale_before: datetime
    repeat_after_hours: int
    recipient_count: int
    suppressed_recent_count: int = 0
    no_unread_count: int = 0
    message_ids: list[UUID]
    share_audit_ids: list[UUID]


class PerformanceModelExtractionBenchmarkCaseCreate(BaseModel):
    case_id: str = Field(min_length=2, max_length=120)
    metric_code: str = Field(min_length=2, max_length=80)
    metric_name: str = Field(min_length=2, max_length=180)
    category: MetricCategory = MetricCategory.WELLNESS
    unit: str | None = Field(default=None, max_length=40)
    min_value: float | None = None
    max_value: float | None = None
    source: MetricSource = MetricSource.AUDIO_NARRATION
    source_provider: str | None = Field(default=None, max_length=80)
    evidence_ref: str = Field(default="benchmark://performance/model-extraction", max_length=500)
    evidence_text: str = Field(min_length=2, max_length=8000)
    expected_value: float
    tolerance: float = Field(default=0.01, ge=0)


class PerformanceModelExtractionBenchmarkRunCreate(BaseModel):
    organization_id: UUID
    dataset_id: UUID | None = None
    cases: list[PerformanceModelExtractionBenchmarkCaseCreate] = Field(default_factory=list, max_length=50)


class PerformanceModelExtractionBenchmarkDatasetCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    slug: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    model_policy: str | None = Field(default=None, max_length=180)
    cases: list[PerformanceModelExtractionBenchmarkCaseCreate] = Field(default_factory=list, min_length=1, max_length=200)


class PerformanceModelExtractionBenchmarkDatasetCaseRead(BaseModel):
    id: UUID
    dataset_id: UUID
    case_id: str
    metric_code: str
    metric_name: str
    category: MetricCategory
    unit: str | None
    source: MetricSource
    source_provider: str | None
    evidence_ref: str
    expected_value: float
    tolerance: float
    status: str


class PerformanceModelExtractionBenchmarkDatasetRead(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: str | None
    model_policy: str | None
    status: str
    case_count: int
    last_run_at: datetime | None
    last_accuracy: float | None
    last_mean_absolute_error: float | None
    cases: list[PerformanceModelExtractionBenchmarkDatasetCaseRead]


class PerformanceModelExtractionBenchmarkCaseRead(BaseModel):
    case_id: str
    metric_code: str
    source: MetricSource
    expected_value: float
    extracted_value: float
    absolute_error: float
    tolerance: float
    passed: bool
    parser_method: str
    model_assisted: bool
    model_policy: str | None
    confidence: float
    summary: str


class PerformanceModelExtractionBenchmarkRunRead(BaseModel):
    organization_id: UUID
    model_policy: str
    case_count: int
    passed_count: int
    failed_count: int
    accuracy: float
    mean_absolute_error: float
    cases: list[PerformanceModelExtractionBenchmarkCaseRead]


class PerformanceForecastValidationRunCreate(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID | None = None


class PerformanceForecastValidationMetricRead(BaseModel):
    athlete_profile_id: UUID
    metric_definition_id: UUID
    metric_code: str
    metric_name: str
    sample_size: int
    predicted_value: float | None
    actual_value: float
    absolute_error: float | None
    relative_error: float | None
    tolerance: float
    passed: bool
    drifted: bool


class PerformanceForecastValidationRunRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID | None
    model_policy: str
    forecast_mode: str
    metric_count: int
    evaluated_count: int
    passed_count: int
    drift_count: int
    mean_absolute_error: float
    mean_relative_error: float
    max_absolute_error: float
    drift_level: str
    recommendation: str
    details: list[PerformanceForecastValidationMetricRead]
    created_at: datetime


class PerformanceForecastValidationAlertRead(BaseModel):
    organization_id: UUID
    validation_run_id: UUID
    drift_level: str
    sent: bool
    dry_run: bool = False
    channels: list[CommunicationChannel]
    channel_count: int
    recipient_count: int
    message_ids: list[UUID]
    skipped_reason: str | None
    validation_run: PerformanceForecastValidationRunRead


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
    filter_category: MetricCategory | None
    filter_metric_code: str | None
    period_start: date | None
    period_end: date | None
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
    filter_category: MetricCategory | None
    filter_metric_code: str | None
    period_start: date | None
    period_end: date | None
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


class AthletePathwayProjectionCreate(BaseModel):
    organization_id: UUID
    sport: str = Field(default="football", min_length=2, max_length=80)
    primary_position: str | None = Field(default=None, max_length=80)
    academic_gpa: float | None = Field(default=None, ge=0, le=5)
    graduation_year: int | None = Field(default=None, ge=2020, le=2100)
    target_pathway: str = Field(default="balanced", min_length=2, max_length=80)
    preferred_regions: list[str] = Field(default_factory=list, max_length=12)
    recruiting_profile_url: str | None = Field(default=None, max_length=800)
    notes: str | None = Field(default=None, max_length=4000)
    share_with_guardians: bool = False


class AthletePathwayOptionRead(BaseModel):
    pathway: str
    score: float
    readiness: str
    timeline: str
    rationale: str
    next_actions: list[str]


class AthletePathwayMilestoneRead(BaseModel):
    title: str
    due_label: str
    priority: str
    owner: str
    status: str
    evidence: str


class AthletePathwayProjectionRead(BaseModel):
    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    athlete_name: str
    created_by_person_id: UUID | None
    sport: str
    primary_position: str | None
    age_years: int | None
    academic_gpa: float | None
    graduation_year: int | None
    target_pathway: str
    model_policy: str
    confidence: float
    readiness_score: int
    projected_level: str
    college_fit_score: float
    semi_pro_fit_score: float
    professional_fit_score: float
    scholarship_fit_score: float
    summary: str
    pathway_options: list[AthletePathwayOptionRead]
    milestones: list[AthletePathwayMilestoneRead]
    scout_actions: list[str]
    evidence: dict[str, object]
    risk_flags: list[str]
    status: str
    generated_at: datetime
    created_at: datetime


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
    biomechanical_observation_count: int
    biomechanical_risk_count: int
    latest_movement_quality_score: float | None
    latest_asymmetry_score: float | None
    video_risk_labels: list[str]
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


class PerformanceForecastValidationWorkerRunRead(BaseModel):
    organization_id: UUID | None
    auto_alerts: bool = False
    dry_run_alerts: bool = False
    alert_repeat_after_hours: int = 24
    alert_channels: list[CommunicationChannel] = Field(default_factory=lambda: [CommunicationChannel.IN_APP])
    alert_channel_count: int = 1
    eligible_count: int
    executed_count: int
    skipped_count: int
    failed_count: int
    run_ids: list[UUID]
    metric_count: int
    evaluated_count: int
    drift_count: int
    watch_count: int
    high_count: int
    alerted_count: int = 0
    alert_skipped_count: int = 0
    alert_failed_count: int = 0
    alert_message_ids: list[UUID] = Field(default_factory=list)
    alert_skipped_reasons: dict[str, int] = Field(default_factory=dict)


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


class PlayerMatchActionPlanRead(BaseModel):
    priority: str
    focus: str
    cue: str
    drill_recommendation: str
    evidence: str
    clip_start_seconds: float | None = None
    clip_end_seconds: float | None = None
    clip_label: str | None = None


class PlayerMatchTrainingFollowupCreate(BaseModel):
    organization_id: UUID
    tracking_run_id: UUID
    track_id: str = Field(min_length=1, max_length=120)
    period_start: date
    period_end: date
    max_items: int = Field(default=3, ge=1, le=6)
    selected_priorities: list[str] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def valid_period(self) -> "PlayerMatchTrainingFollowupCreate":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class PlayerMatchTrainingFollowupRead(BaseModel):
    organization_id: UUID
    athlete_profile_id: UUID
    tracking_run_id: UUID
    track_id: str
    plan_id: UUID
    item_ids: list[UUID]
    title: str
    focus_area: str
    period_start: date
    period_end: date
    item_count: int
    action_plan: list[PlayerMatchActionPlanRead]
    agent_task_id: UUID | None = None
    agent_task_status: str | None = None
    agent_task_title: str | None = None


class PerformanceMatchTrainingFollowupCreate(BaseModel):
    organization_id: UUID
    period_start: date
    period_end: date
    max_items: int = Field(default=5, ge=1, le=8)
    selected_focus_areas: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def valid_period(self) -> "PerformanceMatchTrainingFollowupCreate":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class PerformanceMatchTrainingFollowupRead(BaseModel):
    organization_id: UUID
    tracking_run_id: UUID
    video_asset_id: UUID
    team_id: UUID | None = None
    plan_id: UUID
    item_ids: list[UUID]
    session_plan_ids: list[UUID] = Field(default_factory=list)
    title: str
    focus_area: str
    period_start: date
    period_end: date
    item_count: int
    training_prescriptions: list[dict[str, Any]]
    reused_existing: bool = False
    agent_task_id: UUID | None = None
    agent_task_status: str | None = None
    agent_task_title: str | None = None


class PlayerMatchGuidanceRead(BaseModel):
    tracking_run_id: UUID
    video_asset_id: UUID
    guidance_message_id: UUID
    guidance_recipient_id: UUID | None = None
    guidance_published_at: datetime
    guidance_delivery_status: str
    guidance_recipient_count: int
    opponent_name: str
    match_label: str | None
    tracked_at: datetime
    track_id: str
    team_label: str | None
    player_label: str | None
    jersey_number: str | None
    readiness_level: str
    tracking_quality_score: float
    distance_m: float
    high_speed_distance_m: float
    max_speed_mps: float
    sprint_count: int
    work_rate_m_per_min: float
    dominant_zone: str
    pressure_applied_count: int = 0
    off_ball_run_count: int = 0
    pass_accuracy_percent: float = 0.0
    shot_count: int = 0
    expected_goals: float = 0.0
    coaching_flags: list[str] = Field(default_factory=list)
    player_guidance: list[str] = Field(default_factory=list)
    action_plan: list[PlayerMatchActionPlanRead] = Field(default_factory=list)
    tactical_context: list[str] = Field(default_factory=list)
    quality_warnings: list[str] = Field(default_factory=list)


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
    what_if_scenarios: list[PerformanceForecastWhatIfRead]
    injury_risk: PerformanceInjuryRiskRead
    benchmarks: list[PerformanceMetricBenchmarkRead]
    cohort_comparisons: list[PerformanceCohortComparisonRead]
    match_guidance: list[PlayerMatchGuidanceRead] = Field(default_factory=list)
