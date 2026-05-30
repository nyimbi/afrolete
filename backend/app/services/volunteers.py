import json
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import CommunicationMessage, MessageRecipient
from app.models.event import BackgroundCheck, Event
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.enums import (
    BackgroundCheckStatus,
    CommunicationChannel,
    CommunicationMessageType,
    CommunicationScopeType,
    MemberSubjectType,
    MembershipRole,
)
from app.models.team import Team
from app.models.volunteer import (
    VolunteerAssignment,
    VolunteerGroupApplication,
    VolunteerNeedRequest,
    VolunteerObligation,
    VolunteerOpportunity,
    VolunteerProfile,
    VolunteerRecognition,
    VolunteerSubstitutePoolMember,
    VolunteerTrainingRecord,
)
from app.schemas.volunteer import (
    PublicVolunteerGroupSignupCreate,
    PublicVolunteerSignupCreate,
    VolunteerAssignmentCreate,
    VolunteerAssignmentUpdate,
    VolunteerBackgroundCheckSubmitCreate,
    VolunteerCoordinationMessageCreate,
    VolunteerCoordinationMessageRead,
    VolunteerGroupApplicationUpdate,
    VolunteerNeedRequestCreate,
    VolunteerNeedRequestUpdate,
    VolunteerObligationCreate,
    VolunteerObligationUpdate,
    VolunteerOpportunityCreate,
    VolunteerProfileCreate,
    VolunteerReminderRunCreate,
    VolunteerReminderRunRead,
    VolunteerRecognitionCreate,
    VolunteerSubstituteDispatchCreate,
    VolunteerSubstituteDispatchRead,
    VolunteerSubstitutePoolMemberCreate,
    VolunteerTrainingRecordCreate,
)
from app.schemas.safeguarding import BackgroundCheckProviderSubmissionRead
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.communications import create_message_for_recipients
from app.services.safeguarding import submit_background_check_to_screening_provider


async def ensure_manage_volunteers(
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


def encode_list(values: list[str]) -> str:
    return json.dumps([value.strip().lower() for value in values if value.strip()])


def decode_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item)]


def now_for_datetime_column(value: datetime) -> datetime:
    now = datetime.now(UTC)
    return now.replace(tzinfo=None) if value.tzinfo is None else now


def as_utc_datetime(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def merge_encoded_lists(existing: str | None, incoming: list[str]) -> str:
    merged = [*decode_list(existing), *[value.strip().lower() for value in incoming if value.strip()]]
    return json.dumps(list(dict.fromkeys(merged)))


async def ensure_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def get_public_volunteer_organization(db: AsyncSession, site: str) -> Organization:
    organization = await db.scalar(
        select(Organization).where((Organization.slug == site) | (Organization.subdomain == site))
    )
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return organization


async def ensure_volunteer_scope(
    db: AsyncSession,
    organization_id: UUID,
    team_id: UUID | None = None,
    event_id: UUID | None = None,
) -> None:
    await ensure_organization(db, organization_id)
    if team_id is not None:
        team = await db.get(Team, team_id)
        if team is None or team.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if event_id is not None:
        event = await db.get(Event, event_id)
        if event is None or event.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")


async def get_or_create_volunteer_person(db: AsyncSession, payload: VolunteerProfileCreate) -> Person:
    if payload.person_id is not None:
        person = await db.get(Person, payload.person_id)
        if person is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
        return person
    if not payload.email:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Volunteer email required")
    person = await db.scalar(select(Person).where(Person.primary_email == payload.email.lower()))
    if person is None:
        person = Person(
            display_name=payload.display_name or payload.email.split("@")[0],
            primary_email=payload.email.lower(),
        )
        db.add(person)
        await db.flush()
    return person


async def get_or_create_person_by_contact(
    db: AsyncSession,
    *,
    person_id: UUID | None,
    email: str | None,
    display_name: str | None,
) -> Person:
    if person_id is not None:
        person = await db.get(Person, person_id)
        if person is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
        return person
    if not email:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Person email required")
    person = await db.scalar(select(Person).where(Person.primary_email == email.lower()))
    if person is None:
        person = Person(
            display_name=display_name or email.split("@")[0],
            primary_email=email.lower(),
        )
        db.add(person)
        await db.flush()
    return person


async def ensure_volunteer_membership(
    db: AsyncSession,
    *,
    organization_id: UUID,
    person_id: UUID,
    title: str,
) -> None:
    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == person_id,
            Membership.role == MembershipRole.VOLUNTEER,
        )
    )
    if membership is None:
        db.add(
            Membership(
                organization_id=organization_id,
                subject_type=MemberSubjectType.PERSON,
                subject_id=person_id,
                role=MembershipRole.VOLUNTEER,
                title=title,
            )
        )


async def create_volunteer_profile(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VolunteerProfileCreate,
    authz: AuthorizationService,
) -> VolunteerProfile:
    await ensure_manage_volunteers(authz, identity, payload.organization_id)
    await ensure_volunteer_scope(db, payload.organization_id)
    person = await get_or_create_volunteer_person(db, payload)
    existing = await db.scalar(
        select(VolunteerProfile).where(
            VolunteerProfile.organization_id == payload.organization_id,
            VolunteerProfile.person_id == person.id,
        )
    )
    if existing is not None:
        existing.volunteer_type = payload.volunteer_type
        existing.certification_level = payload.certification_level
        existing.availability_json = encode_list(payload.availability)
        existing.skills_json = encode_list(payload.skills)
        existing.background_check_status = payload.background_check_status
        existing.background_check_expires_on = payload.background_check_expires_on
        existing.training_status = payload.training_status
        existing.onboarding_status = payload.onboarding_status
        existing.reliability_score = payload.reliability_score
        existing.emergency_contact = payload.emergency_contact
        existing.notes = payload.notes
        await db.commit()
        await db.refresh(existing)
        return existing
    profile = VolunteerProfile(
        organization_id=payload.organization_id,
        person_id=person.id,
        volunteer_type=payload.volunteer_type,
        certification_level=payload.certification_level,
        availability_json=encode_list(payload.availability),
        skills_json=encode_list(payload.skills),
        background_check_status=payload.background_check_status,
        background_check_expires_on=payload.background_check_expires_on,
        training_status=payload.training_status,
        onboarding_status=payload.onboarding_status,
        reliability_score=payload.reliability_score,
        emergency_contact=payload.emergency_contact,
        notes=payload.notes,
    )
    db.add(profile)
    await ensure_volunteer_membership(
        db,
        organization_id=payload.organization_id,
        person_id=person.id,
        title=f"{payload.volunteer_type.replace('_', ' ').title()} Volunteer",
    )
    await db.commit()
    await db.refresh(profile)
    return profile


async def list_volunteer_profiles(db: AsyncSession, organization_id: UUID) -> list[tuple[VolunteerProfile, Person]]:
    rows = (
        await db.execute(
            select(VolunteerProfile, Person)
            .join(Person, Person.id == VolunteerProfile.person_id)
            .where(VolunteerProfile.organization_id == organization_id)
            .order_by(VolunteerProfile.volunteer_type, Person.display_name)
        )
    ).all()
    return list(rows)


