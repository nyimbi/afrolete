from typing import Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    AttendanceStatus,
    ConsentCaptureChannel,
    CommunicationChannel,
    EventType,
    MedicalClearanceStatus,
    ParticipationClearanceStatus,
    TravelPlanStatus,
    TravelRiskLevel,
    WeatherAlertLevel,
    WeatherDecision,
)


class EventCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    event_type: EventType
    title: str = Field(min_length=2, max_length=240)
    starts_at: datetime
    ends_at: datetime | None = None
    timezone: str = Field(default="UTC", max_length=80)
    venue_name: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def ends_after_start(self) -> "EventCreate":
        if self.ends_at is not None and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class EventRead(BaseModel):
    id: UUID
    organization_id: UUID
    team_id: UUID | None
    event_type: EventType
    title: str
    starts_at: datetime
    ends_at: datetime | None
    timezone: str
    venue_name: str | None
    notes: str | None


class EventWeatherAssessmentCreate(BaseModel):
    source: str = Field(default="manual", min_length=2, max_length=80)
    observed_at: datetime
    temperature_c: float | None = Field(default=None, ge=-80, le=80)
    heat_index_c: float | None = Field(default=None, ge=-80, le=90)
    wbgt_c: float | None = Field(default=None, ge=-50, le=60)
    humidity_percent: float | None = Field(default=None, ge=0, le=100)
    aqi: int | None = Field(default=None, ge=0, le=500)
    lightning_distance_km: float | None = Field(default=None, ge=0, le=500)
    wind_speed_kph: float | None = Field(default=None, ge=0, le=400)
    wind_gust_kph: float | None = Field(default=None, ge=0, le=500)
    precipitation_mm_per_hr: float | None = Field(default=None, ge=0, le=500)
    notes: str | None = Field(default=None, max_length=4000)


class EventWeatherAssessmentRead(EventWeatherAssessmentCreate):
    id: UUID
    organization_id: UUID
    event_id: UUID
    alert_level: WeatherAlertLevel
    decision: WeatherDecision
    recommended_actions: str


class EventWeatherAlertCreate(BaseModel):
    channel: CommunicationChannel = CommunicationChannel.PUSH
    subject: str | None = Field(default=None, min_length=2, max_length=240)
    body: str | None = Field(default=None, min_length=2, max_length=8000)
    copy_guardians_for_minors: bool = True


class EventWeatherAlertRead(BaseModel):
    event_id: UUID
    assessment_id: UUID
    message_id: UUID
    recipient_count: int
    channel: CommunicationChannel
    subject: str
    urgent: bool


class EventTravelPlanCreate(BaseModel):
    destination: str = Field(min_length=2, max_length=240)
    travel_mode: str = Field(min_length=2, max_length=80)
    departure_at: datetime | None = None
    return_at: datetime | None = None
    route_summary: str | None = Field(default=None, max_length=8000)
    vehicle_details: str | None = Field(default=None, max_length=8000)
    driver_details: str | None = Field(default=None, max_length=8000)
    staff_manifest: str | None = Field(default=None, max_length=8000)
    passenger_manifest: str | None = Field(default=None, max_length=12000)
    lodging_details: str | None = Field(default=None, max_length=8000)
    meal_plan: str | None = Field(default=None, max_length=8000)
    equipment_manifest: str | None = Field(default=None, max_length=8000)
    emergency_contacts: str | None = Field(default=None, max_length=8000)
    medical_access_plan: str | None = Field(default=None, max_length=8000)
    route_weather_risk: str | None = Field(default=None, max_length=80)
    driver_certification_status: str | None = Field(default=None, max_length=80)
    vehicle_inspection_status: str | None = Field(default=None, max_length=80)
    consent_required: bool = True
    consent_due_at: datetime | None = None
    estimated_cost: float | None = Field(default=None, ge=0)
    cost_per_participant: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def return_after_departure(self) -> "EventTravelPlanCreate":
        if self.departure_at is not None and self.return_at is not None and self.return_at <= self.departure_at:
            raise ValueError("return_at must be after departure_at")
        return self


class EventTravelPlanUpdate(BaseModel):
    status: TravelPlanStatus | None = None
    route_summary: str | None = Field(default=None, max_length=8000)
    vehicle_details: str | None = Field(default=None, max_length=8000)
    driver_details: str | None = Field(default=None, max_length=8000)
    staff_manifest: str | None = Field(default=None, max_length=8000)
    passenger_manifest: str | None = Field(default=None, max_length=12000)
    lodging_details: str | None = Field(default=None, max_length=8000)
    meal_plan: str | None = Field(default=None, max_length=8000)
    equipment_manifest: str | None = Field(default=None, max_length=8000)
    emergency_contacts: str | None = Field(default=None, max_length=8000)
    medical_access_plan: str | None = Field(default=None, max_length=8000)
    route_weather_risk: str | None = Field(default=None, max_length=80)
    driver_certification_status: str | None = Field(default=None, max_length=80)
    vehicle_inspection_status: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=4000)


