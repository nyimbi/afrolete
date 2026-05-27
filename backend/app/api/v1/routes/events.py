from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.event import (
    AttendanceRecordRead,
    AttendanceRecordUpsert,
    AttendanceSeedRead,
    EventCreate,
    EventRead,
    EventWeatherAlertCreate,
    EventWeatherAlertRead,
    EventWeatherAssessmentCreate,
    EventWeatherAssessmentRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.events import (
    create_weather_assessment,
    create_event,
    dispatch_weather_assessment_alert,
    get_event,
    list_attendance,
    list_events,
    list_weather_assessments,
    record_attendance,
    seed_attendance_from_team_roster,
)
from app.services.safeguarding import medical_clearance_for_event

router = APIRouter(prefix="/events", tags=["events"])


def to_event_read(event) -> EventRead:
    return EventRead(
        id=event.id,
        organization_id=event.organization_id,
        team_id=event.team_id,
        event_type=event.event_type,
        title=event.title,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        timezone=event.timezone,
        venue_name=event.venue_name,
        notes=event.notes,
    )


def to_weather_assessment_read(assessment) -> EventWeatherAssessmentRead:
    return EventWeatherAssessmentRead(
        id=assessment.id,
        organization_id=assessment.organization_id,
        event_id=assessment.event_id,
        source=assessment.source,
        observed_at=assessment.observed_at,
        temperature_c=float(assessment.temperature_c) if assessment.temperature_c is not None else None,
        heat_index_c=float(assessment.heat_index_c) if assessment.heat_index_c is not None else None,
        wbgt_c=float(assessment.wbgt_c) if assessment.wbgt_c is not None else None,
        humidity_percent=float(assessment.humidity_percent) if assessment.humidity_percent is not None else None,
        aqi=assessment.aqi,
        lightning_distance_km=(
            float(assessment.lightning_distance_km) if assessment.lightning_distance_km is not None else None
        ),
        wind_speed_kph=float(assessment.wind_speed_kph) if assessment.wind_speed_kph is not None else None,
        wind_gust_kph=float(assessment.wind_gust_kph) if assessment.wind_gust_kph is not None else None,
        precipitation_mm_per_hr=(
            float(assessment.precipitation_mm_per_hr) if assessment.precipitation_mm_per_hr is not None else None
        ),
        alert_level=assessment.alert_level,
        decision=assessment.decision,
        recommended_actions=assessment.recommended_actions,
        notes=assessment.notes,
    )


def to_weather_alert_read(message, recipient_count: int, event_id: UUID, assessment_id: UUID) -> EventWeatherAlertRead:
    return EventWeatherAlertRead(
        event_id=event_id,
        assessment_id=assessment_id,
        message_id=message.id,
        recipient_count=recipient_count,
        channel=message.channel,
        subject=message.subject,
        urgent=message.urgent,
    )


def to_attendance_read(
    attendance,
    clearance_status=None,
    medical_clearance_status=None,
    medical_clearance_id=None,
    medical_clearance_reason=None,
) -> AttendanceRecordRead:
    return AttendanceRecordRead(
        id=attendance.id,
        event_id=attendance.event_id,
        person_id=attendance.person_id,
        status=attendance.status,
        recorded_by_person_id=attendance.recorded_by_person_id,
        guardian_consent_id=attendance.guardian_consent_id,
        note=attendance.note,
        clearance_status=clearance_status,
        medical_clearance_status=medical_clearance_status,
        medical_clearance_id=medical_clearance_id,
        medical_clearance_reason=medical_clearance_reason,
    )


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event_route(
    payload: EventCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventRead:
    return to_event_read(await create_event(db, identity, payload, authz))


@router.get("", response_model=list[EventRead])
async def list_events_route(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[EventRead]:
    return [to_event_read(event) for event in await list_events(db, organization_id, team_id)]


@router.get("/{event_id}", response_model=EventRead)
async def get_event_route(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EventRead:
    return to_event_read(await get_event(db, event_id))


@router.post(
    "/{event_id}/weather-assessments",
    response_model=EventWeatherAssessmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_weather_assessment_route(
    event_id: UUID,
    payload: EventWeatherAssessmentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventWeatherAssessmentRead:
    return to_weather_assessment_read(
        await create_weather_assessment(db, identity, event_id, payload, authz)
    )


@router.get("/{event_id}/weather-assessments", response_model=list[EventWeatherAssessmentRead])
async def list_weather_assessments_route(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[EventWeatherAssessmentRead]:
    return [
        to_weather_assessment_read(assessment)
        for assessment in await list_weather_assessments(db, event_id)
    ]


@router.post(
    "/{event_id}/weather-assessments/{assessment_id}/alerts",
    response_model=EventWeatherAlertRead,
    status_code=status.HTTP_201_CREATED,
)
async def dispatch_weather_alert_route(
    event_id: UUID,
    assessment_id: UUID,
    payload: EventWeatherAlertCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventWeatherAlertRead:
    message, recipient_count = await dispatch_weather_assessment_alert(
        db,
        identity,
        event_id,
        assessment_id,
        payload,
        authz,
    )
    return to_weather_alert_read(message, recipient_count, event_id, assessment_id)


@router.post("/{event_id}/attendance", response_model=AttendanceRecordRead, status_code=201)
async def record_attendance_route(
    event_id: UUID,
    payload: AttendanceRecordUpsert,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AttendanceRecordRead:
    (
        attendance,
        clearance_status,
        medical_clearance_status,
        medical_clearance_id,
        medical_clearance_reason,
    ) = await record_attendance(db, identity, event_id, payload, authz)
    return to_attendance_read(
        attendance,
        clearance_status,
        medical_clearance_status,
        medical_clearance_id,
        medical_clearance_reason,
    )


@router.get("/{event_id}/attendance", response_model=list[AttendanceRecordRead])
async def list_attendance_route(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[AttendanceRecordRead]:
    records = []
    for attendance in await list_attendance(db, event_id):
        _, medical_status, medical_id, medical_reason = await medical_clearance_for_event(
            db,
            event_id,
            attendance.person_id,
        )
        records.append(
            to_attendance_read(
                attendance,
                medical_clearance_status=medical_status,
                medical_clearance_id=medical_id,
                medical_clearance_reason=medical_reason,
            )
        )
    return records


@router.post("/{event_id}/attendance/from-roster", response_model=AttendanceSeedRead)
async def seed_attendance_from_roster_route(
    event_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AttendanceSeedRead:
    created, existing = await seed_attendance_from_team_roster(db, identity, event_id, authz)
    return AttendanceSeedRead(event_id=event_id, created=created, existing=existing)