async def create_volunteer_opportunity(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VolunteerOpportunityCreate,
    authz: AuthorizationService,
) -> VolunteerOpportunity:
    await ensure_manage_volunteers(authz, identity, payload.organization_id)
    await ensure_volunteer_scope(db, payload.organization_id, payload.team_id, payload.event_id)
    if payload.ends_at is not None and payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="End must be after start")
    opportunity = VolunteerOpportunity(
        organization_id=payload.organization_id,
        team_id=payload.team_id,
        event_id=payload.event_id,
        title=payload.title,
        role_type=payload.role_type,
        description=payload.description,
        required_skills_json=encode_list(payload.required_skills),
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        location=payload.location,
        slots_required=payload.slots_required,
        min_age=payload.min_age,
        background_check_required=payload.background_check_required,
        training_required=payload.training_required,
        public_signup=payload.public_signup,
        priority=payload.priority,
    )
    db.add(opportunity)
    await db.commit()
    await db.refresh(opportunity)
    return opportunity


async def list_volunteer_opportunities(
    db: AsyncSession,
    organization_id: UUID,
    team_id: UUID | None = None,
) -> list[tuple[VolunteerOpportunity, int]]:
    statement = (
        select(VolunteerOpportunity, func.count(VolunteerAssignment.id))
        .outerjoin(
            VolunteerAssignment,
            and_(
                VolunteerAssignment.opportunity_id == VolunteerOpportunity.id,
                VolunteerAssignment.status.in_(["assigned", "confirmed", "checked_in", "completed"]),
            ),
        )
        .where(VolunteerOpportunity.organization_id == organization_id)
        .group_by(VolunteerOpportunity.id)
        .order_by(VolunteerOpportunity.starts_at.desc())
    )
    if team_id is not None:
        statement = statement.where(VolunteerOpportunity.team_id == team_id)
    return list((await db.execute(statement)).all())