class EventTravelPlanRead(EventTravelPlanCreate):
    id: UUID
    organization_id: UUID
    event_id: UUID
    status: TravelPlanStatus
    risk_level: TravelRiskLevel
    risk_assessment: str


class EventTravelConsentRequestCreate(BaseModel):
    channel: ConsentCaptureChannel = ConsentCaptureChannel.EMAIL
    expires_at: datetime | None = None
    include_unknown_age: bool = True
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelConsentRequestItemRead(BaseModel):
    request_id: UUID
    athlete_person_id: UUID
    guardian_person_id: UUID
    destination: str
    one_time_token: str


class EventTravelConsentBatchRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    created: int
    existing: int
    skipped_no_guardian: int
    skipped_not_minor: int
    requests: list[EventTravelConsentRequestItemRead]


class EventTravelConsentReminderCreate(BaseModel):
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    subject: str | None = Field(default=None, max_length=240)
    body: str | None = Field(default=None, max_length=4000)


class EventTravelConsentReminderRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    message_id: UUID
    pending_request_count: int
    recipient_count: int


class EventTravelConsentReminderRunCreate(BaseModel):
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    due_within_hours: int = Field(default=48, ge=1, le=720)
    send_reminders: bool = True
    subject: str | None = Field(default=None, max_length=240)
    body: str | None = Field(default=None, max_length=4000)


class EventTravelConsentReminderRunPlanRead(BaseModel):
    travel_plan_id: UUID
    destination: str
    travel_mode: str
    consent_due_at: datetime | None
    status: TravelPlanStatus


class EventTravelConsentReminderRunRead(BaseModel):
    event_id: UUID
    due_by: datetime
    due_plan_count: int
    pending_request_count: int
    message_id: UUID | None
    recipient_count: int
    channel: CommunicationChannel
    plans: list[EventTravelConsentReminderRunPlanRead]


class EventTravelManifestParticipantRead(BaseModel):
    person_id: UUID
    display_name: str
    guardian_names: list[str]
    guardian_contacts: list[str]
    medical_clearance_status: MedicalClearanceStatus | None
    medical_clearance_reason: str


class EventTravelManifestRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    destination: str
    participant_count: int
    emergency_contacts: str | None
    medical_access_plan: str | None
    participants: list[EventTravelManifestParticipantRead]


class EventTravelManifestExportCreate(BaseModel):
    format: str = Field(default="csv", pattern="^(csv|text)$")


class EventTravelManifestExportRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    filename: str
    content_type: str
    content: str


class EventTravelManifestOfflineLinkCreate(BaseModel):
    format: str = Field(default="csv", pattern="^(csv|text|pdf)$")
    ttl_seconds: int | None = Field(default=None, ge=60, le=604800)


class EventTravelManifestOfflineLinkRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    checksum: str
    signed_url: str
    expires_at: datetime


class EventTravelFeeInvoiceCreate(BaseModel):
    amount_per_participant: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    due_on: date | None = None
    bill_guardians_for_minors: bool = True
    memo: str | None = Field(default=None, max_length=4000)


class EventTravelFeeInvoiceItemRead(BaseModel):
    invoice_id: UUID
    invoice_number: str
    billed_person_id: UUID
    athlete_person_id: UUID
    amount_due: Decimal
    status: str


class EventTravelFeeInvoiceBatchRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    created: int
    existing: int
    skipped_no_payer: int
    total_amount_due: Decimal
    invoices: list[EventTravelFeeInvoiceItemRead]


class EventTravelFeeCheckoutCreate(BaseModel):
    provider: str = Field(default="manual_gateway", min_length=2, max_length=80)
    checkout_base_url: str = Field(default="/pay/invoices", min_length=2, max_length=500)
    session_base_url: str = Field(default="/pay/sessions", min_length=2, max_length=500)
    success_url: str | None = Field(default=None, max_length=500)
    cancel_url: str | None = Field(default=None, max_length=500)
    expires_at: datetime | None = None


