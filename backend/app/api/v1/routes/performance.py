from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.enums import CommunicationChannel, MetricCategory
from app.schemas.performance import (
    AssessmentReviewQueueSummaryRead,
    AthleteAssessmentCreate,
    AthleteAssessmentRead,
    AthleteAssessmentReviewAssignmentUpdate,
    AthleteAssessmentReviewQueueItemRead,
    AthleteAssessmentReviewCreate,
    AthletePathwayProjectionCreate,
    AthletePathwayProjectionRead,
    AthletePerformanceSummaryRead,
    MetricDefinitionCreate,
    MetricDefinitionRead,
    OppositionScoutingFindingRead,
    OppositionScoutingReportCreate,
    OppositionScoutingReportRead,
    OppositionScoutingVideoAssetRead,
    OppositionScoutingVideoUploadCreate,
    PerformanceCohortComparisonRead,
    PerformanceAchievementAwardRead,
    PerformanceAchievementRunRead,
    PerformanceAssessmentReviewEscalationRunRead,
    PerformanceForecastValidationAlertRead,
    PerformanceForecastValidationRunCreate,
    PerformanceForecastValidationRunRead,
    PerformanceGoalCreate,
    PerformanceGoalRead,
    PerformanceHardwareDeviceCreate,
    PerformanceHardwareDeviceRead,
    PerformanceHardwareKitCreate,
    PerformanceHardwareKitRead,
    PerformanceHardwareSyncRunCreate,
    PerformanceHardwareSyncRunRead,
    PerformanceHighlightReelCreate,
    PerformanceHighlightReelExportCreate,
    PerformanceHighlightReelExportRead,
    PerformanceHighlightReelRead,
    PerformanceInjuryRiskAlertRead,
    PerformanceInjuryRiskAlertRunRead,
    PerformanceInjuryRiskRead,
    PerformanceIngestionCreate,
    PerformanceIngestionRead,
    PerformanceForecastScenarioRead,
    PerformanceForecastWhatIfRead,
    PerformanceMetricBenchmarkRead,
    PerformanceModelExtractionBenchmarkDatasetCreate,
    PerformanceModelExtractionBenchmarkDatasetRead,
    PerformanceModelExtractionBenchmarkRunCreate,
    PerformanceModelExtractionBenchmarkRunRead,
    PerformanceMetricTrendRead,
    PerformanceMetricTrendSeriesRead,
    PerformanceMatchTrackingRunCreate,
    PerformanceMatchTrackingRunRead,
    PerformanceMatchPitchCalibrationCreate,
    PerformanceMatchPitchCalibrationRead,
    PerformanceMovementReferenceProfileCreate,
    PerformanceMovementReferenceProfileRead,
    PerformanceObservationCreate,
    PerformanceObservationRead,
    PerformanceObservationReviewCreate,
    PerformancePoseGaitAnalysisCreate,
    PerformancePoseGaitAnalysisRead,
    PerformancePoseGaitMetricRead,
    PerformancePoseGaitPhaseRead,
    PerformanceOptimalProjectionRead,
    PerformanceVideoAnnotationCreate,
    PerformanceVideoAnnotationRead,
    PerformanceVideoAssetRead,
    PerformanceVideoCoachingCreate,
    PerformanceVideoCoachingMetricRead,
    PerformanceVideoCoachingRead,
    PerformanceVideoPoseSampleBatchCreate,
    PerformanceVideoPoseSampleBatchRead,
    PerformanceVideoPoseSampleRead,
    PerformanceVideoPoseProcessingCreate,
    PerformanceVideoPoseProcessingRead,
    PerformanceVideoUploadCreate,
    PerformanceWearableConnectionCreate,
    PerformanceWearableConnectionRead,
    PerformanceWearableOAuthCallbackCreate,
    PerformanceWearableOAuthCallbackRead,
    PerformanceWearableOAuthStartCreate,
    PerformanceWearableOAuthStartRead,
    PerformanceWearableSyncRunCreate,
    PerformanceWearableSyncRunRead,
    PerformanceWearableTokenRefreshCreate,
    PerformanceWearableTokenRefreshRead,
    PerformanceWearableWebhookCreate,
    PerformanceWearableWebhookRegistrationCreate,
    PerformanceWearableWebhookRegistrationRead,
    PerformanceWearableWebhookRead,
    PlayerSelfAssessmentCreate,
    PlayerPerformanceProfileRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.performance import (
    assessment_review_queue_summary,
    analyze_video_for_coaching,
    analyze_pose_gait_for_video,
    create_assessment,
    create_athlete_pathway_projection,
    create_metric_definition,
    create_match_tracking_run,
    create_match_pitch_calibration,
    create_movement_reference_profile,
    create_observation,
    create_opposition_scouting_report,
    create_performance_video_annotation,
    create_performance_video_pose_samples,
    create_performance_goal,
    create_performance_hardware_kit,
    create_performance_highlight_reel,
    create_performance_highlight_reel_export,
    create_performance_model_extraction_benchmark_dataset,
    create_player_self_assessment,
    create_wearable_provider_connection,
    decode_string_list,
    decode_uuid_list,
    evaluate_performance_achievements,
    ensure_manage_performance,
    ingest_performance_evidence,
    get_performance_video_asset,
    ingest_performance_wearable_webhook,
    list_assessment_review_queue,
    list_assessments,
    list_athlete_pathway_projections,
    list_performance_awards,
    list_performance_goals,
    list_performance_hardware_devices,
    list_performance_hardware_kits,
    list_performance_hardware_sync_runs,
    list_performance_highlight_reels,
    list_performance_highlight_reel_exports,
    list_metric_definitions,
    list_match_tracking_runs,
    list_match_pitch_calibrations,
    match_pitch_calibration_read,
    highlight_reel_read,
    highlight_reel_export_read,
    list_movement_reference_profiles,
    list_my_player_performance,
    list_observations,
    list_performance_video_annotations,
    list_performance_video_pose_samples,
    process_performance_video_pose_samples,
    list_performance_forecast_validation_runs,
    list_performance_model_extraction_benchmark_datasets,
    list_wearable_provider_connections,
    list_wearable_provider_sync_runs,
    performance_forecast_scenarios,
    performance_forecast_what_if_scenarios,
    performance_injury_risk,
    performance_metric_benchmarks,
    run_performance_model_extraction_benchmark,
    performance_cohort_comparisons,
    performance_metric_trend_series,
    performance_metric_trends,
    provision_performance_hardware_device,
    performance_summary,
    run_performance_forecast_validation,
    send_performance_forecast_validation_alert,
    run_assessment_review_escalations,
    run_performance_injury_risk_alert_scan,
    run_performance_hardware_sync,
    render_performance_highlight_reel_export,
    run_wearable_provider_sync,
    refresh_wearable_provider_token,
    register_wearable_provider_webhook,
    start_wearable_provider_oauth,
    review_assessment,
    review_observation,
    send_performance_injury_risk_alert,
    complete_wearable_provider_oauth,
    update_assessment_review_assignment,
    validate_performance_wearable_webhook_signature,
    decode_annotation_tags,
    decode_pose_keypoints,
    decode_reference_metric_targets,
    decode_reference_pose_samples,
    decode_scouting_findings,
    downloadable_performance_highlight_reel_export,
    downloadable_performance_video_asset,
    upload_performance_video_asset,
    upload_opposition_scouting_video_asset,
    list_opposition_scouting_reports,
    list_opposition_scouting_videos,
    video_slow_motion_rates,
)

router = APIRouter(prefix="/performance", tags=["performance"])


def to_metric_read(metric) -> MetricDefinitionRead:
    return MetricDefinitionRead(
        id=metric.id,
        organization_id=metric.organization_id,
        sport=metric.sport,
        code=metric.code,
        name=metric.name,
        category=metric.category,
        unit=metric.unit,
        description=metric.description,
        min_value=metric.min_value,
        max_value=metric.max_value,
        weight=metric.weight,
        higher_is_better=metric.higher_is_better,
        status=metric.status,
    )


def to_observation_read(observation) -> PerformanceObservationRead:
    return PerformanceObservationRead(
        id=observation.id,
        organization_id=observation.organization_id,
        athlete_profile_id=observation.athlete_profile_id,
        metric_definition_id=observation.metric_definition_id,
        event_id=observation.event_id,
        recorded_by_person_id=observation.recorded_by_person_id,
        value=observation.value,
        raw_value=observation.raw_value,
        observed_at=observation.observed_at,
        source=observation.source,
        confidence=observation.confidence,
        verification_status=observation.verification_status,
        notes=observation.notes,
    )


def to_wearable_connection_read(connection) -> PerformanceWearableConnectionRead:
    return PerformanceWearableConnectionRead(
        id=connection.id,
        organization_id=connection.organization_id,
        athlete_profile_id=connection.athlete_profile_id,
        provider=connection.provider,
        display_name=connection.display_name,
        external_athlete_ref=connection.external_athlete_ref,
        status=connection.status,
        auth_type=connection.auth_type,
        scopes=decode_string_list(connection.scopes),
        access_token_configured=bool(connection.access_token_secret_path),
        refresh_token_configured=bool(connection.refresh_token_secret_path),
        webhook_secret_configured=bool(connection.webhook_secret_path),
        access_token_recorded=bool(connection.access_token_hash),
        refresh_token_recorded=bool(connection.refresh_token_hash),
        refresh_token_family_id=connection.refresh_token_family_id,
        refresh_token_rotated_at=connection.refresh_token_rotated_at,
        token_last_refreshed_at=connection.token_last_refreshed_at,
        token_type=connection.token_type,
        token_scope=decode_string_list(connection.token_scope),
        token_expires_at=connection.token_expires_at,
        oauth_client_id=connection.oauth_client_id,
        oauth_client_secret_configured=bool(connection.oauth_client_secret_path),
        oauth_authorization_url=connection.oauth_authorization_url,
        oauth_token_url=connection.oauth_token_url,
        oauth_redirect_uri=connection.oauth_redirect_uri,
        oauth_state_pending=bool(connection.oauth_state_hash),
        oauth_state_expires_at=connection.oauth_state_expires_at,
        oauth_authorized_at=connection.oauth_authorized_at,
        provider_pull_url=connection.provider_pull_url,
        provider_pull_cursor_param=connection.provider_pull_cursor_param,
        provider_pull_since_param=connection.provider_pull_since_param,
        provider_pull_until_param=connection.provider_pull_until_param,
        provider_pull_configured=bool(connection.provider_pull_url),
        sync_cursor=connection.sync_cursor,
        last_sync_at=connection.last_sync_at,
        webhook_registered=connection.webhook_registered,
        provider_webhook_registration_url=connection.provider_webhook_registration_url,
        provider_webhook_callback_url=connection.provider_webhook_callback_url,
        provider_webhook_event_types=decode_string_list(connection.provider_webhook_event_types),
        provider_webhook_registration_status_code=connection.provider_webhook_registration_status_code,
        provider_webhook_registration_hash=connection.provider_webhook_registration_hash,
        provider_webhook_registered_at=connection.provider_webhook_registered_at,
        provider_webhook_registration_error=connection.provider_webhook_registration_error,
        default_metric_definition_ids=decode_uuid_list(connection.default_metric_definition_ids),
    )


def to_wearable_sync_run_read(run) -> PerformanceWearableSyncRunRead:
    return PerformanceWearableSyncRunRead(
        id=run.id,
        organization_id=run.organization_id,
        connection_id=run.connection_id,
        athlete_profile_id=run.athlete_profile_id,
        provider=run.provider,
        external_event_id=run.external_event_id,
        status=run.status,
        sync_mode=run.sync_mode,
        started_at=run.started_at,
        completed_at=run.completed_at,
        observation_count=run.observation_count,
        skipped_metric_count=run.skipped_metric_count,
        replayed=run.replayed,
        provider_status_code=run.provider_status_code,
        provider_response_hash=run.provider_response_hash,
        provider_page_count=run.provider_page_count,
        provider_rate_limited=run.provider_rate_limited,
        provider_retry_after_seconds=run.provider_retry_after_seconds,
        message=run.message,
    )


def to_hardware_kit_read(kit) -> PerformanceHardwareKitRead:
    return PerformanceHardwareKitRead(
        id=kit.id,
        organization_id=kit.organization_id,
        name=kit.name,
        kit_type=kit.kit_type,
        provider=kit.provider,
        sport=kit.sport,
        level=kit.level,
        recommended_camera_count=kit.recommended_camera_count,
        recommended_gps_unit_count=kit.recommended_gps_unit_count,
        supported_metrics=decode_string_list(kit.supported_metrics_json),
        setup_steps=decode_string_list(kit.setup_steps_json),
        estimated_cost=kit.estimated_cost,
        currency=kit.currency,
        status=kit.status,
        notes=kit.notes,
        created_at=kit.created_at,
    )


def to_hardware_device_read(device) -> PerformanceHardwareDeviceRead:
    return PerformanceHardwareDeviceRead(
        id=device.id,
        organization_id=device.organization_id,
        kit_id=device.kit_id,
        team_id=device.team_id,
        facility_id=device.facility_id,
        device_type=device.device_type,
        provider=device.provider,
        device_label=device.device_label,
        external_device_id=device.external_device_id,
        firmware_version=device.firmware_version,
        status=device.status,
        api_key_configured=bool(device.api_key_secret_path or device.api_key_hash),
        api_key_secret_path=device.api_key_secret_path,
        custody_mode=device.custody_mode,
        metrics_supported=decode_string_list(device.metrics_supported_json),
        calibration_id=device.calibration_id,
        last_seen_at=device.last_seen_at,
        battery_percent=device.battery_percent,
        notes=device.notes,
        created_at=device.created_at,
    )


def to_assessment_read(assessment) -> AthleteAssessmentRead:
    return AthleteAssessmentRead(
        id=assessment.id,
        organization_id=assessment.organization_id,
        athlete_profile_id=assessment.athlete_profile_id,
        event_id=assessment.event_id,
        assessed_by_person_id=assessment.assessed_by_person_id,
        assessed_at=assessment.assessed_at,
        physical_score=assessment.physical_score,
        technical_score=assessment.technical_score,
        tactical_score=assessment.tactical_score,
        mental_score=assessment.mental_score,
        overall_score=assessment.overall_score,
        perceived_exertion=assessment.perceived_exertion,
        effort_rating=assessment.effort_rating,
        summary=assessment.summary,
        recommendations=assessment.recommendations,
        review_assigned_to_person_id=assessment.review_assigned_to_person_id,
        review_due_at=assessment.review_due_at,
        review_priority=assessment.review_priority,
        review_notes=assessment.review_notes,
        reviewed_by_person_id=assessment.reviewed_by_person_id,
        reviewed_at=assessment.reviewed_at,
        review_last_escalated_at=assessment.review_last_escalated_at,
        review_escalation_count=assessment.review_escalation_count,
        review_escalation_message_id=assessment.review_escalation_message_id,
        verification_status=assessment.verification_status,
    )


def to_video_asset_read(video_asset) -> PerformanceVideoAssetRead:
    return PerformanceVideoAssetRead(
        id=video_asset.id,
        organization_id=video_asset.organization_id,
        athlete_profile_id=video_asset.athlete_profile_id,
        event_id=video_asset.event_id,
        uploaded_by_person_id=video_asset.uploaded_by_person_id,
        sport=video_asset.sport,
        filename=video_asset.filename,
        content_type=video_asset.content_type,
        size_bytes=video_asset.size_bytes,
        checksum=video_asset.checksum,
        storage_url=video_asset.storage_url,
        video_uri=video_asset.video_uri,
        clip_label=video_asset.clip_label,
        analysis_focus=video_asset.analysis_focus,
        duration_seconds=video_asset.duration_seconds,
        frame_rate=video_asset.frame_rate,
        frame_width=video_asset.frame_width,
        frame_height=video_asset.frame_height,
        status=video_asset.status,
        analysis_model_policy=video_asset.analysis_model_policy,
        analyzed_at=video_asset.analyzed_at,
        slow_motion_rates=video_slow_motion_rates(),
        review_default_rate=0.5,
    )


def to_opposition_scouting_video_read(video_asset) -> OppositionScoutingVideoAssetRead:
    return OppositionScoutingVideoAssetRead(
        id=video_asset.id,
        organization_id=video_asset.organization_id,
        team_id=video_asset.team_id,
        competition_id=video_asset.competition_id,
        event_id=video_asset.event_id,
        uploaded_by_person_id=video_asset.uploaded_by_person_id,
        opponent_name=video_asset.opponent_name,
        sport=video_asset.sport,
        filename=video_asset.filename,
        content_type=video_asset.content_type,
        size_bytes=video_asset.size_bytes,
        checksum=video_asset.checksum,
        storage_url=video_asset.storage_url,
        video_uri=video_asset.video_uri,
        clip_label=video_asset.clip_label,
        match_context=video_asset.match_context,
        analysis_focus=video_asset.analysis_focus,
        status=video_asset.status,
        analyzed_at=video_asset.analyzed_at,
    )


def to_opposition_scouting_report_read(report) -> OppositionScoutingReportRead:
    return OppositionScoutingReportRead(
        id=report.id,
        organization_id=report.organization_id,
        video_asset_id=report.video_asset_id,
        team_id=report.team_id,
        competition_id=report.competition_id,
        event_id=report.event_id,
        created_by_person_id=report.created_by_person_id,
        opponent_name=report.opponent_name,
        sport=report.sport,
        match_context=report.match_context,
        analysis_focus=report.analysis_focus,
        model_policy=report.model_policy,
        confidence=report.confidence,
        formation_detected=report.formation_detected,
        tactical_summary=report.tactical_summary,
        weaknesses=[
            OppositionScoutingFindingRead(**finding)
            for finding in decode_scouting_findings(report.weaknesses_json)
        ],
        threats=[
            OppositionScoutingFindingRead(**finding)
            for finding in decode_scouting_findings(report.threats_json)
        ],
        recommendations=[
            OppositionScoutingFindingRead(**finding)
            for finding in decode_scouting_findings(report.recommendations_json)
        ],
        set_pieces=[
            OppositionScoutingFindingRead(**finding)
            for finding in decode_scouting_findings(report.set_pieces_json)
        ],
        status=report.status,
        generated_at=report.generated_at,
    )


def to_video_annotation_read(annotation) -> PerformanceVideoAnnotationRead:
    return PerformanceVideoAnnotationRead(
        id=annotation.id,
        organization_id=annotation.organization_id,
        video_asset_id=annotation.video_asset_id,
        athlete_profile_id=annotation.athlete_profile_id,
        event_id=annotation.event_id,
        author_person_id=annotation.author_person_id,
        timestamp_seconds=annotation.timestamp_seconds,
        playback_rate=annotation.playback_rate,
        annotation_type=annotation.annotation_type,
        label=annotation.label,
        notes=annotation.notes,
        body_region=annotation.body_region,
        x_percent=annotation.x_percent,
        y_percent=annotation.y_percent,
        width_percent=annotation.width_percent,
        height_percent=annotation.height_percent,
        tags=decode_annotation_tags(annotation.tags_json),
        created_at=annotation.created_at,
    )


def to_video_pose_sample_read(sample) -> PerformanceVideoPoseSampleRead:
    return PerformanceVideoPoseSampleRead(
        id=sample.id,
        organization_id=sample.organization_id,
        video_asset_id=sample.video_asset_id,
        athlete_profile_id=sample.athlete_profile_id,
        event_id=sample.event_id,
        created_by_person_id=sample.created_by_person_id,
        source_provider=sample.source_provider,
        frame_index=sample.frame_index,
        timestamp_seconds=sample.timestamp_seconds,
        phase=sample.phase,
        contact_foot=sample.contact_foot,
        stride_index=sample.stride_index,
        sample_confidence=sample.sample_confidence,
        keypoints=decode_pose_keypoints(sample.keypoints_json),
        created_at=sample.created_at,
    )


def to_video_pose_sample_batch_read(video_asset, samples) -> PerformanceVideoPoseSampleBatchRead:
    return PerformanceVideoPoseSampleBatchRead(
        video_asset=to_video_asset_read(video_asset),
        sample_count=len(samples),
        source_providers=sorted({sample.source_provider for sample in samples}),
        samples=[to_video_pose_sample_read(sample) for sample in samples],
    )


def to_movement_reference_profile_read(profile) -> PerformanceMovementReferenceProfileRead:
    return PerformanceMovementReferenceProfileRead(
        id=profile.id,
        organization_id=profile.organization_id,
        created_by_person_id=profile.created_by_person_id,
        sport=profile.sport,
        name=profile.name,
        benchmark_profile=profile.benchmark_profile,
        performer_name=profile.performer_name,
        source_label=profile.source_label,
        competition_context=profile.competition_context,
        consent_basis=profile.consent_basis,
        visibility=profile.visibility,
        status=profile.status,
        metric_targets=decode_reference_metric_targets(profile.metric_targets_json),
        pose_samples=decode_reference_pose_samples(profile.pose_samples_json),
        notes=profile.notes,
        created_at=profile.created_at,
    )


def to_video_coaching_read(result) -> PerformanceVideoCoachingRead:
    return PerformanceVideoCoachingRead(
        organization_id=result["organization_id"],
        athlete_profile_id=result["athlete_profile_id"],
        event_id=result["event_id"],
        sport=result["sport"],
        video_uri=result["video_uri"],
        clip_label=result["clip_label"],
        model_policy=result["model_policy"],
        confidence=result["confidence"],
        summary=result["summary"],
        coaching_plan=result["coaching_plan"],
        review_required=result["review_required"],
        observations=[
            to_observation_read(observation) for observation in result["observations"]
        ],
        assessment=to_assessment_read(result["assessment"]),
        metrics=[
            PerformanceVideoCoachingMetricRead(**metric) for metric in result["metrics"]
        ],
        next_actions=result["next_actions"],
    )


def assessment_review_sla_state(assessment) -> str:
    if assessment.review_due_at is None:
        return "unscheduled"
    due_at = assessment.review_due_at
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=UTC)
    now = datetime.now(UTC)
    if due_at < now:
        return "overdue"
    if (due_at - now).total_seconds() <= 24 * 60 * 60:
        return "due_soon"
    return "on_track"


