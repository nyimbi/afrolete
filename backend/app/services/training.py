import hashlib
import hmac
import json
import re
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.agent import Agent, AgentTask
from app.models.assets import FacilityBooking
from app.models.competition import CompetitionFixture
from app.models.event import Event
from app.models.enums import AgentKind, AgentTaskStatus, FacilityBookingStatus, TrainingPlanStatus, TrainingSessionStatus
from app.models.organization import Organization
from app.models.performance import AthleteAssessment, AthletePerformanceObservation
from app.models.team import AthleteProfile, Team
from app.models.training import (
    TrainingDrill,
    TrainingPlan,
    TrainingPlanItem,
    TrainingSessionFeedback,
    TrainingSessionPlan,
)
from app.schemas.training import (
    TrainingAvailabilityCreate,
    TrainingCommandCenterRead,
    TrainingCommandCheckRead,
    TrainingCommandMetricRead,
    TrainingDrillCreate,
    TrainingPlanGenerateCreate,
    TrainingPlanCreate,
    TrainingPlanItemCreate,
    TrainingSessionFeedbackCreate,
    TrainingSessionPlanCreate,
)
from app.schemas.agent import AgentTaskCreate
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.agents import queue_agent_task
from app.services.secrets import resolve_secret


async def ensure_manage_training(
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


async def create_training_drill(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: TrainingDrillCreate,
    authz: AuthorizationService,
) -> TrainingDrill:
    await get_organization(db, payload.organization_id)
    await ensure_manage_training(authz, identity, payload.organization_id)

    drill = TrainingDrill(**payload.model_dump())
    db.add(drill)
    await db.commit()
    await db.refresh(drill)
    return drill


async def list_training_drills(
    db: AsyncSession,
    organization_id: UUID,
    sport: str | None = None,
) -> list[TrainingDrill]:
    statement = select(TrainingDrill).where(TrainingDrill.organization_id == organization_id)
    if sport is not None:
        statement = statement.where(TrainingDrill.sport == sport)
    return list(
        (
            await db.scalars(
                statement.order_by(TrainingDrill.focus_area, TrainingDrill.category, TrainingDrill.name)
            )
        ).all()
    )


async def create_training_plan(
    db: AsyncSession,
    identity: CurrentIdentity | None,
    payload: TrainingPlanCreate,
    authz: AuthorizationService | None,
    *,
    enforce_manage_training_scope: bool = True,
) -> TrainingPlan:
    await get_organization(db, payload.organization_id)
    if enforce_manage_training_scope:
        if identity is None or authz is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Identity and authorization required",
            )
        await ensure_manage_training(authz, identity, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    if payload.athlete_profile_id is not None:
        await get_athlete_for_organization(db, payload.athlete_profile_id, payload.organization_id)

    plan = TrainingPlan(
        created_by_person_id=identity.person_id if identity is not None else None,
        **payload.model_dump(),
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def list_training_plans(
    db: AsyncSession,
    organization_id: UUID,
    team_id: UUID | None = None,
    athlete_profile_id: UUID | None = None,
) -> list[TrainingPlan]:
    statement = select(TrainingPlan).where(TrainingPlan.organization_id == organization_id)
    if team_id is not None:
        statement = statement.where(TrainingPlan.team_id == team_id)
    if athlete_profile_id is not None:
        statement = statement.where(TrainingPlan.athlete_profile_id == athlete_profile_id)
    return list(
        (
            await db.scalars(
                statement.order_by(TrainingPlan.period_start.desc(), TrainingPlan.title)
            )
        ).all()
    )


async def add_training_plan_item(
    db: AsyncSession,
    identity: CurrentIdentity | None,
    plan_id: UUID,
    payload: TrainingPlanItemCreate,
    authz: AuthorizationService | None,
    *,
    enforce_manage_training_scope: bool = True,
) -> TrainingPlanItem:
    plan = await get_training_plan(db, plan_id)
    if enforce_manage_training_scope:
        if identity is None or authz is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Identity and authorization required",
            )
        await ensure_manage_training(authz, identity, plan.organization_id)
    if payload.drill_id is not None:
        drill = await db.get(TrainingDrill, payload.drill_id)
        if drill is None or drill.organization_id != plan.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drill not found")

    item = TrainingPlanItem(plan_id=plan.id, **payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def generate_training_plan(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: TrainingPlanGenerateCreate,
    authz: AuthorizationService,
    *,
    settings: Settings | None = None,
) -> dict[str, object]:
    selected_settings = settings or get_settings()
    await get_organization(db, payload.organization_id)
    await ensure_manage_training(authz, identity, payload.organization_id)
    team = await get_team_for_organization(db, payload.team_id, payload.organization_id) if payload.team_id else None
    if payload.athlete_profile_id is not None:
        await get_athlete_for_organization(db, payload.athlete_profile_id, payload.organization_id)

    assessments = await recent_assessments(db, payload.organization_id, payload.athlete_profile_id)
    observations = await recent_observations(db, payload.organization_id, payload.athlete_profile_id)
    next_competition_at = await next_competition_datetime(db, payload.organization_id, payload.team_id)
    focus_area = payload.focus_area or infer_focus_area(assessments, payload.readiness_score)
    readiness_band = readiness_label(payload.readiness_score)
    source_summary = (
        f"Generated from {len(assessments)} assessments, {len(observations)} observations, "
        f"{'one upcoming competition' if next_competition_at else 'no upcoming competition'}, "
        f"and readiness band {readiness_band}."
    )
    load_guidance = generated_load_guidance(payload.readiness_score, payload.weekly_sessions, next_competition_at)
    provider_result = await request_training_plan_provider(
        selected_settings,
        payload,
        team,
        assessments,
        observations,
        next_competition_at,
        source_summary,
        load_guidance,
    )
    provider_payload = provider_result.get("payload") if provider_result else None
    if not isinstance(provider_payload, dict):
        provider_payload = {}
    focus_area = bounded_provider_text(provider_payload, "focus_area", focus_area, 160)
    source_summary = bounded_provider_text(
        provider_payload,
        "source_summary",
        bounded_provider_text(provider_payload, "rationale", source_summary, 4000),
        4000,
    )
    load_guidance = bounded_provider_text(provider_payload, "load_guidance", load_guidance, 4000)
    plan = TrainingPlan(
        organization_id=payload.organization_id,
        team_id=payload.team_id,
        athlete_profile_id=payload.athlete_profile_id,
        created_by_person_id=identity.person_id,
        title=bounded_provider_text(provider_payload, "title", payload.title or f"AI {focus_area} block", 240),
        focus_area=focus_area,
        period_start=payload.period_start,
        period_end=payload.period_end,
        ai_generated=True,
        source_summary=source_summary,
        load_guidance=load_guidance,
        recovery_protocol=bounded_provider_text(
            provider_payload,
            "recovery_protocol",
            generated_recovery_protocol(payload.readiness_score),
            4000,
        ),
        progress_checkpoints=bounded_provider_text(
            provider_payload,
            "progress_checkpoints",
            "Review readiness after session 2; reassess after the final session; adjust load if soreness or school/work constraints increase.",
            4000,
        ),
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    drills = await list_training_drills(db, payload.organization_id, sport=team.sport if team else None)
    selected_drills = select_training_drills(drills, focus_area, payload.weekly_sessions)
    provider_items = provider_training_items(provider_payload, payload.weekly_sessions)
    items: list[TrainingPlanItem] = []
    for sequence in range(1, payload.weekly_sessions + 1):
        drill = selected_drills[sequence - 1] if sequence - 1 < len(selected_drills) else None
        intensity = generated_intensity(payload.readiness_score, sequence, payload.upcoming_competition_weight)
        provider_item = provider_items[sequence - 1] if sequence - 1 < len(provider_items) else {}
        item = TrainingPlanItem(
            plan_id=plan.id,
            drill_id=drill.id if drill else None,
            sequence=sequence,
            day_label=bounded_provider_text(provider_item, "day_label", f"Session {sequence}", 80),
            title=bounded_provider_text(
                provider_item,
                "title",
                drill.name if drill else f"{focus_area} progression {sequence}",
                180,
            ),
            focus_area=bounded_provider_text(provider_item, "focus_area", drill.focus_area if drill else focus_area, 120),
            duration_minutes=bounded_provider_int(
                provider_item,
                "duration_minutes",
                drill.default_duration_minutes if drill else 45,
                1,
                240,
            ),
            intensity=bounded_provider_int(provider_item, "intensity", intensity, 1, 10),
            notes=bounded_provider_text(
                provider_item,
                "notes",
                (
                    f"AI-generated for {readiness_band} readiness. "
                    f"Keep RPE near {intensity}; adjust if competition proximity or recovery changes."
                ),
                4000,
            ),
        )
        db.add(item)
        items.append(item)
    await db.commit()
    for item in items:
        await db.refresh(item)
    return {
        "plan": plan,
        "items": items,
        "readiness_score": payload.readiness_score,
        "rationale": source_summary,
        "load_balance": load_guidance,
        "next_competition_at": next_competition_at,
        "generation_provider": provider_result["provider"] if provider_result else "deterministic",
        "model_policy": provider_result["model_policy"] if provider_result else selected_settings.training_plan_generation_model,
        "provider_status_code": provider_result["status_code"] if provider_result else None,
        "provider_reference": provider_result["provider_reference"] if provider_result else None,
        "provider_notes": provider_result["notes"] if provider_result else None,
    }


async def request_training_plan_provider(
    settings: Settings,
    payload: TrainingPlanGenerateCreate,
    team: Team | None,
    assessments: list[AthleteAssessment],
    observations: list[AthletePerformanceObservation],
    next_competition_at: datetime | None,
    deterministic_source_summary: str,
    deterministic_load_guidance: str,
) -> dict[str, object] | None:
    if settings.training_plan_generation_mode != "webhook":
        return None
    if not settings.training_plan_generation_webhook_url:
        return {
            "provider": "deterministic_fallback",
            "model_policy": settings.training_plan_generation_model,
            "status_code": None,
            "provider_reference": None,
            "notes": "Training plan generation webhook mode is enabled but no webhook URL is configured.",
            "payload": {},
        }
    key_resolution = await resolve_training_plan_generation_key(settings)
    if key_resolution["failure_reason"]:
        return {
            "provider": "deterministic_fallback",
            "model_policy": settings.training_plan_generation_model,
            "status_code": None,
            "provider_reference": None,
            "notes": key_resolution["failure_reason"],
            "payload": {},
        }
    request_payload = training_plan_provider_payload(
        settings,
        payload,
        team,
        assessments,
        observations,
        next_competition_at,
        deterministic_source_summary,
        deterministic_load_guidance,
    )
    body = training_plan_generation_body(request_payload)
    try:
        async with httpx.AsyncClient(timeout=settings.training_plan_generation_timeout_seconds) as client:
            response = await client.post(
                settings.training_plan_generation_webhook_url,
                content=body,
                headers=training_plan_generation_headers(settings, body, str(key_resolution["key"] or "")),
            )
    except httpx.HTTPError as exc:
        return {
            "provider": "deterministic_fallback",
            "model_policy": settings.training_plan_generation_model,
            "status_code": None,
            "provider_reference": None,
            "notes": str(exc)[:600],
            "payload": {},
        }
    if not 200 <= response.status_code < 300:
        return {
            "provider": "deterministic_fallback",
            "model_policy": settings.training_plan_generation_model,
            "status_code": response.status_code,
            "provider_reference": None,
            "notes": f"Training plan provider returned {response.status_code}: {response.text[:400]}",
            "payload": {},
        }
    try:
        response_payload = response.json()
    except ValueError:
        response_payload = {}
    if not isinstance(response_payload, dict):
        response_payload = {}
    return {
        "provider": "webhook",
        "model_policy": str(response_payload.get("model_policy") or settings.training_plan_generation_model),
        "status_code": response.status_code,
        "provider_reference": bounded_optional_provider_text(response_payload, "provider_reference", 240),
        "notes": bounded_optional_provider_text(response_payload, "notes", 600)
        or bounded_optional_provider_text(response_payload, "summary", 600),
        "payload": response_payload,
    }


async def resolve_training_plan_generation_key(settings: Settings) -> dict[str, str | None]:
    source = "openbao" if settings.training_plan_generation_webhook_key_secret_path else "env"
    try:
        secret = await resolve_secret(
            settings,
            env_value=settings.training_plan_generation_webhook_key,
            path=settings.training_plan_generation_webhook_key_secret_path,
            field_name=settings.training_plan_generation_webhook_key_secret_field,
            label="training plan generation webhook key",
        )
    except HTTPException as exc:
        return {"key": None, "source": "openbao", "failure_reason": str(exc.detail)}
    return {"key": secret, "source": source if secret else "unset", "failure_reason": None}


def training_plan_provider_payload(
    settings: Settings,
    payload: TrainingPlanGenerateCreate,
    team: Team | None,
    assessments: list[AthleteAssessment],
    observations: list[AthletePerformanceObservation],
    next_competition_at: datetime | None,
    deterministic_source_summary: str,
    deterministic_load_guidance: str,
) -> dict[str, object]:
    return {
        "event": "afrolete.training.plan.generate",
        "model": settings.training_plan_generation_model,
        "idempotency_key": (
            f"{payload.organization_id}:{payload.team_id or 'org'}:"
            f"{payload.athlete_profile_id or 'team'}:{payload.period_start}:{payload.period_end}"
        ),
        "organization_id": str(payload.organization_id),
        "team": {"id": str(team.id), "name": team.name, "sport": team.sport} if team else None,
        "athlete_profile_id": str(payload.athlete_profile_id) if payload.athlete_profile_id else None,
        "request": payload.model_dump(mode="json"),
        "context": {
            "assessment_count": len(assessments),
            "observation_count": len(observations),
            "next_competition_at": next_competition_at.isoformat() if next_competition_at else None,
            "deterministic_source_summary": deterministic_source_summary,
            "deterministic_load_guidance": deterministic_load_guidance,
            "recent_assessments": [
                {
                    "overall_score": assessment.overall_score,
                    "rating": assessment.rating,
                    "summary": assessment.summary,
                    "assessed_at": assessment.assessed_at.isoformat() if assessment.assessed_at else None,
                }
                for assessment in assessments[:5]
            ],
            "recent_observations": [
                {
                    "metric_code": observation.metric_code,
                    "raw_value": observation.raw_value,
                    "source": observation.source,
                    "confidence": observation.confidence,
                    "observed_at": observation.observed_at.isoformat() if observation.observed_at else None,
                    "notes": observation.notes,
                }
                for observation in observations[:10]
            ],
        },
        "output_contract": {
            "title": "string",
            "focus_area": "string",
            "source_summary": "string",
            "load_guidance": "string",
            "recovery_protocol": "string",
            "progress_checkpoints": "string",
            "items": [
                {
                    "day_label": "string",
                    "title": "string",
                    "focus_area": "string",
                    "duration_minutes": "integer 1..240",
                    "intensity": "integer 1..10",
                    "notes": "string",
                }
            ],
        },
    }


def training_plan_generation_headers(settings: Settings, body: bytes, signing_key: str = "") -> dict[str, str]:
    headers = {
        "User-Agent": "AfroLete-Training-Planner/1.0",
        "Content-Type": "application/json",
    }
    if signing_key:
        timestamp = str(int(time.time()))
        headers["X-Afrolete-Training-Key-Source"] = (
            "openbao" if settings.training_plan_generation_webhook_key_secret_path else "env"
        )
        headers["X-Afrolete-Training-Timestamp"] = timestamp
        headers["X-Afrolete-Training-Signature"] = training_plan_generation_signature(
            signing_key,
            timestamp,
            body,
        )
    return headers


def training_plan_generation_body(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()


def training_plan_generation_signature(signing_key: str, timestamp: str, body: bytes) -> str:
    digest = hmac.new(signing_key.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def provider_training_items(provider_payload: dict[str, object], expected_count: int) -> list[dict[str, object]]:
    raw_items = provider_payload.get("items")
    if not isinstance(raw_items, list):
        return []
    items = [item for item in raw_items if isinstance(item, dict)]
    return items[:expected_count]


def bounded_provider_text(
    provider_payload: dict[str, object],
    key: str,
    fallback: str,
    max_length: int,
) -> str:
    value = provider_payload.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()[:max_length]
    return fallback[:max_length]


def bounded_optional_provider_text(
    provider_payload: dict[str, object],
    key: str,
    max_length: int,
) -> str | None:
    value = provider_payload.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()[:max_length]
    return None


def bounded_provider_int(
    provider_payload: dict[str, object],
    key: str,
    fallback: int,
    lower: int,
    upper: int,
) -> int:
    value = provider_payload.get(key)
    if isinstance(value, int | float):
        return min(max(int(value), lower), upper)
    if isinstance(value, str) and value.strip().isdigit():
        return min(max(int(value), lower), upper)
    return min(max(fallback, lower), upper)


async def list_training_plan_items(
    db: AsyncSession,
    plan_id: UUID,
) -> list[TrainingPlanItem]:
    await get_training_plan(db, plan_id)
    return list(
        (
            await db.scalars(
                select(TrainingPlanItem)
                .where(TrainingPlanItem.plan_id == plan_id)
                .order_by(TrainingPlanItem.sequence, TrainingPlanItem.created_at)
            )
        ).all()
    )


async def recent_assessments(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID | None,
) -> list[AthleteAssessment]:
    statement = select(AthleteAssessment).where(AthleteAssessment.organization_id == organization_id)
    if athlete_profile_id is not None:
        statement = statement.where(AthleteAssessment.athlete_profile_id == athlete_profile_id)
    return list((await db.scalars(statement.order_by(AthleteAssessment.assessed_at.desc()).limit(10))).all())


async def recent_observations(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID | None,
) -> list[AthletePerformanceObservation]:
    statement = select(AthletePerformanceObservation).where(
        AthletePerformanceObservation.organization_id == organization_id
    )
    if athlete_profile_id is not None:
        statement = statement.where(AthletePerformanceObservation.athlete_profile_id == athlete_profile_id)
    return list(
        (
            await db.scalars(
                statement.order_by(AthletePerformanceObservation.observed_at.desc()).limit(20)
            )
        ).all()
    )


async def next_competition_datetime(
    db: AsyncSession,
    organization_id: UUID,
    team_id: UUID | None,
) -> datetime | None:
    statement = (
        select(CompetitionFixture.scheduled_at)
        .where(CompetitionFixture.organization_id == organization_id)
        .where(CompetitionFixture.scheduled_at >= datetime.now(UTC))
    )
    if team_id is not None:
        statement = statement.where(
            (CompetitionFixture.home_team_id == team_id) | (CompetitionFixture.away_team_id == team_id)
        )
    result = await db.scalar(statement.order_by(CompetitionFixture.scheduled_at).limit(1))
    return result


async def create_training_session_plan(
    db: AsyncSession,
    identity: CurrentIdentity | None,
    payload: TrainingSessionPlanCreate,
    authz: AuthorizationService | None,
    *,
    enforce_manage_training_scope: bool = True,
) -> TrainingSessionPlan:
    await get_organization(db, payload.organization_id)
    if enforce_manage_training_scope:
        if identity is None or authz is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Identity and authorization required",
            )
        await ensure_manage_training(authz, identity, payload.organization_id)
    await get_team_for_organization(db, payload.team_id, payload.organization_id)
    if payload.plan_id is not None:
        plan = await get_training_plan_for_organization(db, payload.plan_id, payload.organization_id)
        if plan.team_id is not None and plan.team_id != payload.team_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    if payload.event_id is not None:
        event = await db.get(Event, payload.event_id)
        if event is None or event.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        if event.team_id is not None and event.team_id != payload.team_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    session_plan = TrainingSessionPlan(
        load_score=float(payload.duration_minutes * payload.rpe_target),
        **payload.model_dump(),
    )
    db.add(session_plan)
    await db.commit()
    await db.refresh(session_plan)
    return session_plan


async def list_training_session_plans(
    db: AsyncSession,
    organization_id: UUID,
    team_id: UUID | None = None,
) -> list[TrainingSessionPlan]:
    statement = select(TrainingSessionPlan).where(
        TrainingSessionPlan.organization_id == organization_id
    )
    if team_id is not None:
        statement = statement.where(TrainingSessionPlan.team_id == team_id)
    return list(
        (
            await db.scalars(
                statement.order_by(TrainingSessionPlan.scheduled_for.desc())
            )
        ).all()
    )


async def export_training_calendar_artifact(
    db: AsyncSession,
    identity: CurrentIdentity | None,
    organization_id: UUID,
    authz: AuthorizationService | None,
    team_id: UUID | None = None,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
    *,
    enforce_manage_training_scope: bool = True,
) -> dict[str, object]:
    organization = await get_organization(db, organization_id)
    if enforce_manage_training_scope:
        if identity is None or authz is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Identity and authorization required",
            )
        await ensure_manage_training(authz, identity, organization_id)
    team = await get_team_for_organization(db, team_id, organization_id) if team_id else None
    generated_at = datetime.now(UTC)
    range_start = ensure_utc(starts_at) if starts_at else generated_at - timedelta(days=1)
    range_end = ensure_utc(ends_at) if ends_at else generated_at + timedelta(days=90)
    if range_end <= range_start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="ends_at must be after starts_at")
    statement = (
        select(TrainingSessionPlan)
        .where(TrainingSessionPlan.organization_id == organization_id)
        .where(TrainingSessionPlan.scheduled_for >= range_start)
        .where(TrainingSessionPlan.scheduled_for < range_end)
        .order_by(TrainingSessionPlan.scheduled_for, TrainingSessionPlan.title)
    )
    if team_id is not None:
        statement = statement.where(TrainingSessionPlan.team_id == team_id)
    sessions = list((await db.scalars(statement)).all())
    content = render_training_calendar_ics(organization, team, sessions, generated_at)
    content_bytes = content.encode()
    filename_scope = slug_for_training_calendar(team.name if team else organization.name)
    return {
        "organization_id": organization_id,
        "team_id": team_id,
        "generated_at": generated_at,
        "starts_at": range_start,
        "ends_at": range_end,
        "session_count": len(sessions),
        "content_type": "text/calendar; charset=utf-8",
        "download_filename": f"afrolete-training-{filename_scope}-{range_start.date()}-{range_end.date()}.ics",
        "content": content,
        "checksum": hashlib.sha256(content_bytes).hexdigest(),
        "size_bytes": len(content_bytes),
    }


async def training_command_center(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    *,
    team_id: UUID | None = None,
    ensure_agent_task: bool = False,
) -> tuple[TrainingCommandCenterRead, AgentTask | None]:
    await get_organization(db, organization_id)
    await ensure_manage_training(authz, identity, organization_id)
    team = await get_team_for_organization(db, team_id, organization_id) if team_id is not None else None
    drills = await list_training_drills(db, organization_id, sport=team.sport if team else None)
    plans = await list_training_plans(db, organization_id, team_id=team_id)
    sessions = await list_training_session_plans(db, organization_id, team_id=team_id)
    feedback_rows = await list_training_feedback_for_scope(db, organization_id, team_id=team_id)
    now = datetime.now(UTC)
    active_plan = next((plan for plan in plans if plan.status in {TrainingPlanStatus.ACTIVE, TrainingPlanStatus.DRAFT}), None)
    upcoming_sessions = [session for session in sessions if ensure_utc(session.scheduled_for) >= now]
    upcoming_sessions.sort(key=lambda session: ensure_utc(session.scheduled_for))
    next_session = upcoming_sessions[0] if upcoming_sessions else None
    completed_sessions = [session for session in sessions if session.status == TrainingSessionStatus.COMPLETED]
    planned_sessions = [session for session in sessions if session.status == TrainingSessionStatus.PLANNED]
    avg_readiness = average([float(row["readiness_score"]) for row in feedback_rows])
    avg_load_delta = average(
        [float(row["load_delta"]) for row in feedback_rows if row.get("load_delta") is not None]
    )
    high_risk_feedback_count = sum(
        1
        for row in feedback_rows
        if int(row["readiness_score"]) < 45 or int(row["soreness_score"]) >= 8
    )
    checks = training_command_checks(
        drill_count=len(drills),
        plan_count=len(plans),
        session_count=len(sessions),
        upcoming_count=len(upcoming_sessions),
        feedback_count=len(feedback_rows),
        high_risk_feedback_count=high_risk_feedback_count,
        avg_readiness=avg_readiness,
        avg_load_delta=avg_load_delta,
    )
    readiness_score = round(
        (sum(1 for check in checks if check.status == "ready") / max(len(checks), 1)) * 100
    )
    command_status = "ready" if readiness_score >= 80 else "attention" if readiness_score >= 50 else "blocked"
    agent_task = await find_training_command_agent_task(db, organization_id, team_id)
    if ensure_agent_task and agent_task is None:
        agent_task = await queue_training_command_agent_task(
            db,
            identity,
            organization_id,
            team_id,
            authz,
            readiness_score=readiness_score,
            plan_count=len(plans),
            session_count=len(sessions),
            feedback_count=len(feedback_rows),
            high_risk_feedback_count=high_risk_feedback_count,
        )
    return (
        TrainingCommandCenterRead(
            organization_id=organization_id,
            team_id=team_id,
            team_name=team.name if team else None,
            command_status=command_status,
            readiness_score=readiness_score,
            active_plan_id=active_plan.id if active_plan else None,
            active_plan_title=active_plan.title if active_plan else None,
            next_session_id=next_session.id if next_session else None,
            next_session_title=next_session.title if next_session else None,
            next_session_at=next_session.scheduled_for if next_session else None,
            average_readiness_score=avg_readiness,
            average_load_delta=avg_load_delta,
            high_risk_feedback_count=high_risk_feedback_count,
            metrics=training_command_metrics(
                drill_count=len(drills),
                plan_count=len(plans),
                session_count=len(sessions),
                upcoming_count=len(upcoming_sessions),
                completed_count=len(completed_sessions),
                planned_count=len(planned_sessions),
                feedback_count=len(feedback_rows),
                high_risk_feedback_count=high_risk_feedback_count,
                avg_readiness=avg_readiness,
                avg_load_delta=avg_load_delta,
            ),
            checks=checks,
            coach_actions=training_command_actions(
                checks,
                active_plan=active_plan,
                next_session=next_session,
                avg_readiness=avg_readiness,
                avg_load_delta=avg_load_delta,
                high_risk_feedback_count=high_risk_feedback_count,
                agent_task=agent_task,
            ),
        ),
        agent_task,
    )


async def list_training_feedback_for_scope(
    db: AsyncSession,
    organization_id: UUID,
    *,
    team_id: UUID | None = None,
) -> list[dict[str, object]]:
    statement = (
        select(TrainingSessionFeedback, TrainingSessionPlan)
        .join(TrainingSessionPlan, TrainingSessionPlan.id == TrainingSessionFeedback.session_plan_id)
        .where(TrainingSessionFeedback.organization_id == organization_id)
        .order_by(TrainingSessionFeedback.recorded_at.desc())
        .limit(100)
    )
    if team_id is not None:
        statement = statement.where(TrainingSessionPlan.team_id == team_id)
    rows = (await db.execute(statement)).all()
    return [training_feedback_read(feedback, session_plan) for feedback, session_plan in rows]


def training_command_metrics(
    *,
    drill_count: int,
    plan_count: int,
    session_count: int,
    upcoming_count: int,
    completed_count: int,
    planned_count: int,
    feedback_count: int,
    high_risk_feedback_count: int,
    avg_readiness: float | None,
    avg_load_delta: float | None,
) -> list[TrainingCommandMetricRead]:
    return [
        TrainingCommandMetricRead(
            key="drills",
            label="Drills",
            value=drill_count,
            detail="Reusable coaching blocks available for plan generation.",
            status="ready" if drill_count else "action",
        ),
        TrainingCommandMetricRead(
            key="plans",
            label="Plans",
            value=plan_count,
            detail="Scoped training blocks for teams or athletes.",
            status="ready" if plan_count else "action",
        ),
        TrainingCommandMetricRead(
            key="sessions",
            label="Sessions",
            value=session_count,
            detail=f"{upcoming_count} upcoming, {completed_count} completed, {planned_count} planned.",
            status="ready" if upcoming_count else "action",
        ),
        TrainingCommandMetricRead(
            key="feedback",
            label="Feedback",
            value=feedback_count,
            detail="Readiness/RPE records powering load decisions.",
            status="ready" if feedback_count else "action",
        ),
        TrainingCommandMetricRead(
            key="readiness",
            label="Avg readiness",
            value=round(avg_readiness or 0, 1),
            detail="Recent athlete/team readiness average.",
            status="ready" if avg_readiness is not None and avg_readiness >= 65 else "action",
        ),
        TrainingCommandMetricRead(
            key="load_delta",
            label="Avg load delta",
            value=round(avg_load_delta or 0, 1),
            detail="Actual minus planned training load from feedback.",
            status="ready" if avg_load_delta is None or abs(avg_load_delta) <= 150 else "action",
        ),
        TrainingCommandMetricRead(
            key="risk",
            label="High risk",
            value=high_risk_feedback_count,
            detail="Low-readiness or high-soreness feedback requiring intervention.",
            status="action" if high_risk_feedback_count else "ready",
        ),
    ]


def training_command_checks(
    *,
    drill_count: int,
    plan_count: int,
    session_count: int,
    upcoming_count: int,
    feedback_count: int,
    high_risk_feedback_count: int,
    avg_readiness: float | None,
    avg_load_delta: float | None,
) -> list[TrainingCommandCheckRead]:
    return [
        TrainingCommandCheckRead(
            key="drill_library",
            label="Drill library",
            status="ready" if drill_count else "action",
            detail=f"{drill_count} drill{'' if drill_count == 1 else 's'} available.",
            action_label="Create drills",
        ),
        TrainingCommandCheckRead(
            key="active_plan",
            label="Training plan",
            status="ready" if plan_count else "action",
            detail=f"{plan_count} plan{'' if plan_count == 1 else 's'} in scope.",
            action_label="Generate AI plan",
        ),
        TrainingCommandCheckRead(
            key="scheduled_sessions",
            label="Scheduled sessions",
            status="ready" if upcoming_count else "action" if session_count else "blocked",
            detail=(
                f"{upcoming_count} upcoming session{'' if upcoming_count == 1 else 's'}."
                if upcoming_count
                else "Schedule the next coached session."
            ),
            action_label="Plan session",
        ),
        TrainingCommandCheckRead(
            key="feedback_loop",
            label="Feedback loop",
            status="ready" if feedback_count else "action",
            detail=(
                f"{feedback_count} readiness/RPE feedback record{'' if feedback_count == 1 else 's'} captured."
                if feedback_count
                else "Capture readiness and post-session RPE after the next session."
            ),
            action_label="Record feedback",
        ),
        TrainingCommandCheckRead(
            key="load_safety",
            label="Load safety",
            status="ready" if high_risk_feedback_count == 0 and (avg_readiness is None or avg_readiness >= 65) else "action",
            detail=(
                "No recent high-risk feedback."
                if high_risk_feedback_count == 0 and (avg_readiness is None or avg_readiness >= 65)
                else f"{high_risk_feedback_count} high-risk feedback record(s); avg readiness {round(avg_readiness or 0, 1)}."
            ),
            action_label="Adjust load",
        ),
        TrainingCommandCheckRead(
            key="load_accuracy",
            label="Load accuracy",
            status="ready" if avg_load_delta is None or abs(avg_load_delta) <= 150 else "action",
            detail=(
                "Actual load is close to plan."
                if avg_load_delta is None or abs(avg_load_delta) <= 150
                else f"Average load delta is {avg_load_delta:+.1f}; recalibrate targets."
            ),
            action_label="Review RPE targets",
        ),
    ]


def training_command_actions(
    checks: list[TrainingCommandCheckRead],
    *,
    active_plan: TrainingPlan | None,
    next_session: TrainingSessionPlan | None,
    avg_readiness: float | None,
    avg_load_delta: float | None,
    high_risk_feedback_count: int,
    agent_task: AgentTask | None,
) -> list[str]:
    actions = [f"{check.label}: {check.detail}" for check in checks if check.status in {"blocked", "action"}]
    if active_plan is not None:
        actions.append(f"Keep {active_plan.title} aligned with the latest feedback and competition context.")
    if next_session is not None:
        actions.append(f"Prepare coaching points, attendance, and readiness check for {next_session.title}.")
    if avg_readiness is not None and avg_readiness < 65:
        actions.append("Reduce high-intensity volume until readiness stabilizes above the moderate band.")
    if avg_load_delta is not None and abs(avg_load_delta) > 150:
        actions.append("Recalibrate session RPE or duration targets because actual load is drifting from plan.")
    if high_risk_feedback_count:
        actions.append("Escalate low-readiness or high-soreness athletes for recovery, medical, or guardian follow-up.")
    if agent_task is None:
        actions.append("Queue the Training Strategy Agent to turn the current plan, sessions, and feedback into a coach review draft.")
    else:
        actions.append(f"Review Training Strategy Agent task {agent_task.id} before changing the training block.")
    return actions[:10]


async def find_training_command_agent_task(
    db: AsyncSession,
    organization_id: UUID,
    team_id: UUID | None,
) -> AgentTask | None:
    return await db.scalar(
        select(AgentTask)
        .where(
            AgentTask.organization_id == organization_id,
            AgentTask.task_type == "training_command_review",
            AgentTask.input_ref.like(f"training-command:{organization_id};team:{team_id or 'all'};%"),
            AgentTask.status.not_in([AgentTaskStatus.FAILED, AgentTaskStatus.CANCELLED]),
        )
        .order_by(AgentTask.created_at.desc())
        .limit(1)
    )


async def queue_training_command_agent_task(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    team_id: UUID | None,
    authz: AuthorizationService,
    *,
    readiness_score: int,
    plan_count: int,
    session_count: int,
    feedback_count: int,
    high_risk_feedback_count: int,
) -> AgentTask:
    existing = await find_training_command_agent_task(db, organization_id, team_id)
    if existing is not None:
        return existing

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
                "Review training plans, session load, athlete readiness, and feedback loops "
                "so coaches can adjust the next block safely."
            ),
            status="active",
            model_policy="human_review_required",
        )
        db.add(agent)
        await db.flush()

    input_ref = (
        f"training-command:{organization_id};"
        f"team:{team_id or 'all'};"
        f"score:{readiness_score};"
        f"plans:{plan_count};"
        f"sessions:{session_count};"
        f"feedback:{feedback_count};"
        f"risk:{high_risk_feedback_count}"
    )
    return await queue_agent_task(
        db,
        identity,
        agent.id,
        AgentTaskCreate(
            organization_id=organization_id,
            task_type="training_command_review",
            title="Review training command center",
            input_ref=input_ref,
        ),
        authz,
    )


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 1)


