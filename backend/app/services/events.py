from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AttendanceStatus, ParticipationClearanceStatus
from app.models.event import AttendanceRecord, Event
from app.models.identity import Person
from app.models.organization import Organization
from app.models.team import AthleteProfile, Team, TeamRosterEntry
from app.schemas.event import EventCreate, AttendanceRecordUpsert
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship
from app.services.safeguarding import clearance_for_event


PARTICIPATION_STATUSES = {AttendanceStatus.CONFIRMED, AttendanceStatus.PRESENT}


async def can_manage_event_scope(
    authz: AuthorizationService,
    organization_id: UUID,
    identity: CurrentIdentity,
) -> bool:
    return await authz.check(
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


async def ensure_manage_event_scope(
    authz: AuthorizationService,
    organization_id: UUID,
    identity: CurrentIdentity,
) -> None:
    if not await can_manage_event_scope(authz, organization_id, identity):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def create_event(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: EventCreate,
    authz: AuthorizationService,
) -> Event:
    organization = await db.get(Organization, payload.organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    await ensure_manage_event_scope(authz, payload.organization_id, identity)
    if payload.team_id is not None:
        team = await db.get(Team, payload.team_id)
        if team is None or team.organization_id != payload.organization_id:
            raise HTTPException(status_code=404, detail="Team not found for organization")

    event = Event(
        organization_id=payload.organization_id,
        team_id=payload.team_id,
        event_type=payload.event_type,
        title=payload.title,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        timezone=payload.timezone,
        venue_name=payload.venue_name,
        notes=payload.notes,
    )
    db.add(event)
    await db.flush()
    await authz.touch(
        Relationship(
            resource_type="event",
            resource_id=str(event.id),
            relation="organizer",
            subject_type="user",
            subject_id=str(identity.user_id),
        )
    )
    await authz.touch(
        Relationship(
            resource_type="event",
            resource_id=str(event.id),
            relation="parent_org",
            subject_type="organization",
            subject_id=str(payload.organization_id),
        )
    )
    if payload.team_id is not None:
        await authz.touch(
            Relationship(
                resource_type="event",
                resource_id=str(event.id),
                relation="team",
                subject_type="team",
                subject_id=str(payload.team_id),
            )
        )
    await db.commit()
    await db.refresh(event)
    return event


async def list_events(
    db: AsyncSession,
    organization_id: UUID,
    team_id: UUID | None = None,
) -> list[Event]:
    query = select(Event).where(Event.organization_id == organization_id)
    if team_id is not None:
        query = query.where(Event.team_id == team_id)
    return list((await db.scalars(query.order_by(Event.starts_at))).all())


async def get_event(db: AsyncSession, event_id: UUID) -> Event:
    event = await db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


async def record_attendance(
    db: AsyncSession,
    identity: CurrentIdentity,
    event_id: UUID,
    payload: AttendanceRecordUpsert,
    authz: AuthorizationService,
) -> tuple[AttendanceRecord, ParticipationClearanceStatus | None]:
    event = await get_event(db, event_id)
    await ensure_manage_event_scope(authz, event.organization_id, identity)
    person = await db.get(Person, payload.person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    clearance_status: ParticipationClearanceStatus | None = None
    guardian_consent_id: UUID | None = None
    if payload.status in PARTICIPATION_STATUSES:
        clearance_status, _, _, guardian_consent_id, reason = await clearance_for_event(
            db,
            event_id,
            payload.person_id,
        )
        if clearance_status != ParticipationClearanceStatus.CLEARED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "clearance_status": clearance_status.value,
                    "reason": reason,
                },
            )

    existing = await db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.event_id == event_id,
            AttendanceRecord.person_id == payload.person_id,
        )
    )
    if existing is not None:
        existing.status = payload.status
        existing.recorded_by_person_id = identity.person_id
        existing.guardian_consent_id = guardian_consent_id or existing.guardian_consent_id
        existing.note = payload.note
        await db.commit()
        await db.refresh(existing)
        return existing, clearance_status

    attendance = AttendanceRecord(
        event_id=event_id,
        person_id=payload.person_id,
        status=payload.status,
        recorded_by_person_id=identity.person_id,
        guardian_consent_id=guardian_consent_id,
        note=payload.note,
    )
    db.add(attendance)
    await authz.touch(
        Relationship(
            resource_type="event",
            resource_id=str(event_id),
            relation="participant",
            subject_type="person",
            subject_id=str(payload.person_id),
        )
    )
    await db.commit()
    await db.refresh(attendance)
    return attendance, clearance_status


async def list_attendance(db: AsyncSession, event_id: UUID) -> list[AttendanceRecord]:
    await get_event(db, event_id)
    return list(
        (
            await db.scalars(
                select(AttendanceRecord)
                .where(AttendanceRecord.event_id == event_id)
                .order_by(AttendanceRecord.created_at)
            )
        ).all()
    )


async def seed_attendance_from_team_roster(
    db: AsyncSession,
    identity: CurrentIdentity,
    event_id: UUID,
    authz: AuthorizationService,
) -> tuple[int, int]:
    event = await get_event(db, event_id)
    await ensure_manage_event_scope(authz, event.organization_id, identity)
    if event.team_id is None:
        raise HTTPException(status_code=422, detail="Event is not attached to a team")

    rows = (
        await db.execute(
            select(AthleteProfile.person_id)
            .join(TeamRosterEntry, TeamRosterEntry.athlete_profile_id == AthleteProfile.id)
            .where(TeamRosterEntry.team_id == event.team_id)
        )
    ).all()

    created = 0
    existing = 0
    for (person_id,) in rows:
        attendance = await db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.event_id == event_id,
                AttendanceRecord.person_id == person_id,
            )
        )
        if attendance is not None:
            existing += 1
            continue
        db.add(
            AttendanceRecord(
                event_id=event_id,
                person_id=person_id,
                status=AttendanceStatus.INVITED,
                recorded_by_person_id=identity.person_id,
            )
        )
        created += 1

    await db.commit()
    return created, existing
