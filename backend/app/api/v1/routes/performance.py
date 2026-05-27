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
    PerformanceObservationCreate,
    PerformanceObservationRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.performance import (
    create_assessment,
    create_metric_definition,
    create_observation,
    list_assessments,
    list_metric_definitions,
    list_observations,
    performance_summary,
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
