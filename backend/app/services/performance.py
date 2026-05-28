from datetime import UTC, date, datetime, timedelta
import re
from statistics import pstdev
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import CommunicationMessage, MessageRecipient
from app.models.enums import (
    CommunicationChannel,
    CommunicationMessageType,
    CommunicationScopeType,
    MemberSubjectType,
    MembershipRole,
    MetricSource,
    MetricVerificationStatus,
    SafeguardingIncidentStatus,
    SafeguardingIncidentType,
    WeatherAlertLevel,
)
from app.models.assets import Facility
from app.models.event import Event, EventWeatherAssessment, SafeguardingIncident
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.performance import (
    AthleteAssessment,
    AthletePerformanceObservation,
    PerformanceAchievementAward,
    PerformanceGoal,
    PerformanceMetricDefinition,
)
from app.models.team import AthleteProfile, Team, TeamRosterEntry
from app.models.training import TrainingSessionFeedback, TrainingSessionPlan
from app.schemas.performance import (
    AssessmentReviewLoadRead,
    AssessmentReviewQueueSummaryRead,
    AthleteAssessmentCreate,
    AthleteAssessmentReviewAssignmentUpdate,
    AthleteAssessmentReviewCreate,
    PerformanceAssessmentReviewEscalationRunRead,
    PerformanceInjuryRiskAlertRunRead,
    MetricDefinitionCreate,
    PerformanceAchievementWorkerRunRead,
    PerformanceGoalCreate,
    PerformanceIngestionCreate,
    PerformanceObservationCreate,
    PerformanceObservationReviewCreate,
    PlayerSelfAssessmentCreate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.communications import (
    destination_for_channel,
    guardian_person_ids,
    initial_delivery_status,
)


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

    value = payload.extracted_value
    if value is None:
        value = extract_numeric_value(payload.evidence_text) or default_value_for_metric(metric)
    confidence = payload.confidence if payload.confidence is not None else source_confidence(payload.source)
    observation = AthletePerformanceObservation(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile.id,
        metric_definition_id=metric.id,
        event_id=payload.event_id,
        recorded_by_person_id=identity.person_id,
        value=value,
        raw_value=payload.evidence_text[:160] if payload.evidence_text else str(value),
        observed_at=payload.observed_at or datetime.now(UTC),
        source=payload.source,
        confidence=confidence,
        verification_status=MetricVerificationStatus.PENDING_REVIEW,
        notes=(
            f"Ingested from {payload.source.value} evidence {payload.evidence_ref}. "
            f"Metric: {metric.name}. Review before promoting to verified."
        ),
    )
    db.add(observation)
    await db.commit()
    await db.refresh(observation)
    return {
        "observation": observation,
        "evidence_ref": payload.evidence_ref,
        "extractor": extractor_name(payload.source),
        "confidence": confidence,
        "review_required": True,
        "summary": (
            f"Extracted {metric.name}={value:g}{' ' + metric.unit if metric.unit else ''} "
            f"from {payload.source.value} evidence."
        ),
    }


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
    cohort_scopes: tuple[str, ...] = ("tenant", "age_group", "position", "region"),
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


async def performance_metric_trends(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
    sport: str | None = None,
) -> list[dict[str, object]]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
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
) -> list[dict[str, object]]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
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
                    AthletePerformanceObservation.observed_at.desc(),
                )
            )
        ).all()
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
        scenarios.append(
            {
                "metric_definition_id": metric.id,
                "metric_code": metric.code,
                "metric_name": metric.name,
                "sport": metric.sport,
                "category": metric.category,
                "unit": metric.unit,
                "higher_is_better": metric.higher_is_better,
                **forecast_scenario_summary(values, metric.higher_is_better, metric.name, metric.unit, trend),
            }
        )
    return scenarios


async def performance_forecast_what_if_scenarios(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
    sport: str | None = None,
    training_adjustment_percent: float = 0.0,
    readiness_score: int = 70,
    horizon: int = 4,
) -> list[dict[str, object]]:
    await get_athlete_profile(db, athlete_profile_id, organization_id)
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
        scenarios.append(
            {
                "metric_definition_id": metric.id,
                "metric_code": metric.code,
                "metric_name": metric.name,
                "sport": metric.sport,
                "category": metric.category,
                "unit": metric.unit,
                "higher_is_better": metric.higher_is_better,
                **forecast_scenario_summary(
                    values,
                    metric.higher_is_better,
                    metric.name,
                    metric.unit,
                    trend,
                    training_adjustment_percent=training_adjustment_percent,
                    readiness_score=readiness_score,
                    horizon=horizon,
                    model_policy="deterministic_what_if_forecast_v1",
                ),
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
    return injury_risk_summary(
        athlete_profile_id,
        feedback_rows,
        len(open_incidents),
        declining_metric_count,
        environmental_context,
        biomarker_context,
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
        trends = await performance_metric_trends(db, organization_id, profile.id)
        trend_series = await performance_metric_trend_series(db, organization_id, profile.id)
        forecast_scenarios = await performance_forecast_scenarios(db, organization_id, profile.id)
        benchmarks = await performance_metric_benchmarks(
            db,
            organization_id,
            athlete_profile_id=profile.id,
            cohort_scope=benchmark_cohort_scope,
        )
        cohort_comparisons = await performance_cohort_comparisons(db, organization_id, profile.id)
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
                "benchmarks": benchmarks,
                "cohort_comparisons": cohort_comparisons,
            }
        )
    return results


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


def normalize_benchmark_scope(cohort_scope: str) -> str:
    normalized = cohort_scope.strip().lower()
    if normalized in {"tenant", "age_group", "position", "region"}:
        return normalized
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="cohort_scope must be one of tenant, age_group, position, or region",
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
                Person.date_of_birth,
                Person.country_code,
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
    for athlete_profile_id, date_of_birth, country_code, primary_position, team_age_group in rows:
        context = contexts.setdefault(
            athlete_profile_id,
            {"age_group": None, "position": None, "region": None},
        )
        if context["age_group"] is None:
            context["age_group"] = team_age_group or age_group_from_birthdate(date_of_birth)
        if context["position"] is None and primary_position:
            context["position"] = primary_position
        if context["region"] is None and country_code:
            context["region"] = country_code.upper()
    return contexts


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
) -> dict[str, object]:
    environmental_context = environmental_context or default_injury_risk_environment_context()
    biomarker_context = biomarker_context or default_injury_risk_biomarker_context()
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

    rounded_score = int(round(max(0, min(100, score))))
    band = injury_risk_band(rounded_score)
    if not drivers:
        drivers.append("Training feedback, workload, incidents, and performance trends are within routine range.")
    return {
        "athlete_profile_id": athlete_profile_id,
        "generated_at": now,
        "model_policy": "deterministic_injury_risk_v3_biomarker_environmental",
        "score": rounded_score,
        "risk_band": band,
        "confidence": injury_risk_confidence(
            len(feedbacks),
            open_incident_count,
            declining_metric_count,
            environmental_risk_count,
            biomarker_risk_count,
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
) -> float:
    evidence_bonus = min(0.45, feedback_count * 0.06)
    incident_bonus = 0.12 if open_incident_count else 0.0
    trend_bonus = min(0.15, declining_metric_count * 0.04)
    environment_bonus = min(0.1, environmental_risk_count * 0.03)
    biomarker_bonus = min(0.12, biomarker_risk_count * 0.04)
    return round(
        min(0.95, 0.35 + evidence_bonus + incident_bonus + trend_bonus + environment_bonus + biomarker_bonus),
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