class EventTravelFeeCheckoutItemRead(BaseModel):
    invoice_id: UUID
    invoice_number: str
    billed_person_id: UUID | None
    amount_due: Decimal
    amount_paid: Decimal
    open_amount: Decimal
    currency: str
    status: str
    provider: str
    checkout_url: str
    session_id: str
    session_url: str
    session_status: str
    client_reference: str
    success_url: str | None
    cancel_url: str | None
    expires_at: datetime | None


class EventTravelFeeCheckoutBatchRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    provider: str
    checkout_count: int
    total_open_amount: Decimal
    checkouts: list[EventTravelFeeCheckoutItemRead]


class EventTravelFeeReconciliationPaymentRead(BaseModel):
    payment_id: UUID
    amount: Decimal
    currency: str
    method: str
    external_reference: str | None
    received_at: datetime


class EventTravelFeeReconciliationExceptionRead(BaseModel):
    code: str
    severity: str
    invoice_id: UUID | None = None
    invoice_number: str | None = None
    detail: str
    recommended_action: str


class EventTravelFeeReconciliationItemRead(BaseModel):
    invoice_id: UUID
    invoice_number: str
    billed_person_id: UUID | None
    amount_due: Decimal
    amount_paid: Decimal
    open_amount: Decimal
    currency: str
    status: str
    session_id: str
    session_status: str
    payment_count: int
    last_payment_reference: str | None
    payments: list[EventTravelFeeReconciliationPaymentRead]
    exceptions: list[EventTravelFeeReconciliationExceptionRead]


class EventTravelFeeReconciliationRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    provider: str
    invoice_count: int
    paid_count: int
    partial_count: int
    unpaid_count: int
    total_due: Decimal
    total_paid: Decimal
    total_open: Decimal
    exception_count: int
    exceptions: list[EventTravelFeeReconciliationExceptionRead]
    reconciled_at: datetime
    items: list[EventTravelFeeReconciliationItemRead]


class EventTravelFeeReconciliationResolutionCreate(BaseModel):
    invoice_id: UUID
    action: str = Field(
        pattern=(
            "^(apply_waiver|attach_payment_reference|rebuild_missing_payment|refund_overpayment|"
            "sync_invoice_paid_total|rebook_payment_currency)$"
        )
    )
    payment_id: UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    external_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelFeeReconciliationResolutionRead(BaseModel):
    travel_plan_id: UUID
    invoice_id: UUID
    action: str
    payment_id: UUID | None
    message: str
    reconciliation: EventTravelFeeReconciliationRead


class EventTravelFeeHostedCheckoutRead(BaseModel):
    invoice_id: UUID
    invoice_number: str
    organization_id: UUID
    billed_person_id: UUID | None
    title: str
    memo: str | None
    due_on: date | None
    amount_due: Decimal
    amount_paid: Decimal
    open_amount: Decimal
    currency: str
    status: str
    provider: str
    session_id: str
    session_status: str
    client_reference: str
    payment_methods: list[str]
    settlement_endpoint: str
    checkout_summary: str


class EventTravelFeeCheckoutSettlementCreate(BaseModel):
    invoice_id: UUID
    provider: str = Field(default="manual_gateway", min_length=2, max_length=80)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    method: str = Field(default="hosted_payment_page", min_length=2, max_length=80)
    external_payment_id: str | None = Field(default=None, max_length=240)
    status: str = Field(default="succeeded", pattern="^(succeeded|pending|failed|cancelled)$")
    raw_reference: str | None = Field(default=None, max_length=2000)


class EventTravelFeePaymentWebhookCreate(BaseModel):
    invoice_id: UUID | None = None
    session_id: str | None = Field(default=None, min_length=8, max_length=120)
    provider: str = Field(default="provider_neutral", min_length=2, max_length=80)
    event_type: str = Field(default="payment.succeeded", min_length=2, max_length=120)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    method: str = Field(default="provider_webhook", min_length=2, max_length=80)
    external_payment_id: str | None = Field(default=None, max_length=240)
    status: str = Field(default="succeeded", pattern="^(succeeded|pending|failed|cancelled)$")
    raw_reference: str | None = Field(default=None, max_length=2000)
    raw_payload: dict[str, Any] | None = None


class EventTravelFeeCheckoutSettlementRead(BaseModel):
    invoice_id: UUID
    provider: str
    accepted: bool
    signature_required: bool = False
    signature_validated: bool = False
    payment_id: UUID | None
    invoice_status: str
    amount_paid: Decimal
    open_amount: Decimal
    session_status: str
    message: str


