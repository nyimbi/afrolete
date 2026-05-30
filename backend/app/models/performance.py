from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import CommunicationChannel, MetricCategory, MetricSource, MetricVerificationStatus


class PerformanceMetricDefinition(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_metric_definitions"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "sport",
            "code",
            name="uq_performance_metric_definitions_org_sport_code",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    sport: Mapped[str | None] = mapped_column(String(80), index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    category: Mapped[MetricCategory] = mapped_column(
        enum_type(MetricCategory), nullable=False, index=True
    )
    unit: Mapped[str | None] = mapped_column(String(40))
    description: Mapped[str | None] = mapped_column(Text)
    min_value: Mapped[float | None] = mapped_column(Float)
    max_value: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    higher_is_better: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)


class AthletePerformanceObservation(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_performance_observations"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    metric_definition_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_metric_definitions.id"), index=True
    )
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    recorded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    value: Mapped[float] = mapped_column(Float, nullable=False)
    raw_value: Mapped[str | None] = mapped_column(String(160))
    observed_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    source: Mapped[MetricSource] = mapped_column(enum_type(MetricSource), nullable=False, index=True)
    confidence: Mapped[float | None] = mapped_column(Float)
    verification_status: Mapped[MetricVerificationStatus] = mapped_column(
        enum_type(MetricVerificationStatus),
        default=MetricVerificationStatus.VERIFIED,
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text)


class PerformanceWearableIngestEvent(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_wearable_ingest_events"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "athlete_profile_id",
            "provider",
            "external_event_id",
            name="uq_performance_wearable_ingest_events_replay",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    external_event_id: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    signature_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    signature_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    observation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_metric_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class PerformanceWearableProviderConnection(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_wearable_provider_connections"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "athlete_profile_id",
            "provider",
            "external_athlete_ref",
            name="uq_performance_wearable_provider_connections_external_ref",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(180), nullable=False)
    external_athlete_ref: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="configured", nullable=False, index=True)
    auth_type: Mapped[str] = mapped_column(String(40), default="oauth2", nullable=False)
    scopes: Mapped[str | None] = mapped_column(Text)
    access_token_secret_path: Mapped[str | None] = mapped_column(String(500))
    refresh_token_secret_path: Mapped[str | None] = mapped_column(String(500))
    webhook_secret_path: Mapped[str | None] = mapped_column(String(500))
    access_token_hash: Mapped[str | None] = mapped_column(String(64))
    refresh_token_hash: Mapped[str | None] = mapped_column(String(64))
    refresh_token_family_id: Mapped[str | None] = mapped_column(String(80), index=True)
    refresh_token_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    token_last_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    token_type: Mapped[str | None] = mapped_column(String(40))
    token_scope: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    oauth_client_id: Mapped[str | None] = mapped_column(String(180), index=True)
    oauth_client_secret_path: Mapped[str | None] = mapped_column(String(500))
    oauth_authorization_url: Mapped[str | None] = mapped_column(String(800))
    oauth_token_url: Mapped[str | None] = mapped_column(String(800))
    oauth_redirect_uri: Mapped[str | None] = mapped_column(String(800))
    oauth_state_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    oauth_state_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    oauth_authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    provider_pull_url: Mapped[str | None] = mapped_column(String(800))
    provider_pull_cursor_param: Mapped[str | None] = mapped_column(String(80))
    provider_pull_since_param: Mapped[str | None] = mapped_column(String(80))
    provider_pull_until_param: Mapped[str | None] = mapped_column(String(80))
    sync_cursor: Mapped[str | None] = mapped_column(String(240))
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    webhook_registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provider_webhook_registration_url: Mapped[str | None] = mapped_column(String(800))
    provider_webhook_callback_url: Mapped[str | None] = mapped_column(String(800))
    provider_webhook_event_types: Mapped[str | None] = mapped_column(Text)
    provider_webhook_registration_status_code: Mapped[int | None] = mapped_column(Integer)
    provider_webhook_registration_hash: Mapped[str | None] = mapped_column(String(64))
    provider_webhook_registered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    provider_webhook_registration_error: Mapped[str | None] = mapped_column(Text)
    default_metric_definition_ids: Mapped[str | None] = mapped_column(Text)


