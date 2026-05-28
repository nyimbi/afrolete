from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.performance import (
    AssessmentReviewQueueSummaryRead,
    AthleteAssessmentCreate,
    AthleteAssessmentRead,
    AthleteAssessmentReviewAssignmentUpdate,
    AthleteAssessmentReviewQueueItemRead,
    AthleteAssessmentReviewCreate,
    AthletePerformanceSummaryRead,
    MetricDefinitionCreate,
    MetricDefinitionRead,
    PerformanceAchievementAwardRead,
    PerformanceAchievementRunRead,
    PerformanceAssessmentReviewEscalationRunRead,
    PerformanceGoalCreate,
    PerformanceGoalRead,
    PerformanceIngestionCreate,
    PerformanceIngestionRead,
    PerformanceMetricBenchmarkRead,
    PerformanceMetricTrendRead,
    PerformanceObservationCreate,
    PerformanceObservationRead,
    PerformanceObservationReviewCreate,
    PlayerSelfAssessmentCreate,
    PlayerPerformanceProfileRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.performance import (
    assessment_review_queue_summary,
    create_assessment,
    create_metric_definition,
    create_observation,
    create_performance_goal,
    create_player_self_assessment,
    evaluate_performance_achievements,
    ingest_performance_evidence,
    list_assessment_review_queue,
    list_assessments,
    list_performance_awards,
    list_performance_goals,
    list_metric_definitions,
    list_my_player_performance,
    list_observations,
    performance_metric_benchmarks,
    performance_metric_trends,
    performance_summary,
    run_assessment_review_escalations,
    review_assessment,
    review_observation,
    update_assessment_review_assignment,
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
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[PlayerPerformanceProfileRead]:
    profiles = await list_my_player_performance(
        db,
        identity,
        organization_id,
        observation_limit=observation_limit,
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
            benchmarks=[
                PerformanceMetricBenchmarkRead(**benchmark) for benchmark in profile["benchmarks"]
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
        extractor=result["extractor"],
        confidence=result["confidence"],
        review_required=result["review_required"],
        summary=result["summary"],
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


@router.get("/benchmarks", response_model=list[PerformanceMetricBenchmarkRead])
async def performance_benchmarks_route(
    organization_id: UUID = Query(),
    athlete_profile_id: UUID | None = Query(default=None),
    sport: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceMetricBenchmarkRead]:
    return [
        PerformanceMetricBenchmarkRead(**benchmark)
        for benchmark in await performance_metric_benchmarks(
            db,
            organization_id,
            athlete_profile_id=athlete_profile_id,
            sport=sport,
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
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceMetricBenchmarkRead]:
    return [
        PerformanceMetricBenchmarkRead(**benchmark)
        for benchmark in await performance_metric_benchmarks(
            db,
            organization_id,
            athlete_profile_id=athlete_profile_id,
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
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceMetricTrendRead]:
    return [
        PerformanceMetricTrendRead(**trend)
        for trend in await performance_metric_trends(
            db,
            organization_id,
            athlete_profile_id,
            sport=sport,
        )
    ]


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
