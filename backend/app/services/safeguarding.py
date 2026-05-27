from datetime import UTC, date, datetime
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    AttendanceStatus,
    ConsentCaptureChannel,
    ConsentRequestStatus,
    ConsentScopeType,
    ConsentStatus,
    ParticipationClearanceStatus,
)
from app.models.event import ActivityConsent, AttendanceRecord, ConsentRequest, Event
from app.models.identity import Person
from app.models.team import AthleteProfile, GuardianRelationship, TeamRosterEntry
from app.schemas.safeguarding import (
    ActivityConsentCreate,
    ConsentRequestCreate,
    FamilyAthleteSummaryRead,
    FamilyConsentRequestRead,
    FamilyConsentResponseCreate,
    FamilyEventSummaryRead,
    FamilyEventRsvpCreate,
    GuardianRelationshipCreate,
    KnownChannelConsentCapture,
    TokenConsentCapture,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def is_minor_on(person: Person, on_date: date) -> bool | None:
    if person.date_of_birth is None:
        return None
    birthday_passed = (on_date.month, on_date.day) >= (
        person.date_of_birth.month,
        person.date_of_birth.day,
    )
    age = on_date.year - person.date_of_birth.year - (0 if birthday_passed else 1)
    return age < 18


def normalized_scope_id(
    organization_id: UUID,
    scope_type: ConsentScopeType,
    scope_id: UUID | None,
) -> UUID:
    if scope_type == ConsentScopeType.ORGANIZATION:
        return organization_id
    if scope_id is None:
        raise HTTPException(status_code=422, detail="Team and event consents require scope_id")
    return scope_id


async def ensure_org_manage(
    authz: AuthorizationService,
    organization_id: UUID,
    identity: CurrentIdentity,
) -> None:
    can_manage = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not can_manage:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def create_guardian_relationship(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: GuardianRelationshipCreate,
    authz: AuthorizationService,
) -> GuardianRelationship:
    await ensure_org_manage(authz, payload.organization_id, identity)

    athlete = await db.get(Person, payload.athlete_person_id)
    if athlete is None:
        raise HTTPException(status_code=404, detail="Athlete not found")

    guardian = None
    if payload.guardian_person_id is not None:
        guardian = await db.get(Person, payload.guardian_person_id)
        if guardian is None:
            raise HTTPException(status_code=404, detail="Guardian not found")
    elif payload.guardian_email is not None or payload.guardian_phone is not None:
        if payload.guardian_email is not None:
            guardian = await db.scalar(
                select(Person).where(Person.primary_email == payload.guardian_email)
            )
        if guardian is None and payload.guardian_phone is not None:
            guardian = await db.scalar(
                select(Person).where(Person.primary_phone == payload.guardian_phone)
            )
        if guardian is None:
            guardian = Person(
                display_name=payload.guardian_display_name
                or payload.guardian_email
                or payload.guardian_phone
                or "Guardian",
                primary_email=payload.guardian_email,
                primary_phone=payload.guardian_phone,
            )
            db.add(guardian)
            await db.flush()
        elif payload.guardian_phone and not guardian.primary_phone:
            guardian.primary_phone = payload.guardian_phone

    if guardian is None:
        raise HTTPException(status_code=422, detail="Missing guardian")

    existing = await db.scalar(
        select(GuardianRelationship).where(
            GuardianRelationship.athlete_person_id == payload.athlete_person_id,
            GuardianRelationship.guardian_person_id == guardian.id,
        )
    )
    if existing is not None:
        return existing

    relationship = GuardianRelationship(
        athlete_person_id=payload.athlete_person_id,
        guardian_person_id=guardian.id,
        relationship_kind=payload.relationship_kind,
        relationship=payload.relationship or payload.relationship_kind.value.replace("_", " "),
        can_sign_consent=payload.can_sign_consent,
        can_view_medical=payload.can_view_medical,
        emergency_contact=payload.emergency_contact,
        can_pick_up=payload.can_pick_up,
        is_primary=payload.is_primary,
        notes=payload.notes,
    )
    db.add(relationship)
    await authz.touch(
        Relationship(
            resource_type="athlete_profile",
            resource_id=str(payload.athlete_person_id),
            relation="guardian",
            subject_type="person",
            subject_id=str(guardian.id),
        )
    )
    await db.commit()
    await db.refresh(relationship)
    return relationship


async def list_guardians_for_athlete(
    db: AsyncSession,
    athlete_person_id: UUID,
) -> list[GuardianRelationship]:
    return list(
        (
            await db.scalars(
                select(GuardianRelationship)
                .where(GuardianRelationship.athlete_person_id == athlete_person_id)
                .order_by(GuardianRelationship.is_primary.desc())
            )
        ).all()
    )


async def list_my_family(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> list[FamilyAthleteSummaryRead]:
    rows = (
        await db.execute(
            select(GuardianRelationship, Person)
            .join(Person, Person.id == GuardianRelationship.athlete_person_id)
            .join(AthleteProfile, AthleteProfile.person_id == GuardianRelationship.athlete_person_id)
            .where(AthleteProfile.organization_id == organization_id)
            .where(GuardianRelationship.guardian_person_id == identity.person_id)
            .order_by(GuardianRelationship.is_primary.desc(), Person.display_name)
        )
    ).all()

    summaries: list[FamilyAthleteSummaryRead] = []
    for relationship, athlete in rows:
        pending_count = await db.scalar(
            select(func.count(ConsentRequest.id))
            .where(ConsentRequest.organization_id == organization_id)
            .where(ConsentRequest.athlete_person_id == relationship.athlete_person_id)
            .where(ConsentRequest.guardian_person_id == identity.person_id)
            .where(ConsentRequest.status == ConsentRequestStatus.PENDING)
        )
        latest_consent = await db.scalar(
            select(ActivityConsent)
            .where(ActivityConsent.organization_id == organization_id)
            .where(ActivityConsent.athlete_person_id == relationship.athlete_person_id)
            .where(ActivityConsent.guardian_person_id == identity.person_id)
            .order_by(ActivityConsent.created_at.desc())
            .limit(1)
        )
        summaries.append(
            FamilyAthleteSummaryRead(
                athlete_person_id=relationship.athlete_person_id,
                athlete_name=athlete.display_name,
                relationship=relationship.relationship,
                relationship_kind=relationship.relationship_kind,
                can_sign_consent=relationship.can_sign_consent,
                can_view_medical=relationship.can_view_medical,
                emergency_contact=relationship.emergency_contact,
                pending_consent_requests=int(pending_count or 0),
                latest_consent_status=latest_consent.status if latest_consent else None,
                latest_consent_scope_type=latest_consent.scope_type if latest_consent else None,
                latest_consent_signed_at=latest_consent.signed_at if latest_consent else None,
            )
        )
    return summaries


async def list_my_family_events(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    limit: int = 50,
) -> list[FamilyEventSummaryRead]:
    rows = (
        await db.execute(
            select(GuardianRelationship, Person)
            .join(Person, Person.id == GuardianRelationship.athlete_person_id)
            .join(AthleteProfile, AthleteProfile.person_id == GuardianRelationship.athlete_person_id)
            .where(AthleteProfile.organization_id == organization_id)
            .where(GuardianRelationship.guardian_person_id == identity.person_id)
            .order_by(Person.display_name)
        )
    ).all()

    summaries: list[FamilyEventSummaryRead] = []
    now = utc_now()
    for relationship, athlete in rows:
        events_by_id: dict[UUID, Event] = {}
        attendance_by_event: dict[UUID, AttendanceRecord] = {}
        attendance_rows = (
            await db.execute(
                select(AttendanceRecord, Event)
                .join(Event, Event.id == AttendanceRecord.event_id)
                .where(Event.organization_id == organization_id)
                .where(Event.starts_at >= now)
                .where(AttendanceRecord.person_id == relationship.athlete_person_id)
                .order_by(Event.starts_at)
            )
        ).all()
        for attendance, event in attendance_rows:
            events_by_id[event.id] = event
            attendance_by_event[event.id] = attendance

        team_events = (
            await db.scalars(
                select(Event)
                .join(TeamRosterEntry, TeamRosterEntry.team_id == Event.team_id)
                .join(AthleteProfile, AthleteProfile.id == TeamRosterEntry.athlete_profile_id)
                .where(Event.organization_id == organization_id)
                .where(Event.starts_at >= now)
                .where(AthleteProfile.person_id == relationship.athlete_person_id)
                .where(AthleteProfile.organization_id == organization_id)
                .order_by(Event.starts_at)
            )
        ).all()
        for event in team_events:
            events_by_id[event.id] = event

        for event in events_by_id.values():
            clearance, _, guardian_required, consent_id, reason = await clearance_for_event(
                db,
                event.id,
                relationship.athlete_person_id,
            )
            attendance = attendance_by_event.get(event.id)
            summaries.append(
                FamilyEventSummaryRead(
                    athlete_person_id=relationship.athlete_person_id,
                    athlete_name=athlete.display_name,
                    event_id=event.id,
                    team_id=event.team_id,
                    event_type=event.event_type,
                    title=event.title,
                    starts_at=event.starts_at,
                    ends_at=event.ends_at,
                    timezone=event.timezone,
                    venue_name=event.venue_name,
                    attendance_status=attendance.status if attendance else None,
                    clearance_status=clearance,
                    guardian_required=guardian_required,
                    consent_id=consent_id,
                    reason=reason,
                )
            )

    return sorted(summaries, key=lambda item: item.starts_at)[:limit]


async def respond_to_family_event(
    db: AsyncSession,
    identity: CurrentIdentity,
    event_id: UUID,
    athlete_person_id: UUID,
    payload: FamilyEventRsvpCreate,
) -> FamilyEventSummaryRead:
    relationship = await db.scalar(
        select(GuardianRelationship)
        .join(AthleteProfile, AthleteProfile.person_id == GuardianRelationship.athlete_person_id)
        .where(AthleteProfile.organization_id == payload.organization_id)
        .where(GuardianRelationship.guardian_person_id == identity.person_id)
        .where(GuardianRelationship.athlete_person_id == athlete_person_id)
    )
    if relationship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family relationship not found")

    event = await db.get(Event, event_id)
    if event is None or event.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if not await family_event_applies_to_athlete(db, event, athlete_person_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family event not found")

    clearance, _, _, _, reason = await clearance_for_event(db, event_id, athlete_person_id)
    if payload.status == AttendanceStatus.CONFIRMED and clearance != ParticipationClearanceStatus.CLEARED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"clearance_status": clearance.value, "reason": reason},
        )

    attendance = await db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.event_id == event_id,
            AttendanceRecord.person_id == athlete_person_id,
        )
    )
    if attendance is None:
        attendance = AttendanceRecord(
            event_id=event_id,
            person_id=athlete_person_id,
            status=payload.status,
            recorded_by_person_id=identity.person_id,
            note=payload.note,
        )
        db.add(attendance)
    else:
        attendance.status = payload.status
        attendance.recorded_by_person_id = identity.person_id
        attendance.note = payload.note
    await db.commit()
    await db.refresh(attendance)
    return await family_event_summary(db, relationship, event, attendance)


