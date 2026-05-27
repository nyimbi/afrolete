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
    EventTravelApprovalCreate,
    EventTravelApprovalRead,
    EventTravelApprovalUpdate,
    EventTravelCarpoolRideCreate,
    EventTravelCarpoolRideRead,
    EventTravelCarpoolRideUpdate,
    EventTravelChecklistItemRead,
    EventTravelChecklistItemUpdate,
    EventTravelChecklistSeedCreate,
    EventTravelConsentBatchRead,
    EventTravelConsentReminderCreate,
    EventTravelConsentReminderRead,
    EventTravelConsentRequestCreate,
    EventTravelExpenseCreate,
    EventTravelExpenseRead,
    EventTravelExpenseUpdate,
    EventTravelFeeInvoiceBatchRead,
    EventTravelFeeInvoiceCreate,
    EventTravelLocationUpdateCreate,
    EventTravelLocationUpdateRead,
    EventTravelManifestExportCreate,
    EventTravelManifestExportRead,
    EventTravelManifestRead,
    EventTravelPlanCreate,
    EventTravelPlanRead,
    EventTravelPlanUpdate,
    EventTravelReadinessRead,
    EventTravelRouteOptimizationCreate,
    EventTravelRouteOptimizationRead,
    EventWeatherAlertCreate,
    EventWeatherAlertRead,
    EventWeatherAssessmentCreate,
    EventWeatherAssessmentRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.events import (
    create_travel_plan,
    create_weather_assessment,
    create_event,
    dispatch_weather_assessment_alert,
    create_travel_approval,
    create_travel_carpool_ride,
    create_travel_expense,
    create_travel_location_update,
    export_travel_manifest,
    generate_travel_fee_invoices,
    get_event,
    get_travel_manifest,
    get_travel_readiness,
    list_attendance,
    list_travel_carpool_rides,
    list_travel_checklist_items,
    list_travel_expenses,
    list_travel_location_updates,
    list_travel_approvals,
    list_events,
    list_travel_plans,
    list_weather_assessments,
    optimize_travel_route,
    record_attendance,
    request_travel_consents,
    seed_attendance_from_team_roster,
    seed_travel_checklist_items,
    send_travel_consent_reminders,
    update_travel_approval,
    update_travel_carpool_ride,
    update_travel_checklist_item,
    update_travel_expense,
    update_travel_plan,
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


def to_travel_plan_read(plan) -> EventTravelPlanRead:
    return EventTravelPlanRead(
        id=plan.id,
        organization_id=plan.organization_id,
        event_id=plan.event_id,
        status=plan.status,
        destination=plan.destination,
        travel_mode=plan.travel_mode,
        departure_at=plan.departure_at,
        return_at=plan.return_at,
        route_summary=plan.route_summary,
        vehicle_details=plan.vehicle_details,
        driver_details=plan.driver_details,
        staff_manifest=plan.staff_manifest,
        passenger_manifest=plan.passenger_manifest,
        lodging_details=plan.lodging_details,
        meal_plan=plan.meal_plan,
        equipment_manifest=plan.equipment_manifest,
        emergency_contacts=plan.emergency_contacts,
        medical_access_plan=plan.medical_access_plan,
        route_weather_risk=plan.route_weather_risk,
        driver_certification_status=plan.driver_certification_status,
        vehicle_inspection_status=plan.vehicle_inspection_status,
        consent_required=plan.consent_required,
        consent_due_at=plan.consent_due_at,
        estimated_cost=float(plan.estimated_cost) if plan.estimated_cost is not None else None,
        cost_per_participant=float(plan.cost_per_participant) if plan.cost_per_participant is not None else None,
        risk_level=plan.risk_level,
        risk_assessment=plan.risk_assessment,
        notes=plan.notes,
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


@router.post("/{event_id}/travel-plans", response_model=EventTravelPlanRead, status_code=status.HTTP_201_CREATED)
async def create_travel_plan_route(
    event_id: UUID,
    payload: EventTravelPlanCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelPlanRead:
    return to_travel_plan_read(await create_travel_plan(db, identity, event_id, payload, authz))


@router.get("/{event_id}/travel-plans", response_model=list[EventTravelPlanRead])
async def list_travel_plans_route(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[EventTravelPlanRead]:
    return [to_travel_plan_read(plan) for plan in await list_travel_plans(db, event_id)]


@router.patch("/travel-plans/{travel_plan_id}", response_model=EventTravelPlanRead)
async def update_travel_plan_route(
    travel_plan_id: UUID,
    payload: EventTravelPlanUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelPlanRead:
    return to_travel_plan_read(await update_travel_plan(db, identity, travel_plan_id, payload, authz))


@router.get("/travel-plans/{travel_plan_id}/readiness", response_model=EventTravelReadinessRead)
async def get_travel_readiness_route(
    travel_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelReadinessRead:
    return await get_travel_readiness(db, identity, travel_plan_id, authz)


@router.post("/travel-plans/{travel_plan_id}/route-optimization", response_model=EventTravelRouteOptimizationRead)
async def optimize_travel_route_route(
    travel_plan_id: UUID,
    payload: EventTravelRouteOptimizationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelRouteOptimizationRead:
    return await optimize_travel_route(db, identity, travel_plan_id, payload, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/consent-requests",
    response_model=EventTravelConsentBatchRead,
    status_code=status.HTTP_201_CREATED,
)
async def request_travel_consents_route(
    travel_plan_id: UUID,
    payload: EventTravelConsentRequestCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelConsentBatchRead:
    return await request_travel_consents(db, identity, travel_plan_id, payload, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/consent-reminders",
    response_model=EventTravelConsentReminderRead,
    status_code=status.HTTP_201_CREATED,
)
async def send_travel_consent_reminders_route(
    travel_plan_id: UUID,
    payload: EventTravelConsentReminderCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelConsentReminderRead:
    return await send_travel_consent_reminders(db, identity, travel_plan_id, payload, authz)


@router.get("/travel-plans/{travel_plan_id}/manifest", response_model=EventTravelManifestRead)
async def get_travel_manifest_route(
    travel_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelManifestRead:
    return await get_travel_manifest(db, identity, travel_plan_id, authz)


@router.post("/travel-plans/{travel_plan_id}/manifest/export", response_model=EventTravelManifestExportRead)
async def export_travel_manifest_route(
    travel_plan_id: UUID,
    payload: EventTravelManifestExportCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelManifestExportRead:
    return await export_travel_manifest(db, identity, travel_plan_id, payload, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/fee-invoices",
    response_model=EventTravelFeeInvoiceBatchRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_travel_fee_invoices_route(
    travel_plan_id: UUID,
    payload: EventTravelFeeInvoiceCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelFeeInvoiceBatchRead:
    return await generate_travel_fee_invoices(db, identity, travel_plan_id, payload, authz)


@router.get("/travel-plans/{travel_plan_id}/approvals", response_model=list[EventTravelApprovalRead])
async def list_travel_approvals_route(
    travel_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[EventTravelApprovalRead]:
    return await list_travel_approvals(db, identity, travel_plan_id, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/approvals",
    response_model=EventTravelApprovalRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_travel_approval_route(
    travel_plan_id: UUID,
    payload: EventTravelApprovalCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelApprovalRead:
    return await create_travel_approval(db, identity, travel_plan_id, payload, authz)


@router.patch("/travel-approvals/{approval_id}", response_model=EventTravelApprovalRead)
async def update_travel_approval_route(
    approval_id: UUID,
    payload: EventTravelApprovalUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelApprovalRead:
    return await update_travel_approval(db, identity, approval_id, payload, authz)


@router.get("/travel-plans/{travel_plan_id}/checklist", response_model=list[EventTravelChecklistItemRead])
async def list_travel_checklist_items_route(
    travel_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[EventTravelChecklistItemRead]:
    return await list_travel_checklist_items(db, identity, travel_plan_id, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/checklist",
    response_model=list[EventTravelChecklistItemRead],
    status_code=status.HTTP_201_CREATED,
)
async def seed_travel_checklist_items_route(
    travel_plan_id: UUID,
    payload: EventTravelChecklistSeedCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[EventTravelChecklistItemRead]:
    return await seed_travel_checklist_items(db, identity, travel_plan_id, payload, authz)


@router.patch("/travel-checklist-items/{checklist_item_id}", response_model=EventTravelChecklistItemRead)
async def update_travel_checklist_item_route(
    checklist_item_id: UUID,
    payload: EventTravelChecklistItemUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelChecklistItemRead:
    return await update_travel_checklist_item(db, identity, checklist_item_id, payload, authz)


@router.get("/travel-plans/{travel_plan_id}/location-updates", response_model=list[EventTravelLocationUpdateRead])
async def list_travel_location_updates_route(
    travel_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[EventTravelLocationUpdateRead]:
    return await list_travel_location_updates(db, identity, travel_plan_id, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/location-updates",
    response_model=EventTravelLocationUpdateRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_travel_location_update_route(
    travel_plan_id: UUID,
    payload: EventTravelLocationUpdateCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelLocationUpdateRead:
    return await create_travel_location_update(db, identity, travel_plan_id, payload, authz)


@router.get("/travel-plans/{travel_plan_id}/expenses", response_model=list[EventTravelExpenseRead])
async def list_travel_expenses_route(
    travel_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[EventTravelExpenseRead]:
    return await list_travel_expenses(db, identity, travel_plan_id, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/expenses",
    response_model=EventTravelExpenseRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_travel_expense_route(
    travel_plan_id: UUID,
    payload: EventTravelExpenseCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelExpenseRead:
    return await create_travel_expense(db, identity, travel_plan_id, payload, authz)


@router.patch("/travel-expenses/{expense_id}", response_model=EventTravelExpenseRead)
async def update_travel_expense_route(
    expense_id: UUID,
    payload: EventTravelExpenseUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelExpenseRead:
    return await update_travel_expense(db, identity, expense_id, payload, authz)


@router.get("/travel-plans/{travel_plan_id}/carpools", response_model=list[EventTravelCarpoolRideRead])
async def list_travel_carpool_rides_route(
    travel_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[EventTravelCarpoolRideRead]:
    return await list_travel_carpool_rides(db, identity, travel_plan_id, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/carpools",
    response_model=EventTravelCarpoolRideRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_travel_carpool_ride_route(
    travel_plan_id: UUID,
    payload: EventTravelCarpoolRideCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelCarpoolRideRead:
    return await create_travel_carpool_ride(db, identity, travel_plan_id, payload, authz)


@router.patch("/travel-carpools/{carpool_ride_id}", response_model=EventTravelCarpoolRideRead)
async def update_travel_carpool_ride_route(
    carpool_ride_id: UUID,
    payload: EventTravelCarpoolRideUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelCarpoolRideRead:
    return await update_travel_carpool_ride(db, identity, carpool_ride_id, payload, authz)


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
