from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
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
    EventTravelApprovalRoutingCreate,
    EventTravelApprovalRoutingRead,
    EventTravelApprovalUpdate,
    EventTravelBackupDriverCreate,
    EventTravelBackupDriverDispatchCreate,
    EventTravelBackupDriverDispatchRead,
    EventTravelBackupDriverRead,
    EventTravelBackupDriverUpdate,
    EventTravelCarpoolAutoMatchCreate,
    EventTravelCarpoolAutoMatchRead,
    EventTravelCarpoolRideCreate,
    EventTravelCarpoolRideRead,
    EventTravelCarpoolRideUpdate,
    EventTravelChecklistEvidenceUploadCreate,
    EventTravelChecklistEvidenceUploadRead,
    EventTravelChecklistItemRead,
    EventTravelChecklistItemUpdate,
    EventTravelChecklistSeedCreate,
    EventTravelConsentBatchRead,
    EventTravelConsentReminderCreate,
    EventTravelConsentReminderRead,
    EventTravelConsentReminderRunCreate,
    EventTravelConsentReminderRunRead,
    EventTravelConsentRequestCreate,
    EventTravelDeviceCreate,
    EventTravelDeviceFleetInventoryRead,
    EventTravelDeviceLocationIngestCreate,
    EventTravelDeviceLocationIngestRead,
    EventTravelDeviceRead,
    EventTravelDeviceSecretRead,
    EventTravelDeviceUpdate,
    EventTravelDriverRatingCreate,
    EventTravelDriverRatingRead,
    EventTravelDriverRatingSummaryRead,
    EventTravelExpenseCreate,
    EventTravelExpensePayoutCreate,
    EventTravelExpensePayoutRead,
    EventTravelExpenseRead,
    EventTravelExpenseUpdate,
    EventTravelFeeCheckoutBatchRead,
    EventTravelFeeCheckoutCreate,
    EventTravelFeeInvoiceBatchRead,
    EventTravelFeeInvoiceCreate,
    EventTravelGeofenceCheckCreate,
    EventTravelGeofenceCheckRead,
    EventTravelGeofenceZoneCreate,
    EventTravelGeofenceZoneRead,
    EventTravelGeofenceZoneUpdate,
    EventTravelLocationUpdateCreate,
    EventTravelLocationUpdateRead,
    EventTravelManifestExportCreate,
    EventTravelManifestExportRead,
    EventTravelManifestRead,
    EventTravelManifestOfflineLinkCreate,
    EventTravelManifestOfflineLinkRead,
    EventTravelPlanCreate,
    EventTravelPlanRead,
    EventTravelPlanUpdate,
    EventTravelReadinessRead,
    EventTravelReceiptUploadCreate,
    EventTravelReceiptUploadRead,
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
    dispatch_travel_backup_driver,
    execute_travel_expense_payout,
    create_travel_approval,
    auto_match_travel_carpools,
    create_travel_backup_driver,
    create_travel_carpool_ride,
    create_travel_device,
    create_travel_driver_rating,
    create_travel_expense,
    create_travel_fee_checkouts,
    check_travel_geofence,
    check_travel_geofence_zone,
    create_travel_location_update,
    create_travel_geofence_zone,
    create_travel_manifest_offline_link,
    export_travel_manifest,
    generate_travel_fee_invoices,
    get_event,
    get_travel_device_fleet_inventory,
    get_travel_driver_rating_summary,
    get_travel_manifest,
    get_travel_readiness,
    ingest_travel_device_location,
    list_attendance,
    list_travel_backup_drivers,
    list_travel_carpool_rides,
    list_travel_checklist_items,
    list_travel_devices,
    list_travel_driver_ratings,
    list_travel_expenses,
    list_travel_geofence_zones,
    list_travel_location_updates,
    list_travel_approvals,
    list_events,
    list_travel_plans,
    list_weather_assessments,
    optimize_travel_route,
    record_attendance,
    request_travel_consents,
    read_signed_travel_manifest,
    rotate_travel_device_secret,
    route_travel_approvals,
    run_event_travel_consent_reminders,
    seed_attendance_from_team_roster,
    seed_travel_checklist_items,
    send_travel_consent_reminders,
    update_travel_approval,
    update_travel_backup_driver,
    update_travel_carpool_ride,
    update_travel_checklist_item,
    update_travel_device,
    update_travel_expense,
    update_travel_geofence_zone,
    update_travel_plan,
    upload_travel_checklist_evidence,
    upload_travel_expense_receipt,
    validate_travel_device_ingest_signature,
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


