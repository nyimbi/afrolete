from base64 import b64decode
from binascii import Error as Base64Error
import csv
from datetime import UTC, date, datetime, timedelta
import hmac
import hashlib
import httpx
import io
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from secrets import token_urlsafe
from statistics import pstdev
from urllib.parse import urlencode
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.communication import CommunicationMessage, MessageRecipient
from app.models.enums import (
    AgentKind,
    CommunicationChannel,
    CommunicationMessageType,
    CommunicationScopeType,
    MessageDeliveryStatus,
    AssociationLevel,
    MemberSubjectType,
    MembershipRole,
    MetricCategory,
    MetricSource,
    MetricVerificationStatus,
    RosterStatus,
    SafeguardingIncidentStatus,
    SafeguardingIncidentType,
    TrainingPlanStatus,
    WeatherAlertLevel,
)
from app.models.assets import Facility
from app.models.competition import Competition
from app.models.event import Event, EventWeatherAssessment, SafeguardingIncident
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.performance import (
    AthleteAssessment,
    AthletePathwayProjection,
    AthletePerformanceObservation,
    OppositionScoutingReport,
    OppositionScoutingVideoAsset,
    PerformanceAchievementAward,
    PerformanceGoal,
    PerformanceHardwareDevice,
    PerformanceHardwareKit,
    PerformanceHardwareSyncRun,
    PerformanceHighlightReel,
    PerformanceHighlightReelExport,
    PerformanceMatchAnalysisReport,
    PerformanceMatchPlayerGuidancePublishAudit,
    PerformanceMatchPitchCalibration,
    PerformanceMatchTrackingIdentityReview,
    PerformanceMatchTrackingProviderIngestEvent,
    PerformanceMatchTrackingRun,
    PerformanceMatchTrackingSample,
    PerformanceMetricDefinition,
    PerformanceForecastValidationRun,
    PerformanceMovementReferenceProfile,
    PerformanceModelExtractionBenchmarkCase,
    PerformanceModelExtractionBenchmarkDataset,
    PerformanceVideoAnnotation,
    PerformanceVideoAsset,
    PerformanceVideoPoseSample,
    PerformanceWearableIngestEvent,
    PerformanceWearableProviderConnection,
    PerformanceWearableProviderSyncRun,
)
from app.models.team import AthleteProfile, Team, TeamRosterEntry
from app.models.training import TrainingPlan, TrainingPlanItem, TrainingSessionFeedback, TrainingSessionPlan
from app.schemas.performance import (
    AssessmentReviewLoadRead,
    AssessmentReviewQueueSummaryRead,
    AthleteAssessmentCreate,
    AthletePathwayProjectionCreate,
    AthletePathwayProjectionRead,
    AthleteAssessmentReviewAssignmentUpdate,
    AthleteAssessmentReviewCreate,
    PerformanceAssessmentReviewEscalationRunRead,
    PerformanceInjuryRiskAlertRunRead,
    MetricDefinitionCreate,
    OppositionScoutingReportCreate,
    OppositionScoutingVideoUploadCreate,
    PerformanceAchievementWorkerRunRead,
    PerformanceForecastValidationWorkerRunRead,
    PerformanceGoalCreate,
    PerformanceForecastValidationRunCreate,
    PerformanceHardwareDeviceCreate,
    PerformanceHardwareKitCreate,
    PerformanceHardwareSyncRunCreate,
    PerformanceHighlightReelCreate,
    PerformanceHighlightReelExportCreate,
    PerformanceIngestionCreate,
    PerformanceModelExtractionBulkReviewCreate,
    PerformanceMatchAnalysisReportCreate,
    PerformanceMatchPlayerGuidancePublishCreate,
    PerformanceModelExtractionBenchmarkCaseCreate,
    PerformanceModelExtractionBenchmarkDatasetCreate,
    PerformanceModelExtractionBenchmarkRunCreate,
    PerformanceMatchPitchCalibrationCreate,
    PerformanceMatchTrackingIdentityReviewCreate,
    PerformanceMatchTrackingProviderDetection,
    PerformanceMatchTrackingProviderFrame,
    PerformanceMatchTrackingProviderImportCreate,
    PerformanceMatchTrackingProviderIngestReprocessCreate,
    PerformanceMatchTrackingProviderWebhookCreate,
    PerformanceMatchTrackingRunCreate,
    PerformanceMatchTrackingSampleCreate,
    PlayerMatchTrainingFollowupCreate,
    PerformanceMovementReferenceProfileCreate,
    PerformanceObservationCreate,
    PerformanceObservationReviewCreate,
    PerformancePoseGaitAnalysisCreate,
    PerformanceVideoPoseSampleBatchCreate,
    PerformanceVideoPoseProcessingCreate,
    PerformanceVideoAnnotationCreate,
    PerformanceVideoCoachingCreate,
    PerformanceVideoUploadCreate,
    PerformanceWearableConnectionCreate,
    PerformanceWearableOAuthCallbackCreate,
    PerformanceWearableProviderTokenResponse,
    PerformanceWearableOAuthStartCreate,
    PerformanceWearablePullRetryWorkerRunRead,
    PerformanceWearableSyncRunCreate,
    PerformanceWearableTokenRefreshCreate,
    PerformanceWearableWebhookCreate,
    PerformanceWearableWebhookRegistrationCreate,
    PlayerSelfAssessmentCreate,
)
from app.schemas.agent import AgentTaskCreate
from app.core.config import Settings, get_settings
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.agents import queue_agent_task
from app.services.communications import (
    create_message_for_recipients,
    destination_for_channel,
    guardian_person_ids,
    initial_delivery_status,
)
from app.services.secrets import resolve_secret
from app.services.storage.objects import get_object, put_object


async def ensure_manage_performance(
    authz: AuthorizationService,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> None:
    allowed = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage_roster",
        subject_type="user",
        subject_id=str(identity.user_id),
    ) or await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def ensure_assignment_person(
    db: AsyncSession,
    organization_id: UUID,
    person_id: UUID,
) -> Person:
    person = await db.get(Person, person_id)
    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == person_id,
            Membership.status == "active",
        )
    )
    if person is None or membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return person


def self_assessment_priority(overall_score: float, perceived_exertion: float) -> str:
    if perceived_exertion >= 9 or overall_score < 55:
        return "urgent"
    if perceived_exertion >= 8 or overall_score < 65:
        return "high"
    return "normal"


def as_utc_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def as_naive_utc_datetime(value: datetime | None) -> datetime | None:
    utc_value = as_utc_datetime(value)
    if utc_value is None:
        return None
    return utc_value.replace(tzinfo=None)


async def create_metric_definition(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: MetricDefinitionCreate,
    authz: AuthorizationService,
) -> PerformanceMetricDefinition:
    organization = await db.get(Organization, payload.organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    await ensure_manage_performance(authz, identity, payload.organization_id)

    existing = await db.scalar(
        select(PerformanceMetricDefinition).where(
            PerformanceMetricDefinition.organization_id == payload.organization_id,
            PerformanceMetricDefinition.sport == payload.sport,
            PerformanceMetricDefinition.code == payload.code,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Metric code exists")

    metric = PerformanceMetricDefinition(**payload.model_dump())
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return metric


async def list_metric_definitions(
    db: AsyncSession,
    organization_id: UUID,
    sport: str | None = None,
) -> list[PerformanceMetricDefinition]:
    statement = select(PerformanceMetricDefinition).where(
        PerformanceMetricDefinition.organization_id == organization_id
    )
    if sport is not None:
        statement = statement.where(PerformanceMetricDefinition.sport == sport)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    PerformanceMetricDefinition.category,
                    PerformanceMetricDefinition.name,
                )
            )
        ).all()
    )


async def create_observation(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: PerformanceObservationCreate,
    authz: AuthorizationService,
) -> AthletePerformanceObservation:
    athlete_profile = await get_athlete_profile(db, athlete_profile_id, payload.organization_id)
    await ensure_manage_performance(authz, identity, payload.organization_id)
    metric = await db.get(PerformanceMetricDefinition, payload.metric_definition_id)
    if metric is None or metric.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    if payload.event_id is not None:
        event = await db.get(Event, payload.event_id)
        if event is None or event.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    observation = AthletePerformanceObservation(
        athlete_profile_id=athlete_profile.id,
        recorded_by_person_id=identity.person_id,
        observed_at=payload.observed_at or datetime.now(UTC),
        **payload.model_dump(exclude={"observed_at"}),
    )
    db.add(observation)
    await db.commit()
    await db.refresh(observation)
    return observation


async def ingest_performance_evidence(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: PerformanceIngestionCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    athlete_profile = await get_athlete_profile(db, payload.athlete_profile_id, payload.organization_id)
    await ensure_manage_performance(authz, identity, payload.organization_id)
    metric = await db.get(PerformanceMetricDefinition, payload.metric_definition_id)
    if metric is None or metric.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    if payload.event_id is not None:
        event = await db.get(Event, payload.event_id)
        if event is None or event.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    parsed = parse_performance_evidence(payload, metric)
    model_assist = await model_assisted_performance_extraction(get_settings(), payload, metric, parsed)
    model_applied = False
    if should_apply_model_extraction(parsed, model_assist):
        parsed = apply_model_extraction(parsed, model_assist)
        model_applied = True
    value = float(parsed["value"])
    confidence = float(parsed["confidence"])
    parser_warnings = list(parsed["warnings"])
    model_note = (
        f"Model: {model_assist['model_policy']} "
        f"({float(model_assist['confidence']):.2f}, {'applied' if model_applied else 'evaluated'}). "
        if model_assist
        else ""
    )
    observation = AthletePerformanceObservation(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile.id,
        metric_definition_id=metric.id,
        event_id=payload.event_id,
        recorded_by_person_id=identity.person_id,
        value=value,
        raw_value=evidence_raw_value(payload.evidence_text, value),
        observed_at=payload.observed_at or parsed["observed_at"] or datetime.now(UTC),
        source=payload.source,
        confidence=confidence,
        verification_status=MetricVerificationStatus.PENDING_REVIEW,
        notes=(
            f"Ingested from {payload.source.value} evidence {payload.evidence_ref}. "
            f"Metric: {metric.name}. Parser: {parsed['method']}. "
            f"{model_note}"
            f"{'Warnings: ' + '; '.join(parser_warnings) + '. ' if parser_warnings else ''}"
            "Review before promoting to verified."
        ),
    )
    db.add(observation)
    await db.commit()
    await db.refresh(observation)
    return {
        "observation": observation,
        "evidence_ref": payload.evidence_ref,
        "source_provider": parsed["source_provider"],
        "extractor": extractor_name(payload.source),
        "confidence": confidence,
        "review_required": True,
        "summary": (
            f"Extracted {metric.name}={value:g}{' ' + metric.unit if metric.unit else ''} "
            f"from {payload.source.value} evidence via {parsed['method']}."
        ),
        "parser_method": parsed["method"],
        "parser_confidence_reason": parsed["confidence_reason"],
        "parser_warnings": parser_warnings,
        "parsed_fields": parsed["fields"],
        "model_assisted": model_applied,
        "model_policy": model_assist["model_policy"] if model_assist else None,
        "model_confidence": model_assist["confidence"] if model_assist else None,
        "model_summary": model_assist["summary"] if model_assist else None,
        "model_evaluation": model_evaluation(parsed, model_assist, model_applied),
    }


async def analyze_video_for_coaching(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: PerformanceVideoCoachingCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    athlete_profile = await get_athlete_profile(db, athlete_profile_id, payload.organization_id)
    await ensure_manage_performance(authz, identity, payload.organization_id)
    if payload.event_id is not None:
        event = await db.get(Event, payload.event_id)
        if event is None or event.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    sport = payload.sport.strip().lower()
    specs = video_coaching_metric_specs(sport)
    metrics = await ensure_video_coaching_metrics(db, payload.organization_id, sport, specs)
    await db.flush()

    observed_at = as_naive_utc_datetime(payload.observed_at) or datetime.now(UTC).replace(tzinfo=None)
    metric_cards: list[dict[str, object]] = []
    observations: list[AthletePerformanceObservation] = []
    for spec, metric in zip(specs, metrics, strict=True):
        extracted_value = extract_metric_specific_text_value(payload.evidence_text, metric)
        value = video_coaching_score(payload.evidence_text, spec, extracted_value)
        confidence = video_coaching_confidence(payload.evidence_text, extracted_value)
        evidence_summary = (
            f"Detected {metric.name} at {value:g}/10 from clip evidence."
            if extracted_value is not None
            else f"Estimated {metric.name} at {value:g}/10 from deterministic video cues."
        )
        observation = AthletePerformanceObservation(
            organization_id=payload.organization_id,
            athlete_profile_id=athlete_profile.id,
            metric_definition_id=metric.id,
            event_id=payload.event_id,
            recorded_by_person_id=identity.person_id,
            value=value,
            raw_value=f"{value:g}/10",
            observed_at=observed_at,
            source=MetricSource.VIDEO_ANALYSIS,
            confidence=confidence,
            verification_status=MetricVerificationStatus.PENDING_REVIEW,
            notes=(
                f"AI video coaching analysis for {payload.video_uri}. "
                f"Provider: {payload.provider}. Focus: {payload.analysis_focus}. "
                f"{evidence_summary} Cue: {spec['cue']} Review before applying the plan."
            ),
        )
        db.add(observation)
        observations.append(observation)
        metric_cards.append(
            {
                "metric_definition_id": metric.id,
                "metric_code": metric.code,
                "metric_name": metric.name,
                "category": metric.category,
                "value": value,
                "unit": metric.unit,
                "confidence": confidence,
                "coaching_cue": spec["cue"],
                "evidence_summary": evidence_summary,
            }
        )

    scores_by_category = video_scores_by_category(metric_cards)
    weakest = sorted(metric_cards, key=lambda card: float(card["value"]))[:2]
    confidence = round(
        sum(float(card["confidence"]) for card in metric_cards) / len(metric_cards),
        2,
    )
    summary = video_coaching_summary(payload, metric_cards, confidence)
    coaching_plan = video_coaching_plan(weakest)
    assessment = AthleteAssessment(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile.id,
        event_id=payload.event_id,
        assessed_by_person_id=identity.person_id,
        assessed_at=observed_at,
        physical_score=scores_by_category["physical"],
        technical_score=scores_by_category["technical"],
        tactical_score=scores_by_category["tactical"],
        mental_score=scores_by_category["mental"],
        overall_score=round(
            scores_by_category["physical"] * 0.25
            + scores_by_category["technical"] * 0.35
            + scores_by_category["tactical"] * 0.25
            + scores_by_category["mental"] * 0.15,
            2,
        ),
        perceived_exertion=None,
        effort_rating=None,
        summary=summary,
        recommendations=coaching_plan,
        review_due_at=datetime.now(UTC) + timedelta(hours=48),
        review_priority="high" if any(float(card["value"]) < 6.5 for card in weakest) else "normal",
        verification_status=MetricVerificationStatus.PENDING_REVIEW,
    )
    db.add(assessment)
    await db.commit()
    for observation in observations:
        await db.refresh(observation)
    await db.refresh(assessment)
    return {
        "organization_id": payload.organization_id,
        "athlete_profile_id": athlete_profile.id,
        "event_id": payload.event_id,
        "sport": sport,
        "video_uri": payload.video_uri,
        "clip_label": payload.clip_label,
        "model_policy": "afrolete-video-coach-v1",
        "confidence": confidence,
        "summary": summary,
        "coaching_plan": coaching_plan,
        "review_required": True,
        "observations": observations,
        "assessment": assessment,
        "metrics": metric_cards,
        "next_actions": video_coaching_next_actions(weakest),
    }


async def upload_performance_video_asset(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: PerformanceVideoUploadCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> PerformanceVideoAsset:
    athlete_profile = await get_athlete_profile(db, athlete_profile_id, payload.organization_id)
    await ensure_manage_performance(authz, identity, payload.organization_id)
    if payload.event_id is not None:
        event = await db.get(Event, payload.event_id)
        if event is None or event.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if not payload.content_type.startswith("video/"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Upload must be a video file")

    content = decode_performance_upload_content(payload.content_base64)
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Video file is empty")
    selected_settings = settings or get_settings()
    if len(content) > selected_settings.performance_video_max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Video upload exceeds tenant limit")

    checksum = hashlib.sha256(content).hexdigest()
    safe_name = safe_performance_upload_filename(payload.filename)
    existing = await db.scalar(
        select(PerformanceVideoAsset).where(
            PerformanceVideoAsset.organization_id == payload.organization_id,
            PerformanceVideoAsset.checksum == checksum,
        )
    )
    if existing is not None:
        return existing

    storage_name = f"{checksum[:16]}-{safe_name}"
    relative_path = (
        Path(str(payload.organization_id))
        / str(athlete_profile.id)
        / storage_name
    ).as_posix()
    stored = put_object(
        selected_settings,
        local_root=selected_settings.performance_video_file_dir,
        local_url_prefix=selected_settings.performance_video_file_url_prefix,
        key=relative_path,
        content=content,
        content_type=payload.content_type,
    )
    video_asset = PerformanceVideoAsset(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile.id,
        event_id=payload.event_id,
        uploaded_by_person_id=identity.person_id,
        sport=payload.sport.strip().lower(),
        filename=safe_name,
        content_type=payload.content_type,
        size_bytes=len(content),
        checksum=checksum,
        storage_url=stored.url,
        storage_path=stored.path,
        video_uri=f"performance-video://{payload.organization_id}/{athlete_profile.id}/{checksum[:16]}",
        clip_label=payload.clip_label,
        analysis_focus=payload.analysis_focus,
        duration_seconds=payload.duration_seconds,
        frame_rate=payload.frame_rate,
        frame_width=payload.frame_width,
        frame_height=payload.frame_height,
        status="uploaded",
    )
    db.add(video_asset)
    await db.commit()
    await db.refresh(video_asset)
    return video_asset


async def upload_opposition_scouting_video_asset(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: OppositionScoutingVideoUploadCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> OppositionScoutingVideoAsset:
    await ensure_manage_performance(authz, identity, payload.organization_id)
    await ensure_scouting_scope(db, payload.organization_id, payload.team_id, payload.competition_id, payload.event_id)
    if not payload.content_type.startswith("video/"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Upload must be a video file")
    content = decode_performance_upload_content(payload.content_base64)
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Video file is empty")
    selected_settings = settings or get_settings()
    if len(content) > selected_settings.performance_video_max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Video upload exceeds tenant limit")
    checksum = hashlib.sha256(content).hexdigest()
    existing = await db.scalar(
        select(OppositionScoutingVideoAsset).where(
            OppositionScoutingVideoAsset.organization_id == payload.organization_id,
            OppositionScoutingVideoAsset.checksum == checksum,
        )
    )
    if existing is not None:
        return existing
    safe_name = safe_performance_upload_filename(payload.filename)
    storage_name = f"{checksum[:16]}-{safe_name}"
    relative_path = (Path(str(payload.organization_id)) / "scouting" / storage_name).as_posix()
    stored = put_object(
        selected_settings,
        local_root=selected_settings.performance_video_file_dir,
        local_url_prefix=selected_settings.performance_video_file_url_prefix,
        key=relative_path,
        content=content,
        content_type=payload.content_type,
    )
    video_asset = OppositionScoutingVideoAsset(
        organization_id=payload.organization_id,
        team_id=payload.team_id,
        competition_id=payload.competition_id,
        event_id=payload.event_id,
        uploaded_by_person_id=identity.person_id,
        opponent_name=payload.opponent_name.strip(),
        sport=payload.sport.strip().lower(),
        filename=safe_name,
        content_type=payload.content_type,
        size_bytes=len(content),
        checksum=checksum,
        storage_url=stored.url,
        storage_path=stored.path,
        video_uri=f"opposition-scouting-video://{payload.organization_id}/{checksum[:16]}",
        clip_label=payload.clip_label,
        match_context=payload.match_context,
        analysis_focus=payload.analysis_focus,
        status="uploaded",
    )
    db.add(video_asset)
    await db.commit()
    await db.refresh(video_asset)
    return video_asset


async def list_opposition_scouting_videos(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    team_id: UUID | None = None,
) -> list[OppositionScoutingVideoAsset]:
    await ensure_manage_performance(authz, identity, organization_id)
    statement = select(OppositionScoutingVideoAsset).where(
        OppositionScoutingVideoAsset.organization_id == organization_id
    )
    if team_id is not None:
        statement = statement.where(OppositionScoutingVideoAsset.team_id == team_id)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    OppositionScoutingVideoAsset.analyzed_at.desc().nullslast(),
                    OppositionScoutingVideoAsset.created_at.desc(),
                )
            )
        ).all()
    )


async def create_opposition_scouting_report(
    db: AsyncSession,
    identity: CurrentIdentity,
    video_asset_id: UUID,
    payload: OppositionScoutingReportCreate,
    authz: AuthorizationService,
) -> OppositionScoutingReport:
    video_asset = await get_opposition_scouting_video_asset(db, video_asset_id)
    if video_asset.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    await ensure_manage_performance(authz, identity, video_asset.organization_id)
    await ensure_scouting_scope(
        db,
        video_asset.organization_id,
        payload.team_id or video_asset.team_id,
        payload.competition_id or video_asset.competition_id,
        payload.event_id or video_asset.event_id,
    )
    tracking_run = await latest_match_tracking_run(db, video_asset.id)
    tracking_summary = await match_tracking_run_read(db, tracking_run) if tracking_run is not None else None
    analysis = deterministic_opposition_scouting_analysis(
        opponent_name=video_asset.opponent_name,
        sport=video_asset.sport,
        formation=payload.observed_formation,
        match_context=payload.match_context or video_asset.match_context,
        analysis_focus=payload.analysis_focus or video_asset.analysis_focus,
        evidence_text=payload.evidence_text,
        tracking_summary=tracking_summary,
    )
    now = datetime.now(UTC)
    report = OppositionScoutingReport(
        organization_id=video_asset.organization_id,
        video_asset_id=video_asset.id,
        team_id=payload.team_id or video_asset.team_id,
        competition_id=payload.competition_id or video_asset.competition_id,
        event_id=payload.event_id or video_asset.event_id,
        created_by_person_id=identity.person_id,
        opponent_name=video_asset.opponent_name,
        sport=video_asset.sport,
        match_context=payload.match_context or video_asset.match_context,
        analysis_focus=payload.analysis_focus or video_asset.analysis_focus,
        model_policy="afrolete-opposition-scout-v2" if tracking_summary is not None else "afrolete-opposition-scout-v1",
        confidence=float(analysis["confidence"]),
        formation_detected=str(analysis["formation_detected"]),
        tactical_summary=str(analysis["tactical_summary"]),
        weaknesses_json=json.dumps(analysis["weaknesses"]),
        threats_json=json.dumps(analysis["threats"]),
        recommendations_json=json.dumps(analysis["recommendations"]),
        set_pieces_json=json.dumps(analysis["set_pieces"]),
        status="generated",
        generated_at=now,
    )
    video_asset.status = "scouted"
    video_asset.analyzed_at = now
    db.add(report)
    await db.commit()
    await db.refresh(report)
    await db.refresh(video_asset)
    return report


async def list_opposition_scouting_reports(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    team_id: UUID | None = None,
) -> list[OppositionScoutingReport]:
    await ensure_manage_performance(authz, identity, organization_id)
    statement = select(OppositionScoutingReport).where(OppositionScoutingReport.organization_id == organization_id)
    if team_id is not None:
        statement = statement.where(OppositionScoutingReport.team_id == team_id)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    OppositionScoutingReport.generated_at.desc(),
                    OppositionScoutingReport.created_at.desc(),
                )
            )
        ).all()
    )


async def create_match_pitch_calibration(
    db: AsyncSession,
    identity: CurrentIdentity,
    video_asset_id: UUID,
    payload: PerformanceMatchPitchCalibrationCreate,
    authz: AuthorizationService,
) -> PerformanceMatchPitchCalibration:
    video_asset = await get_opposition_scouting_video_asset(db, video_asset_id)
    if video_asset.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    await ensure_manage_performance(authz, identity, video_asset.organization_id)
    transform = match_pitch_calibration_transform(
        [point.model_dump() for point in payload.points],
        payload.pitch_length_m,
        payload.pitch_width_m,
    )
    calibration = PerformanceMatchPitchCalibration(
        organization_id=video_asset.organization_id,
        video_asset_id=video_asset.id,
        created_by_person_id=identity.person_id,
        name=payload.name,
        calibration_method=payload.calibration_method.strip().lower(),
        pitch_length_m=payload.pitch_length_m,
        pitch_width_m=payload.pitch_width_m,
        quality_score=float(transform["quality_score"]),
        points_json=json.dumps([point.model_dump() for point in payload.points]),
        transform_json=json.dumps(transform),
        status=payload.status,
        notes=payload.notes,
    )
    db.add(calibration)
    await db.commit()
    await db.refresh(calibration)
    return calibration


async def list_match_pitch_calibrations(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    video_asset_id: UUID | None = None,
) -> list[PerformanceMatchPitchCalibration]:
    await ensure_manage_performance(authz, identity, organization_id)
    statement = select(PerformanceMatchPitchCalibration).where(
        PerformanceMatchPitchCalibration.organization_id == organization_id
    )
    if video_asset_id is not None:
        statement = statement.where(PerformanceMatchPitchCalibration.video_asset_id == video_asset_id)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    PerformanceMatchPitchCalibration.created_at.desc(),
                ).limit(25)
            )
        ).all()
    )


async def create_match_tracking_run(
    db: AsyncSession,
    identity: CurrentIdentity,
    video_asset_id: UUID,
    payload: PerformanceMatchTrackingRunCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> dict[str, object]:
    video_asset = await get_opposition_scouting_video_asset(db, video_asset_id)
    if video_asset.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    await ensure_manage_performance(authz, identity, video_asset.organization_id)
    calibration = (
        await get_match_pitch_calibration(db, payload.calibration_id, video_asset.organization_id, video_asset.id)
        if payload.calibration_id is not None
        else None
    )
    pitch_length_m = calibration.pitch_length_m if calibration is not None else payload.pitch_length_m
    pitch_width_m = calibration.pitch_width_m if calibration is not None else payload.pitch_width_m
    selected_settings = settings or get_settings()
    sample_payloads = list(payload.samples)
    source_provider = payload.source_provider.strip().lower()
    model_policy = (payload.model_policy or "afrolete-match-tracking-import-v1").strip()
    warnings = list(payload.quality_warnings)
    if payload.auto_track and not sample_payloads:
        content = get_object(
            selected_settings,
            local_root=selected_settings.performance_video_file_dir,
            key=opposition_scouting_video_object_key(video_asset, selected_settings),
        )
        if hashlib.sha256(content).hexdigest() != video_asset.checksum:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Stored video checksum mismatch")
        extracted = extract_match_tracking_samples_from_video_content(
            content,
            pitch_length_m=pitch_length_m,
            pitch_width_m=pitch_width_m,
            max_frames=payload.max_frames,
            sample_every_seconds=payload.sample_every_seconds,
            min_detection_confidence=payload.min_detection_confidence,
        )
        sample_payloads = list(extracted["samples"])
        source_provider = str(extracted["source_provider"])
        model_policy = str(extracted["model_policy"])
        warnings = list(extracted["warnings"])
    if not sample_payloads:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tracking run requires samples or auto_track=true",
        )
    if payload.replace_existing:
        existing_runs = list(
            (
                await db.scalars(
                    select(PerformanceMatchTrackingRun).where(
                        PerformanceMatchTrackingRun.video_asset_id == video_asset.id
                    )
                )
            ).all()
        )
        if existing_runs:
            run_ids = [run.id for run in existing_runs]
            await db.execute(
                update(PerformanceMatchTrackingProviderIngestEvent)
                .where(PerformanceMatchTrackingProviderIngestEvent.tracking_run_id.in_(run_ids))
                .values(tracking_run_id=None, status="superseded")
            )
            await db.execute(
                delete(PerformanceMatchTrackingSample).where(
                    PerformanceMatchTrackingSample.tracking_run_id.in_(run_ids)
                )
            )
            await db.execute(delete(PerformanceMatchTrackingRun).where(PerformanceMatchTrackingRun.id.in_(run_ids)))
    now = datetime.now(UTC)
    normalized_samples = [
        normalize_match_tracking_sample(item, pitch_length_m, pitch_width_m, calibration=calibration)
        for item in sample_payloads
    ]
    summary = summarize_match_tracking_samples(normalized_samples)
    if warnings:
        summary["warnings"] = warnings
    if payload.provider_metadata:
        summary["provider_metadata"] = payload.provider_metadata
    if calibration is not None:
        summary["calibration_id"] = str(calibration.id)
        summary["calibration_quality_score"] = calibration.quality_score
    summary = enrich_match_tracking_summary(
        summary,
        calibration=calibration,
        source_provider=source_provider,
        model_policy=model_policy,
    )
    run = PerformanceMatchTrackingRun(
        organization_id=video_asset.organization_id,
        video_asset_id=video_asset.id,
        calibration_id=calibration.id if calibration is not None else None,
        team_id=video_asset.team_id,
        event_id=video_asset.event_id,
        created_by_person_id=identity.person_id,
        source_provider=source_provider,
        model_policy=model_policy,
        status="completed",
        pitch_length_m=pitch_length_m,
        pitch_width_m=pitch_width_m,
        sample_count=len(normalized_samples),
        player_count=len(summary["player_metrics"]),
        total_distance_m=float(summary["total_distance_m"]),
        max_speed_mps=float(summary["max_speed_mps"]),
        high_speed_distance_m=float(summary["high_speed_distance_m"]),
        sprint_count=int(summary["sprint_count"]),
        summary_json=json.dumps(summary, default=str),
        started_at=now,
        completed_at=now,
    )
    db.add(run)
    await db.flush()
    db.add_all(
        [
            PerformanceMatchTrackingSample(
                organization_id=video_asset.organization_id,
                tracking_run_id=run.id,
                video_asset_id=video_asset.id,
                track_id=str(item["track_id"]),
                person_id=item.get("person_id"),
                team_label=item.get("team_label"),
                player_label=item.get("player_label"),
                jersey_number=item.get("jersey_number"),
                frame_index=item.get("frame_index"),
                timestamp_seconds=float(item["timestamp_seconds"]),
                x_percent=float(item["x_percent"]),
                y_percent=float(item["y_percent"]),
                x_meters=float(item["x_meters"]),
                y_meters=float(item["y_meters"]),
                speed_mps=item.get("speed_mps"),
                confidence=item.get("confidence"),
                source=str(item.get("source") or "tracking_sample"),
            )
            for item in normalized_samples
        ]
    )
    video_asset.status = "tracked"
    video_asset.analyzed_at = now
    await db.commit()
    await db.refresh(run)
    return await match_tracking_run_read(db, run)


async def create_match_tracking_provider_import(
    db: AsyncSession,
    identity: CurrentIdentity,
    video_asset_id: UUID,
    payload: PerformanceMatchTrackingProviderImportCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    samples = match_tracking_provider_frames_to_samples(
        payload.frames,
        source_provider=payload.source_provider,
    )
    if not samples:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Provider import contained no tracks")
    warnings = list(payload.quality_warnings)
    warnings.append(
        "Provider tracking import preserves external detector confidence; coach review remains required before publishing player decisions."
    )
    return await create_match_tracking_run(
        db,
        identity,
        video_asset_id,
        PerformanceMatchTrackingRunCreate(
            organization_id=payload.organization_id,
            calibration_id=payload.calibration_id,
            source_provider=payload.source_provider,
            model_policy=payload.model_policy,
            pitch_length_m=payload.pitch_length_m,
            pitch_width_m=payload.pitch_width_m,
            replace_existing=payload.replace_existing,
            samples=samples,
            provider_metadata={
                **payload.provider_metadata,
                "frame_count": len(payload.frames),
                "detection_count": sum(len(frame.detections) for frame in payload.frames),
                "ingest_contract": "afrolete-provider-tracking-frames-v1",
            },
            quality_warnings=warnings,
        ),
        authz,
    )


async def ingest_match_tracking_provider_webhook(
    db: AsyncSession,
    payload: PerformanceMatchTrackingProviderWebhookCreate,
    *,
    signature_required: bool,
    signature_validated: bool,
) -> dict[str, object]:
    video_asset = await get_opposition_scouting_video_asset(db, payload.video_asset_id)
    if video_asset.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    provider = normalized_provider_name(payload.source_provider) or payload.source_provider.strip().lower()
    payload_hash = stable_payload_hash(payload.model_dump(mode="json"))
    existing = await db.scalar(
        select(PerformanceMatchTrackingProviderIngestEvent)
        .where(PerformanceMatchTrackingProviderIngestEvent.organization_id == payload.organization_id)
        .where(PerformanceMatchTrackingProviderIngestEvent.video_asset_id == video_asset.id)
        .where(PerformanceMatchTrackingProviderIngestEvent.provider == provider)
        .where(PerformanceMatchTrackingProviderIngestEvent.external_event_id == payload.external_event_id)
    )
    if existing is not None:
        tracking_run = (
            await db.get(PerformanceMatchTrackingRun, existing.tracking_run_id)
            if existing.tracking_run_id is not None
            else None
        )
        return await match_tracking_provider_webhook_result(
            db,
            existing,
            replayed=True,
            tracking_run=tracking_run,
        )

    system_identity = CurrentIdentity(
        user_id=video_asset.uploaded_by_person_id or video_asset.organization_id,
        person_id=video_asset.uploaded_by_person_id or video_asset.organization_id,
        keycloak_sub="system:performance-match-tracking-provider",
        email="system@afrolete.local",
        display_name="AfroLete Match Tracking Provider",
    )
    run = await create_match_tracking_provider_import(
        db,
        system_identity,
        video_asset.id,
        PerformanceMatchTrackingProviderImportCreate(
            organization_id=payload.organization_id,
            calibration_id=payload.calibration_id,
            source_provider=payload.source_provider,
            model_policy=payload.model_policy,
            pitch_length_m=payload.pitch_length_m,
            pitch_width_m=payload.pitch_width_m,
            replace_existing=payload.replace_existing,
            frames=payload.frames,
            provider_metadata={
                **payload.provider_metadata,
                "external_event_id": payload.external_event_id,
                "signature_required": signature_required,
                "signature_validated": signature_validated,
                "ingest_contract": "afrolete-provider-tracking-webhook-v1",
            },
            quality_warnings=payload.quality_warnings,
        ),
        AllowAllAuthorizationService(),
    )
    ingest_event = PerformanceMatchTrackingProviderIngestEvent(
        organization_id=payload.organization_id,
        video_asset_id=video_asset.id,
        tracking_run_id=run["id"],
        team_id=video_asset.team_id,
        event_id=video_asset.event_id,
        provider=provider,
        external_event_id=payload.external_event_id,
        payload_hash=payload_hash,
        payload_json=json.dumps(payload.model_dump(mode="json"), default=str),
        received_at=datetime.now(UTC),
        signature_required=signature_required,
        signature_validated=signature_validated,
        sample_count=int(run["sample_count"]),
        player_count=int(run["player_count"]),
        status="accepted",
    )
    db.add(ingest_event)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existing = await db.scalar(
            select(PerformanceMatchTrackingProviderIngestEvent)
            .where(PerformanceMatchTrackingProviderIngestEvent.organization_id == payload.organization_id)
            .where(PerformanceMatchTrackingProviderIngestEvent.video_asset_id == video_asset.id)
            .where(PerformanceMatchTrackingProviderIngestEvent.provider == provider)
            .where(PerformanceMatchTrackingProviderIngestEvent.external_event_id == payload.external_event_id)
        )
        if existing is None:
            raise
        tracking_run = (
            await db.get(PerformanceMatchTrackingRun, existing.tracking_run_id)
            if existing.tracking_run_id is not None
            else None
        )
        return await match_tracking_provider_webhook_result(
            db,
            existing,
            replayed=True,
            tracking_run=tracking_run,
        )
    await db.refresh(ingest_event)
    tracking_run = await db.get(PerformanceMatchTrackingRun, run["id"])
    return await match_tracking_provider_webhook_result(
        db,
        ingest_event,
        replayed=False,
        tracking_run=tracking_run,
    )


def match_tracking_provider_frames_to_samples(
    frames: list[PerformanceMatchTrackingProviderFrame],
    *,
    source_provider: str,
) -> list[PerformanceMatchTrackingSampleCreate]:
    source = f"{source_provider.strip().lower()}_provider_import"[:80] or "provider_tracking_import"
    samples: list[PerformanceMatchTrackingSampleCreate] = []
    for frame in frames:
        for detection in frame.detections:
            position = match_tracking_provider_detection_position(detection)
            track_id = detection.track_id
            team_label = detection.team_label
            player_label = detection.player_label
            if detection.object_type == "ball":
                team_label = team_label or "ball"
                player_label = player_label or "Ball"
            samples.append(
                PerformanceMatchTrackingSampleCreate(
                    track_id=track_id,
                    person_id=detection.person_id,
                    team_label=team_label,
                    player_label=player_label,
                    jersey_number=detection.jersey_number,
                    frame_index=frame.frame_index,
                    timestamp_seconds=frame.timestamp_seconds,
                    x_percent=position["x_percent"],
                    y_percent=position["y_percent"],
                    x_meters=position["x_meters"],
                    y_meters=position["y_meters"],
                    speed_mps=detection.speed_mps,
                    confidence=detection.confidence,
                    source=detection.source or source,
                )
            )
    samples.sort(key=lambda sample: (sample.timestamp_seconds, sample.track_id, sample.frame_index or 0))
    return samples


def match_tracking_provider_detection_position(
    detection: PerformanceMatchTrackingProviderDetection,
) -> dict[str, float | None]:
    if detection.x_meters is not None and detection.y_meters is not None:
        return {
            "x_percent": detection.x_percent,
            "y_percent": detection.y_percent,
            "x_meters": detection.x_meters,
            "y_meters": detection.y_meters,
        }
    if detection.foot_x_percent is not None and detection.foot_y_percent is not None:
        return {
            "x_percent": detection.foot_x_percent,
            "y_percent": detection.foot_y_percent,
            "x_meters": None,
            "y_meters": None,
        }
    if detection.x_percent is not None and detection.y_percent is not None:
        return {
            "x_percent": detection.x_percent,
            "y_percent": detection.y_percent,
            "x_meters": None,
            "y_meters": None,
        }
    bbox_x = float(detection.bbox_x_percent or 0.0)
    bbox_y = float(detection.bbox_y_percent or 0.0)
    bbox_width = float(detection.bbox_width_percent or 0.0)
    bbox_height = float(detection.bbox_height_percent or 0.0)
    x_percent = bbox_x + bbox_width / 2
    y_percent = bbox_y + (bbox_height / 2 if detection.object_type == "ball" else bbox_height)
    return {
        "x_percent": clamp_percent(x_percent),
        "y_percent": clamp_percent(y_percent),
        "x_meters": None,
        "y_meters": None,
    }


async def list_match_tracking_runs(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    video_asset_id: UUID | None = None,
) -> list[dict[str, object]]:
    await ensure_manage_performance(authz, identity, organization_id)
    statement = select(PerformanceMatchTrackingRun).where(
        PerformanceMatchTrackingRun.organization_id == organization_id
    )
    if video_asset_id is not None:
        statement = statement.where(PerformanceMatchTrackingRun.video_asset_id == video_asset_id)
    runs = list((await db.scalars(statement.order_by(PerformanceMatchTrackingRun.created_at.desc()).limit(25))).all())
    return [await match_tracking_run_read(db, run) for run in runs]


async def downloadable_match_tracking_run_export(
    db: AsyncSession,
    identity: CurrentIdentity,
    tracking_run_id: UUID,
    export_format: str,
    authz: AuthorizationService,
) -> dict[str, object]:
    run = await get_match_tracking_run(db, tracking_run_id)
    await ensure_manage_performance(authz, identity, run.organization_id)
    samples = list(
        (
            await db.scalars(
                select(PerformanceMatchTrackingSample)
                .where(PerformanceMatchTrackingSample.tracking_run_id == run.id)
                .order_by(
                    PerformanceMatchTrackingSample.timestamp_seconds,
                    PerformanceMatchTrackingSample.track_id,
                    PerformanceMatchTrackingSample.frame_index,
                )
            )
        ).all()
    )
    try:
        summary = json.loads(run.summary_json)
    except json.JSONDecodeError:
        summary = {}
    normalized_format = export_format.strip().lower().replace("-", "_")
    if normalized_format in {"json", "full_json", "analysis_json"}:
        content = json.dumps(
            {
                "export_format": "analysis_json",
                "exported_at": datetime.now(UTC).isoformat(),
                "tracking_run": {
                    "id": str(run.id),
                    "organization_id": str(run.organization_id),
                    "video_asset_id": str(run.video_asset_id),
                    "calibration_id": str(run.calibration_id) if run.calibration_id else None,
                    "team_id": str(run.team_id) if run.team_id else None,
                    "event_id": str(run.event_id) if run.event_id else None,
                    "source_provider": run.source_provider,
                    "model_policy": run.model_policy,
                    "status": run.status,
                    "pitch_length_m": run.pitch_length_m,
                    "pitch_width_m": run.pitch_width_m,
                    "sample_count": run.sample_count,
                    "player_count": run.player_count,
                    "total_distance_m": run.total_distance_m,
                    "max_speed_mps": run.max_speed_mps,
                    "high_speed_distance_m": run.high_speed_distance_m,
                    "sprint_count": run.sprint_count,
                    "started_at": run.started_at.isoformat(),
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                },
                "summary": summary,
                "samples": [match_tracking_sample_read(sample) for sample in samples],
            },
            default=str,
            indent=2,
            sort_keys=True,
        ).encode()
        filename = f"match-tracking-{run.id}-analysis.json"
        content_type = "application/json"
    elif normalized_format in {"samples_csv", "tracking_samples_csv", "csv"}:
        rows = [match_tracking_sample_export_row(sample) for sample in samples]
        content = csv_bytes(
            [
                "timestamp_seconds",
                "frame_index",
                "track_id",
                "person_id",
                "team_label",
                "player_label",
                "jersey_number",
                "x_percent",
                "y_percent",
                "x_meters",
                "y_meters",
                "speed_mps",
                "confidence",
                "source",
            ],
            rows,
        )
        filename = f"match-tracking-{run.id}-samples.csv"
        content_type = "text/csv; charset=utf-8"
    elif normalized_format in {"player_metrics_csv", "metrics_csv"}:
        metrics = [item for item in summary.get("player_metrics", []) if isinstance(item, dict)]
        content = csv_bytes(
            [
                "track_id",
                "player_label",
                "team_label",
                "jersey_number",
                "sample_count",
                "duration_seconds",
                "distance_m",
                "high_speed_distance_m",
                "max_speed_mps",
                "average_speed_mps",
                "work_rate_m_per_min",
                "sprint_count",
                "pressure_applied_count",
                "pressure_received_count",
                "pass_completed_count",
                "pass_attempt_count",
                "pass_accuracy_percent",
                "turnover_involved_count",
                "interception_count",
                "tackle_count",
                "shot_count",
                "expected_goals",
                "dominant_zone",
                "tracking_quality_score",
                "coaching_flags",
            ],
            [match_tracking_player_metric_export_row(metric) for metric in metrics],
        )
        filename = f"match-tracking-{run.id}-player-metrics.csv"
        content_type = "text/csv; charset=utf-8"
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported match tracking export format",
        )
    checksum = hashlib.sha256(content).hexdigest()
    return {
        "content": content,
        "content_type": content_type,
        "filename": filename,
        "checksum": checksum,
        "size_bytes": len(content),
    }


def csv_bytes(headers: list[str], rows: list[dict[str, object]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode()


def match_tracking_sample_export_row(sample: PerformanceMatchTrackingSample) -> dict[str, object]:
    return {
        "timestamp_seconds": sample.timestamp_seconds,
        "frame_index": sample.frame_index,
        "track_id": sample.track_id,
        "person_id": str(sample.person_id) if sample.person_id else "",
        "team_label": sample.team_label or "",
        "player_label": sample.player_label or "",
        "jersey_number": sample.jersey_number or "",
        "x_percent": sample.x_percent,
        "y_percent": sample.y_percent,
        "x_meters": sample.x_meters,
        "y_meters": sample.y_meters,
        "speed_mps": sample.speed_mps if sample.speed_mps is not None else "",
        "confidence": sample.confidence if sample.confidence is not None else "",
        "source": sample.source,
    }


def match_tracking_player_metric_export_row(metric: dict[str, object]) -> dict[str, object]:
    row: dict[str, object] = {}
    for key, value in metric.items():
        if isinstance(value, (list, dict)):
            row[key] = json.dumps(value, default=str, sort_keys=True)
        elif value is None:
            row[key] = ""
        else:
            row[key] = value
    return row


async def list_match_tracking_provider_ingest_events(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    *,
    video_asset_id: UUID | None = None,
    limit: int = 25,
) -> list[PerformanceMatchTrackingProviderIngestEvent]:
    await ensure_manage_performance(authz, identity, organization_id)
    statement = select(PerformanceMatchTrackingProviderIngestEvent).where(
        PerformanceMatchTrackingProviderIngestEvent.organization_id == organization_id
    )
    if video_asset_id is not None:
        statement = statement.where(PerformanceMatchTrackingProviderIngestEvent.video_asset_id == video_asset_id)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    PerformanceMatchTrackingProviderIngestEvent.received_at.desc(),
                    PerformanceMatchTrackingProviderIngestEvent.created_at.desc(),
                ).limit(limit)
            )
        ).all()
    )


async def reprocess_match_tracking_provider_ingest_event(
    db: AsyncSession,
    identity: CurrentIdentity,
    ingest_event_id: UUID,
    payload: PerformanceMatchTrackingProviderIngestReprocessCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    ingest_event = await db.get(PerformanceMatchTrackingProviderIngestEvent, ingest_event_id)
    if ingest_event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider ingest event not found")
    await ensure_manage_performance(authz, identity, ingest_event.organization_id)
    stored_payload = decode_json_dict(ingest_event.payload_json)
    if not stored_payload:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Provider ingest payload was not retained for this event",
        )
    try:
        webhook_payload = PerformanceMatchTrackingProviderWebhookCreate.model_validate(stored_payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Provider ingest payload can no longer be validated",
        ) from error
    if (
        webhook_payload.organization_id != ingest_event.organization_id
        or webhook_payload.video_asset_id != ingest_event.video_asset_id
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Provider ingest payload does not match audit row")
    previous_run = (
        await db.get(PerformanceMatchTrackingRun, ingest_event.tracking_run_id)
        if ingest_event.tracking_run_id is not None
        else None
    )
    if previous_run is not None:
        previous_run.status = "superseded"
    reprocessed_at = datetime.now(UTC)
    warnings = list(webhook_payload.quality_warnings)
    warnings.append(
        "Provider tracking payload was reprocessed from the retained signed ingest audit; coach review remains required."
    )
    run = await create_match_tracking_provider_import(
        db,
        identity,
        ingest_event.video_asset_id,
        PerformanceMatchTrackingProviderImportCreate(
            organization_id=ingest_event.organization_id,
            calibration_id=payload.calibration_id or webhook_payload.calibration_id,
            source_provider=webhook_payload.source_provider,
            model_policy=f"{webhook_payload.model_policy}-reprocess"[:160],
            pitch_length_m=webhook_payload.pitch_length_m,
            pitch_width_m=webhook_payload.pitch_width_m,
            replace_existing=False,
            frames=webhook_payload.frames,
            provider_metadata={
                **webhook_payload.provider_metadata,
                "external_event_id": webhook_payload.external_event_id,
                "signature_required": ingest_event.signature_required,
                "signature_validated": ingest_event.signature_validated,
                "ingest_contract": "afrolete-provider-tracking-webhook-v1",
                "reprocessed_from_ingest_event_id": str(ingest_event.id),
                "reprocessed_at": reprocessed_at.isoformat(),
                "reprocessed_by_person_id": str(identity.person_id),
                **({"reprocess_notes": payload.notes} if payload.notes else {}),
            },
            quality_warnings=warnings,
        ),
        authz,
    )
    ingest_event.tracking_run_id = run["id"]
    ingest_event.sample_count = int(run["sample_count"])
    ingest_event.player_count = int(run["player_count"])
    ingest_event.status = "reprocessed"
    await db.commit()
    await db.refresh(ingest_event)
    tracking_run = await db.get(PerformanceMatchTrackingRun, run["id"])
    return await match_tracking_provider_webhook_result(
        db,
        ingest_event,
        replayed=False,
        tracking_run=tracking_run,
        reprocessed=True,
    )


async def create_match_tracking_identity_review(
    db: AsyncSession,
    identity: CurrentIdentity,
    tracking_run_id: UUID,
    payload: PerformanceMatchTrackingIdentityReviewCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    run = await get_match_tracking_run(db, tracking_run_id)
    await ensure_manage_performance(authz, identity, run.organization_id)
    if payload.person_id is not None:
        await ensure_assignment_person(db, run.organization_id, payload.person_id)
    samples = list(
        (
            await db.scalars(
                select(PerformanceMatchTrackingSample)
                .where(
                    PerformanceMatchTrackingSample.tracking_run_id == run.id,
                    PerformanceMatchTrackingSample.track_id == payload.track_id,
                )
                .order_by(PerformanceMatchTrackingSample.timestamp_seconds.asc())
            )
        ).all()
    )
    if not samples:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")
    before = match_tracking_identity_snapshot(samples)
    person_id = payload.person_id if payload.person_id is not None else samples[-1].person_id
    team_label = cleaned_optional_text(payload.team_label, fallback=samples[-1].team_label)
    player_label = cleaned_optional_text(payload.player_label, fallback=samples[-1].player_label)
    jersey_number = cleaned_optional_text(payload.jersey_number, fallback=samples[-1].jersey_number)
    for sample in samples:
        sample.person_id = person_id
        sample.team_label = team_label
        sample.player_label = player_label
        sample.jersey_number = jersey_number
        if "identity_review" not in sample.source:
            sample.source = f"{sample.source}|identity_review"[:80]
    after = {
        "person_id": str(person_id) if person_id else None,
        "team_label": team_label,
        "player_label": player_label,
        "jersey_number": jersey_number,
    }
    review = PerformanceMatchTrackingIdentityReview(
        organization_id=run.organization_id,
        tracking_run_id=run.id,
        video_asset_id=run.video_asset_id,
        track_id=payload.track_id,
        reviewer_person_id=identity.person_id,
        person_id=person_id,
        team_label=team_label,
        player_label=player_label,
        jersey_number=jersey_number,
        decision=payload.decision.strip().lower(),
        sample_count=len(samples),
        before_json=json.dumps(before, default=str),
        after_json=json.dumps(after, default=str),
        notes=payload.notes,
        reviewed_at=datetime.now(UTC),
    )
    db.add(review)
    await recompute_match_tracking_run_summary(db, run)
    run.status = "reviewed"
    await db.commit()
    await db.refresh(review)
    await db.refresh(run)
    return {
        "review": match_tracking_identity_review_read(review),
        "tracking_run": await match_tracking_run_read(db, run),
    }


async def list_match_tracking_identity_reviews(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    tracking_run_id: UUID | None = None,
) -> list[PerformanceMatchTrackingIdentityReview]:
    await ensure_manage_performance(authz, identity, organization_id)
    statement = select(PerformanceMatchTrackingIdentityReview).where(
        PerformanceMatchTrackingIdentityReview.organization_id == organization_id
    )
    if tracking_run_id is not None:
        statement = statement.where(PerformanceMatchTrackingIdentityReview.tracking_run_id == tracking_run_id)
    return list(
        (
            await db.scalars(
                statement.order_by(PerformanceMatchTrackingIdentityReview.reviewed_at.desc()).limit(100)
            )
        ).all()
    )


async def create_performance_match_analysis_report(
    db: AsyncSession,
    identity: CurrentIdentity,
    tracking_run_id: UUID,
    payload: PerformanceMatchAnalysisReportCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> PerformanceMatchAnalysisReport:
    run = await get_match_tracking_run(db, tracking_run_id)
    if run.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    await ensure_manage_performance(authz, identity, run.organization_id)
    video_asset = await get_opposition_scouting_video_asset(db, run.video_asset_id)
    tracking = await match_tracking_run_read(db, run)
    selected_settings = settings or get_settings()
    artifact = build_match_analysis_report_artifact(
        tracking,
        video_asset,
        audience=payload.audience,
        report_scope=payload.report_scope,
        title=payload.title,
        include_player_cards=payload.include_player_cards,
        include_tactical_shape=payload.include_tactical_shape,
        notes=payload.notes,
    )
    report_id = uuid4()
    content = bytes(artifact["content"])
    checksum = hashlib.sha256(content).hexdigest()
    key = match_analysis_report_object_key(run.organization_id, run.id, report_id, str(artifact["filename"]))
    stored = put_object(
        selected_settings,
        local_root=selected_settings.performance_match_report_dir,
        local_url_prefix=selected_settings.performance_match_report_url_prefix,
        key=key,
        content=content,
        content_type=str(artifact["content_type"]),
    )
    report = PerformanceMatchAnalysisReport(
        id=report_id,
        organization_id=run.organization_id,
        tracking_run_id=run.id,
        video_asset_id=run.video_asset_id,
        created_by_person_id=identity.person_id,
        title=str(artifact["title"]),
        audience=payload.audience.strip().lower(),
        report_scope=payload.report_scope.strip().lower(),
        status="generated",
        model_policy=str(artifact["model_policy"]),
        summary_json=json.dumps(artifact["summary"], default=str),
        player_cards_json=json.dumps(artifact["player_cards"], default=str),
        team_shape_json=json.dumps(artifact["team_shape"], default=str),
        recommendations_json=json.dumps(artifact["recommendations"], default=str),
        artifact_format="markdown",
        content_type=str(artifact["content_type"]),
        storage_url=stored.url,
        storage_path=stored.path,
        checksum=checksum,
        size_bytes=len(content),
        generated_at=datetime.now(UTC),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def list_performance_match_analysis_reports(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    tracking_run_id: UUID | None = None,
) -> list[PerformanceMatchAnalysisReport]:
    await ensure_manage_performance(authz, identity, organization_id)
    statement = select(PerformanceMatchAnalysisReport).where(
        PerformanceMatchAnalysisReport.organization_id == organization_id
    )
    if tracking_run_id is not None:
        statement = statement.where(PerformanceMatchAnalysisReport.tracking_run_id == tracking_run_id)
    return list(
        (
            await db.scalars(
                statement.order_by(PerformanceMatchAnalysisReport.generated_at.desc()).limit(50)
            )
        ).all()
    )


async def downloadable_performance_match_analysis_report(
    db: AsyncSession,
    identity: CurrentIdentity,
    report_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> dict[str, object]:
    report = await get_performance_match_analysis_report(db, report_id)
    await ensure_manage_performance(authz, identity, report.organization_id)
    selected_settings = settings or get_settings()
    content = get_object(
        selected_settings,
        local_root=selected_settings.performance_match_report_dir,
        key=performance_match_analysis_report_object_key(report, selected_settings),
    )
    checksum = hashlib.sha256(content).hexdigest()
    if checksum != report.checksum:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match report checksum mismatch")
    return {
        "content": content,
        "content_type": report.content_type,
        "filename": match_analysis_report_download_filename(report),
        "checksum": checksum,
    }


def match_analysis_report_read(report: PerformanceMatchAnalysisReport) -> dict[str, object]:
    return {
        "id": report.id,
        "organization_id": report.organization_id,
        "tracking_run_id": report.tracking_run_id,
        "video_asset_id": report.video_asset_id,
        "created_by_person_id": report.created_by_person_id,
        "title": report.title,
        "audience": report.audience,
        "report_scope": report.report_scope,
        "status": report.status,
        "model_policy": report.model_policy,
        "summary": decode_json_dict(report.summary_json),
        "player_cards": decode_json_list(report.player_cards_json),
        "team_shape": decode_json_list(report.team_shape_json),
        "recommendations": decode_string_list(report.recommendations_json),
        "artifact_format": report.artifact_format,
        "content_type": report.content_type,
        "storage_url": report.storage_url,
        "checksum": report.checksum,
        "size_bytes": report.size_bytes,
        "generated_at": report.generated_at,
        "created_at": report.created_at,
    }


async def review_match_tracking_player_guidance(
    db: AsyncSession,
    identity: CurrentIdentity,
    tracking_run_id: UUID,
    authz: AuthorizationService,
) -> dict[str, object]:
    run = await get_match_tracking_run(db, tracking_run_id)
    await ensure_manage_performance(authz, identity, run.organization_id)
    video_asset = await get_opposition_scouting_video_asset(db, run.video_asset_id)
    tracking = await match_tracking_run_read(db, run)
    artifact = build_match_analysis_report_artifact(
        tracking,
        video_asset,
        audience="player",
        report_scope="player_feedback",
        title=f"{video_asset.opponent_name} player guidance readiness",
        include_player_cards=True,
        include_tactical_shape=True,
        notes=None,
    )
    reviews = list(
        (
            await db.scalars(
                select(PerformanceMatchTrackingIdentityReview)
                .where(PerformanceMatchTrackingIdentityReview.tracking_run_id == run.id)
                .where(PerformanceMatchTrackingIdentityReview.decision.in_(["confirmed", "corrected"]))
            )
        ).all()
    )
    reviewed_track_ids = {review.track_id for review in reviews}
    player_cards = [card for card in artifact["player_cards"] if isinstance(card, dict)]
    anonymous_cards = [
        card
        for card in player_cards
        if str(card.get("player_label") or "").strip().lower().startswith("track ")
        and str(card.get("track_id") or "") not in reviewed_track_ids
    ]
    low_quality_cards = [
        card for card in player_cards if float(card.get("tracking_quality_score") or 0.0) < 0.55
    ]
    tracking_quality = float(tracking.get("tracking_quality_score") or 0.0)
    identity_continuity = float(tracking.get("identity_continuity_score") or 0.0)
    calibration_quality = float(tracking.get("calibration_quality_score") or 0.0)
    sample_count = int(tracking.get("sample_count") or 0)
    player_count = int(tracking.get("player_count") or 0)
    readiness_level = str(tracking.get("readiness_level") or "unknown")
    required_actions: list[str] = []
    review_notes: list[str] = []
    if not player_cards:
        required_actions.append("Create a tracking run with player samples before sharing player guidance.")
    if calibration_quality < 0.75:
        required_actions.append("Calibrate the pitch or import calibrated provider coordinates before publishing distance and speed guidance.")
    if tracking_quality < 0.72:
        required_actions.append("Raise tracking quality above 72% through better footage, provider tracking, calibration, or identity review.")
    if identity_continuity < 0.72:
        required_actions.append("Review identity continuity because track gaps or camera cuts may have swapped players.")
    if anonymous_cards:
        required_actions.append(f"Confirm identities for {len(anonymous_cards)} anonymous track(s) before player-facing sharing.")
    if low_quality_cards:
        required_actions.append(f"Review {len(low_quality_cards)} low-confidence player card(s) before using them for player feedback.")
    if sample_count < max(player_count * 6, 6):
        required_actions.append("Capture or import a longer sample window for reliable player load comparisons.")

    quality_warnings = [str(item) for item in (tracking.get("quality_warnings") or []) if str(item)]
    review_notes.extend(quality_warnings)
    if not required_actions:
        review_notes.append("Player guidance is ready for coach-approved sharing.")
    else:
        review_notes.append("Player guidance is draft-only until required review actions are closed.")

    publishable = not required_actions
    guidance_status = "player_shareable" if publishable else "coach_review_required"
    player_guidance = [
        match_player_guidance_card(card, publishable=publishable and card not in low_quality_cards)
        for card in player_cards
    ]
    return {
        "tracking_run_id": run.id,
        "organization_id": run.organization_id,
        "video_asset_id": run.video_asset_id,
        "publishable": publishable,
        "guidance_status": guidance_status,
        "readiness_level": readiness_level,
        "tracking_quality_score": round(tracking_quality, 3),
        "identity_continuity_score": round(identity_continuity, 3),
        "calibration_quality_score": round(calibration_quality, 3),
        "sample_count": sample_count,
        "player_count": player_count,
        "reviewed_identity_count": len(reviewed_track_ids),
        "unreviewed_track_count": len(anonymous_cards),
        "player_card_count": len(player_cards),
        "required_actions": list(dict.fromkeys(required_actions)),
        "review_notes": list(dict.fromkeys(review_notes)),
        "coach_guidance": [str(item) for item in artifact["recommendations"]],
        "player_guidance": player_guidance,
        "player_cards": player_cards,
        "quality_warnings": quality_warnings,
        "generated_at": datetime.now(UTC),
    }


def match_player_guidance_card(card: dict[str, object], *, publishable: bool) -> dict[str, object]:
    label = str(card.get("player_label") or card.get("track_id") or "Player")
    distance = round(float(card.get("distance_m") or 0.0))
    high_speed = round(float(card.get("high_speed_distance_m") or 0.0))
    max_speed = round(float(card.get("max_speed_mps") or 0.0), 1)
    sprints = int(card.get("sprint_count") or 0)
    pressure = int(card.get("pressure_applied_count") or 0)
    received_pressure = int(card.get("pressure_received_count") or 0)
    actions = [
        str(flag)
        for flag in (card.get("coaching_flags") or [])
        if str(flag).strip()
    ]
    if not actions:
        actions = ["Review match clips with the player and agree one training focus."]
    if high_speed >= 40 or sprints >= 3:
        next_action = "Schedule recovery and sprint-mechanics review before the next high-load session."
    elif pressure or received_pressure:
        next_action = "Review scanning, first touch, and support angles in the pressure clips."
    elif int(card.get("pass_attempt_count") or 0) > 0:
        next_action = "Review passing decisions and receiving body shape with the player."
    else:
        next_action = "Pair this metric card with video clips before giving individual feedback."
    return {
        "track_id": card.get("track_id"),
        "player_label": label,
        "team_label": card.get("team_label"),
        "jersey_number": card.get("jersey_number"),
        "publishable": publishable,
        "headline": f"{label}: {distance}m total, {high_speed}m high-speed, max {max_speed} m/s.",
        "load_summary": f"{sprints} sprint(s), {card.get('work_rate_m_per_min', 0)} m/min work rate.",
        "tactical_summary": (
            f"{pressure} pressure action(s), {received_pressure} pressure received, "
            f"dominant zone {str(card.get('dominant_zone') or 'unknown').replace('_', ' ')}."
        ),
        "recommended_next_action": next_action,
        "evidence": actions[0],
        "caution": None if publishable else "Coach review required before sharing this guidance with the player.",
    }


async def publish_match_tracking_player_guidance(
    db: AsyncSession,
    identity: CurrentIdentity,
    tracking_run_id: UUID,
    payload: PerformanceMatchPlayerGuidancePublishCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    run = await get_match_tracking_run(db, tracking_run_id)
    if run.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    await ensure_manage_performance(authz, identity, run.organization_id)
    review = await review_match_tracking_player_guidance(db, identity, tracking_run_id, authz)
    if payload.require_publishable and not review["publishable"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Player guidance is not publishable yet",
                "required_actions": review["required_actions"],
            },
        )
    video_asset = await get_opposition_scouting_video_asset(db, run.video_asset_id)
    player_person_by_track = await match_tracking_player_person_by_track(db, run)
    guidance_by_track = {
        str(item.get("track_id")): item
        for item in review["player_guidance"]
        if isinstance(item, dict) and item.get("track_id")
    }
    skipped_tracks: list[str] = []
    messages: list[dict[str, object]] = []
    published_at = datetime.now(UTC)
    for track_id, guidance in sorted(guidance_by_track.items()):
        player_person_id = player_person_by_track.get(track_id)
        if player_person_id is None:
            skipped_tracks.append(track_id)
            continue
        recipient_ids = [player_person_id]
        if payload.include_guardians:
            recipient_ids.extend(sorted(await guardian_person_ids(db, player_person_id), key=str))
        recipient_ids = list(dict.fromkeys(recipient_ids))
        player_label = str(guidance.get("player_label") or track_id)
        subject = f"{payload.subject_prefix}: {video_asset.opponent_name} - {player_label}"[:240]
        body = match_player_guidance_message_body(
            guidance,
            video_asset=video_asset,
            run=run,
            message_intro=payload.message_intro,
        )
        message = await create_message_for_recipients(
            db,
            organization_id=run.organization_id,
            message_type=CommunicationMessageType.REPORT,
            channel=payload.channel,
            scope_type=CommunicationScopeType.PERSON,
            scope_id=player_person_id,
            recipient_person_ids=recipient_ids,
            subject=subject,
            body=body,
            created_by_person_id=identity.person_id,
        )
        db.add(
            PerformanceMatchPlayerGuidancePublishAudit(
                organization_id=run.organization_id,
                tracking_run_id=run.id,
                video_asset_id=run.video_asset_id,
                message_id=message.id,
                player_person_id=player_person_id,
                track_id=track_id,
                player_label=player_label,
                channel=payload.channel,
                recipient_count=len(recipient_ids),
                published_by_person_id=identity.person_id,
                status="published",
                published_at=published_at,
            )
        )
        messages.append(
            {
                "message_id": message.id,
                "player_person_id": player_person_id,
                "recipient_person_ids": recipient_ids,
                "track_id": track_id,
                "player_label": player_label,
                "subject": subject,
                "channel": payload.channel,
            }
        )
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No confirmed player tracks are available for guidance publishing",
        )
    await db.commit()
    created_message_ids = {message["message_id"] for message in messages}
    audits = [
        audit
        for audit in await list_match_tracking_player_guidance_publishes(
            db,
            identity,
            tracking_run_id,
            authz,
        )
        if audit["message_id"] in created_message_ids
    ]
    return {
        "tracking_run_id": run.id,
        "organization_id": run.organization_id,
        "video_asset_id": run.video_asset_id,
        "publishable": bool(review["publishable"]),
        "guidance_status": str(review["guidance_status"]),
        "message_count": len(messages),
        "recipient_count": sum(len(message["recipient_person_ids"]) for message in messages),
        "player_count": len(messages),
        "skipped_track_count": len(skipped_tracks),
        "skipped_tracks": skipped_tracks,
        "required_actions": review["required_actions"],
        "messages": messages,
        "audits": audits,
        "published_at": published_at,
    }


async def list_match_tracking_player_guidance_publishes(
    db: AsyncSession,
    identity: CurrentIdentity,
    tracking_run_id: UUID,
    authz: AuthorizationService,
) -> list[dict[str, object]]:
    run = await get_match_tracking_run(db, tracking_run_id)
    await ensure_manage_performance(authz, identity, run.organization_id)
    audits = list(
        (
            await db.scalars(
                select(PerformanceMatchPlayerGuidancePublishAudit)
                .where(PerformanceMatchPlayerGuidancePublishAudit.tracking_run_id == run.id)
                .order_by(
                    PerformanceMatchPlayerGuidancePublishAudit.published_at.desc(),
                    PerformanceMatchPlayerGuidancePublishAudit.created_at.desc(),
                )
                .limit(200)
            )
        ).all()
    )
    if not audits:
        return []
    message_ids = [audit.message_id for audit in audits]
    recipient_rows = (
        await db.execute(
            select(MessageRecipient.message_id, MessageRecipient.delivery_status).where(
                MessageRecipient.message_id.in_(message_ids)
            )
        )
    ).all()
    counts_by_message: dict[UUID, dict[str, int]] = {
        audit.message_id: {
            "queued_count": 0,
            "sent_count": 0,
            "delivered_count": 0,
            "read_count": 0,
            "failed_count": 0,
            "suppressed_count": 0,
        }
        for audit in audits
    }
    status_count_keys = {
        MessageDeliveryStatus.QUEUED.value: "queued_count",
        MessageDeliveryStatus.SENT.value: "sent_count",
        MessageDeliveryStatus.DELIVERED.value: "delivered_count",
        MessageDeliveryStatus.READ.value: "read_count",
        MessageDeliveryStatus.FAILED.value: "failed_count",
        MessageDeliveryStatus.SUPPRESSED.value: "suppressed_count",
    }
    for message_id, delivery_status in recipient_rows:
        key = status_count_keys.get(str(delivery_status))
        if key is None and hasattr(delivery_status, "value"):
            key = status_count_keys.get(str(delivery_status.value))
        if key is not None:
            counts_by_message.setdefault(message_id, {}).setdefault(key, 0)
            counts_by_message[message_id][key] += 1
    return [
        match_player_guidance_publish_audit_read(audit, counts_by_message.get(audit.message_id, {}))
        for audit in audits
    ]


def match_player_guidance_publish_audit_read(
    audit: PerformanceMatchPlayerGuidancePublishAudit,
    delivery_counts: dict[str, int],
) -> dict[str, object]:
    return {
        "id": audit.id,
        "organization_id": audit.organization_id,
        "tracking_run_id": audit.tracking_run_id,
        "video_asset_id": audit.video_asset_id,
        "message_id": audit.message_id,
        "player_person_id": audit.player_person_id,
        "track_id": audit.track_id,
        "player_label": audit.player_label,
        "channel": audit.channel,
        "recipient_count": audit.recipient_count,
        "queued_count": delivery_counts.get("queued_count", 0),
        "sent_count": delivery_counts.get("sent_count", 0),
        "delivered_count": delivery_counts.get("delivered_count", 0),
        "read_count": delivery_counts.get("read_count", 0),
        "failed_count": delivery_counts.get("failed_count", 0),
        "suppressed_count": delivery_counts.get("suppressed_count", 0),
        "published_by_person_id": audit.published_by_person_id,
        "status": audit.status,
        "published_at": audit.published_at,
        "created_at": audit.created_at,
    }


async def match_tracking_player_person_by_track(
    db: AsyncSession,
    run: PerformanceMatchTrackingRun,
) -> dict[str, UUID]:
    samples = list(
        (
            await db.scalars(
                select(PerformanceMatchTrackingSample)
                .where(PerformanceMatchTrackingSample.tracking_run_id == run.id)
                .where(PerformanceMatchTrackingSample.person_id.is_not(None))
                .order_by(
                    PerformanceMatchTrackingSample.track_id.asc(),
                    PerformanceMatchTrackingSample.timestamp_seconds.desc(),
                )
            )
        ).all()
    )
    result: dict[str, UUID] = {}
    for sample in samples:
        if sample.person_id is not None and sample.track_id not in result:
            result[sample.track_id] = sample.person_id
    return result


def match_player_guidance_message_body(
    guidance: dict[str, object],
    *,
    video_asset: OppositionScoutingVideoAsset,
    run: PerformanceMatchTrackingRun,
    message_intro: str | None,
) -> str:
    lines = [
        message_intro.strip() if message_intro else "Your coach has reviewed a match-video guidance card for you.",
        "",
        f"Match: {video_asset.opponent_name}",
        f"Clip: {video_asset.clip_label or video_asset.filename}",
        f"Track: {guidance.get('track_id')}",
        "",
        str(guidance.get("headline") or "Player guidance is ready for review."),
        str(guidance.get("load_summary") or ""),
        str(guidance.get("tactical_summary") or ""),
        "",
        f"Next action: {guidance.get('recommended_next_action') or 'Review the match clip with your coach.'}",
        f"Evidence: {guidance.get('evidence') or 'Tracking-derived match metrics.'}",
    ]
    caution = guidance.get("caution")
    if caution:
        lines.extend(["", f"Coach note: {caution}"])
    lines.extend(
        [
            "",
            f"Tracking run: {run.id}",
            "Open your AfroLete player portal for the full metric card and follow-up plan options.",
        ]
    )
    return "\n".join(line for line in lines if line is not None)[:8000]


async def create_performance_highlight_reel(
    db: AsyncSession,
    identity: CurrentIdentity,
    video_asset_id: UUID,
    payload: PerformanceHighlightReelCreate,
    authz: AuthorizationService,
) -> PerformanceHighlightReel:
    video_asset = await get_opposition_scouting_video_asset(db, video_asset_id)
    if video_asset.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    await ensure_manage_performance(authz, identity, video_asset.organization_id)
    tracking_run = (
        await db.get(PerformanceMatchTrackingRun, payload.tracking_run_id)
        if payload.tracking_run_id is not None
        else await latest_match_tracking_run(db, video_asset.id)
    )
    if tracking_run is not None and (
        tracking_run.organization_id != video_asset.organization_id or tracking_run.video_asset_id != video_asset.id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match tracking run not found")
    if payload.athlete_profile_id is not None:
        athlete_profile = await get_athlete_profile(db, payload.athlete_profile_id, video_asset.organization_id)
        athlete_profile_id = athlete_profile.id
    else:
        athlete_profile_id = None
    report = await latest_opposition_scouting_report(db, video_asset.id)
    clips = await generate_highlight_clips_from_match(
        db,
        video_asset,
        tracking_run,
        report,
        target_duration_seconds=payload.target_duration_seconds,
        audience=payload.audience,
    )
    tags = sorted(
        {
            *[tag.strip().lower() for tag in payload.tags if tag.strip()],
            payload.audience.strip().lower(),
            payload.purpose.strip().lower(),
            video_asset.sport.strip().lower(),
            "automated_highlights",
        }
    )
    distribution = highlight_reel_distribution(payload.channels, payload.audience, clips)
    now = datetime.now(UTC)
    reel = PerformanceHighlightReel(
        organization_id=video_asset.organization_id,
        video_asset_id=video_asset.id,
        tracking_run_id=tracking_run.id if tracking_run is not None else None,
        athlete_profile_id=athlete_profile_id,
        created_by_person_id=identity.person_id,
        title=payload.title or f"{video_asset.opponent_name} {payload.audience.title()} Highlight Reel",
        audience=payload.audience.strip().lower(),
        purpose=payload.purpose.strip().lower(),
        model_policy="afrolete-tracking-highlight-reel-v1" if tracking_run is not None else "afrolete-scouting-highlight-reel-v1",
        status="generated",
        clip_count=len(clips),
        duration_seconds=round(sum(float(clip["duration_seconds"]) for clip in clips), 2),
        clips_json=json.dumps(clips, default=str),
        tags_json=encode_string_list(tags),
        distribution_json=json.dumps(distribution, default=str),
        branding_json=json.dumps(payload.branding, default=str) if payload.branding else None,
        generated_at=now,
    )
    db.add(reel)
    video_asset.status = "highlighted"
    video_asset.analyzed_at = now
    await db.commit()
    await db.refresh(reel)
    return reel


async def list_performance_highlight_reels(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    video_asset_id: UUID | None = None,
) -> list[PerformanceHighlightReel]:
    await ensure_manage_performance(authz, identity, organization_id)
    statement = select(PerformanceHighlightReel).where(PerformanceHighlightReel.organization_id == organization_id)
    if video_asset_id is not None:
        statement = statement.where(PerformanceHighlightReel.video_asset_id == video_asset_id)
    return list((await db.scalars(statement.order_by(PerformanceHighlightReel.generated_at.desc()).limit(25))).all())


async def create_performance_highlight_reel_export(
    db: AsyncSession,
    identity: CurrentIdentity,
    highlight_reel_id: UUID,
    payload: PerformanceHighlightReelExportCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> PerformanceHighlightReelExport:
    reel = await get_performance_highlight_reel(db, highlight_reel_id)
    if reel.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    await ensure_manage_performance(authz, identity, reel.organization_id)
    video_asset = await get_opposition_scouting_video_asset(db, reel.video_asset_id)
    selected_settings = settings or get_settings()
    export_format = normalize_highlight_export_format(payload.export_format)
    artifact = build_highlight_reel_export_artifact(
        reel,
        video_asset,
        export_format=export_format,
        delivery_channel=payload.delivery_channel,
        include_branding=payload.include_branding,
        notes=payload.notes,
    )
    now = datetime.now(UTC)
    checksum = hashlib.sha256(artifact["content"]).hexdigest()
    export_id = uuid4()
    key = highlight_reel_export_object_key(reel.organization_id, reel.id, export_id, str(artifact["filename"]))
    stored = put_object(
        selected_settings,
        local_root=selected_settings.performance_highlight_export_dir,
        local_url_prefix=selected_settings.performance_highlight_export_url_prefix,
        key=key,
        content=artifact["content"],
        content_type=str(artifact["content_type"]),
    )
    export = PerformanceHighlightReelExport(
        id=export_id,
        organization_id=reel.organization_id,
        highlight_reel_id=reel.id,
        video_asset_id=reel.video_asset_id,
        tracking_run_id=reel.tracking_run_id,
        requested_by_person_id=identity.person_id,
        export_format=export_format,
        status=str(artifact["status"]),
        renderer_policy=str(artifact["renderer_policy"]),
        filename=str(artifact["filename"]),
        content_type=str(artifact["content_type"]),
        storage_url=stored.url,
        storage_path=stored.path,
        checksum=checksum,
        size_bytes=len(artifact["content"]),
        message=str(artifact["message"]),
        manifest_json=json.dumps(artifact["manifest"], default=str),
        generated_at=now,
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)
    return export


async def persist_performance_highlight_reel_export_artifact(
    db: AsyncSession,
    organization_id: UUID,
    highlight_reel_id: UUID,
    video_asset_id: UUID,
    tracking_run_id: UUID | None,
    requested_by_person_id: UUID | None,
    artifact: dict[str, object],
    *,
    settings: Settings,
) -> PerformanceHighlightReelExport:
    export_id = uuid4()
    content = bytes(artifact["content"])
    checksum = hashlib.sha256(content).hexdigest()
    key = highlight_reel_export_object_key(
        organization_id,
        highlight_reel_id,
        export_id,
        str(artifact["filename"]),
    )
    stored = put_object(
        settings,
        local_root=settings.performance_highlight_export_dir,
        local_url_prefix=settings.performance_highlight_export_url_prefix,
        key=key,
        content=content,
        content_type=str(artifact["content_type"]),
    )
    export = PerformanceHighlightReelExport(
        id=export_id,
        organization_id=organization_id,
        highlight_reel_id=highlight_reel_id,
        video_asset_id=video_asset_id,
        tracking_run_id=tracking_run_id,
        requested_by_person_id=requested_by_person_id,
        export_format=str(artifact["export_format"]),
        status=str(artifact["status"]),
        renderer_policy=str(artifact["renderer_policy"]),
        filename=str(artifact["filename"]),
        content_type=str(artifact["content_type"]),
        storage_url=stored.url,
        storage_path=stored.path,
        checksum=checksum,
        size_bytes=len(content),
        message=str(artifact["message"]),
        manifest_json=json.dumps(artifact["manifest"], default=str),
        generated_at=datetime.now(UTC),
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)
    return export


async def list_performance_highlight_reel_exports(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    highlight_reel_id: UUID | None = None,
) -> list[PerformanceHighlightReelExport]:
    await ensure_manage_performance(authz, identity, organization_id)
    statement = select(PerformanceHighlightReelExport).where(
        PerformanceHighlightReelExport.organization_id == organization_id
    )
    if highlight_reel_id is not None:
        statement = statement.where(PerformanceHighlightReelExport.highlight_reel_id == highlight_reel_id)
    return list(
        (
            await db.scalars(
                statement.order_by(PerformanceHighlightReelExport.generated_at.desc()).limit(50)
            )
        ).all()
    )


async def render_performance_highlight_reel_export(
    db: AsyncSession,
    identity: CurrentIdentity,
    export_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> PerformanceHighlightReelExport:
    export = await get_performance_highlight_reel_export(db, export_id)
    await ensure_manage_performance(authz, identity, export.organization_id)
    if export.export_format != "mp4_edit_decision_list":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only MP4 edit-decision exports can be rendered",
        )
    reel = await get_performance_highlight_reel(db, export.highlight_reel_id)
    video_asset = await get_opposition_scouting_video_asset(db, export.video_asset_id)
    selected_settings = settings or get_settings()
    ffmpeg_path = selected_settings.performance_highlight_renderer_ffmpeg_path.strip() or "ffmpeg"
    if shutil.which(ffmpeg_path) is None:
        artifact = build_highlight_reel_render_failure_artifact(
            export,
            reason=f"ffmpeg executable '{ffmpeg_path}' is not available",
        )
    else:
        source_content = get_object(
            selected_settings,
            local_root=selected_settings.performance_video_file_dir,
            key=opposition_scouting_video_object_key(video_asset, selected_settings),
        )
        if hashlib.sha256(source_content).hexdigest() != video_asset.checksum:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Source video checksum mismatch")
        artifact = render_highlight_reel_mp4_artifact(
            export,
            reel,
            source_content=source_content,
            ffmpeg_path=ffmpeg_path,
        )
    return await persist_performance_highlight_reel_export_artifact(
        db,
        export.organization_id,
        export.highlight_reel_id,
        export.video_asset_id,
        export.tracking_run_id,
        identity.person_id,
        artifact,
        settings=selected_settings,
    )


async def downloadable_performance_highlight_reel_export(
    db: AsyncSession,
    identity: CurrentIdentity,
    export_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> dict[str, object]:
    export = await get_performance_highlight_reel_export(db, export_id)
    await ensure_manage_performance(authz, identity, export.organization_id)
    selected_settings = settings or get_settings()
    content = get_object(
        selected_settings,
        local_root=selected_settings.performance_highlight_export_dir,
        key=performance_highlight_reel_export_object_key(export, selected_settings),
    )
    checksum = hashlib.sha256(content).hexdigest()
    if checksum != export.checksum:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Highlight export checksum mismatch")
    return {
        "content": content,
        "content_type": export.content_type,
        "filename": export.filename,
        "checksum": checksum,
    }


async def downloadable_performance_video_asset(
    db: AsyncSession,
    identity: CurrentIdentity,
    video_asset_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> dict[str, object]:
    video_asset = await get_performance_video_asset(db, video_asset_id)
    await ensure_manage_performance(authz, identity, video_asset.organization_id)
    selected_settings = settings or get_settings()
    key = performance_video_object_key(video_asset, selected_settings)
    content = get_object(
        selected_settings,
        local_root=selected_settings.performance_video_file_dir,
        key=key,
    )
    checksum = hashlib.sha256(content).hexdigest()
    if checksum != video_asset.checksum:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Video checksum mismatch")
    return {
        "content": content,
        "content_type": video_asset.content_type,
        "filename": video_asset.filename,
        "checksum": checksum,
    }


async def create_performance_video_annotation(
    db: AsyncSession,
    identity: CurrentIdentity,
    video_asset_id: UUID,
    payload: PerformanceVideoAnnotationCreate,
    authz: AuthorizationService,
) -> PerformanceVideoAnnotation:
    video_asset = await get_performance_video_asset(db, video_asset_id)
    await ensure_manage_performance(authz, identity, video_asset.organization_id)
    annotation = PerformanceVideoAnnotation(
        organization_id=video_asset.organization_id,
        video_asset_id=video_asset.id,
        athlete_profile_id=video_asset.athlete_profile_id,
        event_id=video_asset.event_id,
        author_person_id=identity.person_id,
        timestamp_seconds=payload.timestamp_seconds,
        playback_rate=payload.playback_rate,
        annotation_type=payload.annotation_type,
        label=payload.label,
        notes=payload.notes,
        body_region=payload.body_region,
        x_percent=payload.x_percent,
        y_percent=payload.y_percent,
        width_percent=payload.width_percent,
        height_percent=payload.height_percent,
        tags_json=json.dumps(payload.tags),
    )
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)
    return annotation


async def list_performance_video_annotations(
    db: AsyncSession,
    video_asset_id: UUID,
) -> list[PerformanceVideoAnnotation]:
    return list(
        (
            await db.scalars(
                select(PerformanceVideoAnnotation)
                .where(PerformanceVideoAnnotation.video_asset_id == video_asset_id)
                .order_by(
                    PerformanceVideoAnnotation.timestamp_seconds,
                    PerformanceVideoAnnotation.created_at,
                )
            )
        ).all()
    )


async def analyze_pose_gait_for_video(
    db: AsyncSession,
    identity: CurrentIdentity,
    video_asset_id: UUID,
    payload: PerformancePoseGaitAnalysisCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    video_asset = await get_performance_video_asset(db, video_asset_id)
    await ensure_manage_performance(authz, identity, video_asset.organization_id)
    focus = payload.analysis_focus or video_asset.analysis_focus or "pose, gait, and movement efficiency"
    reference_profile = (
        await get_movement_reference_profile(db, payload.reference_profile_id, video_asset.organization_id)
        if payload.reference_profile_id
        else None
    )
    pose_samples = await list_performance_video_pose_samples(db, video_asset.id)
    derived_metrics = derive_pose_sample_metrics(pose_samples)
    metrics = pose_gait_metric_cards(
        payload.evidence_text,
        video_asset.sport,
        derived_metrics,
        reference_profile,
    )
    phases = pose_gait_phase_cards(metrics, video_asset.duration_seconds)
    projections = optimal_projection_cards(metrics)
    confidence = pose_gait_confidence(payload.evidence_text, video_asset, len(pose_samples))
    summary = pose_gait_summary(video_asset, metrics, confidence, len(pose_samples))
    source_providers = sorted({sample.source_provider for sample in pose_samples})
    analysis = {
        "model_policy": (
            "afrolete-pose-gait-keypoints-v1"
            if pose_samples
            else "afrolete-pose-gait-benchmark-v1"
        ),
        "benchmark_profile": payload.benchmark_profile,
        "reference_profile_id": str(reference_profile.id) if reference_profile else None,
        "reference_profile_name": reference_profile.name if reference_profile else None,
        "reference_profile_source": reference_profile.source_label if reference_profile else None,
        "confidence": confidence,
        "pose_sample_count": len(pose_samples),
        "pose_sample_source_providers": source_providers,
        "summary": summary,
        "metrics": metrics,
        "phases": phases,
        "optimal_projections": projections,
        "slow_motion_rates": video_slow_motion_rates(),
        "focus": focus,
    }
    video_asset.pose_analysis_json = json.dumps(analysis, default=str)
    video_asset.analysis_model_policy = str(analysis["model_policy"])
    video_asset.analyzed_at = datetime.now(UTC)
    video_asset.status = "analyzed"
    await db.commit()
    await db.refresh(video_asset)
    coaching_result = None
    if payload.create_coaching_outputs:
        coaching_result = await analyze_video_for_coaching(
            db,
            identity,
            video_asset.athlete_profile_id,
            PerformanceVideoCoachingCreate(
                organization_id=video_asset.organization_id,
                event_id=video_asset.event_id,
                sport=video_asset.sport,
                video_uri=video_asset.video_uri,
                clip_label=video_asset.clip_label,
                analysis_focus=focus,
                evidence_text=pose_gait_evidence_text(video_asset, metrics, phases, payload.evidence_text),
                provider="afrolete_pose_gait_benchmark",
            ),
            authz,
        )
        video_asset = await get_performance_video_asset(db, video_asset_id)
    return {
        "video_asset": video_asset,
        "analysis": analysis,
        "annotations": await list_performance_video_annotations(db, video_asset.id),
        "coaching": coaching_result,
    }


async def run_performance_model_extraction_benchmark(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: PerformanceModelExtractionBenchmarkRunCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    await ensure_manage_performance(authz, identity, payload.organization_id)
    settings = get_settings()
    dataset: PerformanceModelExtractionBenchmarkDataset | None = None
    if payload.dataset_id is not None:
        dataset = await db.get(PerformanceModelExtractionBenchmarkDataset, payload.dataset_id)
        if dataset is None or dataset.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark dataset not found")
        cases = [
            benchmark_case_create_from_model(case)
            for case in await active_benchmark_cases(db, dataset.id)
        ]
    else:
        cases = payload.cases or default_model_extraction_benchmark_cases()
    results = [
        await evaluate_model_extraction_benchmark_case(settings, payload.organization_id, case)
        for case in cases
    ]
    passed_count = sum(1 for result in results if result["passed"])
    mean_absolute_error = (
        round(sum(float(result["absolute_error"]) for result in results) / len(results), 4)
        if results
        else 0.0
    )
    if dataset is not None:
        dataset.last_run_at = datetime.now(UTC)
        dataset.last_accuracy = round(passed_count / len(results), 4) if results else 0.0
        dataset.last_mean_absolute_error = mean_absolute_error
        dataset.last_case_count = len(results)
        db.add(dataset)
        await db.commit()
    return {
        "organization_id": payload.organization_id,
        "model_policy": settings.performance_model_extraction_model,
        "case_count": len(results),
        "passed_count": passed_count,
        "failed_count": len(results) - passed_count,
        "accuracy": round(passed_count / len(results), 4) if results else 0.0,
        "mean_absolute_error": mean_absolute_error,
        "cases": results,
    }


async def create_performance_model_extraction_benchmark_dataset(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: PerformanceModelExtractionBenchmarkDatasetCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    await ensure_manage_performance(authz, identity, payload.organization_id)
    settings = get_settings()
    slug = benchmark_dataset_slug(payload.slug or payload.name)
    existing = await db.scalar(
        select(PerformanceModelExtractionBenchmarkDataset)
        .where(PerformanceModelExtractionBenchmarkDataset.organization_id == payload.organization_id)
        .where(PerformanceModelExtractionBenchmarkDataset.slug == slug)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Benchmark dataset slug already exists")
    dataset = PerformanceModelExtractionBenchmarkDataset(
        organization_id=payload.organization_id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        model_policy=payload.model_policy or settings.performance_model_extraction_model,
        status="active",
        owner_person_id=identity.person_id,
        last_case_count=len(payload.cases),
    )
    db.add(dataset)
    await db.flush()
    dataset_id = dataset.id
    for case in payload.cases:
        db.add(performance_model_benchmark_case_model(payload.organization_id, dataset_id, case))
    await db.commit()
    return await performance_model_benchmark_dataset_read(db, dataset_id)


async def list_performance_model_extraction_benchmark_datasets(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[dict[str, object]]:
    await ensure_manage_performance(authz, identity, organization_id)
    datasets = list(
        (
            await db.scalars(
                select(PerformanceModelExtractionBenchmarkDataset)
                .where(PerformanceModelExtractionBenchmarkDataset.organization_id == organization_id)
                .order_by(
                    PerformanceModelExtractionBenchmarkDataset.updated_at.desc(),
                    PerformanceModelExtractionBenchmarkDataset.created_at.desc(),
                )
            )
        ).all()
    )
    return [await performance_model_benchmark_dataset_read(db, dataset.id) for dataset in datasets]


async def performance_model_extraction_review_queue(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    *,
    athlete_profile_id: UUID | None = None,
    limit: int = 50,
) -> dict[str, object]:
    await ensure_manage_performance(authz, identity, organization_id)
    if athlete_profile_id is not None:
        await get_athlete_profile(db, athlete_profile_id, organization_id)
    statement = (
        select(AthletePerformanceObservation, PerformanceMetricDefinition)
        .join(
            PerformanceMetricDefinition,
            AthletePerformanceObservation.metric_definition_id == PerformanceMetricDefinition.id,
        )
        .where(AthletePerformanceObservation.organization_id == organization_id)
        .where(AthletePerformanceObservation.verification_status == MetricVerificationStatus.PENDING_REVIEW)
        .order_by(
            AthletePerformanceObservation.confidence.asc().nullsfirst(),
            AthletePerformanceObservation.observed_at.desc(),
            AthletePerformanceObservation.created_at.desc(),
        )
        .limit(limit)
    )
    if athlete_profile_id is not None:
        statement = statement.where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
    rows = list((await db.execute(statement)).all())
    items = [
        performance_model_extraction_review_item(observation, metric)
        for observation, metric in rows
        if observation.source in MODEL_ASSIST_SOURCES or performance_observation_model_assisted(observation)
    ]
    confidences = [
        float(item["observation"].confidence)
        for item in items
        if item["observation"].confidence is not None
    ]
    model_assisted_count = sum(1 for item in items if item["model_assisted"])
    high_priority_count = sum(1 for item in items if item["review_priority"] == "high")
    recommendations = performance_model_extraction_queue_recommendations(items)
    return {
        "organization_id": organization_id,
        "athlete_profile_id": athlete_profile_id,
        "pending_count": len(items),
        "model_assisted_count": model_assisted_count,
        "high_priority_count": high_priority_count,
        "average_confidence": round(sum(confidences) / len(confidences), 4) if confidences else None,
        "recommendations": recommendations,
        "items": items,
    }


async def bulk_review_performance_model_extraction_queue(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: PerformanceModelExtractionBulkReviewCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    requested_ids = {str(observation_id) for observation_id in payload.observation_ids}
    if requested_ids:
        await ensure_manage_performance(authz, identity, payload.organization_id)
        if payload.athlete_profile_id is not None:
            await get_athlete_profile(db, payload.athlete_profile_id, payload.organization_id)
        statement = (
            select(AthletePerformanceObservation, PerformanceMetricDefinition)
            .join(
                PerformanceMetricDefinition,
                AthletePerformanceObservation.metric_definition_id == PerformanceMetricDefinition.id,
            )
            .where(AthletePerformanceObservation.organization_id == payload.organization_id)
            .where(AthletePerformanceObservation.verification_status == MetricVerificationStatus.PENDING_REVIEW)
            .where(AthletePerformanceObservation.id.in_(payload.observation_ids))
        )
        if payload.athlete_profile_id is not None:
            statement = statement.where(AthletePerformanceObservation.athlete_profile_id == payload.athlete_profile_id)
        items = [
            performance_model_extraction_review_item(observation, metric)
            for observation, metric in list((await db.execute(statement)).all())
        ]
    else:
        queue = await performance_model_extraction_review_queue(
            db,
            identity,
            payload.organization_id,
            authz,
            athlete_profile_id=payload.athlete_profile_id,
            limit=payload.max_items,
        )
        items = list(queue["items"])
    reviewed: list[AthletePerformanceObservation] = []
    skipped_count = 0
    for item in items:
        observation = item["observation"]
        if payload.only_model_assisted and not item["model_assisted"]:
            skipped_count += 1
            continue
        if observation.confidence is not None and observation.confidence < payload.min_confidence:
            skipped_count += 1
            continue
        observation.verification_status = payload.verification_status
        review_note = payload.notes or "Bulk reviewed through the model-extraction review queue."
        observation.notes = (
            f"{observation.notes or ''} Review decision: {payload.verification_status.value}. "
            f"{review_note}"
        ).strip()[:2000]
        db.add(observation)
        reviewed.append(observation)
        if not requested_ids and len(reviewed) >= payload.max_items:
            break
    if reviewed:
        await db.commit()
        for observation in reviewed:
            await db.refresh(observation)
    recommendations = [
        "Keep low-confidence or non-model-assisted evidence in the queue for individual coach correction."
        if skipped_count
        else "Reviewed observations are ready for downstream summaries, benchmarks, and player guidance."
    ]
    return {
        "organization_id": payload.organization_id,
        "reviewed_count": len(reviewed),
        "skipped_count": skipped_count,
        "verification_status": payload.verification_status,
        "summary": (
            f"{len(reviewed)} model-extraction observation(s) marked "
            f"{payload.verification_status.value}; {skipped_count} skipped by policy."
        ),
        "recommendations": recommendations,
        "observations": reviewed,
    }


def performance_model_extraction_review_item(
    observation: AthletePerformanceObservation,
    metric: PerformanceMetricDefinition,
) -> dict[str, object]:
    confidence = observation.confidence if observation.confidence is not None else 0.0
    model_assisted = performance_observation_model_assisted(observation)
    flags: list[str] = []
    if confidence < 0.75:
        flags.append("low_confidence")
    if metric.category in {MetricCategory.WELLNESS, MetricCategory.PHYSICAL}:
        flags.append("player_safety_relevant")
    if model_assisted:
        flags.append("model_assisted")
    if observation.source in {MetricSource.AUDIO_NARRATION, MetricSource.AGENT_EXTRACTED}:
        flags.append("narrative_source")
    priority = "high" if "low_confidence" in flags or "player_safety_relevant" in flags else "standard"
    if confidence >= 0.88 and model_assisted and priority == "standard":
        recommended_action = "verify"
    elif confidence < 0.65:
        recommended_action = "correct_or_reject"
    else:
        recommended_action = "coach_review"
    observed_at = observation.observed_at
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    age_hours = max((datetime.now(UTC) - observed_at).total_seconds() / 3600, 0.0)
    return {
        "observation": observation,
        "metric_code": metric.code,
        "metric_name": metric.name,
        "metric_category": metric.category,
        "unit": metric.unit,
        "model_assisted": model_assisted,
        "model_policy": performance_observation_model_policy(observation),
        "evidence_ref": performance_observation_evidence_ref(observation),
        "review_priority": priority,
        "confidence_label": performance_confidence_label(confidence),
        "recommended_action": recommended_action,
        "review_reason": performance_model_extraction_review_reason(observation, metric, confidence, model_assisted),
        "flags": flags,
        "age_hours": round(age_hours, 2),
    }


def performance_observation_model_assisted(observation: AthletePerformanceObservation) -> bool:
    notes = observation.notes or ""
    return "model_assisted_extraction" in notes or "model_webhook_extraction" in notes or "Model:" in notes


def performance_observation_model_policy(observation: AthletePerformanceObservation) -> str | None:
    notes = observation.notes or ""
    match = re.search(r"Model:\s*([^(.]+)", notes)
    if match:
        return match.group(1).strip()
    return get_settings().performance_model_extraction_model if performance_observation_model_assisted(observation) else None


def performance_observation_evidence_ref(observation: AthletePerformanceObservation) -> str | None:
    notes = observation.notes or ""
    match = re.search(r"evidence\s+([^.\s]+)", notes)
    return match.group(1).strip() if match else None


def performance_confidence_label(confidence: float) -> str:
    if confidence >= 0.88:
        return "high"
    if confidence >= 0.72:
        return "medium"
    return "low"


def performance_model_extraction_review_reason(
    observation: AthletePerformanceObservation,
    metric: PerformanceMetricDefinition,
    confidence: float,
    model_assisted: bool,
) -> str:
    source = observation.source.value.replace("_", " ")
    method = "model-assisted" if model_assisted else "parser-derived"
    return (
        f"{metric.name} from {source} is {method} evidence at "
        f"{round(confidence * 100)}% confidence and remains pending human verification."
    )


def performance_model_extraction_queue_recommendations(items: list[dict[str, object]]) -> list[str]:
    if not items:
        return ["No model-extraction observations are waiting for review."]
    recommendations = [
        "Review high-priority safety or low-confidence observations before using them in player guidance.",
    ]
    high_confidence = sum(
        1
        for item in items
        if item["model_assisted"] and item["confidence_label"] == "high"
    )
    if high_confidence:
        recommendations.append(f"{high_confidence} high-confidence model-assisted observation(s) are candidates for bulk verification.")
    return recommendations


async def run_performance_forecast_validation(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: PerformanceForecastValidationRunCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    await ensure_manage_performance(authz, identity, payload.organization_id)
    if payload.athlete_profile_id is not None:
        await get_athlete_profile(db, payload.athlete_profile_id, payload.organization_id)
    return await create_performance_forecast_validation_run(
        db,
        payload.organization_id,
        athlete_profile_id=payload.athlete_profile_id,
        created_by_person_id=identity.person_id,
    )


async def create_performance_forecast_validation_run(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID | None = None,
    created_by_person_id: UUID | None = None,
) -> dict[str, object]:
    settings = get_settings()
    profile_ids = await forecast_validation_profile_ids(db, organization_id, athlete_profile_id)
    metric_rows = await forecast_validation_metric_rows(db, organization_id, profile_ids)
    details = [forecast_validation_metric_detail(*row) for row in metric_rows]
    evaluated = [detail for detail in details if detail["absolute_error"] is not None]
    passed_count = sum(1 for detail in evaluated if detail["passed"])
    drift_count = sum(1 for detail in evaluated if detail["drifted"])
    mean_absolute_error = (
        round(sum(float(detail["absolute_error"]) for detail in evaluated) / len(evaluated), 4)
        if evaluated
        else 0.0
    )
    mean_relative_error = (
        round(sum(float(detail["relative_error"] or 0.0) for detail in evaluated) / len(evaluated), 4)
        if evaluated
        else 0.0
    )
    max_absolute_error = (
        round(max(float(detail["absolute_error"]) for detail in evaluated), 4)
        if evaluated
        else 0.0
    )
    drift_level = forecast_validation_drift_level(mean_relative_error, drift_count, len(evaluated))
    recommendation = forecast_validation_recommendation(drift_level, mean_relative_error, drift_count, len(evaluated))
    run = PerformanceForecastValidationRun(
        organization_id=organization_id,
        athlete_profile_id=athlete_profile_id,
        model_policy=forecast_validation_model_policy(settings),
        forecast_mode=settings.performance_forecast_mode,
        metric_count=len(details),
        evaluated_count=len(evaluated),
        passed_count=passed_count,
        drift_count=drift_count,
        mean_absolute_error=mean_absolute_error,
        mean_relative_error=mean_relative_error,
        max_absolute_error=max_absolute_error,
        drift_level=drift_level,
        recommendation=recommendation,
        details_json=stable_payload_text({"details": details}),
        created_by_person_id=created_by_person_id,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return forecast_validation_run_read(run)


async def list_performance_forecast_validation_runs(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    athlete_profile_id: UUID | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    await ensure_manage_performance(authz, identity, organization_id)
    query = (
        select(PerformanceForecastValidationRun)
        .where(PerformanceForecastValidationRun.organization_id == organization_id)
        .order_by(PerformanceForecastValidationRun.created_at.desc())
        .limit(max(1, min(limit, 50)))
    )
    if athlete_profile_id is not None:
        query = query.where(PerformanceForecastValidationRun.athlete_profile_id == athlete_profile_id)
    rows = list((await db.scalars(query)).all())
    return [forecast_validation_run_read(row) for row in rows]


async def send_performance_forecast_validation_alert(
    db: AsyncSession,
    identity: CurrentIdentity,
    validation_run_id: UUID,
    authz: AuthorizationService,
    dry_run: bool = False,
    repeat_after_hours: int = 24,
    channels: list[CommunicationChannel] | None = None,
) -> dict[str, object]:
    run = await db.get(PerformanceForecastValidationRun, validation_run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast validation run not found")
    await ensure_manage_performance(authz, identity, run.organization_id)
    return await send_performance_forecast_validation_alert_for_run(
        db,
        validation_run_id,
        repeat_after_hours=repeat_after_hours,
        channels=channels,
        dry_run=dry_run,
    )


async def send_performance_forecast_validation_alert_for_run(
    db: AsyncSession,
    validation_run_id: UUID,
    *,
    repeat_after_hours: int = 24,
    channels: list[CommunicationChannel] | None = None,
    dry_run: bool = False,
) -> dict[str, object]:
    run = await db.get(PerformanceForecastValidationRun, validation_run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast validation run not found")
    alert_channels = normalized_performance_alert_channels(channels)
    recipient_ids = await performance_manager_recipient_ids(db, run.organization_id)
    sent = False
    message_ids: list[UUID] = []
    skipped_reason = None
    if run.drift_level not in {"watch", "high"}:
        skipped_reason = f"Forecast validation drift level {run.drift_level} does not require an alert."
    elif not recipient_ids:
        skipped_reason = "No eligible forecast-drift alert recipients found."
    elif repeat_after_hours > 0 and await recent_forecast_validation_alert_exists(
        db, run.organization_id, repeat_after_hours
    ):
        skipped_reason = f"A forecast drift alert was already sent within the last {repeat_after_hours} hour(s)."
    elif dry_run:
        sent = False
    else:
        messages = await create_forecast_validation_alert_messages(
            db,
            run,
            recipient_ids,
            alert_channels,
        )
        await db.commit()
        message_ids = [message.id for message in messages]
        sent = True

    return {
        "organization_id": run.organization_id,
        "validation_run_id": run.id,
        "drift_level": run.drift_level,
        "sent": sent,
        "dry_run": dry_run,
        "channels": alert_channels,
        "channel_count": len(alert_channels),
        "recipient_count": len(recipient_ids) * len(alert_channels),
        "message_ids": message_ids,
        "skipped_reason": skipped_reason,
        "validation_run": forecast_validation_run_read(run),
    }


async def run_performance_forecast_validation_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    limit: int = 25,
    auto_alerts: bool = False,
    alert_repeat_after_hours: int = 24,
    alert_channels: list[CommunicationChannel] | None = None,
    dry_run_alerts: bool = False,
) -> PerformanceForecastValidationWorkerRunRead:
    normalized_alert_channels = normalized_performance_alert_channels(alert_channels)
    organization_ids = await forecast_validation_worker_organization_ids(db, organization_id, limit)
    executed_count = 0
    failed_count = 0
    run_ids: list[UUID] = []
    alert_message_ids: list[UUID] = []
    alert_skipped_reasons: dict[str, int] = {}
    metric_count = 0
    evaluated_count = 0
    drift_count = 0
    watch_count = 0
    high_count = 0
    alerted_count = 0
    alert_skipped_count = 0
    alert_failed_count = 0

    for org_id in organization_ids:
        try:
            run = await create_performance_forecast_validation_run(db, org_id)
            executed_count += 1
            run_ids.append(run["id"])
            metric_count += int(run["metric_count"])
            evaluated_count += int(run["evaluated_count"])
            drift_count += int(run["drift_count"])
            if run["drift_level"] == "watch":
                watch_count += 1
            if run["drift_level"] == "high":
                high_count += 1
            if auto_alerts:
                try:
                    alert = await send_performance_forecast_validation_alert_for_run(
                        db,
                        run["id"],
                        repeat_after_hours=alert_repeat_after_hours,
                        channels=normalized_alert_channels,
                        dry_run=dry_run_alerts,
                    )
                    if alert["sent"]:
                        alerted_count += 1
                        alert_message_ids.extend(alert["message_ids"])
                    else:
                        alert_skipped_count += 1
                        reason = str(
                            alert["skipped_reason"] or ("Dry run only." if dry_run_alerts else "Alert not sent.")
                        )
                        alert_skipped_reasons[reason] = alert_skipped_reasons.get(reason, 0) + 1
                except Exception:
                    alert_failed_count += 1
                    await db.rollback()
        except Exception:
            failed_count += 1
            await db.rollback()

    return PerformanceForecastValidationWorkerRunRead(
        organization_id=organization_id,
        auto_alerts=auto_alerts,
        dry_run_alerts=dry_run_alerts,
        alert_repeat_after_hours=alert_repeat_after_hours,
        alert_channels=normalized_alert_channels,
        alert_channel_count=len(normalized_alert_channels),
        eligible_count=len(organization_ids),
        executed_count=executed_count,
        skipped_count=max(len(organization_ids) - executed_count - failed_count, 0),
        failed_count=failed_count,
        run_ids=run_ids,
        metric_count=metric_count,
        evaluated_count=evaluated_count,
        drift_count=drift_count,
        watch_count=watch_count,
        high_count=high_count,
        alerted_count=alerted_count,
        alert_skipped_count=alert_skipped_count,
        alert_failed_count=alert_failed_count,
        alert_message_ids=alert_message_ids,
        alert_skipped_reasons=alert_skipped_reasons,
    )


async def ingest_performance_wearable_webhook(
    db: AsyncSession,
    payload: PerformanceWearableWebhookCreate,
    *,
    signature_required: bool,
    signature_validated: bool,
) -> dict[str, object]:
    athlete_profile = await get_athlete_profile(db, payload.athlete_profile_id, payload.organization_id)
    if payload.event_id is not None:
        event = await db.get(Event, payload.event_id)
        if event is None or event.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    provider = normalized_provider_name(payload.source_provider) or "wearable"
    payload_hash = stable_payload_hash(payload.payload)
    existing = await db.scalar(
        select(PerformanceWearableIngestEvent)
        .where(PerformanceWearableIngestEvent.organization_id == payload.organization_id)
        .where(PerformanceWearableIngestEvent.athlete_profile_id == athlete_profile.id)
        .where(PerformanceWearableIngestEvent.provider == provider)
        .where(PerformanceWearableIngestEvent.external_event_id == payload.external_event_id)
    )
    if existing is not None:
        return wearable_webhook_result(existing, replayed=True, observation_ids=[])

    metrics = await wearable_webhook_metric_definitions(db, payload)
    observation_ids: list[UUID] = []
    skipped_metric_count = 0
    evidence_text = stable_payload_text(payload.payload)
    received_at = datetime.now(UTC)

    for metric in metrics:
        provider_match = provider_specific_metric_match(payload.payload, metric, provider)
        structured_match = provider_match or structured_metric_match(payload.payload, metric)
        if structured_match is None:
            skipped_metric_count += 1
            continue
        parsed_payload = PerformanceIngestionCreate(
            organization_id=payload.organization_id,
            athlete_profile_id=athlete_profile.id,
            metric_definition_id=metric.id,
            event_id=payload.event_id,
            source=MetricSource.WEARABLE,
            source_provider=provider,
            evidence_ref=f"{provider}://webhook/{payload.external_event_id}",
            evidence_text=evidence_text,
        )
        parsed = parse_performance_evidence(parsed_payload, metric)
        value = float(parsed["value"])
        parser_warnings = list(parsed["warnings"])
        observation = AthletePerformanceObservation(
            organization_id=payload.organization_id,
            athlete_profile_id=athlete_profile.id,
            metric_definition_id=metric.id,
            event_id=payload.event_id,
            recorded_by_person_id=None,
            value=value,
            raw_value=evidence_raw_value(evidence_text, value),
            observed_at=parsed["observed_at"] or received_at,
            source=MetricSource.WEARABLE,
            confidence=float(parsed["confidence"]),
            verification_status=MetricVerificationStatus.PENDING_REVIEW,
            notes=(
                f"Wearable webhook {provider}:{payload.external_event_id} parsed {metric.name} "
                f"via {parsed['method']}. "
                f"{'Warnings: ' + '; '.join(parser_warnings) + '. ' if parser_warnings else ''}"
                "Review before promoting to verified."
            ),
        )
        db.add(observation)
        await db.flush()
        observation_ids.append(observation.id)

    ingest_event = PerformanceWearableIngestEvent(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile.id,
        event_id=payload.event_id,
        provider=provider,
        external_event_id=payload.external_event_id,
        payload_hash=payload_hash,
        received_at=received_at,
        signature_required=signature_required,
        signature_validated=signature_validated,
        observation_count=len(observation_ids),
        skipped_metric_count=skipped_metric_count,
    )
    db.add(ingest_event)
    await db.commit()
    await db.refresh(ingest_event)
    return wearable_webhook_result(ingest_event, replayed=False, observation_ids=observation_ids)


async def create_wearable_provider_connection(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: PerformanceWearableConnectionCreate,
    authz: AuthorizationService,
) -> PerformanceWearableProviderConnection:
    athlete_profile = await get_athlete_profile(db, payload.athlete_profile_id, payload.organization_id)
    await ensure_manage_performance(authz, identity, payload.organization_id)
    provider = normalized_provider_name(payload.provider) or payload.provider
    connection = PerformanceWearableProviderConnection(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile.id,
        provider=provider,
        display_name=payload.display_name,
        external_athlete_ref=payload.external_athlete_ref,
        status=payload.status,
        auth_type=payload.auth_type,
        scopes=encode_string_list(payload.scopes),
        access_token_secret_path=payload.access_token_secret_path,
        refresh_token_secret_path=payload.refresh_token_secret_path,
        webhook_secret_path=payload.webhook_secret_path,
        token_expires_at=payload.token_expires_at,
        provider_pull_url=payload.provider_pull_url,
        provider_pull_cursor_param=payload.provider_pull_cursor_param,
        provider_pull_since_param=payload.provider_pull_since_param,
        provider_pull_until_param=payload.provider_pull_until_param,
        sync_cursor=payload.sync_cursor,
        webhook_registered=payload.webhook_registered,
        provider_webhook_registration_url=payload.provider_webhook_registration_url,
        provider_webhook_callback_url=payload.provider_webhook_callback_url,
        provider_webhook_event_types=encode_string_list(payload.provider_webhook_event_types),
        default_metric_definition_ids=encode_uuid_list(payload.default_metric_definition_ids),
    )
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    return connection


async def list_wearable_provider_connections(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    athlete_profile_id: UUID | None = None,
) -> list[PerformanceWearableProviderConnection]:
    await ensure_manage_performance(authz, identity, organization_id)
    statement = select(PerformanceWearableProviderConnection).where(
        PerformanceWearableProviderConnection.organization_id == organization_id
    )
    if athlete_profile_id is not None:
        statement = statement.where(PerformanceWearableProviderConnection.athlete_profile_id == athlete_profile_id)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    PerformanceWearableProviderConnection.provider,
                    PerformanceWearableProviderConnection.created_at.desc(),
                )
            )
        ).all()
    )


async def run_wearable_provider_sync(
    db: AsyncSession,
    identity: CurrentIdentity,
    connection_id: UUID,
    payload: PerformanceWearableSyncRunCreate,
    authz: AuthorizationService,
) -> PerformanceWearableProviderSyncRun:
    connection = await db.get(PerformanceWearableProviderConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wearable connection not found")
    await ensure_manage_performance(authz, identity, connection.organization_id)
    return await execute_wearable_provider_sync(db, connection, payload)


async def execute_wearable_provider_sync(
    db: AsyncSession,
    connection: PerformanceWearableProviderConnection,
    payload: PerformanceWearableSyncRunCreate,
) -> PerformanceWearableProviderSyncRun:
    started_at = datetime.now(UTC)
    status_value = "needs_credentials"
    message = "Connection is missing an access-token secret path or sample provider payload."
    observation_count = 0
    skipped_metric_count = 0
    replayed = False
    external_event_id = payload.external_event_id
    provider_status_code: int | None = None
    provider_response_hash: str | None = None
    provider_page_count = 0
    provider_rate_limited = False
    provider_retry_after_seconds: int | None = None

    if payload.payload is not None:
        external_event_id = external_event_id or f"sync-{connection.provider}-{started_at.isoformat()}"
        ingest = await ingest_wearable_sync_payload(
            db,
            connection,
            payload.payload,
            external_event_id=external_event_id,
            metric_definition_ids=payload.metric_definition_ids,
        )
        observation_count = int(ingest["observation_count"])
        skipped_metric_count = int(ingest["skipped_metric_count"])
        replayed = bool(ingest["replayed"])
        status_value = "replayed" if replayed else "completed"
        message = (
            f"Synced {observation_count} observation(s) from {connection.provider} sample payload."
            if not replayed
            else f"Skipped duplicate {connection.provider} provider event {external_event_id}."
        )
        connection.last_sync_at = started_at
        connection.sync_cursor = external_event_id
        connection.status = "active"
    elif connection.access_token_secret_path and connection.provider_pull_url:
        pulled = await pull_wearable_provider_payload(connection, payload)
        provider_status_code = pulled["provider_status_code"]
        provider_response_hash = pulled["provider_response_hash"]
        provider_page_count = int(pulled["provider_page_count"])
        provider_rate_limited = bool(pulled["provider_rate_limited"])
        provider_retry_after_seconds = (
            int(pulled["provider_retry_after_seconds"])
            if pulled["provider_retry_after_seconds"] is not None
            else None
        )
        external_event_id = external_event_id or str(pulled["external_event_id"])
        if provider_rate_limited:
            status_value = "rate_limited"
            message = (
                f"{connection.provider} provider pull was rate-limited"
                f"{f' for {provider_retry_after_seconds}s' if provider_retry_after_seconds else ''} "
                f"after {provider_page_count} page(s)."
            )
        else:
            replayed_pages = 0
            for index, page in enumerate(pulled["payloads"], start=1):
                page_event_id = str(page["external_event_id"])
                ingest = await ingest_wearable_sync_payload(
                    db,
                    connection,
                    page["payload"],
                    external_event_id=page_event_id,
                    metric_definition_ids=payload.metric_definition_ids,
                )
                observation_count += int(ingest["observation_count"])
                skipped_metric_count += int(ingest["skipped_metric_count"])
                if bool(ingest["replayed"]):
                    replayed_pages += 1
                if index == 1:
                    replayed = bool(ingest["replayed"])
            status_value = "replayed" if replayed_pages == provider_page_count else "completed"
            message = (
                f"Pulled {observation_count} observation(s) from {connection.provider} provider API "
                f"across {provider_page_count} page(s) with HTTP {provider_status_code}."
                if status_value == "completed"
                else f"Skipped duplicate {connection.provider} provider pull page(s): {replayed_pages}/{provider_page_count}."
            )
            connection.last_sync_at = started_at
            connection.sync_cursor = str(pulled["next_cursor"] or external_event_id)
            connection.status = "active"
    elif connection.access_token_secret_path:
        status_value = "pull_not_configured"
        message = (
            f"{connection.provider} credentials are configured in OpenBao/env path; "
            "provider pull URL is not configured for this connection."
        )
    run = PerformanceWearableProviderSyncRun(
        organization_id=connection.organization_id,
        connection_id=connection.id,
        athlete_profile_id=connection.athlete_profile_id,
        provider=connection.provider,
        external_event_id=external_event_id,
        status=status_value,
        sync_mode=payload.sync_mode,
        started_at=started_at,
        completed_at=datetime.now(UTC),
        observation_count=observation_count,
        skipped_metric_count=skipped_metric_count,
        replayed=replayed,
        provider_status_code=provider_status_code,
        provider_response_hash=provider_response_hash,
        provider_page_count=provider_page_count,
        provider_rate_limited=provider_rate_limited,
        provider_retry_after_seconds=provider_retry_after_seconds,
        message=message,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def list_wearable_provider_sync_runs(
    db: AsyncSession,
    identity: CurrentIdentity,
    connection_id: UUID,
    authz: AuthorizationService,
) -> list[PerformanceWearableProviderSyncRun]:
    connection = await db.get(PerformanceWearableProviderConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wearable connection not found")
    await ensure_manage_performance(authz, identity, connection.organization_id)
    return list(
        (
            await db.scalars(
                select(PerformanceWearableProviderSyncRun)
                .where(PerformanceWearableProviderSyncRun.connection_id == connection.id)
                .order_by(PerformanceWearableProviderSyncRun.started_at.desc())
            )
        ).all()
    )


async def create_performance_hardware_kit(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: PerformanceHardwareKitCreate,
    authz: AuthorizationService,
) -> PerformanceHardwareKit:
    await ensure_manage_performance(authz, identity, payload.organization_id)
    kit = PerformanceHardwareKit(
        organization_id=payload.organization_id,
        name=payload.name,
        kit_type=payload.kit_type.strip().lower(),
        provider=normalized_provider_name(payload.provider) or payload.provider.strip().lower(),
        sport=payload.sport.strip().lower(),
        level=payload.level.strip().lower(),
        recommended_camera_count=payload.recommended_camera_count,
        recommended_gps_unit_count=payload.recommended_gps_unit_count,
        supported_metrics_json=encode_string_list(payload.supported_metrics),
        setup_steps_json=encode_string_list(
            payload.setup_steps or default_performance_hardware_setup_steps(payload.kit_type, payload.provider)
        ),
        estimated_cost=payload.estimated_cost,
        currency=payload.currency.upper(),
        status=payload.status.strip().lower(),
        notes=payload.notes,
    )
    db.add(kit)
    await db.commit()
    await db.refresh(kit)
    return kit


async def list_performance_hardware_kits(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    sport: str | None = None,
) -> list[PerformanceHardwareKit]:
    await ensure_manage_performance(authz, identity, organization_id)
    statement = select(PerformanceHardwareKit).where(PerformanceHardwareKit.organization_id == organization_id)
    if sport:
        statement = statement.where(PerformanceHardwareKit.sport == sport.strip().lower())
    return list((await db.scalars(statement.order_by(PerformanceHardwareKit.created_at.desc()))).all())


async def provision_performance_hardware_device(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: PerformanceHardwareDeviceCreate,
    authz: AuthorizationService,
) -> PerformanceHardwareDevice:
    await ensure_manage_performance(authz, identity, payload.organization_id)
    if payload.kit_id is not None:
        kit = await db.get(PerformanceHardwareKit, payload.kit_id)
        if kit is None or kit.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Performance hardware kit not found")
    if payload.team_id is not None:
        team = await db.get(Team, payload.team_id)
        if team is None or team.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if payload.facility_id is not None:
        facility = await db.get(Facility, payload.facility_id)
        if facility is None or facility.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    if payload.calibration_id is not None:
        calibration = await db.get(PerformanceMatchPitchCalibration, payload.calibration_id)
        if calibration is None or calibration.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match pitch calibration not found")
    provider = normalized_provider_name(payload.provider) or payload.provider.strip().lower()
    api_key_hash = hashlib.sha256(payload.api_key.encode()).hexdigest() if payload.api_key else None
    device = PerformanceHardwareDevice(
        organization_id=payload.organization_id,
        kit_id=payload.kit_id,
        team_id=payload.team_id,
        facility_id=payload.facility_id,
        device_type=payload.device_type.strip().lower(),
        provider=provider,
        device_label=payload.device_label,
        external_device_id=payload.external_device_id,
        firmware_version=payload.firmware_version,
        status=payload.status.strip().lower(),
        api_key_secret_path=payload.api_key_secret_path,
        api_key_hash=api_key_hash,
        custody_mode=payload.custody_mode.strip().lower(),
        metrics_supported_json=encode_string_list(payload.metrics_supported or default_hardware_device_metrics(payload.device_type)),
        calibration_id=payload.calibration_id,
        battery_percent=payload.battery_percent,
        notes=payload.notes,
    )
    db.add(device)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Performance hardware device already exists for this provider",
        ) from exc
    await db.refresh(device)
    return device


async def list_performance_hardware_devices(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    kit_id: UUID | None = None,
) -> list[PerformanceHardwareDevice]:
    await ensure_manage_performance(authz, identity, organization_id)
    statement = select(PerformanceHardwareDevice).where(PerformanceHardwareDevice.organization_id == organization_id)
    if kit_id is not None:
        statement = statement.where(PerformanceHardwareDevice.kit_id == kit_id)
    return list((await db.scalars(statement.order_by(PerformanceHardwareDevice.created_at.desc()))).all())


async def run_performance_hardware_sync(
    db: AsyncSession,
    identity: CurrentIdentity,
    device_id: UUID,
    payload: PerformanceHardwareSyncRunCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    device = await db.get(PerformanceHardwareDevice, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Performance hardware device not found")
    await ensure_manage_performance(authz, identity, device.organization_id)
    started_at = datetime.now(UTC)
    tracking_run_id: UUID | None = None
    message = f"{device.provider} {device.device_type} sync recorded."
    if payload.battery_percent is not None:
        device.battery_percent = payload.battery_percent
    device.last_seen_at = started_at
    device.status = "active"
    if payload.tracking_samples:
        if payload.video_asset_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Hardware tracking sync requires a match video asset",
            )
        calibration_id = payload.calibration_id or device.calibration_id
        tracking = await create_match_tracking_run(
            db,
            identity,
            payload.video_asset_id,
            PerformanceMatchTrackingRunCreate(
                organization_id=device.organization_id,
                calibration_id=calibration_id,
                source_provider=f"{device.provider}_{device.device_type}_hardware",
                replace_existing=payload.replace_existing_tracking,
                samples=payload.tracking_samples,
            ),
            authz,
        )
        tracking_run_id = tracking["id"] if isinstance(tracking["id"], UUID) else UUID(str(tracking["id"]))
        message = (
            f"Synced {len(payload.tracking_samples)} tracking sample(s) from {device.device_label} "
            f"into match run {tracking_run_id}."
        )
    payload_hash = hardware_sync_payload_hash(payload)
    run = PerformanceHardwareSyncRun(
        organization_id=device.organization_id,
        device_id=device.id,
        video_asset_id=payload.video_asset_id,
        tracking_run_id=tracking_run_id,
        provider=device.provider,
        sync_mode=payload.sync_mode.strip().lower(),
        status="completed" if payload.metrics or payload.tracking_samples or payload.payload else "heartbeat",
        started_at=started_at,
        completed_at=datetime.now(UTC),
        metrics_ingested=len(payload.metrics),
        sample_count=len(payload.tracking_samples),
        payload_hash=payload_hash,
        message=message,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return await performance_hardware_sync_run_read(db, run)


async def list_performance_hardware_sync_runs(
    db: AsyncSession,
    identity: CurrentIdentity,
    device_id: UUID,
    authz: AuthorizationService,
) -> list[dict[str, object]]:
    device = await db.get(PerformanceHardwareDevice, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Performance hardware device not found")
    await ensure_manage_performance(authz, identity, device.organization_id)
    runs = list(
        (
            await db.scalars(
                select(PerformanceHardwareSyncRun)
                .where(PerformanceHardwareSyncRun.device_id == device.id)
                .order_by(PerformanceHardwareSyncRun.started_at.desc())
            )
        ).all()
    )
    return [await performance_hardware_sync_run_read(db, run) for run in runs]


async def performance_hardware_sync_run_read(
    db: AsyncSession,
    run: PerformanceHardwareSyncRun,
) -> dict[str, object]:
    tracking_run = await db.get(PerformanceMatchTrackingRun, run.tracking_run_id) if run.tracking_run_id else None
    return {
        "id": run.id,
        "organization_id": run.organization_id,
        "device_id": run.device_id,
        "video_asset_id": run.video_asset_id,
        "tracking_run_id": run.tracking_run_id,
        "provider": run.provider,
        "sync_mode": run.sync_mode,
        "status": run.status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "metrics_ingested": run.metrics_ingested,
        "sample_count": run.sample_count,
        "payload_hash": run.payload_hash,
        "message": run.message,
        "tracking_run": await match_tracking_run_read(db, tracking_run) if tracking_run is not None else None,
    }


def default_performance_hardware_setup_steps(kit_type: str, provider: str) -> list[str]:
    normalized = f"{kit_type} {provider}".lower()
    if "gps" in normalized:
        return [
            "Charge and label every GPS unit before assignment.",
            "Pair each tracker to athlete or jersey identifiers.",
            "Run a five-minute warm-up sync and verify speed/distance packets.",
            "Upload match or training payloads after the session.",
        ]
    return [
        "Mount cameras high and stable with full pitch visibility.",
        "Create or attach a pitch calibration profile before match tracking.",
        "Record a short test clip and verify player tracks before kickoff.",
        "Sync tracking samples into AfroLete for coach review.",
    ]


def default_hardware_device_metrics(device_type: str) -> list[str]:
    normalized = device_type.lower()
    if "gps" in normalized:
        return ["speed", "distance", "acceleration", "sprint_count", "player_load"]
    if "camera" in normalized:
        return ["player_location", "distance", "speed", "heatmap", "tactical_shape"]
    return ["speed", "distance", "acceleration"]


def hardware_sync_payload_hash(payload: PerformanceHardwareSyncRunCreate) -> str:
    return hashlib.sha256(
        json.dumps(payload.model_dump(mode="json"), sort_keys=True, default=str).encode()
    ).hexdigest()


async def register_wearable_provider_webhook(
    db: AsyncSession,
    identity: CurrentIdentity,
    connection_id: UUID,
    payload: PerformanceWearableWebhookRegistrationCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    connection = await db.get(PerformanceWearableProviderConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wearable connection not found")
    await ensure_manage_performance(authz, identity, connection.organization_id)
    now = datetime.now(UTC)
    registration_url = payload.registration_url or connection.provider_webhook_registration_url
    event_types = payload.event_types or decode_string_list(connection.provider_webhook_event_types) or [
        "metrics.created",
        "recovery.updated",
        "sleep.updated",
    ]
    registration_payload = wearable_webhook_registration_payload(connection, payload, event_types)
    payload_hash = stable_payload_hash(registration_payload)
    provider_status_code: int | None = None
    registered = False
    error: str | None = None
    message: str

    if registration_url:
        if not connection.access_token_secret_path:
            raise HTTPException(status_code=422, detail="Wearable connection needs an access token before provider webhook registration")
        access_token = await resolve_wearable_token_secret(connection.access_token_secret_path, "access_token")
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.post(
                    registration_url,
                    json=registration_payload,
                    headers={
                        "Accept": "application/json",
                        "Authorization": f"Bearer {access_token}",
                        "X-AfroLete-Provider": connection.provider,
                        "X-AfroLete-Athlete-Ref": connection.external_athlete_ref,
                    },
                )
                provider_status_code = response.status_code
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                provider_status_code = exc.response.status_code
                error = f"Provider webhook registration failed with HTTP {provider_status_code}"
            except httpx.HTTPError as exc:
                error = f"Provider webhook registration failed: {exc}"
        registered = error is None
        message = (
            f"{connection.provider} webhook registration accepted by provider."
            if registered
            else str(error)
        )
    else:
        registered = True
        provider_status_code = None
        message = f"{connection.provider} webhook registration payload prepared for provider console entry."

    connection.provider_webhook_registration_url = registration_url
    connection.provider_webhook_callback_url = payload.callback_url
    connection.provider_webhook_event_types = encode_string_list(event_types)
    connection.provider_webhook_registration_status_code = provider_status_code
    connection.provider_webhook_registration_hash = payload_hash
    connection.provider_webhook_registration_error = error
    if registered:
        connection.webhook_registered = True
        connection.provider_webhook_registered_at = now
        if payload.signing_secret_path:
            connection.webhook_secret_path = payload.signing_secret_path
    else:
        connection.webhook_registered = False
    await db.commit()
    await db.refresh(connection)
    return {
        "connection": connection,
        "status": "registered" if registered else "failed",
        "registered": registered,
        "provider_status_code": provider_status_code,
        "registration_payload_hash": payload_hash,
        "message": message,
    }


def wearable_webhook_registration_payload(
    connection: PerformanceWearableProviderConnection,
    payload: PerformanceWearableWebhookRegistrationCreate,
    event_types: list[str],
) -> dict[str, object]:
    registration_payload: dict[str, object] = {
        "callback_url": payload.callback_url,
        "athlete_ref": connection.external_athlete_ref,
        "event_types": event_types,
        "connection_id": str(connection.id),
        "organization_id": str(connection.organization_id),
        "provider": connection.provider,
    }
    if payload.signing_secret_path:
        registration_payload["signing_secret_path"] = payload.signing_secret_path
    registration_payload.update(payload.provider_payload)
    return registration_payload


async def run_wearable_pull_retry_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    limit: int = 25,
    max_pages: int = 3,
    default_retry_after_seconds: int = 300,
    provider_retry_after_seconds: dict[str, int] | None = None,
    provider_max_pages: dict[str, int] | None = None,
) -> PerformanceWearablePullRetryWorkerRunRead:
    settings = get_settings()
    provider_retry_after_seconds = normalized_provider_policy_map(
        provider_retry_after_seconds
        if provider_retry_after_seconds is not None
        else settings.performance_wearable_provider_retry_after_seconds
    )
    provider_max_pages = normalized_provider_policy_map(
        provider_max_pages if provider_max_pages is not None else settings.performance_wearable_provider_max_pages
    )
    rows = await wearable_pull_retry_rows(
        db,
        organization_id=organization_id,
        limit=limit,
        default_retry_after_seconds=default_retry_after_seconds,
        provider_retry_after_seconds=provider_retry_after_seconds,
    )
    retried_count = 0
    failed_count = 0
    provider_policy_matches: dict[str, int] = {}
    connection_ids: list[UUID] = []
    sync_run_ids: list[UUID] = []
    for previous_run, connection in rows:
        provider = provider_policy_key(connection.provider)
        if provider in provider_retry_after_seconds or provider in provider_max_pages:
            provider_policy_matches[provider] = provider_policy_matches.get(provider, 0) + 1
        try:
            retry_run = await execute_wearable_provider_sync(
                db,
                connection,
                PerformanceWearableSyncRunCreate(
                    sync_mode="pull_retry",
                    metric_definition_ids=decode_uuid_list(connection.default_metric_definition_ids) or None,
                    max_pages=wearable_provider_max_pages(connection, max_pages, provider_max_pages),
                ),
            )
            retried_count += 1
            connection_ids.append(connection.id)
            sync_run_ids.append(retry_run.id)
        except Exception:
            failed_count += 1
            await db.rollback()
            previous_run.message = (
                f"{previous_run.message or 'Rate-limited provider pull.'} Retry worker failed; check provider credentials."
            )[:4000]
            db.add(previous_run)
            await db.commit()
    return PerformanceWearablePullRetryWorkerRunRead(
        organization_id=organization_id,
        eligible_count=len(rows),
        retried_count=retried_count,
        skipped_count=max(len(rows) - retried_count - failed_count, 0),
        failed_count=failed_count,
        rate_limited_count=sum(1 for run, _ in rows if run.provider_rate_limited),
        provider_retry_after_seconds=provider_retry_after_seconds,
        provider_max_pages=provider_max_pages,
        provider_policy_matches=provider_policy_matches,
        connection_ids=connection_ids,
        sync_run_ids=sync_run_ids,
    )


async def wearable_pull_retry_rows(
    db: AsyncSession,
    organization_id: UUID | None,
    limit: int,
    default_retry_after_seconds: int,
    provider_retry_after_seconds: dict[str, int] | None = None,
) -> list[tuple[PerformanceWearableProviderSyncRun, PerformanceWearableProviderConnection]]:
    provider_retry_after_seconds = normalized_provider_policy_map(provider_retry_after_seconds or {})
    now = datetime.now(UTC)
    statement = (
        select(PerformanceWearableProviderSyncRun, PerformanceWearableProviderConnection)
        .join(
            PerformanceWearableProviderConnection,
            PerformanceWearableProviderConnection.id == PerformanceWearableProviderSyncRun.connection_id,
        )
        .where(PerformanceWearableProviderConnection.provider_pull_url.is_not(None))
        .where(PerformanceWearableProviderConnection.access_token_secret_path.is_not(None))
        .order_by(
            PerformanceWearableProviderSyncRun.connection_id,
            PerformanceWearableProviderSyncRun.completed_at.desc().nullslast(),
            PerformanceWearableProviderSyncRun.started_at.desc(),
        )
        .limit(max(limit * 10, 50))
    )
    if organization_id is not None:
        statement = statement.where(PerformanceWearableProviderSyncRun.organization_id == organization_id)
    rows = list((await db.execute(statement)).all())
    selected: list[tuple[PerformanceWearableProviderSyncRun, PerformanceWearableProviderConnection]] = []
    seen_connections: set[UUID] = set()
    for run, connection in rows:
        if connection.id in seen_connections:
            continue
        seen_connections.add(connection.id)
        if run.status != "rate_limited" or not run.provider_rate_limited:
            continue
        completed_at = as_utc_datetime(run.completed_at) or as_utc_datetime(run.started_at)
        retry_after = wearable_provider_retry_after_seconds(
            run,
            connection,
            default_retry_after_seconds,
            provider_retry_after_seconds,
        )
        if completed_at is not None and completed_at + timedelta(seconds=retry_after) > now:
            continue
        selected.append((run, connection))
        if len(selected) >= limit:
            break
    return selected


def provider_policy_key(provider: str) -> str:
    return provider.strip().lower()


def normalized_provider_policy_map(values: dict[str, int]) -> dict[str, int]:
    return {
        provider_policy_key(provider): max(int(value), 1)
        for provider, value in values.items()
        if provider_policy_key(provider)
    }


def wearable_provider_retry_after_seconds(
    run: PerformanceWearableProviderSyncRun,
    connection: PerformanceWearableProviderConnection,
    default_retry_after_seconds: int,
    provider_retry_after_seconds: dict[str, int],
) -> int:
    if run.provider_retry_after_seconds is not None:
        return max(run.provider_retry_after_seconds, 0)
    return provider_retry_after_seconds.get(
        provider_policy_key(connection.provider),
        max(default_retry_after_seconds, 0),
    )


def wearable_provider_max_pages(
    connection: PerformanceWearableProviderConnection,
    default_max_pages: int,
    provider_max_pages: dict[str, int],
) -> int:
    configured_max_pages = provider_max_pages.get(provider_policy_key(connection.provider), default_max_pages)
    return min(max(configured_max_pages, 1), 10)


async def ingest_wearable_sync_payload(
    db: AsyncSession,
    connection: PerformanceWearableProviderConnection,
    provider_payload: dict[str, object],
    *,
    external_event_id: str,
    metric_definition_ids: list[UUID] | None,
) -> dict[str, object]:
    metric_ids = metric_definition_ids or decode_uuid_list(connection.default_metric_definition_ids)
    webhook_payload = PerformanceWearableWebhookCreate(
        organization_id=connection.organization_id,
        athlete_profile_id=connection.athlete_profile_id,
        source_provider=connection.provider,
        external_event_id=external_event_id,
        payload=provider_payload,
        metric_definition_ids=metric_ids or None,
    )
    return await ingest_performance_wearable_webhook(
        db,
        webhook_payload,
        signature_required=False,
        signature_validated=False,
    )


async def pull_wearable_provider_payload(
    connection: PerformanceWearableProviderConnection,
    payload: PerformanceWearableSyncRunCreate,
) -> dict[str, object]:
    if not connection.provider_pull_url:
        raise HTTPException(status_code=422, detail="Wearable provider pull URL is not configured")
    access_token = await resolve_wearable_token_secret(connection.access_token_secret_path or "", "access_token")
    query = wearable_provider_pull_params(connection, payload, cursor=connection.sync_cursor)
    page_payloads: list[dict[str, object]] = []
    response_hashes: list[str] = []
    next_cursor: str | None = None
    last_status_code: int | None = None
    async with httpx.AsyncClient(timeout=20.0) as client:
        for page_number in range(1, payload.max_pages + 1):
            try:
                response = await client.get(
                    connection.provider_pull_url,
                    params=query,
                    headers={
                        "Accept": "application/json",
                        "Authorization": f"Bearer {access_token}",
                        "X-AfroLete-Provider": connection.provider,
                        "X-AfroLete-Athlete-Ref": connection.external_athlete_ref,
                    },
                )
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail=f"Wearable provider pull failed: {exc}") from exc
            last_status_code = response.status_code
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                return {
                    "payloads": page_payloads,
                    "external_event_id": provider_pull_run_event_id(connection, response_hashes, "rate-limited"),
                    "next_cursor": next_cursor or query.get(connection.provider_pull_cursor_param or ""),
                    "provider_status_code": response.status_code,
                    "provider_response_hash": provider_pull_response_hash(response_hashes, "rate-limited"),
                    "provider_page_count": len(page_payloads),
                    "provider_rate_limited": True,
                    "provider_retry_after_seconds": retry_after_seconds(response.headers.get("Retry-After")),
                }
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise HTTPException(
                    status_code=502,
                    detail=f"Wearable provider pull failed with HTTP {exc.response.status_code}",
                ) from exc
            provider_payload = response.json()
            if not isinstance(provider_payload, dict):
                raise HTTPException(status_code=502, detail="Wearable provider pull returned a non-object payload")
            payload_hash = stable_payload_hash(provider_payload)
            response_hashes.append(payload_hash)
            page_payloads.append(
                {
                    "payload": provider_payload,
                    "external_event_id": provider_external_event_id(connection, provider_payload, payload_hash, page_number),
                }
            )
            next_cursor = provider_next_cursor(provider_payload)
            if not next_cursor or next_cursor == query.get(connection.provider_pull_cursor_param or ""):
                break
            query = wearable_provider_pull_params(connection, payload, cursor=next_cursor)
    response_hash = provider_pull_response_hash(response_hashes, "empty")
    return {
        "payloads": page_payloads,
        "external_event_id": provider_pull_run_event_id(connection, response_hashes, "empty"),
        "next_cursor": next_cursor,
        "provider_status_code": last_status_code,
        "provider_response_hash": response_hash,
        "provider_page_count": len(page_payloads),
        "provider_rate_limited": False,
        "provider_retry_after_seconds": None,
    }


def wearable_provider_pull_params(
    connection: PerformanceWearableProviderConnection,
    payload: PerformanceWearableSyncRunCreate,
    *,
    cursor: str | None,
) -> dict[str, str]:
    params = {"athlete_ref": connection.external_athlete_ref}
    if cursor and connection.provider_pull_cursor_param:
        params[connection.provider_pull_cursor_param] = cursor
    if payload.since and connection.provider_pull_since_param:
        params[connection.provider_pull_since_param] = payload.since.isoformat()
    if payload.until and connection.provider_pull_until_param:
        params[connection.provider_pull_until_param] = payload.until.isoformat()
    return params


def provider_external_event_id(
    connection: PerformanceWearableProviderConnection,
    provider_payload: dict[str, object],
    payload_hash: str,
    page_number: int = 1,
) -> str:
    for key in ("external_event_id", "event_id", "id", "activity_id", "cycle_id"):
        value = provider_payload.get(key)
        if value:
            return str(value)[:180]
    return f"pull-{connection.provider}-{payload_hash[:12]}-p{page_number}"


def provider_next_cursor(provider_payload: dict[str, object]) -> str | None:
    for key in ("next_cursor", "cursor", "sync_cursor", "nextPageToken"):
        value = provider_payload.get(key)
        if value:
            return str(value)[:240]
    return None


def provider_pull_response_hash(response_hashes: list[str], fallback: str) -> str:
    if not response_hashes:
        return stable_secret_hash(f"provider-pull:{fallback}")
    return stable_secret_hash("|".join(response_hashes))


def provider_pull_run_event_id(
    connection: PerformanceWearableProviderConnection,
    response_hashes: list[str],
    fallback: str,
) -> str:
    return f"pull-{connection.provider}-{provider_pull_response_hash(response_hashes, fallback)[:16]}"


def retry_after_seconds(value: str | None) -> int | None:
    if not value:
        return None
    try:
        seconds = int(value)
    except ValueError:
        return None
    return max(seconds, 0)


async def start_wearable_provider_oauth(
    db: AsyncSession,
    identity: CurrentIdentity,
    connection_id: UUID,
    payload: PerformanceWearableOAuthStartCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    connection = await db.get(PerformanceWearableProviderConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wearable connection not found")
    await ensure_manage_performance(authz, identity, connection.organization_id)
    state = token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(seconds=payload.state_ttl_seconds)
    scopes = payload.scopes if payload.scopes is not None else decode_string_list(connection.scopes)
    connection.oauth_client_id = payload.client_id
    connection.oauth_client_secret_path = payload.client_secret_path
    connection.oauth_authorization_url = payload.authorization_url
    connection.oauth_token_url = payload.token_url
    connection.oauth_redirect_uri = payload.redirect_uri
    connection.oauth_state_hash = stable_secret_hash(state)
    connection.oauth_state_expires_at = expires_at
    if payload.scopes is not None:
        connection.scopes = encode_string_list(payload.scopes)
    connection.status = "oauth_pending"
    await db.commit()
    await db.refresh(connection)
    return {
        "connection_id": connection.id,
        "provider": connection.provider,
        "authorization_url": wearable_oauth_authorization_url(connection, scopes, state),
        "state": state,
        "expires_at": expires_at,
        "scopes": scopes,
    }


async def complete_wearable_provider_oauth(
    db: AsyncSession,
    identity: CurrentIdentity,
    connection_id: UUID,
    payload: PerformanceWearableOAuthCallbackCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    connection = await db.get(PerformanceWearableProviderConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wearable connection not found")
    await ensure_manage_performance(authz, identity, connection.organization_id)
    now = datetime.now(UTC)
    if not connection.oauth_state_hash or not hmac.compare_digest(
        connection.oauth_state_hash,
        stable_secret_hash(payload.state),
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid wearable OAuth state")
    state_expires_at = as_utc_datetime(connection.oauth_state_expires_at)
    if state_expires_at is None or state_expires_at <= now:
        connection.status = "oauth_expired"
        await db.commit()
        raise HTTPException(status_code=422, detail="Wearable OAuth state has expired")
    token_response = payload.provider_token_response
    if token_response is None and not payload.access_token_secret_path and connection.oauth_token_url and connection.oauth_client_secret_path:
        token_response = await exchange_wearable_oauth_code(connection, payload.code)
    connection.access_token_secret_path = (
        payload.access_token_secret_path or default_wearable_secret_path(connection, "access-token")
    )
    connection.refresh_token_secret_path = (
        payload.refresh_token_secret_path or default_wearable_secret_path(connection, "refresh-token")
    )
    token_ref = apply_wearable_token_response(
        connection,
        token_response,
        access_token_secret_path=connection.access_token_secret_path,
        refresh_token_secret_path=connection.refresh_token_secret_path,
        explicit_expires_at=payload.token_expires_at,
        now=now,
    )
    connection.oauth_authorized_at = now
    connection.oauth_state_hash = None
    connection.oauth_state_expires_at = None
    connection.status = "authorized"
    await db.commit()
    await db.refresh(connection)
    return {
        "connection": connection,
        "status": "authorized",
        "message": (
            f"{connection.provider} OAuth callback accepted; token material must be stored at "
            f"{connection.access_token_secret_path}."
        ),
        "authorization_code_ref": token_ref or stable_secret_hash(payload.code)[:16],
    }


async def refresh_wearable_provider_token(
    db: AsyncSession,
    identity: CurrentIdentity,
    connection_id: UUID,
    payload: PerformanceWearableTokenRefreshCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    connection = await db.get(PerformanceWearableProviderConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wearable connection not found")
    await ensure_manage_performance(authz, identity, connection.organization_id)
    if not connection.refresh_token_secret_path and not connection.refresh_token_hash:
        raise HTTPException(status_code=422, detail="Wearable connection has no refresh token configured")
    now = datetime.now(UTC)
    old_refresh_hash = connection.refresh_token_hash
    token_response = payload.provider_token_response
    if token_response is None:
        token_response = await refresh_wearable_oauth_token_from_provider(connection)
    access_token_ref = apply_wearable_token_response(
        connection,
        token_response,
        access_token_secret_path=payload.access_token_secret_path or connection.access_token_secret_path,
        refresh_token_secret_path=payload.refresh_token_secret_path or connection.refresh_token_secret_path,
        explicit_expires_at=payload.token_expires_at,
        now=now,
    )
    connection.token_last_refreshed_at = now
    connection.status = "authorized"
    refresh_rotated = bool(old_refresh_hash and connection.refresh_token_hash and connection.refresh_token_hash != old_refresh_hash)
    if refresh_rotated and connection.refresh_token_rotated_at is None:
        connection.refresh_token_rotated_at = now
    await db.commit()
    await db.refresh(connection)
    return {
        "connection": connection,
        "status": "refreshed",
        "message": (
            f"{connection.provider} OAuth token refresh recorded; raw provider tokens were not stored in PostgreSQL."
        ),
        "access_token_ref": access_token_ref,
        "refresh_token_rotated": refresh_rotated,
    }


async def exchange_wearable_oauth_code(
    connection: PerformanceWearableProviderConnection,
    code: str,
) -> PerformanceWearableProviderTokenResponse:
    if not connection.oauth_token_url or not connection.oauth_client_id or not connection.oauth_redirect_uri:
        raise HTTPException(status_code=422, detail="Wearable OAuth token endpoint is not fully configured")
    client_secret = await resolve_wearable_client_secret(connection)
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.post(
                connection.oauth_token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": connection.oauth_redirect_uri,
                    "client_id": connection.oauth_client_id,
                    "client_secret": client_secret,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Wearable OAuth token exchange failed: {exc}") from exc
    return wearable_provider_token_response_from_payload(response.json())


async def refresh_wearable_oauth_token_from_provider(
    connection: PerformanceWearableProviderConnection,
) -> PerformanceWearableProviderTokenResponse:
    if not connection.oauth_token_url or not connection.oauth_client_id or not connection.refresh_token_secret_path:
        raise HTTPException(status_code=422, detail="Wearable OAuth refresh endpoint is not fully configured")
    client_secret = await resolve_wearable_client_secret(connection)
    refresh_token = await resolve_wearable_token_secret(connection.refresh_token_secret_path, "refresh_token")
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.post(
                connection.oauth_token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": connection.oauth_client_id,
                    "client_secret": client_secret,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Wearable OAuth token refresh failed: {exc}") from exc
    return wearable_provider_token_response_from_payload(response.json())


def wearable_oauth_authorization_url(
    connection: PerformanceWearableProviderConnection,
    scopes: list[str],
    state: str,
) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": connection.oauth_client_id or "",
            "redirect_uri": connection.oauth_redirect_uri or "",
            "scope": " ".join(scopes),
            "state": state,
        }
    )
    separator = "&" if "?" in (connection.oauth_authorization_url or "") else "?"
    return f"{connection.oauth_authorization_url}{separator}{query}"


def stable_secret_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def default_wearable_secret_path(
    connection: PerformanceWearableProviderConnection,
    token_name: str,
) -> str:
    return (
        "secret/data/afrolete/wearables/"
        f"{connection.organization_id}/{connection.athlete_profile_id}/{connection.provider}/{token_name}"
    )


def wearable_provider_token_response_from_payload(payload: object) -> PerformanceWearableProviderTokenResponse:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail="Wearable OAuth provider returned a non-object token response")
    return PerformanceWearableProviderTokenResponse(
        access_token=payload.get("access_token") if payload.get("access_token") is not None else None,
        refresh_token=payload.get("refresh_token") if payload.get("refresh_token") is not None else None,
        expires_in=payload.get("expires_in") if payload.get("expires_in") is not None else None,
        token_type=payload.get("token_type") if payload.get("token_type") is not None else None,
        scope=payload.get("scope") if payload.get("scope") is not None else None,
    )


def apply_wearable_token_response(
    connection: PerformanceWearableProviderConnection,
    token_response: PerformanceWearableProviderTokenResponse | None,
    *,
    access_token_secret_path: str | None,
    refresh_token_secret_path: str | None,
    explicit_expires_at: datetime | None,
    now: datetime,
) -> str | None:
    if access_token_secret_path:
        connection.access_token_secret_path = access_token_secret_path
    if refresh_token_secret_path:
        connection.refresh_token_secret_path = refresh_token_secret_path
    if token_response is None:
        connection.token_expires_at = explicit_expires_at
        return None

    if token_response.access_token:
        access_hash = stable_secret_hash(token_response.access_token)
        connection.access_token_hash = access_hash
        connection.access_token_secret_path = (
            access_token_secret_path or connection.access_token_secret_path or default_wearable_secret_path(connection, "access-token")
        )
    elif not connection.access_token_secret_path:
        raise HTTPException(status_code=422, detail="Wearable token response did not include an access token")

    if token_response.refresh_token:
        refresh_hash = stable_secret_hash(token_response.refresh_token)
        if connection.refresh_token_hash and connection.refresh_token_hash != refresh_hash:
            connection.refresh_token_rotated_at = now
        connection.refresh_token_hash = refresh_hash
        connection.refresh_token_secret_path = (
            refresh_token_secret_path
            or connection.refresh_token_secret_path
            or default_wearable_secret_path(connection, "refresh-token")
        )
        connection.refresh_token_family_id = connection.refresh_token_family_id or stable_secret_hash(
            f"{connection.id}:{connection.provider}:refresh-token-family"
        )[:32]
    elif refresh_token_secret_path:
        connection.refresh_token_secret_path = refresh_token_secret_path

    connection.token_type = token_response.token_type or connection.token_type
    scope_values = wearable_token_scope_values(token_response.scope)
    if scope_values:
        connection.token_scope = encode_string_list(scope_values)
    if token_response.expires_in is not None:
        connection.token_expires_at = now + timedelta(seconds=token_response.expires_in)
    else:
        connection.token_expires_at = explicit_expires_at or connection.token_expires_at
    return connection.access_token_hash[:16] if connection.access_token_hash else None


def wearable_token_scope_values(scope: str | list[str] | None) -> list[str]:
    if scope is None:
        return []
    if isinstance(scope, str):
        return [item for item in re.split(r"[\s,]+", scope.strip()) if item]
    return [str(item) for item in scope if str(item).strip()]


async def resolve_wearable_client_secret(connection: PerformanceWearableProviderConnection) -> str:
    if not connection.oauth_client_secret_path:
        return ""
    return await resolve_wearable_token_secret(connection.oauth_client_secret_path, "client_secret")


async def resolve_wearable_token_secret(path: str, field_name: str) -> str:
    return await resolve_secret(
        get_settings(),
        env_value="",
        path=path,
        field_name=field_name,
        label=f"wearable OAuth {field_name}",
    )


async def wearable_webhook_metric_definitions(
    db: AsyncSession,
    payload: PerformanceWearableWebhookCreate,
) -> list[PerformanceMetricDefinition]:
    statement = select(PerformanceMetricDefinition).where(
        PerformanceMetricDefinition.organization_id == payload.organization_id
    )
    if payload.metric_definition_ids:
        statement = statement.where(PerformanceMetricDefinition.id.in_(payload.metric_definition_ids))
    else:
        statement = statement.where(PerformanceMetricDefinition.status == "active")
    return list((await db.scalars(statement.order_by(PerformanceMetricDefinition.code))).all())


def wearable_webhook_result(
    ingest_event: PerformanceWearableIngestEvent,
    *,
    replayed: bool,
    observation_ids: list[UUID],
) -> dict[str, object]:
    return {
        "ingest_event_id": ingest_event.id,
        "organization_id": ingest_event.organization_id,
        "athlete_profile_id": ingest_event.athlete_profile_id,
        "source_provider": ingest_event.provider,
        "external_event_id": ingest_event.external_event_id,
        "replayed": replayed,
        "signature_required": ingest_event.signature_required,
        "signature_validated": ingest_event.signature_validated,
        "observation_count": ingest_event.observation_count,
        "skipped_metric_count": ingest_event.skipped_metric_count,
        "observation_ids": observation_ids,
        "payload_hash": ingest_event.payload_hash,
        "received_at": ingest_event.received_at,
    }


def match_tracking_provider_ingest_event_read(
    ingest_event: PerformanceMatchTrackingProviderIngestEvent,
) -> dict[str, object]:
    stored_payload = decode_json_dict(ingest_event.payload_json)
    frames = stored_payload.get("frames") if isinstance(stored_payload, dict) else None
    return {
        "id": ingest_event.id,
        "organization_id": ingest_event.organization_id,
        "video_asset_id": ingest_event.video_asset_id,
        "tracking_run_id": ingest_event.tracking_run_id,
        "team_id": ingest_event.team_id,
        "event_id": ingest_event.event_id,
        "source_provider": ingest_event.provider,
        "external_event_id": ingest_event.external_event_id,
        "payload_hash": ingest_event.payload_hash,
        "received_at": ingest_event.received_at,
        "signature_required": ingest_event.signature_required,
        "signature_validated": ingest_event.signature_validated,
        "sample_count": ingest_event.sample_count,
        "player_count": ingest_event.player_count,
        "status": ingest_event.status,
        "payload_available": bool(stored_payload),
        "frame_count": len(frames) if isinstance(frames, list) else 0,
        "created_at": ingest_event.created_at,
    }


async def match_tracking_provider_webhook_result(
    db: AsyncSession,
    ingest_event: PerformanceMatchTrackingProviderIngestEvent,
    *,
    replayed: bool,
    tracking_run: PerformanceMatchTrackingRun | None,
    reprocessed: bool = False,
) -> dict[str, object]:
    return {
        "ingest_event_id": ingest_event.id,
        "organization_id": ingest_event.organization_id,
        "video_asset_id": ingest_event.video_asset_id,
        "tracking_run_id": ingest_event.tracking_run_id,
        "source_provider": ingest_event.provider,
        "external_event_id": ingest_event.external_event_id,
        "replayed": replayed,
        "reprocessed": reprocessed,
        "signature_required": ingest_event.signature_required,
        "signature_validated": ingest_event.signature_validated,
        "sample_count": ingest_event.sample_count,
        "player_count": ingest_event.player_count,
        "payload_hash": ingest_event.payload_hash,
        "received_at": ingest_event.received_at,
        "tracking_run": await match_tracking_run_read(db, tracking_run) if tracking_run is not None else None,
    }


async def validate_performance_wearable_webhook_signature(
    raw_body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
    settings: Settings | None = None,
) -> tuple[bool, bool]:
    selected_settings = settings or get_settings()
    signing_key = await resolve_secret(
        selected_settings,
        env_value=selected_settings.performance_wearable_webhook_signing_key,
        path=selected_settings.performance_wearable_webhook_signing_key_secret_path,
        field_name=selected_settings.performance_wearable_webhook_signing_key_secret_field,
        label="performance wearable webhook signing key",
    )
    if not signing_key:
        return False, False
    if not timestamp_header or not signature_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing wearable webhook signature")
    try:
        timestamp = int(timestamp_header)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid wearable webhook timestamp") from exc
    age = abs(int(time.time()) - timestamp)
    if age > selected_settings.performance_wearable_webhook_tolerance_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Stale wearable webhook signature")
    expected = hmac.new(
        signing_key.encode(),
        timestamp_header.encode() + b"." + raw_body,
        hashlib.sha256,
    ).hexdigest()
    submitted = signature_header.removeprefix("sha256=")
    if not hmac.compare_digest(expected, submitted):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid wearable webhook signature")
    return True, True


async def validate_performance_match_tracking_webhook_signature(
    raw_body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
    settings: Settings | None = None,
) -> tuple[bool, bool]:
    selected_settings = settings or get_settings()
    signing_key = await resolve_secret(
        selected_settings,
        env_value=selected_settings.performance_match_tracking_webhook_signing_key,
        path=selected_settings.performance_match_tracking_webhook_signing_key_secret_path,
        field_name=selected_settings.performance_match_tracking_webhook_signing_key_secret_field,
        label="performance match tracking webhook signing key",
    )
    if not signing_key:
        return False, False
    if not timestamp_header or not signature_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing match tracking provider webhook signature",
        )
    try:
        timestamp = int(timestamp_header)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid match tracking provider webhook timestamp",
        ) from exc
    age = abs(int(time.time()) - timestamp)
    if age > selected_settings.performance_match_tracking_webhook_tolerance_seconds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Stale match tracking provider webhook signature",
        )
    expected = hmac.new(
        signing_key.encode(),
        timestamp_header.encode() + b"." + raw_body,
        hashlib.sha256,
    ).hexdigest()
    submitted = signature_header.removeprefix("sha256=")
    if not hmac.compare_digest(expected, submitted):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid match tracking provider webhook signature",
        )
    return True, True


async def review_observation(
    db: AsyncSession,
    identity: CurrentIdentity,
    observation_id: UUID,
    payload: PerformanceObservationReviewCreate,
    authz: AuthorizationService,
) -> AthletePerformanceObservation:
    observation = await db.get(AthletePerformanceObservation, observation_id)
    if observation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found")
    await ensure_manage_performance(authz, identity, observation.organization_id)
    if payload.value is not None:
        observation.value = payload.value
        observation.raw_value = str(payload.value)
    observation.verification_status = payload.verification_status
    if payload.notes is not None:
        observation.notes = payload.notes
    await db.commit()
    await db.refresh(observation)
    return observation


async def list_observations(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> list[AthletePerformanceObservation]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
    return list(
        (
            await db.scalars(
                select(AthletePerformanceObservation)
                .where(AthletePerformanceObservation.organization_id == organization_id)
                .where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
                .order_by(AthletePerformanceObservation.observed_at.desc())
            )
        ).all()
    )


async def create_assessment(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: AthleteAssessmentCreate,
    authz: AuthorizationService,
) -> AthleteAssessment:
    athlete_profile = await get_athlete_profile(db, athlete_profile_id, payload.organization_id)
    await ensure_manage_performance(authz, identity, payload.organization_id)
    if payload.event_id is not None:
        event = await db.get(Event, payload.event_id)
        if event is None or event.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    overall_score = payload.overall_score
    if overall_score is None:
        overall_score = round(
            payload.physical_score * 0.25
            + payload.technical_score * 0.35
            + payload.tactical_score * 0.25
            + payload.mental_score * 0.15,
            2,
        )

    assessment = AthleteAssessment(
        athlete_profile_id=athlete_profile.id,
        assessed_by_person_id=identity.person_id,
        assessed_at=payload.assessed_at or datetime.now(UTC),
        overall_score=overall_score,
        **payload.model_dump(exclude={"assessed_at", "overall_score"}),
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    return assessment


async def create_player_self_assessment(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: PlayerSelfAssessmentCreate,
) -> AthleteAssessment:
    athlete_profile = await get_athlete_profile(db, athlete_profile_id, payload.organization_id)
    if athlete_profile.person_id != identity.person_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if payload.event_id is not None:
        event = await db.get(Event, payload.event_id)
        if event is None or event.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    overall_score = round(
        payload.physical_score * 0.25
        + payload.technical_score * 0.35
        + payload.tactical_score * 0.25
        + payload.mental_score * 0.15,
        2,
    )
    summary = payload.summary or (
        f"Player self-assessment with RPE {payload.perceived_exertion:g}/10 "
        f"and effort {payload.effort_rating:g}/10."
    )
    created_at = datetime.now(UTC)
    assessment = AthleteAssessment(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile.id,
        event_id=payload.event_id,
        assessed_by_person_id=identity.person_id,
        assessed_at=payload.assessed_at or created_at,
        physical_score=payload.physical_score,
        technical_score=payload.technical_score,
        tactical_score=payload.tactical_score,
        mental_score=payload.mental_score,
        overall_score=overall_score,
        perceived_exertion=payload.perceived_exertion,
        effort_rating=payload.effort_rating,
        summary=summary,
        recommendations="Coach review requested for player self-assessment.",
        review_due_at=created_at + timedelta(hours=48),
        review_priority=self_assessment_priority(overall_score, payload.perceived_exertion),
        verification_status=MetricVerificationStatus.PENDING_REVIEW,
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    return assessment


async def review_assessment(
    db: AsyncSession,
    identity: CurrentIdentity,
    assessment_id: UUID,
    payload: AthleteAssessmentReviewCreate,
    authz: AuthorizationService,
) -> AthleteAssessment:
    assessment = await db.get(AthleteAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    await ensure_manage_performance(authz, identity, assessment.organization_id)
    for field_name in (
        "physical_score",
        "technical_score",
        "tactical_score",
        "mental_score",
        "perceived_exertion",
        "effort_rating",
    ):
        value = getattr(payload, field_name)
        if value is not None:
            setattr(assessment, field_name, value)
    assessment.overall_score = round(
        assessment.physical_score * 0.25
        + assessment.technical_score * 0.35
        + assessment.tactical_score * 0.25
        + assessment.mental_score * 0.15,
        2,
    )
    assessment.verification_status = payload.verification_status
    assessment.reviewed_by_person_id = identity.person_id
    assessment.reviewed_at = datetime.now(UTC)
    if assessment.review_assigned_to_person_id is None:
        assessment.review_assigned_to_person_id = identity.person_id
    if payload.summary is not None:
        assessment.summary = payload.summary
    if payload.recommendations is not None:
        assessment.recommendations = payload.recommendations
    await db.commit()
    await db.refresh(assessment)
    return assessment


async def update_assessment_review_assignment(
    db: AsyncSession,
    identity: CurrentIdentity,
    assessment_id: UUID,
    payload: AthleteAssessmentReviewAssignmentUpdate,
    authz: AuthorizationService,
) -> AthleteAssessment:
    assessment = await db.get(AthleteAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    await ensure_manage_performance(authz, identity, assessment.organization_id)
    if payload.clear_assignment:
        assessment.review_assigned_to_person_id = None
    elif payload.assign_to_self:
        await ensure_assignment_person(db, assessment.organization_id, identity.person_id)
        assessment.review_assigned_to_person_id = identity.person_id
    elif "assigned_to_person_id" in payload.model_fields_set:
        if payload.assigned_to_person_id is None:
            assessment.review_assigned_to_person_id = None
        else:
            await ensure_assignment_person(db, assessment.organization_id, payload.assigned_to_person_id)
            assessment.review_assigned_to_person_id = payload.assigned_to_person_id
    if "review_due_at" in payload.model_fields_set:
        assessment.review_due_at = payload.review_due_at
    if payload.review_priority is not None:
        assessment.review_priority = payload.review_priority
    if "review_notes" in payload.model_fields_set:
        assessment.review_notes = payload.review_notes
    await db.commit()
    await db.refresh(assessment)
    return assessment


async def list_assessment_review_queue(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    limit: int = 25,
    assignment: str = "all",
    sla: str = "all",
    priority: str = "all",
) -> list[tuple[AthleteAssessment, AthleteProfile, Person, Person | None]]:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    await ensure_manage_performance(authz, identity, organization_id)
    assignee = aliased(Person)
    now = datetime.now(UTC)
    statement = (
        select(AthleteAssessment, AthleteProfile, Person)
        .add_columns(assignee)
        .join(AthleteProfile, AthleteProfile.id == AthleteAssessment.athlete_profile_id)
        .join(Person, Person.id == AthleteProfile.person_id)
        .outerjoin(assignee, assignee.id == AthleteAssessment.review_assigned_to_person_id)
        .where(AthleteAssessment.organization_id == organization_id)
        .where(AthleteAssessment.verification_status == MetricVerificationStatus.PENDING_REVIEW)
    )
    if assignment == "mine":
        statement = statement.where(AthleteAssessment.review_assigned_to_person_id == identity.person_id)
    elif assignment == "unassigned":
        statement = statement.where(AthleteAssessment.review_assigned_to_person_id.is_(None))
    elif assignment == "assigned":
        statement = statement.where(AthleteAssessment.review_assigned_to_person_id.is_not(None))
    if sla == "overdue":
        statement = statement.where(AthleteAssessment.review_due_at.is_not(None), AthleteAssessment.review_due_at < now)
    elif sla == "due_soon":
        statement = statement.where(
            AthleteAssessment.review_due_at.is_not(None),
            AthleteAssessment.review_due_at >= now,
            AthleteAssessment.review_due_at <= now + timedelta(hours=24),
        )
    elif sla == "on_track":
        statement = statement.where(
            (AthleteAssessment.review_due_at.is_(None))
            | (AthleteAssessment.review_due_at > now + timedelta(hours=24))
        )
    if priority != "all":
        statement = statement.where(AthleteAssessment.review_priority == priority)
    rows = await db.execute(
        statement.order_by(
            AthleteAssessment.review_due_at.is_(None),
            AthleteAssessment.review_due_at.asc(),
            AthleteAssessment.assessed_at.desc(),
            AthleteAssessment.created_at.desc(),
        ).limit(limit)
    )
    return list(rows.all())


async def assessment_review_queue_summary(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> AssessmentReviewQueueSummaryRead:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    await ensure_manage_performance(authz, identity, organization_id)
    assignee = aliased(Person)
    rows = list(
        (
            await db.execute(
                select(AthleteAssessment)
                .add_columns(assignee)
                .outerjoin(assignee, assignee.id == AthleteAssessment.review_assigned_to_person_id)
                .where(AthleteAssessment.organization_id == organization_id)
                .where(AthleteAssessment.verification_status == MetricVerificationStatus.PENDING_REVIEW)
            )
        ).all()
    )
    now = datetime.now(UTC)
    priority_counts = {"low": 0, "normal": 0, "high": 0, "urgent": 0}
    reviewer_buckets: dict[UUID | None, dict[str, object]] = {}
    age_hours: list[int] = []
    overdue_count = 0
    due_soon_count = 0
    on_track_count = 0
    unscheduled_count = 0
    urgent_count = 0
    escalated_count = 0
    unassigned_count = 0

    for assessment, reviewer in rows:
        priority_counts[assessment.review_priority] = priority_counts.get(assessment.review_priority, 0) + 1
        due_at = as_utc_datetime(assessment.review_due_at)
        if due_at is None:
            unscheduled_count += 1
        elif due_at < now:
            overdue_count += 1
        elif due_at <= now + timedelta(hours=24):
            due_soon_count += 1
        else:
            on_track_count += 1
        if assessment.review_priority == "urgent":
            urgent_count += 1
        if assessment.review_escalation_count:
            escalated_count += 1
        if assessment.review_assigned_to_person_id is None:
            unassigned_count += 1
        created_at = as_utc_datetime(assessment.created_at) or as_utc_datetime(assessment.assessed_at) or now
        item_age = max(0, int((now - created_at).total_seconds() // 3600))
        age_hours.append(item_age)

        reviewer_key = assessment.review_assigned_to_person_id
        bucket = reviewer_buckets.setdefault(
            reviewer_key,
            {
                "reviewer_person_id": reviewer_key,
                "reviewer_name": reviewer.display_name if reviewer is not None else "Unassigned",
                "open_count": 0,
                "overdue_count": 0,
                "urgent_count": 0,
                "escalated_count": 0,
                "oldest_age_hours": 0,
            },
        )
        bucket["open_count"] = int(bucket["open_count"]) + 1
        if due_at is not None and due_at < now:
            bucket["overdue_count"] = int(bucket["overdue_count"]) + 1
        if assessment.review_priority == "urgent":
            bucket["urgent_count"] = int(bucket["urgent_count"]) + 1
        if assessment.review_escalation_count:
            bucket["escalated_count"] = int(bucket["escalated_count"]) + 1
        bucket["oldest_age_hours"] = max(int(bucket["oldest_age_hours"]), item_age)

    reviewer_loads = [
        AssessmentReviewLoadRead(
            reviewer_person_id=bucket["reviewer_person_id"],
            reviewer_name=str(bucket["reviewer_name"]),
            open_count=int(bucket["open_count"]),
            overdue_count=int(bucket["overdue_count"]),
            urgent_count=int(bucket["urgent_count"]),
            escalated_count=int(bucket["escalated_count"]),
            oldest_age_hours=int(bucket["oldest_age_hours"]),
        )
        for bucket in reviewer_buckets.values()
    ]
    reviewer_loads.sort(key=lambda item: (item.overdue_count, item.urgent_count, item.open_count), reverse=True)
    open_count = len(rows)
    return AssessmentReviewQueueSummaryRead(
        organization_id=organization_id,
        open_count=open_count,
        unassigned_count=unassigned_count,
        assigned_count=open_count - unassigned_count,
        overdue_count=overdue_count,
        due_soon_count=due_soon_count,
        on_track_count=on_track_count,
        unscheduled_count=unscheduled_count,
        urgent_count=urgent_count,
        escalated_count=escalated_count,
        average_age_hours=int(sum(age_hours) // len(age_hours)) if age_hours else 0,
        oldest_age_hours=max(age_hours) if age_hours else 0,
        priority_counts=priority_counts,
        reviewer_loads=reviewer_loads,
    )


async def list_assessments(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> list[AthleteAssessment]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
    return list(
        (
            await db.scalars(
                select(AthleteAssessment)
                .where(AthleteAssessment.organization_id == organization_id)
                .where(AthleteAssessment.athlete_profile_id == athlete_profile_id)
                .order_by(AthleteAssessment.assessed_at.desc())
            )
        ).all()
    )


async def performance_summary(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> tuple[float | None, int, int, UUID | None, str | None]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
    latest_assessment = await db.scalar(
        select(AthleteAssessment)
        .where(AthleteAssessment.organization_id == organization_id)
        .where(AthleteAssessment.athlete_profile_id == athlete_profile_id)
        .where(AthleteAssessment.verification_status == MetricVerificationStatus.VERIFIED)
        .order_by(AthleteAssessment.assessed_at.desc())
        .limit(1)
    )
    observation_count = await db.scalar(
        select(func.count(AthletePerformanceObservation.id))
        .where(AthletePerformanceObservation.organization_id == organization_id)
        .where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
    )
    assessment_count = await db.scalar(
        select(func.count(AthleteAssessment.id))
        .where(AthleteAssessment.organization_id == organization_id)
        .where(AthleteAssessment.athlete_profile_id == athlete_profile_id)
    )
    score = latest_assessment.overall_score if latest_assessment is not None else None
    return (
        score,
        int(observation_count or 0),
        int(assessment_count or 0),
        latest_assessment.id if latest_assessment is not None else None,
        rating_for_score(score),
    )


async def performance_metric_benchmarks(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID | None = None,
    sport: str | None = None,
    cohort_scope: str = "tenant",
) -> list[dict[str, object]]:
    cohort_scope = normalize_benchmark_scope(cohort_scope)
    athlete_profile = None
    if athlete_profile_id is not None:
        athlete_profile = await get_athlete_profile(db, athlete_profile_id, organization_id)
    metrics = await list_metric_definitions(db, organization_id, sport=sport)
    metric_by_id = {metric.id: metric for metric in metrics}
    if not metric_by_id:
        return []

    observations = list(
        (
            await db.scalars(
                select(AthletePerformanceObservation)
                .where(AthletePerformanceObservation.organization_id == organization_id)
                .where(AthletePerformanceObservation.metric_definition_id.in_(list(metric_by_id)))
                .where(
                    AthletePerformanceObservation.verification_status
                    != MetricVerificationStatus.REJECTED
                )
                .order_by(AthletePerformanceObservation.observed_at.desc())
            )
        ).all()
    )
    latest_by_metric_athlete: dict[
        tuple[UUID, UUID],
        AthletePerformanceObservation,
    ] = {}
    for observation in observations:
        key = (observation.metric_definition_id, observation.athlete_profile_id)
        latest_by_metric_athlete.setdefault(key, observation)
    context_athlete_ids = {athlete_id for _, athlete_id in latest_by_metric_athlete}
    if athlete_profile is not None:
        context_athlete_ids.add(athlete_profile.id)
    context_by_athlete = await athlete_benchmark_contexts(
        db,
        organization_id,
        context_athlete_ids,
    )
    target_context = (
        context_by_athlete.get(athlete_profile.id)
        if athlete_profile is not None
        else None
    )
    cohort_label = benchmark_cohort_label(cohort_scope, target_context)

    benchmarks: list[dict[str, object]] = []
    for metric in metrics:
        cohort_observations = [
            observation
            for (metric_id, _), observation in latest_by_metric_athlete.items()
            if metric_id == metric.id
            and benchmark_context_matches(
                cohort_scope,
                target_context,
                context_by_athlete.get(observation.athlete_profile_id),
            )
        ]
        values = [observation.value for observation in cohort_observations]
        athlete_observation = (
            latest_by_metric_athlete.get((metric.id, athlete_profile.id))
            if athlete_profile is not None
            else None
        )
        athlete_value = athlete_observation.value if athlete_observation is not None else None
        average = sum(values) / len(values) if values else None
        percentile_rank, cohort_rank = athlete_percentile_and_rank(
            values,
            athlete_value,
            metric.higher_is_better,
        )
        delta_to_average = None
        if average is not None and athlete_value is not None:
            raw_delta = athlete_value - average
            delta_to_average = raw_delta if metric.higher_is_better else -raw_delta
        band = benchmark_band(percentile_rank, sample_size=len(values), athlete_value=athlete_value)
        benchmarks.append(
            {
                "metric_definition_id": metric.id,
                "metric_code": metric.code,
                "metric_name": metric.name,
                "sport": metric.sport,
                "category": metric.category,
                "unit": metric.unit,
                "higher_is_better": metric.higher_is_better,
                "cohort_scope": cohort_scope,
                "cohort_label": cohort_label,
                "sample_size": len(values),
                "athlete_value": athlete_value,
                "cohort_average": round(average, 2) if average is not None else None,
                "cohort_min": round(min(values), 2) if values else None,
                "cohort_max": round(max(values), 2) if values else None,
                "delta_to_average": round(delta_to_average, 2)
                if delta_to_average is not None
                else None,
                "percentile_rank": percentile_rank,
                "cohort_rank": cohort_rank,
                "benchmark_band": band,
                "recommendation": performance_benchmark_recommendation(
                    band,
                    metric.name,
                    metric.unit,
                    athlete_value,
                    average,
                ),
            }
        )
    return benchmarks


async def performance_cohort_comparisons(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
    sport: str | None = None,
    cohort_scopes: tuple[str, ...] = (
        "tenant",
        "age_group",
        "position",
        "region",
        "local_association",
        "regional_association",
    ),
) -> list[dict[str, object]]:
    comparisons: list[dict[str, object]] = []
    for scope in cohort_scopes:
        benchmarks = await performance_metric_benchmarks(
            db,
            organization_id,
            athlete_profile_id=athlete_profile_id,
            sport=sport,
            cohort_scope=scope,
        )
        if scope in {"local_association", "regional_association"} and not any(
            benchmark["sample_size"] for benchmark in benchmarks
        ):
            continue
        percentiles = [
            benchmark["percentile_rank"]
            for benchmark in benchmarks
            if isinstance(benchmark["percentile_rank"], int | float)
        ]
        top_benchmark = max(
            (
                benchmark
                for benchmark in benchmarks
                if isinstance(benchmark["percentile_rank"], int | float)
            ),
            key=lambda benchmark: benchmark["percentile_rank"],
            default=None,
        )
        watch_count = sum(1 for benchmark in benchmarks if benchmark["benchmark_band"] == "watch")
        average_percentile = (
            round(sum(percentiles) / len(percentiles), 1)
            if percentiles
            else None
        )
        cohort_label = benchmarks[0]["cohort_label"] if benchmarks else benchmark_cohort_label(scope, None)
        comparisons.append(
            {
                "cohort_scope": scope,
                "cohort_label": cohort_label,
                "metric_count": len(benchmarks),
                "sample_size_total": sum(int(benchmark["sample_size"]) for benchmark in benchmarks),
                "average_percentile": average_percentile,
                "watch_count": watch_count,
                "top_metric_name": top_benchmark["metric_name"] if top_benchmark is not None else None,
                "top_percentile": top_benchmark["percentile_rank"] if top_benchmark is not None else None,
                "recommendation": cohort_comparison_recommendation(scope, cohort_label, average_percentile, watch_count),
                "benchmarks": benchmarks,
            }
        )
    return comparisons


def normalized_performance_metric_code(metric_code: str | None) -> str | None:
    value = (metric_code or "").strip().lower()
    return value or None


def performance_trend_metric_filter(
    metrics: list[PerformanceMetricDefinition],
    category: MetricCategory | None = None,
    metric_code: str | None = None,
) -> list[PerformanceMetricDefinition]:
    normalized_code = normalized_performance_metric_code(metric_code)
    return [
        metric
        for metric in metrics
        if (category is None or metric.category == category)
        and (normalized_code is None or metric.code.lower() == normalized_code)
    ]


async def performance_metric_trends(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
    sport: str | None = None,
    category: MetricCategory | None = None,
    metric_code: str | None = None,
    period_start: date | None = None,
    period_end: date | None = None,
) -> list[dict[str, object]]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
    metrics = performance_trend_metric_filter(
        await list_metric_definitions(db, organization_id, sport=sport),
        category=category,
        metric_code=metric_code,
    )
    metric_by_id = {metric.id: metric for metric in metrics}
    if not metric_by_id:
        return []

    start_at, end_at = performance_observation_period_bounds(period_start, period_end)
    observation_query = (
        select(AthletePerformanceObservation)
        .where(AthletePerformanceObservation.organization_id == organization_id)
        .where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
        .where(AthletePerformanceObservation.metric_definition_id.in_(list(metric_by_id)))
        .where(
            AthletePerformanceObservation.verification_status
            != MetricVerificationStatus.REJECTED
        )
        .order_by(
            AthletePerformanceObservation.metric_definition_id,
            AthletePerformanceObservation.observed_at,
        )
    )
    if start_at is not None:
        observation_query = observation_query.where(AthletePerformanceObservation.observed_at >= start_at)
    if end_at is not None:
        observation_query = observation_query.where(AthletePerformanceObservation.observed_at <= end_at)
    observations = list(
        (await db.scalars(observation_query)).all()
    )
    observations_by_metric: dict[UUID, list[AthletePerformanceObservation]] = {}
    for observation in observations:
        observations_by_metric.setdefault(observation.metric_definition_id, []).append(observation)

    trends: list[dict[str, object]] = []
    for metric in metrics:
        metric_observations = observations_by_metric.get(metric.id, [])
        values = [observation.value for observation in metric_observations]
        trend = metric_trend_summary(values, metric.higher_is_better, metric.name, metric.unit)
        trends.append(
            {
                "metric_definition_id": metric.id,
                "metric_code": metric.code,
                "metric_name": metric.name,
                "sport": metric.sport,
                "category": metric.category,
                "unit": metric.unit,
                "higher_is_better": metric.higher_is_better,
                "filter_category": category,
                "filter_metric_code": normalized_performance_metric_code(metric_code),
                "period_start": period_start,
                "period_end": period_end,
                **trend,
            }
        )
    return trends


async def performance_metric_trend_series(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
    sport: str | None = None,
    limit_per_metric: int = 12,
    category: MetricCategory | None = None,
    metric_code: str | None = None,
    period_start: date | None = None,
    period_end: date | None = None,
) -> list[dict[str, object]]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
    metrics = performance_trend_metric_filter(
        await list_metric_definitions(db, organization_id, sport=sport),
        category=category,
        metric_code=metric_code,
    )
    metric_by_id = {metric.id: metric for metric in metrics}
    if not metric_by_id:
        return []

    start_at, end_at = performance_observation_period_bounds(period_start, period_end)
    observation_query = (
        select(AthletePerformanceObservation)
        .where(AthletePerformanceObservation.organization_id == organization_id)
        .where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
        .where(AthletePerformanceObservation.metric_definition_id.in_(list(metric_by_id)))
        .where(
            AthletePerformanceObservation.verification_status
            != MetricVerificationStatus.REJECTED
        )
        .order_by(
            AthletePerformanceObservation.metric_definition_id,
            AthletePerformanceObservation.observed_at.desc(),
        )
    )
    if start_at is not None:
        observation_query = observation_query.where(AthletePerformanceObservation.observed_at >= start_at)
    if end_at is not None:
        observation_query = observation_query.where(AthletePerformanceObservation.observed_at <= end_at)
    observations = list(
        (await db.scalars(observation_query)).all()
    )
    observations_by_metric: dict[UUID, list[AthletePerformanceObservation]] = {}
    for observation in observations:
        metric_observations = observations_by_metric.setdefault(
            observation.metric_definition_id,
            [],
        )
        if len(metric_observations) < limit_per_metric:
            metric_observations.append(observation)

    series: list[dict[str, object]] = []
    for metric in metrics:
        metric_observations = sorted(
            observations_by_metric.get(metric.id, []),
            key=lambda observation: observation.observed_at,
        )
        values = [observation.value for observation in metric_observations]
        trend = metric_trend_summary(values, metric.higher_is_better, metric.name, metric.unit)
        series.append(
            {
                "metric_definition_id": metric.id,
                "metric_code": metric.code,
                "metric_name": metric.name,
                "sport": metric.sport,
                "category": metric.category,
                "unit": metric.unit,
                "higher_is_better": metric.higher_is_better,
                "filter_category": category,
                "filter_metric_code": normalized_performance_metric_code(metric_code),
                "period_start": period_start,
                "period_end": period_end,
                "sample_size": len(metric_observations),
                "latest_value": trend["latest_value"],
                "forecast_next_value": trend["forecast_next_value"],
                "trend_direction": trend["trend_direction"],
                "recommendation": trend["recommendation"],
                "points": [
                    {
                        "observation_id": observation.id,
                        "observed_at": observation.observed_at,
                        "value": observation.value,
                        "normalized_value": normalized_trend_value(
                            observation.value,
                            values,
                            metric.higher_is_better,
                        ),
                        "source": observation.source,
                        "verification_status": observation.verification_status,
                    }
                    for observation in metric_observations
                ],
            }
        )
    return series


async def performance_forecast_scenarios(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
    sport: str | None = None,
) -> list[dict[str, object]]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
    settings = get_settings()
    metrics = await list_metric_definitions(db, organization_id, sport=sport)
    metric_by_id = {metric.id: metric for metric in metrics}
    if not metric_by_id:
        return []

    observations = list(
        (
            await db.scalars(
                select(AthletePerformanceObservation)
                .where(AthletePerformanceObservation.organization_id == organization_id)
                .where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
                .where(AthletePerformanceObservation.metric_definition_id.in_(list(metric_by_id)))
                .where(
                    AthletePerformanceObservation.verification_status
                    != MetricVerificationStatus.REJECTED
                )
                .order_by(
                    AthletePerformanceObservation.metric_definition_id,
                    AthletePerformanceObservation.observed_at,
                )
            )
        ).all()
    )
    observations_by_metric: dict[UUID, list[AthletePerformanceObservation]] = {}
    for observation in observations:
        observations_by_metric.setdefault(observation.metric_definition_id, []).append(observation)

    scenarios: list[dict[str, object]] = []
    for metric in metrics:
        metric_observations = observations_by_metric.get(metric.id, [])
        values = [observation.value for observation in metric_observations]
        trend = metric_trend_summary(values, metric.higher_is_better, metric.name, metric.unit)
        summary = forecast_scenario_summary(values, metric.higher_is_better, metric.name, metric.unit, trend)
        model_forecast = await model_assisted_performance_forecast(
            settings,
            athlete_profile_id,
            metric,
            metric_observations,
            trend,
            summary,
            scenario_type="baseline",
        )
        if model_forecast is not None:
            summary = apply_model_forecast_summary(summary, model_forecast)
        scenarios.append(
            {
                "metric_definition_id": metric.id,
                "metric_code": metric.code,
                "metric_name": metric.name,
                "sport": metric.sport,
                "category": metric.category,
                "unit": metric.unit,
                "higher_is_better": metric.higher_is_better,
                **summary,
            }
        )
    return scenarios


async def performance_forecast_what_if_scenarios(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
    sport: str | None = None,
    category: MetricCategory | None = None,
    metric_code: str | None = None,
    training_adjustment_percent: float = 0.0,
    readiness_score: int = 70,
    horizon: int = 4,
) -> list[dict[str, object]]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
    settings = get_settings()
    metrics = performance_trend_metric_filter(
        await list_metric_definitions(db, organization_id, sport=sport),
        category=category,
        metric_code=metric_code,
    )
    metric_by_id = {metric.id: metric for metric in metrics}
    if not metric_by_id:
        return []

    observations = list(
        (
            await db.scalars(
                select(AthletePerformanceObservation)
                .where(AthletePerformanceObservation.organization_id == organization_id)
                .where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
                .where(AthletePerformanceObservation.metric_definition_id.in_(list(metric_by_id)))
                .where(
                    AthletePerformanceObservation.verification_status
                    != MetricVerificationStatus.REJECTED
                )
                .order_by(
                    AthletePerformanceObservation.metric_definition_id,
                    AthletePerformanceObservation.observed_at,
                )
            )
        ).all()
    )
    observations_by_metric: dict[UUID, list[AthletePerformanceObservation]] = {}
    for observation in observations:
        observations_by_metric.setdefault(observation.metric_definition_id, []).append(observation)

    scenarios: list[dict[str, object]] = []
    for metric in metrics:
        metric_observations = observations_by_metric.get(metric.id, [])
        values = [observation.value for observation in metric_observations]
        trend = metric_trend_summary(values, metric.higher_is_better, metric.name, metric.unit)
        summary = forecast_scenario_summary(
            values,
            metric.higher_is_better,
            metric.name,
            metric.unit,
            trend,
            training_adjustment_percent=training_adjustment_percent,
            readiness_score=readiness_score,
            horizon=horizon,
            model_policy="deterministic_what_if_forecast_v1",
        )
        model_forecast = await model_assisted_performance_forecast(
            settings,
            athlete_profile_id,
            metric,
            metric_observations,
            trend,
            summary,
            scenario_type="what_if",
            training_adjustment_percent=training_adjustment_percent,
            readiness_score=readiness_score,
            horizon=horizon,
        )
        if model_forecast is not None:
            summary = apply_model_forecast_summary(summary, model_forecast)
        scenarios.append(
            {
                "metric_definition_id": metric.id,
                "metric_code": metric.code,
                "metric_name": metric.name,
                "sport": metric.sport,
                "category": metric.category,
                "unit": metric.unit,
                "higher_is_better": metric.higher_is_better,
                **summary,
                "scenario_label": what_if_scenario_label(training_adjustment_percent, readiness_score),
                "training_adjustment_percent": round(training_adjustment_percent, 1),
                "readiness_score": readiness_score,
                "horizon": horizon,
            }
        )
    return scenarios


async def performance_injury_risk(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> dict[str, object]:
    athlete_profile = await get_athlete_profile(db, athlete_profile_id, organization_id)
    feedback_rows = list(
        (
            await db.execute(
                select(TrainingSessionFeedback, TrainingSessionPlan)
                .join(TrainingSessionPlan, TrainingSessionPlan.id == TrainingSessionFeedback.session_plan_id)
                .where(TrainingSessionFeedback.organization_id == organization_id)
                .where(TrainingSessionFeedback.athlete_profile_id == athlete_profile_id)
                .order_by(TrainingSessionFeedback.recorded_at.desc())
                .limit(28)
            )
        ).all()
    )
    open_incidents = list(
        (
            await db.scalars(
                select(SafeguardingIncident)
                .where(SafeguardingIncident.organization_id == organization_id)
                .where(SafeguardingIncident.athlete_person_id == athlete_profile.person_id)
                .where(
                    SafeguardingIncident.incident_type.in_(
                        [SafeguardingIncidentType.INJURY, SafeguardingIncidentType.MEDICAL]
                    )
                )
                .where(
                    SafeguardingIncident.status.not_in(
                        [SafeguardingIncidentStatus.RESOLVED, SafeguardingIncidentStatus.CLOSED]
                    )
                )
                .order_by(SafeguardingIncident.occurred_at.desc())
            )
        ).all()
    )
    trends = await performance_metric_trends(db, organization_id, athlete_profile_id)
    declining_metric_count = sum(1 for trend in trends if trend["trend_direction"] == "declining")
    environmental_context = await injury_risk_environment_context(db, organization_id, feedback_rows)
    biomarker_context = await injury_risk_biomarker_context(db, organization_id, athlete_profile_id)
    biomechanical_context = await injury_risk_biomechanical_context(db, organization_id, athlete_profile_id)
    return injury_risk_summary(
        athlete_profile_id,
        feedback_rows,
        len(open_incidents),
        declining_metric_count,
        environmental_context,
        biomarker_context,
        biomechanical_context,
    )


async def send_performance_injury_risk_alert(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    athlete_profile_id: UUID,
    authz: AuthorizationService,
    threshold_score: int = 65,
    dry_run: bool = False,
    repeat_after_hours: int = 24,
    channels: list[CommunicationChannel] | None = None,
) -> dict[str, object]:
    await ensure_manage_performance(authz, identity, organization_id)
    return await send_performance_injury_risk_alert_for_athlete(
        db,
        organization_id,
        athlete_profile_id,
        threshold_score=threshold_score,
        dry_run=dry_run,
        repeat_after_hours=repeat_after_hours,
        channels=channels,
    )


async def send_performance_injury_risk_alert_for_athlete(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
    threshold_score: int = 65,
    dry_run: bool = False,
    repeat_after_hours: int = 24,
    channels: list[CommunicationChannel] | None = None,
) -> dict[str, object]:
    alert_channels = normalized_injury_risk_alert_channels(channels)
    athlete_profile = await get_athlete_profile(db, athlete_profile_id, organization_id)
    athlete = await db.get(Person, athlete_profile.person_id)
    if athlete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete person not found")
    risk = await performance_injury_risk(db, organization_id, athlete_profile_id)
    recipient_ids = await injury_risk_alert_recipient_ids(db, organization_id, athlete)
    sent = False
    message_ids: list[UUID] = []
    skipped_reason = None
    if int(risk["score"]) < threshold_score:
        skipped_reason = f"Risk score {risk['score']} is below alert threshold {threshold_score}."
    elif not recipient_ids:
        skipped_reason = "No eligible risk-alert recipients found."
    elif repeat_after_hours > 0 and await recent_injury_risk_alert_exists(db, athlete.id, repeat_after_hours):
        skipped_reason = f"An injury-risk alert was already sent within the last {repeat_after_hours} hour(s)."
    elif dry_run:
        sent = False
    else:
        messages = await create_injury_risk_alert_messages(
            db,
            organization_id,
            athlete,
            risk,
            recipient_ids,
            alert_channels,
        )
        await db.commit()
        message_ids = [message.id for message in messages]
        sent = True

    return {
        "organization_id": organization_id,
        "athlete_profile_id": athlete_profile_id,
        "score": risk["score"],
        "risk_band": risk["risk_band"],
        "threshold_score": threshold_score,
        "sent": sent,
        "dry_run": dry_run,
        "channels": alert_channels,
        "channel_count": len(alert_channels),
        "recipient_count": len(recipient_ids) * len(alert_channels),
        "message_id": message_ids[0] if message_ids else None,
        "message_ids": message_ids,
        "skipped_reason": skipped_reason,
        "risk": risk,
    }


async def run_performance_injury_risk_alert_scan(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    limit: int = 50,
    threshold_score: int = 65,
    repeat_after_hours: int = 24,
    dry_run: bool = False,
    channels: list[CommunicationChannel] | None = None,
) -> PerformanceInjuryRiskAlertRunRead:
    await ensure_manage_performance(authz, identity, organization_id)
    return await run_performance_injury_risk_alert_scan_worker(
        db,
        organization_id=organization_id,
        limit=limit,
        threshold_score=threshold_score,
        repeat_after_hours=repeat_after_hours,
        dry_run=dry_run,
        channels=channels,
    )


async def run_performance_injury_risk_alert_scan_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    limit: int = 50,
    threshold_score: int = 65,
    repeat_after_hours: int = 24,
    dry_run: bool = False,
    channels: list[CommunicationChannel] | None = None,
) -> PerformanceInjuryRiskAlertRunRead:
    alert_channels = normalized_injury_risk_alert_channels(channels)
    athlete_profile_ids = await injury_risk_scan_athlete_ids(db, organization_id, limit)
    scanned_count = 0
    alerted_count = 0
    skipped_count = 0
    failed_count = 0
    high_risk_count = 0
    highest_score: int | None = None
    processed_ids: list[UUID] = []
    message_ids: list[UUID] = []
    skipped_reasons: dict[str, int] = {}

    for athlete_profile_id in athlete_profile_ids:
        athlete_profile = await db.get(AthleteProfile, athlete_profile_id)
        if athlete_profile is None:
            failed_count += 1
            continue
        try:
            result = await send_performance_injury_risk_alert_for_athlete(
                db,
                athlete_profile.organization_id,
                athlete_profile_id,
                threshold_score=threshold_score,
                dry_run=dry_run,
                repeat_after_hours=repeat_after_hours,
                channels=alert_channels,
            )
            scanned_count += 1
            processed_ids.append(athlete_profile_id)
            score = int(result["score"])
            highest_score = score if highest_score is None else max(highest_score, score)
            if score >= threshold_score:
                high_risk_count += 1
            if result["sent"]:
                alerted_count += 1
                message_ids.extend(result["message_ids"])
            else:
                skipped_count += 1
                reason = str(result["skipped_reason"] or ("Dry run only." if dry_run else "Alert not sent."))
                skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
        except Exception:
            failed_count += 1
            await db.rollback()

    return PerformanceInjuryRiskAlertRunRead(
        organization_id=organization_id,
        threshold_score=threshold_score,
        repeat_after_hours=repeat_after_hours,
        dry_run=dry_run,
        channels=alert_channels,
        channel_count=len(alert_channels),
        eligible_count=len(athlete_profile_ids),
        scanned_count=scanned_count,
        alerted_count=alerted_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        high_risk_count=high_risk_count,
        highest_score=highest_score,
        athlete_profile_ids=processed_ids,
        message_ids=message_ids,
        skipped_reasons=skipped_reasons,
    )


async def create_performance_goal(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: PerformanceGoalCreate,
    authz: AuthorizationService,
) -> PerformanceGoal:
    await get_athlete_profile(db, athlete_profile_id, payload.organization_id)
    await ensure_manage_performance(authz, identity, payload.organization_id)
    metric = await db.get(PerformanceMetricDefinition, payload.metric_definition_id)
    if metric is None or metric.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    current_value = await latest_metric_value(
        db,
        payload.organization_id,
        athlete_profile_id,
        payload.metric_definition_id,
    )
    baseline_value = payload.baseline_value if payload.baseline_value is not None else current_value
    direction = payload.direction or ("increase" if metric.higher_is_better else "decrease")
    goal = PerformanceGoal(
        athlete_profile_id=athlete_profile_id,
        baseline_value=baseline_value,
        current_value=current_value,
        direction=direction,
        status=goal_status(current_value, payload.target_value, direction),
        reward_badge=payload.reward_badge or badge_code(payload.title),
        **payload.model_dump(exclude={"baseline_value", "direction", "reward_badge"}),
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


async def list_performance_goals(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> list[PerformanceGoal]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
    return list(
        (
            await db.scalars(
                select(PerformanceGoal)
                .where(PerformanceGoal.organization_id == organization_id)
                .where(PerformanceGoal.athlete_profile_id == athlete_profile_id)
                .order_by(PerformanceGoal.status, PerformanceGoal.due_at, PerformanceGoal.created_at.desc())
            )
        ).all()
    )


async def list_performance_awards(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> list[PerformanceAchievementAward]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
    return list(
        (
            await db.scalars(
                select(PerformanceAchievementAward)
                .where(PerformanceAchievementAward.organization_id == organization_id)
                .where(PerformanceAchievementAward.athlete_profile_id == athlete_profile_id)
                .order_by(PerformanceAchievementAward.awarded_at.desc())
            )
        ).all()
    )


async def list_my_player_performance(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    observation_limit: int = 10,
    benchmark_cohort_scope: str = "tenant",
    trend_category: MetricCategory | None = None,
    trend_metric_code: str | None = None,
    trend_period_start: date | None = None,
    trend_period_end: date | None = None,
    what_if_training_adjustment_percent: float = 0.0,
    what_if_readiness_score: int = 70,
    what_if_horizon: int = 4,
) -> list[dict[str, object]]:
    benchmark_cohort_scope = normalize_benchmark_scope(benchmark_cohort_scope)
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    profiles = list(
        (
            await db.scalars(
                select(AthleteProfile)
                .where(AthleteProfile.organization_id == organization_id)
                .where(AthleteProfile.person_id == identity.person_id)
                .order_by(AthleteProfile.created_at.desc())
            )
        ).all()
    )
    athlete = await db.get(Person, identity.person_id)
    athlete_name = athlete.display_name if athlete is not None else identity.display_name
    results: list[dict[str, object]] = []
    for profile in profiles:
        score, observation_count, assessment_count, latest_assessment_id, rating = (
            await performance_summary(db, organization_id, profile.id)
        )
        latest_assessment = None
        if latest_assessment_id is not None:
            latest_assessment = await db.scalar(
                select(AthleteAssessment)
                .where(AthleteAssessment.organization_id == organization_id)
                .where(AthleteAssessment.athlete_profile_id == profile.id)
                .where(AthleteAssessment.id == latest_assessment_id)
                .where(AthleteAssessment.verification_status == MetricVerificationStatus.VERIFIED)
            )
        goals = await list_performance_goals(db, organization_id, profile.id)
        awards = await list_performance_awards(db, organization_id, profile.id)
        observations = (await list_observations(db, organization_id, profile.id))[:observation_limit]
        trends = await performance_metric_trends(
            db,
            organization_id,
            profile.id,
            category=trend_category,
            metric_code=trend_metric_code,
            period_start=trend_period_start,
            period_end=trend_period_end,
        )
        trend_series = await performance_metric_trend_series(
            db,
            organization_id,
            profile.id,
            category=trend_category,
            metric_code=trend_metric_code,
            period_start=trend_period_start,
            period_end=trend_period_end,
        )
        forecast_scenarios = await performance_forecast_scenarios(db, organization_id, profile.id)
        what_if_scenarios = await performance_forecast_what_if_scenarios(
            db,
            organization_id,
            profile.id,
            category=trend_category,
            metric_code=trend_metric_code,
            training_adjustment_percent=what_if_training_adjustment_percent,
            readiness_score=what_if_readiness_score,
            horizon=what_if_horizon,
        )
        injury_risk = await performance_injury_risk(db, organization_id, profile.id)
        benchmarks = await performance_metric_benchmarks(
            db,
            organization_id,
            athlete_profile_id=profile.id,
            cohort_scope=benchmark_cohort_scope,
        )
        cohort_comparisons = await performance_cohort_comparisons(db, organization_id, profile.id)
        match_guidance = await player_match_guidance_for_profile(db, organization_id, profile)
        results.append(
            {
                "organization_id": organization_id,
                "athlete_profile_id": profile.id,
                "athlete_person_id": profile.person_id,
                "athlete_name": athlete_name,
                "latest_overall_score": score,
                "observation_count": observation_count,
                "assessment_count": assessment_count,
                "latest_assessment_id": latest_assessment_id,
                "latest_assessment": latest_assessment,
                "rating": rating,
                "active_goal_count": sum(1 for goal in goals if goal.status == "active"),
                "achieved_goal_count": sum(1 for goal in goals if goal.status == "achieved"),
                "award_count": len(awards),
                "observations": observations,
                "goals": goals,
                "awards": awards,
                "trends": trends,
                "trend_series": trend_series,
                "forecast_scenarios": forecast_scenarios,
                "what_if_scenarios": what_if_scenarios,
                "injury_risk": injury_risk,
                "benchmarks": benchmarks,
                "cohort_comparisons": cohort_comparisons,
                "match_guidance": match_guidance,
            }
        )
    return results


async def player_match_guidance_for_profile(
    db: AsyncSession,
    organization_id: UUID,
    profile: AthleteProfile,
    limit: int = 5,
) -> list[dict[str, object]]:
    audits = list(
        (
            await db.scalars(
                select(PerformanceMatchPlayerGuidancePublishAudit)
                .where(PerformanceMatchPlayerGuidancePublishAudit.organization_id == organization_id)
                .where(PerformanceMatchPlayerGuidancePublishAudit.player_person_id == profile.person_id)
                .where(PerformanceMatchPlayerGuidancePublishAudit.status == "published")
                .order_by(
                    PerformanceMatchPlayerGuidancePublishAudit.published_at.desc(),
                    PerformanceMatchPlayerGuidancePublishAudit.created_at.desc(),
                )
                .limit(limit * 4)
            )
        ).all()
    )
    seen: set[tuple[UUID, str]] = set()
    guidance: list[dict[str, object]] = []
    for audit in audits:
        key = (audit.tracking_run_id, audit.track_id)
        if key in seen:
            continue
        seen.add(key)
        run = await db.get(PerformanceMatchTrackingRun, audit.tracking_run_id)
        if run is None or run.organization_id != organization_id:
            continue
        sample = await db.scalar(
            select(PerformanceMatchTrackingSample)
            .where(PerformanceMatchTrackingSample.tracking_run_id == run.id)
            .where(PerformanceMatchTrackingSample.track_id == audit.track_id)
            .where(PerformanceMatchTrackingSample.person_id == profile.person_id)
            .order_by(PerformanceMatchTrackingSample.timestamp_seconds.desc())
            .limit(1)
        )
        if sample is None:
            continue
        video_asset = await db.get(OppositionScoutingVideoAsset, run.video_asset_id)
        if video_asset is None:
            continue
        summary = decode_match_tracking_summary(run.summary_json)
        metric = next(
            (
                item
                for item in summary.get("player_metrics", [])
                if isinstance(item, dict) and str(item.get("track_id")) == sample.track_id
            ),
            None,
        )
        if metric is None:
            continue
        recipient = await db.scalar(
            select(MessageRecipient)
            .where(MessageRecipient.message_id == audit.message_id)
            .where(MessageRecipient.person_id == profile.person_id)
            .limit(1)
        )
        guidance.append(
            build_player_match_guidance(
                run=run,
                video_asset=video_asset,
                sample=sample,
                metric=metric,
                summary=summary,
                publish_audit=audit,
                player_recipient=recipient,
            )
        )
        if len(guidance) >= limit:
            break
    return guidance


async def create_player_match_training_followup(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: PlayerMatchTrainingFollowupCreate,
) -> dict[str, object]:
    profile = await get_athlete_profile(db, athlete_profile_id, payload.organization_id)
    if profile.person_id != identity.person_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    run = await get_match_tracking_run(db, payload.tracking_run_id)
    if run.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    samples = list(
        (
            await db.scalars(
                select(PerformanceMatchTrackingSample)
                .where(PerformanceMatchTrackingSample.tracking_run_id == run.id)
                .where(PerformanceMatchTrackingSample.track_id == payload.track_id)
                .where(PerformanceMatchTrackingSample.person_id == profile.person_id)
                .order_by(PerformanceMatchTrackingSample.timestamp_seconds.asc())
            )
        ).all()
    )
    if not samples:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confirmed player track not found")
    publish_audit = await player_match_guidance_publish_audit(
        db,
        organization_id=payload.organization_id,
        player_person_id=profile.person_id,
        tracking_run_id=run.id,
        track_id=payload.track_id,
    )
    if publish_audit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published match guidance not found")
    video_asset = await db.get(OppositionScoutingVideoAsset, run.video_asset_id)
    if video_asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match video not found")
    summary = decode_match_tracking_summary(run.summary_json)
    metric = next(
        (
            item
            for item in summary.get("player_metrics", [])
            if isinstance(item, dict) and str(item.get("track_id")) == payload.track_id
        ),
        None,
    )
    if metric is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player metric not found")
    guidance = build_player_match_guidance(
        run=run,
        video_asset=video_asset,
        sample=samples[-1],
        metric=metric,
        summary=summary,
        publish_audit=publish_audit,
    )
    selected_priorities = {priority.lower() for priority in payload.selected_priorities if priority.strip()}
    action_plan = [
        item
        for item in guidance["action_plan"]
        if not selected_priorities or str(item["priority"]).lower() in selected_priorities
    ][: payload.max_items]
    if not action_plan:
        action_plan = list(guidance["action_plan"])[: payload.max_items]
    focus_area = str(action_plan[0]["focus"]) if action_plan else "Match video follow-up"
    title = f"{video_asset.opponent_name} match follow-up"
    plan = TrainingPlan(
        organization_id=payload.organization_id,
        team_id=run.team_id,
        athlete_profile_id=profile.id,
        created_by_person_id=identity.person_id,
        title=title[:240],
        focus_area=focus_area[:160],
        period_start=payload.period_start,
        period_end=payload.period_end,
        status=TrainingPlanStatus.DRAFT,
        ai_generated=True,
        source_summary=(
            f"Generated from match tracking run {run.id} for track {payload.track_id} "
            f"against {video_asset.opponent_name}."
        ),
        load_guidance=(
            f"Use match evidence: {guidance['distance_m']}m total, "
            f"{guidance['high_speed_distance_m']}m high-speed, max {guidance['max_speed_mps']} m/s."
        ),
        recovery_protocol="Confirm soreness/readiness after high-speed or repeated sprint follow-up work.",
        progress_checkpoints="Review the clip, complete the listed action items, then submit a self-assessment.",
    )
    db.add(plan)
    await db.flush()
    items: list[TrainingPlanItem] = []
    for index, action in enumerate(action_plan, start=1):
        item = TrainingPlanItem(
            plan_id=plan.id,
            drill_id=None,
            sequence=index,
            day_label=f"Follow-up {index}",
            title=str(action["focus"])[:180],
            focus_area=str(action["focus"])[:120],
            duration_minutes=player_match_action_duration(str(action["priority"])),
            intensity=player_match_action_intensity(str(action["priority"])),
            notes=(
                f"Cue: {action['cue']}\n"
                f"Drill: {action['drill_recommendation']}\n"
                f"Evidence: {action['evidence']}"
            ),
        )
        db.add(item)
        items.append(item)
    await db.commit()
    await db.refresh(plan)
    for item in items:
        await db.refresh(item)
    agent_task = await queue_player_match_followup_agent_review(
        db,
        identity,
        organization_id=payload.organization_id,
        team_id=run.team_id,
        athlete_profile_id=profile.id,
        plan_id=plan.id,
        tracking_run_id=run.id,
        track_id=payload.track_id,
        focus_area=plan.focus_area,
        item_count=len(items),
    )
    return {
        "organization_id": payload.organization_id,
        "athlete_profile_id": profile.id,
        "tracking_run_id": run.id,
        "track_id": payload.track_id,
        "plan_id": plan.id,
        "item_ids": [item.id for item in items],
        "title": plan.title,
        "focus_area": plan.focus_area,
        "period_start": plan.period_start,
        "period_end": plan.period_end,
        "item_count": len(items),
        "action_plan": action_plan,
        "agent_task_id": agent_task.id if agent_task else None,
        "agent_task_status": agent_task.status.value if agent_task else None,
        "agent_task_title": agent_task.title if agent_task else None,
    }


async def player_match_guidance_publish_audit(
    db: AsyncSession,
    *,
    organization_id: UUID,
    player_person_id: UUID,
    tracking_run_id: UUID,
    track_id: str,
) -> PerformanceMatchPlayerGuidancePublishAudit | None:
    return await db.scalar(
        select(PerformanceMatchPlayerGuidancePublishAudit)
        .where(PerformanceMatchPlayerGuidancePublishAudit.organization_id == organization_id)
        .where(PerformanceMatchPlayerGuidancePublishAudit.player_person_id == player_person_id)
        .where(PerformanceMatchPlayerGuidancePublishAudit.tracking_run_id == tracking_run_id)
        .where(PerformanceMatchPlayerGuidancePublishAudit.track_id == track_id)
        .where(PerformanceMatchPlayerGuidancePublishAudit.status == "published")
        .order_by(
            PerformanceMatchPlayerGuidancePublishAudit.published_at.desc(),
            PerformanceMatchPlayerGuidancePublishAudit.created_at.desc(),
        )
        .limit(1)
    )


async def queue_player_match_followup_agent_review(
    db: AsyncSession,
    identity: CurrentIdentity,
    *,
    organization_id: UUID,
    team_id: UUID | None,
    athlete_profile_id: UUID,
    plan_id: UUID,
    tracking_run_id: UUID,
    track_id: str,
    focus_area: str,
    item_count: int,
):
    agent = await db.scalar(
        select(Agent)
        .where(
            Agent.organization_id == organization_id,
            Agent.kind == AgentKind.COACHING,
            Agent.name == "Training Strategy Agent",
        )
        .order_by(Agent.created_at)
        .limit(1)
    )
    if agent is None:
        agent = Agent(
            organization_id=organization_id,
            name="Training Strategy Agent",
            kind=AgentKind.COACHING,
            purpose=(
                "Review training plans, match-derived action plans, athlete readiness, "
                "and feedback loops so coaches can adjust the next block safely."
            ),
            status="active",
            model_policy="human_review_required",
        )
        db.add(agent)
        await db.flush()
    input_ref = (
        f"player-match-followup:{organization_id};"
        f"team:{team_id or 'none'};"
        f"athlete:{athlete_profile_id};"
        f"plan:{plan_id};"
        f"tracking:{tracking_run_id};"
        f"track:{track_id};"
        f"focus:{focus_area};"
        f"items:{item_count}"
    )
    return await queue_agent_task(
        db,
        identity,
        agent.id,
        AgentTaskCreate(
            organization_id=organization_id,
            task_type="player_match_training_followup_review",
            title=f"Review player match follow-up: {focus_area}"[:240],
            input_ref=input_ref[:500],
        ),
        None,
        enforce_manage_organization=False,
    )


def decode_match_tracking_summary(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def player_match_action_duration(priority: str) -> int:
    normalized = priority.lower()
    if normalized in {"high", "confirm"}:
        return 30
    if normalized == "medium":
        return 24
    return 18


def player_match_action_intensity(priority: str) -> int:
    normalized = priority.lower()
    if normalized == "high":
        return 8
    if normalized == "medium":
        return 6
    if normalized == "confirm":
        return 3
    return 5


def build_player_match_guidance(
    *,
    run: PerformanceMatchTrackingRun,
    video_asset: OppositionScoutingVideoAsset,
    sample: PerformanceMatchTrackingSample,
    metric: dict[str, object],
    summary: dict[str, object],
    publish_audit: PerformanceMatchPlayerGuidancePublishAudit,
    player_recipient: MessageRecipient | None = None,
) -> dict[str, object]:
    team_label = str(metric.get("team_label") or sample.team_label or "").strip() or None
    track_id = str(metric.get("track_id") or sample.track_id)
    coaching_flags = [str(flag) for flag in metric.get("coaching_flags", []) if str(flag)]
    player_guidance = list(coaching_flags[:3])
    high_speed_distance = float(metric.get("high_speed_distance_m") or 0.0)
    sprint_count = int(metric.get("sprint_count") or 0)
    pass_attempts = int(metric.get("pass_attempt_count") or 0)
    pass_accuracy = float(metric.get("pass_accuracy_percent") or 0.0)
    pressure_count = int(metric.get("pressure_applied_count") or 0)
    off_ball_runs = int(metric.get("off_ball_run_count") or 0)
    tracking_quality = float(metric.get("tracking_quality_score") or summary.get("tracking_quality_score") or 0.0)
    if high_speed_distance > 0:
        player_guidance.append(
            f"Review your high-speed actions: {round(high_speed_distance)}m high-speed work and {sprint_count} sprint trigger(s)."
        )
    if pass_attempts > 0:
        player_guidance.append(
            f"Passing review: {pass_accuracy:.0f}% completion across {pass_attempts} tracked attempt(s)."
        )
    if pressure_count > 0:
        player_guidance.append(f"Pressing review: {pressure_count} pressure action(s) were detected near opponents.")
    if off_ball_runs > 0:
        player_guidance.append(f"Off-ball movement: {off_ball_runs} run(s) created separation or territory.")
    if tracking_quality < 0.65:
        player_guidance.append("Confirm this track identity with your coach before using the load numbers.")
    if not player_guidance:
        player_guidance.append("Use the replay with your coach to connect the movement data to match decisions.")

    tactical_context: list[str] = []
    for phase in summary.get("team_phase_metrics", []):
        if isinstance(phase, dict) and str(phase.get("team_label") or "") == team_label:
            tactical_context.append(
                f"{team_label} phase: {str(phase.get('phase_hint') or 'match phase').replace('_', ' ')}."
            )
            break
    for estimate in summary.get("possession_estimates", []):
        if isinstance(estimate, dict) and str(estimate.get("team_label") or "") == team_label:
            tactical_context.append(
                f"{team_label} possession estimate: {float(estimate.get('possession_percent') or 0):.0f}%."
            )
            break
    event_count = sum(
        1
        for event in summary.get("recognized_action_events", [])
        if isinstance(event, dict)
        and track_id
        in {
            str(event.get("track_id") or ""),
            str(event.get("from_track_id") or ""),
            str(event.get("to_track_id") or ""),
            str(event.get("presser_track_id") or ""),
            str(event.get("receiver_track_id") or ""),
        }
    )
    if event_count:
        tactical_context.append(f"{event_count} recognized action cue(s) are linked to this track.")
    action_plan = player_match_action_plan(
        metric=metric,
        tracking_quality=tracking_quality,
        high_speed_distance=high_speed_distance,
        sprint_count=sprint_count,
        pass_attempts=pass_attempts,
        pass_accuracy=pass_accuracy,
        pressure_count=pressure_count,
        off_ball_runs=off_ball_runs,
    )

    return {
        "tracking_run_id": run.id,
        "video_asset_id": video_asset.id,
        "guidance_message_id": publish_audit.message_id,
        "guidance_recipient_id": player_recipient.id if player_recipient is not None else None,
        "guidance_published_at": publish_audit.published_at,
        "guidance_delivery_status": (
            player_recipient.delivery_status.value if player_recipient is not None else "unknown"
        ),
        "guidance_recipient_count": publish_audit.recipient_count,
        "opponent_name": video_asset.opponent_name,
        "match_label": video_asset.clip_label,
        "tracked_at": run.completed_at or run.created_at,
        "track_id": track_id,
        "team_label": team_label,
        "player_label": metric.get("player_label") or sample.player_label,
        "jersey_number": metric.get("jersey_number") or sample.jersey_number,
        "readiness_level": str(summary.get("readiness_level") or "review_required"),
        "tracking_quality_score": round(tracking_quality, 3),
        "distance_m": round(float(metric.get("distance_m") or 0.0), 2),
        "high_speed_distance_m": round(high_speed_distance, 2),
        "max_speed_mps": round(float(metric.get("max_speed_mps") or 0.0), 3),
        "sprint_count": sprint_count,
        "work_rate_m_per_min": round(float(metric.get("work_rate_m_per_min") or 0.0), 2),
        "dominant_zone": str(metric.get("dominant_zone") or "unknown"),
        "pressure_applied_count": pressure_count,
        "off_ball_run_count": off_ball_runs,
        "pass_accuracy_percent": round(pass_accuracy, 2),
        "shot_count": int(metric.get("shot_count") or 0),
        "expected_goals": round(float(metric.get("expected_goals") or 0.0), 3),
        "coaching_flags": coaching_flags,
        "player_guidance": player_guidance[:6],
        "action_plan": action_plan,
        "tactical_context": tactical_context[:4],
        "quality_warnings": [str(item) for item in summary.get("quality_warnings", []) if str(item)][:4],
    }


def player_match_action_plan(
    *,
    metric: dict[str, object],
    tracking_quality: float,
    high_speed_distance: float,
    sprint_count: int,
    pass_attempts: int,
    pass_accuracy: float,
    pressure_count: int,
    off_ball_runs: int,
) -> list[dict[str, str]]:
    plan: list[dict[str, str]] = []
    max_speed = float(metric.get("max_speed_mps") or 0.0)
    recovery_ratio = float(metric.get("recovery_ratio") or 0.0)
    work_rate = float(metric.get("work_rate_m_per_min") or 0.0)
    if tracking_quality < 0.65:
        plan.append(
            {
                "priority": "confirm",
                "focus": "Track identity review",
                "cue": "Confirm this is your track before adjusting training load.",
                "drill_recommendation": "Review the clip with a coach and mark shirt number, role, and key timestamps.",
                "evidence": f"Tracking quality {round(tracking_quality * 100)}%.",
            }
        )
    if max_speed >= 8.5 or sprint_count >= 2 or high_speed_distance >= 40:
        plan.append(
            {
                "priority": "high",
                "focus": "Sprint mechanics and deceleration",
                "cue": "Accelerate tall, keep hips stable, and brake under control after the action.",
                "drill_recommendation": "Run 4 x 20m accelerations with 10m controlled deceleration and video one side-on rep.",
                "evidence": f"{round(high_speed_distance)}m high-speed work, {sprint_count} sprint trigger(s), max {max_speed:.1f} m/s.",
            }
        )
    if pressure_count >= 2:
        plan.append(
            {
                "priority": "medium",
                "focus": "Pressing angle and recovery cover",
                "cue": "Arrive on the opponent's outside shoulder and curve the run to block the easy pass.",
                "drill_recommendation": "Use 3v3+2 pressing waves with a five-second counter-press rule.",
                "evidence": f"{pressure_count} pressure action(s) detected near opponents.",
            }
        )
    if off_ball_runs >= 1:
        plan.append(
            {
                "priority": "medium",
                "focus": "Off-ball timing",
                "cue": "Start the run when the passer's touch opens, not after the pass is already obvious.",
                "drill_recommendation": "Practice third-player runs from midfield into channel gates with a timed release cue.",
                "evidence": f"{off_ball_runs} off-ball run(s) created separation or territory.",
            }
        )
    if pass_attempts >= 2 and pass_accuracy < 70:
        plan.append(
            {
                "priority": "medium",
                "focus": "First touch and passing choice",
                "cue": "Scan before receiving and keep the first touch away from pressure.",
                "drill_recommendation": "Run rondo-to-target sequences with mandatory shoulder checks before each receive.",
                "evidence": f"{pass_accuracy:.0f}% pass completion from {pass_attempts} tracked attempt(s).",
            }
        )
    if recovery_ratio < 0.12 and high_speed_distance > 0:
        plan.append(
            {
                "priority": "medium",
                "focus": "Recovery between efforts",
                "cue": "After sprinting, recover into shape before the next trigger instead of hovering between roles.",
                "drill_recommendation": "Pair repeated sprint work with walk-jog recovery gates and heart-rate/readiness check-ins.",
                "evidence": f"Low-speed recovery ratio {recovery_ratio:.2f} after high-speed load.",
            }
        )
    if work_rate >= 120 and len(plan) < 4:
        plan.append(
            {
                "priority": "monitor",
                "focus": "Work-rate management",
                "cue": "Protect quality late in the match by choosing the highest-value runs.",
                "drill_recommendation": "Use interval possession games with a coach callout for sprint/no-sprint decisions.",
                "evidence": f"Work rate {work_rate:.0f} m/min.",
            }
        )
    if not plan:
        plan.append(
            {
                "priority": "review",
                "focus": "Match decision review",
                "cue": "Pick two moments where your positioning changed the next pass or defensive action.",
                "drill_recommendation": "Review the match replay with your coach and tag one strength plus one next action.",
                "evidence": "No urgent load or tactical flag crossed the action-plan thresholds.",
            }
        )
    return plan[:4]


async def evaluate_performance_achievements(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    athlete_profile_id: UUID,
    authz: AuthorizationService,
) -> dict[str, object]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
    await ensure_manage_performance(authz, identity, organization_id)
    return await evaluate_performance_achievements_for_athlete(db, organization_id, athlete_profile_id)


async def evaluate_performance_achievements_for_athlete(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> dict[str, object]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
    goals = await list_performance_goals(db, organization_id, athlete_profile_id)
    updated_goals = 0
    awards: list[PerformanceAchievementAward] = []
    for goal in goals:
        current_value = await latest_metric_value(db, organization_id, athlete_profile_id, goal.metric_definition_id)
        if current_value != goal.current_value:
            goal.current_value = current_value
            updated_goals += 1
        if goal.status == "active" and goal_met(current_value, goal.target_value, goal.direction):
            goal.status = "achieved"
            updated_goals += 1
            award = await create_award_once(
                db,
                organization_id=organization_id,
                athlete_profile_id=athlete_profile_id,
                goal_id=goal.id,
                metric_definition_id=goal.metric_definition_id,
                title=f"Goal achieved: {goal.title}",
                badge_code=f"goal_{goal.id}",
                achievement_type="goal_achieved",
                achieved_value=current_value,
                threshold_value=goal.target_value,
                source_summary=f"Target {goal.target_value:g} reached with {current_value:g}.",
            )
            if award is not None:
                awards.append(award)
    personal_best_awards = await award_personal_bests(db, organization_id, athlete_profile_id)
    awards.extend(personal_best_awards)
    messages = await create_achievement_notifications(db, organization_id, athlete_profile_id, awards)
    await db.commit()
    for award in awards:
        await db.refresh(award)
    return {
        "organization_id": organization_id,
        "athlete_profile_id": athlete_profile_id,
        "evaluated_goals": len(goals),
        "awarded_count": len(awards),
        "updated_goals": updated_goals,
        "notification_message_count": len(messages),
        "awards": awards,
    }


async def run_performance_achievement_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    limit: int = 25,
) -> PerformanceAchievementWorkerRunRead:
    athlete_profile_ids = await achievement_worker_athlete_ids(db, organization_id, limit)
    executed_count = 0
    failed_count = 0
    awarded_count = 0
    updated_goals = 0
    processed_ids: list[UUID] = []
    for athlete_profile_id in athlete_profile_ids:
        athlete_profile = await db.get(AthleteProfile, athlete_profile_id)
        if athlete_profile is None:
            failed_count += 1
            continue
        try:
            result = await evaluate_performance_achievements_for_athlete(
                db,
                athlete_profile.organization_id,
                athlete_profile_id,
            )
            executed_count += 1
            awarded_count += int(result["awarded_count"])
            updated_goals += int(result["updated_goals"])
            processed_ids.append(athlete_profile_id)
        except Exception:
            failed_count += 1
            await db.rollback()
    return PerformanceAchievementWorkerRunRead(
        organization_id=organization_id,
        eligible_count=len(athlete_profile_ids),
        executed_count=executed_count,
        skipped_count=max(len(athlete_profile_ids) - executed_count - failed_count, 0),
        failed_count=failed_count,
        athlete_profile_ids=processed_ids,
        awarded_count=awarded_count,
        updated_goals=updated_goals,
    )


async def run_assessment_review_escalations(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    limit: int = 25,
    horizon_hours: int = 24,
    repeat_after_hours: int = 24,
    dry_run: bool = False,
) -> PerformanceAssessmentReviewEscalationRunRead:
    await ensure_manage_performance(authz, identity, organization_id)
    return await run_assessment_review_escalation_worker(
        db,
        organization_id=organization_id,
        limit=limit,
        horizon_hours=horizon_hours,
        repeat_after_hours=repeat_after_hours,
        dry_run=dry_run,
    )


async def run_assessment_review_escalation_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    limit: int = 25,
    horizon_hours: int = 24,
    repeat_after_hours: int = 24,
    dry_run: bool = False,
) -> PerformanceAssessmentReviewEscalationRunRead:
    rows = await assessment_review_escalation_rows(
        db,
        organization_id=organization_id,
        limit=limit,
        horizon_hours=horizon_hours,
        repeat_after_hours=repeat_after_hours,
    )
    grouped: dict[UUID, list[tuple[AthleteAssessment, AthleteProfile, Person, Person | None]]] = {}
    for row in rows:
        grouped.setdefault(row[0].organization_id, []).append(row)

    now = datetime.now(UTC)
    escalated_ids: list[UUID] = []
    message_ids: list[UUID] = []
    skipped_count = 0
    failed_count = 0
    overdue_count = 0
    due_soon_count = 0
    for org_id, org_rows in grouped.items():
        local_overdue = sum(
            1
            for assessment, *_ in org_rows
            if (due_at := as_utc_datetime(assessment.review_due_at)) is not None and due_at < now
        )
        overdue_count += local_overdue
        due_soon_count += len(org_rows) - local_overdue
        try:
            recipient_ids = await assessment_review_escalation_recipient_ids(db, org_id, org_rows)
            if not recipient_ids:
                skipped_count += len(org_rows)
                continue
            if dry_run:
                escalated_ids.extend(assessment.id for assessment, *_ in org_rows)
                continue
            message = await create_assessment_review_escalation_message(db, org_id, org_rows, recipient_ids, now)
            message_ids.append(message.id)
            for assessment, *_ in org_rows:
                assessment.review_last_escalated_at = now
                assessment.review_escalation_count = (assessment.review_escalation_count or 0) + 1
                assessment.review_escalation_message_id = message.id
                escalated_ids.append(assessment.id)
            await db.commit()
        except Exception:
            failed_count += len(org_rows)
            await db.rollback()

    return PerformanceAssessmentReviewEscalationRunRead(
        organization_id=organization_id,
        eligible_count=len(rows),
        escalated_count=len(escalated_ids),
        skipped_count=skipped_count,
        failed_count=failed_count,
        overdue_count=overdue_count,
        due_soon_count=due_soon_count,
        assessment_ids=escalated_ids,
        message_ids=message_ids,
        dry_run=dry_run,
    )


async def assessment_review_escalation_rows(
    db: AsyncSession,
    organization_id: UUID | None,
    limit: int,
    horizon_hours: int,
    repeat_after_hours: int,
) -> list[tuple[AthleteAssessment, AthleteProfile, Person, Person | None]]:
    assignee = aliased(Person)
    now = datetime.now(UTC)
    statement = (
        select(AthleteAssessment, AthleteProfile, Person)
        .add_columns(assignee)
        .join(AthleteProfile, AthleteProfile.id == AthleteAssessment.athlete_profile_id)
        .join(Person, Person.id == AthleteProfile.person_id)
        .outerjoin(assignee, assignee.id == AthleteAssessment.review_assigned_to_person_id)
        .where(AthleteAssessment.verification_status == MetricVerificationStatus.PENDING_REVIEW)
        .where(AthleteAssessment.review_due_at.is_not(None))
        .where(AthleteAssessment.review_due_at <= now + timedelta(hours=horizon_hours))
        .where(
            (AthleteAssessment.review_last_escalated_at.is_(None))
            | (AthleteAssessment.review_last_escalated_at <= now - timedelta(hours=repeat_after_hours))
        )
        .order_by(
            AthleteAssessment.review_due_at.asc(),
            AthleteAssessment.review_priority.desc(),
            AthleteAssessment.created_at.asc(),
        )
        .limit(limit)
    )
    if organization_id is not None:
        statement = statement.where(AthleteAssessment.organization_id == organization_id)
    return list((await db.execute(statement)).all())


async def assessment_review_escalation_recipient_ids(
    db: AsyncSession,
    organization_id: UUID,
    rows: list[tuple[AthleteAssessment, AthleteProfile, Person, Person | None]],
) -> set[UUID]:
    manager_rows = (
        await db.execute(
            select(Membership.subject_id)
            .where(Membership.organization_id == organization_id)
            .where(Membership.subject_type == MemberSubjectType.PERSON)
            .where(
                Membership.role.in_(
                    [
                        MembershipRole.OWNER,
                        MembershipRole.ADMIN,
                        MembershipRole.STAFF,
                        MembershipRole.COACH,
                    ]
                )
            )
            .where(Membership.status == "active")
        )
    ).all()
    recipient_ids = {person_id for (person_id,) in manager_rows}
    recipient_ids.update(
        assessment.review_assigned_to_person_id
        for assessment, *_ in rows
        if assessment.review_assigned_to_person_id is not None
    )
    return recipient_ids


async def create_assessment_review_escalation_message(
    db: AsyncSession,
    organization_id: UUID,
    rows: list[tuple[AthleteAssessment, AthleteProfile, Person, Person | None]],
    recipient_ids: set[UUID],
    now: datetime,
) -> CommunicationMessage:
    subject = assessment_review_escalation_subject(rows, now)
    body = assessment_review_escalation_body(rows, now)
    message = CommunicationMessage(
        organization_id=organization_id,
        template_id=None,
        created_by_person_id=None,
        message_type=CommunicationMessageType.ALERT,
        channel=CommunicationChannel.IN_APP,
        scope_type=CommunicationScopeType.ORGANIZATION,
        scope_id=organization_id,
        subject=subject,
        body=body,
        urgent=True,
        quiet_hours_override=True,
        scheduled_for=None,
        sent_at=now,
        status="sent",
    )
    db.add(message)
    await db.flush()
    for person_id in sorted(recipient_ids, key=str):
        person = await db.get(Person, person_id)
        if person is None:
            continue
        db.add(
            MessageRecipient(
                message_id=message.id,
                person_id=person.id,
                destination=destination_for_channel(person, CommunicationChannel.IN_APP),
                delivery_status=initial_delivery_status(person, CommunicationChannel.IN_APP),
            )
        )
    return message


def assessment_review_escalation_subject(
    rows: list[tuple[AthleteAssessment, AthleteProfile, Person, Person | None]],
    now: datetime,
) -> str:
    overdue = sum(
        1
        for assessment, *_ in rows
        if (due_at := as_utc_datetime(assessment.review_due_at)) is not None and due_at < now
    )
    if overdue:
        return f"{overdue} overdue performance assessment review{'s' if overdue != 1 else ''}"[:240]
    return f"{len(rows)} performance assessment review{'s' if len(rows) != 1 else ''} due soon"[:240]


def assessment_review_escalation_body(
    rows: list[tuple[AthleteAssessment, AthleteProfile, Person, Person | None]],
    now: datetime,
) -> str:
    lines = [
        "Performance assessment reviews need coach attention.",
        "",
    ]
    for assessment, _, athlete, assignee in rows[:10]:
        due_at = as_utc_datetime(assessment.review_due_at)
        sla = "overdue" if due_at and due_at < now else "due soon"
        assignee_name = assignee.display_name if assignee is not None else "unassigned"
        due_text = due_at.isoformat() if due_at else "unscheduled"
        lines.append(
            f"- {athlete.display_name}: ALS {assessment.overall_score:g}, "
            f"{assessment.review_priority} priority, {sla}, due {due_text}, {assignee_name}."
        )
    if len(rows) > 10:
        lines.append(f"- Plus {len(rows) - 10} more pending review item(s).")
    lines.extend(
        [
            "",
            "Open the performance review queue, assign ownership, and verify or reject submissions before using them as trusted ALS evidence.",
        ]
    )
    return "\n".join(lines)[:8000]


async def achievement_worker_athlete_ids(
    db: AsyncSession,
    organization_id: UUID | None,
    limit: int,
) -> list[UUID]:
    goal_statement = select(PerformanceGoal.athlete_profile_id).where(PerformanceGoal.status == "active")
    observation_statement = select(AthletePerformanceObservation.athlete_profile_id).where(
        AthletePerformanceObservation.verification_status != MetricVerificationStatus.REJECTED
    )
    if organization_id is not None:
        goal_statement = goal_statement.where(PerformanceGoal.organization_id == organization_id)
        observation_statement = observation_statement.where(
            AthletePerformanceObservation.organization_id == organization_id
        )
    goal_ids = list((await db.scalars(goal_statement.order_by(PerformanceGoal.due_at).limit(limit))).all())
    observation_ids = list(
        (
            await db.scalars(
                observation_statement.order_by(AthletePerformanceObservation.observed_at.desc()).limit(limit)
            )
        ).all()
    )
    seen: set[UUID] = set()
    athlete_profile_ids: list[UUID] = []
    for athlete_profile_id in [*goal_ids, *observation_ids]:
        if athlete_profile_id in seen:
            continue
        seen.add(athlete_profile_id)
        athlete_profile_ids.append(athlete_profile_id)
        if len(athlete_profile_ids) >= limit:
            break
    return athlete_profile_ids


async def get_athlete_profile(
    db: AsyncSession,
    athlete_profile_id: UUID,
    organization_id: UUID,
) -> AthleteProfile:
    athlete_profile = await db.get(AthleteProfile, athlete_profile_id)
    if athlete_profile is None or athlete_profile.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    return athlete_profile


async def create_athlete_pathway_projection(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: AthletePathwayProjectionCreate,
    authz: AuthorizationService,
) -> AthletePathwayProjectionRead:
    athlete_profile = await get_athlete_profile(db, athlete_profile_id, payload.organization_id)
    await ensure_manage_performance(authz, identity, payload.organization_id)
    person = await db.get(Person, athlete_profile.person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete person not found")

    latest_assessment = await latest_athlete_assessment(db, payload.organization_id, athlete_profile_id)
    observation_rows = await pathway_observation_rows(db, payload.organization_id, athlete_profile_id)
    benchmarks = await performance_metric_benchmarks(
        db,
        payload.organization_id,
        athlete_profile_id=athlete_profile_id,
        sport=payload.sport,
        cohort_scope="tenant",
    )
    trends = await performance_metric_trends(
        db,
        payload.organization_id,
        athlete_profile_id,
        sport=payload.sport,
    )
    roster_position = await athlete_primary_position(db, athlete_profile_id)
    primary_position = payload.primary_position or roster_position
    age_years = person_age_years(person.date_of_birth)
    model = athlete_pathway_model(
        athlete_name=person.display_name or "Athlete",
        payload=payload,
        latest_assessment=latest_assessment,
        observation_rows=observation_rows,
        benchmarks=benchmarks,
        trends=trends,
        age_years=age_years,
        primary_position=primary_position,
    )
    now = datetime.now(UTC)
    projection = AthletePathwayProjection(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile_id,
        created_by_person_id=identity.person_id,
        sport=payload.sport,
        primary_position=primary_position,
        age_years=age_years,
        academic_gpa=payload.academic_gpa,
        graduation_year=payload.graduation_year,
        target_pathway=payload.target_pathway.strip().lower(),
        model_policy=model["model_policy"],
        confidence=model["confidence"],
        readiness_score=model["readiness_score"],
        projected_level=model["projected_level"],
        college_fit_score=model["college_fit_score"],
        semi_pro_fit_score=model["semi_pro_fit_score"],
        professional_fit_score=model["professional_fit_score"],
        scholarship_fit_score=model["scholarship_fit_score"],
        summary=model["summary"],
        pathways_json=json.dumps(model["pathway_options"]),
        milestones_json=json.dumps(model["milestones"]),
        scout_actions_json=json.dumps(model["scout_actions"]),
        evidence_json=json.dumps(model["evidence"]),
        risk_flags_json=json.dumps(model["risk_flags"]),
        status="active",
        generated_at=now,
    )
    db.add(projection)
    await db.commit()
    await db.refresh(projection)
    return athlete_pathway_projection_read(projection, person.display_name or "Athlete")


async def list_athlete_pathway_projections(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> list[AthletePathwayProjectionRead]:
    athlete_profile = await get_athlete_profile(db, athlete_profile_id, organization_id)
    person = await db.get(Person, athlete_profile.person_id)
    athlete_name = person.display_name if person is not None and person.display_name else "Athlete"
    projections = list(
        (
            await db.scalars(
                select(AthletePathwayProjection)
                .where(AthletePathwayProjection.organization_id == organization_id)
                .where(AthletePathwayProjection.athlete_profile_id == athlete_profile_id)
                .order_by(AthletePathwayProjection.generated_at.desc(), AthletePathwayProjection.created_at.desc())
            )
        ).all()
    )
    return [athlete_pathway_projection_read(projection, athlete_name) for projection in projections]


async def latest_athlete_assessment(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> AthleteAssessment | None:
    return await db.scalar(
        select(AthleteAssessment)
        .where(AthleteAssessment.organization_id == organization_id)
        .where(AthleteAssessment.athlete_profile_id == athlete_profile_id)
        .where(AthleteAssessment.verification_status != MetricVerificationStatus.REJECTED)
        .order_by(AthleteAssessment.assessed_at.desc(), AthleteAssessment.created_at.desc())
        .limit(1)
    )


async def pathway_observation_rows(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> list[tuple[AthletePerformanceObservation, PerformanceMetricDefinition]]:
    rows = (
        await db.execute(
            select(AthletePerformanceObservation, PerformanceMetricDefinition)
            .join(
                PerformanceMetricDefinition,
                PerformanceMetricDefinition.id == AthletePerformanceObservation.metric_definition_id,
            )
            .where(AthletePerformanceObservation.organization_id == organization_id)
            .where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
            .where(AthletePerformanceObservation.verification_status != MetricVerificationStatus.REJECTED)
            .order_by(AthletePerformanceObservation.observed_at.desc())
            .limit(80)
        )
    ).all()
    return [(observation, metric) for observation, metric in rows]


async def athlete_primary_position(db: AsyncSession, athlete_profile_id: UUID) -> str | None:
    value = await db.scalar(
        select(TeamRosterEntry.primary_position)
        .where(TeamRosterEntry.athlete_profile_id == athlete_profile_id)
        .where(TeamRosterEntry.status == RosterStatus.ACTIVE)
        .where(TeamRosterEntry.primary_position.is_not(None))
        .order_by(TeamRosterEntry.created_at.desc())
        .limit(1)
    )
    return value


def person_age_years(date_of_birth: date | None) -> int | None:
    if date_of_birth is None:
        return None
    today = date.today()
    return today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )


def athlete_pathway_projection_read(
    projection: AthletePathwayProjection,
    athlete_name: str,
) -> AthletePathwayProjectionRead:
    return AthletePathwayProjectionRead(
        id=projection.id,
        organization_id=projection.organization_id,
        athlete_profile_id=projection.athlete_profile_id,
        athlete_name=athlete_name,
        created_by_person_id=projection.created_by_person_id,
        sport=projection.sport,
        primary_position=projection.primary_position,
        age_years=projection.age_years,
        academic_gpa=projection.academic_gpa,
        graduation_year=projection.graduation_year,
        target_pathway=projection.target_pathway,
        model_policy=projection.model_policy,
        confidence=projection.confidence,
        readiness_score=projection.readiness_score,
        projected_level=projection.projected_level,
        college_fit_score=projection.college_fit_score,
        semi_pro_fit_score=projection.semi_pro_fit_score,
        professional_fit_score=projection.professional_fit_score,
        scholarship_fit_score=projection.scholarship_fit_score,
        summary=projection.summary,
        pathway_options=json.loads(projection.pathways_json or "[]"),
        milestones=json.loads(projection.milestones_json or "[]"),
        scout_actions=json.loads(projection.scout_actions_json or "[]"),
        evidence=json.loads(projection.evidence_json or "{}"),
        risk_flags=json.loads(projection.risk_flags_json or "[]"),
        status=projection.status,
        generated_at=projection.generated_at,
        created_at=projection.created_at,
    )


def athlete_pathway_model(
    athlete_name: str,
    payload: AthletePathwayProjectionCreate,
    latest_assessment: AthleteAssessment | None,
    observation_rows: list[tuple[AthletePerformanceObservation, PerformanceMetricDefinition]],
    benchmarks: list[dict[str, object]],
    trends: list[dict[str, object]],
    age_years: int | None,
    primary_position: str | None,
) -> dict[str, object]:
    category_scores = pathway_category_scores(latest_assessment, observation_rows)
    benchmark_score = pathway_benchmark_score(benchmarks)
    trend_score = pathway_trend_score(trends)
    academic_score = pathway_academic_score(payload.academic_gpa)
    base_score = (
        category_scores["physical"] * 0.22
        + category_scores["technical"] * 0.24
        + category_scores["tactical"] * 0.18
        + category_scores["mental"] * 0.18
        + benchmark_score * 0.1
        + trend_score * 0.08
    )
    readiness_score = round_pathway_score(base_score)
    college_fit = round_pathway_score(readiness_score * 0.62 + academic_score * 0.28 + trend_score * 0.1)
    semi_pro_fit = round_pathway_score(readiness_score * 0.74 + benchmark_score * 0.18 + category_scores["mental"] * 0.08)
    professional_fit = round_pathway_score(
        readiness_score * 0.55
        + benchmark_score * 0.25
        + category_scores["physical"] * 0.1
        + category_scores["technical"] * 0.1
    )
    scholarship_fit = round_pathway_score(college_fit * 0.62 + academic_score * 0.26 + category_scores["mental"] * 0.12)
    projected_level = pathway_projected_level(readiness_score, professional_fit, college_fit)
    confidence = pathway_confidence(
        assessment_count=1 if latest_assessment is not None else 0,
        observation_count=len(observation_rows),
        benchmark_count=len([item for item in benchmarks if item.get("athlete_value") is not None]),
        trend_count=len(trends),
    )
    risk_flags = pathway_risk_flags(
        payload=payload,
        readiness_score=readiness_score,
        observation_count=len(observation_rows),
        latest_assessment=latest_assessment,
        age_years=age_years,
        academic_score=academic_score,
    )
    top_pathway = max(
        [
            ("college scholarship", college_fit),
            ("semi-pro", semi_pro_fit),
            ("professional academy", professional_fit),
            ("scholarship", scholarship_fit),
        ],
        key=lambda item: item[1],
    )
    summary = (
        f"{athlete_name} projects as {projected_level.replace('_', ' ')} with "
        f"{readiness_score}/100 pathway readiness. The strongest near-term route is "
        f"{top_pathway[0]} ({top_pathway[1]}/100), backed by "
        f"{len(observation_rows)} accepted observation(s), "
        f"{'one verified assessment' if latest_assessment is not None else 'no verified assessment yet'}, "
        f"and {len(trends)} trend signal(s)."
    )
    evidence = {
        "assessment_count": 1 if latest_assessment is not None else 0,
        "observation_count": len(observation_rows),
        "benchmark_count": len(benchmarks),
        "trend_count": len(trends),
        "latest_overall_score": latest_assessment.overall_score if latest_assessment else None,
        "category_scores": category_scores,
        "benchmark_score": benchmark_score,
        "trend_score": trend_score,
        "academic_score": academic_score,
        "preferred_regions": [item.strip() for item in payload.preferred_regions if item.strip()],
        "recruiting_profile_url": payload.recruiting_profile_url,
        "notes": payload.notes,
        "primary_position": primary_position,
    }
    return {
        "model_policy": "deterministic_pathway_projection_v1",
        "confidence": confidence,
        "readiness_score": readiness_score,
        "projected_level": projected_level,
        "college_fit_score": college_fit,
        "semi_pro_fit_score": semi_pro_fit,
        "professional_fit_score": professional_fit,
        "scholarship_fit_score": scholarship_fit,
        "summary": summary,
        "pathway_options": pathway_options(
            college_fit=college_fit,
            semi_pro_fit=semi_pro_fit,
            professional_fit=professional_fit,
            scholarship_fit=scholarship_fit,
            readiness_score=readiness_score,
            target_pathway=payload.target_pathway,
            age_years=age_years,
        ),
        "milestones": pathway_milestones(
            payload=payload,
            readiness_score=readiness_score,
            primary_position=primary_position,
            latest_assessment=latest_assessment,
            observation_count=len(observation_rows),
            risk_flags=risk_flags,
        ),
        "scout_actions": pathway_scout_actions(payload, projected_level, primary_position),
        "evidence": evidence,
        "risk_flags": risk_flags,
    }


def pathway_category_scores(
    latest_assessment: AthleteAssessment | None,
    observation_rows: list[tuple[AthletePerformanceObservation, PerformanceMetricDefinition]],
) -> dict[str, float]:
    scores = {
        "physical": latest_assessment.physical_score if latest_assessment else None,
        "technical": latest_assessment.technical_score if latest_assessment else None,
        "tactical": latest_assessment.tactical_score if latest_assessment else None,
        "mental": latest_assessment.mental_score if latest_assessment else None,
    }
    observed: dict[str, list[float]] = {key: [] for key in scores}
    for observation, metric in observation_rows:
        category = metric.category.value
        if category in observed:
            observed[category].append(normalized_metric_value(observation.value, metric))
    for category, values in observed.items():
        if scores[category] is None and values:
            scores[category] = sum(values) / len(values)
    fallback = latest_assessment.overall_score if latest_assessment else 55.0
    return {
        category: round(float(score if score is not None else fallback), 1)
        for category, score in scores.items()
    }


def normalized_metric_value(value: float, metric: PerformanceMetricDefinition) -> float:
    if metric.min_value is not None and metric.max_value is not None and metric.max_value != metric.min_value:
        span = metric.max_value - metric.min_value
        normalized = (value - metric.min_value) / span * 100
        if not metric.higher_is_better:
            normalized = 100 - normalized
        return max(0, min(100, normalized))
    return max(0, min(100, value))


def pathway_benchmark_score(benchmarks: list[dict[str, object]]) -> float:
    values = [
        float(percentile)
        for benchmark in benchmarks
        if (percentile := benchmark.get("percentile_rank")) is not None
    ]
    if not values:
        return 55.0
    return round(sum(values) / len(values), 1)


def pathway_trend_score(trends: list[dict[str, object]]) -> float:
    if not trends:
        return 55.0
    score = 55.0
    for trend in trends:
        direction = str(trend.get("trend_direction") or "")
        if direction == "improving":
            score += 8
        elif direction == "stable":
            score += 3
        elif direction == "declining":
            score -= 8
    return round(max(0, min(100, score)), 1)


def pathway_academic_score(academic_gpa: float | None) -> float:
    if academic_gpa is None:
        return 55.0
    return round(max(0, min(100, academic_gpa / 4.0 * 100)), 1)


def round_pathway_score(value: float) -> int:
    return int(round(max(0, min(100, value))))


def pathway_projected_level(readiness_score: int, professional_fit: int, college_fit: int) -> str:
    if professional_fit >= 86 and readiness_score >= 84:
        return "professional_prospect"
    if college_fit >= 78 and readiness_score >= 74:
        return "college_recruit"
    if readiness_score >= 72:
        return "semi_pro_candidate"
    if readiness_score >= 62:
        return "regional_academy"
    if readiness_score >= 50:
        return "school_team"
    return "foundation"


def pathway_confidence(
    assessment_count: int,
    observation_count: int,
    benchmark_count: int,
    trend_count: int,
) -> float:
    value = 0.45 + min(0.16, assessment_count * 0.16) + min(0.18, observation_count * 0.025)
    value += min(0.1, benchmark_count * 0.02) + min(0.08, trend_count * 0.02)
    return round(max(0.35, min(0.94, value)), 2)


def pathway_risk_flags(
    payload: AthletePathwayProjectionCreate,
    readiness_score: int,
    observation_count: int,
    latest_assessment: AthleteAssessment | None,
    age_years: int | None,
    academic_score: float,
) -> list[str]:
    flags: list[str] = []
    if observation_count < 3:
        flags.append("Thin performance data: record at least three accepted observations before external outreach.")
    if latest_assessment is None:
        flags.append("Missing verified coach assessment: projection should not be used for recruiting decisions yet.")
    if payload.academic_gpa is None:
        flags.append("Academic record missing: college and scholarship matching confidence is capped.")
    elif academic_score < 65:
        flags.append("Academic support needed before scholarship outreach.")
    if not payload.recruiting_profile_url:
        flags.append("Recruiting profile URL missing: create a consent-gated profile before sending scouts material.")
    if age_years is not None and 16 <= age_years <= 19 and readiness_score >= 70:
        flags.append("Time-sensitive recruiting window: schedule showcase, transcript, and highlight actions now.")
    if readiness_score < 55:
        flags.append("Readiness below external pathway threshold: prioritize development milestones before outreach.")
    if payload.share_with_guardians:
        flags.append("Guardian-sharing requested: verify consent and minor safeguarding settings before distribution.")
    return flags


def pathway_readiness_label(score: int) -> str:
    if score >= 85:
        return "ready_now"
    if score >= 72:
        return "shortlist"
    if score >= 60:
        return "developing"
    return "foundation"


def pathway_options(
    college_fit: int,
    semi_pro_fit: int,
    professional_fit: int,
    scholarship_fit: int,
    readiness_score: int,
    target_pathway: str,
    age_years: int | None,
) -> list[dict[str, object]]:
    age_note = "current age window" if age_years is not None and age_years >= 16 else "development window"
    options = [
        {
            "pathway": "college_scholarship",
            "score": college_fit,
            "readiness": pathway_readiness_label(college_fit),
            "timeline": "0-12 months" if college_fit >= 72 else "12-24 months",
            "rationale": f"Academic and performance blend supports college matching in the {age_note}.",
            "next_actions": [
                "Compile transcript and eligibility documents.",
                "Build a coach-facing profile with verified metrics.",
                "Shortlist schools by sport level, academics, geography, and budget.",
            ],
        },
        {
            "pathway": "semi_pro",
            "score": semi_pro_fit,
            "readiness": pathway_readiness_label(semi_pro_fit),
            "timeline": "next season" if semi_pro_fit >= 72 else "two development blocks",
            "rationale": "Match-readiness, tactical reliability, and cohort evidence drive semi-pro fit.",
            "next_actions": [
                "Arrange trials against comparable senior competition.",
                "Verify physical benchmarks under match conditions.",
                "Prepare coach references and recent match footage.",
            ],
        },
        {
            "pathway": "professional_academy",
            "score": professional_fit,
            "readiness": pathway_readiness_label(professional_fit),
            "timeline": "active scout list" if professional_fit >= 82 else "18-36 months",
            "rationale": "Professional projection weights top-quartile benchmark evidence and elite technical consistency.",
            "next_actions": [
                "Create a position-specific highlight reel.",
                "Schedule elite benchmark testing.",
                "Track scout feedback as structured evaluation evidence.",
            ],
        },
        {
            "pathway": "dual_career",
            "score": round_pathway_score((scholarship_fit + readiness_score) / 2),
            "readiness": pathway_readiness_label(round_pathway_score((scholarship_fit + readiness_score) / 2)),
            "timeline": "rolling plan",
            "rationale": "Dual-career planning protects academic, health, and sport options when outcomes remain uncertain.",
            "next_actions": [
                "Set academic and sport milestones side by side.",
                "Review financial aid, transfer, and vocational alternatives.",
                "Re-run projection after each assessment cycle.",
            ],
        },
    ]
    target = target_pathway.strip().lower().replace(" ", "_")
    return sorted(
        options,
        key=lambda item: (0 if item["pathway"] == target else 1, -float(item["score"])),
    )


def pathway_milestones(
    payload: AthletePathwayProjectionCreate,
    readiness_score: int,
    primary_position: str | None,
    latest_assessment: AthleteAssessment | None,
    observation_count: int,
    risk_flags: list[str],
) -> list[dict[str, str]]:
    position_label = primary_position or "target role"
    return [
        {
            "title": "Verified performance baseline",
            "due_label": "this week" if latest_assessment is None or observation_count < 3 else "complete",
            "priority": "high" if latest_assessment is None or observation_count < 3 else "normal",
            "owner": "coach",
            "status": "blocked" if latest_assessment is None else "in_progress",
            "evidence": f"{observation_count} accepted observation(s); readiness {readiness_score}/100.",
        },
        {
            "title": f"{position_label} highlight reel and scout packet",
            "due_label": "14 days",
            "priority": "high" if readiness_score >= 70 else "normal",
            "owner": "performance analyst",
            "status": "not_started",
            "evidence": payload.recruiting_profile_url or "No recruiting profile URL recorded.",
        },
        {
            "title": "Academic and eligibility review",
            "due_label": "30 days",
            "priority": "high" if payload.academic_gpa is None else "normal",
            "owner": "family liaison",
            "status": "in_progress" if payload.academic_gpa is not None else "blocked",
            "evidence": f"GPA {payload.academic_gpa:g}" if payload.academic_gpa is not None else "Academic GPA missing.",
        },
        {
            "title": "Target outreach list",
            "due_label": "30-45 days",
            "priority": "normal",
            "owner": "recruiting lead",
            "status": "not_started",
            "evidence": ", ".join(payload.preferred_regions[:4]) if payload.preferred_regions else "No preferred regions recorded.",
        },
        {
            "title": "Consent-gated sharing check",
            "due_label": "before external sharing",
            "priority": "high" if any("consent" in flag.lower() for flag in risk_flags) else "normal",
            "owner": "safeguarding officer",
            "status": "required",
            "evidence": "Guardian-sharing requested." if payload.share_with_guardians else "Standard consent gate required.",
        },
    ]


def pathway_scout_actions(
    payload: AthletePathwayProjectionCreate,
    projected_level: str,
    primary_position: str | None,
) -> list[str]:
    position = primary_position or "primary role"
    actions = [
        f"Create a {position} scout sheet with latest assessment, trend, benchmark, and injury-risk evidence.",
        "Generate a 90-second highlight reel with timestamps, opponent context, and coach annotation notes.",
        "Use consent-gated profile links for guardians, schools, scouts, and scholarship offices.",
        "Record every outreach response as structured scouting feedback before the next projection run.",
    ]
    if payload.preferred_regions:
        actions.append(f"Prioritize outreach in {', '.join(payload.preferred_regions[:3])}.")
    if projected_level in {"college_recruit", "professional_prospect"}:
        actions.append("Schedule a showcase or verified trial while the readiness score is in an external-review band.")
    return actions


def rating_for_score(score: float | None) -> str | None:
    if score is None:
        return None
    if score >= 90:
        return "elite"
    if score >= 80:
        return "excellent"
    if score >= 70:
        return "good"
    if score >= 60:
        return "developing"
    if score >= 50:
        return "emerging"
    return "foundation"


def athlete_percentile_and_rank(
    values: list[float],
    athlete_value: float | None,
    higher_is_better: bool,
) -> tuple[float | None, int | None]:
    if athlete_value is None or not values:
        return None, None
    if higher_is_better:
        better_or_equal = sum(1 for value in values if value <= athlete_value)
        better = sum(1 for value in values if value > athlete_value)
    else:
        better_or_equal = sum(1 for value in values if value >= athlete_value)
        better = sum(1 for value in values if value < athlete_value)
    return round(better_or_equal / len(values) * 100, 1), better + 1


def benchmark_band(
    percentile_rank: float | None,
    sample_size: int,
    athlete_value: float | None,
) -> str:
    if sample_size == 0:
        return "no_data"
    if athlete_value is None or percentile_rank is None:
        return "cohort_ready"
    if percentile_rank >= 75:
        return "top_quartile"
    if percentile_rank >= 55:
        return "above_cohort"
    if percentile_rank >= 40:
        return "on_track"
    return "watch"


def performance_observation_period_bounds(
    period_start: date | None,
    period_end: date | None,
) -> tuple[datetime | None, datetime | None]:
    if period_start is not None and period_end is not None and period_end < period_start:
        raise HTTPException(
            status_code=422,
            detail="period_end must be on or after period_start",
        )
    start_at = datetime.combine(period_start, datetime.min.time(), UTC) if period_start else None
    end_at = datetime.combine(period_end, datetime.max.time(), UTC) if period_end else None
    return start_at, end_at


def normalize_benchmark_scope(cohort_scope: str) -> str:
    normalized = cohort_scope.strip().lower()
    if normalized in {
        "tenant",
        "age_group",
        "position",
        "region",
        "local_association",
        "regional_association",
    }:
        return normalized
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=(
            "cohort_scope must be one of tenant, age_group, position, region, "
            "local_association, or regional_association"
        ),
    )


async def athlete_benchmark_contexts(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_ids: set[UUID],
) -> dict[UUID, dict[str, str | None]]:
    if not athlete_profile_ids:
        return {}
    rows = (
        await db.execute(
            select(
                AthleteProfile.id,
                AthleteProfile.organization_id,
                Person.date_of_birth,
                Person.country_code,
                Team.id,
                TeamRosterEntry.primary_position,
                Team.age_group,
            )
            .join(Person, Person.id == AthleteProfile.person_id)
            .outerjoin(
                TeamRosterEntry,
                TeamRosterEntry.athlete_profile_id == AthleteProfile.id,
            )
            .outerjoin(Team, Team.id == TeamRosterEntry.team_id)
            .where(AthleteProfile.organization_id == organization_id)
            .where(AthleteProfile.id.in_(list(athlete_profile_ids)))
        )
    ).all()
    contexts: dict[UUID, dict[str, str | None]] = {}
    organization_ids_by_athlete: dict[UUID, set[UUID]] = {}
    team_ids_by_athlete: dict[UUID, set[UUID]] = {}
    for (
        athlete_profile_id,
        athlete_organization_id,
        date_of_birth,
        country_code,
        team_id,
        primary_position,
        team_age_group,
    ) in rows:
        context = contexts.setdefault(
            athlete_profile_id,
            {
                "age_group": None,
                "position": None,
                "region": None,
                "local_association": None,
                "regional_association": None,
            },
        )
        organization_ids_by_athlete.setdefault(athlete_profile_id, set()).add(athlete_organization_id)
        if team_id is not None:
            team_ids_by_athlete.setdefault(athlete_profile_id, set()).add(team_id)
        if context["age_group"] is None:
            context["age_group"] = team_age_group or age_group_from_birthdate(date_of_birth)
        if context["position"] is None and primary_position:
            context["position"] = primary_position
        if context["region"] is None and country_code:
            context["region"] = country_code.upper()
    await add_association_benchmark_contexts(
        db,
        contexts,
        organization_ids_by_athlete,
        team_ids_by_athlete,
    )
    return contexts


async def add_association_benchmark_contexts(
    db: AsyncSession,
    contexts: dict[UUID, dict[str, str | None]],
    organization_ids_by_athlete: dict[UUID, set[UUID]],
    team_ids_by_athlete: dict[UUID, set[UUID]],
) -> None:
    organization_athlete_ids: dict[UUID, set[UUID]] = {}
    team_athlete_ids: dict[UUID, set[UUID]] = {}
    for athlete_id, organization_ids in organization_ids_by_athlete.items():
        for organization_id in organization_ids:
            organization_athlete_ids.setdefault(organization_id, set()).add(athlete_id)
    for athlete_id, team_ids in team_ids_by_athlete.items():
        for team_id in team_ids:
            team_athlete_ids.setdefault(team_id, set()).add(athlete_id)
    if not organization_athlete_ids and not team_athlete_ids:
        return

    conditions = []
    if organization_athlete_ids:
        conditions.append(
            and_(
                Membership.subject_type == MemberSubjectType.ORGANIZATION,
                Membership.subject_id.in_(list(organization_athlete_ids)),
            )
        )
    if team_athlete_ids:
        conditions.append(
            and_(
                Membership.subject_type == MemberSubjectType.TEAM,
                Membership.subject_id.in_(list(team_athlete_ids)),
            )
        )
    subject_filter = (
        conditions[0] if len(conditions) == 1 else or_(*conditions)
    )
    rows = (
        await db.execute(
            select(
                Membership.subject_type,
                Membership.subject_id,
                Organization.name,
                Organization.association_level,
            )
            .join(Organization, Organization.id == Membership.organization_id)
            .where(Membership.status == "active")
            .where(subject_filter)
            .where(
                Organization.association_level.in_(
                    [AssociationLevel.LOCAL, AssociationLevel.REGIONAL]
                )
            )
            .order_by(Organization.name.asc())
        )
    ).all()
    for subject_type, subject_id, association_name, association_level in rows:
        athlete_ids = (
            organization_athlete_ids.get(subject_id, set())
            if subject_type == MemberSubjectType.ORGANIZATION
            else team_athlete_ids.get(subject_id, set())
        )
        key = (
            "local_association"
            if association_level == AssociationLevel.LOCAL
            else "regional_association"
        )
        for athlete_id in athlete_ids:
            context = contexts.get(athlete_id)
            if context is not None and context[key] is None:
                context[key] = association_name


def age_group_from_birthdate(date_of_birth: date | None) -> str | None:
    if date_of_birth is None:
        return None
    today = date.today()
    age = today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )
    if age <= 8:
        return "U8"
    if age <= 10:
        return "U10"
    if age <= 12:
        return "U12"
    if age <= 14:
        return "U14"
    if age <= 16:
        return "U16"
    if age <= 18:
        return "U18"
    return "Adult"


def benchmark_cohort_label(cohort_scope: str, target_context: dict[str, str | None] | None) -> str:
    if cohort_scope == "tenant":
        return "All athletes"
    value = target_context.get(cohort_scope) if target_context is not None else None
    return value or f"Unknown {cohort_scope.replace('_', ' ')}"


def benchmark_context_matches(
    cohort_scope: str,
    target_context: dict[str, str | None] | None,
    candidate_context: dict[str, str | None] | None,
) -> bool:
    if cohort_scope == "tenant":
        return True
    if target_context is None or candidate_context is None:
        return False
    target_value = normalized_cohort_value(target_context.get(cohort_scope))
    candidate_value = normalized_cohort_value(candidate_context.get(cohort_scope))
    return bool(target_value) and target_value == candidate_value


def normalized_cohort_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.strip().lower().split())
    return normalized or None


def cohort_comparison_recommendation(
    cohort_scope: str,
    cohort_label: str,
    average_percentile: float | None,
    watch_count: int,
) -> str:
    label = cohort_label.lower()
    scope_label = cohort_scope.replace("_", " ")
    if average_percentile is None:
        return f"Capture accepted observations before comparing this athlete against the {label} {scope_label} cohort."
    if watch_count > 0:
        return f"Prioritize {watch_count} watch metric(s) inside the {label} {scope_label} cohort."
    if average_percentile >= 75:
        return f"This athlete is outperforming the {label} {scope_label} cohort; raise progression targets."
    if average_percentile >= 55:
        return f"This athlete is ahead of the {label} {scope_label} cohort; maintain the current development block."
    if average_percentile >= 40:
        return f"This athlete is broadly aligned with the {label} {scope_label} cohort; keep monitoring trend movement."
    return f"This athlete trails the {label} {scope_label} cohort; assign targeted coaching support."


def performance_benchmark_recommendation(
    band: str,
    metric_name: str,
    unit: str | None,
    athlete_value: float | None,
    average: float | None,
) -> str:
    suffix = f" {unit}" if unit else ""
    if band == "no_data":
        return f"Record at least one {metric_name} observation to establish the cohort baseline."
    if band == "cohort_ready":
        return f"Cohort baseline is ready; select an athlete to compare {metric_name}."
    if athlete_value is None or average is None:
        return f"Continue collecting {metric_name} observations before making coaching decisions."
    if band == "top_quartile":
        return (
            f"Protect the strength: athlete value {athlete_value:g}{suffix} is ahead of "
            f"the cohort average {average:g}{suffix}."
        )
    if band == "above_cohort":
        return (
            f"Maintain progression: athlete value {athlete_value:g}{suffix} is trending above "
            f"the cohort average {average:g}{suffix}."
        )
    if band == "on_track":
        return (
            f"Keep the current plan and reassess soon; athlete value {athlete_value:g}{suffix} "
            f"is near the cohort average {average:g}{suffix}."
        )
    return (
        f"Prioritize targeted work on {metric_name}; athlete value {athlete_value:g}{suffix} "
        f"is behind the cohort average {average:g}{suffix}."
    )


def metric_trend_summary(
    values: list[float],
    higher_is_better: bool,
    metric_name: str,
    unit: str | None,
) -> dict[str, object]:
    if not values:
        return {
            "sample_size": 0,
            "first_value": None,
            "previous_value": None,
            "latest_value": None,
            "best_value": None,
            "average_value": None,
            "change_from_previous": None,
            "change_from_first": None,
            "consistency_index": None,
            "forecast_next_value": None,
            "trend_direction": "no_data",
            "recommendation": f"Record {metric_name} observations to start trend analysis.",
        }

    first = values[0]
    latest = values[-1]
    previous = values[-2] if len(values) >= 2 else None
    best = max(values) if higher_is_better else min(values)
    average = sum(values) / len(values)
    change_previous = directional_change(latest, previous, higher_is_better)
    change_first = directional_change(latest, first, higher_is_better) if len(values) >= 2 else None
    forecast = forecast_next_value(values)
    direction = trend_direction(change_first, values)
    return {
        "sample_size": len(values),
        "first_value": round(first, 2),
        "previous_value": round(previous, 2) if previous is not None else None,
        "latest_value": round(latest, 2),
        "best_value": round(best, 2),
        "average_value": round(average, 2),
        "change_from_previous": round(change_previous, 2)
        if change_previous is not None
        else None,
        "change_from_first": round(change_first, 2) if change_first is not None else None,
        "consistency_index": consistency_index(values),
        "forecast_next_value": round(forecast, 2) if forecast is not None else None,
        "trend_direction": direction,
        "recommendation": trend_recommendation(
            direction,
            metric_name,
            unit,
            latest,
            average,
            change_first,
        ),
    }


def forecast_scenario_summary(
    values: list[float],
    higher_is_better: bool,
    metric_name: str,
    unit: str | None,
    trend: dict[str, object],
    training_adjustment_percent: float = 0.0,
    readiness_score: int | None = None,
    horizon: int = 4,
    model_policy: str = "deterministic_forecast_v1",
) -> dict[str, object]:
    sample_size = len(values)
    forecast = forecast_next_value(values, training_adjustment_percent, readiness_score, higher_is_better)
    consistency = trend["consistency_index"]
    direction = str(trend["trend_direction"])
    projected_points = projected_forecast_points(
        values,
        horizon=horizon,
        training_adjustment_percent=training_adjustment_percent,
        readiness_score=readiness_score,
        higher_is_better=higher_is_better,
    )
    band = forecast_band(values)
    forecast_low = round(float(forecast) - band, 2) if isinstance(forecast, int | float) else None
    forecast_high = round(float(forecast) + band, 2) if isinstance(forecast, int | float) else None
    confidence = forecast_confidence(sample_size, consistency if isinstance(consistency, int | float) else None)
    data_quality = forecast_data_quality(sample_size, confidence)
    risk_level = forecast_risk_level(direction, confidence, data_quality, readiness_score)
    return {
        "sample_size": sample_size,
        "latest_value": trend["latest_value"],
        "forecast_next_value": round(forecast, 2) if forecast is not None else None,
        "forecast_low": forecast_low,
        "forecast_high": forecast_high,
        "confidence": confidence,
        "data_quality": data_quality,
        "risk_level": risk_level,
        "trend_direction": direction,
        "model_policy": model_policy,
        "projected_points": projected_points,
        "recommendation": forecast_recommendation(
            metric_name,
            unit,
            higher_is_better,
            direction,
            data_quality,
            risk_level,
            trend["latest_value"],
            forecast,
            forecast_low,
            forecast_high,
            training_adjustment_percent,
            readiness_score,
        ),
    }


async def model_assisted_performance_forecast(
    settings: Settings,
    athlete_profile_id: UUID,
    metric: PerformanceMetricDefinition,
    observations: list[AthletePerformanceObservation],
    trend: dict[str, object],
    baseline: dict[str, object],
    scenario_type: str,
    training_adjustment_percent: float = 0.0,
    readiness_score: int | None = None,
    horizon: int = 4,
) -> dict[str, object] | None:
    if settings.performance_forecast_mode == "off" or not observations:
        return None
    if settings.performance_forecast_mode == "webhook":
        return await webhook_performance_forecast(
            settings,
            athlete_profile_id,
            metric,
            observations,
            trend,
            baseline,
            scenario_type,
            training_adjustment_percent,
            readiness_score,
            horizon,
        )
    return deterministic_performance_forecast(settings, baseline)


def deterministic_performance_forecast(
    settings: Settings,
    baseline: dict[str, object],
) -> dict[str, object]:
    confidence = structured_float(baseline.get("confidence")) or 0.0
    return {
        "model_policy": settings.performance_forecast_model,
        "confidence": round(min(0.95, confidence + 0.03), 2),
        "summary": "Local governed forecast model reviewed the deterministic runway.",
    }


async def webhook_performance_forecast(
    settings: Settings,
    athlete_profile_id: UUID,
    metric: PerformanceMetricDefinition,
    observations: list[AthletePerformanceObservation],
    trend: dict[str, object],
    baseline: dict[str, object],
    scenario_type: str,
    training_adjustment_percent: float,
    readiness_score: int | None,
    horizon: int,
) -> dict[str, object] | None:
    if not settings.performance_forecast_webhook_url:
        return None
    key_resolution = await resolve_performance_forecast_webhook_key(settings)
    request_payload = {
        "event": "afrolete.performance.forecast",
        "model": settings.performance_forecast_model,
        "athlete_profile_id": str(athlete_profile_id),
        "scenario_type": scenario_type,
        "controls": {
            "training_adjustment_percent": round(training_adjustment_percent, 1),
            "readiness_score": readiness_score,
            "horizon": horizon,
        },
        "metric": {
            "id": str(metric.id),
            "code": metric.code,
            "name": metric.name,
            "sport": metric.sport,
            "category": metric.category.value,
            "unit": metric.unit,
            "higher_is_better": metric.higher_is_better,
            "min_value": metric.min_value,
            "max_value": metric.max_value,
        },
        "observations": [
            {
                "id": str(observation.id),
                "value": observation.value,
                "observed_at": observation.observed_at,
                "source": observation.source.value,
                "verification_status": observation.verification_status.value,
            }
            for observation in observations[-24:]
        ],
        "trend": trend,
        "deterministic_baseline": baseline,
    }
    body = stable_payload_text(request_payload).encode()
    try:
        async with httpx.AsyncClient(timeout=settings.performance_forecast_timeout_seconds) as client:
            response = await client.post(
                settings.performance_forecast_webhook_url,
                content=body,
                headers=performance_forecast_webhook_headers(settings, body, str(key_resolution["key"] or "")),
            )
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    return webhook_performance_forecast_result(settings, response)


async def resolve_performance_forecast_webhook_key(settings: Settings) -> dict[str, str | None]:
    try:
        key = await resolve_secret(
            settings,
            env_value=settings.performance_forecast_webhook_key,
            path=settings.performance_forecast_webhook_key_secret_path,
            field_name=settings.performance_forecast_webhook_key_secret_field,
            label="performance forecast webhook key",
        )
    except HTTPException:
        return {"key": None}
    return {"key": key}


def performance_forecast_webhook_headers(settings: Settings, body: bytes, signing_key: str = "") -> dict[str, str]:
    headers = {
        "User-Agent": "AfroLete-Performance-Forecaster/1.0",
        "Content-Type": "application/json",
    }
    if signing_key:
        timestamp = str(int(time.time()))
        digest = hmac.new(signing_key.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
        headers["X-Afrolete-Performance-Forecast-Timestamp"] = timestamp
        headers["X-Afrolete-Performance-Forecast-Signature"] = f"sha256={digest}"
        headers["X-Afrolete-Performance-Forecast-Key-Source"] = (
            "openbao" if settings.performance_forecast_webhook_key_secret_path else "env"
        )
    return headers


def webhook_performance_forecast_result(settings: Settings, response: httpx.Response) -> dict[str, object] | None:
    try:
        result = response.json()
    except ValueError:
        return None
    if not isinstance(result, dict):
        return None
    forecast = structured_float(result.get("forecast_next_value"))
    if forecast is None:
        forecast = structured_float(result.get("forecast"))
    projected_points = structured_float_list(result.get("projected_points"), limit=12)
    if forecast is None and not projected_points:
        return None
    model_policy = str(result.get("model") or settings.performance_forecast_model)[:160]
    return {
        "model_policy": model_policy,
        "forecast_next_value": forecast,
        "forecast_low": structured_float(result.get("forecast_low")),
        "forecast_high": structured_float(result.get("forecast_high")),
        "confidence": structured_float(result.get("confidence")),
        "data_quality": str(result.get("data_quality")) if result.get("data_quality") else None,
        "risk_level": str(result.get("risk_level")) if result.get("risk_level") else None,
        "projected_points": projected_points,
        "recommendation": str(result.get("recommendation"))[:1000] if result.get("recommendation") else None,
    }


def apply_model_forecast_summary(
    baseline: dict[str, object],
    model_forecast: dict[str, object],
) -> dict[str, object]:
    summary = dict(baseline)
    summary["model_policy"] = model_forecast["model_policy"]
    for key in ("forecast_next_value", "forecast_low", "forecast_high"):
        value = structured_float(model_forecast.get(key))
        if value is not None:
            summary[key] = round(value, 2)
    confidence = structured_float(model_forecast.get("confidence"))
    if confidence is not None:
        summary["confidence"] = round(max(0, min(confidence, 1)), 2)
    data_quality = normalized_forecast_data_quality(model_forecast.get("data_quality"))
    if data_quality is not None:
        summary["data_quality"] = data_quality
    risk_level = normalized_forecast_risk_level(model_forecast.get("risk_level"))
    if risk_level is not None:
        summary["risk_level"] = risk_level
    projected_points = structured_float_list(model_forecast.get("projected_points"), limit=12)
    if projected_points:
        summary["projected_points"] = [round(point, 2) for point in projected_points]
    recommendation = model_forecast.get("recommendation")
    if isinstance(recommendation, str) and recommendation.strip():
        summary["recommendation"] = recommendation.strip()[:1000]
    return summary


def normalized_forecast_data_quality(value: object) -> str | None:
    normalized = str(value or "").strip().lower()
    if normalized in {"no_data", "thin_history", "usable_history", "strong_history", "model_assisted"}:
        return normalized
    return None


def normalized_forecast_risk_level(value: object) -> str | None:
    normalized = str(value or "").strip().lower()
    if normalized in {"no_data", "needs_more_data", "recovery", "watch", "opportunity", "stable", "high_upside"}:
        return normalized
    return None


def structured_float_list(value: object, limit: int = 12) -> list[float]:
    if not isinstance(value, list):
        return []
    points: list[float] = []
    for item in value[:limit]:
        point = structured_float(item)
        if point is not None:
            points.append(point)
    return points


def projected_forecast_points(
    values: list[float],
    horizon: int,
    training_adjustment_percent: float = 0.0,
    readiness_score: int | None = None,
    higher_is_better: bool = True,
) -> list[float]:
    if not values:
        return []
    delta = adjusted_observation_delta(values, training_adjustment_percent, readiness_score, higher_is_better)
    current = values[-1]
    points: list[float] = []
    for _ in range(horizon):
        current += delta
        points.append(round(current, 2))
    return points


def adjusted_observation_delta(
    values: list[float],
    training_adjustment_percent: float,
    readiness_score: int | None,
    higher_is_better: bool,
) -> float:
    if not values:
        return 0.0
    baseline = average_observation_delta(values)
    if training_adjustment_percent == 0:
        return baseline
    latest_magnitude = abs(values[-1]) or 1.0
    baseline_magnitude = max(abs(baseline), latest_magnitude * 0.01)
    readiness_multiplier = readiness_adjustment_multiplier(readiness_score)
    adjustment = baseline_magnitude * (training_adjustment_percent / 100.0) * readiness_multiplier
    direction = 1 if higher_is_better else -1
    return baseline + (direction * adjustment)


def readiness_adjustment_multiplier(readiness_score: int | None) -> float:
    if readiness_score is None:
        return 1.0
    if readiness_score < 45:
        return 0.35
    if readiness_score < 65:
        return 0.65
    if readiness_score > 85:
        return 1.1
    return 1.0


def average_observation_delta(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    deltas = [current - previous for previous, current in zip(values[:-1], values[1:], strict=True)]
    return sum(deltas) / len(deltas)


def forecast_band(values: list[float]) -> float:
    if not values:
        return 0.0
    volatility = pstdev(values) if len(values) >= 2 else 0.0
    momentum = abs(average_observation_delta(values))
    latest_magnitude = abs(values[-1]) or 1.0
    floor = latest_magnitude * 0.03
    return round(max(volatility, momentum, floor), 2)


def forecast_confidence(sample_size: int, consistency: float | None) -> float:
    if sample_size == 0:
        return 0.0
    consistency_factor = (consistency if consistency is not None else 50.0) / 100.0
    sample_factor = min(1.0, sample_size / 6)
    return round(max(0.2, min(0.95, 0.25 + (sample_factor * 0.45) + (consistency_factor * 0.25))), 2)


def forecast_data_quality(sample_size: int, confidence: float) -> str:
    if sample_size == 0:
        return "no_data"
    if sample_size < 3:
        return "thin_history"
    if sample_size >= 6 and confidence >= 0.75:
        return "strong_history"
    return "usable_history"


def forecast_risk_level(
    direction: str,
    confidence: float,
    data_quality: str,
    readiness_score: int | None = None,
) -> str:
    if data_quality == "no_data":
        return "no_data"
    if data_quality == "thin_history":
        return "needs_more_data"
    if readiness_score is not None and readiness_score < 45:
        return "recovery"
    if readiness_score is not None and readiness_score < 60:
        return "watch"
    if direction == "declining" or confidence < 0.5:
        return "watch"
    if direction == "improving":
        return "opportunity"
    return "stable"


def forecast_recommendation(
    metric_name: str,
    unit: str | None,
    higher_is_better: bool,
    direction: str,
    data_quality: str,
    risk_level: str,
    latest: object,
    forecast: object,
    forecast_low: float | None,
    forecast_high: float | None,
    training_adjustment_percent: float = 0.0,
    readiness_score: int | None = None,
) -> str:
    if data_quality == "no_data":
        return f"Record accepted {metric_name} observations before producing a forecast scenario."
    suffix = f" {unit}" if unit else ""
    latest_text = f"{float(latest):g}{suffix}" if isinstance(latest, int | float) else "n/a"
    forecast_text = f"{float(forecast):g}{suffix}" if isinstance(forecast, int | float) else "n/a"
    band_text = (
        f"expected range {forecast_low:g}-{forecast_high:g}{suffix}"
        if forecast_low is not None and forecast_high is not None
        else "expected range unavailable"
    )
    if risk_level == "needs_more_data":
        return (
            f"{metric_name} forecast is based on a thin history; collect another accepted data point "
            f"before changing the plan. Latest {latest_text}, next scenario {forecast_text}."
        )
    if risk_level == "recovery":
        return (
            f"{metric_name} what-if scenario is recovery constrained at readiness {readiness_score}. "
            f"Keep intensity low until readiness improves; latest {latest_text}, next scenario {forecast_text}."
        )
    if risk_level == "watch":
        adjustment_text = f" under {training_adjustment_percent:g}% training adjustment" if training_adjustment_percent else ""
        return (
            f"{metric_name} is a watch item{adjustment_text} with {band_text}. Review load, recovery, and technique "
            f"before chasing the next scenario from latest {latest_text}."
        )
    if risk_level == "opportunity":
        action = "raise the target" if higher_is_better else "tighten the target"
        adjustment_text = f" with a {training_adjustment_percent:g}% training adjustment" if training_adjustment_percent else ""
        return (
            f"{metric_name} has an improving scenario{adjustment_text} from latest {latest_text} to {forecast_text}; "
            f"{action} while preserving the current training stimulus."
        )
    if direction == "stable":
        return (
            f"{metric_name} is stable around latest {latest_text}; use {band_text} as the next "
            f"checkpoint and add a focused stimulus if progress stalls."
        )
    return (
        f"Keep collecting {metric_name} data; current deterministic scenario projects {forecast_text} "
        f"from latest {latest_text}."
    )


def what_if_scenario_label(training_adjustment_percent: float, readiness_score: int) -> str:
    if training_adjustment_percent > 0:
        adjustment = f"+{training_adjustment_percent:g}% load"
    elif training_adjustment_percent < 0:
        adjustment = f"{training_adjustment_percent:g}% load"
    else:
        adjustment = "baseline load"
    return f"{adjustment}, readiness {readiness_score}"


def injury_risk_summary(
    athlete_profile_id: UUID,
    feedback_rows: list[tuple[TrainingSessionFeedback, TrainingSessionPlan]],
    open_incident_count: int,
    declining_metric_count: int,
    environmental_context: dict[str, object] | None = None,
    biomarker_context: dict[str, object] | None = None,
    biomechanical_context: dict[str, object] | None = None,
) -> dict[str, object]:
    environmental_context = environmental_context or default_injury_risk_environment_context()
    biomarker_context = biomarker_context or default_injury_risk_biomarker_context()
    biomechanical_context = biomechanical_context or default_injury_risk_biomechanical_context()
    feedbacks = [feedback for feedback, _ in feedback_rows]
    loads = [training_feedback_load(feedback, session_plan) for feedback, session_plan in feedback_rows]
    now = datetime.now(UTC)
    latest_feedback = feedbacks[0] if feedbacks else None
    latest_load = loads[0] if loads else None
    average_load = average_or_none(loads)
    recent_loads = [
        training_feedback_load(feedback, session_plan)
        for feedback, session_plan in feedback_rows
        if (recorded_at := as_utc_datetime(feedback.recorded_at)) is not None
        and recorded_at >= now - timedelta(days=7)
    ]
    chronic_loads = [
        training_feedback_load(feedback, session_plan)
        for feedback, session_plan in feedback_rows
        if (recorded_at := as_utc_datetime(feedback.recorded_at)) is not None
        and recorded_at >= now - timedelta(days=28)
    ]
    acute_load = sum(recent_loads) if recent_loads else None
    chronic_load = sum(chronic_loads) if chronic_loads else None
    acute_chronic_ratio = (
        round((acute_load / 7) / (chronic_load / 28), 2)
        if acute_load is not None and chronic_load not in {None, 0}
        else None
    )
    load_delta = latest_load - average_load if latest_load is not None and average_load is not None else None
    average_readiness = average_or_none([feedback.readiness_score for feedback in feedbacks])
    average_soreness = average_or_none([feedback.soreness_score for feedback in feedbacks])
    average_sleep = average_or_none([feedback.sleep_quality for feedback in feedbacks])

    score = 10.0
    drivers: list[str] = []
    if latest_feedback is None:
        drivers.append("No athlete-specific training feedback has been recorded yet.")
    else:
        readiness_penalty = max(0, 100 - latest_feedback.readiness_score) * 0.25
        score += readiness_penalty
        if latest_feedback.readiness_score < 60:
            drivers.append(f"Latest readiness is low at {latest_feedback.readiness_score}/100.")
        if average_soreness is not None:
            soreness_penalty = average_soreness * 4
            score += soreness_penalty
            if average_soreness >= 6:
                drivers.append(f"Average soreness is elevated at {average_soreness:.1f}/10.")
        if average_sleep is not None:
            sleep_penalty = max(0, 7 - average_sleep) * 4
            score += sleep_penalty
            if average_sleep <= 5:
                drivers.append(f"Average sleep quality is low at {average_sleep:.1f}/10.")
    if load_delta is not None and load_delta > 150:
        score += min(25, load_delta / 20)
        drivers.append(f"Latest training load is {load_delta:.0f} above the athlete average.")
    if acute_chronic_ratio is not None:
        if acute_chronic_ratio > 1.5:
            score += 20
            drivers.append(f"Acute:chronic workload ratio is high at {acute_chronic_ratio}.")
        elif acute_chronic_ratio > 1.25:
            score += 12
            drivers.append(f"Acute:chronic workload ratio is rising at {acute_chronic_ratio}.")
    if open_incident_count:
        score += min(30, open_incident_count * 18)
        drivers.append(f"{open_incident_count} open injury or medical incident(s) require attention.")
    if declining_metric_count:
        score += min(20, declining_metric_count * 6)
        drivers.append(f"{declining_metric_count} performance metric trend(s) are declining.")
    weather_alert_count = int(environmental_context["weather_alert_count"])
    hazardous_surface_count = int(environmental_context["hazardous_surface_count"])
    environmental_risk_count = weather_alert_count + hazardous_surface_count
    if weather_alert_count:
        score += int(environmental_context["weather_score_penalty"])
        latest_weather = environmental_context["latest_weather_alert_level"]
        latest_decision = environmental_context["latest_weather_decision"]
        drivers.append(
            f"{weather_alert_count} recent weather risk assessment(s) include {latest_weather}/{latest_decision} conditions."
        )
    if hazardous_surface_count:
        score += min(12, hazardous_surface_count * 6)
        labels = ", ".join(str(label) for label in environmental_context["surface_risk_labels"])
        drivers.append(f"{hazardous_surface_count} recent session venue surface risk marker(s): {labels}.")
    biomarker_risk_count = int(biomarker_context["biomarker_risk_count"])
    if biomarker_risk_count:
        score += int(biomarker_context["biomarker_score_penalty"])
        labels = ", ".join(str(label) for label in biomarker_context["wearable_risk_labels"])
        drivers.append(f"{biomarker_risk_count} wearable biomarker risk marker(s): {labels}.")
    biomechanical_risk_count = int(biomechanical_context["biomechanical_risk_count"])
    if biomechanical_risk_count:
        score += int(biomechanical_context["biomechanical_score_penalty"])
        labels = ", ".join(str(label) for label in biomechanical_context["video_risk_labels"])
        drivers.append(f"{biomechanical_risk_count} biomechanical video risk marker(s): {labels}.")

    rounded_score = int(round(max(0, min(100, score))))
    band = injury_risk_band(rounded_score)
    if not drivers:
        drivers.append("Training feedback, workload, incidents, and performance trends are within routine range.")
    return {
        "athlete_profile_id": athlete_profile_id,
        "generated_at": now,
        "model_policy": "deterministic_injury_risk_v4_biomarker_environmental_biomechanical",
        "score": rounded_score,
        "risk_band": band,
        "confidence": injury_risk_confidence(
            len(feedbacks),
            open_incident_count,
            declining_metric_count,
            environmental_risk_count,
            biomarker_risk_count,
            biomechanical_risk_count,
        ),
        "latest_readiness_score": latest_feedback.readiness_score if latest_feedback is not None else None,
        "average_readiness_score": round(average_readiness, 1) if average_readiness is not None else None,
        "average_soreness_score": round(average_soreness, 1) if average_soreness is not None else None,
        "average_sleep_quality": round(average_sleep, 1) if average_sleep is not None else None,
        "latest_load": round(latest_load, 1) if latest_load is not None else None,
        "average_load": round(average_load, 1) if average_load is not None else None,
        "acute_load": round(acute_load, 1) if acute_load is not None else None,
        "chronic_load": round(chronic_load, 1) if chronic_load is not None else None,
        "acute_chronic_ratio": acute_chronic_ratio,
        "load_delta": round(load_delta, 1) if load_delta is not None else None,
        "open_incident_count": open_incident_count,
        "declining_metric_count": declining_metric_count,
        "latest_weather_alert_level": environmental_context["latest_weather_alert_level"],
        "latest_weather_decision": environmental_context["latest_weather_decision"],
        "weather_alert_count": weather_alert_count,
        "hazardous_surface_count": hazardous_surface_count,
        "environmental_risk_count": environmental_risk_count,
        "surface_risk_labels": environmental_context["surface_risk_labels"],
        "wearable_observation_count": biomarker_context["wearable_observation_count"],
        "biomarker_risk_count": biomarker_risk_count,
        "latest_hrv": biomarker_context["latest_hrv"],
        "latest_resting_heart_rate": biomarker_context["latest_resting_heart_rate"],
        "latest_recovery_score": biomarker_context["latest_recovery_score"],
        "latest_hydration_score": biomarker_context["latest_hydration_score"],
        "wearable_risk_labels": biomarker_context["wearable_risk_labels"],
        "biomechanical_observation_count": biomechanical_context["biomechanical_observation_count"],
        "biomechanical_risk_count": biomechanical_risk_count,
        "latest_movement_quality_score": biomechanical_context["latest_movement_quality_score"],
        "latest_asymmetry_score": biomechanical_context["latest_asymmetry_score"],
        "video_risk_labels": biomechanical_context["video_risk_labels"],
        "drivers": drivers,
        "recommendation": injury_risk_recommendation(band),
    }


def training_feedback_load(feedback: TrainingSessionFeedback, session_plan: TrainingSessionPlan) -> float:
    if feedback.actual_rpe is not None:
        return float((feedback.actual_duration_minutes or session_plan.duration_minutes) * feedback.actual_rpe)
    return float(session_plan.load_score)


def average_or_none(values: list[float | int]) -> float | None:
    if not values:
        return None
    return sum(float(value) for value in values) / len(values)


def injury_risk_band(score: int) -> str:
    if score >= 85:
        return "critical"
    if score >= 65:
        return "high"
    if score >= 35:
        return "watch"
    return "low"


async def injury_risk_environment_context(
    db: AsyncSession,
    organization_id: UUID,
    feedback_rows: list[tuple[TrainingSessionFeedback, TrainingSessionPlan]],
) -> dict[str, object]:
    session_plans = [session_plan for _, session_plan in feedback_rows]
    event_ids = {session_plan.event_id for session_plan in session_plans if session_plan.event_id is not None}
    weather_rows: list[EventWeatherAssessment] = []
    if event_ids:
        weather_rows = list(
            (
                await db.scalars(
                    select(EventWeatherAssessment)
                    .where(EventWeatherAssessment.organization_id == organization_id)
                    .where(EventWeatherAssessment.event_id.in_(list(event_ids)))
                    .order_by(EventWeatherAssessment.observed_at.desc(), EventWeatherAssessment.created_at.desc())
                )
            ).all()
        )
    alert_weather_rows = [
        assessment
        for assessment in weather_rows
        if assessment.alert_level in {WeatherAlertLevel.ADVISORY, WeatherAlertLevel.WARNING, WeatherAlertLevel.CRITICAL}
    ]
    latest_weather = alert_weather_rows[0] if alert_weather_rows else weather_rows[0] if weather_rows else None
    weather_alert_count = len(alert_weather_rows)
    weather_score_penalty = sum(weather_alert_score_penalty(assessment.alert_level) for assessment in weather_rows)
    venue_names = {
        normalized_surface_label(session_plan.title)
        for session_plan in session_plans
        if session_plan.title
    }
    event_rows: list[Event] = []
    if event_ids:
        event_rows = list(
            (
                await db.scalars(
                    select(Event)
                    .where(Event.organization_id == organization_id)
                    .where(Event.id.in_(list(event_ids)))
                )
            ).all()
        )
        venue_names.update(
            normalized_surface_label(event.venue_name)
            for event in event_rows
            if event.venue_name
        )
    facilities = []
    if venue_names:
        facilities = list(
            (
                await db.scalars(
                    select(Facility).where(Facility.organization_id == organization_id)
                )
            ).all()
        )
    surface_labels: list[str] = []
    for facility in facilities:
        name = normalized_surface_label(facility.name)
        if name not in venue_names:
            continue
        marker = hazardous_surface_label(facility.surface)
        if marker and marker not in surface_labels:
            surface_labels.append(marker)
    return {
        "latest_weather_alert_level": latest_weather.alert_level.value if latest_weather is not None else None,
        "latest_weather_decision": latest_weather.decision.value if latest_weather is not None else None,
        "weather_alert_count": weather_alert_count,
        "weather_score_penalty": min(24, weather_score_penalty),
        "hazardous_surface_count": len(surface_labels),
        "surface_risk_labels": surface_labels,
    }


def default_injury_risk_environment_context() -> dict[str, object]:
    return {
        "latest_weather_alert_level": None,
        "latest_weather_decision": None,
        "weather_alert_count": 0,
        "weather_score_penalty": 0,
        "hazardous_surface_count": 0,
        "surface_risk_labels": [],
    }


def weather_alert_score_penalty(alert_level: WeatherAlertLevel) -> int:
    return {
        WeatherAlertLevel.INFORMATION: 0,
        WeatherAlertLevel.ADVISORY: 4,
        WeatherAlertLevel.WARNING: 8,
        WeatherAlertLevel.CRITICAL: 14,
    }[alert_level]


def normalized_surface_label(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def hazardous_surface_label(surface: str | None) -> str | None:
    normalized = normalized_surface_label(surface)
    if not normalized:
        return None
    markers = {
        "hard": "hard surface",
        "concrete": "concrete surface",
        "asphalt": "asphalt surface",
        "uneven": "uneven surface",
        "wet": "wet surface",
        "mud": "muddy surface",
        "muddy": "muddy surface",
        "slippery": "slippery surface",
        "poor": "poor surface",
        "damaged": "damaged surface",
        "synthetic": "synthetic surface",
        "artificial": "artificial surface",
    }
    for marker, label in markers.items():
        if marker in normalized:
            return label
    return None


async def injury_risk_biomarker_context(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> dict[str, object]:
    rows = list(
        (
            await db.execute(
                select(AthletePerformanceObservation, PerformanceMetricDefinition)
                .join(
                    PerformanceMetricDefinition,
                    PerformanceMetricDefinition.id == AthletePerformanceObservation.metric_definition_id,
                )
                .where(AthletePerformanceObservation.organization_id == organization_id)
                .where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
                .where(AthletePerformanceObservation.source == MetricSource.WEARABLE)
                .where(AthletePerformanceObservation.verification_status != MetricVerificationStatus.REJECTED)
                .order_by(AthletePerformanceObservation.observed_at.desc())
                .limit(80)
            )
        ).all()
    )
    latest_by_family: dict[str, float] = {}
    risk_labels: list[str] = []
    score_penalty = 0
    for observation, metric in rows:
        family = wearable_metric_family(metric)
        if family is None:
            continue
        latest_by_family.setdefault(family, float(observation.value))
        marker = wearable_biomarker_risk_marker(family, float(observation.value))
        if marker is None:
            continue
        label, penalty = marker
        if label not in risk_labels:
            risk_labels.append(label)
            score_penalty += penalty
    return {
        "wearable_observation_count": len(rows),
        "biomarker_risk_count": len(risk_labels),
        "biomarker_score_penalty": min(24, score_penalty),
        "latest_hrv": rounded_latest_biomarker(latest_by_family.get("hrv")),
        "latest_resting_heart_rate": rounded_latest_biomarker(latest_by_family.get("resting_heart_rate")),
        "latest_recovery_score": rounded_latest_biomarker(latest_by_family.get("recovery")),
        "latest_hydration_score": rounded_latest_biomarker(latest_by_family.get("hydration")),
        "wearable_risk_labels": risk_labels,
    }


def default_injury_risk_biomarker_context() -> dict[str, object]:
    return {
        "wearable_observation_count": 0,
        "biomarker_risk_count": 0,
        "biomarker_score_penalty": 0,
        "latest_hrv": None,
        "latest_resting_heart_rate": None,
        "latest_recovery_score": None,
        "latest_hydration_score": None,
        "wearable_risk_labels": [],
    }


async def injury_risk_biomechanical_context(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> dict[str, object]:
    rows = list(
        (
            await db.execute(
                select(AthletePerformanceObservation, PerformanceMetricDefinition)
                .join(
                    PerformanceMetricDefinition,
                    PerformanceMetricDefinition.id == AthletePerformanceObservation.metric_definition_id,
                )
                .where(AthletePerformanceObservation.organization_id == organization_id)
                .where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
                .where(
                    AthletePerformanceObservation.source.in_(
                        [MetricSource.VIDEO_ANALYSIS, MetricSource.AGENT_EXTRACTED, MetricSource.COACH_EVALUATION]
                    )
                )
                .where(AthletePerformanceObservation.verification_status != MetricVerificationStatus.REJECTED)
                .order_by(AthletePerformanceObservation.observed_at.desc())
                .limit(80)
            )
        ).all()
    )
    latest_by_family: dict[str, float] = {}
    risk_labels: list[str] = []
    score_penalty = 0
    biomechanical_observation_count = 0
    for observation, metric in rows:
        family = biomechanical_metric_family(metric)
        if family is None:
            continue
        biomechanical_observation_count += 1
        value = float(observation.value)
        latest_by_family.setdefault(family, value)
        marker = biomechanical_risk_marker(family, value, metric.higher_is_better)
        if marker is None:
            continue
        label, penalty = marker
        if label not in risk_labels:
            risk_labels.append(label)
            score_penalty += penalty
    return {
        "biomechanical_observation_count": biomechanical_observation_count,
        "biomechanical_risk_count": len(risk_labels),
        "biomechanical_score_penalty": min(24, score_penalty),
        "latest_movement_quality_score": rounded_latest_biomarker(
            latest_by_family.get("movement_quality")
            or latest_by_family.get("landing_mechanics")
            or latest_by_family.get("gait_quality")
            or latest_by_family.get("cutting_control")
        ),
        "latest_asymmetry_score": rounded_latest_biomarker(latest_by_family.get("asymmetry")),
        "video_risk_labels": risk_labels,
    }


def default_injury_risk_biomechanical_context() -> dict[str, object]:
    return {
        "biomechanical_observation_count": 0,
        "biomechanical_risk_count": 0,
        "biomechanical_score_penalty": 0,
        "latest_movement_quality_score": None,
        "latest_asymmetry_score": None,
        "video_risk_labels": [],
    }


def biomechanical_metric_family(metric: PerformanceMetricDefinition) -> str | None:
    label = f"{metric.code} {metric.name} {metric.description or ''}".lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", label)
    if any(marker in normalized for marker in ("asymmetry", "imbalance", "left_right", "lsi", "symmetry")):
        return "asymmetry"
    if any(marker in normalized for marker in ("landing", "knee_valgus", "valgus", "collapse")):
        return "landing_mechanics"
    if any(marker in normalized for marker in ("movement_quality", "movement_score", "mechanics", "technique_quality")):
        return "movement_quality"
    if any(marker in normalized for marker in ("gait", "stride", "limp")):
        return "gait_quality"
    if any(marker in normalized for marker in ("cutting", "change_direction", "deceleration", "braking")):
        return "cutting_control"
    return None


def biomechanical_risk_marker(family: str, value: float, higher_is_better: bool) -> tuple[str, int] | None:
    if family == "asymmetry":
        if value >= 18:
            return f"high movement asymmetry {value:g}", 10
        if value >= 10:
            return f"elevated movement asymmetry {value:g}", 6
        return None
    if family == "landing_mechanics":
        if not higher_is_better and value >= 15:
            return f"landing mechanics risk score {value:g}", 8
        if higher_is_better and value < 60:
            return f"low landing mechanics score {value:g}", 8 if value < 45 else 5
        return None
    if family in {"movement_quality", "gait_quality", "cutting_control"}:
        if higher_is_better and value < 60:
            label = family.replace("_", " ")
            return f"low {label} {value:g}", 8 if value < 45 else 5
        if not higher_is_better and value >= 15:
            label = family.replace("_", " ")
            return f"high {label} risk {value:g}", 8 if value >= 25 else 5
    return None


def wearable_metric_family(metric: PerformanceMetricDefinition) -> str | None:
    label = f"{metric.code} {metric.name} {metric.description or ''}".lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", label)
    if "hrv" in normalized or "heart_rate_variability" in normalized:
        return "hrv"
    if "resting_heart_rate" in normalized or "resting_hr" in normalized or "resting_pulse" in normalized:
        return "resting_heart_rate"
    if "sleep_hours" in normalized or "sleep_duration" in normalized or "sleep_minutes" in normalized:
        return "sleep_hours"
    if "sleep_quality" in normalized:
        return "sleep_quality"
    if "recovery" in normalized or "readiness" in normalized:
        return "recovery"
    if "hydration" in normalized or "dehydration" in normalized:
        return "hydration"
    if "strain" in normalized or "training_strain" in normalized:
        return "strain"
    if "stress" in normalized:
        return "stress"
    if "temperature" in normalized or "body_temp" in normalized:
        return "temperature"
    return None


def wearable_biomarker_risk_marker(family: str, value: float) -> tuple[str, int] | None:
    if family == "hrv" and value < 45:
        return f"low HRV {value:g}", 8 if value < 35 else 5
    if family == "resting_heart_rate" and value > 90:
        return f"high resting heart rate {value:g}", 8 if value > 100 else 5
    if family == "sleep_hours" and value < 6:
        return f"short sleep {value:g}h", 8 if value < 5 else 5
    if family == "sleep_quality" and value < 60:
        return f"low wearable sleep quality {value:g}", 6
    if family == "recovery" and value < 60:
        return f"low recovery score {value:g}", 8 if value < 45 else 5
    if family == "hydration" and value < 70:
        return f"low hydration score {value:g}", 6
    if family == "strain" and value > 16:
        return f"high strain {value:g}", 8 if value > 19 else 5
    if family == "stress" and value > 70:
        return f"high stress {value:g}", 6
    if family == "temperature" and value >= 37.8:
        return f"elevated body temperature {value:g}C", 10
    return None


def rounded_latest_biomarker(value: float | None) -> float | None:
    return round(value, 1) if value is not None else None


def injury_risk_confidence(
    feedback_count: int,
    open_incident_count: int,
    declining_metric_count: int,
    environmental_risk_count: int = 0,
    biomarker_risk_count: int = 0,
    biomechanical_risk_count: int = 0,
) -> float:
    evidence_bonus = min(0.45, feedback_count * 0.06)
    incident_bonus = 0.12 if open_incident_count else 0.0
    trend_bonus = min(0.15, declining_metric_count * 0.04)
    environment_bonus = min(0.1, environmental_risk_count * 0.03)
    biomarker_bonus = min(0.12, biomarker_risk_count * 0.04)
    biomechanical_bonus = min(0.1, biomechanical_risk_count * 0.04)
    return round(
        min(
            0.95,
            0.35
            + evidence_bonus
            + incident_bonus
            + trend_bonus
            + environment_bonus
            + biomarker_bonus
            + biomechanical_bonus,
        ),
        2,
    )


def injury_risk_recommendation(band: str) -> str:
    if band == "critical":
        return "Pause high-intensity participation and require medical or safeguarding review before the next session."
    if band == "high":
        return "Reduce load, assign coach follow-up, and repeat readiness/soreness checks within 24 hours."
    if band == "watch":
        return "Keep the athlete on modified monitoring and avoid sharp load increases until drivers improve."
    return "Continue normal progression with routine readiness and workload monitoring."


async def injury_risk_alert_recipient_ids(
    db: AsyncSession,
    organization_id: UUID,
    athlete: Person,
) -> set[UUID]:
    manager_rows = (
        await db.execute(
            select(Membership.subject_id)
            .where(Membership.organization_id == organization_id)
            .where(Membership.subject_type == MemberSubjectType.PERSON)
            .where(
                Membership.role.in_(
                    [
                        MembershipRole.OWNER,
                        MembershipRole.ADMIN,
                        MembershipRole.STAFF,
                        MembershipRole.COACH,
                    ]
                )
            )
            .where(Membership.status == "active")
        )
    ).all()
    recipient_ids = {person_id for (person_id,) in manager_rows}
    recipient_ids.add(athlete.id)
    recipient_ids.update(await guardian_person_ids(db, athlete.id))
    return recipient_ids


async def injury_risk_scan_athlete_ids(
    db: AsyncSession,
    organization_id: UUID | None,
    limit: int,
) -> list[UUID]:
    statement = (
        select(AthleteProfile.id)
        .outerjoin(TrainingSessionFeedback, TrainingSessionFeedback.athlete_profile_id == AthleteProfile.id)
        .outerjoin(AthletePerformanceObservation, AthletePerformanceObservation.athlete_profile_id == AthleteProfile.id)
        .group_by(AthleteProfile.id)
        .order_by(
            func.max(TrainingSessionFeedback.recorded_at).desc().nulls_last(),
            func.max(AthletePerformanceObservation.observed_at).desc().nulls_last(),
            AthleteProfile.created_at.desc(),
        )
        .limit(limit)
    )
    if organization_id is not None:
        statement = statement.where(AthleteProfile.organization_id == organization_id)
    return list((await db.scalars(statement)).all())


async def recent_injury_risk_alert_exists(
    db: AsyncSession,
    athlete_person_id: UUID,
    repeat_after_hours: int,
) -> bool:
    sent_after = datetime.now(UTC) - timedelta(hours=repeat_after_hours)
    existing = await db.scalar(
        select(CommunicationMessage.id)
        .where(CommunicationMessage.scope_type == CommunicationScopeType.PERSON)
        .where(CommunicationMessage.scope_id == athlete_person_id)
        .where(CommunicationMessage.message_type == CommunicationMessageType.ALERT)
        .where(CommunicationMessage.subject.ilike("%injury risk%"))
        .where(CommunicationMessage.sent_at.is_not(None))
        .where(CommunicationMessage.sent_at >= sent_after)
        .limit(1)
    )
    return existing is not None


def normalized_injury_risk_alert_channels(
    channels: list[CommunicationChannel] | None,
) -> list[CommunicationChannel]:
    selected = channels or [CommunicationChannel.IN_APP]
    normalized: list[CommunicationChannel] = []
    for channel in selected:
        if channel not in normalized:
            normalized.append(channel)
    return normalized or [CommunicationChannel.IN_APP]


async def create_injury_risk_alert_messages(
    db: AsyncSession,
    organization_id: UUID,
    athlete: Person,
    risk: dict[str, object],
    recipient_ids: set[UUID],
    channels: list[CommunicationChannel],
) -> list[CommunicationMessage]:
    messages: list[CommunicationMessage] = []
    for channel in channels:
        messages.append(
            await create_injury_risk_alert_message_for_channel(
                db,
                organization_id,
                athlete,
                risk,
                recipient_ids,
                channel,
            )
        )
    return messages


async def create_injury_risk_alert_message_for_channel(
    db: AsyncSession,
    organization_id: UUID,
    athlete: Person,
    risk: dict[str, object],
    recipient_ids: set[UUID],
    channel: CommunicationChannel,
) -> CommunicationMessage:
    now = datetime.now(UTC)
    message = CommunicationMessage(
        organization_id=organization_id,
        template_id=None,
        created_by_person_id=None,
        message_type=CommunicationMessageType.ALERT,
        channel=channel,
        scope_type=CommunicationScopeType.PERSON,
        scope_id=athlete.id,
        subject=injury_risk_alert_subject(athlete, risk),
        body=injury_risk_alert_body(athlete, risk),
        urgent=True,
        quiet_hours_override=True,
        scheduled_for=None,
        sent_at=now,
        status="sent",
    )
    db.add(message)
    await db.flush()
    for person_id in sorted(recipient_ids, key=str):
        person = await db.get(Person, person_id)
        if person is None:
            continue
        db.add(
            MessageRecipient(
                message_id=message.id,
                person_id=person.id,
                destination=destination_for_channel(person, channel),
                delivery_status=initial_delivery_status(person, channel),
            )
        )
    return message


def injury_risk_alert_subject(athlete: Person, risk: dict[str, object]) -> str:
    return f"{athlete.display_name} injury risk: {risk['risk_band']} ({risk['score']}/100)"[:240]


def injury_risk_alert_body(athlete: Person, risk: dict[str, object]) -> str:
    lines = [
        f"{athlete.display_name} has a {risk['risk_band']} injury-risk score of {risk['score']}/100.",
        f"Confidence: {int(float(risk['confidence']) * 100)}%. Model policy: {risk['model_policy']}.",
        "",
        "Drivers:",
    ]
    drivers = risk.get("drivers", [])
    if isinstance(drivers, list):
        for driver in drivers[:6]:
            lines.append(f"- {driver}")
    lines.extend(
        [
            "",
            f"Recommendation: {risk['recommendation']}",
            "",
            "Review training load, readiness, medical clearance, and guardian communication before the next high-intensity activity.",
        ]
    )
    return "\n".join(lines)[:8000]


def directional_change(
    latest: float,
    earlier: float | None,
    higher_is_better: bool,
) -> float | None:
    if earlier is None:
        return None
    raw_change = latest - earlier
    return raw_change if higher_is_better else -raw_change


def consistency_index(values: list[float]) -> float:
    if len(values) < 2:
        return 100.0
    average_magnitude = abs(sum(values) / len(values))
    if average_magnitude == 0:
        return 100.0 if all(value == 0 for value in values) else 0.0
    variation = pstdev(values) / average_magnitude
    return round(max(0.0, min(100.0, 100.0 - variation * 100.0)), 1)


def forecast_next_value(
    values: list[float],
    training_adjustment_percent: float = 0.0,
    readiness_score: int | None = None,
    higher_is_better: bool = True,
) -> float | None:
    if len(values) < 2:
        return values[-1] if values else None
    return values[-1] + adjusted_observation_delta(
        values,
        training_adjustment_percent,
        readiness_score,
        higher_is_better,
    )


def normalized_trend_value(value: float, values: list[float], higher_is_better: bool) -> float:
    if not values:
        return 0
    low = min(values)
    high = max(values)
    if high == low:
        return 50
    raw = ((value - low) / (high - low)) * 100
    normalized = raw if higher_is_better else 100 - raw
    return round(max(0, min(100, normalized)), 2)


def trend_direction(change_from_first: float | None, values: list[float]) -> str:
    if len(values) < 2 or change_from_first is None:
        return "insufficient_data"
    average_magnitude = abs(sum(values) / len(values)) or 1.0
    threshold = max(0.01, average_magnitude * 0.03)
    if change_from_first > threshold:
        return "improving"
    if change_from_first < -threshold:
        return "declining"
    return "stable"


def trend_recommendation(
    direction: str,
    metric_name: str,
    unit: str | None,
    latest: float,
    average: float,
    change_from_first: float | None,
) -> str:
    suffix = f" {unit}" if unit else ""
    latest_text = f"{latest:g}{suffix}"
    average_text = f"{average:g}{suffix}"
    if direction == "improving":
        return (
            f"Trend is improving for {metric_name}; keep the current plan and raise the "
            f"target from latest {latest_text}."
        )
    if direction == "declining":
        return (
            f"Trend is declining for {metric_name}; review load, recovery, and technique "
            f"before the next block."
        )
    if direction == "stable":
        return (
            f"{metric_name} is stable around {average_text}; add a focused stimulus if "
            f"the athlete needs another jump."
        )
    if change_from_first is None:
        return f"Capture another {metric_name} result to calculate trend direction."
    return f"Continue collecting {metric_name}; latest value is {latest_text}."


async def latest_metric_value(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
    metric_definition_id: UUID,
) -> float | None:
    observation = await db.scalar(
        select(AthletePerformanceObservation)
        .where(AthletePerformanceObservation.organization_id == organization_id)
        .where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
        .where(AthletePerformanceObservation.metric_definition_id == metric_definition_id)
        .where(AthletePerformanceObservation.verification_status != MetricVerificationStatus.REJECTED)
        .order_by(AthletePerformanceObservation.observed_at.desc())
        .limit(1)
    )
    return observation.value if observation is not None else None


def goal_status(current_value: float | None, target_value: float, direction: str) -> str:
    return "achieved" if goal_met(current_value, target_value, direction) else "active"


def goal_met(current_value: float | None, target_value: float, direction: str) -> bool:
    if current_value is None:
        return False
    if direction == "decrease":
        return current_value <= target_value
    return current_value >= target_value


def badge_code(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return normalized[:100] or "performance_goal"


async def create_award_once(
    db: AsyncSession,
    *,
    organization_id: UUID,
    athlete_profile_id: UUID,
    goal_id: UUID | None,
    metric_definition_id: UUID | None,
    title: str,
    badge_code: str,
    achievement_type: str,
    achieved_value: float | None,
    threshold_value: float | None,
    source_summary: str,
) -> PerformanceAchievementAward | None:
    existing = await db.scalar(
        select(PerformanceAchievementAward).where(
            PerformanceAchievementAward.organization_id == organization_id,
            PerformanceAchievementAward.athlete_profile_id == athlete_profile_id,
            PerformanceAchievementAward.badge_code == badge_code,
        )
    )
    if existing is not None:
        return None
    award = PerformanceAchievementAward(
        organization_id=organization_id,
        athlete_profile_id=athlete_profile_id,
        goal_id=goal_id,
        metric_definition_id=metric_definition_id,
        title=title,
        badge_code=badge_code,
        achievement_type=achievement_type,
        achieved_value=achieved_value,
        threshold_value=threshold_value,
        awarded_at=datetime.now(UTC),
        source_summary=source_summary,
    )
    db.add(award)
    return award


async def create_achievement_notifications(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
    awards: list[PerformanceAchievementAward],
) -> list[CommunicationMessage]:
    if not awards:
        return []
    athlete_profile = await get_athlete_profile(db, athlete_profile_id, organization_id)
    athlete = await db.get(Person, athlete_profile.person_id)
    if athlete is None:
        return []
    recipient_ids = {athlete.id}
    recipient_ids.update(await guardian_person_ids(db, athlete.id))
    if not recipient_ids:
        return []

    subject = achievement_notification_subject(athlete, awards)
    body = achievement_notification_body(athlete, awards)
    message = CommunicationMessage(
        organization_id=organization_id,
        template_id=None,
        created_by_person_id=None,
        message_type=CommunicationMessageType.REPORT,
        channel=CommunicationChannel.IN_APP,
        scope_type=CommunicationScopeType.PERSON,
        scope_id=athlete.id,
        subject=subject,
        body=body,
        urgent=False,
        quiet_hours_override=False,
        scheduled_for=None,
        sent_at=datetime.now(UTC),
        status="sent",
    )
    db.add(message)
    await db.flush()
    for person_id in sorted(recipient_ids, key=str):
        person = await db.get(Person, person_id)
        if person is None:
            continue
        db.add(
            MessageRecipient(
                message_id=message.id,
                person_id=person.id,
                destination=destination_for_channel(person, CommunicationChannel.IN_APP),
                delivery_status=initial_delivery_status(person, CommunicationChannel.IN_APP),
            )
        )
    return [message]


def achievement_notification_subject(
    athlete: Person,
    awards: list[PerformanceAchievementAward],
) -> str:
    if len(awards) == 1:
        return f"{athlete.display_name} earned {awards[0].title}"[:240]
    return f"{athlete.display_name} earned {len(awards)} performance achievements"[:240]


def achievement_notification_body(
    athlete: Person,
    awards: list[PerformanceAchievementAward],
) -> str:
    lines = [
        f"{athlete.display_name} has new AfroLete performance recognition.",
        "",
    ]
    for award in awards:
        value = ""
        if award.achieved_value is not None:
            value = f" ({award.achieved_value:g})"
        lines.append(f"- {award.title}{value}: {award.source_summary}")
    lines.extend(
        [
            "",
            "Open the family or player portal to review goals, badges, and recent performance context.",
        ]
    )
    return "\n".join(lines)[:8000]


async def award_personal_bests(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> list[PerformanceAchievementAward]:
    metrics = await list_metric_definitions(db, organization_id)
    awards: list[PerformanceAchievementAward] = []
    for metric in metrics:
        observations = list(
            (
                await db.scalars(
                    select(AthletePerformanceObservation)
                    .where(AthletePerformanceObservation.organization_id == organization_id)
                    .where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
                    .where(AthletePerformanceObservation.metric_definition_id == metric.id)
                    .where(
                        AthletePerformanceObservation.verification_status
                        != MetricVerificationStatus.REJECTED
                    )
                    .order_by(AthletePerformanceObservation.observed_at)
                )
            ).all()
        )
        if len(observations) < 2:
            continue
        values = [observation.value for observation in observations]
        latest = values[-1]
        best = max(values) if metric.higher_is_better else min(values)
        if latest != best:
            continue
        award = await create_award_once(
            db,
            organization_id=organization_id,
            athlete_profile_id=athlete_profile_id,
            goal_id=None,
            metric_definition_id=metric.id,
            title=f"Personal best: {metric.name}",
            badge_code=f"personal_best_{metric.id}_{latest:g}",
            achievement_type="personal_best",
            achieved_value=latest,
            threshold_value=best,
            source_summary=f"Latest {metric.name} value matched the athlete personal best.",
        )
        if award is not None:
            awards.append(award)
    return awards


def extract_numeric_value(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


def stable_payload_text(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def stable_payload_hash(payload: dict[str, object]) -> str:
    return hashlib.sha256(stable_payload_text(payload).encode()).hexdigest()


def encode_uuid_list(values: list[UUID]) -> str:
    return json.dumps([str(value) for value in values])


def decode_uuid_list(value: str | None) -> list[UUID]:
    if not value:
        return []
    try:
        return [UUID(str(item)) for item in json.loads(value)]
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def encode_string_list(values: list[str]) -> str:
    return json.dumps([value for value in values if value])


def decode_string_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        items = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in items if str(item)]


def decode_scouting_findings(value: str | None) -> list[dict[str, str]]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    findings: list[dict[str, str]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        findings.append(
            {
                "category": str(item.get("category") or "tactical"),
                "title": str(item.get("title") or "Scouting note"),
                "severity": str(item.get("severity") or "medium"),
                "evidence": str(item.get("evidence") or ""),
                "recommendation": str(item.get("recommendation") or ""),
            }
        )
    return findings


def deterministic_opposition_scouting_analysis(
    *,
    opponent_name: str,
    sport: str,
    formation: str | None,
    match_context: str | None,
    analysis_focus: str | None,
    evidence_text: str | None,
    tracking_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    corpus = " ".join(
        part.lower()
        for part in [opponent_name, sport, formation, match_context, analysis_focus, evidence_text]
        if part
    )
    formation_detected = formation or detected_formation(corpus)
    weaknesses = [
        scouting_finding(
            "weakness",
            "Space behind wide defenders",
            "high" if any(word in corpus for word in ["high press", "overlap", "fullback"]) else "medium",
            f"{opponent_name} can be stretched when their wide players step high.",
            "Use early diagonal switches and blind-side winger runs after drawing the press.",
        ),
        scouting_finding(
            "weakness",
            "Second-ball exposure",
            "medium",
            "Their defensive midfield line leaves recoverable space after aerial or cleared balls.",
            "Station a late-arriving midfielder at the top of the box and recycle quickly.",
        ),
    ]
    if any(word in corpus for word in ["set piece", "corner", "free kick", "zonal"]):
        weaknesses.append(
            scouting_finding(
                "set_piece",
                "Set-piece marking confusion",
                "high",
                "Evidence mentions set-piece or zonal defending pressure points.",
                "Stack near-post runners, screen the central marker, and attack the far-post second phase.",
            )
        )
    if any(word in corpus for word in ["fatigue", "late", "tired", "drop off"]):
        weaknesses.append(
            scouting_finding(
                "conditioning",
                "Late-game intensity drop",
                "medium",
                "Evidence suggests performance drops after sustained pressure.",
                "Raise tempo after halftime with fresh runners and repeated wide switches.",
            )
        )
    threats = [
        scouting_finding(
            "threat",
            "Fast attacking transition",
            "high" if any(word in corpus for word in ["counter", "transition", "pace"]) else "medium",
            f"{opponent_name} can break quickly when possession turns over.",
            "Keep rest-defense coverage with two staggered players behind the ball.",
        ),
        scouting_finding(
            "threat",
            "Pressing trigger after back passes",
            "medium",
            "The scouting focus includes pressing and tactical pressure cues.",
            "Prepare a third-player outlet and avoid square passes into the first pressing lane.",
        ),
    ]
    recommendations = [
        scouting_finding(
            "game_plan",
            "Build through the weak-side channel",
            "high",
            f"Detected shape: {formation_detected}. Wide recovery is the most exploitable pattern.",
            "Overload one side, switch early, and isolate the far-side winger against the recovering fullback.",
        ),
        scouting_finding(
            "game_plan",
            "Protect central turnovers",
            "high",
            "Transition threat appears in the tactical profile.",
            "Use a conservative six/eight rest-defense pair whenever both fullbacks advance.",
        ),
        scouting_finding(
            "training",
            "Rehearse first 15-minute pressure escape",
            "medium",
            "Opening pressure is likely if the opponent presses from the front.",
            "Run rondo-to-breakout patterns and scripted goalkeeper release options before match day.",
        ),
    ]
    set_pieces = [
        scouting_finding(
            "set_piece",
            "Near-post decoy and far-post attack",
            "medium",
            "Default set-piece recommendation generated from opponent scouting profile.",
            "Send the strongest aerial player to the back post while a decoy run screens the near-post zone.",
        )
    ]
    tracking_notes = scouting_findings_from_match_tracking(tracking_summary, opponent_name=opponent_name)
    weaknesses.extend(tracking_notes["weaknesses"])
    threats.extend(tracking_notes["threats"])
    recommendations.extend(tracking_notes["recommendations"])
    set_pieces.extend(tracking_notes["set_pieces"])
    confidence = 0.74
    if evidence_text and len(evidence_text) > 80:
        confidence += 0.08
    if formation:
        confidence += 0.06
    if tracking_summary is not None:
        confidence += 0.06
    confidence = min(confidence, 0.92)
    tracking_summary_sentence = tracking_notes.get("summary_sentence") or ""
    return {
        "formation_detected": formation_detected,
        "tactical_summary": (
            f"{opponent_name} profiles as a {formation_detected} opponent with transition threat, "
            "recoverable weak-side space, and set-piece second-phase risk. The match plan should "
            f"pull pressure to one side, switch quickly, and keep rest-defense protection central.{tracking_summary_sentence}"
        ),
        "weaknesses": weaknesses,
        "threats": threats,
        "recommendations": recommendations,
        "set_pieces": set_pieces,
        "confidence": round(confidence, 2),
    }


def scouting_findings_from_match_tracking(
    tracking: dict[str, object] | None,
    *,
    opponent_name: str,
) -> dict[str, object]:
    if tracking is None:
        return {
            "weaknesses": [],
            "threats": [],
            "recommendations": [],
            "set_pieces": [],
            "summary_sentence": "",
        }
    ball_metrics = tracking.get("ball_tracking_metrics") if isinstance(tracking.get("ball_tracking_metrics"), dict) else {}
    chance_metrics = tracking.get("chance_creation_metrics") if isinstance(tracking.get("chance_creation_metrics"), dict) else {}
    possession = [item for item in tracking.get("possession_estimates", []) if isinstance(item, dict)]
    pass_types = [item for item in tracking.get("pass_type_metrics", []) if isinstance(item, dict)]
    team_phase = [item for item in tracking.get("team_phase_metrics", []) if isinstance(item, dict)]
    team_shape = [item for item in tracking.get("team_shape_metrics", []) if isinstance(item, dict)]
    pressure_events = [item for item in tracking.get("pressure_events", []) if isinstance(item, dict)]
    weaknesses: list[dict[str, str]] = []
    threats: list[dict[str, str]] = []
    recommendations: list[dict[str, str]] = []
    set_pieces: list[dict[str, str]] = []
    if possession:
        leader = possession[0]
        threats.append(
            scouting_finding(
                "tracking_evidence",
                "Possession control profile",
                "high" if float(leader.get("possession_percent") or 0.0) >= 58 else "medium",
                f"Tracking estimates {leader.get('team_label', 'opponent')} held {leader.get('possession_percent', 0)}% possession across {leader.get('sample_count', 0)} ball samples.",
                "Prepare compact mid-block spells and rehearse transition outlets for long periods without the ball.",
            )
        )
    if int(ball_metrics.get("pass_attempt_count") or 0) > 0:
        recommendations.append(
            scouting_finding(
                "passing_profile",
                "Pass accuracy by risk type",
                "high" if float(ball_metrics.get("pass_accuracy_percent") or 0.0) < 65 else "medium",
                f"Tracking produced {ball_metrics.get('pass_count', 0)}/{ball_metrics.get('pass_attempt_count', 0)} completed pass attempts ({ball_metrics.get('pass_accuracy_percent', 0)}%).",
                "Force the lowest-accuracy pass type and press immediately after backward or square trigger passes.",
            )
        )
    if pass_types:
        risky_pass = min(pass_types, key=lambda item: float(item.get("accuracy_percent") or 0.0))
        weaknesses.append(
            scouting_finding(
                "passing_weakness",
                f"{str(risky_pass.get('pass_type') or 'pass').replace('_', ' ').title()} vulnerability",
                "high" if float(risky_pass.get("accuracy_percent") or 0.0) < 50 else "medium",
                f"{risky_pass.get('team_label', 'Opponent')} completed {risky_pass.get('completed_count', 0)}/{risky_pass.get('attempt_count', 0)} {str(risky_pass.get('pass_type') or 'pass').replace('_', ' ')} attempts.",
                "Set traps that invite this pass, then attack the second ball and nearest counter-press lane.",
            )
        )
    if int(ball_metrics.get("interception_count") or 0) + int(ball_metrics.get("tackle_count") or 0) > 0:
        threats.append(
            scouting_finding(
                "defensive_profile",
                "Ball-win pressure threat",
                "high",
                f"Tracking labelled {ball_metrics.get('interception_count', 0)} interceptions and {ball_metrics.get('tackle_count', 0)} tackles from turnovers.",
                "Coach first-touch security, body shape before receiving, and immediate support angles in contested zones.",
            )
        )
    if int(ball_metrics.get("shot_count") or 0) > 0:
        weaknesses.append(
            scouting_finding(
                "chance_profile",
                "Shot quality concession",
                "high" if float(ball_metrics.get("expected_goals") or 0.0) >= 0.5 else "medium",
                f"Ball tracking derived {ball_metrics.get('shot_count', 0)} shot(s), {ball_metrics.get('shot_on_target_count', 0)} on target, and {ball_metrics.get('expected_goals', 0)} xG.",
                "Use cutback and central final-third actions if the opponent allows similar shot locations.",
            )
        )
    compact_shape = next((item for item in team_shape if str(item.get("shape_hint") or "") == "stretched_shape"), None)
    if compact_shape is not None:
        weaknesses.append(
            scouting_finding(
                "shape_weakness",
                "Stretched team shape",
                "medium",
                f"{compact_shape.get('team_label', opponent_name)} averaged {compact_shape.get('average_width_percent', 0)}% width and {compact_shape.get('average_depth_percent', 0)}% depth.",
                "Switch quickly after circulation and attack the gaps between stretched lines.",
            )
        )
    active_phase = next((item for item in team_phase if int(item.get("pressure_event_count") or 0) > 0), None)
    if active_phase is not None or pressure_events:
        threats.append(
            scouting_finding(
                "pressing_profile",
                "Pressing trigger evidence",
                "medium",
                f"Tracking captured {len(pressure_events)} pressure event(s) and {active_phase.get('pressure_event_count', 0) if active_phase else 0} team-phase pressure count(s).",
                "Use third-player outlets and diagonal support before receiving under pressure.",
            )
        )
    if int(chance_metrics.get("key_pass_count") or 0) > 0:
        recommendations.append(
            scouting_finding(
                "match_plan",
                "Block the key-pass lane",
                "high",
                f"Tracking found {chance_metrics.get('key_pass_count', 0)} key pass(es) leading to {chance_metrics.get('expected_goals', 0)} xG.",
                "Assign a screening midfielder to deny the most productive final-action passing lane.",
            )
        )
    if int(ball_metrics.get("shot_count") or 0) > 0 and int(ball_metrics.get("shot_on_target_count") or 0) == 0:
        set_pieces.append(
            scouting_finding(
                "set_piece",
                "Low shot accuracy from dead-ball-like deliveries",
                "low",
                "Tracking found shot attempts without on-target outcomes.",
                "Concede low-value wide deliveries rather than central free shots.",
            )
        )
    summary_sentence = (
        f" Tracking evidence adds {ball_metrics.get('pass_count', 0)}/{ball_metrics.get('pass_attempt_count', 0)} passing, "
        f"{ball_metrics.get('turnover_count', 0)} turnovers, and {ball_metrics.get('expected_goals', 0)} xG to the scouting model."
    )
    return {
        "weaknesses": weaknesses,
        "threats": threats,
        "recommendations": recommendations,
        "set_pieces": set_pieces,
        "summary_sentence": summary_sentence,
    }


def detected_formation(corpus: str) -> str:
    for candidate in ["4-3-3", "4-2-3-1", "4-4-2", "3-5-2", "3-4-3", "5-3-2"]:
        if candidate in corpus:
            return candidate
    if "back three" in corpus or "three center" in corpus:
        return "3-5-2"
    if "double pivot" in corpus:
        return "4-2-3-1"
    return "4-3-3"


def scouting_finding(
    category: str,
    title: str,
    severity: str,
    evidence: str,
    recommendation: str,
) -> dict[str, str]:
    return {
        "category": category,
        "title": title,
        "severity": severity,
        "evidence": evidence,
        "recommendation": recommendation,
    }


def video_slow_motion_rates() -> list[float]:
    return [0.125, 0.25, 0.5, 0.75, 1.0]


def decode_performance_upload_content(content_base64: str) -> bytes:
    encoded = content_base64.split(",", 1)[1] if "," in content_base64 else content_base64
    try:
        return b64decode(encoded, validate=True)
    except (Base64Error, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid video encoding") from exc


def safe_performance_upload_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip(".-")
    return cleaned[:180] or "performance-video.mp4"


async def get_performance_video_asset(
    db: AsyncSession,
    video_asset_id: UUID,
) -> PerformanceVideoAsset:
    video_asset = await db.get(PerformanceVideoAsset, video_asset_id)
    if video_asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Performance video not found")
    return video_asset


async def get_opposition_scouting_video_asset(
    db: AsyncSession,
    video_asset_id: UUID,
) -> OppositionScoutingVideoAsset:
    video_asset = await db.get(OppositionScoutingVideoAsset, video_asset_id)
    if video_asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scouting video not found")
    return video_asset


async def get_match_pitch_calibration(
    db: AsyncSession,
    calibration_id: UUID,
    organization_id: UUID,
    video_asset_id: UUID,
) -> PerformanceMatchPitchCalibration:
    calibration = await db.get(PerformanceMatchPitchCalibration, calibration_id)
    if (
        calibration is None
        or calibration.organization_id != organization_id
        or calibration.video_asset_id != video_asset_id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match pitch calibration not found")
    return calibration


async def ensure_scouting_scope(
    db: AsyncSession,
    organization_id: UUID,
    team_id: UUID | None,
    competition_id: UUID | None,
    event_id: UUID | None,
) -> None:
    if team_id is not None:
        team = await db.get(Team, team_id)
        if team is None or team.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if competition_id is not None:
        competition = await db.get(Competition, competition_id)
        if competition is None or competition.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found")
    if event_id is not None:
        event = await db.get(Event, event_id)
        if event is None or event.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")


def performance_video_object_key(video_asset: PerformanceVideoAsset, settings: Settings) -> str:
    if video_asset.storage_path.startswith("s3://"):
        prefix = f"s3://{settings.object_storage_bucket}/"
        if video_asset.storage_path.startswith(prefix):
            return video_asset.storage_path[len(prefix):]
    local_root = Path(settings.performance_video_file_dir)
    storage_path = Path(video_asset.storage_path)
    try:
        return storage_path.relative_to(local_root).as_posix()
    except ValueError:
        return (
            Path(str(video_asset.organization_id))
            / str(video_asset.athlete_profile_id)
            / Path(video_asset.storage_path).name
        ).as_posix()


def opposition_scouting_video_object_key(video_asset: OppositionScoutingVideoAsset, settings: Settings) -> str:
    if video_asset.storage_path.startswith("s3://"):
        prefix = f"s3://{settings.object_storage_bucket}/"
        if video_asset.storage_path.startswith(prefix):
            return video_asset.storage_path[len(prefix):]
    local_root = Path(settings.performance_video_file_dir)
    storage_path = Path(video_asset.storage_path)
    try:
        return storage_path.relative_to(local_root).as_posix()
    except ValueError:
        return (Path(str(video_asset.organization_id)) / "scouting" / Path(video_asset.storage_path).name).as_posix()


def highlight_reel_export_object_key(
    organization_id: UUID,
    highlight_reel_id: UUID,
    export_id: UUID,
    filename: str,
) -> str:
    return (
        Path(str(organization_id))
        / "highlight-exports"
        / str(highlight_reel_id)
        / f"{export_id}-{safe_highlight_export_filename(filename)}"
    ).as_posix()


def performance_highlight_reel_export_object_key(
    export: PerformanceHighlightReelExport,
    settings: Settings,
) -> str:
    if export.storage_path.startswith("s3://"):
        prefix = f"s3://{settings.object_storage_bucket}/"
        if export.storage_path.startswith(prefix):
            return export.storage_path[len(prefix):]
    local_root = Path(settings.performance_highlight_export_dir)
    storage_path = Path(export.storage_path)
    try:
        return storage_path.relative_to(local_root).as_posix()
    except ValueError:
        return highlight_reel_export_object_key(
            export.organization_id,
            export.highlight_reel_id,
            export.id,
            export.filename,
        )


def match_analysis_report_object_key(
    organization_id: UUID,
    tracking_run_id: UUID,
    report_id: UUID,
    filename: str,
) -> str:
    return (
        Path(str(organization_id))
        / "match-reports"
        / str(tracking_run_id)
        / f"{report_id}-{safe_highlight_export_filename(filename)}"
    ).as_posix()


def performance_match_analysis_report_object_key(
    report: PerformanceMatchAnalysisReport,
    settings: Settings,
) -> str:
    if report.storage_path.startswith("s3://"):
        prefix = f"s3://{settings.object_storage_bucket}/"
        if report.storage_path.startswith(prefix):
            return report.storage_path[len(prefix):]
    local_root = Path(settings.performance_match_report_dir)
    storage_path = Path(report.storage_path)
    try:
        return storage_path.relative_to(local_root).as_posix()
    except ValueError:
        return match_analysis_report_object_key(
            report.organization_id,
            report.tracking_run_id,
            report.id,
            match_analysis_report_download_filename(report),
        )


def match_analysis_report_download_filename(report: PerformanceMatchAnalysisReport) -> str:
    return f"{safe_highlight_export_filename(report.title)}-{report.id}.md"


def build_match_analysis_report_artifact(
    tracking: dict[str, object],
    video_asset: OppositionScoutingVideoAsset,
    *,
    audience: str,
    report_scope: str,
    title: str | None,
    include_player_cards: bool,
    include_tactical_shape: bool,
    notes: str | None,
) -> dict[str, object]:
    player_metrics = [item for item in tracking.get("player_metrics", []) if isinstance(item, dict)]
    player_cards = sorted(
        [
            {
                "track_id": str(metric.get("track_id") or "unknown"),
                "player_label": metric.get("player_label"),
                "team_label": metric.get("team_label"),
                "jersey_number": metric.get("jersey_number"),
                "distance_m": round(float(metric.get("distance_m") or 0.0), 2),
                "high_speed_distance_m": round(float(metric.get("high_speed_distance_m") or 0.0), 2),
                "max_speed_mps": round(float(metric.get("max_speed_mps") or 0.0), 3),
                "sprint_count": int(metric.get("sprint_count") or 0),
                "work_rate_m_per_min": round(float(metric.get("work_rate_m_per_min") or 0.0), 2),
                "pressure_applied_count": int(metric.get("pressure_applied_count") or 0),
                "pressure_received_count": int(metric.get("pressure_received_count") or 0),
                "off_ball_run_count": int(metric.get("off_ball_run_count") or 0),
                "territorial_advance_count": int(metric.get("territorial_advance_count") or 0),
                "pass_completed_count": int(metric.get("pass_completed_count") or 0),
                "pass_received_count": int(metric.get("pass_received_count") or 0),
                "pass_attempt_count": int(metric.get("pass_attempt_count") or 0),
                "pass_accuracy_percent": round(float(metric.get("pass_accuracy_percent") or 0.0), 2),
                "turnover_involved_count": int(metric.get("turnover_involved_count") or 0),
                "interception_count": int(metric.get("interception_count") or 0),
                "tackle_count": int(metric.get("tackle_count") or 0),
                "ball_carry_m": round(float(metric.get("ball_carry_m") or 0.0), 2),
                "ball_possession_sample_count": int(metric.get("ball_possession_sample_count") or 0),
                "shot_count": int(metric.get("shot_count") or 0),
                "shot_on_target_count": int(metric.get("shot_on_target_count") or 0),
                "expected_goals": round(float(metric.get("expected_goals") or 0.0), 3),
                "key_pass_count": int(metric.get("key_pass_count") or 0),
                "expected_assists": round(float(metric.get("expected_assists") or 0.0), 3),
                "average_nearest_opponent_m": metric.get("average_nearest_opponent_m"),
                "dominant_zone": metric.get("dominant_zone") or "unknown",
                "tracking_quality_score": round(float(metric.get("tracking_quality_score") or 0.0), 3),
                "coaching_flags": [str(flag) for flag in (metric.get("coaching_flags") or [])],
            }
            for metric in player_metrics
        ],
        key=lambda card: (
            float(card["high_speed_distance_m"]),
            float(card["distance_m"]),
            float(card["max_speed_mps"]),
        ),
        reverse=True,
    )[:8] if include_player_cards else []
    team_shape = [
        item for item in tracking.get("team_shape_metrics", []) if isinstance(item, dict)
    ] if include_tactical_shape else []
    team_phase = [item for item in tracking.get("team_phase_metrics", []) if isinstance(item, dict)]
    pressure_events = [item for item in tracking.get("pressure_events", []) if isinstance(item, dict)]
    possession_estimates = [item for item in tracking.get("possession_estimates", []) if isinstance(item, dict)]
    ball_action_events = [item for item in tracking.get("ball_action_events", []) if isinstance(item, dict)]
    shot_events = [item for item in tracking.get("shot_events", []) if isinstance(item, dict)]
    pass_network = [item for item in tracking.get("pass_network", []) if isinstance(item, dict)]
    pass_type_metrics = [item for item in tracking.get("pass_type_metrics", []) if isinstance(item, dict)]
    defensive_action_events = [item for item in tracking.get("defensive_action_events", []) if isinstance(item, dict)]
    chance_creation_metrics = (
        tracking.get("chance_creation_metrics") if isinstance(tracking.get("chance_creation_metrics"), dict) else {}
    )
    ball_tracking_metrics = tracking.get("ball_tracking_metrics") if isinstance(tracking.get("ball_tracking_metrics"), dict) else {}
    summary = {
        "video_asset_id": str(video_asset.id),
        "filename": video_asset.filename,
        "opponent_name": video_asset.opponent_name,
        "sport": video_asset.sport,
        "tracking_run_id": str(tracking.get("id")),
        "status": tracking.get("status"),
        "source_provider": tracking.get("source_provider"),
        "readiness_level": tracking.get("readiness_level"),
        "sample_count": int(tracking.get("sample_count") or 0),
        "player_count": int(tracking.get("player_count") or 0),
        "total_distance_m": round(float(tracking.get("total_distance_m") or 0.0), 2),
        "high_speed_distance_m": round(float(tracking.get("high_speed_distance_m") or 0.0), 2),
        "max_speed_mps": round(float(tracking.get("max_speed_mps") or 0.0), 3),
        "sprint_count": int(tracking.get("sprint_count") or 0),
        "tracking_quality_score": round(float(tracking.get("tracking_quality_score") or 0.0), 3),
        "identity_continuity_score": round(float(tracking.get("identity_continuity_score") or 0.0), 3),
        "calibration_quality_score": round(float(tracking.get("calibration_quality_score") or 0.0), 3),
        "pressure_event_count": len(pressure_events),
        "pass_count": int(ball_tracking_metrics.get("pass_count") or 0),
        "pass_attempt_count": int(ball_tracking_metrics.get("pass_attempt_count") or 0),
        "pass_accuracy_percent": round(float(ball_tracking_metrics.get("pass_accuracy_percent") or 0.0), 2),
        "turnover_count": int(ball_tracking_metrics.get("turnover_count") or 0),
        "interception_count": int(ball_tracking_metrics.get("interception_count") or 0),
        "tackle_count": int(ball_tracking_metrics.get("tackle_count") or 0),
        "shot_count": int(ball_tracking_metrics.get("shot_count") or 0),
        "shot_on_target_count": int(ball_tracking_metrics.get("shot_on_target_count") or 0),
        "expected_goals": round(float(ball_tracking_metrics.get("expected_goals") or 0.0), 3),
    }
    recommendations = match_analysis_report_recommendations(tracking, player_cards, team_shape, team_phase)
    report_title = title.strip() if title and title.strip() else f"{video_asset.opponent_name} match analysis"
    content = match_analysis_report_markdown(
        title=report_title,
        audience=audience,
        report_scope=report_scope,
        summary=summary,
        recommendations=recommendations,
        player_cards=player_cards,
        team_shape=team_shape,
        team_phase=team_phase,
        pressure_events=pressure_events,
        possession_estimates=possession_estimates,
        ball_action_events=ball_action_events,
        shot_events=shot_events,
        pass_network=pass_network,
        pass_type_metrics=pass_type_metrics,
        defensive_action_events=defensive_action_events,
        chance_creation_metrics=chance_creation_metrics,
        ball_tracking_metrics=ball_tracking_metrics,
        quality_warnings=[str(item) for item in (tracking.get("quality_warnings") or [])],
        notes=notes,
    ).encode()
    return {
        "title": report_title,
        "filename": f"{safe_highlight_export_filename(report_title)}.md",
        "content_type": "text/markdown; charset=utf-8",
        "content": content,
        "model_policy": "afrolete-match-analysis-report-v1",
        "summary": summary,
        "player_cards": player_cards,
        "team_shape": team_shape,
        "recommendations": recommendations,
    }


def match_analysis_report_recommendations(
    tracking: dict[str, object],
    player_cards: list[dict[str, object]],
    team_shape: list[dict[str, object]],
    team_phase: list[dict[str, object]],
) -> list[str]:
    recommendations: list[str] = []
    recommendations.extend(str(item) for item in (tracking.get("coaching_guidance") or []) if str(item))
    recommendations.extend(str(item) for item in (tracking.get("tactical_guidance") or []) if str(item))
    for warning in tracking.get("quality_warnings") or []:
        recommendations.append(f"Data quality: {warning}")
    if player_cards:
        top_load = player_cards[0]
        recommendations.append(
            "Review recovery and substitution plans for "
            f"{top_load.get('player_label') or top_load.get('track_id')} after "
            f"{round(float(top_load.get('high_speed_distance_m') or 0))}m high-speed work."
        )
    stretched = [
        shape for shape in team_shape
        if str(shape.get("shape_hint") or "") in {"stretched_shape", "vertical_stagger", "wide_flat_line"}
    ]
    if stretched:
        recommendations.append("Use video review to connect tactical shape changes with pressing and recovery cues.")
    active_press = [phase for phase in team_phase if str(phase.get("phase_hint") or "") == "active_pressing"]
    if active_press:
        recommendations.append("Review whether pressure events were backed by cover shadows and second-ball support.")
    ball_metrics = tracking.get("ball_tracking_metrics") if isinstance(tracking.get("ball_tracking_metrics"), dict) else {}
    if int(ball_metrics.get("turnover_count") or 0) > 0:
        recommendations.append("Review turnover clips to identify first-touch, scanning, and support-angle breakdowns.")
    if int(ball_metrics.get("pass_count") or 0) > 0:
        recommendations.append("Use detected pass chains to compare intended support patterns with actual movement.")
    if int(ball_metrics.get("shot_count") or 0) > 0:
        recommendations.append("Review shot clips against xG estimates to coach shot selection and final-action quality.")
    if int(ball_metrics.get("pass_attempt_count") or 0) > 0:
        recommendations.append("Use pass-type accuracy to separate technical execution problems from risky decision-making.")
    if int(ball_metrics.get("interception_count") or 0) > 0:
        recommendations.append("Review interceptions and tackles to coach scanning, body shape, and counter-press reactions.")
    if not recommendations:
        recommendations.append("Capture a calibrated tracking run before issuing individualized player guidance.")
    return list(dict.fromkeys(recommendations))[:12]


def match_analysis_report_markdown(
    *,
    title: str,
    audience: str,
    report_scope: str,
    summary: dict[str, object],
    recommendations: list[str],
    player_cards: list[dict[str, object]],
    team_shape: list[dict[str, object]],
    team_phase: list[dict[str, object]],
    pressure_events: list[dict[str, object]],
    possession_estimates: list[dict[str, object]],
    ball_action_events: list[dict[str, object]],
    shot_events: list[dict[str, object]],
    pass_network: list[dict[str, object]],
    pass_type_metrics: list[dict[str, object]],
    defensive_action_events: list[dict[str, object]],
    chance_creation_metrics: dict[str, object],
    ball_tracking_metrics: dict[str, object],
    quality_warnings: list[str],
    notes: str | None,
) -> str:
    lines = [
        f"# {title}",
        "",
        f"Audience: {audience.strip().lower()}",
        f"Scope: {report_scope.strip().lower()}",
        f"Video: {summary['filename']}",
        f"Opponent: {summary['opponent_name']}",
        f"Readiness: {str(summary['readiness_level']).replace('_', ' ')}",
        "",
        "## Match Load Summary",
        f"- Players tracked: {summary['player_count']}",
        f"- Samples processed: {summary['sample_count']}",
        f"- Total distance: {summary['total_distance_m']}m",
        f"- High-speed distance: {summary['high_speed_distance_m']}m",
        f"- Max speed: {summary['max_speed_mps']} m/s",
        f"- Sprint count: {summary['sprint_count']}",
        f"- Pressure events: {summary['pressure_event_count']}",
        f"- Passes detected: {summary['pass_count']} / {summary['pass_attempt_count']} attempts ({summary['pass_accuracy_percent']}%)",
        f"- Turnovers detected: {summary['turnover_count']}",
        f"- Defensive ball wins: {summary['interception_count']} interceptions, {summary['tackle_count']} tackles",
        f"- Shots detected: {summary['shot_count']}",
        f"- Expected goals: {summary['expected_goals']}",
        f"- Tracking quality: {round(float(summary['tracking_quality_score']) * 100)}%",
        f"- Identity continuity: {round(float(summary['identity_continuity_score']) * 100)}%",
        "",
        "## Coaching Guidance",
    ]
    lines.extend(f"- {item}" for item in recommendations)
    lines.extend(["", "## Player Metrics"])
    if player_cards:
        for card in player_cards:
            lines.extend(
                [
                    f"### {card.get('player_label') or card.get('track_id')}",
                    f"- Team: {card.get('team_label') or 'unassigned'}"
                    + (f" | Jersey: {card.get('jersey_number')}" if card.get("jersey_number") else ""),
                    f"- Distance: {card['distance_m']}m | High-speed: {card['high_speed_distance_m']}m",
                    f"- Max speed: {card['max_speed_mps']} m/s | Sprints: {card['sprint_count']}",
                    f"- Pressure: +{card['pressure_applied_count']} applied / {card['pressure_received_count']} received | Off-ball runs: {card['off_ball_run_count']}",
                    f"- Ball actions: {card['pass_completed_count']}/{card['pass_attempt_count']} pass(es), {card['pass_accuracy_percent']}% accuracy, {card['pass_received_count']} received, {card['turnover_involved_count']} turnover involvement(s), {card['interception_count']} interception(s), {card['tackle_count']} tackle(s), {card['ball_carry_m']}m carried",
                    f"- Chance creation: {card['shot_count']} shot(s), {card['shot_on_target_count']} on target, {card['expected_goals']} xG, {card['key_pass_count']} key pass(es)",
                    f"- Work rate: {card['work_rate_m_per_min']} m/min | Dominant zone: {str(card['dominant_zone']).replace('_', ' ')}",
                    f"- Guidance: {(card.get('coaching_flags') or ['Review video context before coaching.'])[0]}",
                ]
            )
    else:
        lines.append("- Player cards were not included in this report.")
    lines.extend(["", "## Tactical Shape"])
    if team_shape:
        for shape in team_shape:
            lines.append(
                "- "
                f"{shape.get('team_label', 'Team')}: {str(shape.get('shape_hint', 'shape')).replace('_', ' ')}; "
                f"width {shape.get('average_width_percent', 0)}%, "
                f"depth {shape.get('average_depth_percent', 0)}%, "
                f"compactness {shape.get('average_compactness_score', 0)}."
            )
    else:
        lines.append("- Tactical shape was not included in this report.")
    lines.extend(["", "## Team Phase And Pressure"])
    if team_phase:
        for phase in team_phase:
            lines.append(
                "- "
                f"{phase.get('team_label', 'Team')}: {str(phase.get('phase_hint', 'phase')).replace('_', ' ')}; "
                f"{phase.get('pressure_event_count', 0)} pressure event(s), "
                f"{phase.get('off_ball_run_count', 0)} off-ball run(s), "
                f"{phase.get('territorial_advance_count', 0)} territorial advance(s)."
            )
    else:
        lines.append("- Team phase metrics were not available.")
    if pressure_events:
        lines.append(f"- First pressure cue: {pressure_events[0].get('presser_track_id')} closed {pressure_events[0].get('receiver_track_id')} at {pressure_events[0].get('distance_m')}m.")
    lines.extend(["", "## Possession And Ball Actions"])
    if possession_estimates:
        for estimate in possession_estimates:
            lines.append(
                f"- {estimate.get('team_label', 'Team')}: {estimate.get('possession_percent', 0)}% estimated possession from {estimate.get('sample_count', 0)} ball sample(s)."
            )
    else:
        lines.append("- Ball tracking was not available for possession estimation.")
    if ball_tracking_metrics:
        lines.append(
            f"- Ball distance {ball_tracking_metrics.get('ball_distance_m', 0)}m; max ball speed {ball_tracking_metrics.get('max_ball_speed_mps', 0)} m/s."
        )
    if ball_action_events:
        first_action = ball_action_events[0]
        lines.append(
            f"- First ball action: {first_action.get('event_type')} from {first_action.get('from_track_id')} to {first_action.get('to_track_id')} at {first_action.get('timestamp_seconds')}s."
        )
    if shot_events:
        first_shot = shot_events[0]
        lines.append(
            f"- First shot: {first_shot.get('shooter_track_id')} generated {first_shot.get('expected_goals', 0)} xG toward the {first_shot.get('target_goal', 'goal')} goal."
        )
    if pass_network:
        first_link = pass_network[0]
        lines.append(
            f"- Leading pass link: {first_link.get('from_track_id')} to {first_link.get('to_track_id')} completed {first_link.get('pass_count', 0)} pass(es)."
        )
    if pass_type_metrics:
        first_pass_type = pass_type_metrics[0]
        lines.append(
            f"- Pass-type accuracy: {first_pass_type.get('team_label')} {first_pass_type.get('pass_type')} {first_pass_type.get('completed_count', 0)}/{first_pass_type.get('attempt_count', 0)} ({first_pass_type.get('accuracy_percent', 0)}%)."
        )
    if defensive_action_events:
        first_defense = defensive_action_events[0]
        lines.append(
            f"- First defensive action: {first_defense.get('defensive_action_type')} by {first_defense.get('to_track_id')} after {first_defense.get('from_track_id')} lost possession."
        )
    if chance_creation_metrics:
        lines.append(
            f"- Chance quality: {chance_creation_metrics.get('expected_goals', 0)} xG from {chance_creation_metrics.get('shot_count', 0)} shot(s), {chance_creation_metrics.get('key_pass_count', 0)} key pass(es)."
        )
    lines.extend(["", "## Data Quality"])
    if quality_warnings:
        lines.extend(f"- {warning}" for warning in quality_warnings)
    else:
        lines.append("- Tracking quality is adequate for coach review.")
    if notes:
        lines.extend(["", "## Coach Notes", notes.strip()])
    lines.extend(["", f"Generated: {datetime.now(UTC).isoformat()}"])
    return "\n".join(lines)


def match_pitch_calibration_read(calibration: PerformanceMatchPitchCalibration) -> dict[str, object]:
    return {
        "id": calibration.id,
        "organization_id": calibration.organization_id,
        "video_asset_id": calibration.video_asset_id,
        "created_by_person_id": calibration.created_by_person_id,
        "name": calibration.name,
        "calibration_method": calibration.calibration_method,
        "pitch_length_m": calibration.pitch_length_m,
        "pitch_width_m": calibration.pitch_width_m,
        "quality_score": calibration.quality_score,
        "points": decode_match_pitch_calibration_points(calibration.points_json),
        "transform": decode_match_pitch_calibration_transform(calibration.transform_json),
        "status": calibration.status,
        "notes": calibration.notes,
        "created_at": calibration.created_at,
    }


def decode_match_pitch_calibration_points(value: str) -> list[dict[str, object]]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def decode_match_pitch_calibration_transform(value: str) -> dict[str, float | str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {"method": "linear_percent_to_pitch", "quality_score": 0.0}
    return parsed if isinstance(parsed, dict) else {"method": "linear_percent_to_pitch", "quality_score": 0.0}


def match_pitch_calibration_transform(
    points: list[dict[str, object]],
    pitch_length_m: float,
    pitch_width_m: float,
) -> dict[str, float | str]:
    perspective = match_pitch_perspective_transform(points, pitch_length_m, pitch_width_m)
    if perspective is not None:
        return perspective

    xs = [float(point["image_x_percent"]) for point in points]
    ys = [float(point["image_y_percent"]) for point in points]
    pitch_xs = [float(point["pitch_x_meters"]) for point in points]
    pitch_ys = [float(point["pitch_y_meters"]) for point in points]
    image_min_x, image_max_x = min(xs), max(xs)
    image_min_y, image_max_y = min(ys), max(ys)
    pitch_min_x, pitch_max_x = min(pitch_xs), max(pitch_xs)
    pitch_min_y, pitch_max_y = min(pitch_ys), max(pitch_ys)
    pitch_width = max(pitch_max_y - pitch_min_y, 0.001)
    pitch_length = max(pitch_max_x - pitch_min_x, 0.001)
    coverage_x = min(pitch_length / pitch_length_m, 1.0)
    coverage_y = min(pitch_width / pitch_width_m, 1.0)
    point_bonus = min(len(points) / 8, 1.0) * 0.15
    quality_score = max(0.2, min((coverage_x + coverage_y) / 2 + point_bonus, 0.98))
    return {
        "method": "bounding_box_linear_homography_approximation",
        "image_min_x": image_min_x,
        "image_max_x": image_max_x,
        "image_min_y": image_min_y,
        "image_max_y": image_max_y,
        "pitch_min_x": pitch_min_x,
        "pitch_max_x": pitch_max_x,
        "pitch_min_y": pitch_min_y,
        "pitch_max_y": pitch_max_y,
        "quality_score": round(quality_score, 3),
    }


def match_pitch_perspective_transform(
    points: list[dict[str, object]],
    pitch_length_m: float,
    pitch_width_m: float,
) -> dict[str, float | str] | None:
    if len(points) < 4:
        return None
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None

    image_points = np.array(
        [
            [float(point["image_x_percent"]), float(point["image_y_percent"])]
            for point in points
        ],
        dtype=np.float32,
    )
    pitch_points = np.array(
        [
            [float(point["pitch_x_meters"]), float(point["pitch_y_meters"])]
            for point in points
        ],
        dtype=np.float32,
    )
    matrix, _ = cv2.findHomography(image_points, pitch_points, method=0)
    if matrix is None:
        return None
    projected = cv2.perspectiveTransform(image_points.reshape(-1, 1, 2), matrix).reshape(-1, 2)
    residuals = [
        math.dist((float(projected[index][0]), float(projected[index][1])), (float(point[0]), float(point[1])))
        for index, point in enumerate(pitch_points)
    ]
    mean_residual_m = sum(residuals) / len(residuals)
    max_residual_m = max(residuals)
    pitch_xs = [float(point["pitch_x_meters"]) for point in points]
    pitch_ys = [float(point["pitch_y_meters"]) for point in points]
    coverage_x = min(max(pitch_xs) - min(pitch_xs), pitch_length_m) / pitch_length_m
    coverage_y = min(max(pitch_ys) - min(pitch_ys), pitch_width_m) / pitch_width_m
    point_bonus = min((len(points) - 4) / 4, 1.0) * 0.08
    residual_penalty = min(mean_residual_m / 5, 0.45)
    quality_score = max(0.2, min(((coverage_x + coverage_y) / 2) + 0.12 + point_bonus - residual_penalty, 0.99))
    return {
        "method": "perspective_homography",
        "quality_score": round(quality_score, 3),
        "mean_residual_m": round(mean_residual_m, 3),
        "max_residual_m": round(max_residual_m, 3),
        "h00": float(matrix[0][0]),
        "h01": float(matrix[0][1]),
        "h02": float(matrix[0][2]),
        "h10": float(matrix[1][0]),
        "h11": float(matrix[1][1]),
        "h12": float(matrix[1][2]),
        "h20": float(matrix[2][0]),
        "h21": float(matrix[2][1]),
        "h22": float(matrix[2][2]),
    }


def apply_match_pitch_calibration(
    calibration: PerformanceMatchPitchCalibration,
    x_percent: float,
    y_percent: float,
) -> tuple[float, float]:
    transform = decode_match_pitch_calibration_transform(calibration.transform_json)
    if transform.get("method") == "perspective_homography":
        denominator = (
            float(transform.get("h20", 0.0)) * x_percent
            + float(transform.get("h21", 0.0)) * y_percent
            + float(transform.get("h22", 1.0))
        )
        if abs(denominator) > 0.000001:
            x_meters = (
                float(transform.get("h00", 1.0)) * x_percent
                + float(transform.get("h01", 0.0)) * y_percent
                + float(transform.get("h02", 0.0))
            ) / denominator
            y_meters = (
                float(transform.get("h10", 0.0)) * x_percent
                + float(transform.get("h11", 1.0)) * y_percent
                + float(transform.get("h12", 0.0))
            ) / denominator
            return (
                max(0.0, min(x_meters, calibration.pitch_length_m)),
                max(0.0, min(y_meters, calibration.pitch_width_m)),
            )

    image_min_x = float(transform.get("image_min_x", 0))
    image_max_x = float(transform.get("image_max_x", 100))
    image_min_y = float(transform.get("image_min_y", 0))
    image_max_y = float(transform.get("image_max_y", 100))
    pitch_min_x = float(transform.get("pitch_min_x", 0))
    pitch_max_x = float(transform.get("pitch_max_x", calibration.pitch_length_m))
    pitch_min_y = float(transform.get("pitch_min_y", 0))
    pitch_max_y = float(transform.get("pitch_max_y", calibration.pitch_width_m))
    x_ratio = (x_percent - image_min_x) / max(image_max_x - image_min_x, 0.001)
    y_ratio = (y_percent - image_min_y) / max(image_max_y - image_min_y, 0.001)
    x_meters = pitch_min_x + x_ratio * (pitch_max_x - pitch_min_x)
    y_meters = pitch_min_y + y_ratio * (pitch_max_y - pitch_min_y)
    return (
        max(0.0, min(x_meters, calibration.pitch_length_m)),
        max(0.0, min(y_meters, calibration.pitch_width_m)),
    )


def normalize_match_tracking_sample(
    sample: PerformanceMatchTrackingSampleCreate | dict[str, object],
    pitch_length_m: float,
    pitch_width_m: float,
    calibration: PerformanceMatchPitchCalibration | None = None,
) -> dict[str, object]:
    raw = sample.model_dump() if hasattr(sample, "model_dump") else dict(sample)
    x_meters = raw.get("x_meters")
    y_meters = raw.get("y_meters")
    x_percent = raw.get("x_percent")
    y_percent = raw.get("y_percent")
    if calibration is not None and x_meters is None and y_meters is None and x_percent is not None and y_percent is not None:
        x_meters, y_meters = apply_match_pitch_calibration(calibration, float(x_percent), float(y_percent))
    else:
        if x_meters is None and x_percent is not None:
            x_meters = float(x_percent) / 100 * pitch_length_m
        if y_meters is None and y_percent is not None:
            y_meters = float(y_percent) / 100 * pitch_width_m
    if x_percent is None and x_meters is not None:
        x_percent = float(x_meters) / pitch_length_m * 100
    if y_percent is None and y_meters is not None:
        y_percent = float(y_meters) / pitch_width_m * 100
    return {
        **raw,
        "x_meters": max(0.0, min(float(x_meters or 0), pitch_length_m)),
        "y_meters": max(0.0, min(float(y_meters or 0), pitch_width_m)),
        "x_percent": max(0.0, min(float(x_percent or 0), 100.0)),
        "y_percent": max(0.0, min(float(y_percent or 0), 100.0)),
    }


def summarize_match_tracking_samples(samples: list[dict[str, object]]) -> dict[str, object]:
    by_track: dict[str, list[dict[str, object]]] = {}
    for sample in samples:
        by_track.setdefault(str(sample["track_id"]), []).append(sample)
    player_samples = [sample for sample in samples if not is_match_ball_tracking_row(sample)]
    player_metrics: list[dict[str, object]] = []
    total_distance = 0.0
    total_high_speed_distance = 0.0
    total_sprints = 0
    overall_max_speed = 0.0
    continuity_scores: list[float] = []
    confidence_scores: list[float] = []
    speed_spike_count = 0
    for track_id, rows in sorted(by_track.items()):
        ordered = sorted(rows, key=lambda row: (float(row["timestamp_seconds"]), int(row.get("frame_index") or 0)))
        if is_match_ball_tracking_row(ordered[-1]):
            continue
        distance = 0.0
        low_speed_distance = 0.0
        high_speed_distance = 0.0
        sprint_count = 0
        explosive_effort_count = 0
        max_speed = 0.0
        continuity_hits = 0
        segment_count = 0
        previous_speed: float | None = None
        previous_above_sprint = False
        track_confidences: list[float] = []
        heatmap: dict[str, int] = {}
        for index, row in enumerate(ordered):
            zone = match_tracking_zone(float(row["x_percent"]), float(row["y_percent"]))
            heatmap[zone] = heatmap.get(zone, 0) + 1
            if row.get("confidence") is not None:
                track_confidences.append(float(row["confidence"]))
            if index == 0:
                if row.get("speed_mps") is not None:
                    max_speed = max(max_speed, float(row["speed_mps"]))
                continue
            previous = ordered[index - 1]
            dt = max(float(row["timestamp_seconds"]) - float(previous["timestamp_seconds"]), 0.001)
            segment_distance = math.dist(
                (float(previous["x_meters"]), float(previous["y_meters"])),
                (float(row["x_meters"]), float(row["y_meters"])),
            )
            speed = float(row["speed_mps"]) if row.get("speed_mps") is not None else segment_distance / dt
            distance += segment_distance
            segment_count += 1
            if dt <= 1.5:
                continuity_hits += 1
            if previous_speed is not None:
                acceleration = (speed - previous_speed) / dt
                if acceleration >= 2.5:
                    explosive_effort_count += 1
                if speed >= 12.5 or abs(acceleration) >= 6.0:
                    speed_spike_count += 1
            previous_speed = speed
            max_speed = max(max_speed, speed)
            if speed < 2.0:
                low_speed_distance += segment_distance
            if speed >= 5.5:
                high_speed_distance += segment_distance
            above_sprint = speed >= 7.0
            if above_sprint and not previous_above_sprint:
                sprint_count += 1
            previous_above_sprint = above_sprint
        duration = max(float(ordered[-1]["timestamp_seconds"]) - float(ordered[0]["timestamp_seconds"]), 0.0)
        dominant_zone = max(heatmap.items(), key=lambda item: item[1])[0] if heatmap else "unknown"
        continuity_score = continuity_hits / segment_count if segment_count else 0.0
        confidence_score = sum(track_confidences) / len(track_confidences) if track_confidences else 0.65
        work_rate = distance / (duration / 60) if duration > 0 else 0.0
        recovery_ratio = low_speed_distance / distance if distance > 0 else 0.0
        tracking_quality = match_tracking_player_quality_score(
            sample_count=len(ordered),
            duration_seconds=duration,
            continuity_score=continuity_score,
            confidence_score=confidence_score,
            max_speed_mps=max_speed,
        )
        continuity_scores.append(continuity_score)
        confidence_scores.append(confidence_score)
        player_metrics.append(
            {
                "track_id": track_id,
                "player_label": ordered[-1].get("player_label"),
                "team_label": ordered[-1].get("team_label"),
                "jersey_number": ordered[-1].get("jersey_number"),
                "sample_count": len(ordered),
                "duration_seconds": round(duration, 3),
                "distance_m": round(distance, 2),
                "average_speed_mps": round(distance / duration, 3) if duration > 0 else 0.0,
                "max_speed_mps": round(max_speed, 3),
                "work_rate_m_per_min": round(work_rate, 2),
                "high_speed_distance_m": round(high_speed_distance, 2),
                "sprint_count": sprint_count,
                "explosive_effort_count": explosive_effort_count,
                "recovery_ratio": round(recovery_ratio, 3),
                "pressure_applied_count": 0,
                "pressure_received_count": 0,
                "average_nearest_opponent_m": None,
                "off_ball_run_count": 0,
                "territorial_advance_count": 0,
                "pass_completed_count": 0,
                "pass_received_count": 0,
                "pass_attempt_count": 0,
                "pass_accuracy_percent": 0.0,
                "turnover_involved_count": 0,
                "interception_count": 0,
                "tackle_count": 0,
                "ball_carry_m": 0.0,
                "shot_count": 0,
                "shot_on_target_count": 0,
                "expected_goals": 0.0,
                "key_pass_count": 0,
                "expected_assists": 0.0,
                "tracking_quality_score": round(tracking_quality, 3),
                "coaching_flags": match_tracking_player_coaching_flags(
                    sample_count=len(ordered),
                    duration_seconds=duration,
                    distance_m=distance,
                    max_speed_mps=max_speed,
                    high_speed_distance_m=high_speed_distance,
                    sprint_count=sprint_count,
                    recovery_ratio=recovery_ratio,
                    tracking_quality_score=tracking_quality,
                ),
                "dominant_zone": dominant_zone,
                "heatmap": heatmap,
            }
        )
        total_distance += distance
        total_high_speed_distance += high_speed_distance
        total_sprints += sprint_count
        overall_max_speed = max(overall_max_speed, max_speed)
    identity_continuity_score = sum(continuity_scores) / len(continuity_scores) if continuity_scores else 0.0
    average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    team_shape = derive_match_team_shape(player_samples)
    football_context = derive_match_football_context(player_samples, player_metrics)
    ball_context = derive_match_ball_context(samples, player_metrics)
    action_context = derive_match_action_recognition(
        player_metrics=player_metrics,
        pressure_events=football_context["pressure_events"],
        ball_action_events=ball_context["ball_action_events"],
    )
    return {
        "sample_count": len(samples),
        "player_count": len(player_metrics),
        "total_distance_m": round(total_distance, 2),
        "max_speed_mps": round(overall_max_speed, 3),
        "high_speed_distance_m": round(total_high_speed_distance, 2),
        "sprint_count": total_sprints,
        "identity_continuity_score": round(identity_continuity_score, 3),
        "average_detection_confidence": round(average_confidence, 3),
        "speed_spike_count": speed_spike_count,
        "player_metrics": player_metrics,
        "team_shape_metrics": team_shape["team_shape_metrics"],
        "formation_snapshots": team_shape["formation_snapshots"],
        "team_phase_metrics": football_context["team_phase_metrics"],
        "pressure_events": football_context["pressure_events"],
        "match_phase_snapshots": football_context["match_phase_snapshots"],
        "ball_tracking_metrics": ball_context["ball_tracking_metrics"],
        "possession_estimates": ball_context["possession_estimates"],
        "ball_action_events": ball_context["ball_action_events"],
        "recognized_action_events": action_context["recognized_action_events"],
        "action_recognition_metrics": action_context["action_recognition_metrics"],
        "shot_events": ball_context["shot_events"],
        "pass_network": ball_context["pass_network"],
        "pass_type_metrics": ball_context["pass_type_metrics"],
        "defensive_action_events": ball_context["defensive_action_events"],
        "chance_creation_metrics": ball_context["chance_creation_metrics"],
    }


def is_match_ball_tracking_row(sample: dict[str, object]) -> bool:
    values = [
        str(sample.get("track_id") or ""),
        str(sample.get("player_label") or ""),
        str(sample.get("team_label") or ""),
        str(sample.get("source") or ""),
    ]
    return any(value.strip().lower() in {"ball", "match_ball", "football", "soccer_ball"} for value in values)


def derive_match_team_shape(samples: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    by_team: dict[str, list[dict[str, object]]] = {}
    for sample in samples:
        label = str(sample.get("team_label") or "unassigned").strip() or "unassigned"
        by_team.setdefault(label, []).append(sample)
    team_shape_metrics: list[dict[str, object]] = []
    formation_snapshots: list[dict[str, object]] = []
    for team_label, team_samples in sorted(by_team.items()):
        track_ids = sorted({str(sample.get("track_id")) for sample in team_samples if sample.get("track_id")})
        by_timestamp: dict[float, list[dict[str, object]]] = {}
        for sample in team_samples:
            by_timestamp.setdefault(round(float(sample["timestamp_seconds"]), 2), []).append(sample)
        widths: list[float] = []
        depths: list[float] = []
        centroid_xs: list[float] = []
        centroid_ys: list[float] = []
        compactness_scores: list[float] = []
        for timestamp, rows in sorted(by_timestamp.items()):
            if not rows:
                continue
            x_values = [float(row["x_percent"]) for row in rows]
            y_values = [float(row["y_percent"]) for row in rows]
            width = max(y_values) - min(y_values)
            depth = max(x_values) - min(x_values)
            centroid_x = sum(x_values) / len(x_values)
            centroid_y = sum(y_values) / len(y_values)
            compactness = max(0.0, min(1.0, 1.0 - ((width + depth) / 200)))
            widths.append(width)
            depths.append(depth)
            centroid_xs.append(centroid_x)
            centroid_ys.append(centroid_y)
            compactness_scores.append(compactness)
            if len(formation_snapshots) < 24:
                formation_snapshots.append(
                    {
                        "team_label": team_label,
                        "timestamp_seconds": timestamp,
                        "player_count": len(rows),
                        "width_percent": round(width, 2),
                        "depth_percent": round(depth, 2),
                        "centroid_x_percent": round(centroid_x, 2),
                        "centroid_y_percent": round(centroid_y, 2),
                        "dominant_zone": match_tracking_zone(centroid_x, centroid_y),
                    }
                )
        average_width = sum(widths) / len(widths) if widths else 0.0
        average_depth = sum(depths) / len(depths) if depths else 0.0
        average_centroid_x = sum(centroid_xs) / len(centroid_xs) if centroid_xs else 0.0
        average_centroid_y = sum(centroid_ys) / len(centroid_ys) if centroid_ys else 0.0
        average_compactness = sum(compactness_scores) / len(compactness_scores) if compactness_scores else 0.0
        team_shape_metrics.append(
            {
                "team_label": team_label,
                "track_count": len(track_ids),
                "sample_count": len(team_samples),
                "shape_sample_count": len(widths),
                "average_width_percent": round(average_width, 2),
                "average_depth_percent": round(average_depth, 2),
                "average_centroid_x_percent": round(average_centroid_x, 2),
                "average_centroid_y_percent": round(average_centroid_y, 2),
                "average_compactness_score": round(average_compactness, 3),
                "dominant_zone": match_tracking_zone(average_centroid_x, average_centroid_y),
                "shape_hint": match_team_shape_hint(
                    track_count=len(track_ids),
                    average_width=average_width,
                    average_depth=average_depth,
                    average_centroid_x=average_centroid_x,
                    average_compactness=average_compactness,
                ),
            }
        )
    return {
        "team_shape_metrics": team_shape_metrics,
        "formation_snapshots": formation_snapshots,
    }


def derive_match_football_context(
    samples: list[dict[str, object]],
    player_metrics: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    metric_by_track = {str(metric["track_id"]): metric for metric in player_metrics}
    nearest_distances: dict[str, list[float]] = {track_id: [] for track_id in metric_by_track}
    pressure_events: list[dict[str, object]] = []
    match_phase_snapshots: list[dict[str, object]] = []
    team_totals: dict[str, dict[str, float | int | set[str]]] = {}
    previous_by_track: dict[str, dict[str, object]] = {}
    by_timestamp: dict[float, list[dict[str, object]]] = {}
    for sample in samples:
        by_timestamp.setdefault(round(float(sample["timestamp_seconds"]), 2), []).append(sample)
    for timestamp, rows in sorted(by_timestamp.items()):
        team_rows: dict[str, list[dict[str, object]]] = {}
        for row in rows:
            team_label = str(row.get("team_label") or "unassigned").strip() or "unassigned"
            team_rows.setdefault(team_label, []).append(row)
            totals = team_totals.setdefault(
                team_label,
                {
                    "sample_count": 0,
                    "track_ids": set(),
                    "attacking_samples": 0,
                    "middle_samples": 0,
                    "defensive_samples": 0,
                    "high_press_samples": 0,
                    "deep_block_samples": 0,
                    "pressure_events": 0,
                    "off_ball_runs": 0,
                    "territorial_advances": 0,
                    "nearest_opponent_distance_total": 0.0,
                    "nearest_opponent_distance_count": 0,
                },
            )
            totals["sample_count"] = int(totals["sample_count"]) + 1
            cast_track_ids = totals["track_ids"]
            if isinstance(cast_track_ids, set):
                cast_track_ids.add(str(row.get("track_id") or "unknown"))
            x_percent = float(row["x_percent"])
            if x_percent >= 66.66:
                totals["attacking_samples"] = int(totals["attacking_samples"]) + 1
            elif x_percent <= 33.33:
                totals["defensive_samples"] = int(totals["defensive_samples"]) + 1
            else:
                totals["middle_samples"] = int(totals["middle_samples"]) + 1
        for row in rows:
            team_label = str(row.get("team_label") or "unassigned").strip() or "unassigned"
            opponents = [
                opponent
                for opponent_team, opponent_rows in team_rows.items()
                if opponent_team != team_label
                for opponent in opponent_rows
            ]
            if not opponents:
                continue
            nearest = min(
                opponents,
                key=lambda opponent: math.dist(
                    (float(row["x_meters"]), float(row["y_meters"])),
                    (float(opponent["x_meters"]), float(opponent["y_meters"])),
                ),
            )
            nearest_distance = math.dist(
                (float(row["x_meters"]), float(row["y_meters"])),
                (float(nearest["x_meters"]), float(nearest["y_meters"])),
            )
            track_id = str(row.get("track_id") or "unknown")
            nearest_distances.setdefault(track_id, []).append(nearest_distance)
            totals = team_totals[team_label]
            totals["nearest_opponent_distance_total"] = float(totals["nearest_opponent_distance_total"]) + nearest_distance
            totals["nearest_opponent_distance_count"] = int(totals["nearest_opponent_distance_count"]) + 1
            if nearest_distance <= 8.0:
                if float(row["x_percent"]) >= float(nearest["x_percent"]):
                    presser, receiver = row, nearest
                    pressing_team = team_label
                    pressured_team = str(nearest.get("team_label") or "unassigned")
                else:
                    presser, receiver = nearest, row
                    pressing_team = str(nearest.get("team_label") or "unassigned")
                    pressured_team = team_label
                presser_id = str(presser.get("track_id") or "unknown")
                receiver_id = str(receiver.get("track_id") or "unknown")
                if presser_id in metric_by_track:
                    metric_by_track[presser_id]["pressure_applied_count"] = (
                        int(metric_by_track[presser_id].get("pressure_applied_count") or 0) + 1
                    )
                if receiver_id in metric_by_track:
                    metric_by_track[receiver_id]["pressure_received_count"] = (
                        int(metric_by_track[receiver_id].get("pressure_received_count") or 0) + 1
                    )
                team_totals.setdefault(pressing_team, {}).setdefault("pressure_events", 0)
                team_totals[pressing_team]["pressure_events"] = int(team_totals[pressing_team]["pressure_events"]) + 1
                if len(pressure_events) < 60:
                    pressure_events.append(
                        {
                            "timestamp_seconds": timestamp,
                            "pressing_team_label": pressing_team,
                            "pressured_team_label": pressured_team,
                            "presser_track_id": presser_id,
                            "receiver_track_id": receiver_id,
                            "distance_m": round(nearest_distance, 2),
                            "zone": match_tracking_zone(float(receiver["x_percent"]), float(receiver["y_percent"])),
                            "intensity": "high" if nearest_distance <= 4.0 else "moderate",
                        }
                    )
            previous = previous_by_track.get(track_id)
            if previous is not None:
                dt = max(float(row["timestamp_seconds"]) - float(previous["timestamp_seconds"]), 0.001)
                dx_percent = float(row["x_percent"]) - float(previous["x_percent"])
                speed_mps = math.dist(
                    (float(previous["x_meters"]), float(previous["y_meters"])),
                    (float(row["x_meters"]), float(row["y_meters"])),
                ) / dt
                if dx_percent >= 8.0 and speed_mps >= 4.0:
                    if track_id in metric_by_track:
                        metric_by_track[track_id]["territorial_advance_count"] = (
                            int(metric_by_track[track_id].get("territorial_advance_count") or 0) + 1
                        )
                    totals["territorial_advances"] = int(totals["territorial_advances"]) + 1
                if speed_mps >= 5.0 and nearest_distance > 10.0:
                    if track_id in metric_by_track:
                        metric_by_track[track_id]["off_ball_run_count"] = (
                            int(metric_by_track[track_id].get("off_ball_run_count") or 0) + 1
                        )
                    totals["off_ball_runs"] = int(totals["off_ball_runs"]) + 1
            previous_by_track[track_id] = row
        if len(match_phase_snapshots) < 36:
            match_phase_snapshots.append(match_phase_snapshot(timestamp, team_rows))
    for track_id, distances in nearest_distances.items():
        if distances and track_id in metric_by_track:
            metric_by_track[track_id]["average_nearest_opponent_m"] = round(sum(distances) / len(distances), 2)
    team_phase_metrics: list[dict[str, object]] = []
    for team_label, totals in sorted(team_totals.items()):
        sample_count = max(int(totals.get("sample_count") or 0), 1)
        track_ids = totals.get("track_ids")
        nearest_count = int(totals.get("nearest_opponent_distance_count") or 0)
        team_phase_metrics.append(
            {
                "team_label": team_label,
                "track_count": len(track_ids) if isinstance(track_ids, set) else 0,
                "sample_count": sample_count,
                "attacking_third_percent": round(int(totals.get("attacking_samples") or 0) / sample_count * 100, 2),
                "middle_third_percent": round(int(totals.get("middle_samples") or 0) / sample_count * 100, 2),
                "defensive_third_percent": round(int(totals.get("defensive_samples") or 0) / sample_count * 100, 2),
                "pressure_event_count": int(totals.get("pressure_events") or 0),
                "off_ball_run_count": int(totals.get("off_ball_runs") or 0),
                "territorial_advance_count": int(totals.get("territorial_advances") or 0),
                "average_nearest_opponent_m": (
                    round(float(totals.get("nearest_opponent_distance_total") or 0.0) / nearest_count, 2)
                    if nearest_count
                    else None
                ),
                "phase_hint": match_team_phase_hint(totals, sample_count),
            }
        )
    return {
        "team_phase_metrics": team_phase_metrics,
        "pressure_events": pressure_events,
        "match_phase_snapshots": match_phase_snapshots,
    }


def derive_match_ball_context(
    samples: list[dict[str, object]],
    player_metrics: list[dict[str, object]],
) -> dict[str, object]:
    ball_rows = sorted(
        [sample for sample in samples if is_match_ball_tracking_row(sample)],
        key=lambda row: (float(row["timestamp_seconds"]), int(row.get("frame_index") or 0)),
    )
    if not ball_rows:
        return {
            "ball_tracking_metrics": {
                "ball_sample_count": 0,
                "possession_sample_count": 0,
                "pass_count": 0,
                "pass_attempt_count": 0,
                "pass_accuracy_percent": 0.0,
                "turnover_count": 0,
                "interception_count": 0,
                "tackle_count": 0,
                "carry_count": 0,
                "shot_count": 0,
                "shot_on_target_count": 0,
                "expected_goals": 0.0,
                "key_pass_count": 0,
                "ball_distance_m": 0.0,
                "max_ball_speed_mps": 0.0,
            },
            "possession_estimates": [],
            "ball_action_events": [],
            "shot_events": [],
            "pass_network": [],
            "pass_type_metrics": [],
            "defensive_action_events": [],
            "chance_creation_metrics": {},
        }
    metric_by_track = {str(metric["track_id"]): metric for metric in player_metrics}
    player_rows_by_timestamp: dict[float, list[dict[str, object]]] = {}
    for sample in samples:
        if is_match_ball_tracking_row(sample):
            continue
        player_rows_by_timestamp.setdefault(round(float(sample["timestamp_seconds"]), 2), []).append(sample)
    possession_counts: dict[str, int] = {}
    player_possession_counts: dict[str, int] = {}
    ball_action_events: list[dict[str, object]] = []
    previous_ball: dict[str, object] | None = None
    previous_holder: dict[str, object] | None = None
    ball_distance = 0.0
    max_ball_speed = 0.0
    pass_count = 0
    pass_attempt_count = 0
    turnover_count = 0
    interception_count = 0
    tackle_count = 0
    carry_count = 0
    shot_count = 0
    shot_on_target_count = 0
    expected_goals = 0.0
    pass_type_totals: dict[tuple[str, str], dict[str, int]] = {}
    for ball in ball_rows:
        holder = nearest_ball_holder(ball, player_rows_by_timestamp)
        if holder is not None:
            team_label = str(holder.get("team_label") or "unassigned")
            track_id = str(holder.get("track_id") or "unknown")
            possession_counts[team_label] = possession_counts.get(team_label, 0) + 1
            player_possession_counts[track_id] = player_possession_counts.get(track_id, 0) + 1
        if previous_ball is not None:
            dt = max(float(ball["timestamp_seconds"]) - float(previous_ball["timestamp_seconds"]), 0.001)
            segment_distance = math.dist(
                (float(previous_ball["x_meters"]), float(previous_ball["y_meters"])),
                (float(ball["x_meters"]), float(ball["y_meters"])),
            )
            ball_distance += segment_distance
            max_ball_speed = max(max_ball_speed, segment_distance / dt)
            shot_event = match_tracking_shot_event(previous_ball, ball, previous_holder)
            if shot_event is not None:
                shot_count += 1
                shot_on_target_count += 1 if bool(shot_event["on_target"]) else 0
                shot_xg = float(shot_event["expected_goals"])
                expected_goals += shot_xg
                shooter_id = str(shot_event["shooter_track_id"])
                if shooter_id in metric_by_track:
                    metric_by_track[shooter_id]["shot_count"] = int(metric_by_track[shooter_id].get("shot_count") or 0) + 1
                    metric_by_track[shooter_id]["shot_on_target_count"] = (
                        int(metric_by_track[shooter_id].get("shot_on_target_count") or 0)
                        + (1 if bool(shot_event["on_target"]) else 0)
                    )
                    metric_by_track[shooter_id]["expected_goals"] = round(
                        float(metric_by_track[shooter_id].get("expected_goals") or 0.0) + shot_xg,
                        3,
                    )
                if len(ball_action_events) < 80:
                    ball_action_events.append(shot_event)
            if holder is not None and previous_holder is not None:
                holder_id = str(holder.get("track_id") or "unknown")
                previous_holder_id = str(previous_holder.get("track_id") or "unknown")
                holder_team = str(holder.get("team_label") or "unassigned")
                previous_team = str(previous_holder.get("team_label") or "unassigned")
                if holder_id == previous_holder_id:
                    if segment_distance >= 3.0:
                        carry_count += 1
                        if holder_id in metric_by_track:
                            metric_by_track[holder_id]["ball_carry_m"] = round(
                                float(metric_by_track[holder_id].get("ball_carry_m") or 0.0) + segment_distance,
                                2,
                            )
                elif segment_distance >= 3.0:
                    event_type = "pass" if holder_team == previous_team else "turnover"
                    pass_type = match_tracking_pass_type(previous_ball, ball, previous_holder, holder)
                    pass_attempt_count += 1
                    if previous_holder_id in metric_by_track:
                        metric_by_track[previous_holder_id]["pass_attempt_count"] = (
                            int(metric_by_track[previous_holder_id].get("pass_attempt_count") or 0) + 1
                        )
                    pass_type_key = (previous_team, pass_type)
                    pass_type_totals.setdefault(
                        pass_type_key,
                        {"attempt_count": 0, "completed_count": 0, "turnover_count": 0},
                    )
                    pass_type_totals[pass_type_key]["attempt_count"] += 1
                    if event_type == "pass":
                        pass_count += 1
                        pass_type_totals[pass_type_key]["completed_count"] += 1
                        if previous_holder_id in metric_by_track:
                            metric_by_track[previous_holder_id]["pass_completed_count"] = (
                                int(metric_by_track[previous_holder_id].get("pass_completed_count") or 0) + 1
                            )
                        if holder_id in metric_by_track:
                            metric_by_track[holder_id]["pass_received_count"] = (
                                int(metric_by_track[holder_id].get("pass_received_count") or 0) + 1
                            )
                    else:
                        turnover_count += 1
                        pass_type_totals[pass_type_key]["turnover_count"] += 1
                        defensive_action_type = match_tracking_defensive_action_type(previous_ball, ball)
                        if defensive_action_type == "interception":
                            interception_count += 1
                            if holder_id in metric_by_track:
                                metric_by_track[holder_id]["interception_count"] = (
                                    int(metric_by_track[holder_id].get("interception_count") or 0) + 1
                                )
                        else:
                            tackle_count += 1
                            if holder_id in metric_by_track:
                                metric_by_track[holder_id]["tackle_count"] = (
                                    int(metric_by_track[holder_id].get("tackle_count") or 0) + 1
                                )
                        for track_id in {holder_id, previous_holder_id}:
                            if track_id in metric_by_track:
                                metric_by_track[track_id]["turnover_involved_count"] = (
                                    int(metric_by_track[track_id].get("turnover_involved_count") or 0) + 1
                                )
                    if len(ball_action_events) < 80:
                        ball_action_events.append(
                            {
                                "event_type": event_type,
                                "timestamp_seconds": round(float(ball["timestamp_seconds"]), 2),
                                "from_track_id": previous_holder_id,
                                "from_team_label": previous_team,
                                "to_track_id": holder_id,
                                "to_team_label": holder_team,
                                "ball_distance_m": round(segment_distance, 2),
                                "pass_type": pass_type,
                                "outcome": "completed" if event_type == "pass" else "lost",
                                "defensive_action_type": defensive_action_type if event_type == "turnover" else None,
                                "zone": match_tracking_zone(float(ball["x_percent"]), float(ball["y_percent"])),
                            }
                        )
        previous_ball = ball
        if holder is not None:
            previous_holder = holder
    possession_sample_count = sum(possession_counts.values())
    possession_estimates = [
        {
            "team_label": team_label,
            "sample_count": count,
            "possession_percent": round(count / possession_sample_count * 100, 2)
            if possession_sample_count
            else 0.0,
            "phase_hint": "possession_control" if possession_sample_count and count / possession_sample_count >= 0.55 else "shared_possession",
        }
        for team_label, count in sorted(possession_counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    for track_id, count in player_possession_counts.items():
        if track_id in metric_by_track:
            metric_by_track[track_id]["ball_possession_sample_count"] = count
    for metric in metric_by_track.values():
        attempts = int(metric.get("pass_attempt_count") or 0)
        if attempts:
            metric["pass_accuracy_percent"] = round(int(metric.get("pass_completed_count") or 0) / attempts * 100, 2)
    shot_events = [event for event in ball_action_events if event.get("event_type") == "shot"]
    defensive_action_events = [event for event in ball_action_events if event.get("event_type") == "turnover"]
    pass_type_metrics = [
        {
            "team_label": team_label,
            "pass_type": pass_type,
            "attempt_count": totals["attempt_count"],
            "completed_count": totals["completed_count"],
            "turnover_count": totals["turnover_count"],
            "accuracy_percent": round(totals["completed_count"] / totals["attempt_count"] * 100, 2)
            if totals["attempt_count"]
            else 0.0,
        }
        for (team_label, pass_type), totals in sorted(
            pass_type_totals.items(),
            key=lambda item: (-item[1]["attempt_count"], item[0][0], item[0][1]),
        )
    ]
    pass_network = derive_match_pass_network(ball_action_events, metric_by_track)
    key_pass_count = sum(int(link.get("key_pass_count") or 0) for link in pass_network)
    return {
        "ball_tracking_metrics": {
            "ball_sample_count": len(ball_rows),
            "possession_sample_count": possession_sample_count,
            "pass_count": pass_count,
            "pass_attempt_count": pass_attempt_count,
            "pass_accuracy_percent": round(pass_count / pass_attempt_count * 100, 2)
            if pass_attempt_count
            else 0.0,
            "turnover_count": turnover_count,
            "interception_count": interception_count,
            "tackle_count": tackle_count,
            "carry_count": carry_count,
            "shot_count": shot_count,
            "shot_on_target_count": shot_on_target_count,
            "expected_goals": round(expected_goals, 3),
            "key_pass_count": key_pass_count,
            "ball_distance_m": round(ball_distance, 2),
            "max_ball_speed_mps": round(max_ball_speed, 3),
        },
        "possession_estimates": possession_estimates,
        "ball_action_events": ball_action_events,
        "shot_events": shot_events,
        "pass_network": pass_network,
        "pass_type_metrics": pass_type_metrics,
        "defensive_action_events": defensive_action_events,
        "chance_creation_metrics": {
            "shot_count": shot_count,
            "shot_on_target_count": shot_on_target_count,
            "expected_goals": round(expected_goals, 3),
            "key_pass_count": key_pass_count,
            "shot_accuracy_percent": round(shot_on_target_count / shot_count * 100, 2) if shot_count else 0.0,
        },
    }


def nearest_ball_holder(
    ball: dict[str, object],
    player_rows_by_timestamp: dict[float, list[dict[str, object]]],
) -> dict[str, object] | None:
    timestamp = round(float(ball["timestamp_seconds"]), 2)
    candidates = player_rows_by_timestamp.get(timestamp, [])
    if not candidates:
        nearby_timestamps = sorted(
            player_rows_by_timestamp,
            key=lambda value: abs(value - timestamp),
        )[:1]
        candidates = player_rows_by_timestamp.get(nearby_timestamps[0], []) if nearby_timestamps else []
    if not candidates:
        return None
    nearest = min(
        candidates,
        key=lambda row: math.dist(
            (float(ball["x_meters"]), float(ball["y_meters"])),
            (float(row["x_meters"]), float(row["y_meters"])),
        ),
    )
    distance = math.dist(
        (float(ball["x_meters"]), float(ball["y_meters"])),
        (float(nearest["x_meters"]), float(nearest["y_meters"])),
    )
    return nearest if distance <= 12.0 else None


def derive_match_action_recognition(
    *,
    player_metrics: list[dict[str, object]],
    pressure_events: list[dict[str, object]],
    ball_action_events: list[dict[str, object]],
) -> dict[str, object]:
    events: list[dict[str, object]] = []

    def add_event(
        *,
        action_type: str,
        title: str,
        timestamp_seconds: float | None,
        primary_track_id: str | None,
        team_label: str | None,
        zone: str | None,
        confidence: float,
        evidence: str,
        coaching_cue: str,
        secondary_track_id: str | None = None,
        source: str = "tracking_heuristic",
    ) -> None:
        if len(events) >= 100:
            return
        events.append(
            {
                "action_type": action_type,
                "title": title,
                "timestamp_seconds": round(timestamp_seconds, 2) if timestamp_seconds is not None else None,
                "primary_track_id": primary_track_id,
                "secondary_track_id": secondary_track_id,
                "team_label": team_label,
                "zone": zone,
                "confidence": round(max(0.0, min(confidence, 0.96)), 3),
                "evidence": evidence,
                "coaching_cue": coaching_cue,
                "source": source,
            }
        )

    for event in ball_action_events:
        event_type = str(event.get("event_type") or "")
        timestamp = float(event.get("timestamp_seconds") or 0.0)
        zone = str(event.get("zone") or "unknown")
        if event_type == "shot":
            xg = float(event.get("expected_goals") or 0.0)
            add_event(
                action_type="shot_attempt",
                title="Shot attempt",
                timestamp_seconds=timestamp,
                primary_track_id=str(event.get("shooter_track_id") or "unknown"),
                team_label=str(event.get("shooter_team_label") or "unassigned"),
                zone=zone,
                confidence=0.78 + min(xg, 0.5) * 0.2,
                evidence=(
                    f"Ball movement reached the {event.get('target_goal', 'goal')} goal zone "
                    f"with {xg:.2f} xG."
                ),
                coaching_cue="Review shot selection, support options, and rebound positioning.",
            )
        elif event_type == "pass":
            pass_type = str(event.get("pass_type") or "pass").replace("_", " ")
            add_event(
                action_type="pass_completion",
                title=f"{pass_type.title()} completed",
                timestamp_seconds=timestamp,
                primary_track_id=str(event.get("from_track_id") or "unknown"),
                secondary_track_id=str(event.get("to_track_id") or "unknown"),
                team_label=str(event.get("from_team_label") or "unassigned"),
                zone=zone,
                confidence=0.84 if event.get("outcome") == "completed" else 0.72,
                evidence=f"Ball travelled {event.get('ball_distance_m', 0)}m between same-team holders.",
                coaching_cue="Tag the receiving body shape and next action after the pass.",
            )
        elif event_type == "turnover":
            defensive_action = str(event.get("defensive_action_type") or "ball_win")
            add_event(
                action_type=defensive_action,
                title=defensive_action.replace("_", " ").title(),
                timestamp_seconds=timestamp,
                primary_track_id=str(event.get("to_track_id") or "unknown"),
                secondary_track_id=str(event.get("from_track_id") or "unknown"),
                team_label=str(event.get("to_team_label") or "unassigned"),
                zone=zone,
                confidence=0.82 if defensive_action == "interception" else 0.76,
                evidence=f"Possession changed teams after {event.get('ball_distance_m', 0)}m ball movement.",
                coaching_cue="Review counter-press spacing and the first pass after the ball win.",
            )

    for event in pressure_events[:40]:
        distance = float(event.get("distance_m") or 0.0)
        add_event(
            action_type="pressure",
            title="Pressure applied",
            timestamp_seconds=float(event.get("timestamp_seconds") or 0.0),
            primary_track_id=str(event.get("presser_track_id") or "unknown"),
            secondary_track_id=str(event.get("receiver_track_id") or "unknown"),
            team_label=str(event.get("pressing_team_label") or "unassigned"),
            zone=str(event.get("zone") or "unknown"),
            confidence=0.88 if distance <= 4.0 else 0.72,
            evidence=f"Nearest-opponent distance closed to {distance:.1f}m.",
            coaching_cue="Check pressing cover: nearest support, escape route, and foul risk.",
        )

    for metric in player_metrics:
        label = str(metric.get("player_label") or metric.get("track_id") or "player")
        track_id = str(metric.get("track_id") or "unknown")
        team_label = str(metric.get("team_label") or "unassigned")
        zone = str(metric.get("dominant_zone") or "unknown")
        sprint_count = int(metric.get("sprint_count") or 0)
        if sprint_count > 0:
            add_event(
                action_type="high_speed_run",
                title=f"{label} high-speed run",
                timestamp_seconds=None,
                primary_track_id=track_id,
                team_label=team_label,
                zone=zone,
                confidence=0.82 if sprint_count >= 2 else 0.74,
                evidence=(
                    f"{sprint_count} sprint(s), {metric.get('high_speed_distance_m', 0)}m high-speed "
                    f"distance, max {metric.get('max_speed_mps', 0)} m/s."
                ),
                coaching_cue="Review run timing, deceleration, and recovery spacing.",
            )
        off_ball_runs = int(metric.get("off_ball_run_count") or 0)
        if off_ball_runs > 0:
            add_event(
                action_type="off_ball_run",
                title=f"{label} off-ball run",
                timestamp_seconds=None,
                primary_track_id=track_id,
                team_label=team_label,
                zone=zone,
                confidence=0.74,
                evidence=f"{off_ball_runs} off-ball run(s) detected away from nearest opponent pressure.",
                coaching_cue="Review whether the run opened a passing lane or dragged a defender.",
            )
        territorial_advances = int(metric.get("territorial_advance_count") or 0)
        if territorial_advances > 0:
            add_event(
                action_type="territorial_advance",
                title=f"{label} territorial advance",
                timestamp_seconds=None,
                primary_track_id=track_id,
                team_label=team_label,
                zone=zone,
                confidence=0.72,
                evidence=f"{territorial_advances} forward territorial advance(s) from tracking deltas.",
                coaching_cue="Review support angles behind the advancing player.",
            )
        ball_carry = float(metric.get("ball_carry_m") or 0.0)
        if ball_carry >= 5.0:
            add_event(
                action_type="ball_carry",
                title=f"{label} ball carry",
                timestamp_seconds=None,
                primary_track_id=track_id,
                team_label=team_label,
                zone=zone,
                confidence=0.78,
                evidence=f"{ball_carry:.1f}m of ball-carry distance while nearest to the ball.",
                coaching_cue="Review carry timing, defender engagement, and release point.",
            )

    events.sort(
        key=lambda event: (
            float(event["timestamp_seconds"]) if event["timestamp_seconds"] is not None else 10_000.0,
            str(event["action_type"]),
            str(event["primary_track_id"] or ""),
        )
    )
    action_counts: dict[str, int] = {}
    confidence_total = 0.0
    high_confidence_count = 0
    for event in events:
        action_type = str(event["action_type"])
        action_counts[action_type] = action_counts.get(action_type, 0) + 1
        confidence = float(event["confidence"])
        confidence_total += confidence
        if confidence >= 0.8:
            high_confidence_count += 1
    primary_actions = [
        {"action_type": action_type, "count": count}
        for action_type, count in sorted(action_counts.items(), key=lambda item: (-item[1], item[0]))[:8]
    ]
    return {
        "recognized_action_events": events[:100],
        "action_recognition_metrics": {
            "model_policy": "afrolete-tracking-action-recognition-v1",
            "event_count": len(events),
            "action_type_counts": action_counts,
            "primary_actions": primary_actions,
            "high_confidence_count": high_confidence_count,
            "average_confidence": round(confidence_total / len(events), 3) if events else 0.0,
            "review_required": True,
        },
    }


def match_tracking_pass_type(
    previous_ball: dict[str, object],
    ball: dict[str, object],
    previous_holder: dict[str, object],
    holder: dict[str, object],
) -> str:
    distance = math.dist(
        (float(previous_ball["x_meters"]), float(previous_ball["y_meters"])),
        (float(ball["x_meters"]), float(ball["y_meters"])),
    )
    x_delta = float(ball["x_percent"]) - float(previous_ball["x_percent"])
    y_delta = abs(float(ball["y_percent"]) - float(previous_ball["y_percent"]))
    holder_team = str(holder.get("team_label") or "")
    previous_team = str(previous_holder.get("team_label") or "")
    if previous_team == holder_team and y_delta >= 22 and max(float(previous_ball["x_percent"]), float(ball["x_percent"])) >= 60:
        return "cross"
    if previous_team == holder_team and abs(x_delta) >= 18 and distance >= 16:
        return "through_ball" if x_delta > 0 else "progressive_pass"
    if distance < 12:
        return "short_pass"
    if distance < 28:
        return "medium_pass"
    return "long_pass"


def match_tracking_defensive_action_type(previous_ball: dict[str, object], ball: dict[str, object]) -> str:
    distance = math.dist(
        (float(previous_ball["x_meters"]), float(previous_ball["y_meters"])),
        (float(ball["x_meters"]), float(ball["y_meters"])),
    )
    return "interception" if distance >= 8 else "tackle"


def match_tracking_shot_event(
    previous_ball: dict[str, object],
    ball: dict[str, object],
    previous_holder: dict[str, object] | None,
) -> dict[str, object] | None:
    if previous_holder is None:
        return None
    start_x = float(previous_ball["x_percent"])
    start_y = float(previous_ball["y_percent"])
    end_x = float(ball["x_percent"])
    end_y = float(ball["y_percent"])
    dx = end_x - start_x
    segment_distance = math.dist(
        (float(previous_ball["x_meters"]), float(previous_ball["y_meters"])),
        (float(ball["x_meters"]), float(ball["y_meters"])),
    )
    if segment_distance < 6.0:
        return None
    target_goal: str | None = None
    if end_x >= 94 and abs(dx) >= 4:
        target_goal = "right"
    elif end_x <= 6 and abs(dx) >= 4:
        target_goal = "left"
    elif start_x >= 72 and dx >= 8:
        target_goal = "right"
    elif start_x <= 28 and dx <= -8:
        target_goal = "left"
    if target_goal is None:
        return None
    centrality = max(0.0, 1 - abs(end_y - 50) / 35)
    if centrality <= 0.2:
        return None
    xg = match_tracking_expected_goals(start_x, start_y, target_goal)
    on_target = centrality >= 0.45 and (end_x >= 96 or end_x <= 4)
    return {
        "event_type": "shot",
        "timestamp_seconds": round(float(ball["timestamp_seconds"]), 2),
        "shooter_track_id": str(previous_holder.get("track_id") or "unknown"),
        "shooter_team_label": str(previous_holder.get("team_label") or "unassigned"),
        "target_goal": target_goal,
        "on_target": on_target,
        "expected_goals": xg,
        "ball_distance_m": round(segment_distance, 2),
        "zone": match_tracking_zone(start_x, start_y),
    }


def match_tracking_expected_goals(start_x_percent: float, start_y_percent: float, target_goal: str) -> float:
    goal_x = 100.0 if target_goal == "right" else 0.0
    distance_percent = math.dist((start_x_percent, start_y_percent), (goal_x, 50.0))
    centrality = max(0.0, 1 - abs(start_y_percent - 50.0) / 50.0)
    distance_score = max(0.0, 1 - distance_percent / 80.0)
    xg = 0.04 + distance_score * 0.34 + centrality * 0.18
    if distance_percent <= 18:
        xg += 0.16
    return round(min(max(xg, 0.02), 0.78), 3)


def derive_match_pass_network(
    ball_action_events: list[dict[str, object]],
    metric_by_track: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    pass_events = [event for event in ball_action_events if event.get("event_type") == "pass"]
    shot_events = [event for event in ball_action_events if event.get("event_type") == "shot"]
    links: dict[tuple[str, str], dict[str, object]] = {}
    for event in pass_events:
        from_track_id = str(event.get("from_track_id") or "unknown")
        to_track_id = str(event.get("to_track_id") or "unknown")
        key = (from_track_id, to_track_id)
        link = links.setdefault(
            key,
            {
                "from_track_id": from_track_id,
                "to_track_id": to_track_id,
                "team_label": event.get("from_team_label"),
                "pass_count": 0,
                "total_distance_m": 0.0,
                "key_pass_count": 0,
                "expected_assists": 0.0,
            },
        )
        link["pass_count"] = int(link["pass_count"]) + 1
        link["total_distance_m"] = round(float(link["total_distance_m"]) + float(event.get("ball_distance_m") or 0.0), 2)
    for shot in shot_events:
        shooter_id = str(shot.get("shooter_track_id") or "unknown")
        shot_time = float(shot.get("timestamp_seconds") or 0.0)
        candidates = [
            event
            for event in pass_events
            if str(event.get("to_track_id") or "") == shooter_id
            and 0 <= shot_time - float(event.get("timestamp_seconds") or 0.0) <= 10
        ]
        if not candidates:
            continue
        key_pass = max(candidates, key=lambda event: float(event.get("timestamp_seconds") or 0.0))
        from_track_id = str(key_pass.get("from_track_id") or "unknown")
        to_track_id = str(key_pass.get("to_track_id") or "unknown")
        link = links.get((from_track_id, to_track_id))
        if link is None:
            continue
        shot_xg = float(shot.get("expected_goals") or 0.0)
        link["key_pass_count"] = int(link["key_pass_count"]) + 1
        link["expected_assists"] = round(float(link["expected_assists"]) + shot_xg, 3)
        if from_track_id in metric_by_track:
            metric_by_track[from_track_id]["key_pass_count"] = (
                int(metric_by_track[from_track_id].get("key_pass_count") or 0) + 1
            )
            metric_by_track[from_track_id]["expected_assists"] = round(
                float(metric_by_track[from_track_id].get("expected_assists") or 0.0) + shot_xg,
                3,
            )
    return sorted(
        links.values(),
        key=lambda item: (
            int(item.get("key_pass_count") or 0),
            int(item.get("pass_count") or 0),
            float(item.get("expected_assists") or 0.0),
        ),
        reverse=True,
    )[:40]


def match_phase_snapshot(timestamp: float, team_rows: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    teams: list[dict[str, object]] = []
    for team_label, rows in sorted(team_rows.items()):
        x_values = [float(row["x_percent"]) for row in rows]
        teams.append(
            {
                "team_label": team_label,
                "player_count": len(rows),
                "centroid_x_percent": round(sum(x_values) / len(x_values), 2) if x_values else 0.0,
                "territory": (
                    "attacking"
                    if x_values and sum(x_values) / len(x_values) >= 60
                    else "defensive"
                    if x_values and sum(x_values) / len(x_values) <= 40
                    else "middle"
                ),
            }
        )
    return {"timestamp_seconds": timestamp, "teams": teams}


def match_team_phase_hint(totals: dict[str, float | int | set[str]], sample_count: int) -> str:
    attacking = int(totals.get("attacking_samples") or 0) / sample_count
    defensive = int(totals.get("defensive_samples") or 0) / sample_count
    pressure = int(totals.get("pressure_events") or 0)
    advances = int(totals.get("territorial_advances") or 0)
    off_ball = int(totals.get("off_ball_runs") or 0)
    if pressure >= max(sample_count * 0.25, 2):
        return "active_pressing"
    if attacking >= 0.45:
        return "territorial_dominance"
    if defensive >= 0.55:
        return "deep_defensive_phase"
    if advances >= 2:
        return "direct_progression"
    if off_ball >= 2:
        return "off_ball_running_phase"
    return "balanced_phase"


def match_team_shape_hint(
    *,
    track_count: int,
    average_width: float,
    average_depth: float,
    average_centroid_x: float,
    average_compactness: float,
) -> str:
    if track_count < 2:
        return "individual_track"
    if average_centroid_x >= 62:
        return "high_press_shape"
    if average_centroid_x <= 38:
        return "deep_block_shape"
    if average_compactness < 0.55:
        return "stretched_shape"
    if average_width >= 48 and average_depth <= 24:
        return "wide_flat_line"
    if average_depth >= 45:
        return "vertical_stagger"
    return "compact_mid_block"


def match_tracking_zone(x_percent: float, y_percent: float) -> str:
    third = "defensive" if x_percent < 33.33 else "middle" if x_percent < 66.66 else "attacking"
    channel = "left" if y_percent < 33.33 else "central" if y_percent < 66.66 else "right"
    return f"{third}_{channel}"


def match_tracking_player_quality_score(
    *,
    sample_count: int,
    duration_seconds: float,
    continuity_score: float,
    confidence_score: float,
    max_speed_mps: float,
) -> float:
    sample_score = min(sample_count / 12, 1.0)
    duration_score = min(duration_seconds / 30, 1.0)
    plausible_speed_score = 1.0 if max_speed_mps <= 11.5 else 0.55
    score = (
        sample_score * 0.25
        + duration_score * 0.15
        + continuity_score * 0.25
        + confidence_score * 0.25
        + plausible_speed_score * 0.10
    )
    return max(0.0, min(score, 1.0))


def match_tracking_player_coaching_flags(
    *,
    sample_count: int,
    duration_seconds: float,
    distance_m: float,
    max_speed_mps: float,
    high_speed_distance_m: float,
    sprint_count: int,
    recovery_ratio: float,
    tracking_quality_score: float,
) -> list[str]:
    flags: list[str] = []
    if tracking_quality_score < 0.55:
        flags.append("Review tracking identity before using this player's load numbers.")
    if sample_count < 6 or duration_seconds < 10:
        flags.append("Capture a longer segment for reliable match-load comparison.")
    if max_speed_mps >= 8.5:
        flags.append("High peak speed: inspect sprint mechanics and deceleration posture.")
    if sprint_count >= 3 or high_speed_distance_m >= max(distance_m * 0.35, 40.0):
        flags.append("High repeated-sprint demand: plan recovery and substitution windows.")
    if distance_m > 0 and recovery_ratio < 0.12 and high_speed_distance_m > 0:
        flags.append("Limited low-speed recovery between efforts.")
    if not flags:
        flags.append("Tracking profile is stable enough for coach review.")
    return flags


def enrich_match_tracking_summary(
    summary: dict[str, object],
    *,
    calibration: PerformanceMatchPitchCalibration | None,
    source_provider: str,
    model_policy: str,
) -> dict[str, object]:
    calibration_quality = calibration.quality_score if calibration is not None else 0.0
    identity_continuity = float(summary.get("identity_continuity_score") or 0.0)
    detection_confidence = float(summary.get("average_detection_confidence") or 0.0)
    player_count = int(summary.get("player_count") or 0)
    sample_count = int(summary.get("sample_count") or 0)
    speed_spikes = int(summary.get("speed_spike_count") or 0)
    provider_bonus = 0.15 if "import" in source_provider or "provider" in source_provider else 0.0
    tracking_quality = max(
        0.0,
        min(
            1.0,
            identity_continuity * 0.28
            + detection_confidence * 0.18
            + calibration_quality * 0.24
            + min(sample_count / max(player_count * 12, 12), 1.0) * 0.15
            + min(player_count / 22, 1.0) * 0.10
            + provider_bonus,
        ),
    )
    if speed_spikes:
        tracking_quality = max(0.0, tracking_quality - min(speed_spikes * 0.04, 0.2))
    readiness_level = "coach_ready"
    if tracking_quality < 0.55:
        readiness_level = "demo_only"
    elif tracking_quality < 0.72:
        readiness_level = "coach_review_required"
    elif calibration is None:
        readiness_level = "calibration_required"
    quality_warnings = match_tracking_quality_warnings(
        calibration=calibration,
        model_policy=model_policy,
        readiness_level=readiness_level,
        identity_continuity=identity_continuity,
        player_count=player_count,
        speed_spike_count=speed_spikes,
    )
    quality_warnings.extend(str(warning) for warning in summary.get("warnings", []) if str(warning))
    coaching_guidance = match_tracking_coaching_guidance(summary, readiness_level=readiness_level)
    tactical_guidance = match_tracking_tactical_guidance(summary)
    return {
        **summary,
        "tracking_quality_score": round(tracking_quality, 3),
        "calibration_quality_score": round(calibration_quality, 3),
        "readiness_level": readiness_level,
        "quality_warnings": quality_warnings,
        "coaching_guidance": coaching_guidance,
        "tactical_guidance": tactical_guidance,
    }


def match_tracking_quality_warnings(
    *,
    calibration: PerformanceMatchPitchCalibration | None,
    model_policy: str,
    readiness_level: str,
    identity_continuity: float,
    player_count: int,
    speed_spike_count: int,
) -> list[str]:
    warnings: list[str] = []
    if calibration is None:
        warnings.append("No pitch calibration is attached; distance and speed are frame-normalized estimates.")
    elif calibration.quality_score < 0.75:
        warnings.append("Pitch calibration quality is low; review control points before trusting distance metrics.")
    if "opencv-background-subtraction" in model_policy:
        warnings.append("Automatic tracking uses motion segmentation and should be reviewed before coach decisions.")
    if identity_continuity < 0.65:
        warnings.append("Track continuity is weak; occlusions or camera cuts may have changed player identities.")
    if player_count < 10:
        warnings.append("Fewer than ten players were tracked; treat team-level load as partial footage.")
    if speed_spike_count:
        warnings.append("Implausible speed or acceleration spikes were detected and reduce analytics confidence.")
    if readiness_level == "coach_ready":
        warnings.append("Tracking quality is sufficient for coach review, subject to normal video context checks.")
    return warnings


def match_tracking_coaching_guidance(summary: dict[str, object], *, readiness_level: str) -> list[str]:
    metrics = list(summary.get("player_metrics") or [])
    guidance: list[str] = []
    if readiness_level != "coach_ready":
        guidance.append("Use this run to guide video review first; confirm identities before making selection decisions.")
    if not metrics:
        return guidance or ["No player metrics are available yet."]
    high_speed_leaders = sorted(
        metrics,
        key=lambda item: float(item.get("high_speed_distance_m") or 0.0) if isinstance(item, dict) else 0.0,
        reverse=True,
    )[:3]
    sprint_leaders = sorted(
        metrics,
        key=lambda item: int(item.get("sprint_count") or 0) if isinstance(item, dict) else 0,
        reverse=True,
    )[:3]
    work_rate_leaders = sorted(
        metrics,
        key=lambda item: float(item.get("work_rate_m_per_min") or 0.0) if isinstance(item, dict) else 0.0,
        reverse=True,
    )[:3]
    if high_speed_leaders and isinstance(high_speed_leaders[0], dict):
        if float(high_speed_leaders[0].get("high_speed_distance_m") or 0.0) > 0:
            names = ", ".join(match_tracking_metric_label(item) for item in high_speed_leaders)
            guidance.append(
                f"Review high-speed load for {names}; pair sprint exposure with recovery and hamstring monitoring."
            )
    if sprint_leaders and isinstance(sprint_leaders[0], dict):
        if int(sprint_leaders[0].get("sprint_count") or 0) > 0:
            names = ", ".join(match_tracking_metric_label(item) for item in sprint_leaders)
            guidance.append(f"Inspect repeated-sprint sequences for {names}; check pressing triggers and substitution timing.")
    if work_rate_leaders and isinstance(work_rate_leaders[0], dict):
        if float(work_rate_leaders[0].get("work_rate_m_per_min") or 0.0) > 0:
            names = ", ".join(match_tracking_metric_label(item) for item in work_rate_leaders)
            guidance.append(f"Use work-rate leaders {names} as the first review queue for tactical role load.")
    low_quality = [
        match_tracking_metric_label(item)
        for item in metrics
        if isinstance(item, dict) and float(item.get("tracking_quality_score") or 0.0) < 0.55
    ][:4]
    if low_quality:
        guidance.append(f"Manually review identities for {', '.join(low_quality)} before publishing player reports.")
    pressure_leaders = sorted(
        [item for item in metrics if isinstance(item, dict)],
        key=lambda item: int(item.get("pressure_received_count") or 0),
        reverse=True,
    )[:3]
    if pressure_leaders and int(pressure_leaders[0].get("pressure_received_count") or 0) > 0:
        names = ", ".join(match_tracking_metric_label(item) for item in pressure_leaders)
        guidance.append(f"Review first touch and scanning clips for {names}; they received the most close pressure.")
    runners = sorted(
        [item for item in metrics if isinstance(item, dict)],
        key=lambda item: int(item.get("off_ball_run_count") or 0),
        reverse=True,
    )[:3]
    if runners and int(runners[0].get("off_ball_run_count") or 0) > 0:
        names = ", ".join(match_tracking_metric_label(item) for item in runners)
        guidance.append(f"Use off-ball runs by {names} to review timing, passing lanes, and support angles.")
    return guidance or ["Tracking profile is stable enough for coach review."]


def match_tracking_tactical_guidance(summary: dict[str, object]) -> list[str]:
    shapes = [shape for shape in list(summary.get("team_shape_metrics") or []) if isinstance(shape, dict)]
    phases = [phase for phase in list(summary.get("team_phase_metrics") or []) if isinstance(phase, dict)]
    if not shapes and not phases:
        return ["Capture simultaneous player positions to derive team shape and formation guidance."]
    guidance: list[str] = []
    for shape in shapes[:4]:
        team = str(shape.get("team_label") or "team")
        hint = str(shape.get("shape_hint") or "")
        width = float(shape.get("average_width_percent") or 0.0)
        depth = float(shape.get("average_depth_percent") or 0.0)
        compactness = float(shape.get("average_compactness_score") or 0.0)
        centroid_x = float(shape.get("average_centroid_x_percent") or 0.0)
        if hint == "high_press_shape":
            guidance.append(f"{team} is holding a high press shape; review recovery cover behind the first line.")
        elif hint == "deep_block_shape":
            guidance.append(f"{team} is sitting deep; review outlet distances and transition support.")
        elif hint == "stretched_shape" or compactness < 0.6:
            guidance.append(f"{team} is stretched across width/depth; tighten distances before pressing triggers.")
        elif hint == "wide_flat_line":
            guidance.append(f"{team} has a wide flat line; inspect weak-side protection and central gaps.")
        elif hint == "vertical_stagger":
            guidance.append(f"{team} has strong vertical stagger; check support angles between lines.")
        else:
            guidance.append(
                f"{team} shape is compact around x={round(centroid_x)}%, width={round(width)}%, depth={round(depth)}%."
            )
    for phase in phases[:4]:
        team = str(phase.get("team_label") or "team")
        hint = str(phase.get("phase_hint") or "")
        pressure_count = int(phase.get("pressure_event_count") or 0)
        off_ball = int(phase.get("off_ball_run_count") or 0)
        attacking = float(phase.get("attacking_third_percent") or 0.0)
        if hint == "active_pressing":
            guidance.append(f"{team} created {pressure_count} pressure event(s); review press cover and second-ball shape.")
        elif hint == "territorial_dominance":
            guidance.append(f"{team} spent {round(attacking)}% of samples in the attacking third; review chance creation quality.")
        elif hint == "deep_defensive_phase":
            guidance.append(f"{team} spent extended time deep; rehearse outlet runs and first pass after regain.")
        elif hint == "off_ball_running_phase":
            guidance.append(f"{team} generated {off_ball} off-ball run(s); check whether pass timing matched movement.")
    return guidance


def match_tracking_metric_label(metric: object) -> str:
    item = metric if isinstance(metric, dict) else {}
    label = item.get("player_label") or item.get("track_id") or "tracked player"
    jersey = item.get("jersey_number")
    return f"{label} #{jersey}" if jersey else str(label)


async def latest_match_tracking_run(db: AsyncSession, video_asset_id: UUID) -> PerformanceMatchTrackingRun | None:
    return (
        await db.scalars(
            select(PerformanceMatchTrackingRun)
            .where(PerformanceMatchTrackingRun.video_asset_id == video_asset_id)
            .order_by(PerformanceMatchTrackingRun.created_at.desc())
            .limit(1)
        )
    ).first()


async def latest_opposition_scouting_report(db: AsyncSession, video_asset_id: UUID) -> OppositionScoutingReport | None:
    return (
        await db.scalars(
            select(OppositionScoutingReport)
            .where(OppositionScoutingReport.video_asset_id == video_asset_id)
            .order_by(OppositionScoutingReport.generated_at.desc())
            .limit(1)
        )
    ).first()


async def generate_highlight_clips_from_match(
    db: AsyncSession,
    video_asset: OppositionScoutingVideoAsset,
    tracking_run: PerformanceMatchTrackingRun | None,
    report: OppositionScoutingReport | None,
    *,
    target_duration_seconds: float,
    audience: str,
) -> list[dict[str, object]]:
    clips: list[dict[str, object]] = []
    if tracking_run is not None:
        tracking = await match_tracking_run_read(db, tracking_run)
        player_metrics = list(tracking.get("player_metrics") or [])
        clips.extend(highlight_clips_from_player_metrics(player_metrics, target_duration_seconds, audience))
        guidance = list(tracking.get("coaching_guidance") or [])
        if guidance and len(clips) < 8:
            clips.append(
                highlight_clip(
                    title="Coach guidance sequence",
                    start_seconds=0,
                    duration_seconds=min(18.0, target_duration_seconds / 4),
                    category="coach_guidance",
                    confidence=float(tracking.get("tracking_quality_score") or 0.65),
                    evidence=str(guidance[0]),
                    coaching_note="Use this sequence as the opening review clip before player-specific moments.",
                    tags=["coach_guidance", "tracking"],
                )
            )
    if report is not None:
        clips.extend(highlight_clips_from_scouting_report(report, len(clips), target_duration_seconds))
    if not clips:
        clips.append(
            highlight_clip(
                title=f"{video_asset.opponent_name} context clip",
                start_seconds=0,
                duration_seconds=min(30.0, target_duration_seconds),
                category="context",
                confidence=0.55,
                evidence=video_asset.analysis_focus or video_asset.match_context or "Uploaded match footage is ready for review.",
                coaching_note="Start with a manual review pass because no tracking run or scouting report is available yet.",
                tags=["context", video_asset.sport],
            )
        )
    return trim_highlight_clips(clips, target_duration_seconds)


def highlight_clips_from_player_metrics(
    player_metrics: list[object],
    target_duration_seconds: float,
    audience: str,
) -> list[dict[str, object]]:
    metrics = [metric for metric in player_metrics if isinstance(metric, dict)]
    clips: list[dict[str, object]] = []
    for index, metric in enumerate(
        sorted(metrics, key=lambda item: float(item.get("high_speed_distance_m") or 0.0), reverse=True)[:3]
    ):
        if float(metric.get("high_speed_distance_m") or 0.0) <= 0:
            continue
        clips.append(
            highlight_clip(
                title=f"{match_tracking_metric_label(metric)} high-speed run",
                start_seconds=index * 18,
                duration_seconds=14,
                category="high_speed_run",
                confidence=float(metric.get("tracking_quality_score") or 0.65),
                evidence=(
                    f"{metric.get('high_speed_distance_m')}m high-speed work, "
                    f"max {metric.get('max_speed_mps')} m/s."
                ),
                coaching_note="Show acceleration, body shape, and recovery after the run.",
                tags=["speed", "player_load", audience],
                player_label=str(metric.get("player_label") or metric.get("track_id") or ""),
                team_label=metric.get("team_label"),
                jersey_number=metric.get("jersey_number"),
            )
        )
    for index, metric in enumerate(
        sorted(metrics, key=lambda item: int(item.get("sprint_count") or 0), reverse=True)[:2]
    ):
        if int(metric.get("sprint_count") or 0) <= 0:
            continue
        clips.append(
            highlight_clip(
                title=f"{match_tracking_metric_label(metric)} repeated sprint",
                start_seconds=54 + index * 18,
                duration_seconds=16,
                category="repeated_sprint",
                confidence=float(metric.get("tracking_quality_score") or 0.65),
                evidence=f"{metric.get('sprint_count')} sprint action(s) in the tracked segment.",
                coaching_note="Pair this with substitution and recovery planning.",
                tags=["sprint", "fatigue", audience],
                player_label=str(metric.get("player_label") or metric.get("track_id") or ""),
                team_label=metric.get("team_label"),
                jersey_number=metric.get("jersey_number"),
            )
        )
    if target_duration_seconds >= 60:
        for index, metric in enumerate(
            sorted(metrics, key=lambda item: float(item.get("work_rate_m_per_min") or 0.0), reverse=True)[:2]
        ):
            if float(metric.get("work_rate_m_per_min") or 0.0) <= 0:
                continue
            clips.append(
                highlight_clip(
                    title=f"{match_tracking_metric_label(metric)} work-rate sequence",
                    start_seconds=90 + index * 18,
                    duration_seconds=15,
                    category="work_rate",
                    confidence=float(metric.get("tracking_quality_score") or 0.65),
                    evidence=f"{metric.get('work_rate_m_per_min')} m/min work rate in the tracked window.",
                    coaching_note="Use this clip to compare role load against tactical expectation.",
                    tags=["work_rate", "tactical_role", audience],
                    player_label=str(metric.get("player_label") or metric.get("track_id") or ""),
                    team_label=metric.get("team_label"),
                    jersey_number=metric.get("jersey_number"),
                )
            )
    return clips


def highlight_clips_from_scouting_report(
    report: OppositionScoutingReport,
    existing_count: int,
    target_duration_seconds: float,
) -> list[dict[str, object]]:
    if existing_count >= 8 or target_duration_seconds < 45:
        return []
    findings: list[dict[str, str]] = []
    for raw in [report.weaknesses_json, report.threats_json, report.recommendations_json, report.set_pieces_json]:
        findings.extend(decode_scouting_findings(raw))
    clips: list[dict[str, object]] = []
    for index, finding in enumerate(findings[: max(0, 8 - existing_count)]):
        clips.append(
            highlight_clip(
                title=finding.get("title") or f"Scouting highlight {index + 1}",
                start_seconds=126 + index * 16,
                duration_seconds=14,
                category=finding.get("category") or "scouting",
                confidence=report.confidence,
                evidence=finding.get("evidence") or report.tactical_summary,
                coaching_note=finding.get("recommendation") or "Review this pattern with the match-plan group.",
                tags=["scouting", str(finding.get("severity") or "medium"), report.formation_detected or "shape"],
            )
        )
    return clips


def highlight_clip(
    *,
    title: str,
    start_seconds: float,
    duration_seconds: float,
    category: str,
    confidence: float,
    evidence: str,
    coaching_note: str,
    tags: list[str],
    player_label: str | None = None,
    team_label: object | None = None,
    jersey_number: object | None = None,
) -> dict[str, object]:
    return {
        "title": title[:180],
        "start_seconds": round(max(start_seconds, 0.0), 2),
        "end_seconds": round(max(start_seconds, 0.0) + max(duration_seconds, 1.0), 2),
        "duration_seconds": round(max(duration_seconds, 1.0), 2),
        "category": category,
        "player_label": player_label or None,
        "team_label": str(team_label) if team_label else None,
        "jersey_number": str(jersey_number) if jersey_number else None,
        "confidence": round(max(0.0, min(confidence, 1.0)), 3),
        "evidence": evidence,
        "coaching_note": coaching_note,
        "tags": sorted({tag.strip().lower() for tag in tags if tag and tag.strip()}),
    }


def trim_highlight_clips(clips: list[dict[str, object]], target_duration_seconds: float) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    total = 0.0
    for clip in sorted(clips, key=lambda item: float(item.get("confidence") or 0.0), reverse=True):
        duration = float(clip["duration_seconds"])
        if selected and total + duration > target_duration_seconds:
            continue
        selected.append(clip)
        total += duration
        if len(selected) >= 10 or total >= target_duration_seconds:
            break
    return sorted(selected, key=lambda item: float(item["start_seconds"]))


def highlight_reel_distribution(channels: list[str], audience: str, clips: list[dict[str, object]]) -> dict[str, object]:
    channel_values = [channel.strip().lower() for channel in channels if channel.strip()] or ["coach_review"]
    return {
        "channels": channel_values,
        "audience": audience.strip().lower(),
        "clip_count": len(clips),
        "share_policy": "guardian_approval_required" if audience in {"parent", "family", "scout"} else "team_internal",
        "export_formats": ["timeline_json", "mp4_edit_decision_list", "social_caption_pack"],
        "caption": f"{len(clips)} AI-selected highlight moments for {audience.strip().lower()} review.",
    }


def highlight_reel_read(reel: PerformanceHighlightReel) -> dict[str, object]:
    return {
        "id": reel.id,
        "organization_id": reel.organization_id,
        "video_asset_id": reel.video_asset_id,
        "tracking_run_id": reel.tracking_run_id,
        "athlete_profile_id": reel.athlete_profile_id,
        "created_by_person_id": reel.created_by_person_id,
        "title": reel.title,
        "audience": reel.audience,
        "purpose": reel.purpose,
        "model_policy": reel.model_policy,
        "status": reel.status,
        "clip_count": reel.clip_count,
        "duration_seconds": reel.duration_seconds,
        "clips": decode_json_list(reel.clips_json),
        "tags": decode_string_list(reel.tags_json),
        "distribution": decode_json_dict(reel.distribution_json),
        "branding": decode_json_dict(reel.branding_json) if reel.branding_json else None,
        "generated_at": reel.generated_at,
        "created_at": reel.created_at,
    }


def highlight_reel_export_read(export: PerformanceHighlightReelExport) -> dict[str, object]:
    return {
        "id": export.id,
        "organization_id": export.organization_id,
        "highlight_reel_id": export.highlight_reel_id,
        "video_asset_id": export.video_asset_id,
        "tracking_run_id": export.tracking_run_id,
        "requested_by_person_id": export.requested_by_person_id,
        "export_format": export.export_format,
        "status": export.status,
        "renderer_policy": export.renderer_policy,
        "filename": export.filename,
        "content_type": export.content_type,
        "storage_url": export.storage_url,
        "checksum": export.checksum,
        "size_bytes": export.size_bytes,
        "message": export.message,
        "manifest": decode_json_dict(export.manifest_json),
        "generated_at": export.generated_at,
        "created_at": export.created_at,
    }


async def get_performance_highlight_reel(db: AsyncSession, highlight_reel_id: UUID) -> PerformanceHighlightReel:
    reel = await db.get(PerformanceHighlightReel, highlight_reel_id)
    if reel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Highlight reel not found")
    return reel


async def get_performance_highlight_reel_export(
    db: AsyncSession,
    export_id: UUID,
) -> PerformanceHighlightReelExport:
    export = await db.get(PerformanceHighlightReelExport, export_id)
    if export is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Highlight reel export not found")
    return export


def normalize_highlight_export_format(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "json": "timeline_json",
        "timeline": "timeline_json",
        "edl": "mp4_edit_decision_list",
        "mp4": "mp4_edit_decision_list",
        "mp4_stub": "mp4_edit_decision_list",
        "caption": "social_caption_pack",
        "captions": "social_caption_pack",
        "caption_pack": "social_caption_pack",
        "social": "social_caption_pack",
    }
    normalized = aliases.get(normalized, normalized)
    allowed = {"timeline_json", "mp4_edit_decision_list", "social_caption_pack"}
    if normalized not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported highlight export format",
        )
    return normalized


def build_highlight_reel_export_artifact(
    reel: PerformanceHighlightReel,
    video_asset: OppositionScoutingVideoAsset,
    *,
    export_format: str,
    delivery_channel: str,
    include_branding: bool,
    notes: str | None,
) -> dict[str, object]:
    reel_payload = highlight_reel_read(reel)
    base_manifest: dict[str, object] = {
        "render_policy": "afrolete-highlight-export-v1",
        "export_format": export_format,
        "delivery_channel": delivery_channel.strip().lower(),
        "source_video": {
            "id": str(video_asset.id),
            "filename": video_asset.filename,
            "storage_url": video_asset.storage_url,
            "video_uri": video_asset.video_uri,
            "content_type": video_asset.content_type,
            "checksum": video_asset.checksum,
            "sport": video_asset.sport,
            "opponent_name": video_asset.opponent_name,
            "match_context": video_asset.match_context,
        },
        "reel": reel_payload,
        "clips": reel_payload["clips"],
        "distribution": reel_payload["distribution"],
        "branding": reel_payload["branding"] if include_branding else None,
        "operator_notes": notes,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    safe_title = safe_highlight_export_filename(reel.title)
    if export_format == "timeline_json":
        content = json.dumps(base_manifest, indent=2, default=str).encode()
        return {
            "filename": f"{safe_title}-timeline.json",
            "content_type": "application/json",
            "content": content,
            "status": "rendered",
            "renderer_policy": "afrolete-highlight-export-v1",
            "message": "Timeline JSON is ready for review, archive, or renderer handoff.",
            "manifest": base_manifest,
        }
    if export_format == "mp4_edit_decision_list":
        edit_decisions = [
            {
                "clip_number": index,
                "source_in_seconds": clip.get("start_seconds"),
                "source_out_seconds": clip.get("end_seconds"),
                "timeline_in_seconds": round(sum(float(item.get("duration_seconds") or 0.0) for item in base_manifest["clips"][: index - 1]), 2),
                "duration_seconds": clip.get("duration_seconds"),
                "title": clip.get("title"),
                "overlay_note": clip.get("coaching_note"),
                "tags": clip.get("tags"),
            }
            for index, clip in enumerate(base_manifest["clips"], start=1)
            if isinstance(clip, dict)
        ]
        manifest = {
            **base_manifest,
            "edit_decisions": edit_decisions,
            "renderer_status": "needs_renderer",
            "ffmpeg_policy": "Render source clips in order, preserve audio, add title/coach-note overlays where allowed.",
        }
        content = json.dumps(manifest, indent=2, default=str).encode()
        return {
            "filename": f"{safe_title}-edl.json",
            "content_type": "application/json",
            "content": content,
            "status": "needs_renderer",
            "renderer_policy": "afrolete-highlight-edl-v1",
            "message": "Edit decision list is ready; MP4 clipping/rendering worker must render final video.",
            "manifest": manifest,
        }
    caption_lines = [
        f"# {reel.title}",
        "",
        str(base_manifest["distribution"].get("caption") if isinstance(base_manifest["distribution"], dict) else ""),
        "",
        f"Audience: {reel.audience}",
        f"Purpose: {reel.purpose}",
        f"Delivery: {delivery_channel.strip().lower()}",
        "",
        "## Clip Captions",
    ]
    for index, clip in enumerate(base_manifest["clips"], start=1):
        if not isinstance(clip, dict):
            continue
        caption_lines.extend(
            [
                "",
                f"{index}. {clip.get('title')}",
                f"   - Window: {clip.get('start_seconds')}s-{clip.get('end_seconds')}s",
                f"   - Evidence: {clip.get('evidence')}",
                f"   - Coach note: {clip.get('coaching_note')}",
            ]
        )
    if notes:
        caption_lines.extend(["", "## Operator Notes", notes])
    content = "\n".join(caption_lines).encode()
    manifest = {**base_manifest, "caption_count": len(base_manifest["clips"])}
    return {
        "filename": f"{safe_title}-captions.md",
        "content_type": "text/markdown; charset=utf-8",
        "content": content,
        "status": "rendered",
        "renderer_policy": "afrolete-highlight-caption-pack-v1",
        "message": "Caption pack is ready for social, family, scout, or coach distribution review.",
        "manifest": manifest,
    }


def render_highlight_reel_mp4_artifact(
    source_export: PerformanceHighlightReelExport,
    reel: PerformanceHighlightReel,
    *,
    source_content: bytes,
    ffmpeg_path: str,
) -> dict[str, object]:
    manifest = decode_json_dict(source_export.manifest_json)
    edit_decisions = [item for item in manifest.get("edit_decisions", []) if isinstance(item, dict)]
    if not edit_decisions:
        return build_highlight_reel_render_failure_artifact(
            source_export,
            reason="Edit decision list has no clips to render",
        )
    safe_title = safe_highlight_export_filename(reel.title)
    try:
        with tempfile.TemporaryDirectory() as temporary_dir:
            work_dir = Path(temporary_dir)
            source_path = work_dir / "source.mp4"
            source_path.write_bytes(source_content)
            segment_paths: list[Path] = []
            command_results: list[dict[str, object]] = []
            for index, decision in enumerate(edit_decisions, start=1):
                start_seconds = max(float(decision.get("source_in_seconds") or 0), 0.0)
                end_seconds = decision.get("source_out_seconds")
                duration_seconds = decision.get("duration_seconds")
                if duration_seconds is None and end_seconds is not None:
                    duration_seconds = max(float(end_seconds) - start_seconds, 0.25)
                duration = max(float(duration_seconds or 1.0), 0.25)
                segment_path = work_dir / f"segment-{index:03d}.mp4"
                command = [
                    ffmpeg_path,
                    "-y",
                    "-ss",
                    f"{start_seconds:.3f}",
                    "-t",
                    f"{duration:.3f}",
                    "-i",
                    str(source_path),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-c:a",
                    "aac",
                    "-movflags",
                    "+faststart",
                    str(segment_path),
                ]
                result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
                command_results.append(
                    {
                        "clip_number": index,
                        "return_code": result.returncode,
                        "stderr_tail": result.stderr[-500:] if result.stderr else "",
                    }
                )
                if result.returncode != 0 or not segment_path.is_file():
                    return build_highlight_reel_render_failure_artifact(
                        source_export,
                        reason=f"ffmpeg failed while rendering clip {index}",
                        command_results=command_results,
                    )
                segment_paths.append(segment_path)
            concat_path = work_dir / "concat.txt"
            concat_path.write_text(
                "\n".join(f"file '{path.as_posix()}'" for path in segment_paths),
                encoding="utf-8",
            )
            output_path = work_dir / f"{safe_title}-render.mp4"
            concat_command = [
                ffmpeg_path,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_path),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
            concat_result = subprocess.run(
                concat_command,
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
            command_results.append(
                {
                    "clip_number": "concat",
                    "return_code": concat_result.returncode,
                    "stderr_tail": concat_result.stderr[-500:] if concat_result.stderr else "",
                }
            )
            if concat_result.returncode != 0 or not output_path.is_file():
                return build_highlight_reel_render_failure_artifact(
                    source_export,
                    reason="ffmpeg failed while joining highlight clips",
                    command_results=command_results,
                )
            rendered_content = output_path.read_bytes()
    except (OSError, subprocess.SubprocessError) as exc:
        return build_highlight_reel_render_failure_artifact(source_export, reason=str(exc))
    rendered_manifest = {
        "render_policy": "afrolete-ffmpeg-highlight-renderer-v1",
        "renderer_status": "rendered",
        "source_export_id": str(source_export.id),
        "highlight_reel_id": str(source_export.highlight_reel_id),
        "video_asset_id": str(source_export.video_asset_id),
        "clip_count": len(edit_decisions),
        "source_manifest_checksum": source_export.checksum,
        "generated_at": datetime.now(UTC).isoformat(),
        "ffmpeg_path": ffmpeg_path,
    }
    return {
        "export_format": "mp4_render",
        "filename": f"{safe_title}-render.mp4",
        "content_type": "video/mp4",
        "content": rendered_content,
        "status": "rendered",
        "renderer_policy": "afrolete-ffmpeg-highlight-renderer-v1",
        "message": "Rendered MP4 highlight reel is ready for coach review and controlled sharing.",
        "manifest": rendered_manifest,
    }


def build_highlight_reel_render_failure_artifact(
    source_export: PerformanceHighlightReelExport,
    *,
    reason: str,
    command_results: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    manifest = {
        "render_policy": "afrolete-ffmpeg-highlight-renderer-v1",
        "renderer_status": "failed",
        "source_export_id": str(source_export.id),
        "highlight_reel_id": str(source_export.highlight_reel_id),
        "video_asset_id": str(source_export.video_asset_id),
        "reason": reason,
        "command_results": command_results or [],
        "generated_at": datetime.now(UTC).isoformat(),
    }
    content = json.dumps(manifest, indent=2, default=str).encode()
    safe_source = safe_highlight_export_filename(source_export.filename.rsplit(".", 1)[0])
    return {
        "export_format": "mp4_render",
        "filename": f"{safe_source}-render-failed.json",
        "content_type": "application/json",
        "content": content,
        "status": "failed",
        "renderer_policy": "afrolete-ffmpeg-highlight-renderer-v1",
        "message": f"MP4 render failed: {reason}",
        "manifest": manifest,
    }


def safe_highlight_export_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower()).strip("-")
    return safe[:120] or "highlight-reel"


def decode_json_list(value: str | None) -> list[dict[str, object]]:
    if not value:
        return []
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []


def decode_json_dict(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


async def get_match_tracking_run(db: AsyncSession, tracking_run_id: UUID) -> PerformanceMatchTrackingRun:
    run = await db.get(PerformanceMatchTrackingRun, tracking_run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match tracking run not found")
    return run


async def get_performance_match_analysis_report(
    db: AsyncSession,
    report_id: UUID,
) -> PerformanceMatchAnalysisReport:
    report = await db.get(PerformanceMatchAnalysisReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match analysis report not found")
    return report


def cleaned_optional_text(value: str | None, *, fallback: str | None = None) -> str | None:
    if value is None:
        return fallback
    cleaned = value.strip()
    return cleaned or None


def match_tracking_identity_snapshot(samples: list[PerformanceMatchTrackingSample]) -> dict[str, object]:
    person_ids = sorted({str(sample.person_id) for sample in samples if sample.person_id})
    return {
        "sample_count": len(samples),
        "person_ids": person_ids,
        "team_labels": sorted({sample.team_label for sample in samples if sample.team_label}),
        "player_labels": sorted({sample.player_label for sample in samples if sample.player_label}),
        "jersey_numbers": sorted({sample.jersey_number for sample in samples if sample.jersey_number}),
        "first_timestamp_seconds": samples[0].timestamp_seconds if samples else None,
        "last_timestamp_seconds": samples[-1].timestamp_seconds if samples else None,
    }


def match_tracking_identity_review_read(review: PerformanceMatchTrackingIdentityReview) -> dict[str, object]:
    return {
        "id": review.id,
        "organization_id": review.organization_id,
        "tracking_run_id": review.tracking_run_id,
        "video_asset_id": review.video_asset_id,
        "track_id": review.track_id,
        "reviewer_person_id": review.reviewer_person_id,
        "person_id": review.person_id,
        "team_label": review.team_label,
        "player_label": review.player_label,
        "jersey_number": review.jersey_number,
        "decision": review.decision,
        "sample_count": review.sample_count,
        "before": decode_json_dict(review.before_json),
        "after": decode_json_dict(review.after_json),
        "notes": review.notes,
        "reviewed_at": review.reviewed_at,
        "created_at": review.created_at,
    }


async def recompute_match_tracking_run_summary(db: AsyncSession, run: PerformanceMatchTrackingRun) -> None:
    samples = list(
        (
            await db.scalars(
                select(PerformanceMatchTrackingSample)
                .where(PerformanceMatchTrackingSample.tracking_run_id == run.id)
                .order_by(
                    PerformanceMatchTrackingSample.timestamp_seconds,
                    PerformanceMatchTrackingSample.track_id,
                )
            )
        ).all()
    )
    sample_payloads = [match_tracking_sample_read(sample) for sample in samples]
    summary = summarize_match_tracking_samples(sample_payloads)
    previous_summary = decode_json_dict(run.summary_json)
    warnings = previous_summary.get("warnings")
    if isinstance(warnings, list):
        summary["warnings"] = warnings
    summary["identity_review_count"] = int(previous_summary.get("identity_review_count") or 0) + 1
    summary["identity_reviewed_at"] = datetime.now(UTC).isoformat()
    calibration = await db.get(PerformanceMatchPitchCalibration, run.calibration_id) if run.calibration_id else None
    if calibration is not None:
        summary["calibration_id"] = str(calibration.id)
        summary["calibration_quality_score"] = calibration.quality_score
    summary = enrich_match_tracking_summary(
        summary,
        calibration=calibration,
        source_provider=run.source_provider,
        model_policy=run.model_policy,
    )
    run.sample_count = len(samples)
    run.player_count = len(summary["player_metrics"])
    run.total_distance_m = float(summary["total_distance_m"])
    run.max_speed_mps = float(summary["max_speed_mps"])
    run.high_speed_distance_m = float(summary["high_speed_distance_m"])
    run.sprint_count = int(summary["sprint_count"])
    run.summary_json = json.dumps(summary, default=str)
    run.completed_at = datetime.now(UTC)


async def match_tracking_run_read(db: AsyncSession, run: PerformanceMatchTrackingRun) -> dict[str, object]:
    samples = list(
        (
            await db.scalars(
                select(PerformanceMatchTrackingSample)
                .where(PerformanceMatchTrackingSample.tracking_run_id == run.id)
                .order_by(
                    PerformanceMatchTrackingSample.timestamp_seconds,
                    PerformanceMatchTrackingSample.track_id,
                )
                .limit(500)
            )
        ).all()
    )
    try:
        summary = json.loads(run.summary_json)
    except json.JSONDecodeError:
        summary = {}
    calibration = await db.get(PerformanceMatchPitchCalibration, run.calibration_id) if run.calibration_id else None
    return {
        "id": run.id,
        "organization_id": run.organization_id,
        "video_asset_id": run.video_asset_id,
        "calibration_id": run.calibration_id,
        "team_id": run.team_id,
        "event_id": run.event_id,
        "created_by_person_id": run.created_by_person_id,
        "source_provider": run.source_provider,
        "model_policy": run.model_policy,
        "status": run.status,
        "pitch_length_m": run.pitch_length_m,
        "pitch_width_m": run.pitch_width_m,
        "sample_count": run.sample_count,
        "player_count": run.player_count,
        "total_distance_m": run.total_distance_m,
        "max_speed_mps": run.max_speed_mps,
        "high_speed_distance_m": run.high_speed_distance_m,
        "sprint_count": run.sprint_count,
        "tracking_quality_score": summary.get("tracking_quality_score", 0.0),
        "identity_continuity_score": summary.get("identity_continuity_score", 0.0),
        "calibration_quality_score": summary.get("calibration_quality_score", 0.0),
        "readiness_level": summary.get("readiness_level", "unknown"),
        "quality_warnings": summary.get("quality_warnings", []),
        "coaching_guidance": summary.get("coaching_guidance", []),
        "tactical_guidance": summary.get("tactical_guidance", []),
        "team_shape_metrics": summary.get("team_shape_metrics", []),
        "team_phase_metrics": summary.get("team_phase_metrics", []),
        "pressure_events": summary.get("pressure_events", []),
        "match_phase_snapshots": summary.get("match_phase_snapshots", []),
        "ball_tracking_metrics": summary.get("ball_tracking_metrics", {}),
        "possession_estimates": summary.get("possession_estimates", []),
        "ball_action_events": summary.get("ball_action_events", []),
        "recognized_action_events": summary.get("recognized_action_events", []),
        "action_recognition_metrics": summary.get("action_recognition_metrics", {}),
        "shot_events": summary.get("shot_events", []),
        "pass_network": summary.get("pass_network", []),
        "pass_type_metrics": summary.get("pass_type_metrics", []),
        "defensive_action_events": summary.get("defensive_action_events", []),
        "chance_creation_metrics": summary.get("chance_creation_metrics", {}),
        "formation_snapshots": summary.get("formation_snapshots", []),
        "player_metrics": summary.get("player_metrics", []),
        "samples": [match_tracking_sample_read(sample) for sample in samples],
        "calibration": match_pitch_calibration_read(calibration) if calibration is not None else None,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }


def match_tracking_sample_read(sample: PerformanceMatchTrackingSample) -> dict[str, object]:
    return {
        "id": sample.id,
        "organization_id": sample.organization_id,
        "tracking_run_id": sample.tracking_run_id,
        "video_asset_id": sample.video_asset_id,
        "track_id": sample.track_id,
        "person_id": sample.person_id,
        "team_label": sample.team_label,
        "player_label": sample.player_label,
        "jersey_number": sample.jersey_number,
        "frame_index": sample.frame_index,
        "timestamp_seconds": sample.timestamp_seconds,
        "x_percent": sample.x_percent,
        "y_percent": sample.y_percent,
        "x_meters": sample.x_meters,
        "y_meters": sample.y_meters,
        "speed_mps": sample.speed_mps,
        "confidence": sample.confidence,
        "source": sample.source,
    }


def extract_match_tracking_samples_from_video_content(
    content: bytes,
    *,
    pitch_length_m: float,
    pitch_width_m: float,
    max_frames: int,
    sample_every_seconds: float,
    min_detection_confidence: float,
) -> dict[str, object]:
    try:
        import cv2
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenCV match-tracking worker dependencies are not installed",
        ) from exc
    with tempfile.NamedTemporaryFile(suffix=".mp4") as handle:
        handle.write(content)
        handle.flush()
        capture = cv2.VideoCapture(handle.name)
        if not capture.isOpened():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Video could not be decoded")
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 25.0)
        width = float(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 1.0)
        height = float(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1.0)
        step = max(int(fps * sample_every_seconds), 1)
        subtractor = cv2.createBackgroundSubtractorMOG2(history=120, varThreshold=36, detectShadows=False)
        tracks: dict[str, tuple[float, float]] = {}
        ball_track: tuple[float, float] | None = None
        samples: list[dict[str, object]] = []
        decoded_frames = 0
        processed_frames = 0
        frame_index = 0
        while processed_frames < max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            decoded_frames += 1
            if frame_index % step != 0:
                frame_index += 1
                continue
            mask = subtractor.apply(frame)
            mask = cv2.medianBlur(mask, 5)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            detections: list[dict[str, object]] = []
            ball_candidates: list[tuple[float, float, float]] = []
            frame_area = max(width * height, 1.0)
            for contour in contours:
                area = float(cv2.contourArea(contour))
                x, y, w, h = cv2.boundingRect(contour)
                perimeter = float(cv2.arcLength(contour, True))
                contour_kind = match_tracking_contour_kind(
                    area=area,
                    width=float(w),
                    height=float(h),
                    perimeter=perimeter,
                    frame_area=frame_area,
                    min_detection_confidence=min_detection_confidence,
                )
                if contour_kind is None:
                    continue
                kind, confidence = contour_kind
                if kind == "ball":
                    ball_candidates.append((x + w / 2, y + h / 2, confidence))
                else:
                    detections.append(
                        {
                            "x": x + w / 2,
                            "y": y + h,
                            "confidence": confidence,
                            "jersey_color_rgb": match_tracking_jersey_color_signature(frame, x, y, w, h),
                        }
                    )
            selected_ball = select_match_ball_candidate(ball_candidates, ball_track)
            if selected_ball is not None:
                ball_track = (selected_ball[0], selected_ball[1])
                samples.append(
                    {
                        "track_id": "ball",
                        "team_label": "ball",
                        "player_label": "Ball",
                        "jersey_number": None,
                        "frame_index": frame_index,
                        "timestamp_seconds": frame_index / fps,
                        "x_percent": selected_ball[0] / width * 100,
                        "y_percent": selected_ball[1] / height * 100,
                        "confidence": selected_ball[2],
                        "source": "opencv_ball_tracker",
                    }
                )
            for detection in detections[:22]:
                detection_x = float(detection["x"])
                detection_y = float(detection["y"])
                track_id = nearest_match_track_id(tracks, detection_x, detection_y)
                tracks[track_id] = (detection_x, detection_y)
                x_percent = detection_x / width * 100
                y_percent = detection_y / height * 100
                samples.append(
                    {
                        "track_id": track_id,
                        "team_label": None,
                        "player_label": f"Track {track_id}",
                        "jersey_number": None,
                        "frame_index": frame_index,
                        "timestamp_seconds": frame_index / fps,
                        "x_percent": x_percent,
                        "y_percent": y_percent,
                        "confidence": detection["confidence"],
                        "source": "opencv_motion_tracker",
                        "jersey_color_rgb": detection.get("jersey_color_rgb"),
                    }
                )
            processed_frames += 1
            frame_index += 1
    samples = assign_match_tracking_team_labels(samples)
    team_labels = sorted(
        {
            str(sample["team_label"])
            for sample in samples
            if sample.get("team_label") not in {None, "ball"}
        }
    )
    warnings = [
        "No pitch homography calibration applied; coordinates are frame-normalized estimates.",
        "Ball tracks are best-effort OpenCV contour estimates and require coach review.",
    ]
    if team_labels:
        warnings.append(
            "Team labels are jersey-color cluster estimates and should be confirmed with identity review."
        )
    return {
        "samples": samples,
        "decoded_frame_count": decoded_frames,
        "processed_frame_count": processed_frames,
        "source_provider": "opencv_motion_tracker",
        "model_policy": "opencv-background-subtraction-match-tracker-v3",
        "warnings": warnings,
    }


def nearest_match_track_id(tracks: dict[str, tuple[float, float]], x: float, y: float) -> str:
    if not tracks:
        return "1"
    nearest_id = min(tracks, key=lambda track_id: math.dist(tracks[track_id], (x, y)))
    if math.dist(tracks[nearest_id], (x, y)) <= 80:
        return nearest_id
    return str(len(tracks) + 1)


def match_tracking_jersey_color_signature(
    frame: object,
    x: int,
    y: int,
    width: int,
    height: int,
) -> tuple[int, int, int] | None:
    if width <= 0 or height <= 0:
        return None
    frame_height = int(getattr(frame, "shape", [0, 0])[0] or 0)
    frame_width = int(getattr(frame, "shape", [0, 0])[1] or 0)
    if frame_height <= 0 or frame_width <= 0:
        return None
    x0 = max(0, min(frame_width, int(x + width * 0.25)))
    x1 = max(0, min(frame_width, int(x + width * 0.75)))
    y0 = max(0, min(frame_height, int(y + height * 0.18)))
    y1 = max(0, min(frame_height, int(y + height * 0.58)))
    if x1 <= x0 or y1 <= y0:
        return None
    crop = frame[y0:y1, x0:x1]
    if getattr(crop, "size", 0) == 0:
        return None
    try:
        pixels = crop.reshape(-1, 3)
        bright_pixels = pixels[pixels.sum(axis=1) > 60]
        if getattr(bright_pixels, "size", 0) > 0:
            pixels = bright_pixels
        bgr_mean = pixels.mean(axis=0)
    except (AttributeError, ValueError):
        return None
    return (
        int(round(float(bgr_mean[2]))),
        int(round(float(bgr_mean[1]))),
        int(round(float(bgr_mean[0]))),
    )


def assign_match_tracking_team_labels(samples: list[dict[str, object]]) -> list[dict[str, object]]:
    track_colors: dict[str, list[tuple[float, float, float]]] = {}
    for sample in samples:
        if is_match_ball_tracking_row(sample):
            continue
        color = sample.get("jersey_color_rgb")
        if not isinstance(color, (list, tuple)) or len(color) != 3:
            continue
        try:
            rgb = (float(color[0]), float(color[1]), float(color[2]))
        except (TypeError, ValueError):
            continue
        track_colors.setdefault(str(sample.get("track_id")), []).append(rgb)
    if len(track_colors) < 2:
        return samples
    profiles = {
        track_id: (
            sum(color[0] for color in colors) / len(colors),
            sum(color[1] for color in colors) / len(colors),
            sum(color[2] for color in colors) / len(colors),
        )
        for track_id, colors in track_colors.items()
        if colors
    }
    if len(profiles) < 2:
        return samples
    track_ids = sorted(profiles)
    seed_a, seed_b = max(
        ((left, right) for index, left in enumerate(track_ids) for right in track_ids[index + 1 :]),
        key=lambda pair: math.dist(profiles[pair[0]], profiles[pair[1]]),
    )
    if math.dist(profiles[seed_a], profiles[seed_b]) < 45:
        return samples
    labels_by_track: dict[str, str] = {}
    for track_id, color in profiles.items():
        distance_a = math.dist(color, profiles[seed_a])
        distance_b = math.dist(color, profiles[seed_b])
        labels_by_track[track_id] = "Team A" if distance_a <= distance_b else "Team B"
    for sample in samples:
        track_id = str(sample.get("track_id"))
        team_label = labels_by_track.get(track_id)
        if team_label and not sample.get("team_label"):
            sample["team_label"] = team_label
            sample["player_label"] = f"{team_label} Track {track_id}"
    return samples


def match_tracking_contour_kind(
    *,
    area: float,
    width: float,
    height: float,
    perimeter: float,
    frame_area: float,
    min_detection_confidence: float,
) -> tuple[str, float] | None:
    if area <= 0 or width <= 0 or height <= 0 or frame_area <= 0:
        return None
    area_ratio = area / frame_area
    aspect_ratio = width / height
    compactness = min(aspect_ratio, 1 / aspect_ratio)
    circularity = 4 * math.pi * area / (perimeter * perimeter) if perimeter > 0 else 0.0
    ball_confidence = min(
        circularity * 0.45 + compactness * 0.35 + min(area_ratio / 0.0015, 1.0) * 0.2,
        1.0,
    )
    ball_threshold = max(0.2, min_detection_confidence * 0.5)
    if (
        frame_area * 0.00003 <= area <= frame_area * 0.003
        and 0.55 <= compactness <= 1.0
        and 0.42 <= circularity <= 1.25
        and ball_confidence >= ball_threshold
    ):
        return ("ball", round(ball_confidence, 3))
    player_confidence = min(area / (frame_area * 0.015), 1.0)
    if player_confidence >= min_detection_confidence and area >= frame_area * 0.0003:
        return ("player", round(player_confidence, 3))
    return None


def select_match_ball_candidate(
    candidates: list[tuple[float, float, float]],
    previous_ball: tuple[float, float] | None,
) -> tuple[float, float, float] | None:
    if not candidates:
        return None
    if previous_ball is None:
        return max(candidates, key=lambda candidate: candidate[2])
    return max(
        candidates,
        key=lambda candidate: candidate[2] - min(math.dist(previous_ball, (candidate[0], candidate[1])) / 240, 1.0) * 0.25,
    )


def decode_annotation_tags(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item)]


def decode_pose_keypoints(value: str | None) -> list[dict[str, object]]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    keypoints: list[dict[str, object]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip().lower().replace("-", "_").replace(" ", "_")
        try:
            x_percent = float(item["x_percent"])
            y_percent = float(item["y_percent"])
        except (KeyError, TypeError, ValueError):
            continue
        if not name or not (0 <= x_percent <= 100) or not (0 <= y_percent <= 100):
            continue
        keypoints.append(
            {
                "name": name,
                "x_percent": x_percent,
                "y_percent": y_percent,
                "z": item.get("z"),
                "confidence": item.get("confidence"),
            }
        )
    return keypoints


def pose_keypoint_lookup(sample: PerformanceVideoPoseSample) -> dict[str, tuple[float, float]]:
    lookup: dict[str, tuple[float, float]] = {}
    for point in decode_pose_keypoints(sample.keypoints_json):
        lookup[str(point["name"])] = (float(point["x_percent"]), float(point["y_percent"]))
    return lookup


def first_pose_point(
    lookup: dict[str, tuple[float, float]],
    *names: str,
) -> tuple[float, float] | None:
    for name in names:
        normalized = name.lower().replace("-", "_").replace(" ", "_")
        if normalized in lookup:
            return lookup[normalized]
    return None


def midpoint(*points: tuple[float, float] | None) -> tuple[float, float] | None:
    available = [point for point in points if point is not None]
    if not available:
        return None
    return (
        sum(point[0] for point in available) / len(available),
        sum(point[1] for point in available) / len(available),
    )


def angle_from_vertical_degrees(
    lower: tuple[float, float] | None,
    upper: tuple[float, float] | None,
) -> float | None:
    if lower is None or upper is None:
        return None
    dx = upper[0] - lower[0]
    dy = lower[1] - upper[1]
    if abs(dx) < 0.001 and abs(dy) < 0.001:
        return None
    return abs(math.degrees(math.atan2(dx, dy)))


def derive_pose_sample_metrics(
    samples: list[PerformanceVideoPoseSample],
) -> dict[str, float]:
    if not samples:
        return {}
    torso_angles: list[float] = []
    knee_drive_angles: list[float] = []
    arm_symmetry_values: list[float] = []
    contact_windows: dict[tuple[str, int], list[float]] = {}

    for sample in samples:
        lookup = pose_keypoint_lookup(sample)
        left_shoulder = first_pose_point(lookup, "left_shoulder", "l_shoulder")
        right_shoulder = first_pose_point(lookup, "right_shoulder", "r_shoulder")
        left_hip = first_pose_point(lookup, "left_hip", "l_hip")
        right_hip = first_pose_point(lookup, "right_hip", "r_hip")
        shoulders = midpoint(left_shoulder, right_shoulder)
        hips = midpoint(left_hip, right_hip)
        torso_angle = angle_from_vertical_degrees(hips, shoulders)
        if torso_angle is not None:
            torso_angles.append(torso_angle)

        for hip_name, knee_name, ankle_name in [
            ("left_hip", "left_knee", "left_ankle"),
            ("right_hip", "right_knee", "right_ankle"),
        ]:
            hip = first_pose_point(lookup, hip_name)
            knee = first_pose_point(lookup, knee_name)
            ankle = first_pose_point(lookup, ankle_name)
            if hip is None or knee is None:
                continue
            vertical_lift = max(0.0, hip[1] - knee[1])
            forward_drive = abs(knee[0] - hip[0])
            lower_leg = abs((ankle[1] if ankle else hip[1] + 15) - hip[1]) or 15.0
            lift_ratio = min(1.0, vertical_lift / max(lower_leg, 1.0))
            knee_drive_angles.append(min(95.0, 58.0 + lift_ratio * 28.0 + min(forward_drive, 10.0) * 0.7))

        left_elbow = first_pose_point(lookup, "left_elbow", "l_elbow")
        right_elbow = first_pose_point(lookup, "right_elbow", "r_elbow")
        left_arm_angle = angle_from_vertical_degrees(left_elbow, left_shoulder)
        right_arm_angle = angle_from_vertical_degrees(right_elbow, right_shoulder)
        if left_arm_angle is not None and right_arm_angle is not None:
            diff = abs(left_arm_angle - right_arm_angle)
            arm_symmetry_values.append(max(1.0, min(10.0, 10.0 - diff / 12.0)))

        phase = (sample.phase or "").lower()
        if sample.contact_foot or "contact" in phase or "stance" in phase:
            key = (
                (sample.contact_foot or "unknown").lower(),
                sample.stride_index if sample.stride_index is not None else len(contact_windows),
            )
            contact_windows.setdefault(key, []).append(float(sample.timestamp_seconds))

    metrics: dict[str, float] = {}
    if torso_angles:
        metrics["torso_lean_angle"] = round(sum(torso_angles) / len(torso_angles), 2)
    if knee_drive_angles:
        metrics["knee_drive_angle"] = round(max(knee_drive_angles), 2)
    if arm_symmetry_values:
        metrics["arm_swing_symmetry"] = round(sum(arm_symmetry_values) / len(arm_symmetry_values), 2)
    contact_durations = [
        (max(timestamps) - min(timestamps)) * 1000
        for timestamps in contact_windows.values()
        if len(timestamps) >= 2
    ]
    if contact_durations:
        contact_window = sum(contact_durations) / len(contact_durations)
        if 40 <= contact_window <= 350:
            metrics["ground_contact_time"] = round(contact_window, 2)
    contact_step_timestamps = sorted(
        round(min(timestamps), 3)
        for timestamps in contact_windows.values()
        if timestamps
    )
    if len(contact_step_timestamps) >= 3:
        duration = contact_step_timestamps[-1] - contact_step_timestamps[0]
        if duration > 0:
            metrics["stride_frequency"] = round((len(contact_step_timestamps) - 1) / duration, 2)
    return metrics


async def create_performance_video_pose_samples(
    db: AsyncSession,
    identity: CurrentIdentity,
    video_asset_id: UUID,
    payload: PerformanceVideoPoseSampleBatchCreate,
    authz: AuthorizationService,
) -> list[PerformanceVideoPoseSample]:
    video_asset = await get_performance_video_asset(db, video_asset_id)
    await ensure_manage_performance(authz, identity, video_asset.organization_id)
    return await store_performance_video_pose_samples(
        db,
        video_asset,
        payload,
        actor_person_id=identity.person_id,
    )


async def store_performance_video_pose_samples(
    db: AsyncSession,
    video_asset: PerformanceVideoAsset,
    payload: PerformanceVideoPoseSampleBatchCreate,
    *,
    actor_person_id: UUID | None,
) -> list[PerformanceVideoPoseSample]:
    if payload.organization_id != video_asset.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    if payload.replace_existing:
        await db.execute(
            delete(PerformanceVideoPoseSample).where(
                PerformanceVideoPoseSample.video_asset_id == video_asset.id
            )
        )

    rows: list[PerformanceVideoPoseSample] = []
    for item in payload.samples:
        keypoints = [
            {
                "name": point.name.strip().lower().replace("-", "_").replace(" ", "_"),
                "x_percent": point.x_percent,
                "y_percent": point.y_percent,
                "z": point.z,
                "confidence": point.confidence,
            }
            for point in item.keypoints
        ]
        sample = PerformanceVideoPoseSample(
            organization_id=video_asset.organization_id,
            video_asset_id=video_asset.id,
            athlete_profile_id=video_asset.athlete_profile_id,
            event_id=video_asset.event_id,
            created_by_person_id=actor_person_id,
            source_provider=item.source_provider,
            frame_index=item.frame_index,
            timestamp_seconds=item.timestamp_seconds,
            phase=item.phase,
            contact_foot=item.contact_foot,
            stride_index=item.stride_index,
            sample_confidence=item.sample_confidence,
            keypoints_json=json.dumps(keypoints),
        )
        db.add(sample)
        rows.append(sample)
    await db.commit()
    for row in rows:
        await db.refresh(row)
    return rows


async def list_performance_video_pose_samples(
    db: AsyncSession,
    video_asset_id: UUID,
    limit: int = 600,
) -> list[PerformanceVideoPoseSample]:
    return list(
        (
            await db.scalars(
                select(PerformanceVideoPoseSample)
                .where(PerformanceVideoPoseSample.video_asset_id == video_asset_id)
                .order_by(
                    PerformanceVideoPoseSample.timestamp_seconds,
                    PerformanceVideoPoseSample.frame_index,
                )
                .limit(limit)
            )
        ).all()
    )


def clamp_percent(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 4)


def infer_pose_contact(
    keypoints: list[dict[str, object]],
    previous_contact_foot: str | None,
    current_stride_index: int,
) -> tuple[str | None, str | None, int]:
    ankle_points = {
        str(point["name"]): point
        for point in keypoints
        if str(point["name"]) in {"left_ankle", "right_ankle"}
    }
    left = ankle_points.get("left_ankle")
    right = ankle_points.get("right_ankle")
    if not left and not right:
        return None, "pose_frame", current_stride_index
    left_y = float(left["y_percent"]) if left else -1.0
    right_y = float(right["y_percent"]) if right else -1.0
    foot = "left" if left_y >= right_y else "right"
    lower_y = max(left_y, right_y)
    if lower_y < 55:
        return None, "flight_recovery", current_stride_index
    stride_index = current_stride_index
    if previous_contact_foot is not None and foot != previous_contact_foot:
        stride_index += 1
    return foot, "ground_contact", stride_index


def extract_pose_samples_from_video_content(
    content: bytes,
    *,
    max_frames: int,
    sample_every_seconds: float,
    min_detection_confidence: float,
) -> dict[str, object]:
    try:
        import cv2
        import mediapipe as mp
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MediaPipe/OpenCV pose worker dependencies are not installed",
        ) from exc

    warnings: list[str] = []
    with tempfile.NamedTemporaryFile(suffix=".mp4") as handle:
        handle.write(content)
        handle.flush()
        capture = cv2.VideoCapture(handle.name)
        if not capture.isOpened():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Video could not be decoded")
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        if fps <= 0:
            fps = 25.0
            warnings.append("Video FPS missing; assumed 25 fps for sampling.")
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_seconds = round(total_frames / fps, 3) if total_frames else None
        sample_every_frames = max(1, int(round(fps * sample_every_seconds)))
        pose = mp.solutions.pose.Pose(
            static_image_mode=True,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
        )
        samples: list[dict[str, object]] = []
        decoded_count = 0
        processed_count = 0
        frame_index = 0
        contact_foot: str | None = None
        stride_index = 0
        try:
            while len(samples) < max_frames:
                ok, frame = capture.read()
                if not ok:
                    break
                decoded_count += 1
                if frame_index % sample_every_frames != 0:
                    frame_index += 1
                    continue
                processed_count += 1
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = pose.process(rgb_frame)
                if not result.pose_landmarks:
                    frame_index += 1
                    continue
                keypoints = []
                for landmark_id, landmark in enumerate(result.pose_landmarks.landmark):
                    name = mp.solutions.pose.PoseLandmark(landmark_id).name.lower()
                    keypoints.append(
                        {
                            "name": name,
                            "x_percent": clamp_percent(float(landmark.x) * 100),
                            "y_percent": clamp_percent(float(landmark.y) * 100),
                            "z": round(float(landmark.z), 6),
                            "confidence": round(float(getattr(landmark, "visibility", 0.0)), 4),
                        }
                    )
                contact_foot, phase, stride_index = infer_pose_contact(keypoints, contact_foot, stride_index)
                samples.append(
                    {
                        "source_provider": "mediapipe_pose_solution",
                        "frame_index": frame_index,
                        "timestamp_seconds": round(frame_index / fps, 3),
                        "phase": phase,
                        "contact_foot": contact_foot,
                        "stride_index": stride_index,
                        "sample_confidence": round(
                            sum(float(point.get("confidence") or 0.0) for point in keypoints) / len(keypoints),
                            4,
                        ),
                        "keypoints": keypoints,
                    }
                )
                frame_index += 1
        finally:
            pose.close()
            capture.release()
    if not samples:
        warnings.append("No human pose landmarks were detected in sampled frames.")
    return {
        "samples": samples,
        "decoded_frame_count": decoded_count,
        "processed_frame_count": processed_count,
        "frame_rate": fps,
        "frame_count": total_frames,
        "duration_seconds": duration_seconds,
        "warnings": warnings,
        "source_provider": "mediapipe_pose_solution",
        "model_policy": "mediapipe-pose-solution-v1",
    }


async def process_performance_video_pose_samples(
    db: AsyncSession,
    video_asset_id: UUID,
    payload: PerformanceVideoPoseProcessingCreate,
    *,
    identity: CurrentIdentity | None = None,
    authz: AuthorizationService | None = None,
    settings: Settings | None = None,
) -> dict[str, object]:
    selected_settings = settings or get_settings()
    video_asset = await get_performance_video_asset(db, video_asset_id)
    if identity is not None:
        if authz is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authorization service required")
        await ensure_manage_performance(authz, identity, video_asset.organization_id)
    if payload.organization_id != video_asset.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    if selected_settings.performance_pose_worker_provider == "disabled":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Pose worker is disabled")
    content = get_object(
        selected_settings,
        local_root=selected_settings.performance_video_file_dir,
        key=performance_video_object_key(video_asset, selected_settings),
    )
    if hashlib.sha256(content).hexdigest() != video_asset.checksum:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Stored video checksum mismatch")
    extracted = extract_pose_samples_from_video_content(
        content,
        max_frames=payload.max_frames,
        sample_every_seconds=payload.sample_every_seconds,
        min_detection_confidence=payload.min_detection_confidence,
    )
    samples = list(extracted["samples"])
    rows: list[PerformanceVideoPoseSample] = []
    if samples:
        rows = await store_performance_video_pose_samples(
            db,
            video_asset,
            PerformanceVideoPoseSampleBatchCreate(
                organization_id=video_asset.organization_id,
                replace_existing=payload.replace_existing,
                samples=samples,
            ),
            actor_person_id=identity.person_id if identity else None,
        )
    elif payload.replace_existing:
        await db.execute(
            delete(PerformanceVideoPoseSample).where(
                PerformanceVideoPoseSample.video_asset_id == video_asset.id
            )
        )
        await db.commit()
    video_asset.status = "pose_sampled" if rows else "pose_no_subject"
    video_asset.frame_rate = video_asset.frame_rate or extracted.get("frame_rate")
    video_asset.duration_seconds = video_asset.duration_seconds or extracted.get("duration_seconds")
    await db.commit()
    await db.refresh(video_asset)
    analysis_result = None
    if payload.run_analysis and rows:
        analysis_result = await analyze_pose_gait_for_video(
            db,
            identity or CurrentIdentity(
                user_id=video_asset.uploaded_by_person_id or video_asset.organization_id,
                person_id=video_asset.uploaded_by_person_id or video_asset.organization_id,
                keycloak_sub="system:performance-video-pose-worker",
                email="system@afrolete.local",
                display_name="AfroLete Pose Worker",
            ),
            video_asset.id,
            PerformancePoseGaitAnalysisCreate(
                evidence_text="Pose samples extracted by the MediaPipe video-processing worker.",
                reference_profile_id=payload.reference_profile_id,
                create_coaching_outputs=identity is not None,
            ),
            authz or AllowAllAuthorizationService(),
        )
        video_asset = analysis_result["video_asset"]
    all_samples = await list_performance_video_pose_samples(db, video_asset.id)
    return {
        "video_asset": video_asset,
        "samples": all_samples,
        "created_samples": rows,
        "sample_count": len(all_samples),
        "processed_frame_count": extracted["processed_frame_count"],
        "decoded_frame_count": extracted["decoded_frame_count"],
        "warnings": extracted["warnings"],
        "source_provider": extracted["source_provider"],
        "model_policy": extracted["model_policy"],
        "analysis": analysis_result["analysis"] if analysis_result else None,
    }


class AllowAllAuthorizationService:
    async def check(self, **_: object) -> bool:
        return True


async def run_performance_video_pose_worker(
    db: AsyncSession,
    *,
    organization_id: UUID | None = None,
    video_asset_id: UUID | None = None,
    limit: int = 10,
    max_frames: int | None = None,
    sample_every_seconds: float | None = None,
    settings: Settings | None = None,
) -> dict[str, object]:
    selected_settings = settings or get_settings()
    statement = select(PerformanceVideoAsset).where(
        PerformanceVideoAsset.status.in_(["uploaded", "pose_failed", "pose_no_subject"])
    )
    if organization_id is not None:
        statement = statement.where(PerformanceVideoAsset.organization_id == organization_id)
    if video_asset_id is not None:
        statement = statement.where(PerformanceVideoAsset.id == video_asset_id)
    videos = list((await db.scalars(statement.order_by(PerformanceVideoAsset.created_at.asc()).limit(limit))).all())
    processed_count = 0
    failed_count = 0
    skipped_count = 0
    results: list[dict[str, object]] = []
    for video_asset in videos:
        try:
            result = await process_performance_video_pose_samples(
                db,
                video_asset.id,
                PerformanceVideoPoseProcessingCreate(
                    organization_id=video_asset.organization_id,
                    max_frames=max_frames or selected_settings.performance_pose_worker_max_frames,
                    sample_every_seconds=(
                        sample_every_seconds
                        or selected_settings.performance_pose_worker_sample_every_seconds
                    ),
                    min_detection_confidence=selected_settings.performance_pose_worker_min_detection_confidence,
                    run_analysis=True,
                ),
                settings=selected_settings,
            )
            processed_count += 1
            results.append(
                {
                    "video_asset_id": str(video_asset.id),
                    "status": result["video_asset"].status,
                    "sample_count": result["sample_count"],
                    "processed_frame_count": result["processed_frame_count"],
                    "warning_count": len(result["warnings"]),
                }
            )
        except HTTPException as exc:
            await db.rollback()
            video_asset.status = "pose_failed"
            video_asset.pose_analysis_json = json.dumps({"error": exc.detail})
            await db.commit()
            failed_count += 1
            results.append({"video_asset_id": str(video_asset.id), "status": "pose_failed", "error": str(exc.detail)})
        except Exception as exc:
            await db.rollback()
            video_asset.status = "pose_failed"
            video_asset.pose_analysis_json = json.dumps({"error": str(exc)})
            await db.commit()
            failed_count += 1
            results.append({"video_asset_id": str(video_asset.id), "status": "pose_failed", "error": str(exc)})
    return {
        "organization_id": str(organization_id) if organization_id else None,
        "eligible_count": len(videos),
        "processed_count": processed_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "results": results,
    }


def decode_reference_metric_targets(value: str | None) -> list[dict[str, object]]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    targets: list[dict[str, object]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        try:
            optimal_min = float(item["optimal_min"])
            optimal_max = float(item["optimal_max"])
        except (KeyError, TypeError, ValueError):
            continue
        if optimal_max <= optimal_min:
            continue
        category_value = item.get("category", MetricCategory.TECHNICAL)
        try:
            category = MetricCategory(category_value)
        except ValueError:
            category = MetricCategory.TECHNICAL
        targets.append(
            {
                "key": str(item.get("key", "")).strip(),
                "label": str(item.get("label", "")).strip(),
                "category": category,
                "unit": str(item.get("unit") or "score"),
                "optimal_min": optimal_min,
                "optimal_max": optimal_max,
                "benchmark_label": item.get("benchmark_label"),
                "coaching_cue": item.get("coaching_cue"),
            }
        )
    return [target for target in targets if target["key"] and target["label"]]


def decode_reference_pose_samples(value: str | None) -> list[dict[str, object]]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


async def create_movement_reference_profile(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: PerformanceMovementReferenceProfileCreate,
    authz: AuthorizationService,
) -> PerformanceMovementReferenceProfile:
    organization = await db.get(Organization, payload.organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    await ensure_manage_performance(authz, identity, payload.organization_id)
    metric_targets = [
        {
            "key": target.key.strip().lower(),
            "label": target.label,
            "category": target.category.value,
            "unit": target.unit,
            "optimal_min": target.optimal_min,
            "optimal_max": target.optimal_max,
            "benchmark_label": target.benchmark_label,
            "coaching_cue": target.coaching_cue,
        }
        for target in payload.metric_targets
    ]
    pose_samples = [
        {
            "source_provider": sample.source_provider,
            "frame_index": sample.frame_index,
            "timestamp_seconds": sample.timestamp_seconds,
            "phase": sample.phase,
            "contact_foot": sample.contact_foot,
            "stride_index": sample.stride_index,
            "sample_confidence": sample.sample_confidence,
            "keypoints": [
                {
                    "name": point.name.strip().lower().replace("-", "_").replace(" ", "_"),
                    "x_percent": point.x_percent,
                    "y_percent": point.y_percent,
                    "z": point.z,
                    "confidence": point.confidence,
                }
                for point in sample.keypoints
            ],
        }
        for sample in payload.pose_samples
    ]
    profile = PerformanceMovementReferenceProfile(
        organization_id=payload.organization_id,
        created_by_person_id=identity.person_id,
        sport=payload.sport,
        name=payload.name,
        benchmark_profile=payload.benchmark_profile,
        performer_name=payload.performer_name,
        source_label=payload.source_label,
        competition_context=payload.competition_context,
        consent_basis=payload.consent_basis,
        visibility=payload.visibility,
        metric_targets_json=json.dumps(metric_targets),
        pose_samples_json=json.dumps(pose_samples) if pose_samples else None,
        notes=payload.notes,
    )
    db.add(profile)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reference profile already exists") from exc
    await db.refresh(profile)
    return profile


async def list_movement_reference_profiles(
    db: AsyncSession,
    organization_id: UUID,
    sport: str | None = None,
    benchmark_profile: str | None = None,
) -> list[PerformanceMovementReferenceProfile]:
    statement = select(PerformanceMovementReferenceProfile).where(
        PerformanceMovementReferenceProfile.organization_id == organization_id,
        PerformanceMovementReferenceProfile.status == "active",
    )
    if sport:
        statement = statement.where(PerformanceMovementReferenceProfile.sport == sport)
    if benchmark_profile:
        statement = statement.where(
            PerformanceMovementReferenceProfile.benchmark_profile == benchmark_profile
        )
    return list(
        (
            await db.scalars(
                statement.order_by(
                    PerformanceMovementReferenceProfile.sport,
                    PerformanceMovementReferenceProfile.name,
                )
            )
        ).all()
    )


async def get_movement_reference_profile(
    db: AsyncSession,
    profile_id: UUID,
    organization_id: UUID,
) -> PerformanceMovementReferenceProfile:
    profile = await db.get(PerformanceMovementReferenceProfile, profile_id)
    if profile is None or profile.organization_id != organization_id or profile.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference profile not found")
    return profile


def pose_gait_templates(sport: str) -> list[dict[str, object]]:
    if sport == "athletics":
        return [
            {
                "key": "torso_lean_angle",
                "label": "Torso Lean Angle",
                "category": MetricCategory.TECHNICAL,
                "unit": "degrees",
                "optimal_min": 8.0,
                "optimal_max": 14.0,
                "benchmark": "world-class max-velocity sprint posture",
                "cue": "Stack ribs over hips after acceleration and avoid folding from the waist.",
                "risk_terms": ["collapse", "fold", "excessive lean", "late torso"],
                "positive_terms": ["upright", "stacked", "tall posture"],
                "default": 16.0,
            },
            {
                "key": "knee_drive_angle",
                "label": "Front Knee Drive",
                "category": MetricCategory.PHYSICAL,
                "unit": "degrees",
                "optimal_min": 70.0,
                "optimal_max": 90.0,
                "benchmark": "elite sprint front-side mechanics",
                "cue": "Punch the knee forward and up while keeping the foot dorsiflexed.",
                "risk_terms": ["low knee", "drag", "backside"],
                "positive_terms": ["high knee", "front-side", "knee drive"],
                "default": 66.0,
            },
            {
                "key": "ground_contact_time",
                "label": "Ground Contact Time",
                "category": MetricCategory.PHYSICAL,
                "unit": "ms",
                "optimal_min": 80.0,
                "optimal_max": 120.0,
                "benchmark": "world-class short ground contact window",
                "cue": "Strike under the hips and leave the ground quickly without reaching.",
                "risk_terms": ["long contact", "heavy", "braking", "flat foot"],
                "positive_terms": ["quick contact", "reactive", "stiff ankle"],
                "default": 132.0,
                "lower_is_better": True,
            },
            {
                "key": "arm_swing_symmetry",
                "label": "Arm Swing Symmetry",
                "category": MetricCategory.TECHNICAL,
                "unit": "score",
                "optimal_min": 8.0,
                "optimal_max": 10.0,
                "benchmark": "elite linear arm-drive pattern",
                "cue": "Drive elbows back with compact hands and avoid crossing the midline.",
                "risk_terms": ["cross-body", "wide", "twist", "late arms"],
                "positive_terms": ["compact", "linear", "coordinated arms"],
                "default": 6.8,
            },
            {
                "key": "stride_frequency",
                "label": "Stride Frequency",
                "category": MetricCategory.TACTICAL,
                "unit": "Hz",
                "optimal_min": 4.2,
                "optimal_max": 5.0,
                "benchmark": "elite cadence consistency",
                "cue": "Keep rhythm progressive and resist overstriding to chase speed.",
                "risk_terms": ["ragged", "rushed", "overstride", "fatigue"],
                "positive_terms": ["rhythm", "cadence", "consistent"],
                "default": 4.0,
            },
        ]
    return [
        {
            "key": "movement_symmetry",
            "label": "Movement Symmetry",
            "category": MetricCategory.TECHNICAL,
            "unit": "score",
            "optimal_min": 8.0,
            "optimal_max": 10.0,
            "benchmark": "elite sport movement symmetry",
            "cue": "Match left and right mechanics before increasing intensity.",
            "risk_terms": ["asymmetry", "limp", "collapse"],
            "positive_terms": ["balanced", "symmetric", "controlled"],
            "default": 7.0,
        },
        {
            "key": "postural_control",
            "label": "Postural Control",
            "category": MetricCategory.TECHNICAL,
            "unit": "score",
            "optimal_min": 8.0,
            "optimal_max": 10.0,
            "benchmark": "elite posture under load",
            "cue": "Keep trunk control through direction changes and fatigue.",
            "risk_terms": ["unstable", "late", "fold"],
            "positive_terms": ["stable", "tall", "controlled"],
            "default": 7.1,
        },
    ]


def reference_enriched_pose_templates(
    sport: str,
    reference_profile: PerformanceMovementReferenceProfile | None,
) -> list[dict[str, object]]:
    templates = [dict(template) for template in pose_gait_templates(sport)]
    if reference_profile is None:
        return templates
    targets = {str(target["key"]): target for target in decode_reference_metric_targets(reference_profile.metric_targets_json)}
    for template in templates:
        key = str(template["key"])
        target = targets.get(key)
        if target is None:
            continue
        template["label"] = target["label"]
        template["category"] = target["category"]
        template["unit"] = target["unit"]
        template["optimal_min"] = target["optimal_min"]
        template["optimal_max"] = target["optimal_max"]
        template["benchmark"] = (
            target.get("benchmark_label")
            or reference_profile.source_label
            or template["benchmark"]
        )
        template["cue"] = target.get("coaching_cue") or template["cue"]
    known_keys = {str(template["key"]) for template in templates}
    for target in targets.values():
        key = str(target["key"])
        if key in known_keys:
            continue
        templates.append(
            {
                "key": key,
                "label": target["label"],
                "category": target["category"],
                "unit": target["unit"],
                "optimal_min": target["optimal_min"],
                "optimal_max": target["optimal_max"],
                "benchmark": target.get("benchmark_label") or reference_profile.source_label,
                "cue": target.get("coaching_cue") or "Review against the selected reference profile.",
                "risk_terms": [],
                "positive_terms": [],
                "default": float(target["optimal_min"]),
            }
        )
    return templates


def pose_gait_metric_cards(
    evidence_text: str | None,
    sport: str,
    derived_metrics: dict[str, float] | None = None,
    reference_profile: PerformanceMovementReferenceProfile | None = None,
) -> list[dict[str, object]]:
    text = (evidence_text or "").lower()
    sample_metrics = derived_metrics or {}
    cards: list[dict[str, object]] = []
    for template in reference_enriched_pose_templates(sport, reference_profile):
        key = str(template["key"])
        source = "benchmark_template"
        observed = sample_metrics.get(key)
        if observed is not None:
            source = "pose_keypoints"
        if observed is None:
            observed = extract_labeled_float(evidence_text, str(template["label"]), key)
            if observed is not None:
                source = "evidence_text"
        if observed is None:
            observed = float(template["default"])
            if any(str(term) in text for term in template["positive_terms"]):
                observed += -8 if template.get("lower_is_better") else 0.7
            if any(str(term) in text for term in template["risk_terms"]):
                observed += 14 if template.get("lower_is_better") else -1.2
        optimal_min = float(template["optimal_min"])
        optimal_max = float(template["optimal_max"])
        score = score_against_optimal_range(observed, optimal_min, optimal_max)
        if template.get("lower_is_better") and observed <= optimal_max:
            score = max(score, 8.0)
        if observed < optimal_min:
            delta = round(observed - optimal_min, 2)
        elif observed > optimal_max:
            delta = round(observed - optimal_max, 2)
        else:
            delta = 0.0
        cards.append(
            {
                "key": template["key"],
                "label": template["label"],
                "category": template["category"],
                "observed_value": round(observed, 2),
                "optimal_min": optimal_min,
                "optimal_max": optimal_max,
                "unit": template["unit"],
                "score": score,
                "delta_from_optimal": delta,
                "benchmark_label": template["benchmark"],
                "coaching_cue": template["cue"],
                "source": source,
            }
        )
    return cards


def extract_labeled_float(text: str | None, *labels: str) -> float | None:
    if not text:
        return None
    normalized = text.replace("_", " ")
    for label in labels:
        escaped = re.escape(label.replace("_", " "))
        patterns = [
            rf"{escaped}\D{{0,80}}(-?\d+(?:\.\d+)?)",
            rf"(-?\d+(?:\.\d+)?)\D{{0,80}}{escaped}",
        ]
        for pattern in patterns:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                return float(match.group(1))
    return None


def score_against_optimal_range(value: float, optimal_min: float, optimal_max: float) -> float:
    if optimal_min <= value <= optimal_max:
        return 9.2
    nearest = optimal_min if value < optimal_min else optimal_max
    span = max(abs(optimal_max - optimal_min), 1.0)
    penalty = abs(value - nearest) / span * 2.5
    return round(max(1.0, 9.2 - penalty), 1)


def pose_gait_phase_cards(
    metrics: list[dict[str, object]],
    duration_seconds: float | None,
) -> list[dict[str, object]]:
    duration = duration_seconds or 8.0
    weakest = sorted(metrics, key=lambda metric: float(metric["score"]))[:3]
    phase_names = ["initial contact", "mid-stance", "toe-off", "flight recovery"]
    phases: list[dict[str, object]] = []
    for index, phase in enumerate(phase_names):
        metric = weakest[index % len(weakest)]
        phases.append(
            {
                "phase": phase,
                "timestamp_seconds": round(duration * (index + 1) / (len(phase_names) + 1), 2),
                "playback_rate": 0.25 if index in {1, 2} else 0.5,
                "focus": str(metric["label"]),
                "finding": f"{metric['label']} scored {float(metric['score']):g}/10.",
                "benchmark_note": f"Compared with {metric['benchmark_label']}; delta {metric['delta_from_optimal']} {metric['unit']}.",
            }
        )
    return phases


def optimal_projection_cards(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    projections: list[dict[str, object]] = []
    for metric in sorted(metrics, key=lambda item: float(item["score"]))[:3]:
        observed = float(metric["observed_value"])
        optimal_min = float(metric["optimal_min"])
        optimal_max = float(metric["optimal_max"])
        target = observed
        if observed < optimal_min:
            target = optimal_min
        elif observed > optimal_max:
            target = optimal_max
        projections.append(
            {
                "priority": str(metric["label"]),
                "current_score": float(metric["score"]),
                "projected_score": min(10.0, round(float(metric["score"]) + 1.4, 1)),
                "target_change": f"Move from {observed:g} to {target:g} {metric['unit']}.",
                "drill": str(metric["coaching_cue"]),
            }
        )
    return projections


def pose_gait_confidence(
    evidence_text: str | None,
    video_asset: PerformanceVideoAsset,
    pose_sample_count: int = 0,
) -> float:
    confidence = 0.7
    if evidence_text and len(evidence_text) > 100:
        confidence += 0.08
    if video_asset.frame_rate and video_asset.frame_rate >= 60:
        confidence += 0.06
    if video_asset.frame_width and video_asset.frame_width >= 1280:
        confidence += 0.04
    if pose_sample_count >= 4:
        confidence += 0.06
    if pose_sample_count >= 12:
        confidence += 0.04
    return round(min(confidence, 0.88), 2)


def pose_gait_summary(
    video_asset: PerformanceVideoAsset,
    metrics: list[dict[str, object]],
    confidence: float,
    pose_sample_count: int = 0,
) -> str:
    strongest = max(metrics, key=lambda item: float(item["score"]))
    weakest = min(metrics, key=lambda item: float(item["score"]))
    sample_note = (
        f" using {pose_sample_count} stored pose landmark samples"
        if pose_sample_count
        else ""
    )
    return (
        f"Pose and gait analysis for {video_asset.clip_label or video_asset.filename} compares "
        f"{video_asset.sport} movement against world-class benchmark ranges{sample_note}. "
        f"Strongest pattern: {strongest['label']} ({float(strongest['score']):g}/10). "
        f"Priority correction: {weakest['label']} ({float(weakest['score']):g}/10). "
        f"Confidence {confidence:.0%}; coach review is required before training prescription."
    )


def pose_gait_evidence_text(
    video_asset: PerformanceVideoAsset,
    metrics: list[dict[str, object]],
    phases: list[dict[str, object]],
    evidence_text: str | None,
) -> str:
    metric_text = ". ".join(
        f"{metric['label']} {metric['score']} with observed {metric['observed_value']} {metric['unit']}"
        for metric in metrics
    )
    phase_text = ". ".join(
        f"{phase['phase']} at {phase['timestamp_seconds']}s: {phase['finding']}"
        for phase in phases
    )
    return (
        f"{evidence_text or ''} Video {video_asset.video_uri}. "
        f"Pose-gait benchmark analysis. {metric_text}. {phase_text}."
    ).strip()


def video_coaching_metric_specs(sport: str) -> list[dict[str, object]]:
    if sport == "athletics":
        return [
            {
                "code": "video_stride_efficiency",
                "name": "Stride Efficiency",
                "category": MetricCategory.PHYSICAL,
                "cue": "Run tall through the hips and land under the center of mass.",
                "positive_terms": ["smooth", "efficient", "quick turnover", "relaxed"],
                "risk_terms": ["overstride", "reaching", "braking", "choppy"],
            },
            {
                "code": "video_posture_control",
                "name": "Posture Control",
                "category": MetricCategory.TECHNICAL,
                "cue": "Hold a neutral trunk and avoid late torso collapse under fatigue.",
                "positive_terms": ["upright", "stable", "balanced", "tall"],
                "risk_terms": ["collapse", "lean", "fold", "rotation"],
            },
            {
                "code": "video_ground_contact_control",
                "name": "Ground Contact Control",
                "category": MetricCategory.PHYSICAL,
                "cue": "Keep ground contact crisp with the foot striking under the body.",
                "positive_terms": ["quick contact", "stiff ankle", "reactive", "spring"],
                "risk_terms": ["long contact", "heavy", "braking", "flat foot"],
            },
            {
                "code": "video_arm_drive",
                "name": "Arm Drive Coordination",
                "category": MetricCategory.TECHNICAL,
                "cue": "Drive elbows back and keep hands from crossing the midline.",
                "positive_terms": ["compact", "coordinated", "strong arms", "linear"],
                "risk_terms": ["cross-body", "wide", "late arms", "twist"],
            },
            {
                "code": "video_rhythm_consistency",
                "name": "Rhythm Consistency",
                "category": MetricCategory.TACTICAL,
                "cue": "Build speed progressively while keeping cadence consistent.",
                "positive_terms": ["rhythm", "consistent", "controlled", "progressive"],
                "risk_terms": ["fatigue", "ragged", "rushed", "breakdown"],
            },
        ]
    return [
        {
            "code": "video_movement_quality",
            "name": "Movement Quality",
            "category": MetricCategory.TECHNICAL,
            "cue": "Repeat the core movement pattern at match speed with control.",
            "positive_terms": ["controlled", "balanced", "smooth", "efficient"],
            "risk_terms": ["unstable", "late", "rushed", "asymmetry"],
        },
        {
            "code": "video_physical_execution",
            "name": "Physical Execution",
            "category": MetricCategory.PHYSICAL,
            "cue": "Maintain physical quality while fatigue rises.",
            "positive_terms": ["strong", "explosive", "quick", "powerful"],
            "risk_terms": ["slow", "heavy", "weak", "fatigue"],
        },
        {
            "code": "video_decision_timing",
            "name": "Decision Timing",
            "category": MetricCategory.TACTICAL,
            "cue": "Scan early and commit to the action before pressure arrives.",
            "positive_terms": ["early scan", "decisive", "aware", "timely"],
            "risk_terms": ["late", "hesitant", "blind", "delayed"],
        },
    ]


async def ensure_video_coaching_metrics(
    db: AsyncSession,
    organization_id: UUID,
    sport: str,
    specs: list[dict[str, object]],
) -> list[PerformanceMetricDefinition]:
    metrics: list[PerformanceMetricDefinition] = []
    for spec in specs:
        metric = await db.scalar(
            select(PerformanceMetricDefinition).where(
                PerformanceMetricDefinition.organization_id == organization_id,
                PerformanceMetricDefinition.sport == sport,
                PerformanceMetricDefinition.code == spec["code"],
            )
        )
        if metric is None:
            metric = PerformanceMetricDefinition(
                organization_id=organization_id,
                sport=sport,
                code=str(spec["code"]),
                name=str(spec["name"]),
                category=spec["category"],
                unit="score",
                description="AI video coaching score generated from clip evidence.",
                min_value=0,
                max_value=10,
                weight=1,
                higher_is_better=True,
            )
            db.add(metric)
        metrics.append(metric)
    return metrics


def video_coaching_score(
    evidence_text: str | None,
    spec: dict[str, object],
    extracted_value: float | None,
) -> float:
    if extracted_value is not None:
        return round(min(10.0, max(0.0, extracted_value)), 1)
    text = (evidence_text or "").lower()
    score = 7.2
    positive_terms = [str(term).lower() for term in spec["positive_terms"]]
    risk_terms = [str(term).lower() for term in spec["risk_terms"]]
    if any(term in text for term in positive_terms):
        score += 0.8
    if any(term in text for term in risk_terms):
        score -= 1.4
    if any(term in text for term in ("excellent", "elite", "explosive", "fast")):
        score += 0.5
    if any(term in text for term in ("poor", "weak", "pain", "limp", "asymmetry")):
        score -= 0.8
    return round(min(10.0, max(0.0, score)), 1)


def video_coaching_confidence(evidence_text: str | None, extracted_value: float | None) -> float:
    if extracted_value is not None:
        return 0.84
    if evidence_text and len(evidence_text) >= 80:
        return 0.76
    return 0.68


def video_scores_by_category(metric_cards: list[dict[str, object]]) -> dict[str, float]:
    average_score = round(
        sum(float(card["value"]) for card in metric_cards) / len(metric_cards) * 10,
        1,
    )
    scores: dict[str, float] = {}
    for category in (
        MetricCategory.PHYSICAL,
        MetricCategory.TECHNICAL,
        MetricCategory.TACTICAL,
    ):
        values = [
            float(card["value"]) * 10
            for card in metric_cards
            if card["category"] == category
        ]
        scores[category.value] = round(sum(values) / len(values), 1) if values else average_score
    scores["mental"] = average_score
    return scores


def video_coaching_summary(
    payload: PerformanceVideoCoachingCreate,
    metric_cards: list[dict[str, object]],
    confidence: float,
) -> str:
    weakest = min(metric_cards, key=lambda card: float(card["value"]))
    strongest = max(metric_cards, key=lambda card: float(card["value"]))
    clip = payload.clip_label or payload.video_uri
    return (
        f"AI video coaching reviewed {clip} for {payload.analysis_focus}. "
        f"Strongest signal: {strongest['metric_name']} at {float(strongest['value']):g}/10. "
        f"Priority correction: {weakest['metric_name']} at {float(weakest['value']):g}/10. "
        f"Average confidence {confidence:.0%}; coach verification is required."
    )


def video_coaching_plan(weakest_cards: list[dict[str, object]]) -> str:
    cues = [str(card["coaching_cue"]) for card in weakest_cards]
    return (
        "1. Review the clip with the athlete and confirm the model observations. "
        f"2. Practice cue: {cues[0]} "
        f"3. Secondary cue: {cues[-1]} "
        "4. Re-test with a short comparison clip and promote only verified observations."
    )


def video_coaching_next_actions(weakest_cards: list[dict[str, object]]) -> list[str]:
    return [
        "Coach reviews the pending observations and assessment.",
        f"Run a drill focused on {weakest_cards[0]['metric_name']}.",
        "Capture a follow-up clip after the correction block.",
        "Notify guardians before video review sessions that involve minors.",
    ]


def parse_performance_evidence(
    payload: PerformanceIngestionCreate,
    metric: PerformanceMetricDefinition,
) -> dict[str, object]:
    warnings: list[str] = []
    base_confidence = source_confidence(payload.source)
    structured_payload = decode_structured_evidence(payload.evidence_text)
    source_provider = performance_source_provider(payload, structured_payload)
    if payload.extracted_value is not None:
        value = float(payload.extracted_value)
        method = "operator_supplied_value"
        fields = {"value": f"{value:g}", "source": payload.source.value}
        if source_provider is not None:
            fields["source_provider"] = source_provider
        confidence = payload.confidence if payload.confidence is not None else base_confidence
        reason = "Operator supplied an extracted value; source baseline confidence applied."
        observed_at = None
    else:
        provider_match = (
            provider_specific_metric_match(structured_payload, metric, source_provider)
            if structured_payload is not None and source_provider is not None
            else None
        )
        structured_match = provider_match or (
            structured_metric_match(structured_payload, metric) if structured_payload is not None else None
        )
        if structured_match is not None:
            value = float(structured_match["value"])
            method = (
                f"{source_provider}_provider_schema"
                if provider_match is not None and source_provider is not None
                else "structured_provider_payload"
            )
            fields = primitive_parser_fields(structured_match)
            if source_provider is not None:
                fields["source_provider"] = source_provider
            match_confidence = structured_float(structured_match.get("confidence"))
            confidence = payload.confidence if payload.confidence is not None else (match_confidence or min(base_confidence + 0.08, 0.97))
            reason = (
                f"Normalized a {source_provider} provider schema into the selected metric."
                if provider_match is not None and source_provider is not None
                else "Matched a structured provider metric by code, name, or single-metric payload."
            )
            observed_at = parsed_provider_observed_at(structured_match)
        else:
            metric_value = extract_metric_specific_text_value(payload.evidence_text, metric)
            if metric_value is not None:
                value = metric_value
                method = "metric_specific_text"
                fields = {"value": f"{value:g}", "metric": metric.name, "source": payload.source.value}
                confidence = payload.confidence if payload.confidence is not None else max(base_confidence - 0.04, 0.5)
                reason = "Found the metric label next to a numeric value in narrative evidence."
                observed_at = None
            else:
                fallback_value = extract_numeric_value(payload.evidence_text)
                if fallback_value is not None:
                    value = fallback_value
                    method = "numeric_text_fallback"
                    fields = {"value": f"{value:g}", "source": payload.source.value}
                    confidence = payload.confidence if payload.confidence is not None else max(base_confidence - 0.12, 0.45)
                    reason = "No metric-specific provider field matched; used the first numeric value in evidence text."
                    warnings.append("Parser could not bind the number to the selected metric.")
                else:
                    value = default_value_for_metric(metric)
                    method = "metric_default"
                    fields = {"value": f"{value:g}", "source": payload.source.value}
                    confidence = payload.confidence if payload.confidence is not None else 0.35
                    reason = "No parseable provider value was found; queued a metric default for human review."
                    warnings.append("No parseable numeric value found in evidence.")
                observed_at = None

    if metric.min_value is not None and value < metric.min_value:
        warnings.append(f"Parsed value is below configured minimum {metric.min_value:g}.")
    if metric.max_value is not None and value > metric.max_value:
        warnings.append(f"Parsed value is above configured maximum {metric.max_value:g}.")

    return {
        "value": value,
        "confidence": round(float(confidence), 2),
        "method": method,
        "confidence_reason": reason,
        "warnings": warnings,
        "fields": fields,
        "observed_at": observed_at,
        "source_provider": source_provider,
    }


MODEL_ASSIST_SOURCES = {
    MetricSource.VIDEO_ANALYSIS,
    MetricSource.AUDIO_NARRATION,
    MetricSource.AGENT_EXTRACTED,
}

NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


async def model_assisted_performance_extraction(
    settings: Settings,
    payload: PerformanceIngestionCreate,
    metric: PerformanceMetricDefinition,
    parsed: dict[str, object],
) -> dict[str, object] | None:
    if settings.performance_model_extraction_mode == "off":
        return None
    if payload.extracted_value is not None or payload.source not in MODEL_ASSIST_SOURCES or not payload.evidence_text:
        return None
    if settings.performance_model_extraction_mode == "webhook":
        return await webhook_model_extraction(settings, payload, metric, parsed)
    return deterministic_model_extraction(settings, payload, metric, parsed)


def deterministic_model_extraction(
    settings: Settings,
    payload: PerformanceIngestionCreate,
    metric: PerformanceMetricDefinition,
    parsed: dict[str, object],
) -> dict[str, object] | None:
    text = payload.evidence_text or ""
    value = model_metric_text_value(text, metric)
    if value is None:
        return None
    confidence = min(max(source_confidence(payload.source) + 0.07, float(parsed["confidence"]) + 0.08), 0.93)
    return {
        "value": value,
        "confidence": round(confidence, 2),
        "method": "model_assisted_extraction",
        "model_policy": settings.performance_model_extraction_model,
        "summary": f"Model-assisted parser matched {metric.name} from narrative evidence.",
        "confidence_reason": (
            "Deterministic model-assist evaluated metric aliases, number words, units, and context before human review."
        ),
        "fields": {
            "model_policy": settings.performance_model_extraction_model,
            "model_mode": settings.performance_model_extraction_mode,
            "metric": metric.code,
            "value": f"{value:g}",
        },
    }


async def webhook_model_extraction(
    settings: Settings,
    payload: PerformanceIngestionCreate,
    metric: PerformanceMetricDefinition,
    parsed: dict[str, object],
) -> dict[str, object] | None:
    if not settings.performance_model_extraction_webhook_url:
        return None
    key_resolution = await resolve_performance_model_webhook_key(settings)
    request_payload = {
        "event": "afrolete.performance.extract",
        "model": settings.performance_model_extraction_model,
        "metric": {
            "id": str(metric.id),
            "code": metric.code,
            "name": metric.name,
            "unit": metric.unit,
            "min_value": metric.min_value,
            "max_value": metric.max_value,
        },
        "evidence": {
            "source": payload.source.value,
            "source_provider": payload.source_provider,
            "evidence_ref": payload.evidence_ref,
            "text": payload.evidence_text,
        },
        "parser_baseline": {
            "method": parsed["method"],
            "confidence": parsed["confidence"],
            "value": parsed["value"],
        },
    }
    body = stable_payload_text(request_payload).encode()
    try:
        async with httpx.AsyncClient(timeout=settings.performance_model_extraction_timeout_seconds) as client:
            response = await client.post(
                settings.performance_model_extraction_webhook_url,
                content=body,
                headers=performance_model_webhook_headers(settings, body, str(key_resolution["key"] or "")),
            )
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    return webhook_model_extraction_result(settings, response)


async def resolve_performance_model_webhook_key(settings: Settings) -> dict[str, str | None]:
    try:
        key = await resolve_secret(
            settings,
            env_value=settings.performance_model_extraction_webhook_key,
            path=settings.performance_model_extraction_webhook_key_secret_path,
            field_name=settings.performance_model_extraction_webhook_key_secret_field,
            label="performance model extraction webhook key",
        )
    except HTTPException:
        return {"key": None}
    return {"key": key}


def performance_model_webhook_headers(settings: Settings, body: bytes, signing_key: str = "") -> dict[str, str]:
    headers = {
        "User-Agent": "AfroLete-Performance-Extractor/1.0",
        "Content-Type": "application/json",
    }
    if signing_key:
        timestamp = str(int(time.time()))
        digest = hmac.new(signing_key.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
        headers["X-Afrolete-Performance-Model-Timestamp"] = timestamp
        headers["X-Afrolete-Performance-Model-Signature"] = f"sha256={digest}"
        headers["X-Afrolete-Performance-Model-Key-Source"] = (
            "openbao" if settings.performance_model_extraction_webhook_key_secret_path else "env"
        )
    return headers


def webhook_model_extraction_result(settings: Settings, response: httpx.Response) -> dict[str, object] | None:
    try:
        result = response.json()
    except ValueError:
        return None
    if not isinstance(result, dict):
        return None
    value = structured_float(result.get("value") or result.get("extracted_value"))
    if value is None:
        return None
    confidence = structured_float(result.get("confidence")) or 0.82
    fields = result.get("fields") if isinstance(result.get("fields"), dict) else {}
    return {
        "value": value,
        "confidence": round(max(0, min(confidence, 1)), 2),
        "method": "model_webhook_extraction",
        "model_policy": str(result.get("model") or settings.performance_model_extraction_model),
        "summary": str(result.get("summary") or "External model extracted a performance metric candidate."),
        "confidence_reason": str(
            result.get("confidence_reason")
            or "External model webhook returned a bounded metric candidate for human review."
        ),
        "fields": {str(key): str(value) for key, value in fields.items()},
    }


def should_apply_model_extraction(parsed: dict[str, object], model_assist: dict[str, object] | None) -> bool:
    if model_assist is None:
        return False
    return str(parsed["method"]) in {"numeric_text_fallback", "metric_default"}


def apply_model_extraction(
    parsed: dict[str, object],
    model_assist: dict[str, object],
) -> dict[str, object]:
    fields = {**dict(parsed["fields"]), **dict(model_assist["fields"])}
    warnings = list(parsed["warnings"])
    warnings.append("Model-assisted extraction requires human review before verification.")
    return {
        **parsed,
        "value": model_assist["value"],
        "confidence": model_assist["confidence"],
        "method": model_assist["method"],
        "confidence_reason": model_assist["confidence_reason"],
        "warnings": warnings,
        "fields": fields,
    }


def model_evaluation(
    parsed: dict[str, object],
    model_assist: dict[str, object] | None,
    model_applied: bool,
) -> dict[str, str]:
    if model_assist is None:
        return {"status": "not_attempted", "reason": "No eligible model-assisted extraction candidate was produced."}
    return {
        "status": "applied" if model_applied else "not_applied",
        "model_policy": str(model_assist["model_policy"]),
        "model_method": str(model_assist["method"]),
        "model_confidence": f"{float(model_assist['confidence']):.2f}",
        "final_method": str(parsed["method"]),
    }


def default_model_extraction_benchmark_cases() -> list[PerformanceModelExtractionBenchmarkCaseCreate]:
    return [
        PerformanceModelExtractionBenchmarkCaseCreate(
            case_id="sleep-duration-number-word",
            metric_code="sleep_minutes",
            metric_name="Sleep Minutes",
            unit="minutes",
            min_value=0,
            max_value=900,
            source=MetricSource.AUDIO_NARRATION,
            evidence_ref="benchmark://performance/sleep-duration-number-word",
            evidence_text="Recovery note: sleep duration was seven hours after travel.",
            expected_value=420,
            tolerance=0.01,
        ),
        PerformanceModelExtractionBenchmarkCaseCreate(
            case_id="video-first-touch-specific-number",
            metric_code="first_touch",
            metric_name="First Touch",
            category=MetricCategory.TECHNICAL,
            unit="score",
            min_value=0,
            max_value=10,
            source=MetricSource.VIDEO_ANALYSIS,
            evidence_ref="benchmark://performance/video-first-touch-specific-number",
            evidence_text="70th minute clip: first touch quality 8.4 under pressure after two scans.",
            expected_value=8.4,
            tolerance=0.01,
        ),
        PerformanceModelExtractionBenchmarkCaseCreate(
            case_id="agent-recovery-score",
            metric_code="recovery_score",
            metric_name="Recovery Score",
            unit="score",
            min_value=0,
            max_value=100,
            source=MetricSource.AGENT_EXTRACTED,
            evidence_ref="benchmark://performance/agent-recovery-score",
            evidence_text="Agent summary: fatigue was high but readiness improved; recovery score came out at 74.",
            expected_value=74,
            tolerance=0.01,
        ),
    ]


def benchmark_dataset_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:120] or "performance-model-benchmark"


def performance_model_benchmark_case_model(
    organization_id: UUID,
    dataset_id: UUID,
    case: PerformanceModelExtractionBenchmarkCaseCreate,
) -> PerformanceModelExtractionBenchmarkCase:
    return PerformanceModelExtractionBenchmarkCase(
        organization_id=organization_id,
        dataset_id=dataset_id,
        case_id=case.case_id,
        metric_code=case.metric_code,
        metric_name=case.metric_name,
        category=case.category,
        unit=case.unit,
        min_value=case.min_value,
        max_value=case.max_value,
        source=case.source,
        source_provider=case.source_provider,
        evidence_ref=case.evidence_ref,
        evidence_text=case.evidence_text,
        expected_value=case.expected_value,
        tolerance=case.tolerance,
        status="active",
    )


def benchmark_case_create_from_model(
    case: PerformanceModelExtractionBenchmarkCase,
) -> PerformanceModelExtractionBenchmarkCaseCreate:
    return PerformanceModelExtractionBenchmarkCaseCreate(
        case_id=case.case_id,
        metric_code=case.metric_code,
        metric_name=case.metric_name,
        category=case.category,
        unit=case.unit,
        min_value=case.min_value,
        max_value=case.max_value,
        source=case.source,
        source_provider=case.source_provider,
        evidence_ref=case.evidence_ref,
        evidence_text=case.evidence_text,
        expected_value=case.expected_value,
        tolerance=case.tolerance,
    )


async def active_benchmark_cases(
    db: AsyncSession,
    dataset_id: UUID,
) -> list[PerformanceModelExtractionBenchmarkCase]:
    return list(
        (
            await db.scalars(
                select(PerformanceModelExtractionBenchmarkCase)
                .where(PerformanceModelExtractionBenchmarkCase.dataset_id == dataset_id)
                .where(PerformanceModelExtractionBenchmarkCase.status == "active")
                .order_by(PerformanceModelExtractionBenchmarkCase.created_at.asc())
            )
        ).all()
    )


async def performance_model_benchmark_dataset_read(
    db: AsyncSession,
    dataset_id: UUID,
) -> dict[str, object]:
    dataset = await db.get(PerformanceModelExtractionBenchmarkDataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark dataset not found")
    cases = await active_benchmark_cases(db, dataset.id)
    return {
        "id": dataset.id,
        "organization_id": dataset.organization_id,
        "name": dataset.name,
        "slug": dataset.slug,
        "description": dataset.description,
        "model_policy": dataset.model_policy,
        "status": dataset.status,
        "case_count": len(cases),
        "last_run_at": dataset.last_run_at,
        "last_accuracy": dataset.last_accuracy,
        "last_mean_absolute_error": dataset.last_mean_absolute_error,
        "cases": [
            {
                "id": case.id,
                "dataset_id": case.dataset_id,
                "case_id": case.case_id,
                "metric_code": case.metric_code,
                "metric_name": case.metric_name,
                "category": case.category,
                "unit": case.unit,
                "source": case.source,
                "source_provider": case.source_provider,
                "evidence_ref": case.evidence_ref,
                "expected_value": case.expected_value,
                "tolerance": case.tolerance,
                "status": case.status,
            }
            for case in cases
        ],
    }


async def forecast_validation_profile_ids(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID | None,
) -> list[UUID]:
    if athlete_profile_id is not None:
        return [athlete_profile_id]
    return list(
        (
            await db.scalars(
                select(AthleteProfile.id)
                .where(AthleteProfile.organization_id == organization_id)
                .order_by(AthleteProfile.created_at.desc())
            )
        ).all()
    )


async def forecast_validation_worker_organization_ids(
    db: AsyncSession,
    organization_id: UUID | None,
    limit: int,
) -> list[UUID]:
    if organization_id is not None:
        has_observations = await db.scalar(
            select(func.count(AthletePerformanceObservation.id))
            .where(AthletePerformanceObservation.organization_id == organization_id)
            .where(AthletePerformanceObservation.verification_status != MetricVerificationStatus.REJECTED)
        )
        return [organization_id] if has_observations else []
    rows = list(
        (
            await db.scalars(
                select(AthletePerformanceObservation.organization_id)
                .where(AthletePerformanceObservation.verification_status != MetricVerificationStatus.REJECTED)
                .group_by(AthletePerformanceObservation.organization_id)
                .order_by(func.max(AthletePerformanceObservation.observed_at).desc())
                .limit(max(1, min(limit, 100)))
            )
        ).all()
    )
    return rows


async def forecast_validation_metric_rows(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_ids: list[UUID],
) -> list[tuple[UUID, PerformanceMetricDefinition, list[AthletePerformanceObservation]]]:
    if not athlete_profile_ids:
        return []
    rows = list(
        (
            await db.execute(
                select(AthletePerformanceObservation, PerformanceMetricDefinition)
                .join(
                    PerformanceMetricDefinition,
                    PerformanceMetricDefinition.id == AthletePerformanceObservation.metric_definition_id,
                )
                .where(AthletePerformanceObservation.organization_id == organization_id)
                .where(AthletePerformanceObservation.athlete_profile_id.in_(athlete_profile_ids))
                .where(AthletePerformanceObservation.verification_status != MetricVerificationStatus.REJECTED)
                .order_by(
                    AthletePerformanceObservation.athlete_profile_id,
                    AthletePerformanceObservation.metric_definition_id,
                    AthletePerformanceObservation.observed_at.asc(),
                )
            )
        ).all()
    )
    grouped: dict[tuple[UUID, UUID], tuple[PerformanceMetricDefinition, list[AthletePerformanceObservation]]] = {}
    for observation, metric in rows:
        key = (observation.athlete_profile_id, observation.metric_definition_id)
        if key not in grouped:
            grouped[key] = (metric, [])
        grouped[key][1].append(observation)
    return [
        (athlete_profile_id, metric, observations)
        for (athlete_profile_id, _), (metric, observations) in grouped.items()
        if len(observations) >= 3
    ]


def forecast_validation_metric_detail(
    athlete_profile_id: UUID,
    metric: PerformanceMetricDefinition,
    observations: list[AthletePerformanceObservation],
) -> dict[str, object]:
    history = observations[:-1]
    actual = observations[-1].value
    values = [observation.value for observation in history]
    trend = metric_trend_summary(values, metric.higher_is_better, metric.name, metric.unit)
    summary = forecast_scenario_summary(values, metric.higher_is_better, metric.name, metric.unit, trend)
    predicted = structured_float(summary["forecast_next_value"])
    tolerance = forecast_validation_tolerance(values, actual)
    absolute_error = round(abs(predicted - actual), 4) if predicted is not None else None
    relative_error = (
        round(absolute_error / max(abs(actual), 1.0), 4)
        if absolute_error is not None
        else None
    )
    passed = absolute_error is not None and absolute_error <= tolerance
    drifted = relative_error is not None and relative_error >= 0.12
    return {
        "athlete_profile_id": athlete_profile_id,
        "metric_definition_id": metric.id,
        "metric_code": metric.code,
        "metric_name": metric.name,
        "sample_size": len(history),
        "predicted_value": predicted,
        "actual_value": actual,
        "absolute_error": absolute_error,
        "relative_error": relative_error,
        "tolerance": tolerance,
        "passed": passed,
        "drifted": drifted,
    }


def forecast_validation_tolerance(values: list[float], actual: float) -> float:
    band = forecast_band(values)
    relative_floor = abs(actual) * 0.08
    return round(max(0.01, band, relative_floor), 4)


def forecast_validation_drift_level(mean_relative_error: float, drift_count: int, evaluated_count: int) -> str:
    if evaluated_count == 0:
        return "no_data"
    drift_ratio = drift_count / evaluated_count
    if mean_relative_error >= 0.25 or drift_ratio >= 0.5:
        return "high"
    if mean_relative_error >= 0.12 or drift_ratio >= 0.25:
        return "watch"
    return "stable"


def forecast_validation_recommendation(
    drift_level: str,
    mean_relative_error: float,
    drift_count: int,
    evaluated_count: int,
) -> str:
    if drift_level == "no_data":
        return "Record at least three accepted observations per athlete metric before validating forecast drift."
    percent = round(mean_relative_error * 100, 1)
    if drift_level == "high":
        return (
            f"Forecast drift is high across {drift_count}/{evaluated_count} metric backtests "
            f"with {percent}% mean relative error; recalibrate model-provider settings before using forecasts for selection."
        )
    if drift_level == "watch":
        return (
            f"Forecast drift is on watch across {drift_count}/{evaluated_count} metric backtests "
            f"with {percent}% mean relative error; review outlier metrics and collect another observation cycle."
        )
    return (
        f"Forecast backtests are stable across {evaluated_count} metric(s) with {percent}% mean relative error; "
        "continue routine monitoring."
    )


def forecast_validation_model_policy(settings: Settings) -> str:
    if settings.performance_forecast_mode == "webhook":
        return settings.performance_forecast_model
    return "deterministic_forecast_v1_backtest"


def forecast_validation_run_read(run: PerformanceForecastValidationRun) -> dict[str, object]:
    details: list[dict[str, object]] = []
    if run.details_json:
        try:
            payload = json.loads(run.details_json)
        except ValueError:
            payload = {}
        if isinstance(payload, dict) and isinstance(payload.get("details"), list):
            details = [detail for detail in payload["details"] if isinstance(detail, dict)]
    return {
        "id": run.id,
        "organization_id": run.organization_id,
        "athlete_profile_id": run.athlete_profile_id,
        "model_policy": run.model_policy,
        "forecast_mode": run.forecast_mode,
        "metric_count": run.metric_count,
        "evaluated_count": run.evaluated_count,
        "passed_count": run.passed_count,
        "drift_count": run.drift_count,
        "mean_absolute_error": run.mean_absolute_error,
        "mean_relative_error": run.mean_relative_error,
        "max_absolute_error": run.max_absolute_error,
        "drift_level": run.drift_level,
        "recommendation": run.recommendation,
        "details": details,
        "created_at": run.created_at,
    }


def normalized_performance_alert_channels(
    channels: list[CommunicationChannel] | None,
) -> list[CommunicationChannel]:
    selected = channels or [CommunicationChannel.IN_APP]
    normalized: list[CommunicationChannel] = []
    for channel in selected:
        if channel not in normalized:
            normalized.append(channel)
    return normalized or [CommunicationChannel.IN_APP]


async def performance_manager_recipient_ids(db: AsyncSession, organization_id: UUID) -> set[UUID]:
    rows = (
        await db.execute(
            select(Membership.subject_id)
            .where(Membership.organization_id == organization_id)
            .where(Membership.subject_type == MemberSubjectType.PERSON)
            .where(
                Membership.role.in_(
                    [
                        MembershipRole.OWNER,
                        MembershipRole.ADMIN,
                        MembershipRole.STAFF,
                        MembershipRole.COACH,
                    ]
                )
            )
            .where(Membership.status == "active")
        )
    ).all()
    return {person_id for (person_id,) in rows}


async def recent_forecast_validation_alert_exists(
    db: AsyncSession,
    organization_id: UUID,
    repeat_after_hours: int,
) -> bool:
    sent_after = datetime.now(UTC) - timedelta(hours=repeat_after_hours)
    existing = await db.scalar(
        select(CommunicationMessage.id)
        .where(CommunicationMessage.organization_id == organization_id)
        .where(CommunicationMessage.scope_type == CommunicationScopeType.ORGANIZATION)
        .where(CommunicationMessage.scope_id == organization_id)
        .where(CommunicationMessage.message_type == CommunicationMessageType.ALERT)
        .where(CommunicationMessage.subject.ilike("%forecast drift%"))
        .where(CommunicationMessage.sent_at.is_not(None))
        .where(CommunicationMessage.sent_at >= sent_after)
        .limit(1)
    )
    return existing is not None


async def create_forecast_validation_alert_messages(
    db: AsyncSession,
    run: PerformanceForecastValidationRun,
    recipient_ids: set[UUID],
    channels: list[CommunicationChannel],
) -> list[CommunicationMessage]:
    messages: list[CommunicationMessage] = []
    for channel in channels:
        messages.append(
            await create_forecast_validation_alert_message_for_channel(
                db,
                run,
                recipient_ids,
                channel,
            )
        )
    return messages


async def create_forecast_validation_alert_message_for_channel(
    db: AsyncSession,
    run: PerformanceForecastValidationRun,
    recipient_ids: set[UUID],
    channel: CommunicationChannel,
) -> CommunicationMessage:
    now = datetime.now(UTC)
    message = CommunicationMessage(
        organization_id=run.organization_id,
        template_id=None,
        created_by_person_id=None,
        message_type=CommunicationMessageType.ALERT,
        channel=channel,
        scope_type=CommunicationScopeType.ORGANIZATION,
        scope_id=run.organization_id,
        subject=forecast_validation_alert_subject(run),
        body=forecast_validation_alert_body(run),
        urgent=run.drift_level == "high",
        quiet_hours_override=run.drift_level == "high",
        scheduled_for=None,
        sent_at=now,
        status="sent",
    )
    db.add(message)
    await db.flush()
    for person_id in sorted(recipient_ids, key=str):
        person = await db.get(Person, person_id)
        if person is None:
            continue
        db.add(
            MessageRecipient(
                message_id=message.id,
                person_id=person.id,
                destination=destination_for_channel(person, channel),
                delivery_status=initial_delivery_status(person, channel),
            )
        )
    return message


def forecast_validation_alert_subject(run: PerformanceForecastValidationRun) -> str:
    return f"Performance forecast drift {run.drift_level}: {run.drift_count} metric(s)"


def forecast_validation_alert_body(run: PerformanceForecastValidationRun) -> str:
    details = forecast_validation_run_read(run)["details"]
    drifted = [detail for detail in details if detail.get("drifted")]
    metric_summary = "; ".join(
        f"{detail['metric_name']} predicted {detail.get('predicted_value')} vs actual {detail.get('actual_value')}"
        for detail in drifted[:5]
    )
    if not metric_summary:
        metric_summary = "No individual metric crossed the drift threshold, but aggregate error needs review."
    return (
        f"Forecast validation run {run.id} is {run.drift_level}. "
        f"{run.passed_count}/{run.evaluated_count} backtests passed, "
        f"{run.drift_count} metric(s) drifted, mean relative error is {round(run.mean_relative_error * 100, 1)}%. "
        f"{run.recommendation} Metrics: {metric_summary}."
    )


async def evaluate_model_extraction_benchmark_case(
    settings: Settings,
    organization_id: UUID,
    case: PerformanceModelExtractionBenchmarkCaseCreate,
) -> dict[str, object]:
    metric = PerformanceMetricDefinition(
        id=uuid4(),
        organization_id=organization_id,
        sport="benchmark",
        code=case.metric_code,
        name=case.metric_name,
        category=case.category,
        unit=case.unit,
        min_value=case.min_value,
        max_value=case.max_value,
        weight=1.0,
        higher_is_better=True,
        status="active",
    )
    ingestion_payload = PerformanceIngestionCreate(
        organization_id=organization_id,
        athlete_profile_id=uuid4(),
        metric_definition_id=metric.id,
        source=case.source,
        source_provider=case.source_provider,
        evidence_ref=case.evidence_ref,
        evidence_text=case.evidence_text,
    )
    parsed = parse_performance_evidence(ingestion_payload, metric)
    model_assist = await model_assisted_performance_extraction(settings, ingestion_payload, metric, parsed)
    model_applied = False
    if should_apply_model_extraction(parsed, model_assist):
        parsed = apply_model_extraction(parsed, model_assist)
        model_applied = True
    extracted_value = float(parsed["value"])
    absolute_error = round(abs(extracted_value - case.expected_value), 4)
    return {
        "case_id": case.case_id,
        "metric_code": case.metric_code,
        "source": case.source,
        "expected_value": case.expected_value,
        "extracted_value": extracted_value,
        "absolute_error": absolute_error,
        "tolerance": case.tolerance,
        "passed": absolute_error <= case.tolerance,
        "parser_method": parsed["method"],
        "model_assisted": model_applied,
        "model_policy": model_assist["model_policy"] if model_assist else None,
        "confidence": parsed["confidence"],
        "summary": (
            f"{case.case_id}: expected {case.expected_value:g}, extracted {extracted_value:g} "
            f"via {parsed['method']}."
        ),
    }


def model_metric_text_value(text: str, metric: PerformanceMetricDefinition) -> float | None:
    metric_labels = {metric.code, metric.name}
    metric_labels.update(PROVIDER_METRIC_ALIASES.get(metric.code, set()))
    for label in sorted(metric_labels, key=len, reverse=True):
        if not label:
            continue
        value = number_near_metric_label(text, label)
        if value is not None:
            return convert_model_value_for_metric(value, metric, text)
    if metric.code == "sleep_minutes":
        sleep_value = sleep_duration_from_text(text)
        if sleep_value is not None:
            return sleep_value
    return None


def number_near_metric_label(text: str, label: str) -> float | None:
    normalized = text.replace("_", " ")
    label_words = re.sub(r"([a-z])([A-Z])", r"\1 \2", label).replace("_", " ")
    label_pattern = re.escape(label_words)
    value_pattern = r"(-?\d+(?:\.\d+)?|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    patterns = [
        rf"{label_pattern}\D{{0,80}}{value_pattern}",
        rf"{value_pattern}\D{{0,80}}{label_pattern}",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            return numeric_word_or_float(match.group(1))
    return None


def numeric_word_or_float(value: str) -> float | None:
    normalized = value.strip().lower()
    if normalized in NUMBER_WORDS:
        return float(NUMBER_WORDS[normalized])
    return structured_float(normalized)


def convert_model_value_for_metric(value: float, metric: PerformanceMetricDefinition, text: str) -> float:
    if metric.code in {"sleep_minutes", "sleep_duration_minutes"} and re.search(r"\bhours?\b", text, re.IGNORECASE):
        return round(value * 60, 2)
    return value


def sleep_duration_from_text(text: str) -> float | None:
    value_pattern = r"(-?\d+(?:\.\d+)?|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    match = re.search(rf"(?:sleep|slept|asleep)\D{{0,80}}{value_pattern}\s*(hours?|hrs?|minutes?|mins?)", text, re.IGNORECASE)
    if not match:
        return None
    value = numeric_word_or_float(match.group(1))
    if value is None:
        return None
    unit = match.group(2).lower()
    return round(value * 60, 2) if unit.startswith(("hour", "hr")) else value


def decode_structured_evidence(text: str | None) -> object | None:
    if not text:
        return None
    stripped = text.strip()
    if not stripped or stripped[0] not in "[{":
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


PROVIDER_METRIC_ALIASES: dict[str, set[str]] = {
    "hrv": {
        "hrv",
        "hrv_rmssd",
        "hrv_rmssd_milli",
        "heart_rate_variability",
        "heart_rate_variability_sdnn",
        "heartratevariability",
        "HKQuantityTypeIdentifierHeartRateVariabilitySDNN",
    },
    "resting_heart_rate": {
        "resting_heart_rate",
        "resting_hr",
        "restingHeartRate",
        "resting_pulse",
        "HKQuantityTypeIdentifierRestingHeartRate",
    },
    "recovery_score": {"recovery", "recovery_score", "readiness", "readiness_score"},
    "hydration_score": {"hydration", "hydration_score"},
    "sleep_minutes": {
        "sleep_minutes",
        "sleep_duration_minutes",
        "sleepDurationInSeconds",
        "totalMinutesAsleep",
    },
    "sleep_hours": {"sleep_hours", "sleep_duration_hours"},
    "sleep_quality": {"sleep_quality", "sleep_score", "sleep_performance_percentage", "efficiency"},
    "strain": {"strain", "strain_score", "day_strain"},
    "stress": {"stress", "stress_score", "averageStressLevel", "stressLevel"},
    "temperature": {
        "temperature",
        "body_temperature",
        "body_temp",
        "HKQuantityTypeIdentifierBodyTemperature",
    },
    "body_battery": {"body_battery", "bodyBatteryMostRecentValue", "bodyBattery"},
    "player_load": {"player_load", "playerLoad", "workload", "total_load"},
    "total_distance": {"total_distance", "total_distance_m", "distance", "distance_meters"},
    "max_speed": {"max_speed", "max_velocity", "top_speed", "maxVelocity"},
    "high_speed_distance": {"high_speed_distance", "highSpeedRunningDistance", "hsr_distance"},
    "accelerations": {"accelerations", "acceleration_count", "high_intensity_accelerations"},
    "decelerations": {"decelerations", "deceleration_count", "high_intensity_decelerations"},
    "average_heart_rate": {"average_heart_rate", "avg_hr", "averageHeartRate", "heart_rate_average"},
}


def performance_source_provider(
    payload: PerformanceIngestionCreate,
    structured_payload: object | None,
) -> str | None:
    explicit = normalized_provider_name(payload.source_provider)
    if explicit:
        return explicit
    ref_provider = normalized_provider_name(payload.evidence_ref.partition("://")[0])
    if ref_provider and ref_provider not in {"video", "audio", "text", "manual", "stats", "file"}:
        return ref_provider
    return provider_from_structured_payload(structured_payload)


def normalized_provider_name(value: str | None) -> str | None:
    if not value:
        return None
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return normalized or None


def provider_from_structured_payload(data: object | None) -> str | None:
    if isinstance(data, list):
        for item in data:
            detected = provider_from_structured_payload(item)
            if detected is not None:
                return detected
        return None
    if not isinstance(data, dict):
        return None
    for key in ("provider", "source_provider", "vendor", "source", "application"):
        value = data.get(key)
        if isinstance(value, dict):
            value = value.get("name") or value.get("provider")
        provider = normalized_provider_name(str(value)) if value is not None else None
        if provider:
            return provider
    keys = {str(key) for key in data}
    if {"recovery", "strain"} & keys:
        return "whoop"
    if {"summaryType", "calendarDate", "bodyBatteryMostRecentValue"} & keys:
        return "garmin"
    if "HKQuantityTypeIdentifier" in json.dumps(list(keys)):
        return "apple_health"
    if {"activities", "sleep", "summary"} & keys and "fitbit" in json.dumps(data).lower():
        return "fitbit"
    if {"polar_user", "heart_rate", "hrv", "sleep"} & keys:
        return "polar"
    if {"readiness", "daily_readiness", "sleep", "daily_sleep"} & keys and "oura" in json.dumps(data).lower():
        return "oura"
    if {"playerLoad", "player_load", "athlete_load", "total_distance_m", "max_velocity"} & keys:
        return "catapult"
    return None


def provider_specific_metric_match(
    data: object,
    metric: PerformanceMetricDefinition,
    provider: str,
) -> dict[str, object] | None:
    candidates = provider_specific_metric_candidates(data, provider)
    if not candidates:
        return None
    return structured_metric_match(candidates, metric)


def provider_specific_metric_candidates(data: object, provider: str) -> list[dict[str, object]]:
    if provider == "whoop":
        return whoop_metric_candidates(data)
    if provider == "garmin":
        return garmin_metric_candidates(data)
    if provider in {"apple", "apple_health", "healthkit"}:
        return apple_health_metric_candidates(data)
    if provider == "fitbit":
        return fitbit_metric_candidates(data)
    if provider == "polar":
        return polar_metric_candidates(data)
    if provider == "oura":
        return oura_metric_candidates(data)
    if provider in {"catapult", "statsports", "playertek"}:
        return gps_workload_metric_candidates(data, provider)
    return []


def whoop_metric_candidates(data: object) -> list[dict[str, object]]:
    if not isinstance(data, dict):
        return []
    observed_at = first_string_value(data, "observed_at", "timestamp", "created_at", "updated_at", "start_time")
    recovery = dict_value(data, "recovery", "recovery_score")
    sleep = dict_value(data, "sleep", "sleep_score")
    strain = dict_value(data, "strain", "day_strain")
    candidates: list[dict[str, object]] = []
    add_provider_candidate(candidates, "recovery_score", nested_number(recovery, "score", "recovery_score"), "whoop", observed_at, "recovery.score")
    add_provider_candidate(candidates, "hrv", nested_number(recovery, "hrv_rmssd_milli", "hrv_rmssd", "hrv"), "whoop", observed_at, "recovery.hrv")
    add_provider_candidate(
        candidates,
        "resting_heart_rate",
        nested_number(recovery, "resting_heart_rate", "resting_hr"),
        "whoop",
        observed_at,
        "recovery.resting_heart_rate",
    )
    add_provider_candidate(
        candidates,
        "sleep_quality",
        nested_number(sleep, "score", "sleep_score", "sleep_performance_percentage"),
        "whoop",
        observed_at,
        "sleep.score",
    )
    add_provider_candidate(candidates, "strain", nested_number(strain, "score", "strain", "day_strain"), "whoop", observed_at, "strain.score")
    return candidates


def garmin_metric_candidates(data: object) -> list[dict[str, object]]:
    payload = first_dict_payload(data)
    if payload is None:
        return []
    observed_at = first_string_value(payload, "observed_at", "timestamp", "calendarDate", "startTimeInSeconds")
    candidates: list[dict[str, object]] = []
    for code, keys in {
        "resting_heart_rate": ("restingHeartRate", "resting_heart_rate"),
        "stress": ("averageStressLevel", "stressLevel", "stress_score"),
        "body_battery": ("bodyBatteryMostRecentValue", "bodyBattery"),
        "sleep_minutes": ("sleepDurationInSeconds", "durationInSeconds"),
        "sleep_quality": ("sleepScore", "sleep_score"),
        "hrv": ("lastNightAvg", "weeklyAvg", "hrv"),
    }.items():
        value = deep_number(payload, *keys)
        if value is not None and code == "sleep_minutes" and value > 1440:
            value = round(value / 60, 2)
        add_provider_candidate(candidates, code, value, "garmin", observed_at, ".".join(keys))
    return candidates


def apple_health_metric_candidates(data: object) -> list[dict[str, object]]:
    rows = data if isinstance(data, list) else data.get("data", data.get("samples", [])) if isinstance(data, dict) else []
    if isinstance(rows, dict):
        rows = [rows]
    candidates: list[dict[str, object]] = []
    if not isinstance(rows, list):
        return candidates
    for row in rows:
        if not isinstance(row, dict):
            continue
        metric_type = str(row.get("type") or row.get("identifier") or row.get("name") or "")
        code = apple_health_metric_code(metric_type)
        if code is None:
            continue
        value = provider_numeric_value(row) or structured_float(row.get("duration_minutes"))
        if value is None:
            continue
        add_provider_candidate(
            candidates,
            code,
            value,
            "apple_health",
            first_string_value(row, "observed_at", "date", "startDate", "endDate"),
            metric_type,
            unit=str(row.get("unit") or ""),
        )
    return candidates


def fitbit_metric_candidates(data: object) -> list[dict[str, object]]:
    payload = first_dict_payload(data)
    if payload is None:
        return []
    observed_at = first_string_value(payload, "observed_at", "dateOfSleep", "dateTime")
    sleep_summary = dict_value(dict_value(payload, "sleep"), "summary")
    summary = dict_value(payload, "summary")
    candidates: list[dict[str, object]] = []
    add_provider_candidate(
        candidates,
        "resting_heart_rate",
        deep_number(payload, "restingHeartRate", "resting_heart_rate"),
        "fitbit",
        observed_at,
        "summary.restingHeartRate",
    )
    add_provider_candidate(
        candidates,
        "sleep_minutes",
        nested_number(sleep_summary, "totalMinutesAsleep", "minutesAsleep"),
        "fitbit",
        observed_at,
        "sleep.summary.totalMinutesAsleep",
    )
    add_provider_candidate(
        candidates,
        "sleep_quality",
        nested_number(sleep_summary, "efficiency", "sleepScore") or nested_number(summary, "sleepScore"),
        "fitbit",
        observed_at,
        "sleep.summary.efficiency",
    )
    return candidates


def polar_metric_candidates(data: object) -> list[dict[str, object]]:
    payload = first_dict_payload(data)
    if payload is None:
        return []
    observed_at = first_string_value(payload, "observed_at", "date", "recorded_at", "start_time", "timestamp")
    heart_rate = dict_value(payload, "heart_rate", "heartRate")
    hrv = dict_value(payload, "hrv", "heart_rate_variability")
    sleep = dict_value(payload, "sleep", "sleep_summary")
    candidates: list[dict[str, object]] = []
    add_provider_candidate(
        candidates,
        "resting_heart_rate",
        nested_number(heart_rate, "resting", "resting_hr", "restingHeartRate") or deep_number(payload, "restingHeartRate"),
        "polar",
        observed_at,
        "heart_rate.resting",
    )
    add_provider_candidate(
        candidates,
        "average_heart_rate",
        nested_number(heart_rate, "average", "avg", "averageHeartRate") or deep_number(payload, "averageHeartRate"),
        "polar",
        observed_at,
        "heart_rate.average",
    )
    add_provider_candidate(
        candidates,
        "hrv",
        nested_number(hrv, "rmssd", "hrv_rmssd", "nightlyRechargeHrv") or deep_number(payload, "nightlyRechargeHrv"),
        "polar",
        observed_at,
        "hrv.rmssd",
    )
    add_provider_candidate(
        candidates,
        "sleep_minutes",
        sleep_duration_minutes(
            nested_number(sleep, "duration_minutes", "total_sleep_minutes", "sleepDurationMinutes")
            or deep_number(payload, "sleepDurationMinutes")
            or nested_number(sleep, "duration_seconds", "total_sleep_seconds")
        ),
        "polar",
        observed_at,
        "sleep.duration",
    )
    add_provider_candidate(
        candidates,
        "sleep_quality",
        nested_number(sleep, "score", "sleep_score", "sleepScore") or deep_number(payload, "sleepScore"),
        "polar",
        observed_at,
        "sleep.score",
    )
    return candidates


def oura_metric_candidates(data: object) -> list[dict[str, object]]:
    payload = first_dict_payload(data)
    if payload is None:
        return []
    readiness = dict_value(payload, "readiness", "daily_readiness")
    sleep = dict_value(payload, "sleep", "daily_sleep")
    observed_at = first_string_value(payload, "observed_at", "day", "date", "timestamp")
    candidates: list[dict[str, object]] = []
    add_provider_candidate(
        candidates,
        "recovery_score",
        nested_number(readiness, "score", "readiness_score") or deep_number(payload, "readiness_score"),
        "oura",
        observed_at,
        "readiness.score",
    )
    add_provider_candidate(
        candidates,
        "hrv",
        nested_number(readiness, "average_hrv", "hrv", "rmssd") or deep_number(payload, "average_hrv"),
        "oura",
        observed_at,
        "readiness.average_hrv",
    )
    add_provider_candidate(
        candidates,
        "resting_heart_rate",
        nested_number(readiness, "resting_heart_rate", "lowest_resting_heart_rate")
        or nested_number(sleep, "lowest_resting_heart_rate", "average_heart_rate")
        or deep_number(payload, "lowest_resting_heart_rate"),
        "oura",
        observed_at,
        "readiness.resting_heart_rate",
    )
    add_provider_candidate(
        candidates,
        "sleep_minutes",
        sleep_duration_minutes(
            nested_number(sleep, "total_sleep_duration", "total_sleep_duration_seconds", "duration_seconds")
            or deep_number(payload, "total_sleep_duration")
        ),
        "oura",
        observed_at,
        "sleep.total_sleep_duration",
    )
    add_provider_candidate(
        candidates,
        "sleep_quality",
        nested_number(sleep, "score", "sleep_score") or deep_number(payload, "sleep_score"),
        "oura",
        observed_at,
        "sleep.score",
    )
    add_provider_candidate(
        candidates,
        "temperature",
        nested_number(readiness, "temperature_deviation", "temperature") or deep_number(payload, "temperature_deviation"),
        "oura",
        observed_at,
        "readiness.temperature_deviation",
    )
    return candidates


def gps_workload_metric_candidates(data: object, provider: str) -> list[dict[str, object]]:
    payload = first_dict_payload(data)
    if payload is None:
        return []
    session = dict_value(payload, "session", "metrics", "summary", "workload")
    observed_at = first_string_value(payload, "observed_at", "timestamp", "start_time", "session_start", "date")
    candidates: list[dict[str, object]] = []
    for code, keys, source_path in (
        ("player_load", ("playerLoad", "player_load", "athlete_load", "workload", "total_load"), "metrics.player_load"),
        ("total_distance", ("total_distance_m", "distance_meters", "distance", "totalDistance"), "metrics.total_distance"),
        ("max_speed", ("max_velocity", "max_speed", "top_speed", "maxVelocity"), "metrics.max_speed"),
        (
            "high_speed_distance",
            ("high_speed_distance", "highSpeedRunningDistance", "hsr_distance"),
            "metrics.high_speed_distance",
        ),
        (
            "accelerations",
            ("accelerations", "acceleration_count", "high_intensity_accelerations"),
            "metrics.accelerations",
        ),
        (
            "decelerations",
            ("decelerations", "deceleration_count", "high_intensity_decelerations"),
            "metrics.decelerations",
        ),
        ("average_heart_rate", ("average_heart_rate", "avg_hr", "averageHeartRate"), "metrics.average_heart_rate"),
    ):
        value = nested_number(session, *keys) or deep_number(payload, *keys)
        add_provider_candidate(candidates, code, value, provider, observed_at, source_path)
    return candidates


def sleep_duration_minutes(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value / 60, 2) if value > 1440 else value


def add_provider_candidate(
    candidates: list[dict[str, object]],
    code: str,
    value: float | None,
    provider: str,
    observed_at: str | None,
    source_path: str,
    unit: str = "",
) -> None:
    if value is None:
        return
    candidates.append(
        {
            "code": code,
            "metric": code,
            "metric_name": code.replace("_", " "),
            "value": value,
            "provider": provider,
            "source_path": source_path,
            "unit": unit,
            "observed_at": observed_at,
        }
    )


def dict_value(data: object, *keys: str) -> dict[str, object]:
    if not isinstance(data, dict):
        return {}
    for key in keys:
        value = data.get(key)
        if isinstance(value, dict):
            return value
    return {}


def first_dict_payload(data: object) -> dict[str, object] | None:
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                return item
    return None


def first_string_value(data: object, *keys: str) -> str | None:
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, int | float):
            return str(value)
    return None


def nested_number(data: object, *keys: str) -> float | None:
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = structured_float(data.get(key))
        if value is not None:
            return value
    return None


def deep_number(data: object, *keys: str) -> float | None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys:
                parsed = structured_float(value)
                if parsed is not None:
                    return parsed
            nested = deep_number(value, *keys)
            if nested is not None:
                return nested
    elif isinstance(data, list):
        for item in data:
            nested = deep_number(item, *keys)
            if nested is not None:
                return nested
    return None


def apple_health_metric_code(metric_type: str) -> str | None:
    normalized = normalized_text(metric_type)
    if "heartratevariability" in normalized:
        return "hrv"
    if "restingheartrate" in normalized:
        return "resting_heart_rate"
    if "bodytemperature" in normalized:
        return "temperature"
    if "sleepanalysis" in normalized:
        return "sleep_minutes"
    return None


def structured_metric_match(
    data: object,
    metric: PerformanceMetricDefinition,
) -> dict[str, object] | None:
    candidates = list(iter_metric_candidates(data))
    if not candidates:
        return None
    metric_tokens = normalized_metric_tokens(metric)
    scored: list[tuple[int, dict[str, object]]] = []
    for candidate in candidates:
        label_tokens = normalized_candidate_tokens(candidate)
        score = 0
        if label_tokens & metric_tokens:
            score += 10
        if normalized_text(str(candidate.get("metric_definition_id", ""))) == normalized_text(str(metric.id)):
            score += 20
        if not label_tokens and len(candidates) == 1:
            score += 3
        if score > 0:
            scored.append((score, candidate))
    if not scored:
        return candidates[0] if len(candidates) == 1 else None
    return sorted(scored, key=lambda item: item[0], reverse=True)[0][1]


def iter_metric_candidates(data: object) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    if isinstance(data, list):
        for item in data:
            candidates.extend(iter_metric_candidates(item))
        return candidates
    if not isinstance(data, dict):
        return candidates

    value = provider_numeric_value(data)
    if value is not None:
        candidate = dict(data)
        candidate["value"] = value
        candidates.append(candidate)

    for key, item in data.items():
        if isinstance(item, (list, dict)) and key in {
            "data",
            "metrics",
            "observations",
            "readings",
            "results",
            "samples",
            "stats",
        }:
            candidates.extend(iter_metric_candidates(item))
        elif isinstance(item, int | float) and not isinstance(item, bool):
            candidates.append({"metric": key, "source_key": key, "value": float(item)})
        elif isinstance(item, str) and key not in {"id", "athlete_id", "timestamp", "observed_at"}:
            numeric = structured_float(item)
            if numeric is not None:
                candidates.append({"metric": key, "source_key": key, "value": numeric})
    return candidates


def provider_numeric_value(data: dict[str, object]) -> float | None:
    for key in ("value", "metric_value", "score", "result", "reading", "measurement"):
        value = structured_float(data.get(key))
        if value is not None:
            return value
    return None


def structured_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        return float(match.group(0)) if match else None
    return None


def normalized_metric_tokens(metric: PerformanceMetricDefinition) -> set[str]:
    tokens = {
        token
        for token in {
            normalized_text(metric.code),
            normalized_text(metric.name),
            normalized_text(metric.description or ""),
        }
        if token
    }
    return expand_metric_alias_tokens(tokens)


def normalized_candidate_tokens(candidate: dict[str, object]) -> set[str]:
    labels = []
    for key in (
        "code",
        "metric_code",
        "metric",
        "metric_name",
        "name",
        "label",
        "stat",
        "type",
        "source_key",
    ):
        value = candidate.get(key)
        if value is not None:
            labels.append(normalized_text(str(value)))
    return expand_metric_alias_tokens({label for label in labels if label})


def expand_metric_alias_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for canonical, aliases in PROVIDER_METRIC_ALIASES.items():
        alias_tokens = {normalized_text(alias) for alias in aliases}
        canonical_token = normalized_text(canonical)
        if canonical_token in tokens or alias_tokens & tokens:
            expanded.add(canonical_token)
            expanded.update(alias_tokens)
    return expanded


def normalized_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def extract_metric_specific_text_value(
    text: str | None,
    metric: PerformanceMetricDefinition,
) -> float | None:
    if not text:
        return None
    labels = [metric.code, metric.name]
    labels.extend(part for part in re.split(r"[_\-\s]+", metric.name) if len(part) >= 4)
    for label in labels:
        escaped = re.escape(label.replace("_", " "))
        patterns = [
            rf"{escaped}\D{{0,60}}(-?\d+(?:\.\d+)?)",
            rf"(-?\d+(?:\.\d+)?)\D{{0,60}}{escaped}",
        ]
        normalized = text.replace("_", " ")
        for pattern in patterns:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                return float(match.group(1))
    return None


def primitive_parser_fields(candidate: dict[str, object]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for key, value in candidate.items():
        if isinstance(value, str | int | float | bool) or value is None:
            fields[key] = "" if value is None else str(value)
    return fields


def parsed_provider_observed_at(candidate: dict[str, object]) -> datetime | None:
    for key in ("observed_at", "timestamp", "time", "recorded_at"):
        value = candidate.get(key)
        if not isinstance(value, str):
            continue
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    return None


def evidence_raw_value(evidence_text: str | None, value: float) -> str:
    if evidence_text:
        return evidence_text[:160]
    return f"{value:g}"


def default_value_for_metric(metric: PerformanceMetricDefinition) -> float:
    if metric.min_value is not None and metric.max_value is not None:
        return round((metric.min_value + metric.max_value) / 2, 2)
    if metric.max_value is not None:
        return round(metric.max_value * 0.7, 2)
    return 1.0


def source_confidence(source: MetricSource) -> float:
    return {
        MetricSource.VIDEO_ANALYSIS: 0.78,
        MetricSource.AUDIO_NARRATION: 0.68,
        MetricSource.WEARABLE: 0.86,
        MetricSource.AGENT_EXTRACTED: 0.74,
        MetricSource.OFFICIAL_STATS: 0.9,
        MetricSource.COACH_EVALUATION: 0.8,
        MetricSource.SELF_ASSESSMENT: 0.55,
        MetricSource.MANUAL: 0.65,
    }[source]


def extractor_name(source: MetricSource) -> str:
    return {
        MetricSource.VIDEO_ANALYSIS: "afrolete-video-metric-extractor",
        MetricSource.AUDIO_NARRATION: "afrolete-audio-narration-parser",
        MetricSource.WEARABLE: "afrolete-wearable-feed-normalizer",
        MetricSource.AGENT_EXTRACTED: "afrolete-agent-observation-reviewer",
        MetricSource.OFFICIAL_STATS: "afrolete-official-stats-importer",
        MetricSource.COACH_EVALUATION: "afrolete-coach-note-parser",
        MetricSource.SELF_ASSESSMENT: "afrolete-self-report-parser",
        MetricSource.MANUAL: "afrolete-manual-entry",
    }[source]
