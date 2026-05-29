from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.volunteer import (
    PublicVolunteerGroupSignupCreate,
    PublicVolunteerSignupCreate,
    PublicVolunteerSignupRead,
    VolunteerAssignmentCreate,
    VolunteerAssignmentRead,
    VolunteerAssignmentUpdate,
    VolunteerGroupApplicationRead,
    VolunteerGroupApplicationUpdate,
    VolunteerOpportunityCreate,
    VolunteerOpportunityRead,
    VolunteerProfileCreate,
    VolunteerProfileRead,
    VolunteerRecognitionCreate,
    VolunteerRecognitionRead,
    VolunteerSummaryRead,
    VolunteerTrainingRecordCreate,
    VolunteerTrainingRecordRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.volunteers import (
    create_public_volunteer_group_application,
    create_public_volunteer_signup,
    create_volunteer_assignment,
    create_volunteer_opportunity,
    create_volunteer_profile,
    create_volunteer_recognition,
    create_volunteer_training_record,
    decode_list,
    ensure_manage_volunteers,
    list_public_volunteer_opportunities,
    list_volunteer_group_applications,
    list_volunteer_assignments,
    list_volunteer_opportunities,
    list_volunteer_profiles,
    list_volunteer_recognitions,
    list_volunteer_training_records,
    update_volunteer_group_application,
    update_volunteer_assignment,
    volunteer_summary,
)

router = APIRouter(prefix="/volunteers", tags=["volunteers"])


def to_profile_read(profile, person) -> VolunteerProfileRead:
    return VolunteerProfileRead(
        id=profile.id,
        organization_id=profile.organization_id,
        person_id=profile.person_id,
        person_name=person.display_name,
        person_email=person.primary_email,
        volunteer_type=profile.volunteer_type,
        certification_level=profile.certification_level,
        availability=decode_list(profile.availability_json),
        skills=decode_list(profile.skills_json),
        background_check_status=profile.background_check_status,
        background_check_expires_on=profile.background_check_expires_on,
        training_status=profile.training_status,
        onboarding_status=profile.onboarding_status,
        reliability_score=profile.reliability_score,
        emergency_contact=profile.emergency_contact,
        notes=profile.notes,
        status=profile.status,
    )


def to_opportunity_read(opportunity, assigned_count: int) -> VolunteerOpportunityRead:
    return VolunteerOpportunityRead(
        id=opportunity.id,
        organization_id=opportunity.organization_id,
        team_id=opportunity.team_id,
        event_id=opportunity.event_id,
        title=opportunity.title,
        role_type=opportunity.role_type,
        description=opportunity.description,
        required_skills=decode_list(opportunity.required_skills_json),
        starts_at=opportunity.starts_at,
        ends_at=opportunity.ends_at,
        location=opportunity.location,
        slots_required=opportunity.slots_required,
        assigned_count=assigned_count,
        open_slots=max(opportunity.slots_required - assigned_count, 0),
        min_age=opportunity.min_age,
        background_check_required=opportunity.background_check_required,
        training_required=opportunity.training_required,
        public_signup=opportunity.public_signup,
        priority=opportunity.priority,
        status=opportunity.status,
    )


def to_assignment_read(item) -> VolunteerAssignmentRead:
    assignment, _profile, person, opportunity = item
    return VolunteerAssignmentRead(
        id=assignment.id,
        organization_id=assignment.organization_id,
        opportunity_id=assignment.opportunity_id,
        volunteer_profile_id=assignment.volunteer_profile_id,
        person_id=assignment.person_id,
        person_name=person.display_name,
        opportunity_title=opportunity.title,
        role_type=opportunity.role_type,
        status=assignment.status,
        match_score=assignment.match_score,
        confirmed_at=assignment.confirmed_at,
        checked_in_at=assignment.checked_in_at,
        checked_out_at=assignment.checked_out_at,
        hours_logged=assignment.hours_logged,
        notes=assignment.notes,
    )


def to_training_read(record) -> VolunteerTrainingRecordRead:
    return VolunteerTrainingRecordRead(
        id=record.id,
        organization_id=record.organization_id,
        volunteer_profile_id=record.volunteer_profile_id,
        module_name=record.module_name,
        role_type=record.role_type,
        required=record.required,
        status=record.status,
        assigned_at=record.assigned_at,
        completed_at=record.completed_at,
        expires_on=record.expires_on,
        score=record.score,
        certificate_url=record.certificate_url,
    )


def to_recognition_read(recognition) -> VolunteerRecognitionRead:
    return VolunteerRecognitionRead(
        id=recognition.id,
        organization_id=recognition.organization_id,
        volunteer_profile_id=recognition.volunteer_profile_id,
        recognition_type=recognition.recognition_type,
        badge_code=recognition.badge_code,
        title=recognition.title,
        points=recognition.points,
        awarded_on=recognition.awarded_on,
        source_summary=recognition.source_summary,
    )


def to_public_signup_read(item) -> PublicVolunteerSignupRead:
    assignment, profile, person, opportunity = item
    return PublicVolunteerSignupRead(
        organization_id=assignment.organization_id,
        opportunity_id=assignment.opportunity_id,
        opportunity_title=opportunity.title,
        volunteer_profile_id=profile.id,
        assignment_id=assignment.id,
        person_id=person.id,
        person_name=person.display_name,
        person_email=person.primary_email,
        status=assignment.status,
        match_score=assignment.match_score,
        onboarding_status=profile.onboarding_status,
        message=assignment.notes,
    )


def to_group_application_read(item) -> VolunteerGroupApplicationRead:
    application, opportunity = item
    return VolunteerGroupApplicationRead(
        id=application.id,
        organization_id=application.organization_id,
        opportunity_id=application.opportunity_id,
        opportunity_title=opportunity.title,
        company_name=application.company_name,
        coordinator_name=application.coordinator_name,
        coordinator_email=application.coordinator_email,
        coordinator_phone=application.coordinator_phone,
        group_size=application.group_size,
        requested_slots=application.requested_slots,
        approved_slots=application.approved_slots,
        skills=decode_list(application.skills_json),
        availability=decode_list(application.availability_json),
        message=application.message,
        source_url=application.source_url,
        status=application.status,
        reviewed_by_person_id=application.reviewed_by_person_id,
        reviewed_at=application.reviewed_at,
        review_notes=application.review_notes,
    )


@router.get("/public/{site}/opportunities", response_model=list[VolunteerOpportunityRead])
async def list_public_volunteer_opportunities_route(
    site: str,
    db: AsyncSession = Depends(get_db),
) -> list[VolunteerOpportunityRead]:
    _organization, rows = await list_public_volunteer_opportunities(db, site)
    return [to_opportunity_read(opportunity, int(assigned_count)) for opportunity, assigned_count in rows]


@router.post("/public/{site}/signups", response_model=PublicVolunteerSignupRead, status_code=status.HTTP_201_CREATED)
async def create_public_volunteer_signup_route(
    site: str,
    payload: PublicVolunteerSignupCreate,
    db: AsyncSession = Depends(get_db),
) -> PublicVolunteerSignupRead:
    return to_public_signup_read(await create_public_volunteer_signup(db, site, payload))


@router.post(
    "/public/{site}/group-signups",
    response_model=VolunteerGroupApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_public_volunteer_group_signup_route(
    site: str,
    payload: PublicVolunteerGroupSignupCreate,
    db: AsyncSession = Depends(get_db),
) -> VolunteerGroupApplicationRead:
    return to_group_application_read(await create_public_volunteer_group_application(db, site, payload))


@router.post("/profiles", response_model=VolunteerProfileRead, status_code=status.HTTP_201_CREATED)
async def create_volunteer_profile_route(
    payload: VolunteerProfileCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> VolunteerProfileRead:
    profile = await create_volunteer_profile(db, identity, payload, authz)
    rows = await list_volunteer_profiles(db, payload.organization_id)
    person = next(person for candidate, person in rows if candidate.id == profile.id)
    return to_profile_read(profile, person)


@router.get("/profiles", response_model=list[VolunteerProfileRead])
async def list_volunteer_profiles_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[VolunteerProfileRead]:
    return [to_profile_read(profile, person) for profile, person in await list_volunteer_profiles(db, organization_id)]


@router.post("/opportunities", response_model=VolunteerOpportunityRead, status_code=status.HTTP_201_CREATED)
async def create_volunteer_opportunity_route(
    payload: VolunteerOpportunityCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> VolunteerOpportunityRead:
    opportunity = await create_volunteer_opportunity(db, identity, payload, authz)
    return to_opportunity_read(opportunity, 0)


@router.get("/opportunities", response_model=list[VolunteerOpportunityRead])
async def list_volunteer_opportunities_route(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[VolunteerOpportunityRead]:
    return [
        to_opportunity_read(opportunity, int(assigned_count))
        for opportunity, assigned_count in await list_volunteer_opportunities(db, organization_id, team_id)
    ]


@router.post("/assignments", response_model=VolunteerAssignmentRead, status_code=status.HTTP_201_CREATED)
async def create_volunteer_assignment_route(
    payload: VolunteerAssignmentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> VolunteerAssignmentRead:
    assignment = await create_volunteer_assignment(db, identity, payload, authz)
    rows = await list_volunteer_assignments(db, payload.organization_id)
    return to_assignment_read(next(item for item in rows if item[0].id == assignment.id))


@router.patch("/assignments/{assignment_id}", response_model=VolunteerAssignmentRead)
async def update_volunteer_assignment_route(
    assignment_id: UUID,
    payload: VolunteerAssignmentUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> VolunteerAssignmentRead:
    assignment = await update_volunteer_assignment(db, identity, assignment_id, payload, authz)
    rows = await list_volunteer_assignments(db, assignment.organization_id)
    return to_assignment_read(next(item for item in rows if item[0].id == assignment.id))


@router.get("/assignments", response_model=list[VolunteerAssignmentRead])
async def list_volunteer_assignments_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[VolunteerAssignmentRead]:
    return [to_assignment_read(item) for item in await list_volunteer_assignments(db, organization_id)]


@router.get("/group-applications", response_model=list[VolunteerGroupApplicationRead])
async def list_volunteer_group_applications_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[VolunteerGroupApplicationRead]:
    await ensure_manage_volunteers(authz, identity, organization_id)
    return [to_group_application_read(item) for item in await list_volunteer_group_applications(db, organization_id)]


@router.patch("/group-applications/{application_id}", response_model=VolunteerGroupApplicationRead)
async def update_volunteer_group_application_route(
    application_id: UUID,
    payload: VolunteerGroupApplicationUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> VolunteerGroupApplicationRead:
    application = await update_volunteer_group_application(db, identity, application_id, payload, authz)
    rows = await list_volunteer_group_applications(db, application.organization_id)
    return to_group_application_read(next(item for item in rows if item[0].id == application.id))


@router.post("/training-records", response_model=VolunteerTrainingRecordRead, status_code=status.HTTP_201_CREATED)
async def create_volunteer_training_record_route(
    payload: VolunteerTrainingRecordCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> VolunteerTrainingRecordRead:
    return to_training_read(await create_volunteer_training_record(db, identity, payload, authz))


@router.get("/training-records", response_model=list[VolunteerTrainingRecordRead])
async def list_volunteer_training_records_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[VolunteerTrainingRecordRead]:
    return [to_training_read(record) for record in await list_volunteer_training_records(db, organization_id)]


@router.post("/recognitions", response_model=VolunteerRecognitionRead, status_code=status.HTTP_201_CREATED)
async def create_volunteer_recognition_route(
    payload: VolunteerRecognitionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> VolunteerRecognitionRead:
    return to_recognition_read(await create_volunteer_recognition(db, identity, payload, authz))


@router.get("/recognitions", response_model=list[VolunteerRecognitionRead])
async def list_volunteer_recognitions_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[VolunteerRecognitionRead]:
    return [to_recognition_read(record) for record in await list_volunteer_recognitions(db, organization_id)]


@router.get("/summary", response_model=VolunteerSummaryRead)
async def volunteer_summary_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> VolunteerSummaryRead:
    return VolunteerSummaryRead(**await volunteer_summary(db, organization_id))