async def record_training_session_feedback(
    db: AsyncSession,
    identity: CurrentIdentity | None,
    session_plan_id: UUID,
    payload: TrainingSessionFeedbackCreate,
    authz: AuthorizationService | None,
    *,
    enforce_manage_training_scope: bool = True,
) -> dict[str, object]:
    session_plan = await get_training_session_plan(db, session_plan_id)
    if enforce_manage_training_scope:
        if identity is None or authz is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Identity and authorization required",
            )
        await ensure_manage_training(authz, identity, session_plan.organization_id)
    if payload.athlete_profile_id is not None:
        await get_athlete_for_organization(db, payload.athlete_profile_id, session_plan.organization_id)

    feedback = TrainingSessionFeedback(
        organization_id=session_plan.organization_id,
        session_plan_id=session_plan.id,
        recorded_by_person_id=identity.person_id if identity is not None else None,
        recorded_at=datetime.now(UTC),
        **payload.model_dump(),
    )
    if payload.completed:
        session_plan.status = TrainingSessionStatus.COMPLETED
    elif payload.readiness_score < 45:
        session_plan.status = TrainingSessionStatus.PLANNED
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    await db.refresh(session_plan)
    return training_feedback_read(feedback, session_plan)


async def list_training_session_feedback(
    db: AsyncSession,
    session_plan_id: UUID,
) -> list[dict[str, object]]:
    session_plan = await get_training_session_plan(db, session_plan_id)
    rows = (
        await db.scalars(
            select(TrainingSessionFeedback)
            .where(TrainingSessionFeedback.session_plan_id == session_plan_id)
            .order_by(TrainingSessionFeedback.recorded_at.desc())
        )
    ).all()
    return [training_feedback_read(feedback, session_plan) for feedback in rows]


