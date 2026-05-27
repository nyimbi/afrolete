import hmac
import io
import time
from base64 import b64decode, urlsafe_b64encode
from binascii import Error as Base64Error
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from re import sub
from urllib.parse import quote
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.communication import CommunicationMessage, MessageRecipient
from app.models.commercial import FinanceInvoice
from app.models.enums import (
    AttendanceStatus,
    CommunicationChannel,
    ConsentRequestStatus,
    ConsentScopeType,
    CommunicationMessageType,
    CommunicationScopeType,
    MedicalClearanceStatus,
    ParticipationClearanceStatus,
    TravelPlanStatus,
    TravelRiskLevel,
    WeatherAlertLevel,
    WeatherDecision,
)
from app.models.event import (
    AttendanceRecord,
    ConsentRequest,
    Event,
    EventTravelApproval,
    EventTravelCarpoolRide,
    EventTravelChecklistItem,
    EventTravelDevice,
    EventTravelExpense,
    EventTravelGeofenceZone,
    EventTravelLocationUpdate,
    EventTravelPlan,
    EventWeatherAssessment,
)
from app.models.identity import Person
from app.models.organization import Organization
from app.models.team import AthleteProfile, GuardianRelationship, Team, TeamRosterEntry
from app.schemas.communication import CommunicationMessageCreate
from app.schemas.safeguarding import ConsentRequestCreate
from app.schemas.event import (
    EventCreate,
    EventTravelConsentBatchRead,
    EventTravelConsentReminderCreate,
    EventTravelConsentReminderRead,
    EventTravelConsentReminderRunCreate,
    EventTravelConsentReminderRunPlanRead,
    EventTravelConsentReminderRunRead,
    EventTravelConsentRequestCreate,
    EventTravelConsentRequestItemRead,
    EventTravelApprovalCreate,
    EventTravelApprovalRead,
    EventTravelApprovalRoutingCreate,
    EventTravelApprovalRoutingRead,
    EventTravelApprovalUpdate,
    EventTravelCarpoolAutoMatchCreate,
    EventTravelCarpoolAutoMatchPairRead,
    EventTravelCarpoolAutoMatchRead,
    EventTravelCarpoolRideCreate,
    EventTravelCarpoolRideRead,
    EventTravelCarpoolRideUpdate,
    EventTravelChecklistEvidenceUploadCreate,
    EventTravelChecklistEvidenceUploadRead,
    EventTravelChecklistItemRead,
    EventTravelChecklistItemUpdate,
    EventTravelChecklistSeedCreate,
    EventTravelDeviceCreate,
    EventTravelDeviceLocationIngestCreate,
    EventTravelDeviceLocationIngestRead,
    EventTravelDeviceRead,
    EventTravelDeviceUpdate,
    EventTravelExpenseCreate,
    EventTravelExpenseRead,
    EventTravelExpenseUpdate,
    EventTravelFeeCheckoutBatchRead,
    EventTravelFeeCheckoutCreate,
    EventTravelFeeCheckoutItemRead,
    EventTravelFeeInvoiceBatchRead,
    EventTravelFeeInvoiceCreate,
    EventTravelFeeInvoiceItemRead,
    EventTravelGeofenceCheckCreate,
    EventTravelGeofenceCheckRead,
    EventTravelGeofenceZoneCreate,
    EventTravelGeofenceZoneRead,
    EventTravelGeofenceZoneUpdate,
    EventTravelLocationUpdateCreate,
    EventTravelLocationUpdateRead,
    EventTravelManifestExportCreate,
    EventTravelManifestExportRead,
    EventTravelManifestOfflineLinkCreate,
    EventTravelManifestOfflineLinkRead,
    EventTravelManifestParticipantRead,
    EventTravelManifestRead,
    EventTravelPlanCreate,
    EventTravelPlanUpdate,
    EventTravelReadinessRead,
    EventTravelReceiptUploadCreate,
    EventTravelReceiptUploadRead,
    EventTravelRouteOptimizationCreate,
    EventTravelRouteOptimizationRead,
    EventTravelRouteStopRead,
    EventWeatherAlertCreate,
    EventWeatherAssessmentCreate,
    AttendanceRecordUpsert,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship
from app.services.communications import create_message
from app.services.safeguarding import (
    create_consent_request,
    clearance_for_event,
    is_minor_on,
    medical_clearance_for_event,
)
from app.services.storage.objects import get_object, put_object


PARTICIPATION_STATUSES = {AttendanceStatus.CONFIRMED, AttendanceStatus.PRESENT}
DEFAULT_TRAVEL_CHECKLIST_ITEMS = [
    "Vehicle exterior and tire inspection complete",
    "Seatbelts, first-aid kit, and emergency equipment checked",
    "Driver license, insurance, and certification verified",
    "Passenger count matches approved manifest",
    "Emergency contacts and medical access plan available",
    "Departure and arrival communication plan confirmed",
]
AttendanceResult = tuple[
    AttendanceRecord,
    ParticipationClearanceStatus | None,
    MedicalClearanceStatus | None,
    UUID | None,
    str | None,
]


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


async def ensure_optional_person(db: AsyncSession, person_id: UUID | None, detail: str) -> None:
    if person_id is not None and await db.get(Person, person_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


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


async def create_weather_assessment(
    db: AsyncSession,
    identity: CurrentIdentity,
    event_id: UUID,
    payload: EventWeatherAssessmentCreate,
    authz: AuthorizationService,
) -> EventWeatherAssessment:
    event = await get_event(db, event_id)
    await ensure_manage_event_scope(authz, event.organization_id, identity)
    alert_level, decision, actions = classify_weather_risk(payload)
    assessment = EventWeatherAssessment(
        organization_id=event.organization_id,
        event_id=event.id,
        source=payload.source,
        observed_at=payload.observed_at,
        temperature_c=payload.temperature_c,
        heat_index_c=payload.heat_index_c,
        wbgt_c=payload.wbgt_c,
        humidity_percent=payload.humidity_percent,
        aqi=payload.aqi,
        lightning_distance_km=payload.lightning_distance_km,
        wind_speed_kph=payload.wind_speed_kph,
        wind_gust_kph=payload.wind_gust_kph,
        precipitation_mm_per_hr=payload.precipitation_mm_per_hr,
        alert_level=alert_level,
        decision=decision,
        recommended_actions=actions,
        notes=payload.notes,
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    return assessment


async def list_weather_assessments(db: AsyncSession, event_id: UUID) -> list[EventWeatherAssessment]:
    await get_event(db, event_id)
    rows = await db.scalars(
        select(EventWeatherAssessment)
        .where(EventWeatherAssessment.event_id == event_id)
        .order_by(EventWeatherAssessment.observed_at.desc())
    )
    return list(rows.all())


async def dispatch_weather_assessment_alert(
    db: AsyncSession,
    identity: CurrentIdentity,
    event_id: UUID,
    assessment_id: UUID,
    payload: EventWeatherAlertCreate,
    authz: AuthorizationService,
) -> tuple[CommunicationMessage, int]:
    event = await get_event(db, event_id)
    await ensure_manage_event_scope(authz, event.organization_id, identity)
    assessment = await db.get(EventWeatherAssessment, assessment_id)
    if assessment is None or assessment.event_id != event.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weather assessment not found")
    message = await create_message(
        db,
        identity,
        CommunicationMessageCreate(
            organization_id=event.organization_id,
            message_type=CommunicationMessageType.ALERT,
            channel=payload.channel,
            scope_type=CommunicationScopeType.EVENT,
            scope_id=event.id,
            subject=payload.subject or weather_alert_subject(event, assessment),
            body=payload.body or weather_alert_body(event, assessment),
            urgent=True,
            quiet_hours_override=True,
            copy_guardians_for_minors=payload.copy_guardians_for_minors,
        ),
        authz,
    )
    recipient_count = await db.scalar(
        select(func.count(MessageRecipient.id)).where(MessageRecipient.message_id == message.id)
    )
    return message, int(recipient_count or 0)


async def create_travel_plan(
    db: AsyncSession,
    identity: CurrentIdentity,
    event_id: UUID,
    payload: EventTravelPlanCreate,
    authz: AuthorizationService,
) -> EventTravelPlan:
    event = await get_event(db, event_id)
    await ensure_manage_event_scope(authz, event.organization_id, identity)
    risk_level, risk_assessment = classify_travel_risk(payload)
    plan = EventTravelPlan(
        organization_id=event.organization_id,
        event_id=event.id,
        risk_level=risk_level,
        risk_assessment=risk_assessment,
        **payload.model_dump(),
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def list_travel_plans(db: AsyncSession, event_id: UUID) -> list[EventTravelPlan]:
    await get_event(db, event_id)
    rows = await db.scalars(
        select(EventTravelPlan)
        .where(EventTravelPlan.event_id == event_id)
        .order_by(EventTravelPlan.departure_at.nulls_last(), EventTravelPlan.created_at.desc())
    )
    return list(rows.all())


async def update_travel_plan(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelPlanUpdate,
    authz: AuthorizationService,
) -> EventTravelPlan:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    for field in [
        "status",
        "route_summary",
        "vehicle_details",
        "driver_details",
        "staff_manifest",
        "passenger_manifest",
        "lodging_details",
        "meal_plan",
        "equipment_manifest",
        "emergency_contacts",
        "medical_access_plan",
        "route_weather_risk",
        "driver_certification_status",
        "vehicle_inspection_status",
        "notes",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(plan, field, value)
    risk_level, risk_assessment = classify_travel_plan(plan)
    plan.risk_level = risk_level
    plan.risk_assessment = risk_assessment
    await db.commit()
    await db.refresh(plan)
    return plan


async def request_travel_consents(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelConsentRequestCreate,
    authz: AuthorizationService,
) -> EventTravelConsentBatchRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    event = await get_event(db, plan.event_id)
    await ensure_manage_event_scope(authz, plan.organization_id, identity)

    created = 0
    existing = 0
    skipped_no_guardian = 0
    skipped_not_minor = 0
    request_items: list[EventTravelConsentRequestItemRead] = []
    for athlete_person_id in await event_participant_person_ids(db, event):
        athlete = await db.get(Person, athlete_person_id)
        if athlete is None:
            continue
        minor = is_minor_on(athlete, event.starts_at.date())
        if minor is False or (minor is None and not payload.include_unknown_age):
            skipped_not_minor += 1
            continue
        clearance, _, _, consent_id, _ = await clearance_for_event(db, event.id, athlete_person_id)
        if clearance == ParticipationClearanceStatus.CLEARED and consent_id is not None:
            existing += 1
            continue
        guardian = await primary_signing_guardian(db, athlete_person_id)
        if guardian is None:
            skipped_no_guardian += 1
            continue
        existing_request = await db.scalar(
            select(ConsentRequest).where(
                ConsentRequest.organization_id == event.organization_id,
                ConsentRequest.athlete_person_id == athlete_person_id,
                ConsentRequest.guardian_person_id == guardian.guardian_person_id,
                ConsentRequest.scope_type == ConsentScopeType.EVENT,
                ConsentRequest.scope_id == event.id,
                ConsentRequest.status == ConsentRequestStatus.PENDING,
            )
        )
        if existing_request is not None:
            existing += 1
            continue
        notes = payload.notes or travel_consent_notes(event, plan)
        request, token = await create_consent_request(
            db,
            identity,
            ConsentRequestCreate(
                organization_id=event.organization_id,
                athlete_person_id=athlete_person_id,
                guardian_person_id=guardian.guardian_person_id,
                scope_type=ConsentScopeType.EVENT,
                scope_id=event.id,
                channel=payload.channel,
                expires_at=payload.expires_at or plan.consent_due_at,
                notes=notes,
            ),
            authz,
        )
        created += 1
        request_items.append(
            EventTravelConsentRequestItemRead(
                request_id=request.id,
                athlete_person_id=athlete_person_id,
                guardian_person_id=guardian.guardian_person_id,
                destination=request.destination,
                one_time_token=token,
            )
        )
    return EventTravelConsentBatchRead(
        event_id=event.id,
        travel_plan_id=plan.id,
        created=created,
        existing=existing,
        skipped_no_guardian=skipped_no_guardian,
        skipped_not_minor=skipped_not_minor,
        requests=request_items,
    )


async def send_travel_consent_reminders(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelConsentReminderCreate,
    authz: AuthorizationService,
) -> EventTravelConsentReminderRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    event = await get_event(db, plan.event_id)
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    pending_requests = await pending_event_consent_requests(db, event)
    if not pending_requests:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No pending travel consents")

    guardian_ids = sorted({request.guardian_person_id for request in pending_requests}, key=str)
    message = await create_message(
        db,
        identity,
        CommunicationMessageCreate(
            organization_id=event.organization_id,
            message_type=CommunicationMessageType.REMINDER,
            channel=payload.channel,
            scope_type=CommunicationScopeType.PERSON,
            scope_id=guardian_ids[0],
            recipient_person_ids=guardian_ids,
            subject=payload.subject or travel_consent_reminder_subject(event),
            body=payload.body or travel_consent_reminder_body(event, plan, len(pending_requests)),
            urgent=False,
            quiet_hours_override=False,
            copy_guardians_for_minors=False,
        ),
        authz,
    )
    recipient_count = await db.scalar(
        select(func.count(MessageRecipient.id)).where(MessageRecipient.message_id == message.id)
    )
    return EventTravelConsentReminderRead(
        event_id=event.id,
        travel_plan_id=plan.id,
        message_id=message.id,
        pending_request_count=len(pending_requests),
        recipient_count=int(recipient_count or 0),
    )


async def run_event_travel_consent_reminders(
    db: AsyncSession,
    identity: CurrentIdentity,
    event_id: UUID,
    payload: EventTravelConsentReminderRunCreate,
    authz: AuthorizationService,
) -> EventTravelConsentReminderRunRead:
    event = await get_event(db, event_id)
    await ensure_manage_event_scope(authz, event.organization_id, identity)
    now = datetime.now(UTC)
    due_by = now + timedelta(hours=payload.due_within_hours)
    due_plans = list(
        (
            await db.scalars(
                select(EventTravelPlan)
                .where(EventTravelPlan.event_id == event.id)
                .where(EventTravelPlan.consent_required.is_(True))
                .where(EventTravelPlan.status.not_in([TravelPlanStatus.COMPLETED, TravelPlanStatus.CANCELLED]))
                .where(EventTravelPlan.consent_due_at.is_not(None))
                .where(EventTravelPlan.consent_due_at <= due_by)
                .order_by(EventTravelPlan.consent_due_at, EventTravelPlan.destination)
            )
        ).all()
    )
    pending_requests = await pending_event_consent_requests(db, event)
    guardian_ids = sorted({request.guardian_person_id for request in pending_requests}, key=str)
    message_id: UUID | None = None
    recipient_count = 0
    if payload.send_reminders and due_plans and guardian_ids:
        message = await create_message(
            db,
            identity,
            CommunicationMessageCreate(
                organization_id=event.organization_id,
                message_type=CommunicationMessageType.REMINDER,
                channel=payload.channel,
                scope_type=CommunicationScopeType.PERSON,
                scope_id=guardian_ids[0],
                recipient_person_ids=guardian_ids,
                subject=payload.subject or scheduled_travel_consent_reminder_subject(event),
                body=payload.body or scheduled_travel_consent_reminder_body(event, due_plans, len(pending_requests)),
                urgent=False,
                quiet_hours_override=False,
                copy_guardians_for_minors=False,
            ),
            authz,
        )
        message_id = message.id
        recipient_count = int(
            await db.scalar(select(func.count(MessageRecipient.id)).where(MessageRecipient.message_id == message.id))
            or 0
        )
    return EventTravelConsentReminderRunRead(
        event_id=event.id,
        due_by=due_by,
        due_plan_count=len(due_plans),
        pending_request_count=len(pending_requests),
        message_id=message_id,
        recipient_count=recipient_count,
        channel=payload.channel,
        plans=[
            EventTravelConsentReminderRunPlanRead(
                travel_plan_id=plan.id,
                destination=plan.destination,
                travel_mode=plan.travel_mode,
                consent_due_at=plan.consent_due_at,
                status=plan.status,
            )
            for plan in due_plans
        ],
    )


async def get_travel_manifest(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    authz: AuthorizationService,
) -> EventTravelManifestRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    event = await get_event(db, plan.event_id)
    await ensure_manage_event_scope(authz, plan.organization_id, identity)

    participants: list[EventTravelManifestParticipantRead] = []
    for athlete_person_id in await event_participant_person_ids(db, event):
        athlete = await db.get(Person, athlete_person_id)
        if athlete is None:
            continue
        guardian_rows = await guardian_contact_rows(db, athlete_person_id)
        _, medical_status, _, medical_reason = await medical_clearance_for_event(db, event.id, athlete_person_id)
        participants.append(
            EventTravelManifestParticipantRead(
                person_id=athlete.id,
                display_name=athlete.display_name,
                guardian_names=[guardian.display_name for _, guardian in guardian_rows],
                guardian_contacts=guardian_contacts(guardian_rows),
                medical_clearance_status=medical_status,
                medical_clearance_reason=medical_reason,
            )
        )

    return EventTravelManifestRead(
        event_id=event.id,
        travel_plan_id=plan.id,
        destination=plan.destination,
        participant_count=len(participants),
        emergency_contacts=plan.emergency_contacts,
        medical_access_plan=plan.medical_access_plan,
        participants=participants,
    )


async def export_travel_manifest(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelManifestExportCreate,
    authz: AuthorizationService,
) -> EventTravelManifestExportRead:
    manifest = await get_travel_manifest(db, identity, travel_plan_id, authz)
    suffix = "csv" if payload.format == "csv" else "txt"
    filename = f"travel-manifest-{slugify_filename(manifest.destination)}.{suffix}"
    if payload.format == "csv":
        content_type = "text/csv"
        content = travel_manifest_csv(manifest)
    else:
        content_type = "text/plain"
        content = travel_manifest_text(manifest)
    return EventTravelManifestExportRead(
        event_id=manifest.event_id,
        travel_plan_id=manifest.travel_plan_id,
        filename=filename,
        content_type=content_type,
        content=content,
    )


async def create_travel_manifest_offline_link(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelManifestOfflineLinkCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> EventTravelManifestOfflineLinkRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    selected_settings = settings or get_settings()
    manifest = await get_travel_manifest(db, identity, travel_plan_id, authz)
    filename, content_type, content = travel_manifest_artifact(manifest, payload.format)
    checksum = sha256(content).hexdigest()
    storage_name = f"{checksum[:16]}-{safe_upload_filename(filename, fallback='travel-manifest')}"
    relative_path = (Path(str(plan.organization_id)) / str(plan.id) / storage_name).as_posix()
    put_object(
        selected_settings,
        local_root=selected_settings.travel_manifest_file_dir,
        local_url_prefix=selected_settings.travel_manifest_file_url_prefix,
        key=relative_path,
        content=content,
        content_type=content_type,
    )
    ttl_seconds = payload.ttl_seconds or selected_settings.travel_manifest_url_ttl_seconds
    expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
    signed_url = signed_travel_manifest_url(
        selected_settings,
        plan.organization_id,
        plan.id,
        storage_name,
        expires_at,
    )
    return EventTravelManifestOfflineLinkRead(
        event_id=manifest.event_id,
        travel_plan_id=plan.id,
        filename=filename,
        content_type=content_type,
        size_bytes=len(content),
        checksum=checksum,
        signed_url=signed_url,
        expires_at=expires_at,
    )


def read_signed_travel_manifest(
    organization_id: UUID,
    travel_plan_id: UUID,
    filename: str,
    expires: int,
    signature: str,
    settings: Settings | None = None,
) -> dict[str, object]:
    selected_settings = settings or get_settings()
    if "/" in filename or "\\" in filename or filename in {"", ".", ".."}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid manifest name")
    if expires < int(time.time()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manifest link expired")
    expected = travel_manifest_signature(selected_settings, organization_id, travel_plan_id, filename, expires)
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid manifest signature")
    content = get_object(
        selected_settings,
        local_root=selected_settings.travel_manifest_file_dir,
        key=(Path(str(organization_id)) / str(travel_plan_id) / filename).as_posix(),
    )
    return {
        "content": content,
        "content_type": travel_manifest_content_type(filename),
        "filename": public_manifest_filename(filename),
        "checksum": sha256(content).hexdigest(),
    }


async def generate_travel_fee_invoices(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelFeeInvoiceCreate,
    authz: AuthorizationService,
) -> EventTravelFeeInvoiceBatchRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    event = await get_event(db, plan.event_id)
    await ensure_manage_event_scope(authz, plan.organization_id, identity)

    amount = payload.amount_per_participant or plan.cost_per_participant
    if amount is None or amount <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Travel fee amount required")
    amount = Decimal(amount).quantize(Decimal("0.01"))
    due_on = payload.due_on or (plan.consent_due_at.date() if plan.consent_due_at is not None else None)

    created = 0
    existing = 0
    skipped_no_payer = 0
    total_amount_due = Decimal("0")
    invoice_items: list[EventTravelFeeInvoiceItemRead] = []
    for athlete_person_id in await event_participant_person_ids(db, event):
        billed_person_id = await travel_fee_payer_id(db, athlete_person_id, event, payload.bill_guardians_for_minors)
        if billed_person_id is None:
            skipped_no_payer += 1
            continue
        invoice_number = travel_fee_invoice_number(plan, billed_person_id, athlete_person_id)
        invoice = await db.scalar(
            select(FinanceInvoice).where(
                FinanceInvoice.organization_id == event.organization_id,
                FinanceInvoice.invoice_number == invoice_number,
            )
        )
        if invoice is None:
            invoice = FinanceInvoice(
                organization_id=event.organization_id,
                person_id=billed_person_id,
                team_id=event.team_id,
                sponsor_id=None,
                invoice_number=invoice_number,
                title=f"Travel fee: {event.title}",
                amount_due=amount,
                currency=payload.currency.upper(),
                due_on=due_on,
                memo=payload.memo or travel_fee_invoice_memo(event, plan),
            )
            db.add(invoice)
            await db.flush()
            created += 1
        else:
            existing += 1
        total_amount_due += invoice.amount_due
        invoice_items.append(
            EventTravelFeeInvoiceItemRead(
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                billed_person_id=billed_person_id,
                athlete_person_id=athlete_person_id,
                amount_due=invoice.amount_due,
                status=invoice.status.value,
            )
        )
    await db.commit()

    return EventTravelFeeInvoiceBatchRead(
        event_id=event.id,
        travel_plan_id=plan.id,
        created=created,
        existing=existing,
        skipped_no_payer=skipped_no_payer,
        total_amount_due=total_amount_due.quantize(Decimal("0.01")),
        invoices=invoice_items,
    )


async def create_travel_fee_checkouts(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelFeeCheckoutCreate,
    authz: AuthorizationService,
) -> EventTravelFeeCheckoutBatchRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    event = await get_event(db, plan.event_id)
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    invoice_prefix = f"TRAVEL-{str(plan.id)[:8]}".upper()
    invoices = (
        await db.scalars(
            select(FinanceInvoice)
            .where(
                FinanceInvoice.organization_id == plan.organization_id,
                FinanceInvoice.invoice_number.like(f"{invoice_prefix}-%"),
            )
            .order_by(FinanceInvoice.due_on, FinanceInvoice.invoice_number)
        )
    ).all()
    if not invoices:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel fee invoices not found")

    checkouts: list[EventTravelFeeCheckoutItemRead] = []
    total_open_amount = Decimal("0.00")
    for invoice in invoices:
        open_amount = max(invoice.amount_due - invoice.amount_paid, Decimal("0.00")).quantize(Decimal("0.01"))
        total_open_amount += open_amount
        checkouts.append(
            EventTravelFeeCheckoutItemRead(
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                billed_person_id=invoice.person_id,
                amount_due=invoice.amount_due,
                amount_paid=invoice.amount_paid,
                open_amount=open_amount,
                currency=invoice.currency,
                status=invoice.status.value,
                provider=payload.provider,
                checkout_url=travel_fee_checkout_url(payload.checkout_base_url, invoice, payload.provider),
                expires_at=payload.expires_at,
            )
        )

    return EventTravelFeeCheckoutBatchRead(
        event_id=event.id,
        travel_plan_id=plan.id,
        provider=payload.provider,
        checkout_count=len(checkouts),
        total_open_amount=total_open_amount.quantize(Decimal("0.01")),
        checkouts=checkouts,
    )


async def list_travel_approvals(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    authz: AuthorizationService,
) -> list[EventTravelApprovalRead]:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    rows = (
        await db.scalars(
            select(EventTravelApproval)
            .where(EventTravelApproval.travel_plan_id == plan.id)
            .order_by(EventTravelApproval.approval_level)
        )
    ).all()
    return [travel_approval_read(item) for item in rows]


async def create_travel_approval(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelApprovalCreate,
    authz: AuthorizationService,
) -> EventTravelApprovalRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    if payload.approver_person_id is not None and await db.get(Person, payload.approver_person_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approver not found")
    existing = await db.scalar(
        select(EventTravelApproval).where(
            EventTravelApproval.travel_plan_id == plan.id,
            EventTravelApproval.approval_level == payload.approval_level,
        )
    )
    if existing is not None:
        return travel_approval_read(existing)
    approval = EventTravelApproval(
        organization_id=plan.organization_id,
        travel_plan_id=plan.id,
        approval_level=payload.approval_level,
        status="pending",
        approver_person_id=payload.approver_person_id,
        notes=payload.notes,
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    return travel_approval_read(approval)


async def route_travel_approvals(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelApprovalRoutingCreate,
    authz: AuthorizationService,
) -> EventTravelApprovalRoutingRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    event = await get_event(db, plan.event_id)
    await ensure_manage_event_scope(authz, plan.organization_id, identity)

    levels, rationale = recommended_travel_approval_levels(plan, payload)
    created = 0
    existing = 0
    for level in levels:
        current = await db.scalar(
            select(EventTravelApproval).where(
                EventTravelApproval.travel_plan_id == plan.id,
                EventTravelApproval.approval_level == level,
            )
        )
        if current is None:
            db.add(
                EventTravelApproval(
                    organization_id=plan.organization_id,
                    travel_plan_id=plan.id,
                    approval_level=level,
                    status="pending",
                    notes=payload.notes or travel_approval_routing_note(plan, level),
                )
            )
            created += 1
        else:
            existing += 1
    await db.commit()
    approvals = await list_travel_approvals(db, identity, travel_plan_id, authz)
    return EventTravelApprovalRoutingRead(
        event_id=event.id,
        travel_plan_id=plan.id,
        recommended_levels=levels,
        created=created,
        existing=existing,
        rationale=rationale,
        approvals=approvals,
    )


async def update_travel_approval(
    db: AsyncSession,
    identity: CurrentIdentity,
    approval_id: UUID,
    payload: EventTravelApprovalUpdate,
    authz: AuthorizationService,
) -> EventTravelApprovalRead:
    approval = await db.get(EventTravelApproval, approval_id)
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel approval not found")
    await ensure_manage_event_scope(authz, approval.organization_id, identity)
    approval.status = payload.status
    approval.notes = payload.notes if payload.notes is not None else approval.notes
    if payload.status in {"approved", "rejected", "cancelled"}:
        approval.decided_by_person_id = identity.person_id
        approval.decided_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(approval)
    return travel_approval_read(approval)


async def list_travel_checklist_items(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    authz: AuthorizationService,
) -> list[EventTravelChecklistItemRead]:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    rows = (
        await db.scalars(
            select(EventTravelChecklistItem)
            .where(EventTravelChecklistItem.travel_plan_id == plan.id)
            .order_by(EventTravelChecklistItem.checklist_type, EventTravelChecklistItem.item_label)
        )
    ).all()
    return [travel_checklist_item_read(item) for item in rows]


async def seed_travel_checklist_items(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelChecklistSeedCreate,
    authz: AuthorizationService,
) -> list[EventTravelChecklistItemRead]:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    labels = [item.strip() for item in (payload.items or DEFAULT_TRAVEL_CHECKLIST_ITEMS) if item.strip()]
    if not labels:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Checklist items required")
    for label in labels:
        existing = await db.scalar(
            select(EventTravelChecklistItem).where(
                EventTravelChecklistItem.travel_plan_id == plan.id,
                EventTravelChecklistItem.checklist_type == payload.checklist_type,
                EventTravelChecklistItem.item_label == label[:240],
            )
        )
        if existing is None:
            db.add(
                EventTravelChecklistItem(
                    organization_id=plan.organization_id,
                    travel_plan_id=plan.id,
                    checklist_type=payload.checklist_type,
                    item_label=label[:240],
                    status="pending",
                )
            )
    await db.commit()
    return await list_travel_checklist_items(db, identity, travel_plan_id, authz)


async def update_travel_checklist_item(
    db: AsyncSession,
    identity: CurrentIdentity,
    checklist_item_id: UUID,
    payload: EventTravelChecklistItemUpdate,
    authz: AuthorizationService,
) -> EventTravelChecklistItemRead:
    item = await db.get(EventTravelChecklistItem, checklist_item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel checklist item not found")
    await ensure_manage_event_scope(authz, item.organization_id, identity)
    item.status = payload.status
    item.evidence_url = payload.evidence_url if payload.evidence_url is not None else item.evidence_url
    item.notes = payload.notes if payload.notes is not None else item.notes
    if payload.status in {"completed", "blocked", "not_applicable"}:
        item.completed_by_person_id = identity.person_id
        item.completed_at = datetime.now(UTC)
    elif payload.status == "pending":
        item.completed_by_person_id = None
        item.completed_at = None
    await db.commit()
    await db.refresh(item)
    return travel_checklist_item_read(item)


async def upload_travel_checklist_evidence(
    db: AsyncSession,
    identity: CurrentIdentity,
    checklist_item_id: UUID,
    payload: EventTravelChecklistEvidenceUploadCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> EventTravelChecklistEvidenceUploadRead:
    item = await db.get(EventTravelChecklistItem, checklist_item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel checklist item not found")
    await ensure_manage_event_scope(authz, item.organization_id, identity)
    content = decode_upload_content(payload.content_base64)
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Evidence file is empty")
    selected_settings = settings or get_settings()
    checksum = sha256(content).hexdigest()
    safe_name = safe_upload_filename(payload.filename, fallback="travel-checklist-evidence")
    storage_name = f"{checksum[:16]}-{safe_name}"
    relative_path = (
        Path(str(item.organization_id))
        / str(item.travel_plan_id)
        / str(item.id)
        / storage_name
    ).as_posix()
    stored = put_object(
        selected_settings,
        local_root=selected_settings.travel_checklist_file_dir,
        local_url_prefix=selected_settings.travel_checklist_file_url_prefix,
        key=relative_path,
        content=content,
        content_type=payload.content_type or "application/octet-stream",
    )
    item.evidence_url = stored.url
    item.status = payload.status
    item.notes = payload.notes if payload.notes is not None else item.notes
    if payload.status in {"completed", "blocked", "not_applicable"}:
        item.completed_by_person_id = identity.person_id
        item.completed_at = datetime.now(UTC)
    elif payload.status == "pending":
        item.completed_by_person_id = None
        item.completed_at = None
    await db.commit()
    await db.refresh(item)
    return EventTravelChecklistEvidenceUploadRead(
        checklist_item_id=item.id,
        filename=safe_name,
        content_type=payload.content_type or "application/octet-stream",
        size_bytes=len(content),
        checksum=checksum,
        evidence_url=stored.url,
        checklist_item=travel_checklist_item_read(item),
    )


async def list_travel_location_updates(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    authz: AuthorizationService,
) -> list[EventTravelLocationUpdateRead]:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    rows = (
        await db.scalars(
            select(EventTravelLocationUpdate)
            .where(EventTravelLocationUpdate.travel_plan_id == plan.id)
            .order_by(EventTravelLocationUpdate.recorded_at.desc())
        )
    ).all()
    return [await travel_location_update_read(db, item) for item in rows]


async def create_travel_location_update(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelLocationUpdateCreate,
    authz: AuthorizationService,
) -> EventTravelLocationUpdateRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    event = await get_event(db, plan.event_id)
    await ensure_manage_event_scope(authz, plan.organization_id, identity)

    update = EventTravelLocationUpdate(
        organization_id=plan.organization_id,
        travel_plan_id=plan.id,
        phase=payload.phase,
        source=payload.source,
        recorded_at=payload.recorded_at or datetime.now(UTC),
        recorded_by_person_id=identity.person_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed_kph=payload.speed_kph,
        heading_degrees=payload.heading_degrees,
        notes=payload.notes,
    )
    db.add(update)
    await db.flush()

    apply_travel_phase_status(plan, payload.phase)

    if payload.notify_guardians and payload.phase in {"departed", "delayed", "arrived", "returned"}:
        message = await create_message(
            db,
            identity,
            CommunicationMessageCreate(
                organization_id=event.organization_id,
                message_type=CommunicationMessageType.ALERT
                if payload.phase in {"delayed"}
                else CommunicationMessageType.REMINDER,
                channel=payload.channel,
                scope_type=CommunicationScopeType.EVENT,
                scope_id=event.id,
                subject=travel_location_subject(event, plan, payload.phase),
                body=travel_location_body(event, plan, update),
                urgent=payload.phase == "delayed",
                quiet_hours_override=payload.phase == "delayed",
                copy_guardians_for_minors=True,
            ),
            authz,
        )
        update.notification_message_id = message.id
        await db.flush()

    await db.commit()
    await db.refresh(update)
    return await travel_location_update_read(db, update)


async def list_travel_devices(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    authz: AuthorizationService,
) -> list[EventTravelDeviceRead]:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    devices = (
        await db.scalars(
            select(EventTravelDevice)
            .where(EventTravelDevice.travel_plan_id == plan.id)
            .order_by(EventTravelDevice.status, EventTravelDevice.label)
        )
    ).all()
    return [travel_device_read(device) for device in devices]


async def create_travel_device(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelDeviceCreate,
    authz: AuthorizationService,
) -> EventTravelDeviceRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    existing = await db.scalar(
        select(EventTravelDevice)
        .where(EventTravelDevice.travel_plan_id == plan.id)
        .where(EventTravelDevice.provider == payload.provider)
        .where(EventTravelDevice.device_id == payload.device_id)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Travel device already provisioned")
    device = EventTravelDevice(
        organization_id=plan.organization_id,
        travel_plan_id=plan.id,
        provider=payload.provider,
        device_id=payload.device_id,
        label=payload.label,
        status=payload.status,
        assigned_vehicle=payload.assigned_vehicle,
        installed_at=payload.installed_at,
        notes=payload.notes,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return travel_device_read(device)


async def update_travel_device(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_device_id: UUID,
    payload: EventTravelDeviceUpdate,
    authz: AuthorizationService,
) -> EventTravelDeviceRead:
    device = await db.get(EventTravelDevice, travel_device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel device not found")
    await ensure_manage_event_scope(authz, device.organization_id, identity)
    if payload.label is not None:
        device.label = payload.label
    if payload.status is not None:
        device.status = payload.status
    if "assigned_vehicle" in payload.model_fields_set:
        device.assigned_vehicle = payload.assigned_vehicle
    if "installed_at" in payload.model_fields_set:
        device.installed_at = payload.installed_at
    if "notes" in payload.model_fields_set:
        device.notes = payload.notes
    await db.commit()
    await db.refresh(device)
    return travel_device_read(device)


async def ingest_travel_device_location(
    db: AsyncSession,
    travel_plan_id: UUID,
    payload: EventTravelDeviceLocationIngestCreate,
    *,
    signature_required: bool = False,
    signature_validated: bool = False,
) -> EventTravelDeviceLocationIngestRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    device = await travel_device_for_ingest(db, plan, payload)
    update = EventTravelLocationUpdate(
        organization_id=plan.organization_id,
        travel_plan_id=plan.id,
        phase=payload.phase,
        source=f"{payload.provider}:{payload.device_id}"[:80],
        recorded_at=payload.recorded_at or datetime.now(UTC),
        recorded_by_person_id=None,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed_kph=payload.speed_kph,
        heading_degrees=payload.heading_degrees,
        notes=travel_device_location_notes(payload, signature_required, signature_validated),
    )
    db.add(update)
    await db.flush()
    if device is not None:
        device.last_seen_at = update.recorded_at
        device.last_location_update_id = update.id
        device.last_battery_percent = payload.battery_percent
        device.last_accuracy_meters = payload.accuracy_meters
    apply_travel_phase_status(plan, payload.phase)
    await db.commit()
    await db.refresh(update)
    if device is not None:
        await db.refresh(device)
    return EventTravelDeviceLocationIngestRead(
        travel_plan_id=plan.id,
        device_id=payload.device_id,
        provider=payload.provider,
        device_registration_id=device.id if device is not None else None,
        device_status=device.status if device is not None else None,
        signature_required=signature_required,
        signature_validated=signature_validated,
        update=await travel_location_update_read(db, update),
    )


def validate_travel_device_ingest_signature(
    raw_body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
    settings: Settings | None = None,
) -> tuple[bool, bool]:
    selected_settings = settings or get_settings()
    signing_key = selected_settings.travel_device_ingest_key
    if not signing_key:
        return False, False
    if not timestamp_header or not signature_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing travel device signature")
    try:
        timestamp = int(timestamp_header)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid travel device timestamp") from exc
    age = abs(int(time.time()) - timestamp)
    if age > selected_settings.travel_device_ingest_tolerance_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Stale travel device signature")
    expected = hmac.new(
        signing_key.encode(),
        timestamp_header.encode() + b"." + raw_body,
        sha256,
    ).hexdigest()
    submitted = signature_header.removeprefix("sha256=")
    if not hmac.compare_digest(expected, submitted):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid travel device signature")
    return True, True


async def travel_device_for_ingest(
    db: AsyncSession,
    plan: EventTravelPlan,
    payload: EventTravelDeviceLocationIngestCreate,
) -> EventTravelDevice | None:
    device = await db.scalar(
        select(EventTravelDevice)
        .where(EventTravelDevice.travel_plan_id == plan.id)
        .where(EventTravelDevice.provider == payload.provider)
        .where(EventTravelDevice.device_id == payload.device_id)
    )
    if device is not None:
        if device.status != "active":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Travel device is not active")
        return device
    provisioned_count = int(
        await db.scalar(select(func.count(EventTravelDevice.id)).where(EventTravelDevice.travel_plan_id == plan.id)) or 0
    )
    if provisioned_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel device is not provisioned")
    return None


async def check_travel_geofence(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelGeofenceCheckCreate,
    authz: AuthorizationService,
) -> EventTravelGeofenceCheckRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    event = await get_event(db, plan.event_id)
    await ensure_manage_event_scope(authz, plan.organization_id, identity)

    latest_update = await db.scalar(
        select(EventTravelLocationUpdate)
        .where(EventTravelLocationUpdate.travel_plan_id == plan.id)
        .order_by(EventTravelLocationUpdate.recorded_at.desc())
    )
    if latest_update is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Record a travel location update before checking geofence status",
        )

    distance_km_value = travel_distance_km(
        float(payload.center_latitude),
        float(payload.center_longitude),
        float(latest_update.latitude),
        float(latest_update.longitude),
    )
    distance_km = Decimal(str(round(distance_km_value, 3)))
    breached = distance_km > payload.radius_km
    message_id: UUID | None = None
    recipient_count = 0
    if breached and payload.alert_on_breach:
        message = await create_message(
            db,
            identity,
            CommunicationMessageCreate(
                organization_id=event.organization_id,
                message_type=CommunicationMessageType.ALERT,
                channel=payload.channel,
                scope_type=CommunicationScopeType.EVENT,
                scope_id=event.id,
                subject=travel_geofence_subject(event, plan, payload.label),
                body=travel_geofence_body(event, plan, latest_update, payload, distance_km),
                urgent=True,
                quiet_hours_override=True,
                copy_guardians_for_minors=True,
            ),
            authz,
        )
        message_id = message.id
        recipient_count = int(
            await db.scalar(select(func.count(MessageRecipient.id)).where(MessageRecipient.message_id == message.id))
            or 0
        )

    return EventTravelGeofenceCheckRead(
        event_id=event.id,
        travel_plan_id=plan.id,
        latest_update_id=latest_update.id,
        label=payload.label,
        center_latitude=payload.center_latitude,
        center_longitude=payload.center_longitude,
        radius_km=payload.radius_km,
        distance_km=distance_km,
        inside=not breached,
        breached=breached,
        message_id=message_id,
        recipient_count=recipient_count,
        recommendation=travel_geofence_recommendation(breached, payload.radius_km, distance_km),
    )


async def list_travel_geofence_zones(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    authz: AuthorizationService,
) -> list[EventTravelGeofenceZoneRead]:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    zones = (
        await db.scalars(
            select(EventTravelGeofenceZone)
            .where(EventTravelGeofenceZone.travel_plan_id == plan.id)
            .order_by(EventTravelGeofenceZone.active.desc(), EventTravelGeofenceZone.label)
        )
    ).all()
    return [travel_geofence_zone_read(zone) for zone in zones]


async def create_travel_geofence_zone(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelGeofenceZoneCreate,
    authz: AuthorizationService,
) -> EventTravelGeofenceZoneRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    existing = await db.scalar(
        select(EventTravelGeofenceZone)
        .where(EventTravelGeofenceZone.travel_plan_id == plan.id)
        .where(EventTravelGeofenceZone.label == payload.label)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Travel geofence zone already exists")
    zone = EventTravelGeofenceZone(
        organization_id=plan.organization_id,
        travel_plan_id=plan.id,
        label=payload.label,
        center_latitude=payload.center_latitude,
        center_longitude=payload.center_longitude,
        radius_km=payload.radius_km,
        alert_on_breach=payload.alert_on_breach,
        channel=payload.channel.value,
        active=payload.active,
        notes=payload.notes,
    )
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return travel_geofence_zone_read(zone)


async def update_travel_geofence_zone(
    db: AsyncSession,
    identity: CurrentIdentity,
    geofence_zone_id: UUID,
    payload: EventTravelGeofenceZoneUpdate,
    authz: AuthorizationService,
) -> EventTravelGeofenceZoneRead:
    zone = await db.get(EventTravelGeofenceZone, geofence_zone_id)
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel geofence zone not found")
    await ensure_manage_event_scope(authz, zone.organization_id, identity)
    if payload.label is not None and payload.label != zone.label:
        existing = await db.scalar(
            select(EventTravelGeofenceZone)
            .where(EventTravelGeofenceZone.travel_plan_id == zone.travel_plan_id)
            .where(EventTravelGeofenceZone.label == payload.label)
            .where(EventTravelGeofenceZone.id != zone.id)
        )
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Travel geofence zone already exists")
        zone.label = payload.label
    if payload.center_latitude is not None:
        zone.center_latitude = payload.center_latitude
    if payload.center_longitude is not None:
        zone.center_longitude = payload.center_longitude
    if payload.radius_km is not None:
        zone.radius_km = payload.radius_km
    if payload.alert_on_breach is not None:
        zone.alert_on_breach = payload.alert_on_breach
    if payload.channel is not None:
        zone.channel = payload.channel.value
    if payload.active is not None:
        zone.active = payload.active
    if "notes" in payload.model_fields_set:
        zone.notes = payload.notes
    await db.commit()
    await db.refresh(zone)
    return travel_geofence_zone_read(zone)


async def check_travel_geofence_zone(
    db: AsyncSession,
    identity: CurrentIdentity,
    geofence_zone_id: UUID,
    authz: AuthorizationService,
) -> EventTravelGeofenceCheckRead:
    zone = await db.get(EventTravelGeofenceZone, geofence_zone_id)
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel geofence zone not found")
    if not zone.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Travel geofence zone is inactive")
    payload = EventTravelGeofenceCheckCreate(
        center_latitude=zone.center_latitude,
        center_longitude=zone.center_longitude,
        radius_km=zone.radius_km,
        label=zone.label,
        alert_on_breach=zone.alert_on_breach,
        channel=CommunicationChannel(zone.channel),
    )
    return await check_travel_geofence(db, identity, zone.travel_plan_id, payload, authz)


def travel_geofence_zone_read(zone: EventTravelGeofenceZone) -> EventTravelGeofenceZoneRead:
    return EventTravelGeofenceZoneRead(
        id=zone.id,
        organization_id=zone.organization_id,
        travel_plan_id=zone.travel_plan_id,
        label=zone.label,
        center_latitude=zone.center_latitude,
        center_longitude=zone.center_longitude,
        radius_km=zone.radius_km,
        alert_on_breach=zone.alert_on_breach,
        channel=CommunicationChannel(zone.channel),
        active=zone.active,
        notes=zone.notes,
        created_at=zone.created_at,
        updated_at=zone.updated_at,
    )


async def list_travel_expenses(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    authz: AuthorizationService,
) -> list[EventTravelExpenseRead]:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    rows = (
        await db.scalars(
            select(EventTravelExpense)
            .where(EventTravelExpense.travel_plan_id == plan.id)
            .order_by(EventTravelExpense.incurred_at.desc(), EventTravelExpense.created_at.desc())
        )
    ).all()
    return [travel_expense_read(item) for item in rows]


async def create_travel_expense(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelExpenseCreate,
    authz: AuthorizationService,
) -> EventTravelExpenseRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    if payload.paid_by_person_id is not None and await db.get(Person, payload.paid_by_person_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paid-by person not found")

    expense = EventTravelExpense(
        organization_id=plan.organization_id,
        travel_plan_id=plan.id,
        category=payload.category,
        vendor=payload.vendor,
        amount=payload.amount,
        currency=payload.currency.upper(),
        incurred_at=payload.incurred_at or datetime.now(UTC),
        paid_by_person_id=payload.paid_by_person_id,
        reimbursement_status="submitted",
        receipt_url=payload.receipt_url,
        notes=payload.notes,
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return travel_expense_read(expense)


async def update_travel_expense(
    db: AsyncSession,
    identity: CurrentIdentity,
    expense_id: UUID,
    payload: EventTravelExpenseUpdate,
    authz: AuthorizationService,
) -> EventTravelExpenseRead:
    expense = await db.get(EventTravelExpense, expense_id)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel expense not found")
    await ensure_manage_event_scope(authz, expense.organization_id, identity)
    expense.reimbursement_status = payload.reimbursement_status
    expense.receipt_url = payload.receipt_url if payload.receipt_url is not None else expense.receipt_url
    expense.notes = payload.notes if payload.notes is not None else expense.notes
    if payload.reimbursement_status in {"approved", "reimbursed", "rejected"}:
        expense.approved_by_person_id = identity.person_id
    if payload.reimbursement_status == "reimbursed":
        expense.reimbursed_at = datetime.now(UTC)
    elif payload.reimbursement_status in {"draft", "submitted", "approved", "rejected"}:
        expense.reimbursed_at = None
    await db.commit()
    await db.refresh(expense)
    return travel_expense_read(expense)


async def upload_travel_expense_receipt(
    db: AsyncSession,
    identity: CurrentIdentity,
    expense_id: UUID,
    payload: EventTravelReceiptUploadCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> EventTravelReceiptUploadRead:
    expense = await db.get(EventTravelExpense, expense_id)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel expense not found")
    await ensure_manage_event_scope(authz, expense.organization_id, identity)
    content = decode_upload_content(payload.content_base64)
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Receipt file is empty")
    selected_settings = settings or get_settings()
    checksum = sha256(content).hexdigest()
    safe_name = safe_upload_filename(payload.filename, fallback="travel-receipt")
    storage_name = f"{checksum[:16]}-{safe_name}"
    relative_path = (
        Path(str(expense.organization_id))
        / str(expense.travel_plan_id)
        / str(expense.id)
        / storage_name
    ).as_posix()
    stored = put_object(
        selected_settings,
        local_root=selected_settings.travel_receipt_file_dir,
        local_url_prefix=selected_settings.travel_receipt_file_url_prefix,
        key=relative_path,
        content=content,
        content_type=payload.content_type or "application/octet-stream",
    )
    expense.receipt_url = stored.url
    if payload.notes is not None:
        expense.notes = payload.notes
    await db.commit()
    await db.refresh(expense)
    return EventTravelReceiptUploadRead(
        expense_id=expense.id,
        filename=safe_name,
        content_type=payload.content_type or "application/octet-stream",
        size_bytes=len(content),
        checksum=checksum,
        receipt_url=stored.url,
        expense=travel_expense_read(expense),
    )


async def list_travel_carpool_rides(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    authz: AuthorizationService,
) -> list[EventTravelCarpoolRideRead]:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    rows = (
        await db.scalars(
            select(EventTravelCarpoolRide)
            .where(EventTravelCarpoolRide.travel_plan_id == plan.id)
            .order_by(EventTravelCarpoolRide.status, EventTravelCarpoolRide.departure_window_start)
        )
    ).all()
    return [travel_carpool_ride_read(item) for item in rows]


async def create_travel_carpool_ride(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelCarpoolRideCreate,
    authz: AuthorizationService,
) -> EventTravelCarpoolRideRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    await ensure_optional_person(db, payload.rider_person_id, "Rider not found")
    await ensure_optional_person(db, payload.driver_person_id, "Driver not found")
    if payload.ride_type == "offer" and payload.seats_available < 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Offer needs available seats")

    ride = EventTravelCarpoolRide(
        organization_id=plan.organization_id,
        travel_plan_id=plan.id,
        ride_type=payload.ride_type,
        status="open",
        rider_person_id=payload.rider_person_id,
        driver_person_id=payload.driver_person_id,
        pickup_location=payload.pickup_location,
        dropoff_location=payload.dropoff_location,
        seats_requested=payload.seats_requested,
        seats_available=payload.seats_available,
        departure_window_start=payload.departure_window_start,
        departure_window_end=payload.departure_window_end,
        notes=payload.notes,
    )
    db.add(ride)
    await db.commit()
    await db.refresh(ride)
    return travel_carpool_ride_read(ride)


async def auto_match_travel_carpools(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelCarpoolAutoMatchCreate,
    authz: AuthorizationService,
) -> EventTravelCarpoolAutoMatchRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    await ensure_manage_event_scope(authz, plan.organization_id, identity)
    rides = list(
        (
            await db.scalars(
                select(EventTravelCarpoolRide)
                .where(EventTravelCarpoolRide.travel_plan_id == plan.id)
                .where(EventTravelCarpoolRide.status.in_(["open", "matched"]))
                .order_by(EventTravelCarpoolRide.created_at, EventTravelCarpoolRide.departure_window_start)
            )
        ).all()
    )
    requests = [ride for ride in rides if ride.ride_type == "request" and ride.status == "open"]
    offers = [ride for ride in rides if ride.ride_type == "offer" and ride.status == "open"]
    available_seats = {offer.id: offer.seats_available for offer in offers}
    pairs: list[EventTravelCarpoolAutoMatchPairRead] = []
    used_requests: set[UUID] = set()
    for request in requests:
        ranked = sorted(
            [
                (travel_carpool_match_score(request, offer), offer)
                for offer in offers
                if available_seats.get(offer.id, 0) >= request.seats_requested
            ],
            key=lambda item: item[0],
            reverse=True,
        )
        if not ranked:
            continue
        score, offer = ranked[0]
        if score < payload.minimum_score:
            continue
        now = datetime.now(UTC)
        request.status = "confirmed" if payload.confirm_matches else "matched"
        offer.status = "confirmed" if payload.confirm_matches else "matched"
        request.match_score = score
        offer.match_score = max(offer.match_score or Decimal("0"), score)
        request.matched_at = request.matched_at or now
        offer.matched_at = offer.matched_at or now
        request.driver_person_id = request.driver_person_id or offer.driver_person_id
        request.notes = append_note(request.notes, f"Auto-matched to offer {offer.id} with score {score}.")
        offer.notes = append_note(offer.notes, f"Auto-matched request {request.id} with score {score}.")
        available_seats[offer.id] = available_seats[offer.id] - request.seats_requested
        offer.seats_available = available_seats[offer.id]
        used_requests.add(request.id)
        pairs.append(
            EventTravelCarpoolAutoMatchPairRead(
                request_id=request.id,
                offer_id=offer.id,
                score=score,
                seats_requested=request.seats_requested,
                seats_available=offer.seats_available,
                pickup_match=location_match_summary(request, offer),
                window_match=window_match_summary(request, offer),
            )
        )
    if pairs:
        await db.commit()
    refreshed_rides = await list_travel_carpool_rides(db, identity, travel_plan_id, authz)
    return EventTravelCarpoolAutoMatchRead(
        travel_plan_id=plan.id,
        matched_count=len(used_requests),
        request_count=len(requests),
        offer_count=len(offers),
        pairs=pairs,
        rides=refreshed_rides,
    )


async def update_travel_carpool_ride(
    db: AsyncSession,
    identity: CurrentIdentity,
    carpool_ride_id: UUID,
    payload: EventTravelCarpoolRideUpdate,
    authz: AuthorizationService,
) -> EventTravelCarpoolRideRead:
    ride = await db.get(EventTravelCarpoolRide, carpool_ride_id)
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carpool ride not found")
    await ensure_manage_event_scope(authz, ride.organization_id, identity)
    await ensure_optional_person(db, payload.rider_person_id, "Rider not found")
    await ensure_optional_person(db, payload.driver_person_id, "Driver not found")
    ride.status = payload.status
    ride.rider_person_id = payload.rider_person_id if payload.rider_person_id is not None else ride.rider_person_id
    ride.driver_person_id = payload.driver_person_id if payload.driver_person_id is not None else ride.driver_person_id
    ride.match_score = payload.match_score if payload.match_score is not None else ride.match_score
    ride.notes = payload.notes if payload.notes is not None else ride.notes
    if payload.status in {"matched", "confirmed"}:
        ride.matched_at = ride.matched_at or datetime.now(UTC)
    elif payload.status in {"open", "cancelled"}:
        ride.matched_at = None
    await db.commit()
    await db.refresh(ride)
    return travel_carpool_ride_read(ride)


async def get_travel_readiness(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    authz: AuthorizationService,
) -> EventTravelReadinessRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    event = await get_event(db, plan.event_id)
    await ensure_manage_event_scope(authz, plan.organization_id, identity)

    risk_level, risk_assessment = classify_travel_plan(plan)
    warnings = [line for line in risk_assessment.splitlines() if line]
    blockers: list[str] = []
    if risk_level == TravelRiskLevel.CRITICAL:
        blockers.append("Travel risk is critical; resolve route, driver, or vehicle blockers before departure.")

    approval_count = await count_travel_approvals(db, plan.id)
    pending_approval_count = await count_travel_approvals(db, plan.id, "pending")
    rejected_approval_count = await count_travel_approvals(db, plan.id, "rejected")
    if pending_approval_count:
        blockers.append(f"{pending_approval_count} travel approval(s) are still pending.")
    if rejected_approval_count:
        blockers.append(f"{rejected_approval_count} travel approval(s) were rejected.")
    if approval_count == 0:
        warnings.append("No travel approval requirements are recorded.")

    checklist_count = await count_travel_checklist_items(db, plan.id)
    pending_checklist_count = await count_travel_checklist_items(db, plan.id, "pending")
    blocked_checklist_count = await count_travel_checklist_items(db, plan.id, "blocked")
    if pending_checklist_count:
        blockers.append(f"{pending_checklist_count} travel checklist item(s) are still pending.")
    if blocked_checklist_count:
        blockers.append(f"{blocked_checklist_count} travel checklist item(s) are blocked.")
    if checklist_count == 0:
        warnings.append("No travel inspection checklist has been seeded.")

    pending_consent_request_count = 0
    if plan.consent_required:
        pending_consent_request_count = int(
            await db.scalar(
                select(func.count(ConsentRequest.id)).where(
                    ConsentRequest.organization_id == plan.organization_id,
                    ConsentRequest.scope_type == ConsentScopeType.EVENT,
                    ConsentRequest.scope_id == event.id,
                    ConsentRequest.destination == plan.destination,
                    ConsentRequest.status == ConsentRequestStatus.PENDING,
                )
            )
            or 0
        )
        if pending_consent_request_count:
            blockers.append(f"{pending_consent_request_count} guardian travel consent request(s) are pending.")

    ready = not blockers
    return EventTravelReadinessRead(
        event_id=event.id,
        travel_plan_id=plan.id,
        ready=ready,
        recommended_status=TravelPlanStatus.READY if ready else TravelPlanStatus.DRAFT,
        risk_level=risk_level,
        blockers=blockers,
        warnings=warnings,
        approval_count=approval_count,
        pending_approval_count=pending_approval_count,
        rejected_approval_count=rejected_approval_count,
        checklist_count=checklist_count,
        pending_checklist_count=pending_checklist_count,
        blocked_checklist_count=blocked_checklist_count,
        pending_consent_request_count=pending_consent_request_count,
    )


async def optimize_travel_route(
    db: AsyncSession,
    identity: CurrentIdentity,
    travel_plan_id: UUID,
    payload: EventTravelRouteOptimizationCreate,
    authz: AuthorizationService,
) -> EventTravelRouteOptimizationRead:
    plan = await db.get(EventTravelPlan, travel_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel plan not found")
    event = await get_event(db, plan.event_id)
    await ensure_manage_event_scope(authz, plan.organization_id, identity)

    risk_level, risk_assessment = classify_travel_plan(plan)
    warnings = [
        line
        for line in risk_assessment.splitlines()
        if line and not line.startswith("Passenger manifest, staff manifest")
    ]
    stops: list[EventTravelRouteStopRead] = [
        EventTravelRouteStopRead(
            sequence=1,
            stop_type="origin",
            label="Team departure",
            location=travel_origin_label(plan),
            pickup_window_start=plan.departure_at,
            seats=0,
            notes=plan.route_summary,
        )
    ]

    if payload.include_carpools:
        rides = (
            await db.scalars(
                select(EventTravelCarpoolRide)
                .where(
                    EventTravelCarpoolRide.travel_plan_id == plan.id,
                    EventTravelCarpoolRide.status.in_(["open", "matched", "confirmed"]),
                )
                .order_by(
                    EventTravelCarpoolRide.departure_window_start,
                    EventTravelCarpoolRide.pickup_location,
                )
            )
        ).all()
        for ride in rides:
            stops.append(
                EventTravelRouteStopRead(
                    sequence=len(stops) + 1,
                    stop_type=f"carpool_{ride.ride_type}",
                    label=f"{ride.ride_type.title()} pickup",
                    location=ride.pickup_location,
                    pickup_window_start=ride.departure_window_start,
                    pickup_window_end=ride.departure_window_end,
                    seats=ride.seats_available or ride.seats_requested,
                    notes=ride.notes,
                )
            )
        if not rides:
            warnings.append("No open, matched, or confirmed carpool stops are available for route optimization.")

    stops.append(
        EventTravelRouteStopRead(
            sequence=len(stops) + 1,
            stop_type="destination",
            label="Destination",
            location=plan.destination,
            pickup_window_start=plan.return_at,
            seats=0,
            notes=plan.medical_access_plan,
        )
    )
    stops = resequence_stops(stops)
    estimated_duration_minutes = estimate_travel_duration_minutes(payload.strategy, len(stops), risk_level)
    recommended_departure_at = optimized_departure_time(plan.departure_at, stops, estimated_duration_minutes)
    if payload.avoid_weather_risk and risk_level in {TravelRiskLevel.HIGH, TravelRiskLevel.CRITICAL}:
        warnings.append("Use safest routing with weather monitoring, backup stops, and guardian updates before departure.")

    return EventTravelRouteOptimizationRead(
        event_id=event.id,
        travel_plan_id=plan.id,
        strategy=payload.strategy,
        destination=plan.destination,
        stop_count=len(stops),
        recommended_departure_at=recommended_departure_at,
        estimated_duration_minutes=estimated_duration_minutes,
        risk_level=risk_level,
        warnings=warnings,
        route_summary=route_optimization_summary(payload.strategy, stops, estimated_duration_minutes, risk_level),
        stops=stops,
    )


def classify_weather_risk(
    payload: EventWeatherAssessmentCreate,
) -> tuple[WeatherAlertLevel, WeatherDecision, str]:
    critical: list[str] = []
    warnings: list[str] = []
    advisories: list[str] = []

    wbgt = payload.wbgt_c if payload.wbgt_c is not None else payload.heat_index_c
    lightning = payload.lightning_distance_km
    wind = max(value for value in [payload.wind_speed_kph, payload.wind_gust_kph] if value is not None) if (
        payload.wind_speed_kph is not None or payload.wind_gust_kph is not None
    ) else None

    if lightning is not None:
        if lightning < 8:
            critical.append("Lightning is within 8 km: stop activity, clear fields, and shelter immediately.")
        elif lightning < 16:
            warnings.append("Lightning is within 16 km: suspend outdoor activity and prepare 30-minute all-clear clock.")
        elif lightning < 25:
            advisories.append("Lightning is within 25 km: monitor strike trend and keep shelter routes ready.")

    if wbgt is not None:
        if wbgt > 32:
            critical.append("Extreme heat/WBGT above 32C: cancel or move activity indoors.")
        elif wbgt >= 28:
            warnings.append("Heat advisory/WBGT 28-32C: add cooling breaks, reduce intensity, and monitor athletes.")
        elif wbgt >= 25:
            advisories.append("Moderate heat/WBGT 25-28C: increase hydration checks and shade access.")

    if payload.aqi is not None:
        if payload.aqi > 200:
            critical.append("Very unhealthy air quality: cancel outdoor activity for all participants.")
        elif payload.aqi > 150:
            warnings.append("Unhealthy air quality: modify or delay outdoor activity, especially for sensitive athletes.")
        elif payload.aqi > 100:
            advisories.append("Moderate air quality concern: monitor sensitive athletes and reduce high-intensity load.")

    if wind is not None:
        if wind >= 64:
            critical.append("Damaging wind risk: clear exposed areas and secure equipment.")
        elif wind > 40:
            warnings.append("High wind warning: inspect field hazards and avoid elevated or projectile equipment.")
        elif wind >= 25:
            advisories.append("Breezy conditions: monitor loose equipment, tents, signage, and ball flight safety.")

    if payload.precipitation_mm_per_hr is not None:
        if payload.precipitation_mm_per_hr >= 30:
            critical.append("Intense precipitation: suspend activity and assess flooding or surface safety.")
        elif payload.precipitation_mm_per_hr >= 10:
            warnings.append("Heavy rain: inspect footing, visibility, drainage, and travel safety.")
        elif payload.precipitation_mm_per_hr > 0:
            advisories.append("Light precipitation: monitor surface traction and equipment grip.")

    if critical:
        return WeatherAlertLevel.CRITICAL, WeatherDecision.EVACUATE, "\n".join(critical + warnings + advisories)
    if warnings:
        decision = WeatherDecision.DELAY if lightning is not None and lightning < 16 else WeatherDecision.MODIFY
        return WeatherAlertLevel.WARNING, decision, "\n".join(warnings + advisories)
    if advisories:
        return WeatherAlertLevel.ADVISORY, WeatherDecision.MONITOR, "\n".join(advisories)
    return WeatherAlertLevel.INFORMATION, WeatherDecision.PROCEED, "Conditions are within normal operating thresholds."


async def event_participant_person_ids(db: AsyncSession, event: Event) -> list[UUID]:
    attendance_rows = (
        await db.execute(select(AttendanceRecord.person_id).where(AttendanceRecord.event_id == event.id))
    ).all()
    if attendance_rows:
        return [person_id for (person_id,) in attendance_rows]
    if event.team_id is None:
        return []
    roster_rows = (
        await db.execute(
            select(AthleteProfile.person_id)
            .join(TeamRosterEntry, TeamRosterEntry.athlete_profile_id == AthleteProfile.id)
            .where(TeamRosterEntry.team_id == event.team_id)
        )
    ).all()
    return [person_id for (person_id,) in roster_rows]


async def primary_signing_guardian(db: AsyncSession, athlete_person_id: UUID) -> GuardianRelationship | None:
    return await db.scalar(
        select(GuardianRelationship)
        .where(GuardianRelationship.athlete_person_id == athlete_person_id)
        .where(GuardianRelationship.can_sign_consent.is_(True))
        .order_by(GuardianRelationship.is_primary.desc(), GuardianRelationship.created_at)
    )


async def guardian_contact_rows(db: AsyncSession, athlete_person_id: UUID) -> list[tuple[GuardianRelationship, Person]]:
    return list(
        (
            await db.execute(
                select(GuardianRelationship, Person)
                .join(Person, Person.id == GuardianRelationship.guardian_person_id)
                .where(GuardianRelationship.athlete_person_id == athlete_person_id)
                .order_by(GuardianRelationship.is_primary.desc(), Person.display_name)
            )
        ).all()
    )


def guardian_contacts(rows: list[tuple[GuardianRelationship, Person]]) -> list[str]:
    contacts: list[str] = []
    for _, guardian in rows:
        if guardian.primary_email:
            contacts.append(guardian.primary_email)
        if guardian.primary_phone:
            contacts.append(guardian.primary_phone)
    return contacts


async def travel_fee_payer_id(
    db: AsyncSession,
    athlete_person_id: UUID,
    event: Event,
    bill_guardians_for_minors: bool,
) -> UUID | None:
    athlete = await db.get(Person, athlete_person_id)
    if athlete is None:
        return None
    minor = is_minor_on(athlete, event.starts_at.date())
    if bill_guardians_for_minors and minor is not False:
        guardian = await primary_signing_guardian(db, athlete_person_id)
        if guardian is None:
            return None
        return guardian.guardian_person_id
    return athlete_person_id


def travel_fee_invoice_number(plan: EventTravelPlan, billed_person_id: UUID, athlete_person_id: UUID) -> str:
    return f"TRAVEL-{str(plan.id)[:8]}-{str(billed_person_id)[:8]}-{str(athlete_person_id)[:8]}".upper()


def travel_fee_checkout_url(base_url: str, invoice: FinanceInvoice, provider: str) -> str:
    token = sha256(f"{invoice.id}:{invoice.invoice_number}:{invoice.amount_due}:{provider}".encode()).hexdigest()[:24]
    return f"{base_url.rstrip('/')}/{invoice.id}?provider={provider}&token={token}"


async def pending_event_consent_requests(db: AsyncSession, event: Event) -> list[ConsentRequest]:
    return list(
        (
            await db.scalars(
                select(ConsentRequest)
                .where(ConsentRequest.organization_id == event.organization_id)
                .where(ConsentRequest.scope_type == ConsentScopeType.EVENT)
                .where(ConsentRequest.scope_id == event.id)
                .where(ConsentRequest.status == ConsentRequestStatus.PENDING)
                .order_by(ConsentRequest.sent_at.desc())
            )
        ).all()
    )


def decode_upload_content(content_base64: str) -> bytes:
    encoded = content_base64.split(",", 1)[1] if "," in content_base64 else content_base64
    try:
        return b64decode(encoded, validate=True)
    except (Base64Error, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid file encoding") from exc


def safe_upload_filename(filename: str, *, fallback: str) -> str:
    cleaned = sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip(".-")
    return cleaned[:180] or fallback


def travel_fee_invoice_memo(event: Event, plan: EventTravelPlan) -> str:
    parts = [
        f"Trip fee for {event.title}.",
        f"Destination: {plan.destination}.",
        f"Transport: {plan.travel_mode}.",
    ]
    if plan.departure_at is not None:
        parts.append(f"Departure: {plan.departure_at.isoformat()}.")
    if plan.return_at is not None:
        parts.append(f"Return: {plan.return_at.isoformat()}.")
    if plan.route_summary:
        parts.append(f"Route: {plan.route_summary}")
    return "\n".join(parts)[:4000]


def travel_approval_read(approval: EventTravelApproval) -> EventTravelApprovalRead:
    return EventTravelApprovalRead(
        id=approval.id,
        organization_id=approval.organization_id,
        travel_plan_id=approval.travel_plan_id,
        approval_level=approval.approval_level,
        status=approval.status,
        approver_person_id=approval.approver_person_id,
        decided_by_person_id=approval.decided_by_person_id,
        decided_at=approval.decided_at,
        notes=approval.notes,
    )


def recommended_travel_approval_levels(
    plan: EventTravelPlan,
    payload: EventTravelApprovalRoutingCreate,
) -> tuple[list[str], list[str]]:
    risk_level, _ = classify_travel_plan(plan)
    levels: list[str] = []
    rationale: list[str] = []

    if payload.include_operations:
        levels.append("operations")
        rationale.append("Operations approval is required for every managed trip.")
    if payload.include_school and plan.consent_required:
        levels.append("school")
        rationale.append("School or program approval is recommended because guardian consent is required.")
    if payload.include_association and (
        risk_level in {TravelRiskLevel.HIGH, TravelRiskLevel.CRITICAL}
        or contains_any(plan.destination, {"regional", "national", "championship", "tournament"})
        or contains_any(plan.route_weather_risk or "", {"high", "severe", "critical"})
    ):
        levels.append("association")
        rationale.append("Association approval is recommended for elevated-risk or higher-level travel.")
    if payload.include_medical and (
        bool(plan.medical_access_plan)
        or risk_level in {TravelRiskLevel.HIGH, TravelRiskLevel.CRITICAL}
        or contains_any(plan.passenger_manifest or "", {"injury", "medical", "minor"})
    ):
        levels.append("medical")
        rationale.append("Medical approval is recommended because the trip carries health or minor-safety context.")
    estimated_cost = Decimal("0")
    if plan.estimated_cost is not None:
        estimated_cost = Decimal(str(plan.estimated_cost))
    participant_cost = Decimal("0")
    if plan.cost_per_participant is not None:
        participant_cost = Decimal(str(plan.cost_per_participant))
    if payload.include_finance and (estimated_cost >= Decimal("500") or participant_cost > Decimal("0")):
        levels.append("finance")
        rationale.append("Finance approval is recommended because the trip has billable or reimbursable cost.")

    seen: set[str] = set()
    ordered_levels = []
    for level in levels:
        if level not in seen:
            ordered_levels.append(level)
            seen.add(level)
    return ordered_levels, rationale


def contains_any(value: str, needles: set[str]) -> bool:
    lowered = value.lower()
    return any(needle in lowered for needle in needles)


def travel_approval_routing_note(plan: EventTravelPlan, level: str) -> str:
    return (
        f"Automatically routed {level} approval for {plan.destination} travel "
        f"based on risk, consent, cost, and medical context."
    )[:2000]


def travel_checklist_item_read(item: EventTravelChecklistItem) -> EventTravelChecklistItemRead:
    return EventTravelChecklistItemRead(
        id=item.id,
        organization_id=item.organization_id,
        travel_plan_id=item.travel_plan_id,
        checklist_type=item.checklist_type,
        item_label=item.item_label,
        status=item.status,
        completed_by_person_id=item.completed_by_person_id,
        completed_at=item.completed_at,
        evidence_url=item.evidence_url,
        notes=item.notes,
    )


def travel_expense_read(expense: EventTravelExpense) -> EventTravelExpenseRead:
    return EventTravelExpenseRead(
        id=expense.id,
        organization_id=expense.organization_id,
        travel_plan_id=expense.travel_plan_id,
        category=expense.category,
        vendor=expense.vendor,
        amount=expense.amount,
        currency=expense.currency,
        incurred_at=expense.incurred_at,
        paid_by_person_id=expense.paid_by_person_id,
        reimbursement_status=expense.reimbursement_status,
        approved_by_person_id=expense.approved_by_person_id,
        reimbursed_at=expense.reimbursed_at,
        receipt_url=expense.receipt_url,
        notes=expense.notes,
    )


def travel_carpool_ride_read(ride: EventTravelCarpoolRide) -> EventTravelCarpoolRideRead:
    return EventTravelCarpoolRideRead(
        id=ride.id,
        organization_id=ride.organization_id,
        travel_plan_id=ride.travel_plan_id,
        ride_type=ride.ride_type,
        status=ride.status,
        rider_person_id=ride.rider_person_id,
        driver_person_id=ride.driver_person_id,
        pickup_location=ride.pickup_location,
        dropoff_location=ride.dropoff_location,
        seats_requested=ride.seats_requested,
        seats_available=ride.seats_available,
        departure_window_start=ride.departure_window_start,
        departure_window_end=ride.departure_window_end,
        match_score=ride.match_score,
        matched_at=ride.matched_at,
        notes=ride.notes,
    )


def travel_carpool_match_score(request: EventTravelCarpoolRide, offer: EventTravelCarpoolRide) -> Decimal:
    pickup_score = token_overlap_score(request.pickup_location, offer.pickup_location)
    dropoff_score = token_overlap_score(request.dropoff_location or "", offer.dropoff_location or "")
    if not request.dropoff_location or not offer.dropoff_location:
        dropoff_score = Decimal("0.50")
    location_score = (pickup_score * Decimal("0.75")) + (dropoff_score * Decimal("0.25"))
    seats_score = Decimal("1.00") if offer.seats_available >= request.seats_requested else Decimal("0.00")
    window_score = carpool_window_score(request, offer)
    score = (
        location_score * Decimal("55")
        + window_score * Decimal("30")
        + seats_score * Decimal("15")
    )
    return score.quantize(Decimal("0.01"))


def token_overlap_score(left: str, right: str) -> Decimal:
    left_tokens = location_tokens(left)
    right_tokens = location_tokens(right)
    if not left_tokens or not right_tokens:
        return Decimal("0.25")
    overlap = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    if union == 0:
        return Decimal("0")
    return Decimal(overlap) / Decimal(union)


def location_tokens(value: str) -> set[str]:
    cleaned = sub(r"[^a-z0-9]+", " ", value.lower())
    return {token for token in cleaned.split() if len(token) > 2}


def carpool_window_score(request: EventTravelCarpoolRide, offer: EventTravelCarpoolRide) -> Decimal:
    if (
        request.departure_window_start is None
        or request.departure_window_end is None
        or offer.departure_window_start is None
        or offer.departure_window_end is None
    ):
        return Decimal("0.50")
    latest_start = max(request.departure_window_start, offer.departure_window_start)
    earliest_end = min(request.departure_window_end, offer.departure_window_end)
    if latest_start <= earliest_end:
        return Decimal("1.00")
    gap_minutes = abs((latest_start - earliest_end).total_seconds()) / 60
    if gap_minutes <= 15:
        return Decimal("0.80")
    if gap_minutes <= 30:
        return Decimal("0.60")
    if gap_minutes <= 60:
        return Decimal("0.35")
    return Decimal("0.10")


def location_match_summary(request: EventTravelCarpoolRide, offer: EventTravelCarpoolRide) -> str:
    overlap = location_tokens(request.pickup_location) & location_tokens(offer.pickup_location)
    if overlap:
        return f"Shared pickup terms: {', '.join(sorted(overlap))}"
    return "Pickup locations require manual review."


def window_match_summary(request: EventTravelCarpoolRide, offer: EventTravelCarpoolRide) -> str:
    if request.departure_window_start is None or offer.departure_window_start is None:
        return "One or both rides have no pickup window."
    score = carpool_window_score(request, offer)
    if score == Decimal("1.00"):
        return "Pickup windows overlap."
    return "Pickup windows are near but do not overlap."


def append_note(existing: str | None, addition: str) -> str:
    return f"{existing}\n{addition}"[:2000] if existing else addition[:2000]


async def count_travel_approvals(db: AsyncSession, travel_plan_id: UUID, status_value: str | None = None) -> int:
    query = select(func.count(EventTravelApproval.id)).where(EventTravelApproval.travel_plan_id == travel_plan_id)
    if status_value is not None:
        query = query.where(EventTravelApproval.status == status_value)
    return int(await db.scalar(query) or 0)


async def count_travel_checklist_items(db: AsyncSession, travel_plan_id: UUID, status_value: str | None = None) -> int:
    query = select(func.count(EventTravelChecklistItem.id)).where(EventTravelChecklistItem.travel_plan_id == travel_plan_id)
    if status_value is not None:
        query = query.where(EventTravelChecklistItem.status == status_value)
    return int(await db.scalar(query) or 0)


def travel_origin_label(plan: EventTravelPlan) -> str:
    if plan.route_summary:
        return plan.route_summary.splitlines()[0][:240]
    if plan.staff_manifest:
        return "Team assembly point from staff manifest"
    return "Team assembly point"


def resequence_stops(stops: list[EventTravelRouteStopRead]) -> list[EventTravelRouteStopRead]:
    carpool_stops = sorted(
        [stop for stop in stops if stop.stop_type.startswith("carpool")],
        key=lambda stop: (stop.pickup_window_start or datetime.max.replace(tzinfo=UTC), stop.location),
    )
    ordered = [
        *[stop for stop in stops if stop.stop_type == "origin"],
        *carpool_stops,
        *[stop for stop in stops if stop.stop_type == "destination"],
    ]
    return [stop.model_copy(update={"sequence": index}) for index, stop in enumerate(ordered, start=1)]


def estimate_travel_duration_minutes(strategy: str, stop_count: int, risk_level: TravelRiskLevel) -> int:
    base_minutes = 30 if strategy == "fastest" else 45
    per_stop_minutes = 6 if strategy == "fastest" else 10
    if strategy == "safest":
        base_minutes += 20
        per_stop_minutes += 4
    if strategy == "carpool_dense":
        per_stop_minutes += 8
    if risk_level == TravelRiskLevel.HIGH:
        base_minutes += 20
    if risk_level == TravelRiskLevel.CRITICAL:
        base_minutes += 45
    return base_minutes + max(stop_count - 1, 0) * per_stop_minutes


def optimized_departure_time(
    planned_departure_at: datetime | None,
    stops: list[EventTravelRouteStopRead],
    estimated_duration_minutes: int,
) -> datetime | None:
    pickup_times = [stop.pickup_window_start for stop in stops if stop.pickup_window_start is not None]
    if pickup_times:
        return min(pickup_times)
    if planned_departure_at is None:
        return None
    return planned_departure_at - timedelta(minutes=max(estimated_duration_minutes - 30, 0))


def route_optimization_summary(
    strategy: str,
    stops: list[EventTravelRouteStopRead],
    estimated_duration_minutes: int,
    risk_level: TravelRiskLevel,
) -> str:
    stop_labels = " -> ".join(stop.location for stop in stops[:5])
    if len(stops) > 5:
        stop_labels += f" -> +{len(stops) - 5} more"
    return (
        f"{strategy.replace('_', ' ')} route with {len(stops)} stops, "
        f"estimated {estimated_duration_minutes} minutes, {risk_level.value} travel risk: {stop_labels}"
    )


async def travel_location_update_read(
    db: AsyncSession,
    update: EventTravelLocationUpdate,
) -> EventTravelLocationUpdateRead:
    recipient_count = 0
    if update.notification_message_id is not None:
        recipient_count = int(
            await db.scalar(
                select(func.count(MessageRecipient.id)).where(
                    MessageRecipient.message_id == update.notification_message_id
                )
            )
            or 0
        )
    return EventTravelLocationUpdateRead(
        id=update.id,
        organization_id=update.organization_id,
        travel_plan_id=update.travel_plan_id,
        phase=update.phase,
        source=update.source,
        recorded_at=update.recorded_at,
        recorded_by_person_id=update.recorded_by_person_id,
        latitude=update.latitude,
        longitude=update.longitude,
        speed_kph=update.speed_kph,
        heading_degrees=update.heading_degrees,
        notification_message_id=update.notification_message_id,
        notification_recipient_count=recipient_count,
        notes=update.notes,
    )


def travel_device_read(device: EventTravelDevice) -> EventTravelDeviceRead:
    return EventTravelDeviceRead(
        id=device.id,
        organization_id=device.organization_id,
        travel_plan_id=device.travel_plan_id,
        provider=device.provider,
        device_id=device.device_id,
        label=device.label,
        status=device.status,
        assigned_vehicle=device.assigned_vehicle,
        installed_at=device.installed_at,
        last_seen_at=device.last_seen_at,
        last_location_update_id=device.last_location_update_id,
        last_battery_percent=device.last_battery_percent,
        last_accuracy_meters=device.last_accuracy_meters,
        notes=device.notes,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


def apply_travel_phase_status(plan: EventTravelPlan, phase: str) -> None:
    if phase in {"departed", "en_route", "delayed", "arrived"} and plan.status not in {
        TravelPlanStatus.COMPLETED,
        TravelPlanStatus.CANCELLED,
    }:
        plan.status = TravelPlanStatus.IN_PROGRESS
    if phase == "returned":
        plan.status = TravelPlanStatus.COMPLETED


def travel_device_location_notes(
    payload: EventTravelDeviceLocationIngestCreate,
    signature_required: bool,
    signature_validated: bool,
) -> str:
    lines = [
        f"Hardware GPS ingest from {payload.provider} device {payload.device_id}.",
        f"Signature required: {signature_required}; validated: {signature_validated}.",
    ]
    if payload.accuracy_meters is not None:
        lines.append(f"Accuracy: {payload.accuracy_meters}m.")
    if payload.battery_percent is not None:
        lines.append(f"Battery: {payload.battery_percent}%.")
    if payload.external_event_id:
        lines.append(f"External event: {payload.external_event_id}.")
    if payload.notes:
        lines.append(payload.notes)
    return "\n".join(lines)[:2000]


def travel_distance_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    radius_km = 6371.0
    d_latitude = radians(latitude_b - latitude_a)
    d_longitude = radians(longitude_b - longitude_a)
    start_latitude = radians(latitude_a)
    end_latitude = radians(latitude_b)
    haversine = (
        sin(d_latitude / 2) ** 2
        + cos(start_latitude) * cos(end_latitude) * sin(d_longitude / 2) ** 2
    )
    return 2 * radius_km * asin(min(1.0, sqrt(haversine)))


def travel_location_subject(event: Event, plan: EventTravelPlan, phase: str) -> str:
    label = {
        "departed": "departed",
        "delayed": "delayed",
        "arrived": "arrived",
        "returned": "returned",
    }.get(phase, "updated")
    return f"{event.title} travel {label}"[:240]


def travel_location_body(event: Event, plan: EventTravelPlan, update: EventTravelLocationUpdate) -> str:
    parts = [
        f"Travel update for {event.title}.",
        f"Destination: {plan.destination}.",
        f"Status: {update.phase}.",
        f"Location: {update.latitude}, {update.longitude}.",
        f"Recorded: {update.recorded_at.isoformat()}.",
    ]
    if update.speed_kph is not None:
        parts.append(f"Speed: {update.speed_kph} kph.")
    if update.notes:
        parts.append(update.notes)
    return "\n".join(parts)[:4000]


def travel_geofence_subject(event: Event, plan: EventTravelPlan, label: str) -> str:
    return f"{event.title} travel outside {label}: {plan.destination}"[:240]


def travel_geofence_body(
    event: Event,
    plan: EventTravelPlan,
    update: EventTravelLocationUpdate,
    payload: EventTravelGeofenceCheckCreate,
    distance_km: Decimal,
) -> str:
    parts = [
        f"Travel geofence alert for {event.title}.",
        f"Destination: {plan.destination}.",
        f"Zone: {payload.label}.",
        f"Latest location: {update.latitude}, {update.longitude}.",
        f"Zone center: {payload.center_latitude}, {payload.center_longitude}.",
        f"Distance from center: {distance_km} km; allowed radius: {payload.radius_km} km.",
        f"Recorded: {update.recorded_at.isoformat()}.",
        "Recommended action: contact the driver, verify passenger safety, and update guardians if routing changed.",
    ]
    if update.notes:
        parts.append(update.notes)
    return "\n".join(parts)[:4000]


def travel_geofence_recommendation(breached: bool, radius_km: Decimal, distance_km: Decimal) -> str:
    if breached:
        overage = max(distance_km - radius_km, Decimal("0"))
        return (
            f"Outside the configured zone by {overage} km. "
            "Confirm route, driver status, and whether emergency escalation is needed."
        )
    return "Latest travel position is inside the configured geofence. Continue normal monitoring."


def travel_consent_notes(event: Event, plan: EventTravelPlan) -> str:
    parts = [
        f"Travel consent for {event.title}.",
        f"Destination: {plan.destination}.",
        f"Transport: {plan.travel_mode}.",
    ]
    if plan.departure_at is not None:
        parts.append(f"Departure: {plan.departure_at.isoformat()}.")
    if plan.return_at is not None:
        parts.append(f"Return: {plan.return_at.isoformat()}.")
    if plan.route_summary:
        parts.append(f"Route: {plan.route_summary}")
    if plan.emergency_contacts:
        parts.append(f"Emergency contacts: {plan.emergency_contacts}")
    if plan.medical_access_plan:
        parts.append(f"Medical access: {plan.medical_access_plan}")
    if plan.cost_per_participant is not None:
        parts.append(f"Estimated participant cost: {plan.cost_per_participant}.")
    return "\n".join(parts)[:2000]


def travel_consent_reminder_subject(event: Event) -> str:
    return f"Travel consent needed: {event.title}"[:240]


def travel_consent_reminder_body(event: Event, plan: EventTravelPlan, pending_count: int) -> str:
    parts = [
        f"Please review the pending travel consent request for {event.title}.",
        f"Destination: {plan.destination}.",
        f"Pending requests: {pending_count}.",
        "Open the family portal or the one-use consent link already sent to respond.",
    ]
    if plan.departure_at is not None:
        parts.append(f"Departure: {plan.departure_at.isoformat()}.")
    if plan.consent_due_at is not None:
        parts.append(f"Consent due: {plan.consent_due_at.isoformat()}.")
    if plan.emergency_contacts:
        parts.append(f"Emergency contacts: {plan.emergency_contacts}")
    return "\n".join(parts)[:4000]


def scheduled_travel_consent_reminder_subject(event: Event) -> str:
    return f"Travel consent deadline approaching: {event.title}"[:240]


def scheduled_travel_consent_reminder_body(
    event: Event,
    due_plans: list[EventTravelPlan],
    pending_count: int,
) -> str:
    parts = [
        f"Automated travel consent reminder for {event.title}.",
        f"Pending consent requests: {pending_count}.",
        "Please open the family portal or the one-use consent link already sent to respond.",
    ]
    for plan in due_plans[:5]:
        due = plan.consent_due_at.isoformat() if plan.consent_due_at is not None else "not set"
        parts.append(f"- {plan.destination} by {plan.travel_mode}; consent due {due}.")
    if len(due_plans) > 5:
        parts.append(f"- {len(due_plans) - 5} additional travel plan(s) are also due soon.")
    return "\n".join(parts)[:4000]


def slugify_filename(value: str) -> str:
    cleaned = "".join(character.lower() if character.isalnum() else "-" for character in value)
    return "-".join(part for part in cleaned.split("-") if part)[:80] or "travel"


def csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    escaped = text.replace('"', '""')
    return f'"{escaped}"'


def travel_manifest_csv(manifest: EventTravelManifestRead) -> str:
    rows = [
        ["person_id", "display_name", "guardian_names", "guardian_contacts", "medical_clearance", "medical_reason"]
    ]
    rows.extend(
        [
            str(participant.person_id),
            participant.display_name,
            "; ".join(participant.guardian_names),
            "; ".join(participant.guardian_contacts),
            participant.medical_clearance_status.value if participant.medical_clearance_status else "",
            participant.medical_clearance_reason,
        ]
        for participant in manifest.participants
    )
    return "\n".join(",".join(csv_cell(cell) for cell in row) for row in rows)


def travel_manifest_text(manifest: EventTravelManifestRead) -> str:
    lines = [
        f"Travel manifest: {manifest.destination}",
        f"Participants: {manifest.participant_count}",
        f"Emergency contacts: {manifest.emergency_contacts or 'not set'}",
        f"Medical access: {manifest.medical_access_plan or 'not set'}",
        "",
    ]
    for participant in manifest.participants:
        lines.extend(
            [
                participant.display_name,
                f"  Person: {participant.person_id}",
                f"  Guardians: {'; '.join(participant.guardian_names) or 'none listed'}",
                f"  Contacts: {'; '.join(participant.guardian_contacts) or 'none listed'}",
                f"  Medical: {participant.medical_clearance_status or 'not reviewed'} - {participant.medical_clearance_reason}",
            ]
        )
    return "\n".join(lines)


def travel_manifest_artifact(manifest: EventTravelManifestRead, format_value: str) -> tuple[str, str, bytes]:
    if format_value == "csv":
        return (
            f"travel-manifest-{slugify_filename(manifest.destination)}.csv",
            "text/csv",
            travel_manifest_csv(manifest).encode(),
        )
    if format_value == "pdf":
        return (
            f"travel-manifest-{slugify_filename(manifest.destination)}.pdf",
            "application/pdf",
            travel_manifest_pdf(manifest),
        )
    return (
        f"travel-manifest-{slugify_filename(manifest.destination)}.txt",
        "text/plain",
        travel_manifest_text(manifest).encode(),
    )


def travel_manifest_pdf(manifest: EventTravelManifestRead) -> bytes:
    body_lines = travel_manifest_pdf_lines(manifest)
    chunks = [body_lines[index : index + 44] for index in range(0, len(body_lines), 44)] or [[]]
    page_objects: list[bytes] = []
    page_ids: list[int] = []
    total_pages = len(chunks)
    for page_index, chunk in enumerate(chunks):
        page_id = 4 + page_index * 2
        stream_id = page_id + 1
        page_ids.append(page_id)
        page_lines = [
            f"Travel manifest: {manifest.destination}",
            f"Page {page_index + 1} of {total_pages}",
            "",
            *chunk,
        ]
        text_commands = ["BT", "/F1 9 Tf", "54 748 Td"]
        for line_index, line in enumerate(page_lines):
            if line_index:
                text_commands.append("0 -13 Td")
            text_commands.append(f"({travel_manifest_pdf_escape(line[:112])}) Tj")
        text_commands.append("ET")
        stream = "\n".join(text_commands).encode()
        page_objects.extend(
            [
                (
                    f"{page_id} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                    f"/Resources << /Font << /F1 3 0 R >> >> /Contents {stream_id} 0 R >> endobj\n"
                ).encode(),
                (
                    f"{stream_id} 0 obj << /Length {len(stream)} >> stream\n".encode()
                    + stream
                    + b"\nendstream endobj\n"
                ),
            ]
        )
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        f"2 0 obj << /Type /Pages /Kids [{kids}] /Count {total_pages} >> endobj\n".encode(),
        b"3 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        *page_objects,
    ]
    output = io.BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets = [0]
    for item in objects:
        offsets.append(output.tell())
        output.write(item)
    xref_at = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode())
    output.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode())
    output.write(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode()
    )
    return output.getvalue()


def travel_manifest_pdf_lines(manifest: EventTravelManifestRead) -> list[str]:
    lines = [
        f"Participants: {manifest.participant_count}",
        f"Emergency contacts: {manifest.emergency_contacts or 'not set'}",
        f"Medical access: {manifest.medical_access_plan or 'not set'}",
        "",
        "Participants",
    ]
    for participant in manifest.participants:
        medical_status = participant.medical_clearance_status.value if participant.medical_clearance_status else "not reviewed"
        lines.extend(
            [
                f"- {participant.display_name} ({participant.person_id})",
                f"  Guardians: {'; '.join(participant.guardian_names) or 'none listed'}",
                f"  Contacts: {'; '.join(participant.guardian_contacts) or 'none listed'}",
                f"  Medical: {medical_status} - {participant.medical_clearance_reason}",
            ]
        )
    return lines


def travel_manifest_pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def signed_travel_manifest_url(
    settings: Settings,
    organization_id: UUID,
    travel_plan_id: UUID,
    storage_name: str,
    expires_at: datetime,
) -> str:
    expires = int(expires_at.timestamp())
    signature = travel_manifest_signature(settings, organization_id, travel_plan_id, storage_name, expires)
    safe_name = quote(storage_name, safe="")
    return (
        f"{settings.api_prefix}/events/travel-manifests/{organization_id}/{travel_plan_id}/{safe_name}"
        f"?expires={expires}&signature={signature}"
    )


def travel_manifest_signature(
    settings: Settings,
    organization_id: UUID,
    travel_plan_id: UUID,
    storage_name: str,
    expires: int,
) -> str:
    payload = f"{organization_id}/{travel_plan_id}/{storage_name}:{expires}"
    digest = hmac.new(travel_manifest_signing_key(settings), payload.encode(), sha256).digest()
    return urlsafe_b64encode(digest).decode().rstrip("=")


def travel_manifest_signing_key(settings: Settings) -> bytes:
    key = settings.travel_manifest_signing_key or settings.report_artifact_signing_key or settings.agent_webhook_key
    return (key or "local-travel-manifest-key").encode()


def travel_manifest_content_type(storage_name: str) -> str:
    if storage_name.endswith(".csv"):
        return "text/csv"
    if storage_name.endswith(".pdf"):
        return "application/pdf"
    return "text/plain"


def public_manifest_filename(storage_name: str) -> str:
    parts = storage_name.split("-", 1)
    return parts[1] if len(parts) == 2 else storage_name


def classify_travel_risk(payload: EventTravelPlanCreate) -> tuple[TravelRiskLevel, str]:
    class DraftPlan:
        route_weather_risk = payload.route_weather_risk
        driver_certification_status = payload.driver_certification_status
        vehicle_inspection_status = payload.vehicle_inspection_status
        lodging_details = payload.lodging_details
        emergency_contacts = payload.emergency_contacts
        medical_access_plan = payload.medical_access_plan
        consent_required = payload.consent_required
        consent_due_at = payload.consent_due_at
        departure_at = payload.departure_at
        travel_mode = payload.travel_mode

    return classify_travel_plan(DraftPlan())


def classify_travel_plan(plan) -> tuple[TravelRiskLevel, str]:
    blockers: list[str] = []
    warnings: list[str] = []
    checks: list[str] = []

    if plan.route_weather_risk and plan.route_weather_risk.lower() in {"critical", "severe", "storm", "flood"}:
        blockers.append("Route weather risk requires reroute, delay, or emergency travel approval.")
    elif plan.route_weather_risk and plan.route_weather_risk.lower() in {"high", "warning", "moderate"}:
        warnings.append("Route weather should be monitored with backup stops and parent updates.")

    if not plan.driver_certification_status:
        warnings.append("Driver certification status is missing.")
    elif plan.driver_certification_status.lower() not in {"verified", "current", "valid", "cleared"}:
        blockers.append("Driver certification is not verified as current.")

    if not plan.vehicle_inspection_status:
        warnings.append("Vehicle inspection status is missing.")
    elif plan.vehicle_inspection_status.lower() not in {"passed", "current", "valid", "complete"}:
        blockers.append("Vehicle inspection is not marked current or passed.")

    if plan.consent_required and plan.consent_due_at is None:
        warnings.append("Travel consent is required but no due time is set.")
    if plan.travel_mode.lower() in {"bus", "van", "minibus", "carpool"} and not plan.emergency_contacts:
        warnings.append("Emergency contacts should be attached before departure.")
    if not plan.medical_access_plan:
        warnings.append("Medical access plan is missing for the trip.")
    if plan.departure_at is None:
        warnings.append("Departure time is missing.")
    if plan.lodging_details and "chaperone" not in plan.lodging_details.lower():
        warnings.append("Lodging details should explicitly name chaperone coverage.")

    checks.append("Passenger manifest, staff manifest, route, vehicle, driver, consent, and medical access reviewed.")
    if blockers:
        return TravelRiskLevel.CRITICAL, "\n".join(blockers + warnings + checks)
    if len(warnings) >= 3:
        return TravelRiskLevel.HIGH, "\n".join(warnings + checks)
    if warnings:
        return TravelRiskLevel.MEDIUM, "\n".join(warnings + checks)
    return TravelRiskLevel.LOW, "\n".join(checks)


def weather_alert_subject(event: Event, assessment: EventWeatherAssessment) -> str:
    return f"Weather {assessment.alert_level.value}: {event.title}"[:240]


def weather_alert_body(event: Event, assessment: EventWeatherAssessment) -> str:
    lines = [
        f"Event: {event.title}",
        f"Venue: {event.venue_name or 'not specified'}",
        f"Weather alert: {assessment.alert_level.value}",
        f"Decision: {assessment.decision.value}",
        f"Observed at: {assessment.observed_at.isoformat()}",
    ]
    metrics = [
        f"WBGT {assessment.wbgt_c}C" if assessment.wbgt_c is not None else None,
        f"Heat index {assessment.heat_index_c}C" if assessment.heat_index_c is not None else None,
        f"AQI {assessment.aqi}" if assessment.aqi is not None else None,
        f"Lightning {assessment.lightning_distance_km} km" if assessment.lightning_distance_km is not None else None,
        f"Wind gust {assessment.wind_gust_kph} kph" if assessment.wind_gust_kph is not None else None,
        (
            f"Precipitation {assessment.precipitation_mm_per_hr} mm/hr"
            if assessment.precipitation_mm_per_hr is not None
            else None
        ),
    ]
    metric_line = "; ".join(metric for metric in metrics if metric)
    if metric_line:
        lines.append(f"Conditions: {metric_line}")
    lines.append(f"Actions: {assessment.recommended_actions}")
    if assessment.notes:
        lines.append(f"Notes: {assessment.notes}")
    return "\n".join(lines)[:8000]


async def record_attendance(
    db: AsyncSession,
    identity: CurrentIdentity,
    event_id: UUID,
    payload: AttendanceRecordUpsert,
    authz: AuthorizationService,
) -> AttendanceResult:
    event = await get_event(db, event_id)
    await ensure_manage_event_scope(authz, event.organization_id, identity)
    person = await db.get(Person, payload.person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    clearance_status: ParticipationClearanceStatus | None = None
    medical_clearance_status: MedicalClearanceStatus | None = None
    medical_clearance_id: UUID | None = None
    medical_clearance_reason: str | None = None
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
        (
            medical_gate_status,
            medical_clearance_status,
            medical_clearance_id,
            medical_clearance_reason,
        ) = await medical_clearance_for_event(db, event_id, payload.person_id)
        if medical_gate_status != ParticipationClearanceStatus.CLEARED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "clearance_status": medical_gate_status.value,
                    "medical_clearance_status": medical_clearance_status.value
                    if medical_clearance_status is not None
                    else None,
                    "medical_clearance_id": str(medical_clearance_id)
                    if medical_clearance_id is not None
                    else None,
                    "reason": medical_clearance_reason,
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
        return (
            existing,
            clearance_status,
            medical_clearance_status,
            medical_clearance_id,
            medical_clearance_reason,
        )

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
    return (
        attendance,
        clearance_status,
        medical_clearance_status,
        medical_clearance_id,
        medical_clearance_reason,
    )


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