def assessment_review_age_hours(assessment) -> int:
    created_at = assessment.created_at or assessment.assessed_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return max(0, int((datetime.now(UTC) - created_at).total_seconds() // 3600))


def to_goal_read(goal) -> PerformanceGoalRead:
    return PerformanceGoalRead(
        id=goal.id,
        organization_id=goal.organization_id,
        athlete_profile_id=goal.athlete_profile_id,
        metric_definition_id=goal.metric_definition_id,
        title=goal.title,
        target_value=goal.target_value,
        baseline_value=goal.baseline_value,
        current_value=goal.current_value,
        direction=goal.direction,
        starts_at=goal.starts_at,
        due_at=goal.due_at,
        status=goal.status,
        reward_badge=goal.reward_badge,
        notes=goal.notes,
    )


def to_award_read(award) -> PerformanceAchievementAwardRead:
    return PerformanceAchievementAwardRead(
        id=award.id,
        organization_id=award.organization_id,
        athlete_profile_id=award.athlete_profile_id,
        goal_id=award.goal_id,
        metric_definition_id=award.metric_definition_id,
        title=award.title,
        badge_code=award.badge_code,
        achievement_type=award.achievement_type,
        achieved_value=award.achieved_value,
        threshold_value=award.threshold_value,
        awarded_at=award.awarded_at,
        source_summary=award.source_summary,
    )


@router.post("/metrics", response_model=MetricDefinitionRead, status_code=status.HTTP_201_CREATED)
async def create_metric_definition_route(
    payload: MetricDefinitionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MetricDefinitionRead:
    return to_metric_read(await create_metric_definition(db, identity, payload, authz))


@router.get("/metrics", response_model=list[MetricDefinitionRead])
async def list_metric_definitions_route(
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[MetricDefinitionRead]:
    return [
        to_metric_read(metric)
        for metric in await list_metric_definitions(db, organization_id, sport=sport)
    ]


@router.get("/my-profiles", response_model=list[PlayerPerformanceProfileRead])
async def list_my_player_performance_route(
    organization_id: UUID = Query(),
    observation_limit: int = Query(default=10, ge=1, le=50),
    benchmark_cohort_scope: str = Query(default="tenant"),
    trend_category: MetricCategory | None = Query(default=None),
    trend_metric_code: str | None = Query(default=None),
    trend_period_start: date | None = Query(default=None),
    trend_period_end: date | None = Query(default=None),
    what_if_training_adjustment_percent: float = Query(default=0.0, ge=-50, le=50),
    what_if_readiness_score: int = Query(default=70, ge=0, le=100),
    what_if_horizon: int = Query(default=4, ge=1, le=8),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[PlayerPerformanceProfileRead]:
    profiles = await list_my_player_performance(
        db,
        identity,
        organization_id,
        observation_limit=observation_limit,
        benchmark_cohort_scope=benchmark_cohort_scope,
        trend_category=trend_category,
        trend_metric_code=trend_metric_code,
        trend_period_start=trend_period_start,
        trend_period_end=trend_period_end,
        what_if_training_adjustment_percent=what_if_training_adjustment_percent,
        what_if_readiness_score=what_if_readiness_score,
        what_if_horizon=what_if_horizon,
    )
    return [
        PlayerPerformanceProfileRead(
            organization_id=profile["organization_id"],
            athlete_profile_id=profile["athlete_profile_id"],
            athlete_person_id=profile["athlete_person_id"],
            athlete_name=profile["athlete_name"],
            latest_overall_score=profile["latest_overall_score"],
            observation_count=profile["observation_count"],
            assessment_count=profile["assessment_count"],
            latest_assessment_id=profile["latest_assessment_id"],
            latest_assessment=(
                to_assessment_read(profile["latest_assessment"])
                if profile["latest_assessment"] is not None
                else None
            ),
            rating=profile["rating"],
            active_goal_count=profile["active_goal_count"],
            achieved_goal_count=profile["achieved_goal_count"],
            award_count=profile["award_count"],
            observations=[
                to_observation_read(observation) for observation in profile["observations"]
            ],
            goals=[to_goal_read(goal) for goal in profile["goals"]],
            awards=[to_award_read(award) for award in profile["awards"]],
            trends=[
                PerformanceMetricTrendRead(**trend) for trend in profile["trends"]
            ],
            trend_series=[
                PerformanceMetricTrendSeriesRead(**series)
                for series in profile["trend_series"]
            ],
            forecast_scenarios=[
                PerformanceForecastScenarioRead(**scenario)
                for scenario in profile["forecast_scenarios"]
            ],
            what_if_scenarios=[
                PerformanceForecastWhatIfRead(**scenario)
                for scenario in profile["what_if_scenarios"]
            ],
            injury_risk=PerformanceInjuryRiskRead(**profile["injury_risk"]),
            benchmarks=[
                PerformanceMetricBenchmarkRead(**benchmark) for benchmark in profile["benchmarks"]
            ],
            cohort_comparisons=[
                PerformanceCohortComparisonRead(**comparison)
                for comparison in profile["cohort_comparisons"]
            ],
        )
        for profile in profiles
    ]


@router.post(
    "/my-profiles/{athlete_profile_id}/self-assessments",
    response_model=AthleteAssessmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_player_self_assessment_route(
    athlete_profile_id: UUID,
    payload: PlayerSelfAssessmentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> AthleteAssessmentRead:
    return to_assessment_read(
        await create_player_self_assessment(db, identity, athlete_profile_id, payload)
    )


@router.post(
    "/athletes/{athlete_profile_id}/observations",
    response_model=PerformanceObservationRead,
    status_code=201,
)
async def create_observation_route(
    athlete_profile_id: UUID,
    payload: PerformanceObservationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceObservationRead:
    return to_observation_read(
        await create_observation(db, identity, athlete_profile_id, payload, authz)
    )


@router.post(
    "/ingest",
    response_model=PerformanceIngestionRead,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_performance_evidence_route(
    payload: PerformanceIngestionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceIngestionRead:
    result = await ingest_performance_evidence(db, identity, payload, authz)
    return PerformanceIngestionRead(
        observation=to_observation_read(result["observation"]),
        evidence_ref=result["evidence_ref"],
        source_provider=result["source_provider"],
        extractor=result["extractor"],
        confidence=result["confidence"],
        review_required=result["review_required"],
        summary=result["summary"],
        parser_method=result["parser_method"],
        parser_confidence_reason=result["parser_confidence_reason"],
        parser_warnings=result["parser_warnings"],
        parsed_fields=result["parsed_fields"],
        model_assisted=result["model_assisted"],
        model_policy=result["model_policy"],
        model_confidence=result["model_confidence"],
        model_summary=result["model_summary"],
        model_evaluation=result["model_evaluation"],
    )


@router.post(
    "/athletes/{athlete_profile_id}/video-coaching",
    response_model=PerformanceVideoCoachingRead,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_video_for_coaching_route(
    athlete_profile_id: UUID,
    payload: PerformanceVideoCoachingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceVideoCoachingRead:
    result = await analyze_video_for_coaching(
        db,
        identity,
        athlete_profile_id,
        payload,
        authz,
    )
    return to_video_coaching_read(result)


@router.post(
    "/scouting/videos",
    response_model=OppositionScoutingVideoAssetRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_opposition_scouting_video_route(
    payload: OppositionScoutingVideoUploadCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OppositionScoutingVideoAssetRead:
    return to_opposition_scouting_video_read(
        await upload_opposition_scouting_video_asset(db, identity, payload, authz)
    )


@router.get("/scouting/videos", response_model=list[OppositionScoutingVideoAssetRead])
async def list_opposition_scouting_videos_route(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OppositionScoutingVideoAssetRead]:
    return [
        to_opposition_scouting_video_read(video_asset)
        for video_asset in await list_opposition_scouting_videos(
            db,
            identity,
            organization_id,
            authz,
            team_id=team_id,
        )
    ]


@router.post(
    "/scouting/videos/{video_asset_id}/reports",
    response_model=OppositionScoutingReportRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_opposition_scouting_report_route(
    video_asset_id: UUID,
    payload: OppositionScoutingReportCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> OppositionScoutingReportRead:
    return to_opposition_scouting_report_read(
        await create_opposition_scouting_report(db, identity, video_asset_id, payload, authz)
    )


@router.post(
    "/scouting/videos/{video_asset_id}/pitch-calibrations",
    response_model=PerformanceMatchPitchCalibrationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_match_pitch_calibration_route(
    video_asset_id: UUID,
    payload: PerformanceMatchPitchCalibrationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceMatchPitchCalibrationRead:
    return PerformanceMatchPitchCalibrationRead(
        **match_pitch_calibration_read(
            await create_match_pitch_calibration(db, identity, video_asset_id, payload, authz)
        )
    )


@router.get("/scouting/pitch-calibrations", response_model=list[PerformanceMatchPitchCalibrationRead])
async def list_match_pitch_calibrations_route(
    organization_id: UUID = Query(),
    video_asset_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[PerformanceMatchPitchCalibrationRead]:
    return [
        PerformanceMatchPitchCalibrationRead(**match_pitch_calibration_read(calibration))
        for calibration in await list_match_pitch_calibrations(
            db,
            identity,
            organization_id,
            authz,
            video_asset_id=video_asset_id,
        )
    ]


@router.post(
    "/scouting/videos/{video_asset_id}/tracking-runs",
    response_model=PerformanceMatchTrackingRunRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_match_tracking_run_route(
    video_asset_id: UUID,
    payload: PerformanceMatchTrackingRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceMatchTrackingRunRead:
    return PerformanceMatchTrackingRunRead(
        **await create_match_tracking_run(db, identity, video_asset_id, payload, authz)
    )


@router.get("/scouting/tracking-runs", response_model=list[PerformanceMatchTrackingRunRead])
async def list_match_tracking_runs_route(
    organization_id: UUID = Query(),
    video_asset_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[PerformanceMatchTrackingRunRead]:
    return [
        PerformanceMatchTrackingRunRead(**run)
        for run in await list_match_tracking_runs(
            db,
            identity,
            organization_id,
            authz,
            video_asset_id=video_asset_id,
        )
    ]


@router.post(
    "/scouting/videos/{video_asset_id}/highlight-reels",
    response_model=PerformanceHighlightReelRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance_highlight_reel_route(
    video_asset_id: UUID,
    payload: PerformanceHighlightReelCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceHighlightReelRead:
    return PerformanceHighlightReelRead(
        **highlight_reel_read(
            await create_performance_highlight_reel(db, identity, video_asset_id, payload, authz)
        )
    )


@router.get("/scouting/highlight-reels", response_model=list[PerformanceHighlightReelRead])
async def list_performance_highlight_reels_route(
    organization_id: UUID = Query(),
    video_asset_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[PerformanceHighlightReelRead]:
    return [
        PerformanceHighlightReelRead(**highlight_reel_read(reel))
        for reel in await list_performance_highlight_reels(
            db,
            identity,
            organization_id,
            authz,
            video_asset_id=video_asset_id,
        )
    ]


@router.post(
    "/scouting/highlight-reels/{highlight_reel_id}/exports",
    response_model=PerformanceHighlightReelExportRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance_highlight_reel_export_route(
    highlight_reel_id: UUID,
    payload: PerformanceHighlightReelExportCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceHighlightReelExportRead:
    return PerformanceHighlightReelExportRead(
        **highlight_reel_export_read(
            await create_performance_highlight_reel_export(db, identity, highlight_reel_id, payload, authz)
        )
    )


@router.get("/scouting/highlight-reel-exports", response_model=list[PerformanceHighlightReelExportRead])
async def list_performance_highlight_reel_exports_route(
    organization_id: UUID = Query(),
    highlight_reel_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[PerformanceHighlightReelExportRead]:
    return [
        PerformanceHighlightReelExportRead(**highlight_reel_export_read(export))
        for export in await list_performance_highlight_reel_exports(
            db,
            identity,
            organization_id,
            authz,
            highlight_reel_id=highlight_reel_id,
        )
    ]


@router.post(
    "/scouting/highlight-reel-exports/{export_id}/render",
    response_model=PerformanceHighlightReelExportRead,
    status_code=status.HTTP_201_CREATED,
)
async def render_performance_highlight_reel_export_route(
    export_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceHighlightReelExportRead:
    return PerformanceHighlightReelExportRead(
        **highlight_reel_export_read(
            await render_performance_highlight_reel_export(db, identity, export_id, authz)
        )
    )


@router.get("/scouting/reports", response_model=list[OppositionScoutingReportRead])
async def list_opposition_scouting_reports_route(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[OppositionScoutingReportRead]:
    return [
        to_opposition_scouting_report_read(report)
        for report in await list_opposition_scouting_reports(
            db,
            identity,
            organization_id,
            authz,
            team_id=team_id,
        )
    ]


@router.post(
    "/movement-reference-profiles",
    response_model=PerformanceMovementReferenceProfileRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_movement_reference_profile_route(
    payload: PerformanceMovementReferenceProfileCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceMovementReferenceProfileRead:
    return to_movement_reference_profile_read(
        await create_movement_reference_profile(db, identity, payload, authz)
    )


@router.get(
    "/movement-reference-profiles",
    response_model=list[PerformanceMovementReferenceProfileRead],
)
async def list_movement_reference_profiles_route(
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    benchmark_profile: str | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[PerformanceMovementReferenceProfileRead]:
    await ensure_manage_performance(authz, identity, organization_id)
    return [
        to_movement_reference_profile_read(profile)
        for profile in await list_movement_reference_profiles(
            db,
            organization_id,
            sport=sport,
            benchmark_profile=benchmark_profile,
        )
    ]


@router.post(
    "/athletes/{athlete_profile_id}/videos",
    response_model=PerformanceVideoAssetRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_performance_video_asset_route(
    athlete_profile_id: UUID,
    payload: PerformanceVideoUploadCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceVideoAssetRead:
    return to_video_asset_read(
        await upload_performance_video_asset(db, identity, athlete_profile_id, payload, authz)
    )


@router.get("/videos/{video_asset_id}/content")
async def download_performance_video_asset_route(
    video_asset_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> Response:
    artifact = await downloadable_performance_video_asset(db, identity, video_asset_id, authz)
    return Response(
        content=artifact["content"],
        media_type=str(artifact["content_type"]),
        headers={
            "Content-Disposition": f"inline; filename={artifact['filename']}",
            "X-Afrolete-Performance-Video-Checksum": str(artifact["checksum"]),
        },
    )


@router.get("/scouting/highlight-reel-exports/{export_id}/content")
async def download_performance_highlight_reel_export_route(
    export_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> Response:
    artifact = await downloadable_performance_highlight_reel_export(db, identity, export_id, authz)
    return Response(
        content=artifact["content"],
        media_type=str(artifact["content_type"]),
        headers={
            "Content-Disposition": f"attachment; filename={artifact['filename']}",
            "X-Afrolete-Highlight-Export-Checksum": str(artifact["checksum"]),
        },
    )


@router.post(
    "/videos/{video_asset_id}/annotations",
    response_model=PerformanceVideoAnnotationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance_video_annotation_route(
    video_asset_id: UUID,
    payload: PerformanceVideoAnnotationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceVideoAnnotationRead:
    return to_video_annotation_read(
        await create_performance_video_annotation(db, identity, video_asset_id, payload, authz)
    )


@router.get(
    "/videos/{video_asset_id}/annotations",
    response_model=list[PerformanceVideoAnnotationRead],
)
async def list_performance_video_annotations_route(
    video_asset_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceVideoAnnotationRead]:
    return [
        to_video_annotation_read(annotation)
        for annotation in await list_performance_video_annotations(db, video_asset_id)
    ]


@router.post(
    "/videos/{video_asset_id}/pose-samples",
    response_model=PerformanceVideoPoseSampleBatchRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance_video_pose_samples_route(
    video_asset_id: UUID,
    payload: PerformanceVideoPoseSampleBatchCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceVideoPoseSampleBatchRead:
    samples = await create_performance_video_pose_samples(db, identity, video_asset_id, payload, authz)
    video_asset = await get_performance_video_asset(db, video_asset_id)
    return to_video_pose_sample_batch_read(video_asset, samples)


@router.get(
    "/videos/{video_asset_id}/pose-samples",
    response_model=PerformanceVideoPoseSampleBatchRead,
)
async def list_performance_video_pose_samples_route(
    video_asset_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceVideoPoseSampleBatchRead:
    samples = await list_performance_video_pose_samples(db, video_asset_id)
    video_asset = await get_performance_video_asset(db, video_asset_id)
    await ensure_manage_performance(authz, identity, video_asset.organization_id)
    return to_video_pose_sample_batch_read(video_asset, samples)


@router.post(
    "/videos/{video_asset_id}/pose-processing-runs",
    response_model=PerformanceVideoPoseProcessingRead,
    status_code=status.HTTP_201_CREATED,
)
async def process_performance_video_pose_samples_route(
    video_asset_id: UUID,
    payload: PerformanceVideoPoseProcessingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceVideoPoseProcessingRead:
    result = await process_performance_video_pose_samples(
        db,
        video_asset_id,
        payload,
        identity=identity,
        authz=authz,
    )
    analysis = result["analysis"]
    return PerformanceVideoPoseProcessingRead(
        video_asset=to_video_asset_read(result["video_asset"]),
        model_policy=str(result["model_policy"]),
        source_provider=str(result["source_provider"]),
        processed_frame_count=int(result["processed_frame_count"]),
        decoded_frame_count=int(result["decoded_frame_count"]),
        sample_count=int(result["sample_count"]),
        warning_count=len(result["warnings"]),
        warnings=list(result["warnings"]),
        pose_samples=to_video_pose_sample_batch_read(result["video_asset"], result["samples"]),
        analysis_summary=analysis.get("summary") if analysis else None,
        analysis_model_policy=analysis.get("model_policy") if analysis else None,
    )


@router.post(
    "/videos/{video_asset_id}/pose-gait-analysis",
    response_model=PerformancePoseGaitAnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_pose_gait_for_video_route(
    video_asset_id: UUID,
    payload: PerformancePoseGaitAnalysisCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformancePoseGaitAnalysisRead:
    result = await analyze_pose_gait_for_video(db, identity, video_asset_id, payload, authz)
    analysis = result["analysis"]
    return PerformancePoseGaitAnalysisRead(
        video_asset=to_video_asset_read(result["video_asset"]),
        model_policy=analysis["model_policy"],
        benchmark_profile=analysis["benchmark_profile"],
        reference_profile_id=analysis.get("reference_profile_id"),
        reference_profile_name=analysis.get("reference_profile_name"),
        reference_profile_source=analysis.get("reference_profile_source"),
        confidence=analysis["confidence"],
        pose_sample_count=analysis.get("pose_sample_count", 0),
        pose_sample_source_providers=analysis.get("pose_sample_source_providers", []),
        summary=analysis["summary"],
        metrics=[
            PerformancePoseGaitMetricRead(**metric) for metric in analysis["metrics"]
        ],
        phases=[
            PerformancePoseGaitPhaseRead(**phase) for phase in analysis["phases"]
        ],
        optimal_projections=[
            PerformanceOptimalProjectionRead(**projection)
            for projection in analysis["optimal_projections"]
        ],
        slow_motion_rates=analysis["slow_motion_rates"],
        annotations=[
            to_video_annotation_read(annotation) for annotation in result["annotations"]
        ],
        coaching=to_video_coaching_read(result["coaching"]) if result["coaching"] else None,
    )


@router.post(
    "/model-extraction/benchmark-datasets",
    response_model=PerformanceModelExtractionBenchmarkDatasetRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance_model_extraction_benchmark_dataset_route(
    payload: PerformanceModelExtractionBenchmarkDatasetCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceModelExtractionBenchmarkDatasetRead:
    return PerformanceModelExtractionBenchmarkDatasetRead(
        **await create_performance_model_extraction_benchmark_dataset(db, identity, payload, authz)
    )


@router.get(
    "/model-extraction/benchmark-datasets",
    response_model=list[PerformanceModelExtractionBenchmarkDatasetRead],
)
async def list_performance_model_extraction_benchmark_datasets_route(
    organization_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[PerformanceModelExtractionBenchmarkDatasetRead]:
    return [
        PerformanceModelExtractionBenchmarkDatasetRead(**dataset)
        for dataset in await list_performance_model_extraction_benchmark_datasets(
            db, identity, organization_id, authz
        )
    ]


@router.post(
    "/model-extraction/benchmarks",
    response_model=PerformanceModelExtractionBenchmarkRunRead,
)
async def run_performance_model_extraction_benchmark_route(
    payload: PerformanceModelExtractionBenchmarkRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceModelExtractionBenchmarkRunRead:
    return PerformanceModelExtractionBenchmarkRunRead(
        **await run_performance_model_extraction_benchmark(db, identity, payload, authz)
    )


@router.post(
    "/forecast-validation-runs",
    response_model=PerformanceForecastValidationRunRead,
    status_code=status.HTTP_201_CREATED,
)
async def run_performance_forecast_validation_route(
    payload: PerformanceForecastValidationRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceForecastValidationRunRead:
    return PerformanceForecastValidationRunRead(
        **await run_performance_forecast_validation(db, identity, payload, authz)
    )


@router.get(
    "/forecast-validation-runs",
    response_model=list[PerformanceForecastValidationRunRead],
)
async def list_performance_forecast_validation_runs_route(
    organization_id: UUID = Query(),
    athlete_profile_id: UUID | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[PerformanceForecastValidationRunRead]:
    return [
        PerformanceForecastValidationRunRead(**run)
        for run in await list_performance_forecast_validation_runs(
            db,
            identity,
            organization_id,
            authz,
            athlete_profile_id=athlete_profile_id,
            limit=limit,
        )
    ]


@router.post(
    "/forecast-validation-runs/{validation_run_id}/alerts",
    response_model=PerformanceForecastValidationAlertRead,
)
async def send_performance_forecast_validation_alert_route(
    validation_run_id: UUID,
    repeat_after_hours: int = Query(default=24, ge=0, le=720),
    channels: list[CommunicationChannel] | None = Query(default=None),
    dry_run: bool = Query(default=False),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceForecastValidationAlertRead:
    result = await send_performance_forecast_validation_alert(
        db,
        identity,
        validation_run_id,
        authz,
        dry_run=dry_run,
        repeat_after_hours=repeat_after_hours,
        channels=channels,
    )
    return PerformanceForecastValidationAlertRead(
        **{
            **result,
            "validation_run": PerformanceForecastValidationRunRead(**result["validation_run"]),
        }
    )


@router.post(
    "/webhooks/wearables",
    response_model=PerformanceWearableWebhookRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_performance_wearable_webhook_route(
    request: Request,
    payload: PerformanceWearableWebhookCreate,
    x_afrolete_performance_timestamp: str | None = Header(
        default=None,
        alias="X-Afrolete-Performance-Timestamp",
    ),
    x_afrolete_performance_signature: str | None = Header(
        default=None,
        alias="X-Afrolete-Performance-Signature",
    ),
    db: AsyncSession = Depends(get_db),
) -> PerformanceWearableWebhookRead:
    signature_required, signature_validated = await validate_performance_wearable_webhook_signature(
        await request.body(),
        x_afrolete_performance_timestamp,
        x_afrolete_performance_signature,
    )
    return PerformanceWearableWebhookRead(
        **await ingest_performance_wearable_webhook(
            db,
            payload,
            signature_required=signature_required,
            signature_validated=signature_validated,
        )
    )


@router.post(
    "/wearable-connections",
    response_model=PerformanceWearableConnectionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_wearable_connection_route(
    payload: PerformanceWearableConnectionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceWearableConnectionRead:
    return to_wearable_connection_read(
        await create_wearable_provider_connection(db, identity, payload, authz)
    )


@router.get("/wearable-connections", response_model=list[PerformanceWearableConnectionRead])
async def list_wearable_connections_route(
    organization_id: UUID = Query(),
    athlete_profile_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[PerformanceWearableConnectionRead]:
    return [
        to_wearable_connection_read(connection)
        for connection in await list_wearable_provider_connections(
            db,
            identity,
            organization_id,
            authz,
            athlete_profile_id,
        )
    ]


@router.post(
    "/wearable-connections/{connection_id}/sync-runs",
    response_model=PerformanceWearableSyncRunRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_wearable_connection_sync_route(
    connection_id: UUID,
    payload: PerformanceWearableSyncRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceWearableSyncRunRead:
    return to_wearable_sync_run_read(
        await run_wearable_provider_sync(db, identity, connection_id, payload, authz)
    )


@router.get(
    "/wearable-connections/{connection_id}/sync-runs",
    response_model=list[PerformanceWearableSyncRunRead],
)
async def list_wearable_connection_sync_runs_route(
    connection_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[PerformanceWearableSyncRunRead]:
    return [
        to_wearable_sync_run_read(run)
        for run in await list_wearable_provider_sync_runs(db, identity, connection_id, authz)
    ]


@router.post(
    "/hardware-kits",
    response_model=PerformanceHardwareKitRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance_hardware_kit_route(
    payload: PerformanceHardwareKitCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceHardwareKitRead:
    return to_hardware_kit_read(await create_performance_hardware_kit(db, identity, payload, authz))


@router.get("/hardware-kits", response_model=list[PerformanceHardwareKitRead])
async def list_performance_hardware_kits_route(
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[PerformanceHardwareKitRead]:
    return [
        to_hardware_kit_read(kit)
        for kit in await list_performance_hardware_kits(db, identity, organization_id, authz, sport=sport)
    ]


@router.post(
    "/hardware-devices",
    response_model=PerformanceHardwareDeviceRead,
    status_code=status.HTTP_201_CREATED,
)
async def provision_performance_hardware_device_route(
    payload: PerformanceHardwareDeviceCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceHardwareDeviceRead:
    return to_hardware_device_read(await provision_performance_hardware_device(db, identity, payload, authz))


@router.get("/hardware-devices", response_model=list[PerformanceHardwareDeviceRead])
async def list_performance_hardware_devices_route(
    organization_id: UUID = Query(),
    kit_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[PerformanceHardwareDeviceRead]:
    return [
        to_hardware_device_read(device)
        for device in await list_performance_hardware_devices(db, identity, organization_id, authz, kit_id=kit_id)
    ]


@router.post(
    "/hardware-devices/{device_id}/sync-runs",
    response_model=PerformanceHardwareSyncRunRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_performance_hardware_sync_route(
    device_id: UUID,
    payload: PerformanceHardwareSyncRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceHardwareSyncRunRead:
    return PerformanceHardwareSyncRunRead(
        **await run_performance_hardware_sync(db, identity, device_id, payload, authz)
    )


@router.get(
    "/hardware-devices/{device_id}/sync-runs",
    response_model=list[PerformanceHardwareSyncRunRead],
)
async def list_performance_hardware_sync_runs_route(
    device_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[PerformanceHardwareSyncRunRead]:
    return [
        PerformanceHardwareSyncRunRead(**run)
        for run in await list_performance_hardware_sync_runs(db, identity, device_id, authz)
    ]


@router.post(
    "/wearable-connections/{connection_id}/webhook-registration",
    response_model=PerformanceWearableWebhookRegistrationRead,
)
async def register_wearable_connection_webhook_route(
    connection_id: UUID,
    payload: PerformanceWearableWebhookRegistrationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceWearableWebhookRegistrationRead:
    result = await register_wearable_provider_webhook(db, identity, connection_id, payload, authz)
    return PerformanceWearableWebhookRegistrationRead(
        connection=to_wearable_connection_read(result["connection"]),
        status=result["status"],
        registered=result["registered"],
        provider_status_code=result["provider_status_code"],
        registration_payload_hash=result["registration_payload_hash"],
        message=result["message"],
    )


@router.post(
    "/wearable-connections/{connection_id}/oauth/start",
    response_model=PerformanceWearableOAuthStartRead,
)
async def start_wearable_connection_oauth_route(
    connection_id: UUID,
    payload: PerformanceWearableOAuthStartCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceWearableOAuthStartRead:
    return PerformanceWearableOAuthStartRead(
        **await start_wearable_provider_oauth(db, identity, connection_id, payload, authz)
    )


@router.post(
    "/wearable-connections/{connection_id}/oauth/callback",
    response_model=PerformanceWearableOAuthCallbackRead,
)
async def complete_wearable_connection_oauth_route(
    connection_id: UUID,
    payload: PerformanceWearableOAuthCallbackCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceWearableOAuthCallbackRead:
    result = await complete_wearable_provider_oauth(db, identity, connection_id, payload, authz)
    return PerformanceWearableOAuthCallbackRead(
        connection=to_wearable_connection_read(result["connection"]),
        status=result["status"],
        message=result["message"],
        authorization_code_ref=result["authorization_code_ref"],
    )


@router.post(
    "/wearable-connections/{connection_id}/oauth/refresh",
    response_model=PerformanceWearableTokenRefreshRead,
)
async def refresh_wearable_connection_token_route(
    connection_id: UUID,
    payload: PerformanceWearableTokenRefreshCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceWearableTokenRefreshRead:
    result = await refresh_wearable_provider_token(db, identity, connection_id, payload, authz)
    return PerformanceWearableTokenRefreshRead(
        connection=to_wearable_connection_read(result["connection"]),
        status=result["status"],
        message=result["message"],
        access_token_ref=result["access_token_ref"],
        refresh_token_rotated=result["refresh_token_rotated"],
    )


@router.patch(
    "/observations/{observation_id}/review",
    response_model=PerformanceObservationRead,
)
async def review_observation_route(
    observation_id: UUID,
    payload: PerformanceObservationReviewCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceObservationRead:
    return to_observation_read(
        await review_observation(db, identity, observation_id, payload, authz)
    )


@router.patch(
    "/assessments/{assessment_id}/review",
    response_model=AthleteAssessmentRead,
)
async def review_assessment_route(
    assessment_id: UUID,
    payload: AthleteAssessmentReviewCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthleteAssessmentRead:
    return to_assessment_read(await review_assessment(db, identity, assessment_id, payload, authz))


@router.patch(
    "/assessments/{assessment_id}/review-assignment",
    response_model=AthleteAssessmentRead,
)
async def update_assessment_review_assignment_route(
    assessment_id: UUID,
    payload: AthleteAssessmentReviewAssignmentUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthleteAssessmentRead:
    return to_assessment_read(
        await update_assessment_review_assignment(db, identity, assessment_id, payload, authz)
    )


@router.post(
    "/assessments/review-escalations",
    response_model=PerformanceAssessmentReviewEscalationRunRead,
)
async def run_assessment_review_escalations_route(
    organization_id: UUID = Query(),
    limit: int = Query(default=25, ge=1, le=100),
    horizon_hours: int = Query(default=24, ge=0, le=168),
    repeat_after_hours: int = Query(default=24, ge=1, le=168),
    dry_run: bool = Query(default=False),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceAssessmentReviewEscalationRunRead:
    return await run_assessment_review_escalations(
        db,
        identity,
        organization_id,
        authz,
        limit=limit,
        horizon_hours=horizon_hours,
        repeat_after_hours=repeat_after_hours,
        dry_run=dry_run,
    )


@router.get(
    "/assessments/review-queue",
    response_model=list[AthleteAssessmentReviewQueueItemRead],
)
async def list_assessment_review_queue_route(
    organization_id: UUID = Query(),
    limit: int = Query(default=25, ge=1, le=100),
    assignment: str = Query(default="all", pattern="^(all|mine|unassigned|assigned)$"),
    sla: str = Query(default="all", pattern="^(all|overdue|due_soon|on_track)$"),
    priority: str = Query(default="all", pattern="^(all|low|normal|high|urgent)$"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[AthleteAssessmentReviewQueueItemRead]:
    rows = await list_assessment_review_queue(
        db,
        identity,
        organization_id,
        authz,
        limit=limit,
        assignment=assignment,
        sla=sla,
        priority=priority,
    )
    return [
        AthleteAssessmentReviewQueueItemRead(
            assessment=to_assessment_read(assessment),
            athlete_person_id=athlete_profile.person_id,
            athlete_name=person.display_name,
            review_assigned_to_name=assignee.display_name if assignee is not None else None,
            review_sla_state=assessment_review_sla_state(assessment),
            review_age_hours=assessment_review_age_hours(assessment),
        )
        for assessment, athlete_profile, person, assignee in rows
    ]


@router.get(
    "/assessments/review-summary",
    response_model=AssessmentReviewQueueSummaryRead,
)
async def assessment_review_queue_summary_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AssessmentReviewQueueSummaryRead:
    return await assessment_review_queue_summary(db, identity, organization_id, authz)


@router.get(
    "/athletes/{athlete_profile_id}/observations",
    response_model=list[PerformanceObservationRead],
)
async def list_observations_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceObservationRead]:
    return [
        to_observation_read(observation)
        for observation in await list_observations(db, organization_id, athlete_profile_id)
    ]


@router.post(
    "/athletes/{athlete_profile_id}/assessments",
    response_model=AthleteAssessmentRead,
    status_code=201,
)
async def create_assessment_route(
    athlete_profile_id: UUID,
    payload: AthleteAssessmentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthleteAssessmentRead:
    return to_assessment_read(
        await create_assessment(db, identity, athlete_profile_id, payload, authz)
    )


@router.get(
    "/athletes/{athlete_profile_id}/assessments",
    response_model=list[AthleteAssessmentRead],
)
async def list_assessments_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AthleteAssessmentRead]:
    return [
        to_assessment_read(assessment)
        for assessment in await list_assessments(db, organization_id, athlete_profile_id)
    ]


@router.get(
    "/athletes/{athlete_profile_id}/summary",
    response_model=AthletePerformanceSummaryRead,
)
async def performance_summary_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> AthletePerformanceSummaryRead:
    score, observation_count, assessment_count, latest_assessment_id, rating = (
        await performance_summary(db, organization_id, athlete_profile_id)
    )
    return AthletePerformanceSummaryRead(
        athlete_profile_id=athlete_profile_id,
        latest_overall_score=score,
        observation_count=observation_count,
        assessment_count=assessment_count,
        latest_assessment_id=latest_assessment_id,
        rating=rating,
    )


@router.post(
    "/athletes/{athlete_profile_id}/pathway-projections",
    response_model=AthletePathwayProjectionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_athlete_pathway_projection_route(
    athlete_profile_id: UUID,
    payload: AthletePathwayProjectionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthletePathwayProjectionRead:
    return await create_athlete_pathway_projection(
        db,
        identity,
        athlete_profile_id,
        payload,
        authz,
    )


@router.get(
    "/athletes/{athlete_profile_id}/pathway-projections",
    response_model=list[AthletePathwayProjectionRead],
)
async def list_athlete_pathway_projections_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AthletePathwayProjectionRead]:
    return await list_athlete_pathway_projections(db, organization_id, athlete_profile_id)


@router.get("/benchmarks", response_model=list[PerformanceMetricBenchmarkRead])
async def performance_benchmarks_route(
    organization_id: UUID = Query(),
    athlete_profile_id: UUID | None = Query(default=None),
    sport: str | None = Query(default=None),
    cohort_scope: str = Query(default="tenant"),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceMetricBenchmarkRead]:
    return [
        PerformanceMetricBenchmarkRead(**benchmark)
        for benchmark in await performance_metric_benchmarks(
            db,
            organization_id,
            athlete_profile_id=athlete_profile_id,
            sport=sport,
            cohort_scope=cohort_scope,
        )
    ]


@router.get(
    "/athletes/{athlete_profile_id}/benchmarks",
    response_model=list[PerformanceMetricBenchmarkRead],
)
async def athlete_performance_benchmarks_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    cohort_scope: str = Query(default="tenant"),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceMetricBenchmarkRead]:
    return [
        PerformanceMetricBenchmarkRead(**benchmark)
        for benchmark in await performance_metric_benchmarks(
            db,
            organization_id,
            athlete_profile_id=athlete_profile_id,
            sport=sport,
            cohort_scope=cohort_scope,
        )
    ]


@router.get(
    "/athletes/{athlete_profile_id}/cohort-comparisons",
    response_model=list[PerformanceCohortComparisonRead],
)
async def athlete_performance_cohort_comparisons_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceCohortComparisonRead]:
    return [
        PerformanceCohortComparisonRead(**comparison)
        for comparison in await performance_cohort_comparisons(
            db,
            organization_id,
            athlete_profile_id,
            sport=sport,
        )
    ]


@router.get(
    "/athletes/{athlete_profile_id}/trends",
    response_model=list[PerformanceMetricTrendRead],
)
async def athlete_performance_trends_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    category: MetricCategory | None = Query(default=None),
    metric_code: str | None = Query(default=None),
    period_start: date | None = Query(default=None),
    period_end: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceMetricTrendRead]:
    return [
        PerformanceMetricTrendRead(**trend)
        for trend in await performance_metric_trends(
            db,
            organization_id,
            athlete_profile_id,
            sport=sport,
            category=category,
            metric_code=metric_code,
            period_start=period_start,
            period_end=period_end,
        )
    ]


@router.get(
    "/athletes/{athlete_profile_id}/trend-series",
    response_model=list[PerformanceMetricTrendSeriesRead],
)
async def athlete_performance_trend_series_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    limit_per_metric: int = Query(default=12, ge=2, le=50),
    category: MetricCategory | None = Query(default=None),
    metric_code: str | None = Query(default=None),
    period_start: date | None = Query(default=None),
    period_end: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceMetricTrendSeriesRead]:
    return [
        PerformanceMetricTrendSeriesRead(**series)
        for series in await performance_metric_trend_series(
            db,
            organization_id,
            athlete_profile_id,
            sport=sport,
            limit_per_metric=limit_per_metric,
            category=category,
            metric_code=metric_code,
            period_start=period_start,
            period_end=period_end,
        )
    ]


@router.get(
    "/athletes/{athlete_profile_id}/forecast-scenarios",
    response_model=list[PerformanceForecastScenarioRead],
)
async def athlete_performance_forecast_scenarios_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceForecastScenarioRead]:
    return [
        PerformanceForecastScenarioRead(**scenario)
        for scenario in await performance_forecast_scenarios(
            db,
            organization_id,
            athlete_profile_id,
            sport=sport,
        )
    ]


@router.get(
    "/athletes/{athlete_profile_id}/forecast-scenarios/what-if",
    response_model=list[PerformanceForecastWhatIfRead],
)
async def athlete_performance_forecast_what_if_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    category: MetricCategory | None = Query(default=None),
    metric_code: str | None = Query(default=None),
    training_adjustment_percent: float = Query(default=0.0, ge=-50, le=50),
    readiness_score: int = Query(default=70, ge=0, le=100),
    horizon: int = Query(default=4, ge=1, le=8),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceForecastWhatIfRead]:
    return [
        PerformanceForecastWhatIfRead(**scenario)
        for scenario in await performance_forecast_what_if_scenarios(
            db,
            organization_id,
            athlete_profile_id,
            sport=sport,
            category=category,
            metric_code=metric_code,
            training_adjustment_percent=training_adjustment_percent,
            readiness_score=readiness_score,
            horizon=horizon,
        )
    ]


@router.get(
    "/athletes/{athlete_profile_id}/injury-risk",
    response_model=PerformanceInjuryRiskRead,
)
async def athlete_performance_injury_risk_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> PerformanceInjuryRiskRead:
    return PerformanceInjuryRiskRead(
        **await performance_injury_risk(db, organization_id, athlete_profile_id)
    )


@router.post(
    "/athletes/{athlete_profile_id}/injury-risk/alerts",
    response_model=PerformanceInjuryRiskAlertRead,
)
async def athlete_performance_injury_risk_alert_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    threshold_score: int = Query(default=65, ge=0, le=100),
    repeat_after_hours: int = Query(default=24, ge=0, le=720),
    channels: list[CommunicationChannel] | None = Query(default=None),
    dry_run: bool = Query(default=False),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceInjuryRiskAlertRead:
    result = await send_performance_injury_risk_alert(
        db,
        identity,
        organization_id,
        athlete_profile_id,
        authz,
        threshold_score=threshold_score,
        dry_run=dry_run,
        repeat_after_hours=repeat_after_hours,
        channels=channels,
    )
    return PerformanceInjuryRiskAlertRead(
        **{
            **result,
            "risk": PerformanceInjuryRiskRead(**result["risk"]),
        }
    )


@router.post(
    "/injury-risk/alert-scans",
    response_model=PerformanceInjuryRiskAlertRunRead,
)
async def run_performance_injury_risk_alert_scan_route(
    organization_id: UUID = Query(),
    limit: int = Query(default=50, ge=1, le=250),
    threshold_score: int = Query(default=65, ge=0, le=100),
    repeat_after_hours: int = Query(default=24, ge=0, le=720),
    channels: list[CommunicationChannel] | None = Query(default=None),
    dry_run: bool = Query(default=False),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceInjuryRiskAlertRunRead:
    return await run_performance_injury_risk_alert_scan(
        db,
        identity,
        organization_id,
        authz,
        limit=limit,
        threshold_score=threshold_score,
        repeat_after_hours=repeat_after_hours,
        channels=channels,
        dry_run=dry_run,
    )


@router.post(
    "/athletes/{athlete_profile_id}/goals",
    response_model=PerformanceGoalRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance_goal_route(
    athlete_profile_id: UUID,
    payload: PerformanceGoalCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceGoalRead:
    return to_goal_read(await create_performance_goal(db, identity, athlete_profile_id, payload, authz))


@router.get(
    "/athletes/{athlete_profile_id}/goals",
    response_model=list[PerformanceGoalRead],
)
async def list_performance_goals_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceGoalRead]:
    return [
        to_goal_read(goal)
        for goal in await list_performance_goals(db, organization_id, athlete_profile_id)
    ]


@router.get(
    "/athletes/{athlete_profile_id}/awards",
    response_model=list[PerformanceAchievementAwardRead],
)
async def list_performance_awards_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceAchievementAwardRead]:
    return [
        to_award_read(award)
        for award in await list_performance_awards(db, organization_id, athlete_profile_id)
    ]


@router.post(
    "/athletes/{athlete_profile_id}/achievements/evaluate",
    response_model=PerformanceAchievementRunRead,
)
async def evaluate_performance_achievements_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> PerformanceAchievementRunRead:
    result = await evaluate_performance_achievements(
        db,
        identity,
        organization_id,
        athlete_profile_id,
        authz,
    )
    return PerformanceAchievementRunRead(
        organization_id=result["organization_id"],
        athlete_profile_id=result["athlete_profile_id"],
        evaluated_goals=result["evaluated_goals"],
        awarded_count=result["awarded_count"],
        updated_goals=result["updated_goals"],
        awards=[to_award_read(award) for award in result["awards"]],
    )
