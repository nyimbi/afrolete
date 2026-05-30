from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.assets import (
    AssetAccountingExportRead,
    AssetAccountingSyncRead,
    AssetSummaryRead,
    AssetUtilizationRecommendationRead,
    ClubhouseAmenityCreate,
    ClubhouseAmenityRead,
    ClubhouseAmenityReservationCreate,
    ClubhouseAmenityReservationRead,
    ClubhouseAmenityReservationUpdate,
    ClubhouseBusinessDashboardRead,
    ClubhouseDashboardRead,
    ClubhouseEventCreate,
    ClubhouseEventGuestCreate,
    ClubhouseEventRead,
    ClubhouseEventUpdate,
    ClubhouseFeedbackCreate,
    ClubhouseFeedbackRead,
    ClubhouseFeedbackUpdate,
    ClubhouseMenuItemCreate,
    ClubhouseMenuItemRead,
    ClubhouseMenuItemUpdate,
    ClubhouseOperationsChecklistCreate,
    ClubhouseOperationsChecklistItemRead,
    ClubhouseOperationsChecklistItemUpdate,
    ClubhouseOperationsChecklistRead,
    ClubhouseOperationsChecklistUpdate,
    ClubhouseOperationsDashboardRead,
    ClubhousePOSDashboardRead,
    ClubhousePOSOrderCreate,
    ClubhousePOSOrderRead,
    ClubhousePOSOrderUpdate,
    ClubhouseServiceBookingCreate,
    ClubhouseServiceBookingRead,
    ClubhouseServiceBookingUpdate,
    ClubhouseServiceOfferingCreate,
    ClubhouseServiceOfferingRead,
    ClubhouseVisitCreate,
    ClubhouseVisitRead,
    ClubhouseVisitUpdate,
    EmergencyActivationAlertCreate,
    EmergencyActivationAlertRead,
    EmergencyActivationIncidentCreate,
    EmergencyActionPlanCreate,
    EmergencyActionPlanRead,
    EmergencyActionPlanUpdate,
    EmergencyEscalationTimerRunCreate,
    EmergencyEscalationTimerRunRead,
    EmergencyPlanActivationCreate,
    EmergencyPlanActivationRead,
    EmergencyPlanActivationUpdate,
    EquipmentCheckoutCreate,
    EquipmentCheckoutRead,
    EquipmentCheckoutReturn,
    EquipmentFileRead,
    EquipmentFileUploadCreate,
    EquipmentItemCreate,
    EquipmentItemRead,
    EquipmentLeaseInvoiceCreate,
    EquipmentLeaseInvoiceRead,
    EquipmentLeasePaymentCreate,
    EquipmentLeasePaymentRead,
    EquipmentLeaseQuoteRead,
    EquipmentLeaseScheduleCreate,
    EquipmentLeaseScheduleRead,
    EquipmentPhotoUpdate,
    EquipmentReaderCreate,
    EquipmentReaderGatewayScanCreate,
    EquipmentReaderProvisionRead,
    EquipmentReaderRead,
    EquipmentScanEventCreate,
    EquipmentScanEventRead,
    EquipmentScanRead,
    FacilityAccessCredentialCreate,
    FacilityAccessCredentialRead,
    FacilityAccessCredentialUpdate,
    FacilityAccessCommandRead,
    FacilityAccessDashboardRead,
    FacilityAccessDeviceCreate,
    FacilityAccessDeviceHealthCreate,
    FacilityAccessDeviceHealthRead,
    FacilityAccessDeviceProvisionRead,
    FacilityAccessDeviceRead,
    FacilityAccessEventRead,
    FacilityAccessGatewayScanCreate,
    FacilityAccessGatewayScanRead,
    FacilityAccessLockdownCreate,
    FacilityAccessLockdownDashboardRead,
    FacilityAccessLockdownRead,
    FacilityAccessLockdownResultRead,
    FacilityAccessLockdownUpdate,
    FacilityAccessScanCreate,
    FacilityAvailabilityRead,
    FacilityBookingCheckoutRead,
    FacilityBookingCreate,
    FacilityBookingRead,
    FacilityBookingRuleCreate,
    FacilityBookingRuleRead,
    FacilityBookingStatusUpdate,
    FacilityBookingWaitlistConversionCreate,
    FacilityBookingWaitlistCreate,
    FacilityBookingWaitlistRead,
    FacilityBookingWaitlistUpdate,
    FacilityCreate,
    FacilityHireCheckoutSettlementCreate,
    FacilityHireCheckoutSettlementRead,
    FacilityHireHostedCheckoutRead,
    FacilityLeaseAgreementCreate,
    FacilityLeaseAgreementRead,
    FacilityLeaseAgreementUpdate,
    FacilityLeaseInvoiceCreate,
    FacilityLeaseInvoiceRead,
    FacilityMaintenanceDashboardRead,
    FacilityMaintenanceScheduleCreate,
    FacilityMaintenanceScheduleRead,
    FacilityMaintenanceScheduleRunRead,
    FacilityMaintenanceScheduleUpdate,
    FacilityUtilityAlertRead,
    FacilityUtilityAlertUpdate,
    FacilityUtilityDashboardRead,
    FacilityUtilityGatewayReadingCreate,
    FacilityUtilityMeterCreate,
    FacilityUtilityMeterProvisionRead,
    FacilityUtilityMeterRead,
    FacilityUtilityReadingCreate,
    FacilityUtilityReadingResultRead,
    FacilityPublicBookingCreate,
    FacilityPublicListingRead,
    FacilityRead,
    FacilityRecurringBookingCreate,
    FacilityUtilizationRead,
    MaintenanceWorkOrderCreate,
    MaintenanceWorkOrderRead,
    MaintenanceWorkOrderUpdate,
    ProcurementRecommendationRead,
    SupplierOrderCreate,
    SupplierInvoiceSyncRead,
    SupplierOrderRead,
    SupplierOrderReceive,
    SupplierOrderSubmissionRead,
    SupplierScoreRead,
)
from app.schemas.safeguarding import SafeguardingIncidentRead
from app.services.assets import (
    activate_emergency_action_plan,
    activate_facility_access_lockdown,
    asset_accounting_export,
    asset_summary,
    checkout_equipment,
    clubhouse_dashboard,
    clubhouse_operations_dashboard,
    clubhouse_business_dashboard,
    clubhouse_pos_dashboard,
    add_clubhouse_event_guest,
    create_clubhouse_amenity,
    create_clubhouse_amenity_reservation,
    create_clubhouse_event,
    create_clubhouse_feedback,
    create_clubhouse_menu_item,
    create_clubhouse_operations_checklist,
    create_clubhouse_pos_order,
    create_clubhouse_service_booking,
    create_clubhouse_service_offering,
    create_clubhouse_visit,
    create_facility_access_credential,
    create_emergency_action_plan,
    create_incident_from_emergency_activation,
    create_equipment_item,
    create_facility,
    create_facility_booking,
    create_facility_lease_agreement,
    create_facility_maintenance_schedule,
    create_public_facility_waitlist_entry,
    create_recurring_facility_bookings,
    create_equipment_lease_invoice,
    create_equipment_lease_schedule,
    dispatch_emergency_activation_alert,
    list_equipment_readers,
    create_supplier_order,
    create_work_order,
    downloadable_equipment_file,
    equipment_lease_quote,
    ensure_manage_assets,
    facility_access_dashboard,
    facility_access_lockdown_dashboard,
    facility_availability,
    facility_maintenance_dashboard,
    facility_utility_dashboard,
    facility_utilization,
    generate_facility_lease_invoice,
    create_public_facility_booking,
    get_facility_booking_rule,
    get_facility_hire_hosted_checkout,
    list_public_facility_hire,
    list_facility_waitlist_entries,
    list_equipment_files,
    list_equipment_scan_events,
    list_checkouts,
    list_clubhouse_amenities,
    list_clubhouse_amenity_reservations,
    list_clubhouse_events,
    list_clubhouse_feedback,
    list_clubhouse_menu_items,
    list_clubhouse_operations_checklists,
    list_clubhouse_pos_orders,
    list_clubhouse_service_bookings,
    list_clubhouse_service_offerings,
    list_clubhouse_visits,
    list_emergency_action_plans,
    list_emergency_plan_activations,
    list_equipment_items,
    list_equipment_lease_schedules,
    list_facilities,
    list_facility_access_credentials,
    list_facility_access_commands,
    list_facility_access_devices,
    list_facility_access_lockdowns,
    list_facility_bookings,
    list_facility_lease_agreements,
    list_facility_maintenance_schedules,
    list_facility_utility_meters,
    list_supplier_orders,
    list_work_orders,
    procurement_recommendations,
    receive_supplier_order,
    reconcile_equipment_lease_payment,
    record_facility_access_scan,
    record_facility_access_device_health,
    record_facility_utility_reading,
    record_gateway_facility_access_scan,
    record_gateway_facility_utility_reading,
    record_gateway_equipment_scan,
    record_equipment_scan_event,
    return_equipment,
    run_emergency_escalation_timer_scheduler,
    scan_equipment,
    submit_supplier_order,
    sync_asset_accounting_export,
    sync_supplier_invoice,
    settle_facility_hire_checkout,
    update_facility_access_credential,
    update_facility_access_lockdown,
    update_facility_booking_status,
    update_facility_lease_agreement,
    update_facility_maintenance_schedule,
    update_facility_waitlist_entry,
    supplier_scorecard,
    update_emergency_action_plan,
    update_emergency_plan_activation,
    update_equipment_photo,
    upsert_facility_booking_rule,
    upload_equipment_file,
    provision_equipment_reader,
    provision_facility_access_device,
    provision_facility_utility_meter,
    update_work_order,
    update_facility_utility_alert,
    update_clubhouse_amenity_reservation,
    update_clubhouse_event,
    update_clubhouse_feedback,
    update_clubhouse_menu_item,
    update_clubhouse_operations_checklist,
    update_clubhouse_operations_checklist_item,
    update_clubhouse_pos_order,
    update_clubhouse_service_booking,
    update_clubhouse_visit,
    utilization_recommendations,
    convert_facility_waitlist_entry,
    generate_facility_maintenance_work_order,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service

router = APIRouter(prefix="/assets", tags=["assets"])


def to_facility_read(facility) -> FacilityRead:
    return FacilityRead(
        id=facility.id,
        organization_id=facility.organization_id,
        name=facility.name,
        facility_type=facility.facility_type,
        status=facility.status,
        sport=facility.sport,
        surface=facility.surface,
        capacity=facility.capacity,
        location=facility.location,
        dimensions=facility.dimensions,
        amenities=facility.amenities,
        hourly_rate=facility.hourly_rate,
        maintenance_budget=facility.maintenance_budget,
        condition=facility.condition,
        insurance_policy_ref=facility.insurance_policy_ref,
        last_inspection_on=facility.last_inspection_on,
        notes=facility.notes,
    )


def to_booking_rule_read(rule) -> FacilityBookingRuleRead:
    return FacilityBookingRuleRead(
        id=rule.id,
        organization_id=rule.organization_id,
        facility_id=rule.facility_id,
        min_booking_minutes=rule.min_booking_minutes,
        max_booking_minutes=rule.max_booking_minutes,
        buffer_minutes=rule.buffer_minutes,
        advance_booking_days=rule.advance_booking_days,
        requires_approval=rule.requires_approval,
        allow_public_booking=rule.allow_public_booking,
        cancellation_notice_hours=rule.cancellation_notice_hours,
        peak_hour_rate_multiplier=rule.peak_hour_rate_multiplier,
        public_booking_note=rule.public_booking_note,
        status=rule.status,
    )


def to_emergency_plan_read(plan) -> EmergencyActionPlanRead:
    return EmergencyActionPlanRead(
        id=plan.id,
        organization_id=plan.organization_id,
        facility_id=plan.facility_id,
        title=plan.title,
        emergency_type=plan.emergency_type,
        status=plan.status,
        effective_from=plan.effective_from,
        review_due_on=plan.review_due_on,
        emergency_contacts=plan.emergency_contacts,
        evacuation_routes=plan.evacuation_routes,
        medical_protocols=plan.medical_protocols,
        weather_protocols=plan.weather_protocols,
        communication_protocols=plan.communication_protocols,
        incident_command_roles=plan.incident_command_roles,
        escalation_matrix=plan.escalation_matrix,
        external_agency_contacts=plan.external_agency_contacts,
        equipment_locations=plan.equipment_locations,
        assembly_points=plan.assembly_points,
        special_needs_plan=plan.special_needs_plan,
        notes=plan.notes,
    )


def to_emergency_activation_read(activation) -> EmergencyPlanActivationRead:
    return EmergencyPlanActivationRead(
        id=activation.id,
        organization_id=activation.organization_id,
        plan_id=activation.plan_id,
        facility_id=activation.facility_id,
        incident_id=activation.incident_id,
        activated_by_person_id=activation.activated_by_person_id,
        closed_by_person_id=activation.closed_by_person_id,
        emergency_type=activation.emergency_type,
        status=activation.status,
        location_detail=activation.location_detail,
        activated_at=activation.activated_at,
        closed_at=activation.closed_at,
        escalation_level=activation.escalation_level,
        assigned_responders=activation.assigned_responders,
        guidance_steps=activation.guidance_steps,
        communication_log=activation.communication_log,
        outcome_summary=activation.outcome_summary,
        response_time_seconds=activation.response_time_seconds,
        notes=activation.notes,
    )


def to_emergency_activation_alert_read(message, recipient_count: int, activation_id: UUID) -> EmergencyActivationAlertRead:
    return EmergencyActivationAlertRead(
        activation_id=activation_id,
        message_id=message.id,
        recipient_count=recipient_count,
        channel=message.channel,
        subject=message.subject,
        urgent=message.urgent,
    )


def to_safeguarding_incident_read(incident) -> SafeguardingIncidentRead:
    return SafeguardingIncidentRead(
        id=incident.id,
        organization_id=incident.organization_id,
        event_id=incident.event_id,
        team_id=incident.team_id,
        athlete_person_id=incident.athlete_person_id,
        reported_by_person_id=incident.reported_by_person_id,
        assigned_to_person_id=incident.assigned_to_person_id,
        incident_type=incident.incident_type,
        severity=incident.severity,
        status=incident.status,
        occurred_at=incident.occurred_at,
        location=incident.location,
        title=incident.title,
        description=incident.description,
        immediate_action=incident.immediate_action,
        parent_notified_at=incident.parent_notified_at,
        medical_follow_up_required=incident.medical_follow_up_required,
        regulatory_report_required=incident.regulatory_report_required,
        resolution_notes=incident.resolution_notes,
        resolved_at=incident.resolved_at,
        created_at=incident.created_at,
    )


def to_equipment_read(item) -> EquipmentItemRead:
    return EquipmentItemRead(
        id=item.id,
        organization_id=item.organization_id,
        facility_id=item.facility_id,
        team_id=item.team_id,
        name=item.name,
        category=item.category,
        subcategory=item.subcategory,
        brand=item.brand,
        model=item.model,
        tag_code=item.tag_code,
        serial_number=item.serial_number,
        quantity_total=item.quantity_total,
        quantity_available=item.quantity_available,
        condition=item.condition,
        status=item.status,
        storage_location=item.storage_location,
        min_stock_level=item.min_stock_level,
        reorder_point=item.reorder_point,
        unit_value=item.unit_value,
        depreciation_rate=item.depreciation_rate,
        warranty_expires_on=item.warranty_expires_on,
        last_audit_on=item.last_audit_on,
        photo_url=item.photo_url,
        notes=item.notes,
    )


def to_equipment_file_read(file_record) -> EquipmentFileRead:
    return EquipmentFileRead(
        id=file_record.id,
        organization_id=file_record.organization_id,
        equipment_item_id=file_record.equipment_item_id,
        uploaded_by_person_id=file_record.uploaded_by_person_id,
        filename=file_record.filename,
        content_type=file_record.content_type,
        size_bytes=file_record.size_bytes,
        checksum=file_record.checksum,
        storage_url=file_record.storage_url,
        notes=file_record.notes,
    )


def to_checkout_read(checkout) -> EquipmentCheckoutRead:
    return EquipmentCheckoutRead(
        id=checkout.id,
        organization_id=checkout.organization_id,
        equipment_item_id=checkout.equipment_item_id,
        team_id=checkout.team_id,
        event_id=checkout.event_id,
        borrower_person_id=checkout.borrower_person_id,
        checked_out_by_person_id=checkout.checked_out_by_person_id,
        returned_by_person_id=checkout.returned_by_person_id,
        quantity=checkout.quantity,
        purpose=checkout.purpose,
        checked_out_at=checkout.checked_out_at,
        due_at=checkout.due_at,
        returned_at=checkout.returned_at,
        status=checkout.status,
        condition_out=checkout.condition_out,
        condition_in=checkout.condition_in,
        condition_notes=checkout.condition_notes,
        damage_report=checkout.damage_report,
        late_fee=checkout.late_fee,
    )


def to_work_order_read(work_order) -> MaintenanceWorkOrderRead:
    return MaintenanceWorkOrderRead(
        id=work_order.id,
        organization_id=work_order.organization_id,
        facility_maintenance_schedule_id=work_order.facility_maintenance_schedule_id,
        facility_id=work_order.facility_id,
        equipment_item_id=work_order.equipment_item_id,
        assigned_to_person_id=work_order.assigned_to_person_id,
        title=work_order.title,
        priority=work_order.priority,
        status=work_order.status,
        due_at=work_order.due_at,
        completed_at=work_order.completed_at,
        vendor=work_order.vendor,
        estimated_cost=work_order.estimated_cost,
        actual_cost=work_order.actual_cost,
        safety_related=work_order.safety_related,
        compliance_reference=work_order.compliance_reference,
        notes=work_order.notes,
    )


def to_booking_read(booking) -> FacilityBookingRead:
    return FacilityBookingRead(
        id=booking.id,
        organization_id=booking.organization_id,
        facility_id=booking.facility_id,
        team_id=booking.team_id,
        event_id=booking.event_id,
        requested_by_person_id=booking.requested_by_person_id,
        title=booking.title,
        starts_at=booking.starts_at,
        ends_at=booking.ends_at,
        status=booking.status,
        requester_name=booking.requester_name,
        requester_email=booking.requester_email,
        expected_attendees=booking.expected_attendees,
        rate=booking.rate,
        deposit_required=booking.deposit_required,
        finance_invoice_id=booking.finance_invoice_id,
        insurance_certificate_ref=booking.insurance_certificate_ref,
        special_requirements=booking.special_requirements,
        access_code=booking.access_code,
        public_visible=booking.public_visible,
        recurrence_group_id=booking.recurrence_group_id,
        occurrence_index=booking.occurrence_index,
        booking_source=booking.booking_source,
        public_booking_reference=booking.public_booking_reference,
        payment_status=booking.payment_status,
        payment_checkout_url=booking.payment_checkout_url,
        access_starts_at=booking.access_starts_at,
        access_ends_at=booking.access_ends_at,
        conflict_note=booking.conflict_note,
    )


def to_supplier_order_read(order) -> SupplierOrderRead:
    return SupplierOrderRead(
        id=order.id,
        organization_id=order.organization_id,
        equipment_item_id=order.equipment_item_id,
        supplier_name=order.supplier_name,
        item_name=order.item_name,
        quantity=order.quantity,
        unit_cost=order.unit_cost,
        total_cost=order.total_cost,
        currency=order.currency,
        status=order.status,
        external_reference=order.external_reference,
        ordered_at=order.ordered_at,
        expected_delivery_at=order.expected_delivery_at,
        received_at=order.received_at,
        notes=order.notes,
    )


@router.post("/facilities", response_model=FacilityRead, status_code=status.HTTP_201_CREATED)
async def create_facility_route(
    payload: FacilityCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityRead:
    return to_facility_read(await create_facility(db, identity, payload, authz))


@router.get("/facilities", response_model=list[FacilityRead])
async def list_facilities_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[FacilityRead]:
    return [
        to_facility_read(facility)
        for facility in await list_facilities(db, organization_id)
    ]


@router.post("/facility-booking-rules", response_model=FacilityBookingRuleRead, status_code=status.HTTP_201_CREATED)
async def upsert_facility_booking_rule_route(
    payload: FacilityBookingRuleCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityBookingRuleRead:
    return to_booking_rule_read(await upsert_facility_booking_rule(db, identity, payload, authz))


@router.get("/facility-booking-rules/{facility_id}", response_model=FacilityBookingRuleRead | None)
async def get_facility_booking_rule_route(
    facility_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> FacilityBookingRuleRead | None:
    rule = await get_facility_booking_rule(db, organization_id, facility_id)
    return to_booking_rule_read(rule) if rule else None


@router.get("/facilities/{facility_id}/availability", response_model=FacilityAvailabilityRead)
async def facility_availability_route(
    facility_id: UUID,
    organization_id: UUID = Query(),
    starts_at: datetime = Query(),
    ends_at: datetime = Query(),
    db: AsyncSession = Depends(get_db),
) -> FacilityAvailabilityRead:
    return await facility_availability(db, organization_id, facility_id, starts_at, ends_at)


@router.get("/facilities/{facility_id}/utilization", response_model=FacilityUtilizationRead)
async def facility_utilization_route(
    facility_id: UUID,
    organization_id: UUID = Query(),
    starts_at: datetime = Query(),
    ends_at: datetime = Query(),
    db: AsyncSession = Depends(get_db),
) -> FacilityUtilizationRead:
    return await facility_utilization(db, organization_id, facility_id, starts_at, ends_at)


@router.get("/public/{site}/facilities", response_model=list[FacilityPublicListingRead])
async def public_facility_hire_route(
    site: str,
    starts_at: datetime = Query(),
    ends_at: datetime = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[FacilityPublicListingRead]:
    return await list_public_facility_hire(db, site, starts_at, ends_at)


@router.post(
    "/public/{site}/bookings",
    response_model=FacilityBookingCheckoutRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_public_facility_booking_route(
    site: str,
    payload: FacilityPublicBookingCreate,
    db: AsyncSession = Depends(get_db),
) -> FacilityBookingCheckoutRead:
    return await create_public_facility_booking(db, site, payload)


@router.post(
    "/public/{site}/waitlist",
    response_model=FacilityBookingWaitlistRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_public_facility_waitlist_route(
    site: str,
    payload: FacilityBookingWaitlistCreate,
    db: AsyncSession = Depends(get_db),
) -> FacilityBookingWaitlistRead:
    return await create_public_facility_waitlist_entry(db, site, payload)


@router.get(
    "/facility-checkout-sessions/{session_id}",
    response_model=FacilityHireHostedCheckoutRead,
)
async def get_facility_checkout_session_route(
    session_id: str,
    invoice_id: UUID = Query(),
    booking_id: UUID = Query(),
    provider: str = Query(default="manual_gateway"),
    db: AsyncSession = Depends(get_db),
) -> FacilityHireHostedCheckoutRead:
    return await get_facility_hire_hosted_checkout(db, session_id, invoice_id, booking_id, provider)


@router.post(
    "/facility-checkout-sessions/{session_id}/settle",
    response_model=FacilityHireCheckoutSettlementRead,
)
async def settle_facility_checkout_session_route(
    session_id: str,
    payload: FacilityHireCheckoutSettlementCreate,
    db: AsyncSession = Depends(get_db),
) -> FacilityHireCheckoutSettlementRead:
    return await settle_facility_hire_checkout(db, session_id, payload)


@router.post("/emergency-plans", response_model=EmergencyActionPlanRead, status_code=status.HTTP_201_CREATED)
async def create_emergency_plan_route(
    payload: EmergencyActionPlanCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EmergencyActionPlanRead:
    return to_emergency_plan_read(await create_emergency_action_plan(db, identity, payload, authz))


@router.get("/emergency-plans", response_model=list[EmergencyActionPlanRead])
async def list_emergency_plans_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[EmergencyActionPlanRead]:
    return [
        to_emergency_plan_read(plan)
        for plan in await list_emergency_action_plans(db, organization_id, facility_id)
    ]


@router.patch("/emergency-plans/{plan_id}", response_model=EmergencyActionPlanRead)
async def update_emergency_plan_route(
    plan_id: UUID,
    payload: EmergencyActionPlanUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EmergencyActionPlanRead:
    return to_emergency_plan_read(
        await update_emergency_action_plan(db, identity, plan_id, payload, authz)
    )


@router.post(
    "/emergency-activations",
    response_model=EmergencyPlanActivationRead,
    status_code=status.HTTP_201_CREATED,
)
async def activate_emergency_plan_route(
    payload: EmergencyPlanActivationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EmergencyPlanActivationRead:
    return to_emergency_activation_read(await activate_emergency_action_plan(db, identity, payload, authz))


@router.get("/emergency-activations", response_model=list[EmergencyPlanActivationRead])
async def list_emergency_activations_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[EmergencyPlanActivationRead]:
    return [
        to_emergency_activation_read(activation)
        for activation in await list_emergency_plan_activations(db, organization_id)
    ]


@router.patch("/emergency-activations/{activation_id}", response_model=EmergencyPlanActivationRead)
async def update_emergency_activation_route(
    activation_id: UUID,
    payload: EmergencyPlanActivationUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EmergencyPlanActivationRead:
    return to_emergency_activation_read(
        await update_emergency_plan_activation(db, identity, activation_id, payload, authz)
    )


@router.post(
    "/emergency-activations/{activation_id}/alerts",
    response_model=EmergencyActivationAlertRead,
    status_code=status.HTTP_201_CREATED,
)
async def dispatch_emergency_activation_alert_route(
    activation_id: UUID,
    payload: EmergencyActivationAlertCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EmergencyActivationAlertRead:
    message, recipient_count = await dispatch_emergency_activation_alert(
        db,
        identity,
        activation_id,
        payload,
        authz,
    )
    return to_emergency_activation_alert_read(message, recipient_count, activation_id)


@router.post("/emergency-escalations/run", response_model=EmergencyEscalationTimerRunRead)
async def run_emergency_escalation_timer_route(
    payload: EmergencyEscalationTimerRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EmergencyEscalationTimerRunRead:
    return await run_emergency_escalation_timer_scheduler(db, identity, payload, authz)


@router.post(
    "/emergency-activations/{activation_id}/incident",
    response_model=SafeguardingIncidentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_emergency_activation_incident_route(
    activation_id: UUID,
    payload: EmergencyActivationIncidentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingIncidentRead:
    return to_safeguarding_incident_read(
        await create_incident_from_emergency_activation(
            db,
            identity,
            activation_id,
            payload,
            authz,
        )
    )


@router.post("/equipment", response_model=EquipmentItemRead, status_code=status.HTTP_201_CREATED)
async def create_equipment_route(
    payload: EquipmentItemCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EquipmentItemRead:
    return to_equipment_read(await create_equipment_item(db, identity, payload, authz))


@router.get("/equipment", response_model=list[EquipmentItemRead])
async def list_equipment_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    team_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[EquipmentItemRead]:
    return [
        to_equipment_read(item)
        for item in await list_equipment_items(
            db,
            organization_id,
            facility_id=facility_id,
            team_id=team_id,
        )
    ]


@router.get("/equipment/scan", response_model=EquipmentScanRead)
async def scan_equipment_route(
    organization_id: UUID = Query(),
    code: str = Query(min_length=1),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EquipmentScanRead:
    return await scan_equipment(db, identity, organization_id, code, authz)


@router.post(
    "/equipment/rfid-scans",
    response_model=EquipmentScanEventRead,
    status_code=status.HTTP_201_CREATED,
)
async def record_equipment_scan_event_route(
    payload: EquipmentScanEventCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EquipmentScanEventRead:
    return await record_equipment_scan_event(db, identity, payload, authz)


@router.get("/equipment/rfid-scans", response_model=list[EquipmentScanEventRead])
async def list_equipment_scan_events_route(
    organization_id: UUID = Query(),
    equipment_item_id: UUID | None = Query(default=None),
    matched: bool | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[EquipmentScanEventRead]:
    return await list_equipment_scan_events(
        db,
        identity,
        organization_id,
        authz,
        equipment_item_id=equipment_item_id,
        matched=matched,
    )


@router.post(
    "/equipment/rfid-readers",
    response_model=EquipmentReaderProvisionRead,
    status_code=status.HTTP_201_CREATED,
)
async def provision_equipment_reader_route(
    payload: EquipmentReaderCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EquipmentReaderProvisionRead:
    return await provision_equipment_reader(db, identity, payload, authz)


@router.get("/equipment/rfid-readers", response_model=list[EquipmentReaderRead])
async def list_equipment_readers_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[EquipmentReaderRead]:
    return await list_equipment_readers(db, identity, organization_id, authz)


@router.post("/equipment/rfid-gateway/{organization_id}/{reader_id}/scans", response_model=EquipmentScanEventRead)
async def record_gateway_equipment_scan_route(
    organization_id: UUID,
    reader_id: str,
    payload: EquipmentReaderGatewayScanCreate,
    x_afrolete_rfid_key: str | None = Header(default=None, alias="X-Afrolete-RFID-Key"),
    db: AsyncSession = Depends(get_db),
) -> EquipmentScanEventRead:
    return await record_gateway_equipment_scan(db, organization_id, reader_id, x_afrolete_rfid_key, payload)


@router.patch("/equipment/{equipment_item_id}/photo", response_model=EquipmentItemRead)
async def update_equipment_photo_route(
    equipment_item_id: UUID,
    payload: EquipmentPhotoUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EquipmentItemRead:
    return to_equipment_read(await update_equipment_photo(db, identity, equipment_item_id, payload, authz))


@router.post(
    "/equipment/{equipment_item_id}/files",
    response_model=EquipmentFileRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_equipment_file_route(
    equipment_item_id: UUID,
    payload: EquipmentFileUploadCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EquipmentFileRead:
    return to_equipment_file_read(
        await upload_equipment_file(db, identity, equipment_item_id, payload, authz)
    )


@router.get("/equipment/{equipment_item_id}/files", response_model=list[EquipmentFileRead])
async def list_equipment_files_route(
    equipment_item_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[EquipmentFileRead]:
    return [
        to_equipment_file_read(file_record)
        for file_record in await list_equipment_files(db, equipment_item_id)
    ]


@router.get("/equipment/files/{file_id}/download")
async def download_equipment_file_route(
    file_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> Response:
    artifact = await downloadable_equipment_file(db, identity, file_id, authz)
    return Response(
        content=artifact["content"],
        media_type=str(artifact["content_type"]),
        headers={
            "Content-Disposition": f"attachment; filename={artifact['filename']}",
            "X-Afrolete-Equipment-Checksum": str(artifact["checksum"]),
        },
    )


@router.get("/equipment/{equipment_item_id}/lease-quote", response_model=EquipmentLeaseQuoteRead)
async def equipment_lease_quote_route(
    equipment_item_id: UUID,
    organization_id: UUID = Query(),
    quantity: int = Query(default=1, ge=1),
    term_months: int = Query(default=12, ge=1, le=120),
    db: AsyncSession = Depends(get_db),
) -> EquipmentLeaseQuoteRead:
    return await equipment_lease_quote(db, organization_id, equipment_item_id, quantity, term_months)


@router.post(
    "/equipment/{equipment_item_id}/lease-invoice",
    response_model=EquipmentLeaseInvoiceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_equipment_lease_invoice_route(
    equipment_item_id: UUID,
    payload: EquipmentLeaseInvoiceCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EquipmentLeaseInvoiceRead:
    return await create_equipment_lease_invoice(db, identity, equipment_item_id, payload, authz)


@router.post(
    "/equipment/{equipment_item_id}/lease-schedules",
    response_model=EquipmentLeaseScheduleRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_equipment_lease_schedule_route(
    equipment_item_id: UUID,
    payload: EquipmentLeaseScheduleCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EquipmentLeaseScheduleRead:
    return await create_equipment_lease_schedule(db, identity, equipment_item_id, payload, authz)


@router.get("/lease-schedules", response_model=list[EquipmentLeaseScheduleRead])
async def list_equipment_lease_schedules_route(
    organization_id: UUID = Query(),
    equipment_item_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[EquipmentLeaseScheduleRead]:
    return await list_equipment_lease_schedules(db, organization_id, equipment_item_id=equipment_item_id)


@router.post("/lease-schedules/{lease_schedule_id}/payments", response_model=EquipmentLeasePaymentRead)
async def reconcile_equipment_lease_payment_route(
    lease_schedule_id: UUID,
    payload: EquipmentLeasePaymentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EquipmentLeasePaymentRead:
    return await reconcile_equipment_lease_payment(db, identity, lease_schedule_id, payload, authz)


@router.post("/checkouts", response_model=EquipmentCheckoutRead, status_code=status.HTTP_201_CREATED)
async def checkout_equipment_route(
    payload: EquipmentCheckoutCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EquipmentCheckoutRead:
    return to_checkout_read(await checkout_equipment(db, identity, payload, authz))


@router.get("/checkouts", response_model=list[EquipmentCheckoutRead])
async def list_checkouts_route(
    organization_id: UUID = Query(),
    open_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> list[EquipmentCheckoutRead]:
    return [
        to_checkout_read(checkout)
        for checkout in await list_checkouts(db, organization_id, open_only=open_only)
    ]


@router.patch("/checkouts/{checkout_id}/return", response_model=EquipmentCheckoutRead)
async def return_equipment_route(
    checkout_id: UUID,
    payload: EquipmentCheckoutReturn,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> EquipmentCheckoutRead:
    return to_checkout_read(await return_equipment(db, identity, checkout_id, payload, authz))


@router.post(
    "/work-orders",
    response_model=MaintenanceWorkOrderRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_work_order_route(
    payload: MaintenanceWorkOrderCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MaintenanceWorkOrderRead:
    return to_work_order_read(await create_work_order(db, identity, payload, authz))


@router.get("/work-orders", response_model=list[MaintenanceWorkOrderRead])
async def list_work_orders_route(
    organization_id: UUID = Query(),
    open_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> list[MaintenanceWorkOrderRead]:
    return [
        to_work_order_read(work_order)
        for work_order in await list_work_orders(db, organization_id, open_only=open_only)
    ]


@router.patch("/work-orders/{work_order_id}", response_model=MaintenanceWorkOrderRead)
async def update_work_order_route(
    work_order_id: UUID,
    payload: MaintenanceWorkOrderUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MaintenanceWorkOrderRead:
    return to_work_order_read(await update_work_order(db, identity, work_order_id, payload, authz))


@router.post(
    "/maintenance-schedules",
    response_model=FacilityMaintenanceScheduleRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_facility_maintenance_schedule_route(
    payload: FacilityMaintenanceScheduleCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityMaintenanceScheduleRead:
    return await create_facility_maintenance_schedule(db, identity, payload, authz)


@router.get("/maintenance-schedules", response_model=list[FacilityMaintenanceScheduleRead])
async def list_facility_maintenance_schedules_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[FacilityMaintenanceScheduleRead]:
    return await list_facility_maintenance_schedules(
        db,
        organization_id,
        facility_id=facility_id,
        status_filter=status_filter,
    )


@router.patch("/maintenance-schedules/{schedule_id}", response_model=FacilityMaintenanceScheduleRead)
async def update_facility_maintenance_schedule_route(
    schedule_id: UUID,
    payload: FacilityMaintenanceScheduleUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityMaintenanceScheduleRead:
    return await update_facility_maintenance_schedule(db, identity, schedule_id, payload, authz)


@router.post("/maintenance-schedules/{schedule_id}/work-order", response_model=FacilityMaintenanceScheduleRunRead)
async def generate_facility_maintenance_work_order_route(
    schedule_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityMaintenanceScheduleRunRead:
    return await generate_facility_maintenance_work_order(db, identity, schedule_id, authz)


@router.get("/maintenance-dashboard", response_model=FacilityMaintenanceDashboardRead)
async def facility_maintenance_dashboard_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> FacilityMaintenanceDashboardRead:
    return await facility_maintenance_dashboard(db, organization_id, facility_id=facility_id)


@router.post("/facility-leases", response_model=FacilityLeaseAgreementRead, status_code=status.HTTP_201_CREATED)
async def create_facility_lease_agreement_route(
    payload: FacilityLeaseAgreementCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityLeaseAgreementRead:
    return await create_facility_lease_agreement(db, identity, payload, authz)


@router.get("/facility-leases", response_model=list[FacilityLeaseAgreementRead])
async def list_facility_lease_agreements_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[FacilityLeaseAgreementRead]:
    return await list_facility_lease_agreements(
        db,
        organization_id,
        facility_id=facility_id,
        status_filter=status_filter,
    )


@router.patch("/facility-leases/{lease_id}", response_model=FacilityLeaseAgreementRead)
async def update_facility_lease_agreement_route(
    lease_id: UUID,
    payload: FacilityLeaseAgreementUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityLeaseAgreementRead:
    return await update_facility_lease_agreement(db, identity, lease_id, payload, authz)


@router.post("/facility-leases/{lease_id}/invoice", response_model=FacilityLeaseInvoiceRead)
async def generate_facility_lease_invoice_route(
    lease_id: UUID,
    payload: FacilityLeaseInvoiceCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityLeaseInvoiceRead:
    return await generate_facility_lease_invoice(db, identity, lease_id, payload, authz)


@router.post("/access-credentials", response_model=FacilityAccessCredentialRead, status_code=status.HTTP_201_CREATED)
async def create_facility_access_credential_route(
    payload: FacilityAccessCredentialCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityAccessCredentialRead:
    return await create_facility_access_credential(db, identity, payload, authz)


@router.get("/access-credentials", response_model=list[FacilityAccessCredentialRead])
async def list_facility_access_credentials_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[FacilityAccessCredentialRead]:
    return await list_facility_access_credentials(
        db,
        organization_id,
        facility_id=facility_id,
        status_filter=status_filter,
    )


@router.patch("/access-credentials/{credential_id}", response_model=FacilityAccessCredentialRead)
async def update_facility_access_credential_route(
    credential_id: UUID,
    payload: FacilityAccessCredentialUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityAccessCredentialRead:
    return await update_facility_access_credential(db, identity, credential_id, payload, authz)


@router.post("/access-scans", response_model=FacilityAccessEventRead)
async def record_facility_access_scan_route(
    payload: FacilityAccessScanCreate,
    db: AsyncSession = Depends(get_db),
) -> FacilityAccessEventRead:
    return await record_facility_access_scan(db, payload)


@router.get("/access-dashboard", response_model=FacilityAccessDashboardRead)
async def facility_access_dashboard_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> FacilityAccessDashboardRead:
    return await facility_access_dashboard(db, organization_id, facility_id=facility_id)


@router.post("/access-devices", response_model=FacilityAccessDeviceProvisionRead, status_code=status.HTTP_201_CREATED)
async def provision_facility_access_device_route(
    payload: FacilityAccessDeviceCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityAccessDeviceProvisionRead:
    return await provision_facility_access_device(db, identity, payload, authz)


@router.get("/access-devices", response_model=list[FacilityAccessDeviceRead])
async def list_facility_access_devices_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[FacilityAccessDeviceRead]:
    return await list_facility_access_devices(db, identity, organization_id, authz, facility_id=facility_id)


@router.get("/access-commands", response_model=list[FacilityAccessCommandRead])
async def list_facility_access_commands_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    device_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[FacilityAccessCommandRead]:
    return await list_facility_access_commands(
        db,
        identity,
        organization_id,
        authz,
        facility_id=facility_id,
        device_id=device_id,
    )


@router.post("/access-gateway/{organization_id}/{device_id}/scans", response_model=FacilityAccessGatewayScanRead)
async def record_gateway_facility_access_scan_route(
    organization_id: UUID,
    device_id: str,
    payload: FacilityAccessGatewayScanCreate,
    x_afrolete_access_key: str | None = Header(default=None, alias="X-Afrolete-Access-Key"),
    db: AsyncSession = Depends(get_db),
) -> FacilityAccessGatewayScanRead:
    return await record_gateway_facility_access_scan(db, organization_id, device_id, x_afrolete_access_key, payload)


@router.post("/access-gateway/{organization_id}/{device_id}/health", response_model=FacilityAccessDeviceHealthRead)
async def record_facility_access_device_health_route(
    organization_id: UUID,
    device_id: str,
    payload: FacilityAccessDeviceHealthCreate,
    x_afrolete_access_key: str | None = Header(default=None, alias="X-Afrolete-Access-Key"),
    db: AsyncSession = Depends(get_db),
) -> FacilityAccessDeviceHealthRead:
    return await record_facility_access_device_health(db, organization_id, device_id, x_afrolete_access_key, payload)


@router.post("/access-lockdowns", response_model=FacilityAccessLockdownResultRead, status_code=status.HTTP_201_CREATED)
async def activate_facility_access_lockdown_route(
    payload: FacilityAccessLockdownCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityAccessLockdownResultRead:
    return await activate_facility_access_lockdown(db, identity, payload, authz)


@router.get("/access-lockdowns", response_model=list[FacilityAccessLockdownRead])
async def list_facility_access_lockdowns_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[FacilityAccessLockdownRead]:
    return await list_facility_access_lockdowns(db, identity, organization_id, authz, facility_id=facility_id)


@router.patch("/access-lockdowns/{lockdown_id}", response_model=FacilityAccessLockdownRead)
async def update_facility_access_lockdown_route(
    lockdown_id: UUID,
    payload: FacilityAccessLockdownUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityAccessLockdownRead:
    return await update_facility_access_lockdown(db, identity, lockdown_id, payload, authz)


@router.get("/access-lockdown-dashboard", response_model=FacilityAccessLockdownDashboardRead)
async def facility_access_lockdown_dashboard_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> FacilityAccessLockdownDashboardRead:
    return await facility_access_lockdown_dashboard(db, organization_id, facility_id=facility_id)


@router.post("/utility-meters", response_model=FacilityUtilityMeterProvisionRead, status_code=status.HTTP_201_CREATED)
async def provision_facility_utility_meter_route(
    payload: FacilityUtilityMeterCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityUtilityMeterProvisionRead:
    return await provision_facility_utility_meter(db, identity, payload, authz)


@router.get("/utility-meters", response_model=list[FacilityUtilityMeterRead])
async def list_facility_utility_meters_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[FacilityUtilityMeterRead]:
    return await list_facility_utility_meters(db, identity, organization_id, authz, facility_id=facility_id)


@router.post("/utility-readings", response_model=FacilityUtilityReadingResultRead)
async def record_facility_utility_reading_route(
    payload: FacilityUtilityReadingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityUtilityReadingResultRead:
    return await record_facility_utility_reading(db, identity, payload, authz)


@router.post("/utility-gateway/{organization_id}/{meter_id}/readings", response_model=FacilityUtilityReadingResultRead)
async def record_gateway_facility_utility_reading_route(
    organization_id: UUID,
    meter_id: str,
    payload: FacilityUtilityGatewayReadingCreate,
    x_afrolete_utility_key: str | None = Header(default=None, alias="X-Afrolete-Utility-Key"),
    db: AsyncSession = Depends(get_db),
) -> FacilityUtilityReadingResultRead:
    return await record_gateway_facility_utility_reading(db, organization_id, meter_id, x_afrolete_utility_key, payload)


@router.get("/utility-dashboard", response_model=FacilityUtilityDashboardRead)
async def facility_utility_dashboard_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> FacilityUtilityDashboardRead:
    return await facility_utility_dashboard(db, organization_id, facility_id=facility_id)


@router.patch("/utility-alerts/{alert_id}", response_model=FacilityUtilityAlertRead)
async def update_facility_utility_alert_route(
    alert_id: UUID,
    payload: FacilityUtilityAlertUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityUtilityAlertRead:
    return await update_facility_utility_alert(db, identity, alert_id, payload, authz)


@router.post("/clubhouse/amenities", response_model=ClubhouseAmenityRead, status_code=status.HTTP_201_CREATED)
async def create_clubhouse_amenity_route(
    payload: ClubhouseAmenityCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseAmenityRead:
    return await create_clubhouse_amenity(db, identity, payload, authz)


@router.get("/clubhouse/amenities", response_model=list[ClubhouseAmenityRead])
async def list_clubhouse_amenities_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[ClubhouseAmenityRead]:
    return await list_clubhouse_amenities(db, identity, organization_id, authz, facility_id=facility_id)


@router.post("/clubhouse/visits", response_model=ClubhouseVisitRead, status_code=status.HTTP_201_CREATED)
async def create_clubhouse_visit_route(
    payload: ClubhouseVisitCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseVisitRead:
    return await create_clubhouse_visit(db, identity, payload, authz)


@router.get("/clubhouse/visits", response_model=list[ClubhouseVisitRead])
async def list_clubhouse_visits_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[ClubhouseVisitRead]:
    return await list_clubhouse_visits(
        db,
        identity,
        organization_id,
        authz,
        facility_id=facility_id,
        status_filter=status_filter,
    )


@router.patch("/clubhouse/visits/{visit_id}", response_model=ClubhouseVisitRead)
async def update_clubhouse_visit_route(
    visit_id: UUID,
    payload: ClubhouseVisitUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseVisitRead:
    return await update_clubhouse_visit(db, identity, visit_id, payload, authz)


@router.post(
    "/clubhouse/reservations",
    response_model=ClubhouseAmenityReservationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_clubhouse_amenity_reservation_route(
    payload: ClubhouseAmenityReservationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseAmenityReservationRead:
    return await create_clubhouse_amenity_reservation(db, identity, payload, authz)


@router.get("/clubhouse/reservations", response_model=list[ClubhouseAmenityReservationRead])
async def list_clubhouse_amenity_reservations_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    amenity_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[ClubhouseAmenityReservationRead]:
    return await list_clubhouse_amenity_reservations(
        db,
        identity,
        organization_id,
        authz,
        facility_id=facility_id,
        amenity_id=amenity_id,
        status_filter=status_filter,
    )


@router.patch("/clubhouse/reservations/{reservation_id}", response_model=ClubhouseAmenityReservationRead)
async def update_clubhouse_amenity_reservation_route(
    reservation_id: UUID,
    payload: ClubhouseAmenityReservationUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseAmenityReservationRead:
    return await update_clubhouse_amenity_reservation(db, identity, reservation_id, payload, authz)


@router.get("/clubhouse/dashboard", response_model=ClubhouseDashboardRead)
async def clubhouse_dashboard_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> ClubhouseDashboardRead:
    return await clubhouse_dashboard(db, organization_id, facility_id=facility_id)


@router.post("/clubhouse/menu-items", response_model=ClubhouseMenuItemRead, status_code=status.HTTP_201_CREATED)
async def create_clubhouse_menu_item_route(
    payload: ClubhouseMenuItemCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseMenuItemRead:
    return await create_clubhouse_menu_item(db, identity, payload, authz)


@router.get("/clubhouse/menu-items", response_model=list[ClubhouseMenuItemRead])
async def list_clubhouse_menu_items_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[ClubhouseMenuItemRead]:
    return await list_clubhouse_menu_items(
        db,
        identity,
        organization_id,
        authz,
        facility_id=facility_id,
        status_filter=status_filter,
    )


@router.patch("/clubhouse/menu-items/{menu_item_id}", response_model=ClubhouseMenuItemRead)
async def update_clubhouse_menu_item_route(
    menu_item_id: UUID,
    payload: ClubhouseMenuItemUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseMenuItemRead:
    return await update_clubhouse_menu_item(db, identity, menu_item_id, payload, authz)


@router.post("/clubhouse/pos-orders", response_model=ClubhousePOSOrderRead, status_code=status.HTTP_201_CREATED)
async def create_clubhouse_pos_order_route(
    payload: ClubhousePOSOrderCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhousePOSOrderRead:
    return await create_clubhouse_pos_order(db, identity, payload, authz)


@router.get("/clubhouse/pos-orders", response_model=list[ClubhousePOSOrderRead])
async def list_clubhouse_pos_orders_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[ClubhousePOSOrderRead]:
    return await list_clubhouse_pos_orders(
        db,
        identity,
        organization_id,
        authz,
        facility_id=facility_id,
        status_filter=status_filter,
    )


@router.patch("/clubhouse/pos-orders/{order_id}", response_model=ClubhousePOSOrderRead)
async def update_clubhouse_pos_order_route(
    order_id: UUID,
    payload: ClubhousePOSOrderUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhousePOSOrderRead:
    return await update_clubhouse_pos_order(db, identity, order_id, payload, authz)


@router.get("/clubhouse/pos-dashboard", response_model=ClubhousePOSDashboardRead)
async def clubhouse_pos_dashboard_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> ClubhousePOSDashboardRead:
    return await clubhouse_pos_dashboard(db, organization_id, facility_id=facility_id)


@router.post(
    "/clubhouse/operations-checklists",
    response_model=ClubhouseOperationsChecklistRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_clubhouse_operations_checklist_route(
    payload: ClubhouseOperationsChecklistCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseOperationsChecklistRead:
    return await create_clubhouse_operations_checklist(db, identity, payload, authz)


@router.get("/clubhouse/operations-checklists", response_model=list[ClubhouseOperationsChecklistRead])
async def list_clubhouse_operations_checklists_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[ClubhouseOperationsChecklistRead]:
    return await list_clubhouse_operations_checklists(
        db,
        identity,
        organization_id,
        authz,
        facility_id=facility_id,
        status_filter=status_filter,
    )


@router.patch("/clubhouse/operations-checklists/{checklist_id}", response_model=ClubhouseOperationsChecklistRead)
async def update_clubhouse_operations_checklist_route(
    checklist_id: UUID,
    payload: ClubhouseOperationsChecklistUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseOperationsChecklistRead:
    return await update_clubhouse_operations_checklist(db, identity, checklist_id, payload, authz)


@router.patch("/clubhouse/operations-checklist-items/{item_id}", response_model=ClubhouseOperationsChecklistItemRead)
async def update_clubhouse_operations_checklist_item_route(
    item_id: UUID,
    payload: ClubhouseOperationsChecklistItemUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseOperationsChecklistItemRead:
    return await update_clubhouse_operations_checklist_item(db, identity, item_id, payload, authz)


@router.get("/clubhouse/operations-dashboard", response_model=ClubhouseOperationsDashboardRead)
async def clubhouse_operations_dashboard_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> ClubhouseOperationsDashboardRead:
    return await clubhouse_operations_dashboard(db, organization_id, facility_id=facility_id)


@router.post("/clubhouse/events", response_model=ClubhouseEventRead, status_code=status.HTTP_201_CREATED)
async def create_clubhouse_event_route(
    payload: ClubhouseEventCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseEventRead:
    return await create_clubhouse_event(db, identity, payload, authz)


@router.get("/clubhouse/events", response_model=list[ClubhouseEventRead])
async def list_clubhouse_events_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[ClubhouseEventRead]:
    return await list_clubhouse_events(db, identity, organization_id, authz, facility_id, status_filter)


@router.patch("/clubhouse/events/{event_id}", response_model=ClubhouseEventRead)
async def update_clubhouse_event_route(
    event_id: UUID,
    payload: ClubhouseEventUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseEventRead:
    return await update_clubhouse_event(db, identity, event_id, payload, authz)


@router.post("/clubhouse/events/{event_id}/guests", response_model=ClubhouseEventRead, status_code=status.HTTP_201_CREATED)
async def add_clubhouse_event_guest_route(
    event_id: UUID,
    payload: ClubhouseEventGuestCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseEventRead:
    return await add_clubhouse_event_guest(db, identity, event_id, payload, authz)


@router.post("/clubhouse/services", response_model=ClubhouseServiceOfferingRead, status_code=status.HTTP_201_CREATED)
async def create_clubhouse_service_offering_route(
    payload: ClubhouseServiceOfferingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseServiceOfferingRead:
    return await create_clubhouse_service_offering(db, identity, payload, authz)


@router.get("/clubhouse/services", response_model=list[ClubhouseServiceOfferingRead])
async def list_clubhouse_service_offerings_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[ClubhouseServiceOfferingRead]:
    return await list_clubhouse_service_offerings(db, identity, organization_id, authz, facility_id)


@router.post("/clubhouse/service-bookings", response_model=ClubhouseServiceBookingRead, status_code=status.HTTP_201_CREATED)
async def create_clubhouse_service_booking_route(
    payload: ClubhouseServiceBookingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseServiceBookingRead:
    return await create_clubhouse_service_booking(db, identity, payload, authz)


@router.get("/clubhouse/service-bookings", response_model=list[ClubhouseServiceBookingRead])
async def list_clubhouse_service_bookings_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[ClubhouseServiceBookingRead]:
    return await list_clubhouse_service_bookings(db, identity, organization_id, authz, facility_id)


@router.patch("/clubhouse/service-bookings/{booking_id}", response_model=ClubhouseServiceBookingRead)
async def update_clubhouse_service_booking_route(
    booking_id: UUID,
    payload: ClubhouseServiceBookingUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseServiceBookingRead:
    return await update_clubhouse_service_booking(db, identity, booking_id, payload, authz)


@router.post("/clubhouse/feedback", response_model=ClubhouseFeedbackRead, status_code=status.HTTP_201_CREATED)
async def create_clubhouse_feedback_route(
    payload: ClubhouseFeedbackCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseFeedbackRead:
    return await create_clubhouse_feedback(db, identity, payload, authz)


@router.get("/clubhouse/feedback", response_model=list[ClubhouseFeedbackRead])
async def list_clubhouse_feedback_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[ClubhouseFeedbackRead]:
    return await list_clubhouse_feedback(db, identity, organization_id, authz, facility_id, status_filter)


@router.patch("/clubhouse/feedback/{feedback_id}", response_model=ClubhouseFeedbackRead)
async def update_clubhouse_feedback_route(
    feedback_id: UUID,
    payload: ClubhouseFeedbackUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ClubhouseFeedbackRead:
    return await update_clubhouse_feedback(db, identity, feedback_id, payload, authz)


@router.get("/clubhouse/business-dashboard", response_model=ClubhouseBusinessDashboardRead)
async def clubhouse_business_dashboard_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> ClubhouseBusinessDashboardRead:
    return await clubhouse_business_dashboard(db, organization_id, facility_id=facility_id)


@router.post("/bookings", response_model=FacilityBookingRead, status_code=status.HTTP_201_CREATED)
async def create_facility_booking_route(
    payload: FacilityBookingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityBookingRead:
    return to_booking_read(await create_facility_booking(db, identity, payload, authz))


@router.post("/bookings/recurring", response_model=list[FacilityBookingRead], status_code=status.HTTP_201_CREATED)
async def create_recurring_facility_bookings_route(
    payload: FacilityRecurringBookingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[FacilityBookingRead]:
    return [
        to_booking_read(booking)
        for booking in await create_recurring_facility_bookings(db, identity, payload, authz)
    ]


@router.patch("/bookings/{booking_id}/status", response_model=FacilityBookingRead)
async def update_facility_booking_status_route(
    booking_id: UUID,
    payload: FacilityBookingStatusUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityBookingRead:
    return to_booking_read(await update_facility_booking_status(db, identity, booking_id, payload, authz))


@router.get("/bookings", response_model=list[FacilityBookingRead])
async def list_facility_bookings_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[FacilityBookingRead]:
    return [
        to_booking_read(booking)
        for booking in await list_facility_bookings(db, organization_id, facility_id=facility_id)
    ]


@router.get("/waitlist", response_model=list[FacilityBookingWaitlistRead])
async def list_facility_waitlist_route(
    organization_id: UUID = Query(),
    facility_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[FacilityBookingWaitlistRead]:
    return await list_facility_waitlist_entries(
        db,
        organization_id,
        facility_id=facility_id,
        status_filter=status_filter,
    )


@router.patch("/waitlist/{entry_id}", response_model=FacilityBookingWaitlistRead)
async def update_facility_waitlist_route(
    entry_id: UUID,
    payload: FacilityBookingWaitlistUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityBookingWaitlistRead:
    return await update_facility_waitlist_entry(db, identity, entry_id, payload, authz)


@router.post("/waitlist/{entry_id}/convert", response_model=FacilityBookingCheckoutRead)
async def convert_facility_waitlist_route(
    entry_id: UUID,
    payload: FacilityBookingWaitlistConversionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityBookingCheckoutRead:
    return await convert_facility_waitlist_entry(db, identity, entry_id, payload, authz)


@router.get("/summary", response_model=AssetSummaryRead)
async def asset_summary_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> AssetSummaryRead:
    return await asset_summary(db, organization_id)


@router.get("/procurement/recommendations", response_model=list[ProcurementRecommendationRead])
async def procurement_recommendations_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[ProcurementRecommendationRead]:
    return await procurement_recommendations(db, organization_id)


@router.get("/suppliers/scorecard", response_model=list[SupplierScoreRead])
async def supplier_scorecard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SupplierScoreRead]:
    return await supplier_scorecard(db, organization_id)


@router.post("/suppliers/orders", response_model=SupplierOrderRead, status_code=status.HTTP_201_CREATED)
async def create_supplier_order_route(
    payload: SupplierOrderCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SupplierOrderRead:
    return to_supplier_order_read(await create_supplier_order(db, identity, payload, authz))


@router.get("/suppliers/orders", response_model=list[SupplierOrderRead])
async def list_supplier_orders_route(
    organization_id: UUID = Query(),
    open_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> list[SupplierOrderRead]:
    return [
        to_supplier_order_read(order)
        for order in await list_supplier_orders(db, organization_id, open_only=open_only)
    ]


@router.patch("/suppliers/orders/{supplier_order_id}/receive", response_model=SupplierOrderRead)
async def receive_supplier_order_route(
    supplier_order_id: UUID,
    payload: SupplierOrderReceive,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SupplierOrderRead:
    return to_supplier_order_read(await receive_supplier_order(db, identity, supplier_order_id, payload, authz))


@router.post("/suppliers/orders/{supplier_order_id}/submit", response_model=SupplierOrderSubmissionRead)
async def submit_supplier_order_route(
    supplier_order_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SupplierOrderSubmissionRead:
    return await submit_supplier_order(db, identity, supplier_order_id, authz)


@router.post("/suppliers/orders/{supplier_order_id}/invoice-sync", response_model=SupplierInvoiceSyncRead)
async def sync_supplier_invoice_route(
    supplier_order_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SupplierInvoiceSyncRead:
    return await sync_supplier_invoice(db, identity, supplier_order_id, authz)


@router.get("/accounting-export", response_model=AssetAccountingExportRead)
async def asset_accounting_export_route(
    organization_id: UUID = Query(),
    system: str = Query(default="quickbooks", min_length=2, max_length=80),
    basis: str = Query(default="accrual", min_length=2, max_length=40),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AssetAccountingExportRead:
    await ensure_manage_assets(authz, identity, organization_id)
    return await asset_accounting_export(db, organization_id, system, basis)


@router.post("/accounting-export/sync", response_model=AssetAccountingSyncRead)
async def sync_asset_accounting_export_route(
    organization_id: UUID = Query(),
    system: str = Query(default="quickbooks", min_length=2, max_length=80),
    basis: str = Query(default="accrual", min_length=2, max_length=40),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AssetAccountingSyncRead:
    return await sync_asset_accounting_export(db, identity, organization_id, system, basis, authz)


@router.get("/utilization/recommendations", response_model=list[AssetUtilizationRecommendationRead])
async def utilization_recommendations_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AssetUtilizationRecommendationRead]:
    return await utilization_recommendations(db, organization_id)