async def suggest_training_availability(
    db: AsyncSession,
    payload: TrainingAvailabilityCreate,
) -> dict[str, object]:
    await get_organization(db, payload.organization_id)
    await get_team_for_organization(db, payload.team_id, payload.organization_id)
    search_start = ensure_utc(payload.starts_at)
    search_end = search_start + timedelta(days=payload.days)
    busy_windows = await team_busy_windows(db, payload.organization_id, payload.team_id, search_start, search_end)
    slots = []
    for day_offset in range(payload.days):
        day = search_start + timedelta(days=day_offset)
        for hour in range(payload.earliest_hour, payload.latest_hour, 2):
            candidate_start = day.replace(hour=hour, minute=0, second=0, microsecond=0)
            if candidate_start < search_start:
                continue
            candidate_end = candidate_start + timedelta(minutes=payload.duration_minutes)
            conflicts = [
                label
                for starts_at, ends_at, label in busy_windows
                if starts_at < candidate_end and ends_at > candidate_start
            ]
            score = max(0, 100 - (len(conflicts) * 35))
            slots.append(
                {
                    "starts_at": candidate_start,
                    "ends_at": candidate_end,
                    "conflict_count": len(conflicts),
                    "conflicts": conflicts[:5],
                    "score": score,
                    "recommendation": availability_recommendation(score, conflicts),
                }
            )
    slots.sort(key=lambda slot: (-int(slot["score"]), slot["starts_at"]))
    return {
        "organization_id": payload.organization_id,
        "team_id": payload.team_id,
        "duration_minutes": payload.duration_minutes,
        "slots": slots[:8],
    }