class EventTravelApprovalCreate(BaseModel):
    approval_level: str = Field(default="school", min_length=2, max_length=80)
    approver_person_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelApprovalUpdate(BaseModel):
    status: str = Field(pattern="^(pending|approved|rejected|cancelled)$")
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelApprovalRead(BaseModel):
    id: UUID
    organization_id: UUID
    travel_plan_id: UUID
    approval_level: str
    status: str
    approver_person_id: UUID | None
    decided_by_person_id: UUID | None
    decided_at: datetime | None
    notes: str | None


class EventTravelApprovalRoutingCreate(BaseModel):
    include_school: bool = True
    include_association: bool = True
    include_operations: bool = True
    include_medical: bool = True
    include_finance: bool = True
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelApprovalRoutingRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    recommended_levels: list[str]
    created: int
    existing: int
    rationale: list[str]
    approvals: list[EventTravelApprovalRead]


class EventTravelChecklistSeedCreate(BaseModel):
    checklist_type: str = Field(default="pre_trip_inspection", min_length=2, max_length=80)
    items: list[str] | None = None


class EventTravelChecklistItemUpdate(BaseModel):
    status: str = Field(pattern="^(pending|completed|blocked|not_applicable)$")
    evidence_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelChecklistItemRead(BaseModel):
    id: UUID
    organization_id: UUID
    travel_plan_id: UUID
    checklist_type: str
    item_label: str
    status: str
    completed_by_person_id: UUID | None
    completed_at: datetime | None
    evidence_url: str | None
    notes: str | None


class EventTravelChecklistEvidenceUploadCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=240)
    content_type: str = Field(default="application/octet-stream", max_length=120)
    content_base64: str = Field(min_length=1)
    status: str = Field(default="completed", pattern="^(pending|completed|blocked|not_applicable)$")
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelChecklistEvidenceUploadRead(BaseModel):
    checklist_item_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    checksum: str
    evidence_url: str
    checklist_item: EventTravelChecklistItemRead


class EventTravelLocationUpdateCreate(BaseModel):
    phase: str = Field(default="en_route", pattern="^(departed|en_route|delayed|arrived|returned)$")
    source: str = Field(default="manual", min_length=2, max_length=80)
    recorded_at: datetime | None = None
    latitude: Decimal = Field(ge=-90, le=90, max_digits=9, decimal_places=6)
    longitude: Decimal = Field(ge=-180, le=180, max_digits=9, decimal_places=6)
    speed_kph: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=2)
    heading_degrees: Decimal | None = Field(default=None, ge=0, le=360, max_digits=6, decimal_places=2)
    notify_guardians: bool = True
    channel: CommunicationChannel = CommunicationChannel.PUSH
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelLocationUpdateRead(BaseModel):
    id: UUID
    organization_id: UUID
    travel_plan_id: UUID
    phase: str
    source: str
    recorded_at: datetime
    recorded_by_person_id: UUID | None
    latitude: Decimal
    longitude: Decimal
    speed_kph: Decimal | None
    heading_degrees: Decimal | None
    notification_message_id: UUID | None
    notification_recipient_count: int = 0
    notes: str | None


class EventTravelTelemetryStreamRead(BaseModel):
    travel_plan_id: UUID
    stream_url: str
    content_type: str = "application/x-ndjson"
    update_count: int
    latest_update_id: UUID | None = None
    latest_recorded_at: datetime | None = None
    replay_window_seconds: int = 300


class EventTravelMapPathRead(BaseModel):
    sequence: int
    latitude: Decimal
    longitude: Decimal
    recorded_at: datetime
    phase: str
    source: str


class EventTravelMapMarkerRead(BaseModel):
    label: str
    marker_type: str
    latitude: Decimal
    longitude: Decimal
    recorded_at: datetime | None = None
    status: str | None = None


class EventTravelMapBoundsRead(BaseModel):
    min_latitude: Decimal | None = None
    max_latitude: Decimal | None = None
    min_longitude: Decimal | None = None
    max_longitude: Decimal | None = None


class EventTravelMapRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    destination: str
    provider_hint: str = "provider-neutral"
    path: list[EventTravelMapPathRead]
    markers: list[EventTravelMapMarkerRead]
    bounds: EventTravelMapBoundsRead
    latest_phase: str | None = None
    latest_recorded_at: datetime | None = None