class PerformanceWearableProviderSyncRun(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_wearable_provider_sync_runs"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    connection_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_wearable_provider_connections.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    external_event_id: Mapped[str | None] = mapped_column(String(180), index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    sync_mode: Mapped[str] = mapped_column(String(40), default="pull", nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    observation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_metric_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    replayed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provider_status_code: Mapped[int | None] = mapped_column(Integer)
    provider_response_hash: Mapped[str | None] = mapped_column(String(64))
    provider_page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    provider_rate_limited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provider_retry_after_seconds: Mapped[int | None] = mapped_column(Integer)
    message: Mapped[str | None] = mapped_column(Text)


class PerformanceHardwareKit(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_hardware_kits"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    kit_type: Mapped[str] = mapped_column(String(80), default="hybrid", nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(80), default="afrolete", nullable=False, index=True)
    sport: Mapped[str] = mapped_column(String(80), default="football", nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(80), default="club", nullable=False, index=True)
    recommended_camera_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    recommended_gps_unit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    supported_metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    setup_steps_json: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_cost: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="planned", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class PerformanceHardwareDevice(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_hardware_devices"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "provider",
            "external_device_id",
            name="uq_performance_hardware_devices_external_device",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    kit_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("performance_hardware_kits.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    facility_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("facilities.id"), index=True)
    device_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    device_label: Mapped[str] = mapped_column(String(180), nullable=False)
    external_device_id: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    firmware_version: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default="provisioned", nullable=False, index=True)
    api_key_secret_path: Mapped[str | None] = mapped_column(String(500))
    api_key_hash: Mapped[str | None] = mapped_column(String(64))
    custody_mode: Mapped[str] = mapped_column(String(40), default="openbao_reference", nullable=False, index=True)
    metrics_supported_json: Mapped[str] = mapped_column(Text, nullable=False)
    calibration_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("performance_match_pitch_calibrations.id"), index=True
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    battery_percent: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)


class PerformanceHardwareSyncRun(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_hardware_sync_runs"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    device_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_hardware_devices.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), index=True
    )
    tracking_run_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("performance_match_tracking_runs.id"), index=True
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    sync_mode: Mapped[str] = mapped_column(String(80), default="sample_payload", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    metrics_ingested: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    message: Mapped[str | None] = mapped_column(Text)


class PerformanceVideoAsset(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_video_assets"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "checksum",
            name="uq_performance_video_assets_org_checksum",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    uploaded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    sport: Mapped[str] = mapped_column(String(80), default="athletics", nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(240), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_url: Mapped[str] = mapped_column(String(800), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    video_uri: Mapped[str] = mapped_column(String(900), nullable=False, index=True)
    clip_label: Mapped[str | None] = mapped_column(String(180))
    analysis_focus: Mapped[str | None] = mapped_column(String(1000))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    frame_rate: Mapped[float | None] = mapped_column(Float)
    frame_width: Mapped[int | None] = mapped_column(Integer)
    frame_height: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), default="uploaded", nullable=False, index=True)
    analysis_model_policy: Mapped[str | None] = mapped_column(String(180), index=True)
    pose_analysis_json: Mapped[str | None] = mapped_column(Text)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class PerformanceVideoAnnotation(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_video_annotations"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_video_assets.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    author_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    playback_rate: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    annotation_type: Mapped[str] = mapped_column(String(80), default="coach_note", nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(180), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    body_region: Mapped[str | None] = mapped_column(String(80), index=True)
    x_percent: Mapped[float | None] = mapped_column(Float)
    y_percent: Mapped[float | None] = mapped_column(Float)
    width_percent: Mapped[float | None] = mapped_column(Float)
    height_percent: Mapped[float | None] = mapped_column(Float)
    tags_json: Mapped[str | None] = mapped_column(Text)


class PerformanceVideoPoseSample(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_video_pose_samples"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_video_assets.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    source_provider: Mapped[str] = mapped_column(String(80), default="manual_pose", nullable=False, index=True)
    frame_index: Mapped[int | None] = mapped_column(Integer, index=True)
    timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    phase: Mapped[str | None] = mapped_column(String(80), index=True)
    contact_foot: Mapped[str | None] = mapped_column(String(20), index=True)
    stride_index: Mapped[int | None] = mapped_column(Integer, index=True)
    sample_confidence: Mapped[float | None] = mapped_column(Float)
    keypoints_json: Mapped[str] = mapped_column(Text, nullable=False)


class OppositionScoutingVideoAsset(IdMixin, TimestampMixin, Base):
    __tablename__ = "opposition_scouting_video_assets"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "checksum",
            name="uq_opposition_scouting_video_assets_org_checksum",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    competition_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("competitions.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    uploaded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    opponent_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    sport: Mapped[str] = mapped_column(String(80), default="football", nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(240), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_url: Mapped[str] = mapped_column(String(800), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    video_uri: Mapped[str] = mapped_column(String(900), nullable=False, index=True)
    clip_label: Mapped[str | None] = mapped_column(String(180))
    match_context: Mapped[str | None] = mapped_column(Text)
    analysis_focus: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(40), default="uploaded", nullable=False, index=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class OppositionScoutingReport(IdMixin, TimestampMixin, Base):
    __tablename__ = "opposition_scouting_reports"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    competition_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("competitions.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    opponent_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    sport: Mapped[str] = mapped_column(String(80), default="football", nullable=False, index=True)
    match_context: Mapped[str | None] = mapped_column(Text)
    analysis_focus: Mapped[str | None] = mapped_column(String(1000))
    model_policy: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    formation_detected: Mapped[str | None] = mapped_column(String(80), index=True)
    tactical_summary: Mapped[str] = mapped_column(Text, nullable=False)
    weaknesses_json: Mapped[str] = mapped_column(Text, nullable=False)
    threats_json: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations_json: Mapped[str] = mapped_column(Text, nullable=False)
    set_pieces_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="generated", nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class PerformanceMatchPitchCalibration(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_match_pitch_calibrations"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    calibration_method: Mapped[str] = mapped_column(String(80), default="manual_corner_map", nullable=False, index=True)
    pitch_length_m: Mapped[float] = mapped_column(Float, default=105.0, nullable=False)
    pitch_width_m: Mapped[float] = mapped_column(Float, default=68.0, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    points_json: Mapped[str] = mapped_column(Text, nullable=False)
    transform_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class PerformanceMatchTrackingRun(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_match_tracking_runs"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    calibration_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("performance_match_pitch_calibrations.id"), index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    source_provider: Mapped[str] = mapped_column(String(80), default="manual_tracking", nullable=False, index=True)
    model_policy: Mapped[str] = mapped_column(String(180), default="afrolete-match-tracking-v1", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="completed", nullable=False, index=True)
    pitch_length_m: Mapped[float] = mapped_column(Float, default=105.0, nullable=False)
    pitch_width_m: Mapped[float] = mapped_column(Float, default=68.0, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    player_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_distance_m: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_speed_mps: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    high_speed_distance_m: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sprint_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary_json: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class PerformanceMultiCameraAnalysis(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_multi_camera_analyses"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    competition_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("competitions.id"), index=True)
    primary_video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    analysis_label: Mapped[str] = mapped_column(String(180), nullable=False)
    sport: Mapped[str] = mapped_column(String(80), default="football", nullable=False, index=True)
    synchronization_policy: Mapped[str] = mapped_column(String(80), default="timestamp_offset", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="completed", nullable=False, index=True)
    camera_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tracking_run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fused_player_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fused_sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    camera_package_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    fused_summary_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    recommendations_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    model_policy: Mapped[str] = mapped_column(
        String(180), default="afrolete-multicamera-match-analysis-v1", nullable=False
    )
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class PerformanceMatchTrackingProviderIngestEvent(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_match_tracking_provider_ingest_events"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "video_asset_id",
            "provider",
            "external_event_id",
            name="uq_performance_match_tracking_provider_ingest_events_replay",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    tracking_run_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("performance_match_tracking_runs.id"), index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    external_event_id: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    signature_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    signature_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    player_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="accepted", nullable=False, index=True)


class PerformanceMatchTrackingSample(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_match_tracking_samples"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    tracking_run_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_match_tracking_runs.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    track_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    team_label: Mapped[str | None] = mapped_column(String(120), index=True)
    player_label: Mapped[str | None] = mapped_column(String(180), index=True)
    jersey_number: Mapped[str | None] = mapped_column(String(20), index=True)
    frame_index: Mapped[int | None] = mapped_column(Integer, index=True)
    timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    x_percent: Mapped[float] = mapped_column(Float, nullable=False)
    y_percent: Mapped[float] = mapped_column(Float, nullable=False)
    x_meters: Mapped[float] = mapped_column(Float, nullable=False)
    y_meters: Mapped[float] = mapped_column(Float, nullable=False)
    speed_mps: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(80), default="tracking_sample", nullable=False, index=True)


class PerformanceMatchTrackingIdentityReview(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_match_tracking_identity_reviews"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    tracking_run_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_match_tracking_runs.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    track_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    reviewer_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    team_label: Mapped[str | None] = mapped_column(String(120), index=True)
    player_label: Mapped[str | None] = mapped_column(String(180), index=True)
    jersey_number: Mapped[str | None] = mapped_column(String(20), index=True)
    decision: Mapped[str] = mapped_column(String(40), default="confirmed", nullable=False, index=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    before_json: Mapped[str] = mapped_column(Text, nullable=False)
    after_json: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class PerformanceMatchAnalysisReport(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_match_analysis_reports"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    tracking_run_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_match_tracking_runs.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    audience: Mapped[str] = mapped_column(String(80), default="coach", nullable=False, index=True)
    report_scope: Mapped[str] = mapped_column(String(80), default="team_match_review", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="generated", nullable=False, index=True)
    model_policy: Mapped[str] = mapped_column(String(180), default="afrolete-match-report-v1", nullable=False)
    summary_json: Mapped[str] = mapped_column(Text, nullable=False)
    player_cards_json: Mapped[str] = mapped_column(Text, nullable=False)
    team_shape_json: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations_json: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_format: Mapped[str] = mapped_column(String(40), default="markdown", nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(120), default="text/markdown; charset=utf-8", nullable=False)
    storage_url: Mapped[str] = mapped_column(String(800), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class PerformanceMatchPlayerGuidancePublishAudit(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_match_player_guidance_publish_audits"
    __table_args__ = (
        UniqueConstraint(
            "tracking_run_id",
            "message_id",
            name="uq_performance_match_player_guidance_publish_audits_message",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    tracking_run_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_match_tracking_runs.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    message_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("communication_messages.id"), nullable=False, index=True
    )
    player_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), nullable=False, index=True)
    track_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    player_label: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    channel: Mapped[CommunicationChannel] = mapped_column(
        enum_type(CommunicationChannel), nullable=False, index=True
    )
    recipient_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="published", nullable=False, index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class PerformanceMatchMoment(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_match_moments"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    tracking_run_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_match_tracking_runs.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    moment_category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    start_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    moment_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)
    technical_quality: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tactical_importance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    emotional_impact: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rarity_difficulty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    game_context: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    primary_track_id: Mapped[str | None] = mapped_column(String(120), index=True)
    secondary_track_id: Mapped[str | None] = mapped_column(String(120), index=True)
    team_label: Mapped[str | None] = mapped_column(String(120), index=True)
    player_label: Mapped[str | None] = mapped_column(String(180), index=True)
    jersey_number: Mapped[str | None] = mapped_column(String(20), index=True)
    zone: Mapped[str | None] = mapped_column(String(80), index=True)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    coaching_note: Mapped[str] = mapped_column(Text, nullable=False)
    tags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    source_event_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="detected", nullable=False, index=True)
    model_policy: Mapped[str] = mapped_column(String(180), default="afrolete-match-moment-detector-v1", nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class PerformanceHighlightReel(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_highlight_reels"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    tracking_run_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("performance_match_tracking_runs.id"), index=True
    )
    athlete_profile_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("athlete_profiles.id"), index=True)
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    audience: Mapped[str] = mapped_column(String(80), default="coach", nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(120), default="match_review", nullable=False, index=True)
    model_policy: Mapped[str] = mapped_column(String(180), default="afrolete-highlight-reel-v1", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="generated", nullable=False, index=True)
    clip_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    clips_json: Mapped[str] = mapped_column(Text, nullable=False)
    tags_json: Mapped[str] = mapped_column(Text, nullable=False)
    distribution_json: Mapped[str] = mapped_column(Text, nullable=False)
    branding_json: Mapped[str | None] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class PerformanceHighlightReelExport(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_highlight_reel_exports"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    highlight_reel_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_highlight_reels.id"), nullable=False, index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    tracking_run_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("performance_match_tracking_runs.id"), index=True
    )
    requested_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    export_format: Mapped[str] = mapped_column(String(80), default="timeline_json", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="rendered", nullable=False, index=True)
    renderer_policy: Mapped[str] = mapped_column(String(180), default="afrolete-highlight-export-v1", nullable=False)
    filename: Mapped[str] = mapped_column(String(220), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    storage_url: Mapped[str] = mapped_column(String(800), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    manifest_json: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class PerformanceHighlightReelShareAudit(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_highlight_reel_share_audits"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    highlight_reel_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_highlight_reels.id"), nullable=False, index=True
    )
    highlight_reel_export_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("performance_highlight_reel_exports.id"), index=True
    )
    video_asset_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("opposition_scouting_video_assets.id"), nullable=False, index=True
    )
    tracking_run_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("performance_match_tracking_runs.id"), index=True
    )
    message_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("communication_messages.id"), nullable=False, index=True
    )
    channel: Mapped[CommunicationChannel] = mapped_column(
        enum_type(CommunicationChannel), nullable=False, index=True
    )
    audience: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    share_policy: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    recipient_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    player_recipient_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    guardian_recipient_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    explicit_recipient_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="shared", nullable=False, index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class PerformanceHighlightReelDownloadAudit(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_highlight_reel_download_audits"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    highlight_reel_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_highlight_reels.id"), nullable=False, index=True
    )
    highlight_reel_export_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_highlight_reel_exports.id"), nullable=False, index=True
    )
    message_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("communication_messages.id"), nullable=False, index=True)
    message_recipient_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("message_recipients.id"), nullable=False, index=True
    )
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), nullable=False, index=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class PerformanceHighlightReelFeedback(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_highlight_reel_feedback"
    __table_args__ = (
        UniqueConstraint("message_recipient_id", name="uq_performance_highlight_reel_feedback_recipient"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    highlight_reel_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_highlight_reels.id"), nullable=False, index=True
    )
    highlight_reel_export_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("performance_highlight_reel_exports.id"), index=True
    )
    share_audit_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_highlight_reel_share_audits.id"), nullable=False, index=True
    )
    message_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("communication_messages.id"), nullable=False, index=True
    )
    message_recipient_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("message_recipients.id"), nullable=False, index=True
    )
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="acknowledged", nullable=False, index=True)
    rating: Mapped[int | None] = mapped_column(Integer)
    response_text: Mapped[str | None] = mapped_column(Text)
    priority_focus: Mapped[str | None] = mapped_column(String(120))
    requested_follow_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    clip_time_seconds: Mapped[float | None] = mapped_column(Float)
    agent_task_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("agent_tasks.id"), index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class PerformanceMovementReferenceProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_movement_reference_profiles"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "sport",
            "benchmark_profile",
            "name",
            name="uq_performance_movement_reference_profiles_name",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    sport: Mapped[str] = mapped_column(String(80), default="athletics", nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    benchmark_profile: Mapped[str] = mapped_column(
        String(120), default="world_class_sprint", nullable=False, index=True
    )
    performer_name: Mapped[str | None] = mapped_column(String(180), index=True)
    source_label: Mapped[str] = mapped_column(String(240), nullable=False)
    competition_context: Mapped[str | None] = mapped_column(String(240))
    consent_basis: Mapped[str | None] = mapped_column(String(240))
    visibility: Mapped[str] = mapped_column(String(40), default="tenant", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    metric_targets_json: Mapped[str] = mapped_column(Text, nullable=False)
    pose_samples_json: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class PerformanceModelExtractionBenchmarkDataset(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_model_extraction_benchmark_datasets"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "slug",
            name="uq_performance_model_extraction_benchmark_datasets_slug",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    model_policy: Mapped[str | None] = mapped_column(String(180), index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    owner_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_accuracy: Mapped[float | None] = mapped_column(Float)
    last_mean_absolute_error: Mapped[float | None] = mapped_column(Float)
    last_case_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class PerformanceModelExtractionBenchmarkCase(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_model_extraction_benchmark_cases"
    __table_args__ = (
        UniqueConstraint(
            "dataset_id",
            "case_id",
            name="uq_performance_model_extraction_benchmark_cases_case_id",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    dataset_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("performance_model_extraction_benchmark_datasets.id"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    metric_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(180), nullable=False)
    category: Mapped[MetricCategory] = mapped_column(
        enum_type(MetricCategory), default=MetricCategory.WELLNESS, nullable=False
    )
    unit: Mapped[str | None] = mapped_column(String(40))
    min_value: Mapped[float | None] = mapped_column(Float)
    max_value: Mapped[float | None] = mapped_column(Float)
    source: Mapped[MetricSource] = mapped_column(enum_type(MetricSource), nullable=False, index=True)
    source_provider: Mapped[str | None] = mapped_column(String(80), index=True)
    evidence_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    tolerance: Mapped[float] = mapped_column(Float, default=0.01, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class PerformanceForecastValidationRun(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_forecast_validation_runs"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    model_policy: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    forecast_mode: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    metric_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evaluated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    drift_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mean_absolute_error: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mean_relative_error: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_absolute_error: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    drift_level: Mapped[str] = mapped_column(String(40), default="no_data", nullable=False, index=True)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text)
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)


class AthletePathwayProjection(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_pathway_projections"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    sport: Mapped[str] = mapped_column(String(80), default="football", nullable=False, index=True)
    primary_position: Mapped[str | None] = mapped_column(String(80), index=True)
    age_years: Mapped[int | None] = mapped_column(Integer, index=True)
    academic_gpa: Mapped[float | None] = mapped_column(Float)
    graduation_year: Mapped[int | None] = mapped_column(Integer, index=True)
    target_pathway: Mapped[str] = mapped_column(String(80), default="balanced", nullable=False, index=True)
    model_policy: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    readiness_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    projected_level: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    college_fit_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    semi_pro_fit_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    professional_fit_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    scholarship_fit_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    pathways_json: Mapped[str] = mapped_column(Text, nullable=False)
    milestones_json: Mapped[str] = mapped_column(Text, nullable=False)
    scout_actions_json: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False)
    risk_flags_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class AthleteAssessment(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_assessments"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    assessed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    assessed_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    physical_score: Mapped[float] = mapped_column(Float, nullable=False)
    technical_score: Mapped[float] = mapped_column(Float, nullable=False)
    tactical_score: Mapped[float] = mapped_column(Float, nullable=False)
    mental_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    perceived_exertion: Mapped[float | None] = mapped_column(Float)
    effort_rating: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    recommendations: Mapped[str | None] = mapped_column(Text)
    review_assigned_to_person_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("persons.id"), index=True
    )
    review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    review_priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False, index=True)
    review_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    review_last_escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    review_escalation_count: Mapped[int] = mapped_column(default=0, nullable=False)
    review_escalation_message_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("communication_messages.id"), index=True
    )
    verification_status: Mapped[MetricVerificationStatus] = mapped_column(
        enum_type(MetricVerificationStatus),
        default=MetricVerificationStatus.VERIFIED,
        nullable=False,
        index=True,
    )


class PerformanceGoal(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_goals"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    metric_definition_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("performance_metric_definitions.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_value: Mapped[float | None] = mapped_column(Float)
    current_value: Mapped[float | None] = mapped_column(Float)
    direction: Mapped[str] = mapped_column(String(40), default="increase", nullable=False)
    starts_at: Mapped[date] = mapped_column(nullable=False, index=True)
    due_at: Mapped[date | None] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    reward_badge: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)


class PerformanceAchievementAward(IdMixin, TimestampMixin, Base):
    __tablename__ = "performance_achievement_awards"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "athlete_profile_id",
            "badge_code",
            name="uq_performance_achievement_awards_badge",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), index=True
    )
    goal_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("performance_goals.id"), index=True)
    metric_definition_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("performance_metric_definitions.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    badge_code: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    achievement_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    achieved_value: Mapped[float | None] = mapped_column(Float)
    threshold_value: Mapped[float | None] = mapped_column(Float)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source_summary: Mapped[str | None] = mapped_column(Text)
