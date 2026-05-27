from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competition import CompetitionFixture
from app.models.event import Event
from app.models.enums import TrainingSessionStatus
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
    TrainingDrillCreate,
    TrainingPlanGenerateCreate,
    TrainingPlanCreate,
    TrainingPlanItemCreate,
    TrainingSessionFeedbackCreate,
    TrainingSessionPlanCreate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService


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
    identity: CurrentIdentity,
    payload: TrainingPlanCreate,
    authz: AuthorizationService,
) -> TrainingPlan:
    await get_organization(db, payload.organization_id)
    await ensure_manage_training(authz, identity, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    if payload.athlete_profile_id is not None:
        await get_athlete_for_organization(db, payload.athlete_profile_id, payload.organization_id)

    plan = TrainingPlan(
        created_by_person_id=identity.person_id,
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
    identity: CurrentIdentity,
    plan_id: UUID,
    payload: TrainingPlanItemCreate,
    authz: AuthorizationService,
) -> TrainingPlanItem:
    plan = await get_training_plan(db, plan_id)
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
) -> dict[str, object]:
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
    plan = TrainingPlan(
        organization_id=payload.organization_id,
        team_id=payload.team_id,
        athlete_profile_id=payload.athlete_profile_id,
        created_by_person_id=identity.person_id,
        title=payload.title or f"AI {focus_area} block",
        focus_area=focus_area,
        period_start=payload.period_start,
        period_end=payload.period_end,
        ai_generated=True,
        source_summary=source_summary,
        load_guidance=load_guidance,
        recovery_protocol=generated_recovery_protocol(payload.readiness_score),
        progress_checkpoints="Review readiness after session 2; reassess after the final session; adjust load if soreness or school/work constraints increase.",
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    drills = await list_training_drills(db, payload.organization_id, sport=team.sport if team else None)
    selected_drills = select_training_drills(drills, focus_area, payload.weekly_sessions)
    items: list[TrainingPlanItem] = []
    for sequence in range(1, payload.weekly_sessions + 1):
        drill = selected_drills[sequence - 1] if sequence - 1 < len(selected_drills) else None
        intensity = generated_intensity(payload.readiness_score, sequence, payload.upcoming_competition_weight)
        item = TrainingPlanItem(
            plan_id=plan.id,
            drill_id=drill.id if drill else None,
            sequence=sequence,
            day_label=f"Session {sequence}",
            title=drill.name if drill else f"{focus_area} progression {sequence}",
            focus_area=drill.focus_area if drill else focus_area,
            duration_minutes=drill.default_duration_minutes if drill else 45,
            intensity=intensity,
            notes=(
                f"AI-generated for {readiness_band} readiness. "
                f"Keep RPE near {intensity}; adjust if competition proximity or recovery changes."
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
    }


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
    identity: CurrentIdentity,
    payload: TrainingSessionPlanCreate,
    authz: AuthorizationService,
) -> TrainingSessionPlan:
    await get_organization(db, payload.organization_id)
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


async def record_training_session_feedback(
    db: AsyncSession,
    identity: CurrentIdentity,
    session_plan_id: UUID,
    payload: TrainingSessionFeedbackCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    session_plan = await get_training_session_plan(db, session_plan_id)
    await ensure_manage_training(authz, identity, session_plan.organization_id)
    if payload.athlete_profile_id is not None:
        await get_athlete_for_organization(db, payload.athlete_profile_id, session_plan.organization_id)

    feedback = TrainingSessionFeedback(
        organization_id=session_plan.organization_id,
        session_plan_id=session_plan.id,
        recorded_by_person_id=identity.person_id,
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
