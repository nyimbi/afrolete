from datetime import UTC, datetime
import re
from statistics import pstdev
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.organization import Organization
from app.models.performance import (
    AthleteAssessment,
    AthletePerformanceObservation,
    PerformanceMetricDefinition,
)
from app.models.enums import MetricSource, MetricVerificationStatus
from app.models.team import AthleteProfile
from app.schemas.performance import (
    AthleteAssessmentCreate,
    MetricDefinitionCreate,
    PerformanceIngestionCreate,
    PerformanceObservationCreate,
    PerformanceObservationReviewCreate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService


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
) -> list[dict[str, object]]:
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

    benchmarks: list[dict[str, object]] = []
    for metric in metrics:
        cohort_observations = [
            observation
            for (metric_id, _), observation in latest_by_metric_athlete.items()
            if metric_id == metric.id
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


def forecast_next_value(values: list[float]) -> float | None:
    if len(values) < 2:
        return values[-1] if values else None
    deltas = [current - previous for previous, current in zip(values[:-1], values[1:], strict=True)]
    return values[-1] + sum(deltas) / len(deltas)


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