async def team_busy_windows(
    db: AsyncSession,
    organization_id: UUID,
    team_id: UUID,
    starts_at: datetime,
    ends_at: datetime,
) -> list[tuple[datetime, datetime, str]]:
    starts_at = ensure_utc(starts_at)
    ends_at = ensure_utc(ends_at)
    windows: list[tuple[datetime, datetime, str]] = []
    events = (
        await db.scalars(
            select(Event).where(
                Event.organization_id == organization_id,
                Event.team_id == team_id,
                Event.starts_at < ends_at,
            )
        )
    ).all()
    for event in events:
        event_start = ensure_utc(event.starts_at)
        event_end = ensure_utc(event.ends_at) if event.ends_at else event_start + timedelta(hours=2)
        if event_end > starts_at:
            windows.append((event_start, event_end, f"event:{event.title}"))

    sessions = (
        await db.scalars(
            select(TrainingSessionPlan).where(
                TrainingSessionPlan.organization_id == organization_id,
                TrainingSessionPlan.team_id == team_id,
                TrainingSessionPlan.scheduled_for < ends_at,
            )
        )
    ).all()
    for session_plan in sessions:
        session_start = ensure_utc(session_plan.scheduled_for)
        session_end = session_start + timedelta(minutes=session_plan.duration_minutes)
        if session_end > starts_at:
            windows.append((session_start, session_end, f"training:{session_plan.title}"))

    fixtures = (
        await db.scalars(
            select(CompetitionFixture).where(
                CompetitionFixture.organization_id == organization_id,
                CompetitionFixture.scheduled_at < ends_at,
                (CompetitionFixture.home_team_id == team_id) | (CompetitionFixture.away_team_id == team_id),
            )
        )
    ).all()
    for fixture in fixtures:
        fixture_start = ensure_utc(fixture.scheduled_at)
        fixture_end = fixture_start + timedelta(hours=2)
        if fixture_end > starts_at:
            windows.append((fixture_start, fixture_end, f"fixture:{fixture.round_label or 'match'}"))

    bookings = (
        await db.scalars(
            select(FacilityBooking).where(
                FacilityBooking.organization_id == organization_id,
                FacilityBooking.team_id == team_id,
                FacilityBooking.starts_at < ends_at,
                FacilityBooking.status.in_(
                    [
                        FacilityBookingStatus.REQUESTED,
                        FacilityBookingStatus.APPROVED,
                        FacilityBookingStatus.CONFIRMED,
                        FacilityBookingStatus.CHECKED_IN,
                    ]
                ),
            )
        )
    ).all()
    for booking in bookings:
        booking_start = ensure_utc(booking.starts_at)
        booking_end = ensure_utc(booking.ends_at)
        if booking_end > starts_at:
            windows.append((booking_start, booking_end, f"facility:{booking.title}"))
    return windows


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def get_team_for_organization(
    db: AsyncSession,
    team_id: UUID,
    organization_id: UUID,
) -> Team:
    team = await db.get(Team, team_id)
    if team is None or team.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


