from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.performance import (
    AthleteAssessmentCreate,
    AthleteAssessmentRead,
    AthletePerformanceSummaryRead,
    MetricDefinitionCreate,
    MetricDefinitionRead,
    PerformanceAchievementAwardRead,
    PerformanceAchievementRunRead,
    PerformanceGoalCreate,
    PerformanceGoalRead,
    PerformanceMetricBenchmarkRead,
    PerformanceMetricTrendRead,
    PerformanceIngestionCreate,
    PerformanceIngestionRead,
    PerformanceObservationCreate,
    PerformanceObservationRead,
    PerformanceObservationReviewCreate,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.performance import (
    create_assessment,
    create_performance_goal,
    create_metric_definition,
    create_observation,
    evaluate_performance_achievements,
    ingest_performance_evidence,
    list_performance_awards,
    list_performance_goals,
    list_assessments,
    list_metric_definitions,
    list_observations,
    performance_metric_benchmarks,
    performance_metric_trends,
    performance_summary,
    review_observation,
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
        summary=assessment.summary,
        recommendations=assessment.recommendations,
        verification_status=assessment.verification_status,
    )


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