class EventTravelDeviceLocationIngestCreate(BaseModel):
    device_id: str = Field(min_length=2, max_length=120)
    provider: str = Field(default="hardware-gps", min_length=2, max_length=80)
    phase: str = Field(default="en_route", pattern="^(departed|en_route|delayed|arrived|returned)$")
    recorded_at: datetime | None = None
    latitude: Decimal = Field(ge=-90, le=90, max_digits=9, decimal_places=6)
    longitude: Decimal = Field(ge=-180, le=180, max_digits=9, decimal_places=6)
    speed_kph: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=2)
    heading_degrees: Decimal | None = Field(default=None, ge=0, le=360, max_digits=6, decimal_places=2)
    accuracy_meters: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    battery_percent: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    external_event_id: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelDeviceLocationIngestRead(BaseModel):
    travel_plan_id: UUID
    device_id: str
    provider: str
    device_registration_id: UUID | None = None
    device_status: str | None = None
    replay_protected: bool = False
    external_event_id: str | None = None
    replay_retention_days: int | None = None
    replay_retention_source: str | None = None
    replay_events_pruned: int = 0
    signature_required: bool
    signature_validated: bool
    update: EventTravelLocationUpdateRead


class EventTravelDeviceCreate(BaseModel):
    provider: str = Field(default="hardware-gps", min_length=2, max_length=80)
    device_id: str = Field(min_length=2, max_length=120)
    label: str = Field(min_length=2, max_length=160)
    status: str = Field(default="active", pattern="^(active|standby|disabled|lost|maintenance)$")
    assigned_vehicle: str | None = Field(default=None, max_length=180)
    installed_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelDeviceUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=2, max_length=160)
    status: str | None = Field(default=None, pattern="^(active|standby|disabled|lost|maintenance)$")
    assigned_vehicle: str | None = Field(default=None, max_length=180)
    installed_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelDeviceRead(EventTravelDeviceCreate):
    id: UUID
    organization_id: UUID
    travel_plan_id: UUID
    last_seen_at: datetime | None
    last_location_update_id: UUID | None
    last_battery_percent: Decimal | None
    last_accuracy_meters: Decimal | None
    secret_configured: bool = False
    secret_storage_mode: str = "database"
    secret_vault_provider: str | None = None
    secret_vault_reference: str | None = None
    secret_rotated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EventTravelDeviceSecretRead(BaseModel):
    id: UUID
    travel_plan_id: UUID
    provider: str
    device_id: str
    label: str
    ingest_secret: str
    secret_storage_mode: str = "database"
    secret_vault_provider: str | None = None
    secret_vault_reference: str | None = None
    secret_rotated_at: datetime


class EventTravelDeviceFleetItemRead(BaseModel):
    id: UUID
    organization_id: UUID
    travel_plan_id: UUID
    event_id: UUID
    destination: str
    provider: str
    device_id: str
    label: str
    status: str
    assigned_vehicle: str | None
    last_seen_at: datetime | None
    last_battery_percent: Decimal | None
    last_accuracy_meters: Decimal | None
    secret_configured: bool = False
    secret_storage_mode: str = "database"
    secret_vault_provider: str | None = None
    secret_vault_reference: str | None = None


class EventTravelDeviceFleetInventoryRead(BaseModel):
    organization_id: UUID
    total_devices: int
    active_devices: int
    maintenance_devices: int
    disabled_devices: int
    lost_devices: int
    stale_devices: int
    low_battery_devices: int
    devices: list[EventTravelDeviceFleetItemRead]


class EventTravelGeofencePoint(BaseModel):
    latitude: Decimal = Field(ge=-90, le=90, max_digits=9, decimal_places=6)
    longitude: Decimal = Field(ge=-180, le=180, max_digits=9, decimal_places=6)


class EventTravelGeofenceCheckCreate(BaseModel):
    center_latitude: Decimal = Field(ge=-90, le=90, max_digits=9, decimal_places=6)
    center_longitude: Decimal = Field(ge=-180, le=180, max_digits=9, decimal_places=6)
    radius_km: Decimal = Field(gt=0, le=20000, max_digits=8, decimal_places=3)
    label: str = Field(default="travel safety zone", min_length=2, max_length=160)
    polygon_coordinates: list[EventTravelGeofencePoint] | None = None
    alert_on_breach: bool = True
    channel: CommunicationChannel = CommunicationChannel.PUSH


