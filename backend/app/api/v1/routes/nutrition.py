from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.nutrition import (
    AthleteMealLogCreate,
    AthleteMealLogRead,
    AthleteMealPlanCreate,
    AthleteMealPlanRead,
    AthleteNutritionDashboardRead,
    AthleteNutritionProfileCreate,
    AthleteNutritionProfileRead,
    NutritionEducationAssignmentCreate,
    NutritionEducationAssignmentRead,
    NutritionEducationProgressUpdate,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.nutrition import (
    assign_nutrition_education,
    athlete_nutrition_dashboard,
    create_meal_plan,
    get_nutrition_profile,
    list_meal_logs,
    list_meal_plans,
    list_nutrition_education,
    record_meal_log,
    update_nutrition_education_progress,
    upsert_nutrition_profile,
)

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.post(
    "/athletes/{athlete_profile_id}/profile",
    response_model=AthleteNutritionProfileRead,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_nutrition_profile_route(
    athlete_profile_id: UUID,
    payload: AthleteNutritionProfileCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthleteNutritionProfileRead:
    return AthleteNutritionProfileRead.model_validate(
        await upsert_nutrition_profile(db, identity, athlete_profile_id, payload, authz)
    )


@router.get(
    "/athletes/{athlete_profile_id}/profile",
    response_model=AthleteNutritionProfileRead | None,
)
async def get_nutrition_profile_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> AthleteNutritionProfileRead | None:
    profile = await get_nutrition_profile(db, organization_id, athlete_profile_id)
    return AthleteNutritionProfileRead.model_validate(profile) if profile else None


@router.post(
    "/athletes/{athlete_profile_id}/meal-plans",
    response_model=AthleteMealPlanRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_meal_plan_route(
    athlete_profile_id: UUID,
    payload: AthleteMealPlanCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthleteMealPlanRead:
    return AthleteMealPlanRead.model_validate(await create_meal_plan(db, identity, athlete_profile_id, payload, authz))


@router.get(
    "/athletes/{athlete_profile_id}/meal-plans",
    response_model=list[AthleteMealPlanRead],
)
async def list_meal_plans_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AthleteMealPlanRead]:
    return [
        AthleteMealPlanRead.model_validate(plan)
        for plan in await list_meal_plans(db, organization_id, athlete_profile_id)
    ]


@router.post(
    "/athletes/{athlete_profile_id}/meal-logs",
    response_model=AthleteMealLogRead,
    status_code=status.HTTP_201_CREATED,
)
async def record_meal_log_route(
    athlete_profile_id: UUID,
    payload: AthleteMealLogCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthleteMealLogRead:
    return AthleteMealLogRead.model_validate(await record_meal_log(db, identity, athlete_profile_id, payload, authz))


@router.get(
    "/athletes/{athlete_profile_id}/meal-logs",
    response_model=list[AthleteMealLogRead],
)
async def list_meal_logs_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    limit: int = Query(default=20, ge=1, le=80),
    db: AsyncSession = Depends(get_db),
) -> list[AthleteMealLogRead]:
    return [
        AthleteMealLogRead.model_validate(log)
        for log in await list_meal_logs(db, organization_id, athlete_profile_id, limit=limit)
    ]


@router.post(
    "/athletes/{athlete_profile_id}/education-assignments",
    response_model=NutritionEducationAssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def assign_nutrition_education_route(
    athlete_profile_id: UUID,
    payload: NutritionEducationAssignmentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> NutritionEducationAssignmentRead:
    return NutritionEducationAssignmentRead.model_validate(
        await assign_nutrition_education(db, identity, athlete_profile_id, payload, authz)
    )


@router.patch(
    "/education-assignments/{assignment_id}",
    response_model=NutritionEducationAssignmentRead,
)
async def update_nutrition_education_progress_route(
    assignment_id: UUID,
    payload: NutritionEducationProgressUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> NutritionEducationAssignmentRead:
    return NutritionEducationAssignmentRead.model_validate(
        await update_nutrition_education_progress(db, identity, assignment_id, payload, authz)
    )


@router.get(
    "/athletes/{athlete_profile_id}/education-assignments",
    response_model=list[NutritionEducationAssignmentRead],
)
async def list_nutrition_education_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[NutritionEducationAssignmentRead]:
    return [
        NutritionEducationAssignmentRead.model_validate(assignment)
        for assignment in await list_nutrition_education(db, organization_id, athlete_profile_id)
    ]


@router.get(
    "/athletes/{athlete_profile_id}/dashboard",
    response_model=AthleteNutritionDashboardRead,
)
async def athlete_nutrition_dashboard_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> AthleteNutritionDashboardRead:
    return await athlete_nutrition_dashboard(db, organization_id, athlete_profile_id)
