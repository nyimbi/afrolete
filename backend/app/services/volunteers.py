import json
from collections import Counter
from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.enums import MemberSubjectType, MembershipRole
from app.models.team import Team
from app.models.volunteer import (
    VolunteerAssignment,
    VolunteerOpportunity,
    VolunteerProfile,
    VolunteerRecognition,
    VolunteerTrainingRecord,
)
from app.schemas.volunteer import (
    VolunteerAssignmentCreate,
    VolunteerAssignmentUpdate,
    VolunteerOpportunityCreate,
    VolunteerProfileCreate,
    VolunteerRecognitionCreate,
    VolunteerTrainingRecordCreate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService


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


async def ensure_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
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
    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == payload.organization_id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == person.id,
            Membership.role == MembershipRole.VOLUNTEER,
        )
    )
    if membership is None:
        db.add(
            Membership(
                organization_id=payload.organization_id,
                subject_type=MemberSubjectType.PERSON,
                subject_id=person.id,
                role=MembershipRole.VOLUNTEER,
                title=f"{payload.volunteer_type.replace('_', ' ').title()} Volunteer",
            )
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
        "completed_hours": round(sum(assignment.hours_logged for assignment in assignments), 2),
        "training_compliance_percent": round((len(completed_required) / len(required_training) * 100) if required_training else 100, 2),
        "coverage_percent": round((assigned_slots / total_slots * 100) if total_slots else 100, 2),
        "top_skills": [skill for skill, _ in skill_counts.most_common(6)],
        "shortage_roles": list(dict.fromkeys(shortage_roles))[:6],
    }