class EventTravelGeofenceZoneCreate(EventTravelGeofenceCheckCreate):
    provider: str | None = Field(default=None, max_length=80)
    provider_zone_id: str | None = Field(default=None, max_length=180)
    provider_revision: str | None = Field(default=None, max_length=80)
    active: bool = True
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelGeofenceZoneUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=2, max_length=160)
    center_latitude: Decimal | None = Field(default=None, ge=-90, le=90, max_digits=9, decimal_places=6)
    center_longitude: Decimal | None = Field(default=None, ge=-180, le=180, max_digits=9, decimal_places=6)
    radius_km: Decimal | None = Field(default=None, gt=0, le=20000, max_digits=8, decimal_places=3)
    polygon_coordinates: list[EventTravelGeofencePoint] | None = None
    provider: str | None = Field(default=None, max_length=80)
    provider_zone_id: str | None = Field(default=None, max_length=180)
    provider_revision: str | None = Field(default=None, max_length=80)
    alert_on_breach: bool | None = None
    channel: CommunicationChannel | None = None
    active: bool | None = None
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelGeofenceZoneRead(EventTravelGeofenceZoneCreate):
    id: UUID
    organization_id: UUID
    travel_plan_id: UUID
    created_at: datetime
    updated_at: datetime


class EventTravelGeofenceCheckRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    latest_update_id: UUID
    label: str
    center_latitude: Decimal
    center_longitude: Decimal
    radius_km: Decimal
    distance_km: Decimal
    boundary_type: str = "radius"
    polygon_vertices: int = 0
    inside: bool
    breached: bool
    message_id: UUID | None
    recipient_count: int
    recommendation: str


class EventTravelDriverRatingCreate(BaseModel):
    driver_name: str = Field(min_length=2, max_length=160)
    driver_person_id: UUID | None = None
    vehicle_label: str | None = Field(default=None, max_length=180)
    overall_score: int = Field(ge=1, le=5)
    safety_score: int | None = Field(default=None, ge=1, le=5)
    punctuality_score: int | None = Field(default=None, ge=1, le=5)
    communication_score: int | None = Field(default=None, ge=1, le=5)
    vehicle_condition_score: int | None = Field(default=None, ge=1, le=5)
    would_use_again: bool = True
    incident_reported: bool = False
    reviewer_person_id: UUID | None = None
    reviewed_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelDriverRatingRead(EventTravelDriverRatingCreate):
    id: UUID
    organization_id: UUID
    travel_plan_id: UUID
    created_at: datetime
    updated_at: datetime


class EventTravelDriverRatingSummaryRead(BaseModel):
    travel_plan_id: UUID
    rating_count: int
    average_overall_score: Decimal | None
    would_use_again_count: int
    incident_reported_count: int


class EventTravelBackupDriverCreate(BaseModel):
    driver_name: str = Field(min_length=2, max_length=160)
    driver_person_id: UUID | None = None
    phone: str | None = Field(default=None, max_length=80)
    vehicle_label: str | None = Field(default=None, max_length=180)
    capacity: int = Field(default=0, ge=0, le=80)
    license_status: str = Field(default="unverified", min_length=2, max_length=80)
    background_check_status: str = Field(default="unverified", min_length=2, max_length=80)
    availability_status: str = Field(default="standby", pattern="^(standby|available|dispatched|unavailable)$")
    response_minutes: int | None = Field(default=None, ge=0, le=1440)
    priority: int = Field(default=1, ge=1, le=20)
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelBackupDriverUpdate(BaseModel):
    phone: str | None = Field(default=None, max_length=80)
    vehicle_label: str | None = Field(default=None, max_length=180)
    capacity: int | None = Field(default=None, ge=0, le=80)
    license_status: str | None = Field(default=None, min_length=2, max_length=80)
    background_check_status: str | None = Field(default=None, min_length=2, max_length=80)
    availability_status: str | None = Field(
        default=None,
        pattern="^(standby|available|dispatched|unavailable)$",
    )
    response_minutes: int | None = Field(default=None, ge=0, le=1440)
    priority: int | None = Field(default=None, ge=1, le=20)
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelBackupDriverRead(EventTravelBackupDriverCreate):
    id: UUID
    organization_id: UUID
    travel_plan_id: UUID
    dispatched_at: datetime | None
    dispatched_by_person_id: UUID | None
    dispatch_message_id: UUID | None
    dispatch_reason: str | None
    created_at: datetime
    updated_at: datetime


class EventTravelBackupDriverDispatchCreate(BaseModel):
    minimum_capacity: int = Field(default=1, ge=0, le=80)
    require_verified: bool = True
    channel: CommunicationChannel = CommunicationChannel.SMS
    reason: str = Field(default="Primary driver unavailable", min_length=2, max_length=500)
    notify_driver: bool = True


class EventTravelBackupDriverDispatchRead(BaseModel):
    travel_plan_id: UUID
    driver: EventTravelBackupDriverRead
    eligible_driver_count: int
    message_id: UUID | None
    recipient_count: int = 0
    rationale: list[str]


