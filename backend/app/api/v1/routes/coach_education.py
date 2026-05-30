from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.coach_education import (
    CoachEducationActivityCreate,
    CoachEducationActivityRead,
    CoachEducationCatalogRead,
    CoachEducationDashboardRead,
    CoachEducationEnrollmentCreate,
    CoachEducationEnrollmentRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.coach_education import (
    coach_education_catalog,
    coach_education_dashboard,
    coach_education_enrollment_read,
    create_coach_education_enrollment,
    list_coach_education_enrollments,
    record_coach_education_activity,
)

router = APIRouter(prefix="/coach-education", tags=["coach-education"])


@router.get("/catalog", response_model=CoachEducationCatalogRead)
async def coach_education_catalog_route() -> CoachEducationCatalogRead:
    return CoachEducationCatalogRead(**coach_education_catalog())


@router.post("/enrollments", response_model=CoachEducationEnrollmentRead, status_code=status.HTTP_201_CREATED)
async def create_coach_education_enrollment_route(
    payload: CoachEducationEnrollmentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CoachEducationEnrollmentRead:
    enrollment = await create_coach_education_enrollment(db, identity, payload, authz)
    return CoachEducationEnrollmentRead(**await coach_education_enrollment_read(db, enrollment))


@router.get("/enrollments", response_model=list[CoachEducationEnrollmentRead])
async def list_coach_education_enrollments_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[CoachEducationEnrollmentRead]:
    return [
        CoachEducationEnrollmentRead(**await coach_education_enrollment_read(db, enrollment))
        for enrollment in await list_coach_education_enrollments(db, identity, organization_id, authz)
    ]


@router.post(
    "/enrollments/{enrollment_id}/activities",
    response_model=CoachEducationActivityRead,
    status_code=status.HTTP_201_CREATED,
)
async def record_coach_education_activity_route(
    enrollment_id: UUID,
    payload: CoachEducationActivityCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CoachEducationActivityRead:
    activity, enrollment = await record_coach_education_activity(db, identity, enrollment_id, payload, authz)
    return CoachEducationActivityRead(
        id=activity.id,
        organization_id=activity.organization_id,
        enrollment_id=activity.enrollment_id,
        person_id=activity.person_id,
        activity_type=activity.activity_type,
        module_key=activity.module_key,
        title=activity.title,
        xp_awarded=activity.xp_awarded,
        evidence_ref=activity.evidence_ref,
        score_percent=activity.score_percent,
        completed_at=activity.completed_at,
        enrollment=CoachEducationEnrollmentRead(**await coach_education_enrollment_read(db, enrollment)),
    )


@router.get("/dashboard", response_model=CoachEducationDashboardRead)
async def coach_education_dashboard_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CoachEducationDashboardRead:
    return CoachEducationDashboardRead(
        **await coach_education_dashboard(db, identity, organization_id, authz)
    )