@router.post(
    "/{event_id}/travel-consent-reminder-run",
    response_model=EventTravelConsentReminderRunRead,
    status_code=status.HTTP_201_CREATED,
)
async def run_event_travel_consent_reminders_route(
    event_id: UUID,
    payload: EventTravelConsentReminderRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelConsentReminderRunRead:
    return await run_event_travel_consent_reminders(db, identity, event_id, payload, authz)


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
    "/travel-plans/{travel_plan_id}/manifest/offline-link",
    response_model=EventTravelManifestOfflineLinkRead,
)
async def create_travel_manifest_offline_link_route(
    travel_plan_id: UUID,
    payload: EventTravelManifestOfflineLinkCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelManifestOfflineLinkRead:
    return await create_travel_manifest_offline_link(db, identity, travel_plan_id, payload, authz)


@router.get("/travel-manifests/{organization_id}/{travel_plan_id}/{filename}")
async def read_travel_manifest_route(
    organization_id: UUID,
    travel_plan_id: UUID,
    filename: str,
    expires: int = Query(),
    signature: str = Query(),
) -> Response:
    manifest = read_signed_travel_manifest(organization_id, travel_plan_id, filename, expires, signature)
    return Response(
        content=manifest["content"],
        media_type=str(manifest["content_type"]),
        headers={
            "Content-Disposition": f"inline; filename={manifest['filename']}",
            "X-Afrolete-Travel-Manifest-Checksum": str(manifest["checksum"]),
        },
    )


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


@router.post(
    "/travel-plans/{travel_plan_id}/fee-checkouts",
    response_model=EventTravelFeeCheckoutBatchRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_travel_fee_checkouts_route(
    travel_plan_id: UUID,
    payload: EventTravelFeeCheckoutCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelFeeCheckoutBatchRead:
    return await create_travel_fee_checkouts(db, identity, travel_plan_id, payload, authz)


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


@router.post(
    "/travel-plans/{travel_plan_id}/approval-routing",
    response_model=EventTravelApprovalRoutingRead,
    status_code=status.HTTP_201_CREATED,
)
async def route_travel_approvals_route(
    travel_plan_id: UUID,
    payload: EventTravelApprovalRoutingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelApprovalRoutingRead:
    return await route_travel_approvals(db, identity, travel_plan_id, payload, authz)


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


@router.post(
    "/travel-checklist-items/{checklist_item_id}/evidence",
    response_model=EventTravelChecklistEvidenceUploadRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_travel_checklist_evidence_route(
    checklist_item_id: UUID,
    payload: EventTravelChecklistEvidenceUploadCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelChecklistEvidenceUploadRead:
    return await upload_travel_checklist_evidence(db, identity, checklist_item_id, payload, authz)


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


@router.get("/travel-plans/{travel_plan_id}/devices", response_model=list[EventTravelDeviceRead])
async def list_travel_devices_route(
    travel_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[EventTravelDeviceRead]:
    return await list_travel_devices(db, identity, travel_plan_id, authz)


@router.get("/travel-devices/fleet-inventory", response_model=EventTravelDeviceFleetInventoryRead)
async def get_travel_device_fleet_inventory_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelDeviceFleetInventoryRead:
    return await get_travel_device_fleet_inventory(db, identity, organization_id, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/devices",
    response_model=EventTravelDeviceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_travel_device_route(
    travel_plan_id: UUID,
    payload: EventTravelDeviceCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelDeviceRead:
    return await create_travel_device(db, identity, travel_plan_id, payload, authz)


@router.patch("/travel-devices/{travel_device_id}", response_model=EventTravelDeviceRead)
async def update_travel_device_route(
    travel_device_id: UUID,
    payload: EventTravelDeviceUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelDeviceRead:
    return await update_travel_device(db, identity, travel_device_id, payload, authz)


@router.post("/travel-devices/{travel_device_id}/rotate-secret", response_model=EventTravelDeviceSecretRead)
async def rotate_travel_device_secret_route(
    travel_device_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelDeviceSecretRead:
    return await rotate_travel_device_secret(db, identity, travel_device_id, authz)


@router.get("/travel-plans/{travel_plan_id}/backup-drivers", response_model=list[EventTravelBackupDriverRead])
async def list_travel_backup_drivers_route(
    travel_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[EventTravelBackupDriverRead]:
    return await list_travel_backup_drivers(db, identity, travel_plan_id, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/backup-drivers",
    response_model=EventTravelBackupDriverRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_travel_backup_driver_route(
    travel_plan_id: UUID,
    payload: EventTravelBackupDriverCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelBackupDriverRead:
    return await create_travel_backup_driver(db, identity, travel_plan_id, payload, authz)


@router.patch("/travel-backup-drivers/{backup_driver_id}", response_model=EventTravelBackupDriverRead)
async def update_travel_backup_driver_route(
    backup_driver_id: UUID,
    payload: EventTravelBackupDriverUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelBackupDriverRead:
    return await update_travel_backup_driver(db, identity, backup_driver_id, payload, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/backup-drivers/dispatch",
    response_model=EventTravelBackupDriverDispatchRead,
)
async def dispatch_travel_backup_driver_route(
    travel_plan_id: UUID,
    payload: EventTravelBackupDriverDispatchCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelBackupDriverDispatchRead:
    return await dispatch_travel_backup_driver(db, identity, travel_plan_id, payload, authz)


@router.get("/travel-plans/{travel_plan_id}/driver-ratings", response_model=list[EventTravelDriverRatingRead])
async def list_travel_driver_ratings_route(
    travel_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[EventTravelDriverRatingRead]:
    return await list_travel_driver_ratings(db, identity, travel_plan_id, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/driver-ratings",
    response_model=EventTravelDriverRatingRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_travel_driver_rating_route(
    travel_plan_id: UUID,
    payload: EventTravelDriverRatingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelDriverRatingRead:
    return await create_travel_driver_rating(db, identity, travel_plan_id, payload, authz)


@router.get(
    "/travel-plans/{travel_plan_id}/driver-rating-summary",
    response_model=EventTravelDriverRatingSummaryRead,
)
async def get_travel_driver_rating_summary_route(
    travel_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelDriverRatingSummaryRead:
    return await get_travel_driver_rating_summary(db, identity, travel_plan_id, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/location-ingest",
    response_model=EventTravelDeviceLocationIngestRead,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_travel_device_location_route(
    request: Request,
    travel_plan_id: UUID,
    payload: EventTravelDeviceLocationIngestCreate,
    x_afrolete_travel_timestamp: str | None = Header(default=None, alias="X-Afrolete-Travel-Timestamp"),
    x_afrolete_travel_signature: str | None = Header(default=None, alias="X-Afrolete-Travel-Signature"),
    db: AsyncSession = Depends(get_db),
) -> EventTravelDeviceLocationIngestRead:
    signature_required, signature_validated = await validate_travel_device_ingest_signature(
        db,
        travel_plan_id,
        payload,
        await request.body(),
        x_afrolete_travel_timestamp,
        x_afrolete_travel_signature,
    )
    return await ingest_travel_device_location(
        db,
        travel_plan_id,
        payload,
        signature_required=signature_required,
        signature_validated=signature_validated,
    )


@router.post("/travel-plans/{travel_plan_id}/geofence-check", response_model=EventTravelGeofenceCheckRead)
async def check_travel_geofence_route(
    travel_plan_id: UUID,
    payload: EventTravelGeofenceCheckCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelGeofenceCheckRead:
    return await check_travel_geofence(db, identity, travel_plan_id, payload, authz)


@router.get("/travel-plans/{travel_plan_id}/geofence-zones", response_model=list[EventTravelGeofenceZoneRead])
async def list_travel_geofence_zones_route(
    travel_plan_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[EventTravelGeofenceZoneRead]:
    return await list_travel_geofence_zones(db, identity, travel_plan_id, authz)


@router.post(
    "/travel-plans/{travel_plan_id}/geofence-zones",
    response_model=EventTravelGeofenceZoneRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_travel_geofence_zone_route(
    travel_plan_id: UUID,
    payload: EventTravelGeofenceZoneCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelGeofenceZoneRead:
    return await create_travel_geofence_zone(db, identity, travel_plan_id, payload, authz)


@router.post("/travel-geofence-zones/{geofence_zone_id}/check", response_model=EventTravelGeofenceCheckRead)
async def check_travel_geofence_zone_route(
    geofence_zone_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelGeofenceCheckRead:
    return await check_travel_geofence_zone(db, identity, geofence_zone_id, authz)


@router.patch("/travel-geofence-zones/{geofence_zone_id}", response_model=EventTravelGeofenceZoneRead)
async def update_travel_geofence_zone_route(
    geofence_zone_id: UUID,
    payload: EventTravelGeofenceZoneUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelGeofenceZoneRead:
    return await update_travel_geofence_zone(db, identity, geofence_zone_id, payload, authz)


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


@router.post(
    "/travel-expenses/{expense_id}/payout",
    response_model=EventTravelExpensePayoutRead,
)
async def execute_travel_expense_payout_route(
    expense_id: UUID,
    payload: EventTravelExpensePayoutCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelExpensePayoutRead:
    return await execute_travel_expense_payout(db, identity, expense_id, payload, authz)


@router.post(
    "/travel-expenses/{expense_id}/receipt",
    response_model=EventTravelReceiptUploadRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_travel_expense_receipt_route(
    expense_id: UUID,
    payload: EventTravelReceiptUploadCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelReceiptUploadRead:
    return await upload_travel_expense_receipt(db, identity, expense_id, payload, authz)


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


@router.post(
    "/travel-plans/{travel_plan_id}/carpools/auto-match",
    response_model=EventTravelCarpoolAutoMatchRead,
)
async def auto_match_travel_carpools_route(
    travel_plan_id: UUID,
    payload: EventTravelCarpoolAutoMatchCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EventTravelCarpoolAutoMatchRead:
    return await auto_match_travel_carpools(db, identity, travel_plan_id, payload, authz)


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