class EventTravelDriverMarketplaceCandidateRead(BaseModel):
    driver: EventTravelBackupDriverRead
    match_score: Decimal
    verified: bool
    rating_count: int
    average_rating: Decimal | None
    incident_reported_count: int
    response_minutes: int | None
    marketplace_status: str
    rationale: list[str]


class EventTravelDriverMarketplaceRead(BaseModel):
    travel_plan_id: UUID
    candidate_count: int
    verified_candidate_count: int
    recommended_driver_id: UUID | None
    candidates: list[EventTravelDriverMarketplaceCandidateRead]


class EventTravelExpenseCreate(BaseModel):
    category: str = Field(default="fuel", min_length=2, max_length=80)
    vendor: str | None = Field(default=None, max_length=180)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    incurred_at: datetime | None = None
    paid_by_person_id: UUID | None = None
    receipt_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelExpenseUpdate(BaseModel):
    reimbursement_status: str = Field(pattern="^(draft|submitted|approved|reimbursed|rejected)$")
    receipt_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelExpenseRead(BaseModel):
    id: UUID
    organization_id: UUID
    travel_plan_id: UUID
    category: str
    vendor: str | None
    amount: Decimal
    currency: str
    incurred_at: datetime
    paid_by_person_id: UUID | None
    reimbursement_status: str
    approved_by_person_id: UUID | None
    reimbursed_at: datetime | None
    payout_provider: str | None = None
    payout_reference: str | None = None
    payout_status: str | None = None
    payout_requested_at: datetime | None = None
    payout_processed_by_person_id: UUID | None = None
    payout_adapter_mode: str | None = None
    payout_destination: str | None = None
    payout_idempotency_key: str | None = None
    payout_provider_status_code: int | None = None
    payout_provider_response: str | None = None
    receipt_url: str | None
    notes: str | None


class EventTravelExpensePayoutCreate(BaseModel):
    provider: str = Field(default="manual_reimbursement", min_length=2, max_length=80)
    external_reference: str | None = Field(default=None, max_length=180)
    destination: str | None = Field(default=None, max_length=240)
    adapter_mode: str | None = Field(default=None, max_length=80)
    idempotency_key: str | None = Field(default=None, max_length=180)
    mark_reimbursed: bool = True
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelExpensePayoutRead(BaseModel):
    expense_id: UUID
    provider: str
    payout_reference: str
    payout_status: str
    amount: Decimal
    currency: str
    processed_at: datetime
    adapter_mode: str
    destination: str | None
    idempotency_key: str
    provider_status_code: int | None
    provider_response: str | None
    expense: EventTravelExpenseRead


class EventTravelExpensePayoutCallbackCreate(BaseModel):
    provider: str = Field(default="manual_reimbursement", min_length=2, max_length=80)
    payout_reference: str | None = Field(default=None, max_length=180)
    idempotency_key: str | None = Field(default=None, max_length=180)
    status: str = Field(default="paid", min_length=2, max_length=80)
    provider_status_code: int | None = Field(default=None, ge=100, le=599)
    external_event_id: str | None = Field(default=None, max_length=180)
    raw_payload: dict[str, Any] | None = None
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelExpensePayoutCallbackRead(BaseModel):
    accepted: bool
    signature_required: bool = False
    signature_validated: bool = False
    matched_by: str
    payout_reference: str | None
    payout_status: str
    reimbursement_status: str
    message: str
    expense: EventTravelExpenseRead


class EventTravelReceiptUploadCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=240)
    content_type: str = Field(default="application/octet-stream", max_length=120)
    content_base64: str = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelReceiptUploadRead(BaseModel):
    expense_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    checksum: str
    receipt_url: str
    expense: EventTravelExpenseRead


class EventTravelCarpoolRideCreate(BaseModel):
    ride_type: str = Field(default="request", pattern="^(request|offer)$")
    rider_person_id: UUID | None = None
    driver_person_id: UUID | None = None
    pickup_location: str = Field(min_length=2, max_length=240)
    pickup_latitude: Decimal | None = Field(default=None, ge=-90, le=90, max_digits=9, decimal_places=6)
    pickup_longitude: Decimal | None = Field(default=None, ge=-180, le=180, max_digits=9, decimal_places=6)
    dropoff_location: str | None = Field(default=None, max_length=240)
    dropoff_latitude: Decimal | None = Field(default=None, ge=-90, le=90, max_digits=9, decimal_places=6)
    dropoff_longitude: Decimal | None = Field(default=None, ge=-180, le=180, max_digits=9, decimal_places=6)
    seats_requested: int = Field(default=1, ge=1, le=20)
    seats_available: int = Field(default=0, ge=0, le=20)
    departure_window_start: datetime | None = None
    departure_window_end: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def window_end_after_start(self) -> "EventTravelCarpoolRideCreate":
        if (
            self.departure_window_start is not None
            and self.departure_window_end is not None
            and self.departure_window_end <= self.departure_window_start
        ):
            raise ValueError("departure_window_end must be after departure_window_start")
        return self