async def get_athlete_for_organization(
    db: AsyncSession,
    athlete_profile_id: UUID,
    organization_id: UUID,
) -> AthleteProfile:
    athlete_profile = await db.get(AthleteProfile, athlete_profile_id)
    if athlete_profile is None or athlete_profile.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    return athlete_profile


async def get_training_plan(db: AsyncSession, plan_id: UUID) -> TrainingPlan:
    plan = await db.get(TrainingPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


async def get_training_plan_for_organization(
    db: AsyncSession,
    plan_id: UUID,
    organization_id: UUID,
) -> TrainingPlan:
    plan = await get_training_plan(db, plan_id)
    if plan.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


async def get_training_session_plan(db: AsyncSession, session_plan_id: UUID) -> TrainingSessionPlan:
    session_plan = await db.get(TrainingSessionPlan, session_plan_id)
    if session_plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session plan not found")
    return session_plan


def training_feedback_read(
    feedback: TrainingSessionFeedback,
    session_plan: TrainingSessionPlan,
) -> dict[str, object]:
    actual_load = None
    load_delta = None
    if feedback.actual_rpe is not None:
        duration = feedback.actual_duration_minutes or session_plan.duration_minutes
        actual_load = float(duration * feedback.actual_rpe)
        load_delta = actual_load - session_plan.load_score
    return {
        "id": feedback.id,
        "organization_id": feedback.organization_id,
        "session_plan_id": feedback.session_plan_id,
        "athlete_profile_id": feedback.athlete_profile_id,
        "recorded_by_person_id": feedback.recorded_by_person_id,
        "readiness_score": feedback.readiness_score,
        "soreness_score": feedback.soreness_score,
        "sleep_quality": feedback.sleep_quality,
        "mood_score": feedback.mood_score,
        "actual_rpe": feedback.actual_rpe,
        "actual_duration_minutes": feedback.actual_duration_minutes,
        "completed": feedback.completed,
        "feedback": feedback.feedback,
        "coach_notes": feedback.coach_notes,
        "recorded_at": feedback.recorded_at,
        "readiness_band": readiness_label(feedback.readiness_score),
        "load_delta": load_delta,
        "recommendation": training_feedback_recommendation(feedback, load_delta),
    }


def training_feedback_recommendation(
    feedback: TrainingSessionFeedback,
    load_delta: float | None,
) -> str:
    if feedback.readiness_score < 45 or feedback.soreness_score >= 8:
        return "Reduce intensity, add recovery work, and consider medical or guardian follow-up before the next load."
    if feedback.readiness_score < 65 or feedback.sleep_quality <= 4:
        return "Keep technical work, reduce high-intensity volume, and repeat readiness check before the next session."
    if load_delta is not None and load_delta > 150:
        return "Session load exceeded target; schedule recovery and monitor soreness within 24 hours."
    if feedback.completed:
        return "Session completed within acceptable readiness range; continue progression if next-day check remains stable."
    return "Readiness is acceptable; proceed with planned session and capture post-session RPE."


def availability_recommendation(score: int, conflicts: list[str]) -> str:
    if score == 100:
        return "Clear slot with no known team, fixture, training, or facility conflicts."
    if score >= 65:
        return f"Usable with review; check {', '.join(conflicts[:2])}."
    return "Avoid this slot unless conflicts are moved or the session is split."


def render_training_calendar_ics(
    organization: Organization,
    team: Team | None,
    sessions: list[TrainingSessionPlan],
    generated_at: datetime,
) -> str:
    calendar_name = f"{organization.name} training" if team is None else f"{team.name} training"
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AfroLete//Training Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{ics_escape(calendar_name)}",
        f"X-WR-CALDESC:{ics_escape('AfroLete training schedule export')}",
    ]
    for session in sessions:
        starts_at = ensure_utc(session.scheduled_for)
        ends_at = starts_at + timedelta(minutes=session.duration_minutes)
        description_parts = [
            f"Status: {session.status.value}",
            f"Target RPE: {session.rpe_target}",
            f"Load score: {session.load_score:g}",
        ]
        if session.objectives:
            description_parts.append(f"Objectives: {session.objectives}")
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:training-session-{session.id}@afrolete",
                f"DTSTAMP:{ics_datetime(generated_at)}",
                f"DTSTART:{ics_datetime(starts_at)}",
                f"DTEND:{ics_datetime(ends_at)}",
                f"SUMMARY:{ics_escape(session.title)}",
                f"DESCRIPTION:{ics_escape(chr(10).join(description_parts))}",
                f"CATEGORIES:{ics_escape('Training')}",
                f"STATUS:{ics_status(session.status)}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold_ics_line(line) for line in lines) + "\r\n"


