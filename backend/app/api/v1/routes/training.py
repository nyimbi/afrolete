from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.training import (
    GeneratedTrainingPlanRead,
    TrainingDrillCreate,
    TrainingDrillRead,
    TrainingPlanGenerateCreate,
    TrainingPlanCreate,
    TrainingPlanItemCreate,
    TrainingPlanItemRead,
    TrainingPlanRead,
    TrainingSessionPlanCreate,
    TrainingSessionPlanRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.training import (
    add_training_plan_item,
    create_training_drill,
    create_training_plan,
    create_training_session_plan,
    generate_training_plan,
    list_training_drills,
    list_training_plan_items,
    list_training_plans,
    list_training_session_plans,
)

router = APIRouter(prefix="/training", tags=["training"])


def to_drill_read(drill) -> TrainingDrillRead:
    return TrainingDrillRead(
        id=drill.id,
        organization_id=drill.organization_id,
        sport=drill.sport,
        name=drill.name,
        focus_area=drill.focus_area,
        category=drill.category,
        min_age=drill.min_age,
        max_age=drill.max_age,
        equipment=drill.equipment,
        description=drill.description,
        coaching_points=drill.coaching_points,
        default_duration_minutes=drill.default_duration_minutes,
        default_intensity=drill.default_intensity,
        status=drill.status,
    )


def to_plan_read(plan) -> TrainingPlanRead:
    return TrainingPlanRead(
        id=plan.id,
        organization_id=plan.organization_id,
        team_id=plan.team_id,
        athlete_profile_id=plan.athlete_profile_id,
        created_by_person_id=plan.created_by_person_id,
        title=plan.title,
        focus_area=plan.focus_area,
        period_start=plan.period_start,
        period_end=plan.period_end,
        status=plan.status,
        ai_generated=plan.ai_generated,
        source_summary=plan.source_summary,
        load_guidance=plan.load_guidance,
        recovery_protocol=plan.recovery_protocol,
        progress_checkpoints=plan.progress_checkpoints,
    )


def to_plan_item_read(item) -> TrainingPlanItemRead:
    return TrainingPlanItemRead(
        id=item.id,
        plan_id=item.plan_id,
        drill_id=item.drill_id,
        sequence=item.sequence,
        day_label=item.day_label,
        title=item.title,
        focus_area=item.focus_area,
        duration_minutes=item.duration_minutes,
        intensity=item.intensity,
        notes=item.notes,
    )


def to_session_plan_read(session_plan) -> TrainingSessionPlanRead:
    return TrainingSessionPlanRead(
        id=session_plan.id,
        organization_id=session_plan.organization_id,
        team_id=session_plan.team_id,
        plan_id=session_plan.plan_id,
        event_id=session_plan.event_id,
        title=session_plan.title,
        scheduled_for=session_plan.scheduled_for,
        duration_minutes=session_plan.duration_minutes,
        rpe_target=session_plan.rpe_target,
        load_score=session_plan.load_score,
        objectives=session_plan.objectives,
        status=session_plan.status,
    )


@router.post("/drills", response_model=TrainingDrillRead, status_code=status.HTTP_201_CREATED)
async def create_training_drill_route(
    payload: TrainingDrillCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TrainingDrillRead:
    return to_drill_read(await create_training_drill(db, identity, payload, authz))


@router.get("/drills", response_model=list[TrainingDrillRead])
async def list_training_drills_route(
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[TrainingDrillRead]:
    return [
        to_drill_read(drill)
        for drill in await list_training_drills(db, organization_id, sport=sport)
    ]


@router.post("/plans", response_model=TrainingPlanRead, status_code=status.HTTP_201_CREATED)
async def create_training_plan_route(
    payload: TrainingPlanCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TrainingPlanRead:
    return to_plan_read(await create_training_plan(db, identity, payload, authz))


@router.post(
    "/plans/generate",
    response_model=GeneratedTrainingPlanRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_training_plan_route(
    payload: TrainingPlanGenerateCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GeneratedTrainingPlanRead:
    result = await generate_training_plan(db, identity, payload, authz)
    return GeneratedTrainingPlanRead(
        plan=to_plan_read(result["plan"]),
        items=[to_plan_item_read(item) for item in result["items"]],
        readiness_score=result["readiness_score"],
        rationale=result["rationale"],
        load_balance=result["load_balance"],
        next_competition_at=result["next_competition_at"],
    )


@router.get("/plans", response_model=list[TrainingPlanRead])
async def list_training_plans_route(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    athlete_profile_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[TrainingPlanRead]:
    return [
        to_plan_read(plan)
        for plan in await list_training_plans(
            db,
            organization_id,
            team_id=team_id,
            athlete_profile_id=athlete_profile_id,
        )
    ]


@router.post(
    "/plans/{plan_id}/items",
    response_model=TrainingPlanItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_training_plan_item_route(
    plan_id: UUID,
    payload: TrainingPlanItemCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TrainingPlanItemRead:
    return to_plan_item_read(await add_training_plan_item(db, identity, plan_id, payload, authz))


@router.get("/plans/{plan_id}/items", response_model=list[TrainingPlanItemRead])
async def list_training_plan_items_route(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[TrainingPlanItemRead]:
    return [to_plan_item_read(item) for item in await list_training_plan_items(db, plan_id)]


@router.post(
    "/sessions",
    response_model=TrainingSessionPlanRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_training_session_plan_route(
    payload: TrainingSessionPlanCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TrainingSessionPlanRead:
    return to_session_plan_read(
        await create_training_session_plan(db, identity, payload, authz)
    )


@router.get("/sessions", response_model=list[TrainingSessionPlanRead])
async def list_training_session_plans_route(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[TrainingSessionPlanRead]:
    return [
        to_session_plan_read(session_plan)
        for session_plan in await list_training_session_plans(db, organization_id, team_id=team_id)
    ]