async def create_volunteer_need_request(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VolunteerNeedRequestCreate,
    authz: AuthorizationService,
) -> VolunteerNeedRequest:
    await ensure_manage_volunteers(authz, identity, payload.organization_id)
    await ensure_volunteer_scope(db, payload.organization_id, payload.team_id, payload.event_id)
    opportunity_id: UUID | None = None
    status_value = "requested"
    if payload.create_opportunity:
        starts_at = payload.needed_by or datetime.now(UTC)
        opportunity = VolunteerOpportunity(
            organization_id=payload.organization_id,
            team_id=payload.team_id,
            event_id=payload.event_id,
            title=payload.title,
            role_type=payload.role_type,
            description=payload.notes,
            required_skills_json=encode_list(payload.required_skills),
            starts_at=starts_at,
            ends_at=None,
            slots_required=payload.needed_count,
            priority=payload.priority,
        )
        db.add(opportunity)
        await db.flush()
        opportunity_id = opportunity.id
        status_value = "converted"
    request = VolunteerNeedRequest(
        organization_id=payload.organization_id,
        team_id=payload.team_id,
        event_id=payload.event_id,
        requested_by_person_id=identity.person_id,
        title=payload.title,
        role_type=payload.role_type,
        needed_count=payload.needed_count,
        required_skills_json=encode_list(payload.required_skills),
        needed_by=payload.needed_by,
        priority=payload.priority,
        status=status_value,
        notes=payload.notes,
        opportunity_id=opportunity_id,
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def list_volunteer_need_requests(
    db: AsyncSession,
    organization_id: UUID,
) -> list[VolunteerNeedRequest]:
    return list(
        (
            await db.scalars(
                select(VolunteerNeedRequest)
                .where(VolunteerNeedRequest.organization_id == organization_id)
                .order_by(VolunteerNeedRequest.created_at.desc())
            )
        ).all()
    )


async def update_volunteer_need_request(
    db: AsyncSession,
    identity: CurrentIdentity,
    request_id: UUID,
    payload: VolunteerNeedRequestUpdate,
    authz: AuthorizationService,
) -> VolunteerNeedRequest:
    request = await db.get(VolunteerNeedRequest, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need request not found")
    await ensure_manage_volunteers(authz, identity, request.organization_id)
    if payload.opportunity_id is not None:
        opportunity = await get_volunteer_opportunity(db, payload.opportunity_id)
        if opportunity.organization_id != request.organization_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
        request.opportunity_id = opportunity.id
        if request.status == "requested":
            request.status = "converted"
    if payload.status is not None:
        request.status = payload.status
    if payload.notes is not None:
        request.notes = payload.notes
    await db.commit()
    await db.refresh(request)
    return request


async def list_public_volunteer_opportunities(
    db: AsyncSession,
    site: str,
) -> tuple[Organization, list[tuple[VolunteerOpportunity, int]]]:
    organization = await get_public_volunteer_organization(db, site)
    statement = (
        select(VolunteerOpportunity, func.count(VolunteerAssignment.id))
        .outerjoin(
            VolunteerAssignment,
            and_(
                VolunteerAssignment.opportunity_id == VolunteerOpportunity.id,
                VolunteerAssignment.status.in_(["assigned", "confirmed", "checked_in", "completed"]),
            ),
        )
        .where(VolunteerOpportunity.organization_id == organization.id)
        .where(VolunteerOpportunity.public_signup.is_(True))
        .where(VolunteerOpportunity.status == "open")
        .where(VolunteerOpportunity.starts_at >= datetime.now(UTC))
        .group_by(VolunteerOpportunity.id)
        .order_by(VolunteerOpportunity.starts_at, VolunteerOpportunity.priority.desc(), VolunteerOpportunity.title)
        .limit(24)
    )
    return organization, list((await db.execute(statement)).all())


async def get_volunteer_opportunity(db: AsyncSession, opportunity_id: UUID) -> VolunteerOpportunity:
    opportunity = await db.get(VolunteerOpportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return opportunity


async def get_volunteer_profile(db: AsyncSession, profile_id: UUID) -> VolunteerProfile:
    profile = await db.get(VolunteerProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volunteer profile not found")
    return profile


def volunteer_background_check_status(check_status: BackgroundCheckStatus) -> str:
    return {
        BackgroundCheckStatus.REQUESTED: "pending",
        BackgroundCheckStatus.IN_PROGRESS: "in_progress",
        BackgroundCheckStatus.CLEAR: "cleared",
        BackgroundCheckStatus.REVIEW_REQUIRED: "review_required",
        BackgroundCheckStatus.FAILED: "failed",
        BackgroundCheckStatus.EXPIRED: "expired",
    }.get(check_status, str(check_status))


def volunteer_background_check_type(profile: VolunteerProfile, payload: VolunteerBackgroundCheckSubmitCreate) -> str:
    if payload.check_type:
        return payload.check_type
    role = profile.volunteer_type.strip().lower().replace(" ", "_") or "volunteer"
    return f"{role}_volunteer_screening"


async def submit_volunteer_background_check(
    db: AsyncSession,
    identity: CurrentIdentity,
    profile_id: UUID,
    payload: VolunteerBackgroundCheckSubmitCreate,
    authz: AuthorizationService,
) -> tuple[VolunteerProfile, Person, BackgroundCheckProviderSubmissionRead, bool]:
    profile = await get_volunteer_profile(db, profile_id)
    await ensure_manage_volunteers(authz, identity, profile.organization_id)
    person = await db.get(Person, profile.person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    check_type = volunteer_background_check_type(profile, payload)
    existing_check = await db.scalar(
        select(BackgroundCheck)
        .where(BackgroundCheck.organization_id == profile.organization_id)
        .where(BackgroundCheck.person_id == profile.person_id)
        .where(BackgroundCheck.provider == payload.provider)
        .where(BackgroundCheck.check_type == check_type)
        .where(BackgroundCheck.status.in_([BackgroundCheckStatus.REQUESTED, BackgroundCheckStatus.IN_PROGRESS]))
        .order_by(BackgroundCheck.requested_at.desc())
        .limit(1)
    )
    created = False
    if existing_check is None:
        existing_check = BackgroundCheck(
            organization_id=profile.organization_id,
            person_id=profile.person_id,
            requested_by_person_id=identity.person_id,
            provider=payload.provider,
            check_type=check_type,
            status=BackgroundCheckStatus.REQUESTED,
            requested_at=datetime.now(UTC),
            notes=(
                payload.notes
                or f"Volunteer screening request for {person.display_name} ({profile.volunteer_type})."
            ),
        )
        db.add(existing_check)
        await db.flush()
        created = True
    submission = await submit_background_check_to_screening_provider(
        db,
        identity,
        existing_check.id,
        authz,
    )
    profile.background_check_status = volunteer_background_check_status(submission.check_status)
    profile.background_check_expires_on = existing_check.expires_at
    if profile.onboarding_status in {"invited", "applied"}:
        profile.onboarding_status = "screening"
    await db.commit()
    await db.refresh(profile)
    return profile, person, submission, created


def compute_match_score(profile: VolunteerProfile, opportunity: VolunteerOpportunity) -> float:
    required = set(decode_list(opportunity.required_skills_json))
    skills = set(decode_list(profile.skills_json))
    availability = set(decode_list(profile.availability_json))
    skill_score = 1.0 if not required else len(required & skills) / len(required)
    role_score = 1.0 if profile.volunteer_type == opportunity.role_type else 0.6
    availability_score = 0.8 if not availability else max(
        0.4,
        1.0 if opportunity.starts_at.strftime("%A").lower() in availability else 0.5,
    )
    readiness_score = 1.0
    if opportunity.background_check_required and profile.background_check_status not in {"cleared", "approved"}:
        readiness_score -= 0.35
    if opportunity.training_required and profile.training_status != "complete":
        readiness_score -= 0.25
    score = (skill_score * 0.4) + (availability_score * 0.25) + (role_score * 0.2) + (profile.reliability_score * 0.15)
    return round(max(0.0, min(score * readiness_score, 1.0)), 3)


def substitute_candidate_score(
    pool_member: VolunteerSubstitutePoolMember,
    profile: VolunteerProfile,
    opportunity: VolunteerOpportunity,
) -> float:
    base_score = compute_match_score(profile, opportunity)
    priority_bonus = min(max(pool_member.priority, 0), 100) / 1000
    status_bonus = 0.05 if pool_member.status == "available" else 0
    return round(min(base_score + priority_bonus + status_bonus, 1.0), 3)


async def active_assignment_count(db: AsyncSession, opportunity_id: UUID) -> int:
    return int(
        await db.scalar(
            select(func.count(VolunteerAssignment.id)).where(
                VolunteerAssignment.opportunity_id == opportunity_id,
                VolunteerAssignment.status.in_(["assigned", "confirmed", "checked_in", "completed"]),
            )
        )
        or 0
    )


async def create_volunteer_substitute_pool_member(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VolunteerSubstitutePoolMemberCreate,
    authz: AuthorizationService,
) -> VolunteerSubstitutePoolMember:
    await ensure_manage_volunteers(authz, identity, payload.organization_id)
    await ensure_volunteer_scope(db, payload.organization_id, payload.team_id)
    profile = await get_volunteer_profile(db, payload.volunteer_profile_id)
    if profile.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    existing = await db.scalar(
        select(VolunteerSubstitutePoolMember).where(
            VolunteerSubstitutePoolMember.organization_id == payload.organization_id,
            VolunteerSubstitutePoolMember.volunteer_profile_id == profile.id,
            VolunteerSubstitutePoolMember.team_id == payload.team_id,
            VolunteerSubstitutePoolMember.role_type == payload.role_type,
        )
    )
    if existing is not None:
        existing.availability_json = encode_list(payload.availability)
        existing.priority = payload.priority
        existing.max_dispatches_per_month = payload.max_dispatches_per_month
        existing.status = payload.status
        existing.notes = payload.notes
        await db.commit()
        await db.refresh(existing)
        return existing
    pool_member = VolunteerSubstitutePoolMember(
        organization_id=payload.organization_id,
        volunteer_profile_id=profile.id,
        team_id=payload.team_id,
        role_type=payload.role_type,
        availability_json=encode_list(payload.availability),
        priority=payload.priority,
        max_dispatches_per_month=payload.max_dispatches_per_month,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(pool_member)
    await db.commit()
    await db.refresh(pool_member)
    return pool_member


async def list_volunteer_substitute_pool_members(
    db: AsyncSession,
    organization_id: UUID,
) -> list[tuple[VolunteerSubstitutePoolMember, VolunteerProfile, Person]]:
    return list(
        (
            await db.execute(
                select(VolunteerSubstitutePoolMember, VolunteerProfile, Person)
                .join(VolunteerProfile, VolunteerProfile.id == VolunteerSubstitutePoolMember.volunteer_profile_id)
                .join(Person, Person.id == VolunteerProfile.person_id)
                .where(VolunteerSubstitutePoolMember.organization_id == organization_id)
                .order_by(
                    VolunteerSubstitutePoolMember.status,
                    VolunteerSubstitutePoolMember.priority.desc(),
                    Person.display_name,
                )
            )
        ).all()
    )


async def volunteer_substitute_candidates(
    db: AsyncSession,
    opportunity: VolunteerOpportunity,
) -> list[tuple[VolunteerSubstitutePoolMember, VolunteerProfile, Person, float]]:
    rows = await db.execute(
        select(VolunteerSubstitutePoolMember, VolunteerProfile, Person)
        .join(VolunteerProfile, VolunteerProfile.id == VolunteerSubstitutePoolMember.volunteer_profile_id)
        .join(Person, Person.id == VolunteerProfile.person_id)
        .where(VolunteerSubstitutePoolMember.organization_id == opportunity.organization_id)
        .where(VolunteerSubstitutePoolMember.status == "available")
        .where(VolunteerSubstitutePoolMember.role_type == opportunity.role_type)
        .where(
            or_(
                VolunteerSubstitutePoolMember.team_id.is_(None),
                VolunteerSubstitutePoolMember.team_id == opportunity.team_id,
            )
        )
    )
    candidates: list[tuple[VolunteerSubstitutePoolMember, VolunteerProfile, Person, float]] = []
    for pool_member, profile, person in rows.all():
        existing = await db.scalar(
            select(VolunteerAssignment.id)
            .join(VolunteerOpportunity, VolunteerOpportunity.id == VolunteerAssignment.opportunity_id)
            .where(
                VolunteerAssignment.volunteer_profile_id == profile.id,
                VolunteerAssignment.status.in_(["invited", "assigned", "confirmed", "checked_in"]),
                VolunteerOpportunity.starts_at < (opportunity.ends_at or opportunity.starts_at),
                or_(VolunteerOpportunity.ends_at.is_(None), VolunteerOpportunity.ends_at > opportunity.starts_at),
            )
            .limit(1)
        )
        if existing is not None:
            continue
        if opportunity.background_check_required and profile.background_check_status not in {"cleared", "approved"}:
            continue
        if opportunity.training_required and profile.training_status != "complete":
            continue
        candidates.append((pool_member, profile, person, substitute_candidate_score(pool_member, profile, opportunity)))
    return sorted(candidates, key=lambda row: (row[3], row[0].priority, row[2].display_name), reverse=True)


async def dispatch_volunteer_substitutes(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VolunteerSubstituteDispatchCreate,
    authz: AuthorizationService,
) -> VolunteerSubstituteDispatchRead:
    await ensure_manage_volunteers(authz, identity, payload.organization_id)
    opportunity = await get_volunteer_opportunity(db, payload.opportunity_id)
    if opportunity.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    assigned_count = await active_assignment_count(db, opportunity.id)
    open_slots = max(opportunity.slots_required - assigned_count, 0)
    if open_slots <= 0:
        return VolunteerSubstituteDispatchRead(
            organization_id=payload.organization_id,
            opportunity_id=opportunity.id,
            opportunity_title=opportunity.title,
            open_slots_before=0,
            candidate_count=0,
            dispatched_count=0,
            assignment_ids=[],
            message_id=None,
            recipient_count=0,
            skipped_reasons=["Opportunity is already fully staffed."],
        )
    candidates = await volunteer_substitute_candidates(db, opportunity)
    selected = candidates[: min(payload.limit, open_slots)]
    assignment_ids: list[UUID] = []
    recipient_ids: list[UUID] = []
    now = datetime.now(UTC)
    for pool_member, profile, person, match_score in selected:
        assignment = await db.scalar(
            select(VolunteerAssignment).where(
                VolunteerAssignment.opportunity_id == opportunity.id,
                VolunteerAssignment.volunteer_profile_id == profile.id,
            )
        )
        if assignment is None:
            assignment = VolunteerAssignment(
                organization_id=payload.organization_id,
                opportunity_id=opportunity.id,
                volunteer_profile_id=profile.id,
                person_id=profile.person_id,
                assigned_by_person_id=identity.person_id,
                status="invited",
                match_score=match_score,
                notes="Emergency substitute dispatch invitation.",
            )
            db.add(assignment)
            await db.flush()
        else:
            assignment.status = "invited"
            assignment.match_score = match_score
            assignment.notes = payload.message or assignment.notes
        pool_member.last_contacted_at = now
        assignment_ids.append(assignment.id)
        recipient_ids.append(person.id)
    message_id: UUID | None = None
    recipient_count = 0
    if recipient_ids:
        message = await create_message_for_recipients(
            db,
            organization_id=payload.organization_id,
            message_type=CommunicationMessageType.REMINDER,
            channel=payload.channel,
            scope_type=CommunicationScopeType.ORGANIZATION,
            scope_id=payload.organization_id,
            recipient_person_ids=recipient_ids,
            subject=f"Emergency substitute request: {opportunity.title}",
            body=payload.message
            or (
                f"{opportunity.title} needs emergency substitute volunteer coverage.\n\n"
                f"Role: {opportunity.role_type}\n"
                f"Starts: {opportunity.starts_at.isoformat()}\n"
                "Please confirm if you can cover this assignment."
            ),
            created_by_person_id=identity.person_id,
        )
        message_id = message.id
        recipient_count = int(
            await db.scalar(select(func.count(MessageRecipient.id)).where(MessageRecipient.message_id == message.id))
            or 0
        )
    await db.commit()
    return VolunteerSubstituteDispatchRead(
        organization_id=payload.organization_id,
        opportunity_id=opportunity.id,
        opportunity_title=opportunity.title,
        open_slots_before=open_slots,
        candidate_count=len(candidates),
        dispatched_count=len(assignment_ids),
        assignment_ids=assignment_ids,
        message_id=message_id,
        recipient_count=recipient_count,
        skipped_reasons=[] if selected else ["No available substitute pool members matched this opportunity."],
    )


def volunteer_coordination_scope(opportunity: VolunteerOpportunity) -> tuple[CommunicationScopeType, UUID]:
    if opportunity.event_id is not None:
        return CommunicationScopeType.EVENT, opportunity.event_id
    if opportunity.team_id is not None:
        return CommunicationScopeType.TEAM, opportunity.team_id
    return CommunicationScopeType.ORGANIZATION, opportunity.organization_id


async def send_volunteer_coordination_message(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VolunteerCoordinationMessageCreate,
    authz: AuthorizationService,
) -> VolunteerCoordinationMessageRead:
    await ensure_manage_volunteers(authz, identity, payload.organization_id)
    opportunity = await get_volunteer_opportunity(db, payload.opportunity_id)
    if opportunity.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    statuses = [status_value.strip().lower() for status_value in payload.include_statuses if status_value.strip()]
    if not statuses:
        statuses = ["assigned", "confirmed", "checked_in", "invited"]
    rows = list(
        (
            await db.execute(
                select(VolunteerAssignment, Person)
                .join(Person, Person.id == VolunteerAssignment.person_id)
                .where(VolunteerAssignment.organization_id == payload.organization_id)
                .where(VolunteerAssignment.opportunity_id == opportunity.id)
                .where(VolunteerAssignment.status.in_(statuses))
                .order_by(Person.display_name)
            )
        ).all()
    )
    assignment_ids = [assignment.id for assignment, _person in rows]
    recipient_person_ids = list(dict.fromkeys([person.id for _assignment, person in rows]))
    subject = payload.subject or f"Volunteer briefing: {opportunity.title}"
    skipped_reasons: list[str] = []
    if not recipient_person_ids:
        skipped_reasons.append("No volunteer assignments matched the selected statuses.")
        return VolunteerCoordinationMessageRead(
            organization_id=payload.organization_id,
            opportunity_id=opportunity.id,
            opportunity_title=opportunity.title,
            channel=payload.channel,
            subject=subject,
            body=payload.body,
            urgent=payload.urgent,
            eligible_assignment_count=0,
            recipient_count=0,
            assignment_ids=[],
            recipient_person_ids=[],
            message_id=None,
            skipped_reasons=skipped_reasons,
        )
    scope_type, scope_id = volunteer_coordination_scope(opportunity)
    message = await create_message_for_recipients(
        db,
        organization_id=payload.organization_id,
        message_type=CommunicationMessageType.ANNOUNCEMENT,
        channel=payload.channel,
        scope_type=scope_type,
        scope_id=scope_id,
        recipient_person_ids=recipient_person_ids,
        subject=subject,
        body=(
            f"{payload.body}\n\n"
            f"Opportunity: {opportunity.title}\n"
            f"Role: {opportunity.role_type}\n"
            f"Starts: {opportunity.starts_at.isoformat()}\n"
            f"Location: {opportunity.location or 'TBC'}"
        ),
        urgent=payload.urgent,
        quiet_hours_override=payload.urgent,
        created_by_person_id=identity.person_id,
    )
    recipient_count = int(
        await db.scalar(select(func.count(MessageRecipient.id)).where(MessageRecipient.message_id == message.id))
        or 0
    )
    return VolunteerCoordinationMessageRead(
        organization_id=payload.organization_id,
        opportunity_id=opportunity.id,
        opportunity_title=opportunity.title,
        channel=payload.channel,
        subject=message.subject,
        body=message.body,
        urgent=message.urgent,
        eligible_assignment_count=len(assignment_ids),
        recipient_count=recipient_count,
        assignment_ids=assignment_ids,
        recipient_person_ids=recipient_person_ids,
        message_id=message.id,
        skipped_reasons=skipped_reasons,
    )


async def create_public_volunteer_signup(
    db: AsyncSession,
    site: str,
    payload: PublicVolunteerSignupCreate,
) -> tuple[VolunteerAssignment, VolunteerProfile, Person, VolunteerOpportunity]:
    organization = await get_public_volunteer_organization(db, site)
    opportunity = await get_volunteer_opportunity(db, payload.opportunity_id)
    if opportunity.organization_id != organization.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    if (
        not opportunity.public_signup
        or opportunity.status != "open"
        or opportunity.starts_at < now_for_datetime_column(opportunity.starts_at)
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Opportunity is not accepting signups")

    email = payload.email.lower()
    person = await db.scalar(select(Person).where(Person.primary_email == email))
    if person is None:
        person = Person(
            display_name=payload.display_name,
            primary_email=email,
            primary_phone=payload.phone,
        )
        db.add(person)
        await db.flush()
    else:
        person.display_name = payload.display_name or person.display_name
        if payload.phone and not person.primary_phone:
            person.primary_phone = payload.phone

    profile = await db.scalar(
        select(VolunteerProfile).where(
            VolunteerProfile.organization_id == organization.id,
            VolunteerProfile.person_id == person.id,
        )
    )
    if profile is None:
        profile = VolunteerProfile(
            organization_id=organization.id,
            person_id=person.id,
            volunteer_type=opportunity.role_type,
            availability_json=encode_list(payload.availability),
            skills_json=encode_list(payload.skills),
            background_check_status="not_started",
            training_status="not_started",
            onboarding_status="applied",
            reliability_score=0.75,
            emergency_contact=payload.emergency_contact,
            notes=payload.message,
        )
        db.add(profile)
        await db.flush()
    else:
        profile.volunteer_type = profile.volunteer_type or opportunity.role_type
        if payload.availability:
            profile.availability_json = merge_encoded_lists(profile.availability_json, payload.availability)
        if payload.skills:
            profile.skills_json = merge_encoded_lists(profile.skills_json, payload.skills)
        profile.onboarding_status = "applied" if profile.onboarding_status == "invited" else profile.onboarding_status
        if payload.emergency_contact:
            profile.emergency_contact = payload.emergency_contact
        if payload.message:
            profile.notes = payload.message

    await ensure_volunteer_membership(
        db,
        organization_id=organization.id,
        person_id=person.id,
        title=f"{opportunity.role_type.replace('_', ' ').title()} Volunteer",
    )

    assignment = await db.scalar(
        select(VolunteerAssignment).where(
            VolunteerAssignment.opportunity_id == opportunity.id,
            VolunteerAssignment.volunteer_profile_id == profile.id,
        )
    )
    if assignment is None:
        assigned_count = await db.scalar(
            select(func.count(VolunteerAssignment.id)).where(
                VolunteerAssignment.opportunity_id == opportunity.id,
                VolunteerAssignment.status.in_(["assigned", "confirmed", "checked_in", "completed"]),
            )
        )
        assignment = VolunteerAssignment(
            organization_id=organization.id,
            opportunity_id=opportunity.id,
            volunteer_profile_id=profile.id,
            person_id=person.id,
            assigned_by_person_id=None,
            status="waitlisted" if int(assigned_count or 0) >= opportunity.slots_required else "applied",
            match_score=compute_match_score(profile, opportunity),
            notes=payload.message,
        )
        db.add(assignment)
    else:
        assignment.match_score = compute_match_score(profile, opportunity)
        if payload.message:
            assignment.notes = payload.message
    await db.commit()
    await db.refresh(assignment)
    await db.refresh(profile)
    await db.refresh(person)
    return assignment, profile, person, opportunity


async def create_public_volunteer_group_application(
    db: AsyncSession,
    site: str,
    payload: PublicVolunteerGroupSignupCreate,
) -> tuple[VolunteerGroupApplication, VolunteerOpportunity]:
    organization = await get_public_volunteer_organization(db, site)
    opportunity = await get_volunteer_opportunity(db, payload.opportunity_id)
    if opportunity.organization_id != organization.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    if (
        not opportunity.public_signup
        or opportunity.status != "open"
        or opportunity.starts_at < now_for_datetime_column(opportunity.starts_at)
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Opportunity is not accepting group signups")
    existing = await db.scalar(
        select(VolunteerGroupApplication).where(
            VolunteerGroupApplication.opportunity_id == opportunity.id,
            VolunteerGroupApplication.coordinator_email == payload.coordinator_email.lower(),
            VolunteerGroupApplication.company_name == payload.company_name,
        )
    )
    if existing is not None:
        existing.coordinator_name = payload.coordinator_name
        existing.coordinator_phone = payload.coordinator_phone
        existing.group_size = payload.group_size
        existing.requested_slots = payload.requested_slots
        existing.skills_json = merge_encoded_lists(existing.skills_json, payload.skills)
        existing.availability_json = merge_encoded_lists(existing.availability_json, payload.availability)
        existing.message = payload.message
        existing.source_url = payload.source_url
        if existing.status in {"declined", "cancelled"}:
            existing.status = "pending"
            existing.approved_slots = 0
            existing.reviewed_by_person_id = None
            existing.reviewed_at = None
            existing.review_notes = None
        await db.commit()
        await db.refresh(existing)
        return existing, opportunity
    application = VolunteerGroupApplication(
        organization_id=organization.id,
        opportunity_id=opportunity.id,
        company_name=payload.company_name,
        coordinator_name=payload.coordinator_name,
        coordinator_email=payload.coordinator_email.lower(),
        coordinator_phone=payload.coordinator_phone,
        group_size=payload.group_size,
        requested_slots=payload.requested_slots,
        approved_slots=0,
        skills_json=encode_list(payload.skills),
        availability_json=encode_list(payload.availability),
        message=payload.message,
        source_url=payload.source_url,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application, opportunity


async def create_volunteer_assignment(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VolunteerAssignmentCreate,
    authz: AuthorizationService,
) -> VolunteerAssignment:
    await ensure_manage_volunteers(authz, identity, payload.organization_id)
    opportunity = await get_volunteer_opportunity(db, payload.opportunity_id)
    profile = await get_volunteer_profile(db, payload.volunteer_profile_id)
    if opportunity.organization_id != payload.organization_id or profile.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    overlapping = await db.scalar(
        select(VolunteerAssignment)
        .join(VolunteerOpportunity, VolunteerOpportunity.id == VolunteerAssignment.opportunity_id)
        .where(
            VolunteerAssignment.volunteer_profile_id == profile.id,
            VolunteerAssignment.status.in_(["assigned", "confirmed", "checked_in"]),
            VolunteerOpportunity.id != opportunity.id,
            VolunteerOpportunity.starts_at < (opportunity.ends_at or opportunity.starts_at),
            or_(VolunteerOpportunity.ends_at.is_(None), VolunteerOpportunity.ends_at > opportunity.starts_at),
        )
    )
    if overlapping is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Volunteer has a scheduling conflict")
    assigned_count = await db.scalar(
        select(func.count(VolunteerAssignment.id)).where(
            VolunteerAssignment.opportunity_id == opportunity.id,
            VolunteerAssignment.status.in_(["assigned", "confirmed", "checked_in", "completed"]),
        )
    )
    if int(assigned_count or 0) >= opportunity.slots_required:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Opportunity is already fully staffed")
    assignment = VolunteerAssignment(
        organization_id=payload.organization_id,
        opportunity_id=opportunity.id,
        volunteer_profile_id=profile.id,
        person_id=profile.person_id,
        assigned_by_person_id=identity.person_id,
        status=payload.status,
        match_score=compute_match_score(profile, opportunity),
        notes=payload.notes,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def update_volunteer_assignment(
    db: AsyncSession,
    identity: CurrentIdentity,
    assignment_id: UUID,
    payload: VolunteerAssignmentUpdate,
    authz: AuthorizationService,
) -> VolunteerAssignment:
    assignment = await db.get(VolunteerAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    await ensure_manage_volunteers(authz, identity, assignment.organization_id)
    if payload.status is not None:
        assignment.status = payload.status
        if payload.status == "confirmed" and assignment.confirmed_at is None:
            assignment.confirmed_at = datetime.now(UTC)
    if payload.checked_in_at is not None:
        assignment.checked_in_at = payload.checked_in_at
        assignment.status = "checked_in"
    if payload.checked_out_at is not None:
        assignment.checked_out_at = payload.checked_out_at
        assignment.status = "completed"
    if payload.hours_logged is not None:
        assignment.hours_logged = payload.hours_logged
    elif assignment.checked_in_at and assignment.checked_out_at and assignment.hours_logged == 0:
        assignment.hours_logged = round((assignment.checked_out_at - assignment.checked_in_at).total_seconds() / 3600, 2)
    if payload.notes is not None:
        assignment.notes = payload.notes
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def list_volunteer_assignments(db: AsyncSession, organization_id: UUID) -> list[tuple[VolunteerAssignment, VolunteerProfile, Person, VolunteerOpportunity]]:
    return list(
        (
            await db.execute(
                select(VolunteerAssignment, VolunteerProfile, Person, VolunteerOpportunity)
                .join(VolunteerProfile, VolunteerProfile.id == VolunteerAssignment.volunteer_profile_id)
                .join(Person, Person.id == VolunteerAssignment.person_id)
                .join(VolunteerOpportunity, VolunteerOpportunity.id == VolunteerAssignment.opportunity_id)
                .where(VolunteerAssignment.organization_id == organization_id)
                .order_by(VolunteerOpportunity.starts_at.desc(), Person.display_name)
            )
        ).all()
    )


async def list_volunteer_group_applications(
    db: AsyncSession,
    organization_id: UUID,
) -> list[tuple[VolunteerGroupApplication, VolunteerOpportunity]]:
    return list(
        (
            await db.execute(
                select(VolunteerGroupApplication, VolunteerOpportunity)
                .join(VolunteerOpportunity, VolunteerOpportunity.id == VolunteerGroupApplication.opportunity_id)
                .where(VolunteerGroupApplication.organization_id == organization_id)
                .order_by(VolunteerGroupApplication.created_at.desc())
            )
        ).all()
    )


async def update_volunteer_group_application(
    db: AsyncSession,
    identity: CurrentIdentity,
    application_id: UUID,
    payload: VolunteerGroupApplicationUpdate,
    authz: AuthorizationService,
) -> VolunteerGroupApplication:
    application = await db.get(VolunteerGroupApplication, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group application not found")
    await ensure_manage_volunteers(authz, identity, application.organization_id)
    if payload.approved_slots is not None and payload.approved_slots > application.requested_slots:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Approved slots exceed request")
    if payload.status is not None:
        application.status = payload.status
    if payload.approved_slots is not None:
        application.approved_slots = payload.approved_slots
        if payload.approved_slots > 0 and application.status == "pending":
            application.status = "approved"
    if payload.review_notes is not None:
        application.review_notes = payload.review_notes
    if payload.status is not None or payload.approved_slots is not None or payload.review_notes is not None:
        application.reviewed_by_person_id = identity.person_id
        application.reviewed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(application)
    return application


async def create_volunteer_training_record(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VolunteerTrainingRecordCreate,
    authz: AuthorizationService,
) -> VolunteerTrainingRecord:
    await ensure_manage_volunteers(authz, identity, payload.organization_id)
    profile = await get_volunteer_profile(db, payload.volunteer_profile_id)
    if profile.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    record = VolunteerTrainingRecord(
        organization_id=payload.organization_id,
        volunteer_profile_id=profile.id,
        module_name=payload.module_name,
        role_type=payload.role_type or profile.volunteer_type,
        required=payload.required,
        status=payload.status,
        assigned_at=datetime.now(UTC),
        completed_at=payload.completed_at,
        expires_on=payload.expires_on,
        score=payload.score,
        certificate_url=payload.certificate_url,
    )
    if payload.completed_at is not None or payload.status == "complete":
        profile.training_status = "complete"
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def list_volunteer_training_records(db: AsyncSession, organization_id: UUID) -> list[VolunteerTrainingRecord]:
    return list(
        (
            await db.scalars(
                select(VolunteerTrainingRecord)
                .where(VolunteerTrainingRecord.organization_id == organization_id)
                .order_by(VolunteerTrainingRecord.assigned_at.desc())
            )
        ).all()
    )


async def create_volunteer_obligation(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VolunteerObligationCreate,
    authz: AuthorizationService,
) -> VolunteerObligation:
    await ensure_manage_volunteers(authz, identity, payload.organization_id)
    await ensure_volunteer_scope(db, payload.organization_id, payload.team_id)
    person = await get_or_create_person_by_contact(
        db,
        person_id=payload.person_id,
        email=payload.email,
        display_name=payload.display_name,
    )
    obligation = await db.scalar(
        select(VolunteerObligation).where(
            VolunteerObligation.organization_id == payload.organization_id,
            VolunteerObligation.person_id == person.id,
            VolunteerObligation.season_label == payload.season_label,
            VolunteerObligation.category == payload.category,
        )
    )
    if obligation is None:
        obligation = VolunteerObligation(
            organization_id=payload.organization_id,
            person_id=person.id,
            team_id=payload.team_id,
            season_label=payload.season_label,
            category=payload.category,
            required_hours=payload.required_hours,
            completed_hours=payload.completed_hours,
            waived_hours=payload.waived_hours,
            due_on=payload.due_on,
            notes=payload.notes,
        )
        db.add(obligation)
    else:
        obligation.team_id = payload.team_id
        obligation.required_hours = payload.required_hours
        obligation.completed_hours = payload.completed_hours
        obligation.waived_hours = payload.waived_hours
        obligation.due_on = payload.due_on
        obligation.notes = payload.notes
    remaining = obligation.required_hours - obligation.completed_hours - obligation.waived_hours
    obligation.status = "complete" if remaining <= 0 else "open"
    await db.commit()
    await db.refresh(obligation)
    return obligation


async def update_volunteer_obligation(
    db: AsyncSession,
    identity: CurrentIdentity,
    obligation_id: UUID,
    payload: VolunteerObligationUpdate,
    authz: AuthorizationService,
) -> VolunteerObligation:
    obligation = await db.get(VolunteerObligation, obligation_id)
    if obligation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volunteer obligation not found")
    await ensure_manage_volunteers(authz, identity, obligation.organization_id)
    if payload.completed_hours is not None:
        obligation.completed_hours = payload.completed_hours
    if payload.waived_hours is not None:
        obligation.waived_hours = payload.waived_hours
    if payload.notes is not None:
        obligation.notes = payload.notes
    if payload.status is not None:
        obligation.status = payload.status
    else:
        remaining = obligation.required_hours - obligation.completed_hours - obligation.waived_hours
        obligation.status = "complete" if remaining <= 0 else "open"
    await db.commit()
    await db.refresh(obligation)
    return obligation


async def list_volunteer_obligations(
    db: AsyncSession,
    organization_id: UUID,
) -> list[tuple[VolunteerObligation, Person]]:
    return list(
        (
            await db.execute(
                select(VolunteerObligation, Person)
                .join(Person, Person.id == VolunteerObligation.person_id)
                .where(VolunteerObligation.organization_id == organization_id)
                .order_by(VolunteerObligation.season_label.desc(), Person.display_name)
            )
        ).all()
    )


async def organization_volunteer_manager_person_ids(db: AsyncSession, organization_id: UUID) -> list[UUID]:
    manager_roles = {
        MembershipRole.OWNER,
        MembershipRole.ADMIN,
        MembershipRole.COACH,
        MembershipRole.STAFF,
    }
    return list(
        dict.fromkeys(
            (
                await db.scalars(
                    select(Membership.subject_id)
                    .where(Membership.organization_id == organization_id)
                    .where(Membership.subject_type == MemberSubjectType.PERSON)
                    .where(Membership.status == "active")
                    .where(Membership.role.in_(manager_roles))
                    .order_by(Membership.created_at.asc())
                )
            ).all()
        )
    )


async def recent_volunteer_reminder_exists(
    db: AsyncSession,
    *,
    organization_id: UUID,
    marker: str,
    repeat_after_hours: int,
) -> bool:
    if repeat_after_hours <= 0:
        return False
    cutoff = datetime.now(UTC) - timedelta(hours=repeat_after_hours)
    return (
        await db.scalar(
            select(func.count(CommunicationMessage.id))
            .where(CommunicationMessage.organization_id == organization_id)
            .where(CommunicationMessage.message_type == CommunicationMessageType.REMINDER)
            .where(CommunicationMessage.body.contains(marker))
            .where(CommunicationMessage.created_at >= cutoff)
        )
        or 0
    ) > 0


def volunteer_reminder_body(
    *,
    title: str,
    action: str,
    details: list[str],
    marker: str,
) -> str:
    detail_lines = "\n".join(f"- {detail}" for detail in details if detail)
    return (
        f"{title}\n\n"
        f"{action}\n\n"
        f"{detail_lines}\n\n"
        "This reminder was generated by AfroLete volunteer operations.\n"
        f"[{marker}]"
    )


async def create_volunteer_reminder_message(
    db: AsyncSession,
    *,
    organization_id: UUID,
    channel: CommunicationChannel,
    scope_type: CommunicationScopeType,
    scope_id: UUID,
    recipient_person_ids: list[UUID],
    subject: str,
    body: str,
) -> tuple[UUID, int]:
    message = await create_message_for_recipients(
        db,
        organization_id=organization_id,
        message_type=CommunicationMessageType.REMINDER,
        channel=channel,
        scope_type=scope_type,
        scope_id=scope_id,
        recipient_person_ids=recipient_person_ids,
        subject=subject,
        body=body,
        urgent=False,
        quiet_hours_override=False,
        created_by_person_id=None,
    )
    recipient_count = int(
        await db.scalar(select(func.count(MessageRecipient.id)).where(MessageRecipient.message_id == message.id))
        or 0
    )
    return message.id, recipient_count


async def run_volunteer_reminders(
    db: AsyncSession,
    payload: VolunteerReminderRunCreate,
) -> VolunteerReminderRunRead:
    await ensure_organization(db, payload.organization_id)
    now = datetime.now(UTC)
    due_by = now + timedelta(days=payload.due_within_days)
    due_date = due_by.date()
    manager_person_ids = await organization_volunteer_manager_person_ids(db, payload.organization_id)
    opportunities = await list_volunteer_opportunities(db, payload.organization_id)
    obligations = await list_volunteer_obligations(db, payload.organization_id)
    training_records = await list_volunteer_training_records(db, payload.organization_id)
    profile_rows = await list_volunteer_profiles(db, payload.organization_id)
    profile_person_ids = {profile.id: profile.person_id for profile, _person in profile_rows}

    message_ids: list[UUID] = []
    recipient_count = 0
    skipped_count = 0
    failed_count = 0
    coverage_gap_count = 0
    obligation_count = 0
    training_count = 0
    eligible_count = 0

    for opportunity, assigned_count in opportunities:
        open_slots = max(opportunity.slots_required - assigned_count, 0)
        if opportunity.status != "open" or open_slots <= 0 or as_utc_datetime(opportunity.starts_at) > due_by:
            continue
        eligible_count += 1
        coverage_gap_count += 1
        marker = f"volunteer-reminder:coverage:{opportunity.id}"
        if not manager_person_ids or payload.dry_run:
            skipped_count += 1
            continue
        if await recent_volunteer_reminder_exists(
            db,
            organization_id=payload.organization_id,
            marker=marker,
            repeat_after_hours=payload.repeat_after_hours,
        ):
            skipped_count += 1
            continue
        try:
            message_id, count = await create_volunteer_reminder_message(
                db,
                organization_id=payload.organization_id,
                channel=payload.channel,
                scope_type=CommunicationScopeType.ORGANIZATION,
                scope_id=payload.organization_id,
                recipient_person_ids=manager_person_ids,
                subject=f"Volunteer coverage needed: {opportunity.title}",
                body=volunteer_reminder_body(
                    title=f"{opportunity.title} still needs {open_slots} volunteer slot(s).",
                    action="Review the staffing plan and assign or recruit volunteers before the activity.",
                    details=[
                        f"Role: {opportunity.role_type}",
                        f"Starts: {opportunity.starts_at.isoformat()}",
                        f"Priority: {opportunity.priority}",
                    ],
                    marker=marker,
                ),
            )
            message_ids.append(message_id)
            recipient_count += count
        except Exception:
            failed_count += 1
            await db.rollback()
        if len(message_ids) >= payload.limit:
            break

    for obligation, person in obligations:
        remaining_hours = max(obligation.required_hours - obligation.completed_hours - obligation.waived_hours, 0)
        if obligation.status == "complete" or remaining_hours <= 0 or not obligation.due_on:
            continue
        if obligation.due_on > due_date:
            continue
        eligible_count += 1
        obligation_count += 1
        marker = f"volunteer-reminder:obligation:{obligation.id}"
        if payload.dry_run:
            skipped_count += 1
            continue
        if await recent_volunteer_reminder_exists(
            db,
            organization_id=payload.organization_id,
            marker=marker,
            repeat_after_hours=payload.repeat_after_hours,
        ):
            skipped_count += 1
            continue
        try:
            message_id, count = await create_volunteer_reminder_message(
                db,
                organization_id=payload.organization_id,
                channel=payload.channel,
                scope_type=CommunicationScopeType.PERSON,
                scope_id=person.id,
                recipient_person_ids=[person.id],
                subject=f"Volunteer hours due: {obligation.season_label}",
                body=volunteer_reminder_body(
                    title=f"{person.display_name}, {remaining_hours:g} volunteer hour(s) remain.",
                    action="Please sign up for an open shift or contact the team manager if this is incorrect.",
                    details=[
                        f"Season: {obligation.season_label}",
                        f"Due date: {obligation.due_on.isoformat()}",
                        f"Completed: {obligation.completed_hours:g} hour(s)",
                    ],
                    marker=marker,
                ),
            )
            message_ids.append(message_id)
            recipient_count += count
        except Exception:
            failed_count += 1
            await db.rollback()
        if len(message_ids) >= payload.limit:
            break

    for record in training_records:
        person_id = profile_person_ids.get(record.volunteer_profile_id)
        due_for_training = record.required and record.status != "complete"
        expiring = record.required and record.expires_on is not None and record.expires_on <= due_date
        if person_id is None or not (due_for_training or expiring):
            continue
        eligible_count += 1
        training_count += 1
        marker = f"volunteer-reminder:training:{record.id}"
        if payload.dry_run:
            skipped_count += 1
            continue
        if await recent_volunteer_reminder_exists(
            db,
            organization_id=payload.organization_id,
            marker=marker,
            repeat_after_hours=payload.repeat_after_hours,
        ):
            skipped_count += 1
            continue
        try:
            message_id, count = await create_volunteer_reminder_message(
                db,
                organization_id=payload.organization_id,
                channel=payload.channel,
                scope_type=CommunicationScopeType.PERSON,
                scope_id=person_id,
                recipient_person_ids=[person_id],
                subject=f"Volunteer training reminder: {record.module_name}",
                body=volunteer_reminder_body(
                    title=f"{record.module_name} requires volunteer attention.",
                    action="Complete or renew the training before your next volunteer assignment.",
                    details=[
                        f"Status: {record.status}",
                        f"Expires: {record.expires_on.isoformat() if record.expires_on else 'not set'}",
                    ],
                    marker=marker,
                ),
            )
            message_ids.append(message_id)
            recipient_count += count
        except Exception:
            failed_count += 1
            await db.rollback()
        if len(message_ids) >= payload.limit:
            break

    return VolunteerReminderRunRead(
        organization_id=payload.organization_id,
        eligible_count=eligible_count,
        reminded_count=len(message_ids),
        skipped_count=skipped_count,
        failed_count=failed_count,
        dry_run=payload.dry_run,
        coverage_gap_count=coverage_gap_count,
        obligation_count=obligation_count,
        training_count=training_count,
        recipient_count=recipient_count,
        message_ids=message_ids,
    )


async def run_volunteer_reminder_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    *,
    channel: CommunicationChannel = CommunicationChannel.EMAIL,
    due_within_days: int = 7,
    repeat_after_hours: int = 24,
    limit: int = 50,
    dry_run: bool = False,
) -> VolunteerReminderRunRead:
    if organization_id is not None:
        return await run_volunteer_reminders(
            db,
            VolunteerReminderRunCreate(
                organization_id=organization_id,
                channel=channel,
                due_within_days=due_within_days,
                repeat_after_hours=repeat_after_hours,
                limit=limit,
                dry_run=dry_run,
            ),
        )
    opportunity_org_ids = (
        await db.scalars(
            select(VolunteerOpportunity.organization_id)
            .where(VolunteerOpportunity.status == "open")
            .group_by(VolunteerOpportunity.organization_id)
            .order_by(func.min(VolunteerOpportunity.starts_at).asc())
            .limit(limit)
        )
    ).all()
    obligation_org_ids = (
        await db.scalars(
            select(VolunteerObligation.organization_id)
            .where(VolunteerObligation.status != "complete")
            .group_by(VolunteerObligation.organization_id)
            .limit(limit)
        )
    ).all()
    training_org_ids = (
        await db.scalars(
            select(VolunteerTrainingRecord.organization_id)
            .where(VolunteerTrainingRecord.required.is_(True))
            .where(VolunteerTrainingRecord.status != "complete")
            .group_by(VolunteerTrainingRecord.organization_id)
            .limit(limit)
        )
    ).all()
    organization_ids = list(dict.fromkeys([*opportunity_org_ids, *obligation_org_ids, *training_org_ids]))[:limit]
    aggregate = VolunteerReminderRunRead(
        organization_id=UUID(int=0),
        eligible_count=0,
        reminded_count=0,
        skipped_count=0,
        failed_count=0,
        dry_run=dry_run,
        coverage_gap_count=0,
        obligation_count=0,
        training_count=0,
        recipient_count=0,
        message_ids=[],
    )
    for selected_organization_id in organization_ids:
        result = await run_volunteer_reminders(
            db,
            VolunteerReminderRunCreate(
                organization_id=selected_organization_id,
                channel=channel,
                due_within_days=due_within_days,
                repeat_after_hours=repeat_after_hours,
                limit=limit,
                dry_run=dry_run,
            ),
        )
        aggregate.eligible_count += result.eligible_count
        aggregate.reminded_count += result.reminded_count
        aggregate.skipped_count += result.skipped_count
        aggregate.failed_count += result.failed_count
        aggregate.coverage_gap_count += result.coverage_gap_count
        aggregate.obligation_count += result.obligation_count
        aggregate.training_count += result.training_count
        aggregate.recipient_count += result.recipient_count
        aggregate.message_ids.extend(result.message_ids)
    return aggregate


async def create_volunteer_recognition(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VolunteerRecognitionCreate,
    authz: AuthorizationService,
) -> VolunteerRecognition:
    await ensure_manage_volunteers(authz, identity, payload.organization_id)
    profile = await get_volunteer_profile(db, payload.volunteer_profile_id)
    if profile.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    recognition = VolunteerRecognition(
        organization_id=payload.organization_id,
        volunteer_profile_id=profile.id,
        recognition_type=payload.recognition_type,
        badge_code=payload.badge_code,
        title=payload.title,
        points=payload.points,
        awarded_on=payload.awarded_on or date.today(),
        source_summary=payload.source_summary,
    )
    db.add(recognition)
    await db.commit()
    await db.refresh(recognition)
    return recognition


async def list_volunteer_recognitions(db: AsyncSession, organization_id: UUID) -> list[VolunteerRecognition]:
    return list(
        (
            await db.scalars(
                select(VolunteerRecognition)
                .where(VolunteerRecognition.organization_id == organization_id)
                .order_by(VolunteerRecognition.awarded_on.desc(), VolunteerRecognition.created_at.desc())
            )
        ).all()
    )


async def volunteer_summary(db: AsyncSession, organization_id: UUID) -> dict[str, object]:
    profiles = list(
        (
            await db.scalars(
                select(VolunteerProfile).where(VolunteerProfile.organization_id == organization_id)
            )
        ).all()
    )
    opportunities = await list_volunteer_opportunities(db, organization_id)
    assignments = list(
        (
            await db.scalars(
                select(VolunteerAssignment).where(VolunteerAssignment.organization_id == organization_id)
            )
        ).all()
    )
    group_applications = list(
        (
            await db.scalars(
                select(VolunteerGroupApplication).where(VolunteerGroupApplication.organization_id == organization_id)
            )
        ).all()
    )
    need_requests = await list_volunteer_need_requests(db, organization_id)
    obligation_rows = await list_volunteer_obligations(db, organization_id)
    training = await list_volunteer_training_records(db, organization_id)
    total_slots = sum(opportunity.slots_required for opportunity, _ in opportunities if opportunity.status == "open")
    assigned_slots = sum(count for opportunity, count in opportunities if opportunity.status == "open")
    required_training = [record for record in training if record.required]
    completed_required = [record for record in required_training if record.status == "complete" or record.completed_at]
    skill_counts = Counter(skill for profile in profiles for skill in decode_list(profile.skills_json))
    shortage_roles = [
        opportunity.role_type
        for opportunity, count in opportunities
        if opportunity.status == "open" and count < opportunity.slots_required
    ]
    return {
        "organization_id": organization_id,
        "active_volunteers": sum(1 for profile in profiles if profile.status == "active"),
        "open_opportunities": sum(1 for opportunity, _ in opportunities if opportunity.status == "open"),
        "open_slots": max(total_slots - assigned_slots, 0),
        "assigned_shifts": sum(1 for assignment in assignments if assignment.status in {"assigned", "confirmed", "checked_in"}),
        "confirmed_shifts": sum(1 for assignment in assignments if assignment.status in {"confirmed", "checked_in"}),
        "pending_group_applications": sum(1 for application in group_applications if application.status == "pending"),
        "approved_group_slots": sum(
            application.approved_slots for application in group_applications if application.status == "approved"
        ),
        "open_need_requests": sum(1 for request in need_requests if request.status in {"requested", "open"}),
        "obligation_deficit_hours": round(
            sum(
                max(obligation.required_hours - obligation.completed_hours - obligation.waived_hours, 0)
                for obligation, _person in obligation_rows
                if obligation.status != "complete"
            ),
            2,
        ),
        "completed_hours": round(sum(assignment.hours_logged for assignment in assignments), 2),
        "training_compliance_percent": round((len(completed_required) / len(required_training) * 100) if required_training else 100, 2),
        "coverage_percent": round((assigned_slots / total_slots * 100) if total_slots else 100, 2),
        "top_skills": [skill for skill, _ in skill_counts.most_common(6)],
        "shortage_roles": list(dict.fromkeys(shortage_roles))[:6],
    }