def ics_datetime(value: datetime) -> str:
    return ensure_utc(value).strftime("%Y%m%dT%H%M%SZ")


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def ics_escape(value: object) -> str:
    text = str(value)
    return (
        text.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def ics_status(status_value: TrainingSessionStatus) -> str:
    if status_value == TrainingSessionStatus.CANCELLED:
        return "CANCELLED"
    if status_value == TrainingSessionStatus.COMPLETED:
        return "CONFIRMED"
    return "TENTATIVE" if status_value == TrainingSessionStatus.PLANNED else "CONFIRMED"


def fold_ics_line(line: str) -> str:
    if len(line) <= 75:
        return line
    chunks = [line[:75]]
    remaining = line[75:]
    while remaining:
        chunks.append(f" {remaining[:74]}")
        remaining = remaining[74:]
    return "\r\n".join(chunks)


def slug_for_training_calendar(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "schedule"


def infer_focus_area(assessments: list[AthleteAssessment], readiness_score: int) -> str:
    if readiness_score < 45:
        return "recovery and movement quality"
    if not assessments:
        return "technical fundamentals"
    latest = assessments[0]
    scores = {
        "physical conditioning": latest.physical_score,
        "technical execution": latest.technical_score,
        "tactical decision making": latest.tactical_score,
        "mental resilience": latest.mental_score,
    }
    return min(scores, key=scores.get)


def readiness_label(readiness_score: int) -> str:
    if readiness_score >= 85:
        return "high"
    if readiness_score >= 65:
        return "moderate"
    if readiness_score >= 45:
        return "limited"
    return "recovery"


def generated_load_guidance(
    readiness_score: int,
    weekly_sessions: int,
    next_competition_at: datetime | None,
) -> str:
    base = (
        f"Plan for {weekly_sessions} session(s) with "
        f"{'reduced' if readiness_score < 65 else 'progressive'} load."
    )
    if next_competition_at is not None:
        return f"{base} Taper the final session before {next_competition_at.date()}."
    return f"{base} Increase intensity only after readiness and soreness checks are stable."


def generated_recovery_protocol(readiness_score: int) -> str:
    if readiness_score < 45:
        return "Prioritize sleep, hydration, mobility, and medical review before high-intensity work."
    if readiness_score < 65:
        return "Add mobility, low-impact conditioning, and post-session soreness checks."
    return "Use normal cooldown, hydration, nutrition, and next-day readiness check-ins."


def select_training_drills(
    drills: list[TrainingDrill],
    focus_area: str,
    weekly_sessions: int,
) -> list[TrainingDrill]:
    focus = focus_area.lower()
    matching = [drill for drill in drills if focus in drill.focus_area.lower()]
    selected = matching or drills
    return selected[:weekly_sessions]


def generated_intensity(
    readiness_score: int,
    sequence: int,
    competition_weight: int,
) -> int:
    base = 4 if readiness_score < 45 else 5 if readiness_score < 65 else 6
    progression = min(sequence - 1, 2)
    taper = 1 if competition_weight >= 7 and sequence > 1 else 0
    return max(1, min(10, base + progression - taper))
