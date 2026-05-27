from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import CommunicationMessage, MessageRecipient
from app.models.enums import (
    AttendanceStatus,
    CommunicationMessageType,
    CommunicationScopeType,
    MedicalClearanceStatus,
    ParticipationClearanceStatus,
    TravelRiskLevel,
    WeatherAlertLevel,
    WeatherDecision,
)
from app.models.event import AttendanceRecord, Event, EventTravelPlan, EventWeatherAssessment
from app.models.identity import Person
from app.models.organization import Organization
from app.models.team import AthleteProfile, Team, TeamRosterEntry
from app.schemas.communication import CommunicationMessageCreate
from app.schemas.event import (
    EventCreate,
    EventTravelPlanCreate,
    EventTravelPlanUpdate,
    EventWeatherAlertCreate,
    EventWeatherAssessmentCreate,
    AttendanceRecordUpsert,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship
from app.services.communications import create_message
from app.services.safeguarding import clearance_for_event, medical_clearance_for_event


PARTICIPATION_STATUSES = {AttendanceStatus.CONFIRMED, AttendanceStatus.PRESENT}
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
