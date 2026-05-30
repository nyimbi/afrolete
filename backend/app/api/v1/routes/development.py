from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.development import (
    AthleteAcademicRecordCreate,
    AthleteAcademicRecordRead,
    AthleteDevelopmentDashboardRead,
    AthleteLifeSkillAssignmentCreate,
    AthleteLifeSkillAssignmentRead,
    AthleteLifeSkillProgressUpdate,
    AthleteScholarshipApplicationCreate,
    AthleteScholarshipApplicationRead,
    AthleteScholarshipApplicationReview,
    AthleteWellnessCheckInCreate,
    AthleteWellnessCheckInRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.development import (
    athlete_development_dashboard,
    assign_life_skill_module,
    create_scholarship_application,
    create_wellness_check_in,
    list_academic_records,
    list_life_skill_assignments,
    list_scholarship_applications,
    list_wellness_check_ins,
    review_scholarship_application,
    update_life_skill_progress,
    upsert_academic_record,
)

router = APIRouter(prefix="/development", tags=["development"])


def to_wellness_read(check_in) -> AthleteWellnessCheckInRead:
    return AthleteWellnessCheckInRead(
        id=check_in.id,
        organization_id=check_in.organization_id,
        athlete_profile_id=check_in.athlete_profile_id,
        submitted_by_person_id=check_in.submitted_by_person_id,
        check_in_at=check_in.check_in_at,
        mood_score=check_in.mood_score,
        stress_score=check_in.stress_score,
        sleep_hours=check_in.sleep_hours,
        energy_score=check_in.energy_score,
        soreness_score=check_in.soreness_score,
        resilience_score=check_in.resilience_score,
        support_requested=check_in.support_requested,
        risk_band=check_in.risk_band,
        notes=check_in.notes,
        created_at=check_in.created_at,
    )


def to_academic_read(record) -> AthleteAcademicRecordRead:
    return AthleteAcademicRecordRead(
        id=record.id,
        organization_id=record.organization_id,
        athlete_profile_id=record.athlete_profile_id,
        recorded_by_person_id=record.recorded_by_person_id,
        school_name=record.school_name,
        term_label=record.term_label,
        grade_level=record.grade_level,
        gpa=record.gpa,
        attendance_rate=record.attendance_rate,
        study_hours_weekly=record.study_hours_weekly,
        missing_assignment_count=record.missing_assignment_count,
        eligibility_status=record.eligibility_status,
        risk_level=record.risk_level,
        next_review_on=record.next_review_on,
        notes=record.notes,
        created_at=record.created_at,
    )


def to_life_skill_read(assignment) -> AthleteLifeSkillAssignmentRead:
    return AthleteLifeSkillAssignmentRead(
        id=assignment.id,
        organization_id=assignment.organization_id,
        athlete_profile_id=assignment.athlete_profile_id,
        assigned_by_person_id=assignment.assigned_by_person_id,
        module_code=assignment.module_code,
        title=assignment.title,
        category=assignment.category,
        level=assignment.level,
        status=assignment.status,
        progress_percent=assignment.progress_percent,
        due_on=assignment.due_on,
        completed_at=assignment.completed_at,
        evidence_notes=assignment.evidence_notes,
        created_at=assignment.created_at,
    )


def to_scholarship_read(application) -> AthleteScholarshipApplicationRead:
    return AthleteScholarshipApplicationRead(
        id=application.id,
        organization_id=application.organization_id,
        athlete_profile_id=application.athlete_profile_id,
        created_by_person_id=application.created_by_person_id,
        program_name=application.program_name,
        scholarship_type=application.scholarship_type,
        donor_or_fund=application.donor_or_fund,
        amount_requested=application.amount_requested,
        amount_awarded=application.amount_awarded,
        currency=application.currency,
        status=application.status,
        eligibility_score=application.eligibility_score,
        committee_recommendation=application.committee_recommendation,
        deadline_on=application.deadline_on,
        submitted_on=application.submitted_on,
        decided_on=application.decided_on,
        notes=application.notes,
        created_at=application.created_at,
    )


@router.post(
    "/athletes/{athlete_profile_id}/wellness-check-ins",
    response_model=AthleteWellnessCheckInRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_wellness_check_in_route(
    athlete_profile_id: UUID,
    payload: AthleteWellnessCheckInCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthleteWellnessCheckInRead:
    return to_wellness_read(await create_wellness_check_in(db, identity, athlete_profile_id, payload, authz))


@router.get(
    "/athletes/{athlete_profile_id}/wellness-check-ins",
    response_model=list[AthleteWellnessCheckInRead],
)
async def list_wellness_check_ins_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    limit: int = Query(default=12, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
) -> list[AthleteWellnessCheckInRead]:
    return [
        to_wellness_read(check_in)
        for check_in in await list_wellness_check_ins(db, organization_id, athlete_profile_id, limit=limit)
    ]


@router.post(
    "/athletes/{athlete_profile_id}/academic-records",
    response_model=AthleteAcademicRecordRead,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_academic_record_route(
    athlete_profile_id: UUID,
    payload: AthleteAcademicRecordCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthleteAcademicRecordRead:
    return to_academic_read(await upsert_academic_record(db, identity, athlete_profile_id, payload, authz))


@router.get(
    "/athletes/{athlete_profile_id}/academic-records",
    response_model=list[AthleteAcademicRecordRead],
)
async def list_academic_records_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AthleteAcademicRecordRead]:
    return [
        to_academic_read(record)
        for record in await list_academic_records(db, organization_id, athlete_profile_id)
    ]


@router.post(
    "/athletes/{athlete_profile_id}/life-skill-assignments",
    response_model=AthleteLifeSkillAssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def assign_life_skill_module_route(
    athlete_profile_id: UUID,
    payload: AthleteLifeSkillAssignmentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthleteLifeSkillAssignmentRead:
    return to_life_skill_read(await assign_life_skill_module(db, identity, athlete_profile_id, payload, authz))


@router.patch(
    "/life-skill-assignments/{assignment_id}",
    response_model=AthleteLifeSkillAssignmentRead,
)
async def update_life_skill_progress_route(
    assignment_id: UUID,
    payload: AthleteLifeSkillProgressUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthleteLifeSkillAssignmentRead:
    return to_life_skill_read(await update_life_skill_progress(db, identity, assignment_id, payload, authz))


@router.get(
    "/athletes/{athlete_profile_id}/life-skill-assignments",
    response_model=list[AthleteLifeSkillAssignmentRead],
)
async def list_life_skill_assignments_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AthleteLifeSkillAssignmentRead]:
    return [
        to_life_skill_read(assignment)
        for assignment in await list_life_skill_assignments(db, organization_id, athlete_profile_id)
    ]


@router.post(
    "/athletes/{athlete_profile_id}/scholarship-applications",
    response_model=AthleteScholarshipApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_scholarship_application_route(
    athlete_profile_id: UUID,
    payload: AthleteScholarshipApplicationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthleteScholarshipApplicationRead:
    return to_scholarship_read(await create_scholarship_application(db, identity, athlete_profile_id, payload, authz))


@router.patch(
    "/scholarship-applications/{application_id}",
    response_model=AthleteScholarshipApplicationRead,
)
async def review_scholarship_application_route(
    application_id: UUID,
    payload: AthleteScholarshipApplicationReview,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AthleteScholarshipApplicationRead:
    return to_scholarship_read(await review_scholarship_application(db, identity, application_id, payload, authz))


@router.get(
    "/athletes/{athlete_profile_id}/scholarship-applications",
    response_model=list[AthleteScholarshipApplicationRead],
)
async def list_scholarship_applications_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AthleteScholarshipApplicationRead]:
    return [
        to_scholarship_read(application)
        for application in await list_scholarship_applications(db, organization_id, athlete_profile_id)
    ]


@router.get(
    "/athletes/{athlete_profile_id}/dashboard",
    response_model=AthleteDevelopmentDashboardRead,
)
async def athlete_development_dashboard_route(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> AthleteDevelopmentDashboardRead:
    return await athlete_development_dashboard(db, organization_id, athlete_profile_id)