async def list_my_family_consent_requests(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> list[FamilyConsentRequestRead]:
    rows = (
        await db.execute(
            select(ConsentRequest, Person)
            .join(Person, Person.id == ConsentRequest.athlete_person_id)
            .join(
                GuardianRelationship,
                and_(
                    GuardianRelationship.athlete_person_id == ConsentRequest.athlete_person_id,
                    GuardianRelationship.guardian_person_id == ConsentRequest.guardian_person_id,
                ),
            )
            .where(ConsentRequest.organization_id == organization_id)
            .where(ConsentRequest.guardian_person_id == identity.person_id)
            .where(ConsentRequest.status == ConsentRequestStatus.PENDING)
            .where(GuardianRelationship.can_sign_consent.is_(True))
            .order_by(ConsentRequest.sent_at.desc())
        )
    ).all()
    now = utc_now()
    pending: list[FamilyConsentRequestRead] = []
    expired = False
    for request, athlete in rows:
        if request.expires_at is not None and request.expires_at < now:
            request.status = ConsentRequestStatus.EXPIRED
            expired = True
            continue
        pending.append(family_consent_request_read(request, athlete.display_name))
    if expired:
        await db.commit()
    return pending


async def respond_to_family_consent_request(
    db: AsyncSession,
    identity: CurrentIdentity,
    request_id: UUID,
    payload: FamilyConsentResponseCreate,
) -> ActivityConsent:
    request = await db.get(ConsentRequest, request_id)
    if request is None or request.guardian_person_id != identity.person_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent request not found")
    if request.status != ConsentRequestStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Consent request already used")
    relationship = await db.scalar(
        select(GuardianRelationship).where(
            GuardianRelationship.athlete_person_id == request.athlete_person_id,
            GuardianRelationship.guardian_person_id == identity.person_id,
            GuardianRelationship.can_sign_consent.is_(True),
        )
    )
    if relationship is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    now = utc_now()
    if request.expires_at is not None and request.expires_at < now:
        request.status = ConsentRequestStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Consent request expired")

    consent = await upsert_activity_consent(
        db,
        organization_id=request.organization_id,
        athlete_person_id=request.athlete_person_id,
        guardian_person_id=request.guardian_person_id,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        status_value=payload.status,
        capture_channel=ConsentCaptureChannel.WEB_LINK,
        identity=identity,
        source_request_id=request.id,
        consent_text=f"Guardian responded {payload.status.value} in the family portal.",
        notes=payload.notes,
    )
    request.status = ConsentRequestStatus.FULFILLED
    request.fulfilled_at = now
    request.response_payload = payload.notes
    await db.commit()
    await db.refresh(consent)
    return consent


def family_consent_request_read(
    request: ConsentRequest,
    athlete_name: str,
) -> FamilyConsentRequestRead:
    return FamilyConsentRequestRead(
        id=request.id,
        organization_id=request.organization_id,
        athlete_person_id=request.athlete_person_id,
        athlete_name=athlete_name,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        channel=request.channel,
        destination=request.destination,
        status=request.status,
        expires_at=request.expires_at,
        sent_at=request.sent_at,
        notes=request.notes,
    )


async def family_event_applies_to_athlete(
    db: AsyncSession,
    event: Event,
    athlete_person_id: UUID,
) -> bool:
    attendance = await db.scalar(
        select(AttendanceRecord.id).where(
            AttendanceRecord.event_id == event.id,
            AttendanceRecord.person_id == athlete_person_id,
        )
    )
    if attendance is not None:
        return True
    if event.team_id is None:
        return False
    roster_entry = await db.scalar(
        select(TeamRosterEntry.id)
        .join(AthleteProfile, AthleteProfile.id == TeamRosterEntry.athlete_profile_id)
        .where(TeamRosterEntry.team_id == event.team_id)
        .where(AthleteProfile.person_id == athlete_person_id)
        .where(AthleteProfile.organization_id == event.organization_id)
    )
    return roster_entry is not None


async def family_event_summary(
    db: AsyncSession,
    relationship: GuardianRelationship,
    event: Event,
    attendance: AttendanceRecord | None = None,
) -> FamilyEventSummaryRead:
    athlete = await db.get(Person, relationship.athlete_person_id)
    if athlete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    clearance, _, guardian_required, consent_id, reason = await clearance_for_event(
        db,
        event.id,
        relationship.athlete_person_id,
    )
    return FamilyEventSummaryRead(
        athlete_person_id=relationship.athlete_person_id,
        athlete_name=athlete.display_name,
        event_id=event.id,
        team_id=event.team_id,
        event_type=event.event_type,
        title=event.title,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        timezone=event.timezone,
        venue_name=event.venue_name,
        attendance_status=attendance.status if attendance else None,
        clearance_status=clearance,
        guardian_required=guardian_required,
        consent_id=consent_id,
        reason=reason,
    )


async def consent_destination(db: AsyncSession, payload: ConsentRequestCreate) -> str:
    if payload.destination is not None:
        return payload.destination
    guardian = await db.get(Person, payload.guardian_person_id)
    if guardian is None:
        raise HTTPException(status_code=404, detail="Guardian not found")
    if payload.channel == ConsentCaptureChannel.EMAIL:
        if guardian.primary_email:
            return guardian.primary_email
    elif guardian.primary_phone:
        return guardian.primary_phone
    raise HTTPException(status_code=422, detail="No known destination for consent channel")


async def create_consent_request(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: ConsentRequestCreate,
    authz: AuthorizationService,
) -> tuple[ConsentRequest, str]:
    await ensure_org_manage(authz, payload.organization_id, identity)
    relationship = await db.scalar(
        select(GuardianRelationship).where(
            GuardianRelationship.athlete_person_id == payload.athlete_person_id,
            GuardianRelationship.guardian_person_id == payload.guardian_person_id,
            GuardianRelationship.can_sign_consent.is_(True),
        )
    )
    if relationship is None:
        raise HTTPException(status_code=422, detail="Guardian cannot sign consent for athlete")

    token = token_urlsafe(32)
    request = ConsentRequest(
        organization_id=payload.organization_id,
        athlete_person_id=payload.athlete_person_id,
        guardian_person_id=payload.guardian_person_id,
        scope_type=payload.scope_type,
        scope_id=normalized_scope_id(
            payload.organization_id,
            payload.scope_type,
            payload.scope_id,
        ),
        channel=payload.channel,
        destination=await consent_destination(db, payload),
        token_hash=hash_token(token),
        status=ConsentRequestStatus.PENDING,
        expires_at=payload.expires_at,
        sent_at=utc_now(),
        external_message_id=payload.external_message_id,
        notes=payload.notes,
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request, token


async def upsert_activity_consent(
    db: AsyncSession,
    *,
    organization_id: UUID,
    athlete_person_id: UUID,
    guardian_person_id: UUID,
    scope_type: ConsentScopeType,
    scope_id: UUID | None,
    status_value: ConsentStatus,
    capture_channel: ConsentCaptureChannel,
    identity: CurrentIdentity | None = None,
    source_request_id: UUID | None = None,
    consent_text: str | None = None,
    response_payload: str | None = None,
    notes: str | None = None,
) -> ActivityConsent:
    scope_id = normalized_scope_id(organization_id, scope_type, scope_id)
    existing = await db.scalar(
        select(ActivityConsent).where(
            ActivityConsent.athlete_person_id == athlete_person_id,
            ActivityConsent.guardian_person_id == guardian_person_id,
            ActivityConsent.scope_type == scope_type,
            ActivityConsent.scope_id == scope_id,
        )
    )
    signed_at = utc_now() if status_value == ConsentStatus.GRANTED else None
    revoked_at = utc_now() if status_value == ConsentStatus.REVOKED else None
    if existing is not None:
        existing.status = status_value
        existing.capture_channel = capture_channel
        existing.source_request_id = source_request_id
        existing.signed_at = signed_at or existing.signed_at
        existing.revoked_at = revoked_at
        existing.consent_text = consent_text or existing.consent_text
        existing.notes = notes or response_payload or existing.notes
        await db.commit()
        await db.refresh(existing)
        return existing

    consent = ActivityConsent(
        organization_id=organization_id,
        athlete_person_id=athlete_person_id,
        guardian_person_id=guardian_person_id,
        scope_type=scope_type,
        scope_id=scope_id,
        status=status_value,
        source_request_id=source_request_id,
        capture_channel=capture_channel,
        signed_at=signed_at,
        revoked_at=revoked_at,
        recorded_by_person_id=identity.person_id if identity is not None else None,
        consent_text=consent_text,
        notes=notes or response_payload,
    )
    db.add(consent)
    await db.commit()
    await db.refresh(consent)
    return consent


async def create_activity_consent(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: ActivityConsentCreate,
    authz: AuthorizationService,
) -> ActivityConsent:
    await ensure_org_manage(authz, payload.organization_id, identity)
    return await upsert_activity_consent(
        db,
        organization_id=payload.organization_id,
        athlete_person_id=payload.athlete_person_id,
        guardian_person_id=payload.guardian_person_id,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        status_value=payload.status,
        capture_channel=ConsentCaptureChannel.MANUAL,
        identity=identity,
        consent_text=payload.consent_text,
        notes=payload.notes,
    )


async def capture_consent_by_token(
    db: AsyncSession,
    payload: TokenConsentCapture,
) -> ActivityConsent:
    request = await db.scalar(
        select(ConsentRequest).where(ConsentRequest.token_hash == hash_token(payload.token))
    )
    if request is None:
        raise HTTPException(status_code=404, detail="Consent request not found")
    if request.status != ConsentRequestStatus.PENDING:
        raise HTTPException(status_code=409, detail="Consent request already used")
    now = utc_now()
    if request.expires_at is not None and request.expires_at < now:
        request.status = ConsentRequestStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=410, detail="Consent request expired")

    consent = await upsert_activity_consent(
        db,
        organization_id=request.organization_id,
        athlete_person_id=request.athlete_person_id,
        guardian_person_id=request.guardian_person_id,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        status_value=payload.status,
        capture_channel=request.channel,
        source_request_id=request.id,
        consent_text=payload.consent_text,
        response_payload=payload.response_payload,
        notes=payload.notes,
    )
    request.status = ConsentRequestStatus.FULFILLED
    request.fulfilled_at = now
    request.response_payload = payload.response_payload
    await db.commit()
    await db.refresh(consent)
    return consent


def channel_matches_guardian(channel: ConsentCaptureChannel, guardian: Person, source: str) -> bool:
    normalized = source.strip().lower()
    if channel == ConsentCaptureChannel.EMAIL:
        return bool(guardian.primary_email and guardian.primary_email.lower() == normalized)
    if channel in {
        ConsentCaptureChannel.SMS,
        ConsentCaptureChannel.WHATSAPP,
        ConsentCaptureChannel.TELEGRAM,
    }:
        return bool(guardian.primary_phone and guardian.primary_phone.strip() == source.strip())
    return False


async def capture_consent_by_known_channel(
    db: AsyncSession,
    payload: KnownChannelConsentCapture,
) -> ActivityConsent:
    relationships = (
        await db.execute(
            select(GuardianRelationship, Person)
            .join(Person, Person.id == GuardianRelationship.guardian_person_id)
            .where(GuardianRelationship.athlete_person_id == payload.athlete_person_id)
            .where(GuardianRelationship.can_sign_consent.is_(True))
        )
    ).all()
    for relationship, guardian in relationships:
        if channel_matches_guardian(payload.channel, guardian, payload.source_address):
            pending_request = await db.scalar(
                select(ConsentRequest)
                .where(ConsentRequest.athlete_person_id == payload.athlete_person_id)
                .where(ConsentRequest.guardian_person_id == relationship.guardian_person_id)
                .where(ConsentRequest.scope_type == payload.scope_type)
                .where(
                    ConsentRequest.scope_id
                    == normalized_scope_id(
                        payload.organization_id,
                        payload.scope_type,
                        payload.scope_id,
                    )
                )
                .where(ConsentRequest.channel == payload.channel)
                .where(ConsentRequest.status == ConsentRequestStatus.PENDING)
                .order_by(ConsentRequest.sent_at.desc())
            )
            consent = await upsert_activity_consent(
                db,
                organization_id=payload.organization_id,
                athlete_person_id=payload.athlete_person_id,
                guardian_person_id=relationship.guardian_person_id,
                scope_type=payload.scope_type,
                scope_id=normalized_scope_id(
                    payload.organization_id,
                    payload.scope_type,
                    payload.scope_id,
                ),
                status_value=payload.status,
                capture_channel=payload.channel,
                source_request_id=pending_request.id if pending_request is not None else None,
                response_payload=payload.response_payload,
                notes=payload.notes,
            )
            if pending_request is not None:
                pending_request.status = ConsentRequestStatus.FULFILLED
                pending_request.fulfilled_at = utc_now()
                pending_request.response_payload = payload.response_payload
                await db.commit()
            return consent
    raise HTTPException(status_code=404, detail="No matching guardian contact found")


async def clearance_for_event(
    db: AsyncSession,
    event_id: UUID,
    athlete_person_id: UUID,
) -> tuple[ParticipationClearanceStatus, bool, bool, UUID | None, str]:
    event = await db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    athlete = await db.get(Person, athlete_person_id)
    if athlete is None:
        raise HTTPException(status_code=404, detail="Athlete not found")

    minor = is_minor_on(athlete, event.starts_at.date())
    if minor is False:
        return (
            ParticipationClearanceStatus.CLEARED,
            False,
            False,
            None,
            "Athlete is not a minor on the event date.",
        )

    guardians = await list_guardians_for_athlete(db, athlete_person_id)
    signing_guardians = [guardian for guardian in guardians if guardian.can_sign_consent]
    if not signing_guardians:
        return (
            ParticipationClearanceStatus.NO_GUARDIAN,
            minor is True,
            True,
            None,
            "No guardian with consent authority is recorded.",
        )

    today = utc_now().date()
    applicable_scope = or_(
        and_(
            ActivityConsent.scope_type == ConsentScopeType.ORGANIZATION,
            ActivityConsent.scope_id == event.organization_id,
        ),
        and_(
            ActivityConsent.scope_type == ConsentScopeType.EVENT,
            ActivityConsent.scope_id == event_id,
        ),
        and_(
            ActivityConsent.scope_type == ConsentScopeType.TEAM,
            ActivityConsent.scope_id == event.team_id,
        ),
    )
    latest_consent = await db.scalar(
        select(ActivityConsent)
        .where(ActivityConsent.athlete_person_id == athlete_person_id)
        .where(applicable_scope)
        .order_by(ActivityConsent.updated_at.desc())
    )
    if latest_consent is None:
        return (
            ParticipationClearanceStatus.MINOR_REQUIRES_CONSENT,
            minor is True,
            True,
            None,
            "Guardian consent is required before participation.",
        )
    if latest_consent.status == ConsentStatus.DENIED:
        return (
            ParticipationClearanceStatus.CONSENT_DENIED,
            minor is True,
            True,
            latest_consent.id,
            "Guardian consent was denied.",
        )
    if latest_consent.status == ConsentStatus.EXPIRED:
        return (
            ParticipationClearanceStatus.CONSENT_EXPIRED,
            minor is True,
            True,
            latest_consent.id,
            "Guardian consent is marked expired.",
        )
    if latest_consent.status != ConsentStatus.GRANTED:
        return (
            ParticipationClearanceStatus.MINOR_REQUIRES_CONSENT,
            minor is True,
            True,
            latest_consent.id,
            "Guardian consent has not been granted.",
        )
    if latest_consent.valid_until is not None and latest_consent.valid_until < today:
        return (
            ParticipationClearanceStatus.CONSENT_EXPIRED,
            minor is True,
            True,
            latest_consent.id,
            "Guardian consent exists but has expired.",
        )
    return (
        ParticipationClearanceStatus.CLEARED,
        minor is True,
        True,
        latest_consent.id,
        "Guardian consent is recorded.",
    )