class EventTravelCarpoolRideUpdate(BaseModel):
    status: str = Field(pattern="^(open|matched|confirmed|cancelled)$")
    rider_person_id: UUID | None = None
    driver_person_id: UUID | None = None
    match_score: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    notes: str | None = Field(default=None, max_length=2000)


class EventTravelCarpoolRideRead(BaseModel):
    id: UUID
    organization_id: UUID
    travel_plan_id: UUID
    ride_type: str
    status: str
    rider_person_id: UUID | None
    driver_person_id: UUID | None
    pickup_location: str
    pickup_latitude: Decimal | None
    pickup_longitude: Decimal | None
    dropoff_location: str | None
    dropoff_latitude: Decimal | None
    dropoff_longitude: Decimal | None
    seats_requested: int
    seats_available: int
    departure_window_start: datetime | None
    departure_window_end: datetime | None
    match_score: Decimal | None
    matched_at: datetime | None
    notes: str | None


class EventTravelCarpoolAutoMatchCreate(BaseModel):
    minimum_score: Decimal = Field(default=Decimal("55.00"), ge=0, le=100, max_digits=5, decimal_places=2)
    confirm_matches: bool = False


class EventTravelCarpoolAutoMatchPairRead(BaseModel):
    request_id: UUID
    offer_id: UUID
    score: Decimal
    pickup_distance_km: Decimal | None = None
    dropoff_distance_km: Decimal | None = None
    seats_requested: int
    seats_available: int
    pickup_match: str
    window_match: str


class EventTravelCarpoolAutoMatchRead(BaseModel):
    travel_plan_id: UUID
    matched_count: int
    request_count: int
    offer_count: int
    pairs: list[EventTravelCarpoolAutoMatchPairRead]
    rides: list[EventTravelCarpoolRideRead]


class EventTravelReadinessRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    ready: bool
    recommended_status: TravelPlanStatus
    risk_level: TravelRiskLevel
    blockers: list[str]
    warnings: list[str]
    approval_count: int
    pending_approval_count: int
    rejected_approval_count: int
    checklist_count: int
    pending_checklist_count: int
    blocked_checklist_count: int
    pending_consent_request_count: int


class EventTravelRouteOptimizationCreate(BaseModel):
    strategy: str = Field(default="balanced", pattern="^(balanced|fastest|safest|carpool_dense)$")
    include_carpools: bool = True
    avoid_weather_risk: bool = True


class EventTravelRouteStopRead(BaseModel):
    sequence: int
    stop_type: str
    label: str
    location: str
    pickup_window_start: datetime | None = None
    pickup_window_end: datetime | None = None
    seats: int = 0
    notes: str | None = None


class EventTravelRouteOptimizationRead(BaseModel):
    event_id: UUID
    travel_plan_id: UUID
    strategy: str
    recommended_strategy: str
    destination: str
    stop_count: int
    recommended_departure_at: datetime | None
    estimated_duration_minutes: int
    traffic_delay_minutes: int = 0
    weather_delay_minutes: int = 0
    reroute_required: bool = False
    reroute_reason: str | None = None
    latest_weather_alert_level: WeatherAlertLevel | None = None
    latest_weather_decision: WeatherDecision | None = None
    risk_level: TravelRiskLevel
    warnings: list[str]
    reroute_actions: list[str] = []
    route_summary: str
    stops: list[EventTravelRouteStopRead]


class AttendanceRecordUpsert(BaseModel):
    person_id: UUID
    status: AttendanceStatus
    note: str | None = Field(default=None, max_length=2000)


class AttendanceRecordRead(BaseModel):
    id: UUID
    event_id: UUID
    person_id: UUID
    status: AttendanceStatus
    recorded_by_person_id: UUID | None
    guardian_consent_id: UUID | None
    note: str | None
    clearance_status: ParticipationClearanceStatus | None = None
    medical_clearance_status: MedicalClearanceStatus | None = None
    medical_clearance_id: UUID | None = None
    medical_clearance_reason: str | None = None


class AttendanceSeedRead(BaseModel):
    event_id: UUID
    created: int
    existing: int
