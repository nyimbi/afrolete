from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.safeguarding import (
    ActivityConsentCreate,
    ActivityConsentRead,
    ConsentRequestCreate,
    ConsentRequestRead,
    FamilyAthleteSummaryRead,
    FamilyConsentRequestRead,
    FamilyConsentResponseCreate,
    FamilyEventSummaryRead,
    FamilyEventRsvpCreate,
    GuardianRelationshipCreate,
    GuardianRelationshipRead,
    KnownChannelConsentCapture,
    ParticipationClearanceRead,
    TokenConsentCapture,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.safeguarding import (
    capture_consent_by_known_channel,
    capture_consent_by_token,
    clearance_for_event,
    create_activity_consent,
    create_consent_request,
    create_guardian_relationship,
    list_guardians_for_athlete,
    list_my_family_consent_requests,
    list_my_family,
    list_my_family_events,
    respond_to_family_consent_request,
    respond_to_family_event,
)

router = APIRouter(prefix="/safeguarding", tags=["safeguarding"])


def to_guardian_read(relationship) -> GuardianRelationshipRead:
    return GuardianRelationshipRead(
        id=relationship.id,
        athlete_person_id=relationship.athlete_person_id,
        guardian_person_id=relationship.guardian_person_id,
        relationship_kind=relationship.relationship_kind,
        relationship=relationship.relationship,
        can_sign_consent=relationship.can_sign_consent,
        can_view_medical=relationship.can_view_medical,
        emergency_contact=relationship.emergency_contact,
        can_pick_up=relationship.can_pick_up,
        is_primary=relationship.is_primary,
        notes=relationship.notes,
    )


def to_consent_read(consent) -> ActivityConsentRead:
    return ActivityConsentRead(
        id=consent.id,
        organization_id=consent.organization_id,
        athlete_person_id=consent.athlete_person_id,
        guardian_person_id=consent.guardian_person_id,
        scope_type=consent.scope_type,
        scope_id=consent.scope_id,
        status=consent.status,
        source_request_id=consent.source_request_id,
        capture_channel=consent.capture_channel,
        valid_from=consent.valid_from,
        valid_until=consent.valid_until,
        signed_at=consent.signed_at,
        revoked_at=consent.revoked_at,
        recorded_by_person_id=consent.recorded_by_person_id,
        consent_text=consent.consent_text,
        notes=consent.notes,
    )


def to_request_read(request, one_time_token: str | None = None) -> ConsentRequestRead:
    return ConsentRequestRead(
        id=request.id,
        organization_id=request.organization_id,
        athlete_person_id=request.athlete_person_id,
        guardian_person_id=request.guardian_person_id,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        channel=request.channel,
        destination=request.destination,
        status=request.status,
        expires_at=request.expires_at,
        sent_at=request.sent_at,
        fulfilled_at=request.fulfilled_at,
        external_message_id=request.external_message_id,
        one_time_token=one_time_token,
    )


@router.post("/guardians", response_model=GuardianRelationshipRead, status_code=201)
async def create_guardian_route(
    payload: GuardianRelationshipCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GuardianRelationshipRead:
    return to_guardian_read(await create_guardian_relationship(db, identity, payload, authz))


@router.get(
    "/athletes/{athlete_person_id}/guardians", response_model=list[GuardianRelationshipRead]
)
async def list_guardians_route(
    athlete_person_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[GuardianRelationshipRead]:
    return [
        to_guardian_read(relationship)
        for relationship in await list_guardians_for_athlete(db, athlete_person_id)
    ]


@router.get("/my-family", response_model=list[FamilyAthleteSummaryRead])
async def list_my_family_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[FamilyAthleteSummaryRead]:
    return await list_my_family(db, identity, organization_id)


@router.get("/my-family/events", response_model=list[FamilyEventSummaryRead])
async def list_my_family_events_route(
    organization_id: UUID = Query(),
    limit: int = Query(default=50, ge=1, le=200),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[FamilyEventSummaryRead]:
    return await list_my_family_events(db, identity, organization_id, limit)


@router.get("/my-family/consent-requests", response_model=list[FamilyConsentRequestRead])
async def list_my_family_consent_requests_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[FamilyConsentRequestRead]:
    return await list_my_family_consent_requests(db, identity, organization_id)


@router.post("/my-family/consent-requests/{request_id}/response", response_model=ActivityConsentRead)
async def respond_to_family_consent_request_route(
    request_id: UUID,
    payload: FamilyConsentResponseCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> ActivityConsentRead:
    return to_consent_read(await respond_to_family_consent_request(db, identity, request_id, payload))


@router.post(
    "/my-family/events/{event_id}/athletes/{athlete_person_id}/rsvp",
    response_model=FamilyEventSummaryRead,
)
async def respond_to_family_event_route(
    event_id: UUID,
    athlete_person_id: UUID,
    payload: FamilyEventRsvpCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> FamilyEventSummaryRead:
    return await respond_to_family_event(db, identity, event_id, athlete_person_id, payload)


@router.post("/consent-requests", response_model=ConsentRequestRead, status_code=201)
async def create_consent_request_route(
    payload: ConsentRequestCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ConsentRequestRead:
    request, token = await create_consent_request(db, identity, payload, authz)
    return to_request_read(request, token)


@router.post("/consents", response_model=ActivityConsentRead, status_code=201)
async def create_activity_consent_route(
    payload: ActivityConsentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ActivityConsentRead:
    return to_consent_read(await create_activity_consent(db, identity, payload, authz))


@router.post("/consents/by-token", response_model=ActivityConsentRead)
async def capture_consent_by_token_route(
    payload: TokenConsentCapture,
    db: AsyncSession = Depends(get_db),
) -> ActivityConsentRead:
    return to_consent_read(await capture_consent_by_token(db, payload))


@router.post("/consents/by-known-channel", response_model=ActivityConsentRead)
async def capture_consent_by_known_channel_route(
    payload: KnownChannelConsentCapture,
    db: AsyncSession = Depends(get_db),
) -> ActivityConsentRead:
    return to_consent_read(await capture_consent_by_known_channel(db, payload))


@router.get(
    "/events/{event_id}/athletes/{athlete_person_id}/clearance",
    response_model=ParticipationClearanceRead,
)
async def participation_clearance_route(
    event_id: UUID,
    athlete_person_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ParticipationClearanceRead:
    clearance, is_minor, guardian_required, consent_id, reason = await clearance_for_event(
        db,
        event_id,
        athlete_person_id,
    )
    return ParticipationClearanceRead(
        event_id=event_id,
        athlete_person_id=athlete_person_id,
        is_minor=is_minor,
        guardian_required=guardian_required,
        status=clearance,
        consent_id=consent_id,
        reason=reason,
    )
