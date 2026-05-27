from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.organization import Organization
from app.models.team import AthleteProfile, Team
from app.models.training import (
    TrainingDrill,
    TrainingPlan,
    TrainingPlanItem,
    TrainingSessionPlan,
)
from app.schemas.training import (
    TrainingDrillCreate,
    TrainingPlanCreate,
    TrainingPlanItemCreate,
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
