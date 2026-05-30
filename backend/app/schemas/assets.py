from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    AssetCondition,
    CheckoutStatus,
    CommunicationChannel,
    CommunicationScopeType,
    EmergencyActionPlanStatus,
    EmergencyActivationStatus,
    EmergencyType,
    EquipmentStatus,
    FacilityBookingStatus,
    FacilityStatus,
    FacilityType,
    SafeguardingIncidentSeverity,
    SafeguardingIncidentType,
    WorkOrderPriority,
    WorkOrderStatus,
)
from app.schemas.commercial import FinanceInvoiceRead, FinancePaymentRead


class FacilityCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    facility_type: FacilityType
    sport: str | None = Field(default=None, max_length=80)
    surface: str | None = Field(default=None, max_length=120)
    capacity: int | None = Field(default=None, ge=0, le=1_000_000)
    location: str | None = Field(default=None, max_length=240)
    dimensions: str | None = Field(default=None, max_length=120)
    amenities: str | None = Field(default=None, max_length=4000)
    hourly_rate: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    maintenance_budget: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    condition: AssetCondition = AssetCondition.GOOD
    insurance_policy_ref: str | None = Field(default=None, max_length=180)
    last_inspection_on: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class FacilityRead(FacilityCreate):
    id: UUID
    status: FacilityStatus


class FacilityPublicListingRead(FacilityRead):
    rule: "FacilityBookingRuleRead"
    availability: "FacilityAvailabilityRead"
    public_rate: Decimal
    rate_summary: str
    next_available_slot: datetime | None = None


class FacilityBookingRuleCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    min_booking_minutes: int = Field(default=60, ge=15, le=24 * 60)
    max_booking_minutes: int = Field(default=240, ge=15, le=24 * 60)
    buffer_minutes: int = Field(default=30, ge=0, le=240)
    advance_booking_days: int = Field(default=90, ge=0, le=730)
    requires_approval: bool = False
    allow_public_booking: bool = False
    cancellation_notice_hours: int = Field(default=24, ge=0, le=720)
    peak_hour_rate_multiplier: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    public_booking_note: str | None = Field(default=None, max_length=4000)
    status: str = Field(default="active", min_length=2, max_length=40)

    @model_validator(mode="after")
    def valid_duration_bounds(self) -> "FacilityBookingRuleCreate":
        if self.max_booking_minutes < self.min_booking_minutes:
            raise ValueError("max_booking_minutes must be at least min_booking_minutes")
        return self


class FacilityBookingRuleRead(FacilityBookingRuleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class EmergencyActionPlanCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID | None = None
    title: str = Field(min_length=2, max_length=240)
    emergency_type: EmergencyType
    effective_from: date | None = None
    review_due_on: date | None = None
    emergency_contacts: str = Field(min_length=2, max_length=8000)
    evacuation_routes: str | None = Field(default=None, max_length=8000)
    medical_protocols: str | None = Field(default=None, max_length=8000)
    weather_protocols: str | None = Field(default=None, max_length=8000)
    communication_protocols: str | None = Field(default=None, max_length=8000)
    incident_command_roles: str | None = Field(default=None, max_length=8000)
    escalation_matrix: str | None = Field(default=None, max_length=8000)
    external_agency_contacts: str | None = Field(default=None, max_length=8000)
    equipment_locations: str | None = Field(default=None, max_length=8000)
    assembly_points: str | None = Field(default=None, max_length=8000)
    special_needs_plan: str | None = Field(default=None, max_length=8000)
    notes: str | None = Field(default=None, max_length=4000)


class EmergencyActionPlanUpdate(BaseModel):
    status: EmergencyActionPlanStatus | None = None
    review_due_on: date | None = None
    emergency_contacts: str | None = Field(default=None, max_length=8000)
    evacuation_routes: str | None = Field(default=None, max_length=8000)
    medical_protocols: str | None = Field(default=None, max_length=8000)
    weather_protocols: str | None = Field(default=None, max_length=8000)
    communication_protocols: str | None = Field(default=None, max_length=8000)
    incident_command_roles: str | None = Field(default=None, max_length=8000)
    escalation_matrix: str | None = Field(default=None, max_length=8000)
    external_agency_contacts: str | None = Field(default=None, max_length=8000)
    equipment_locations: str | None = Field(default=None, max_length=8000)
    assembly_points: str | None = Field(default=None, max_length=8000)
    special_needs_plan: str | None = Field(default=None, max_length=8000)
    notes: str | None = Field(default=None, max_length=4000)


class EmergencyActionPlanRead(EmergencyActionPlanCreate):
    id: UUID
    status: EmergencyActionPlanStatus


class EmergencyPlanActivationCreate(BaseModel):
    organization_id: UUID
    plan_id: UUID
    facility_id: UUID | None = None
    incident_id: UUID | None = None
    emergency_type: EmergencyType
    location_detail: str = Field(min_length=2, max_length=240)
    activated_at: datetime | None = None
    escalation_level: int = Field(default=1, ge=1, le=5)
    assigned_responders: str | None = Field(default=None, max_length=8000)
    guidance_steps: str | None = Field(default=None, max_length=8000)
    communication_log: str | None = Field(default=None, max_length=12000)
    notes: str | None = Field(default=None, max_length=4000)


class EmergencyPlanActivationUpdate(BaseModel):
    status: EmergencyActivationStatus | None = None
    closed_at: datetime | None = None
    escalation_level: int | None = Field(default=None, ge=1, le=5)
    assigned_responders: str | None = Field(default=None, max_length=8000)
    guidance_steps: str | None = Field(default=None, max_length=8000)
    communication_log: str | None = Field(default=None, max_length=12000)
    outcome_summary: str | None = Field(default=None, max_length=8000)
    response_time_seconds: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=4000)


class EmergencyPlanActivationRead(BaseModel):
    id: UUID
    organization_id: UUID
    plan_id: UUID
    facility_id: UUID | None
    incident_id: UUID | None
    activated_by_person_id: UUID | None
    closed_by_person_id: UUID | None
    emergency_type: EmergencyType
    status: EmergencyActivationStatus
    location_detail: str
    activated_at: datetime
    closed_at: datetime | None
    escalation_level: int
    assigned_responders: str | None
    guidance_steps: str | None
    communication_log: str | None
    outcome_summary: str | None
    response_time_seconds: int | None
    notes: str | None


class EmergencyActivationAlertCreate(BaseModel):
    channel: CommunicationChannel = CommunicationChannel.PUSH
    scope_type: CommunicationScopeType = CommunicationScopeType.ORGANIZATION
    scope_id: UUID | None = None
    recipient_person_ids: list[UUID] = Field(default_factory=list)
    subject: str | None = Field(default=None, min_length=2, max_length=240)
    body: str | None = Field(default=None, min_length=2, max_length=8000)
    copy_guardians_for_minors: bool = True


class EmergencyActivationAlertRead(BaseModel):
    activation_id: UUID
    message_id: UUID
    recipient_count: int
    channel: CommunicationChannel
    subject: str
    urgent: bool


class EmergencyEscalationTimerRunCreate(BaseModel):
    organization_id: UUID
    unresolved_after_minutes: int = Field(default=15, ge=0, le=10080)
    repeat_after_minutes: int = Field(default=15, ge=1, le=10080)
    limit: int = Field(default=50, ge=1, le=500)
    dry_run: bool = False


class EmergencyEscalationTimerRunRead(BaseModel):
    organization_id: UUID | None
    eligible_count: int
    executed_count: int
    escalated_count: int
    skipped_count: int
    failed_count: int
    dry_run: bool = False
    activation_ids: list[UUID]
    max_level_count: int


class EmergencyActivationIncidentCreate(BaseModel):
    incident_type: SafeguardingIncidentType | None = None
    severity: SafeguardingIncidentSeverity = SafeguardingIncidentSeverity.HIGH
    title: str | None = Field(default=None, min_length=2, max_length=240)
    description: str | None = Field(default=None, min_length=2, max_length=8000)
    immediate_action: str | None = Field(default=None, max_length=4000)
    medical_follow_up_required: str = Field(default="unknown", max_length=40)
    regulatory_report_required: bool = False


class EquipmentItemCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID | None = None
    team_id: UUID | None = None
    name: str = Field(min_length=2, max_length=180)
    category: str = Field(min_length=2, max_length=100)
    subcategory: str | None = Field(default=None, max_length=100)
    brand: str | None = Field(default=None, max_length=120)
    model: str | None = Field(default=None, max_length=120)
    tag_code: str | None = Field(default=None, max_length=120)
    serial_number: str | None = Field(default=None, max_length=160)
    quantity_total: int = Field(default=1, ge=1)
    quantity_available: int | None = Field(default=None, ge=0)
    condition: AssetCondition = AssetCondition.GOOD
    storage_location: str | None = Field(default=None, max_length=240)
    min_stock_level: int = Field(default=0, ge=0)
    reorder_point: int = Field(default=0, ge=0)
    unit_value: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    depreciation_rate: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    warranty_expires_on: date | None = None
    last_audit_on: date | None = None
    photo_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def valid_quantities(self) -> "EquipmentItemCreate":
        if self.quantity_available is None:
            self.quantity_available = self.quantity_total
        if self.quantity_available > self.quantity_total:
            raise ValueError("quantity_available cannot exceed quantity_total")
        return self


class EquipmentItemRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_id: UUID | None
    team_id: UUID | None
    name: str
    category: str
    subcategory: str | None
    brand: str | None
    model: str | None
    tag_code: str | None
    serial_number: str | None
    quantity_total: int
    quantity_available: int
    condition: AssetCondition
    status: EquipmentStatus
    storage_location: str | None
    min_stock_level: int
    reorder_point: int
    unit_value: Decimal | None
    depreciation_rate: Decimal | None
    warranty_expires_on: date | None
    last_audit_on: date | None
    photo_url: str | None
    notes: str | None


class EquipmentPhotoUpdate(BaseModel):
    photo_url: str = Field(min_length=4, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)


class EquipmentFileUploadCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=240)
    content_type: str = Field(default="application/octet-stream", max_length=120)
    content_base64: str = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=4000)
    mark_as_photo: bool = False


class EquipmentFileRead(BaseModel):
    id: UUID
    organization_id: UUID
    equipment_item_id: UUID
    uploaded_by_person_id: UUID | None
    filename: str
    content_type: str
    size_bytes: int
    checksum: str
    storage_url: str
    notes: str | None


class EquipmentScanRead(BaseModel):
    scanned_code: str
    match_type: str
    item: EquipmentItemRead


class EquipmentScanEventCreate(BaseModel):
    organization_id: UUID
    scanned_code: str = Field(min_length=1, max_length=160)
    reader_id: str = Field(default="manual-reader", min_length=1, max_length=160)
    reader_location: str | None = Field(default=None, max_length=240)
    source: str = Field(default="rfid_reader", min_length=2, max_length=40)
    movement: str = Field(default="audit", min_length=2, max_length=40)
    scanned_at: datetime | None = None
    external_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)


class EquipmentScanEventRead(BaseModel):
    id: UUID
    organization_id: UUID
    equipment_item_id: UUID | None
    scanned_code: str
    match_type: str | None
    item_name: str | None
    reader_id: str
    reader_location: str | None
    source: str
    movement: str
    matched: bool
    scanned_at: datetime
    external_reference: str | None
    notes: str | None


class EquipmentReaderCreate(BaseModel):
    organization_id: UUID
    reader_id: str = Field(min_length=2, max_length=160)
    name: str = Field(min_length=2, max_length=180)
    location: str | None = Field(default=None, max_length=240)
    status: str = Field(default="active", min_length=2, max_length=40)
    api_key: str | None = Field(default=None, min_length=16, max_length=200)
    notes: str | None = Field(default=None, max_length=4000)


class EquipmentReaderRead(BaseModel):
    id: UUID
    organization_id: UUID
    reader_id: str
    name: str
    location: str | None
    status: str
    last_seen_at: datetime | None
    last_scan_at: datetime | None
    notes: str | None


class EquipmentReaderProvisionRead(BaseModel):
    reader: EquipmentReaderRead
    api_key: str


class EquipmentReaderGatewayScanCreate(BaseModel):
    scanned_code: str = Field(min_length=1, max_length=160)
    movement: str = Field(default="audit", min_length=2, max_length=40)
    scanned_at: datetime | None = None
    external_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)


class ProcurementRecommendationRead(BaseModel):
    equipment_item_id: UUID
    item_name: str
    category: str
    quantity_available: int
    reorder_point: int
    recommended_quantity: int
    estimated_cost: Decimal
    supplier_hint: str
    urgency: str
    rationale: str


class SupplierScoreRead(BaseModel):
    supplier_name: str
    work_orders: int
    completed_orders: int
    safety_orders: int
    estimated_cost: Decimal
    actual_cost: Decimal
    score: int
    recommendation: str


class SupplierOrderCreate(BaseModel):
    organization_id: UUID
    equipment_item_id: UUID | None = None
    supplier_name: str = Field(min_length=2, max_length=180)
    item_name: str = Field(min_length=2, max_length=180)
    quantity: int = Field(ge=1)
    unit_cost: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    external_reference: str | None = Field(default=None, max_length=240)
    expected_delivery_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)
    submit: bool = True


class SupplierOrderReceive(BaseModel):
    quantity_received: int | None = Field(default=None, ge=1)
    received_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)


class SupplierOrderRead(BaseModel):
    id: UUID
    organization_id: UUID
    equipment_item_id: UUID | None
    supplier_name: str
    item_name: str
    quantity: int
    unit_cost: Decimal
    total_cost: Decimal
    currency: str
    status: str
    external_reference: str | None
    ordered_at: datetime | None
    expected_delivery_at: datetime | None
    received_at: datetime | None
    notes: str | None


class SupplierOrderSubmissionRead(BaseModel):
    order: SupplierOrderRead
    submission_mode: str
    adapter_profile: str
    delivery_attempted: bool
    delivered: bool
    destination: str | None
    provider_status_code: int | None
    submitted_at: datetime
    failure_reason: str | None


class SupplierInvoiceSyncRead(BaseModel):
    order: SupplierOrderRead
    sync_mode: str
    adapter_profile: str
    sync_attempted: bool
    synced: bool
    destination: str | None
    provider_status_code: int | None
    synced_at: datetime
    failure_reason: str | None


class EquipmentLeaseQuoteRead(BaseModel):
    equipment_item_id: UUID
    item_name: str
    quantity: int
    term_months: int
    monthly_amount: Decimal
    total_amount: Decimal
    residual_value: Decimal
    rationale: str


class EquipmentLeaseInvoiceCreate(BaseModel):
    organization_id: UUID
    quantity: int = Field(default=1, ge=1)
    term_months: int = Field(default=12, ge=1, le=120)
    person_id: UUID | None = None
    team_id: UUID | None = None
    due_on: date | None = None
    memo: str | None = Field(default=None, max_length=4000)


class EquipmentLeaseInvoiceRead(BaseModel):
    lease_quote: EquipmentLeaseQuoteRead
    invoice: FinanceInvoiceRead


class EquipmentLeaseScheduleCreate(BaseModel):
    organization_id: UUID
    quantity: int = Field(default=1, ge=1)
    term_months: int = Field(default=12, ge=1, le=120)
    person_id: UUID | None = None
    team_id: UUID | None = None
    starts_on: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class EquipmentLeaseInstallmentRead(BaseModel):
    id: UUID
    organization_id: UUID
    lease_schedule_id: UUID
    sequence_number: int
    due_on: date
    amount: Decimal
    amount_paid: Decimal
    currency: str
    status: str
    paid_at: datetime | None


class EquipmentLeaseScheduleRead(BaseModel):
    id: UUID
    organization_id: UUID
    equipment_item_id: UUID
    finance_invoice_id: UUID
    person_id: UUID | None
    team_id: UUID | None
    quantity: int
    term_months: int
    monthly_amount: Decimal
    total_amount: Decimal
    currency: str
    starts_on: date
    status: str
    notes: str | None
    invoice: FinanceInvoiceRead
    installments: list[EquipmentLeaseInstallmentRead]


class EquipmentLeasePaymentCreate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    method: str = Field(default="bank_transfer", min_length=2, max_length=80)
    external_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)


class EquipmentLeasePaymentRead(BaseModel):
    schedule: EquipmentLeaseScheduleRead
    payment: FinancePaymentRead
    installments_paid: int
    installments_partially_paid: int
    amount_applied: Decimal
    remaining_balance: Decimal


class AssetAccountingExportRow(BaseModel):
    row_type: str
    source_id: UUID
    source_label: str
    account_code: str
    memo: str
    debit: Decimal
    credit: Decimal
    currency: str
    external_reference: str | None = None


class AssetAccountingExportRead(BaseModel):
    organization_id: UUID
    basis: str
    system: str
    rows: list[AssetAccountingExportRow]
    debit_total: Decimal
    credit_total: Decimal
    supplier_order_count: int
    lease_schedule_count: int
    payment_count: int


class AssetAccountingSyncRead(BaseModel):
    organization_id: UUID
    basis: str
    system: str
    mode: str
    delivered: bool
    row_count: int
    debit_total: Decimal
    credit_total: Decimal
    sync_reference: str
    provider_status_code: int | None = None
    failure_reason: str | None = None
    webhook_configured: bool
    synced_at: datetime


class AssetUtilizationRecommendationRead(BaseModel):
    target_type: str
    target_id: UUID
    title: str
    severity: str
    recommendation: str
    expected_impact: str


class EquipmentCheckoutCreate(BaseModel):
    organization_id: UUID
    equipment_item_id: UUID
    team_id: UUID | None = None
    event_id: UUID | None = None
    borrower_person_id: UUID | None = None
    quantity: int = Field(ge=1)
    purpose: str = Field(min_length=2, max_length=240)
    due_at: datetime
    condition_out: AssetCondition = AssetCondition.GOOD
    condition_notes: str | None = Field(default=None, max_length=4000)


class EquipmentCheckoutReturn(BaseModel):
    returned_at: datetime | None = None
    condition_in: AssetCondition = AssetCondition.GOOD
    damage_report: str | None = Field(default=None, max_length=4000)
    late_fee: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class EquipmentCheckoutRead(BaseModel):
    id: UUID
    organization_id: UUID
    equipment_item_id: UUID
    team_id: UUID | None
    event_id: UUID | None
    borrower_person_id: UUID | None
    checked_out_by_person_id: UUID | None
    returned_by_person_id: UUID | None
    quantity: int
    purpose: str
    checked_out_at: datetime
    due_at: datetime
    returned_at: datetime | None
    status: CheckoutStatus
    condition_out: AssetCondition
    condition_in: AssetCondition | None
    condition_notes: str | None
    damage_report: str | None
    late_fee: Decimal | None


class MaintenanceWorkOrderCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID | None = None
    equipment_item_id: UUID | None = None
    assigned_to_person_id: UUID | None = None
    title: str = Field(min_length=2, max_length=220)
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM
    due_at: datetime | None = None
    vendor: str | None = Field(default=None, max_length=180)
    estimated_cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    safety_related: bool = False
    compliance_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)


class MaintenanceWorkOrderUpdate(BaseModel):
    status: WorkOrderStatus
    actual_cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    notes: str | None = Field(default=None, max_length=4000)


class MaintenanceWorkOrderRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_maintenance_schedule_id: UUID | None
    facility_id: UUID | None
    equipment_item_id: UUID | None
    assigned_to_person_id: UUID | None
    title: str
    priority: WorkOrderPriority
    status: WorkOrderStatus
    due_at: datetime | None
    completed_at: datetime | None
    vendor: str | None
    estimated_cost: Decimal | None
    actual_cost: Decimal | None
    safety_related: bool
    compliance_reference: str | None
    notes: str | None


class FacilityMaintenanceScheduleCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    equipment_item_id: UUID | None = None
    assigned_to_person_id: UUID | None = None
    title: str = Field(min_length=2, max_length=220)
    category: str = Field(default="preventive", min_length=2, max_length=120)
    frequency: str = Field(default="weekly", pattern="^(daily|weekly|monthly|quarterly|annual|custom)$")
    interval_days: int = Field(default=7, ge=1, le=730)
    next_due_at: datetime
    vendor: str | None = Field(default=None, max_length=180)
    estimated_cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    safety_related: bool = False
    compliance_reference: str | None = Field(default=None, max_length=240)
    condition_metric: str | None = Field(default=None, max_length=120)
    condition_threshold: str | None = Field(default=None, max_length=120)
    warranty_expires_on: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class FacilityMaintenanceScheduleUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(active|paused|retired)$")
    next_due_at: datetime | None = None
    interval_days: int | None = Field(default=None, ge=1, le=730)
    estimated_cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    notes: str | None = Field(default=None, max_length=4000)


class FacilityMaintenanceScheduleRead(FacilityMaintenanceScheduleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    last_generated_at: datetime | None
    last_completed_at: datetime | None


class FacilityMaintenanceScheduleRunRead(BaseModel):
    schedule: FacilityMaintenanceScheduleRead
    work_order: MaintenanceWorkOrderRead
    next_due_at: datetime


class FacilityMaintenanceCostRead(BaseModel):
    facility_id: UUID
    facility_name: str
    maintenance_budget: Decimal | None
    actual_cost: Decimal
    estimated_open_cost: Decimal
    net_budget_remaining: Decimal | None


class FacilityMaintenanceDashboardRead(BaseModel):
    organization_id: UUID
    due_count: int
    overdue_count: int
    safety_due_count: int
    maintenance_cost_ytd: Decimal
    estimated_open_cost: Decimal
    budget_remaining: Decimal | None
    upcoming_schedules: list[FacilityMaintenanceScheduleRead]
    recent_work_orders: list[MaintenanceWorkOrderRead]
    cost_by_facility: list[FacilityMaintenanceCostRead]
    recommendation: str


class FacilityLeaseAgreementCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    lessor_name: str = Field(min_length=2, max_length=180)
    lessee_name: str = Field(min_length=2, max_length=180)
    lessee_contact_name: str | None = Field(default=None, max_length=180)
    lessee_contact_email: str | None = Field(default=None, max_length=255)
    usage_terms: str = Field(min_length=2, max_length=8000)
    included_services: str | None = Field(default=None, max_length=4000)
    extra_charges: str | None = Field(default=None, max_length=4000)
    starts_on: date
    ends_on: date
    monthly_rent: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    security_deposit: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    deposit_status: str = Field(default="held", pattern="^(not_required|due|held|returned|forfeited)$")
    next_invoice_on: date | None = None
    auto_renew: bool = False
    renewal_notice_on: date | None = None
    compliance_status: str = Field(default="pending", pattern="^(pending|compliant|review_required|breach|waived)$")
    compliance_notes: str | None = Field(default=None, max_length=4000)
    document_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def valid_term(self) -> "FacilityLeaseAgreementCreate":
        if self.ends_on <= self.starts_on:
            raise ValueError("ends_on must be after starts_on")
        return self


class FacilityLeaseAgreementUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(draft|active|invoicing|completed|terminated|disputed)$")
    deposit_status: str | None = Field(default=None, pattern="^(not_required|due|held|returned|forfeited)$")
    compliance_status: str | None = Field(default=None, pattern="^(pending|compliant|review_required|breach|waived)$")
    next_invoice_on: date | None = None
    renewal_notice_on: date | None = None
    signed_at: datetime | None = None
    terminated_at: datetime | None = None
    document_url: str | None = Field(default=None, max_length=500)
    compliance_notes: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)


class FacilityLeaseInvoiceCreate(BaseModel):
    period_start: date
    period_end: date
    extra_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    late_fee: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    due_on: date | None = None
    memo: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def valid_period(self) -> "FacilityLeaseInvoiceCreate":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class FacilityLeaseAgreementRead(FacilityLeaseAgreementCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    finance_invoice_id: UUID | None
    status: str
    signed_at: datetime | None
    terminated_at: datetime | None
    version: int


class FacilityLeaseInvoiceRead(BaseModel):
    lease: FacilityLeaseAgreementRead
    invoice: FinanceInvoiceRead
    period_label: str


class FacilityAccessCredentialCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    booking_id: UUID | None = None
    lease_agreement_id: UUID | None = None
    person_id: UUID | None = None
    guest_name: str | None = Field(default=None, max_length=180)
    guest_email: str | None = Field(default=None, max_length=255)
    credential_type: str = Field(default="qr_code", pattern="^(qr_code|mobile_key|rfid|pin|biometric)$")
    access_code: str | None = Field(default=None, min_length=4, max_length=120)
    access_level: str = Field(default="standard", min_length=2, max_length=80)
    zones: str | None = Field(default=None, max_length=2000)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    max_uses: int | None = Field(default=None, ge=1, le=10000)
    notes: str | None = Field(default=None, max_length=4000)


class FacilityAccessCredentialUpdate(BaseModel):
    status: str = Field(pattern="^(active|paused|revoked|expired)$")
    valid_until: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)


class FacilityAccessCredentialRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_id: UUID
    booking_id: UUID | None
    lease_agreement_id: UUID | None
    person_id: UUID | None
    guest_name: str | None
    guest_email: str | None
    credential_type: str
    access_code: str
    access_level: str
    zones: str | None
    valid_from: datetime
    valid_until: datetime
    status: str
    max_uses: int | None
    uses_count: int
    last_used_at: datetime | None
    issued_by_person_id: UUID | None
    notes: str | None


class FacilityAccessScanCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    access_code: str = Field(min_length=1, max_length=120)
    reader_id: str = Field(min_length=1, max_length=160)
    reader_location: str | None = Field(default=None, max_length=240)
    occurred_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)


class FacilityAccessEventRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_id: UUID
    credential_id: UUID | None
    booking_id: UUID | None
    lease_agreement_id: UUID | None
    access_code: str | None
    reader_id: str
    reader_location: str | None
    subject_summary: str | None
    decision: str
    reason: str
    occurred_at: datetime
    notes: str | None


class FacilityAccessDashboardRead(BaseModel):
    organization_id: UUID
    facility_id: UUID | None
    active_credentials: int
    guest_credentials: int
    grants_last_24h: int
    denials_last_24h: int
    recent_events: list[FacilityAccessEventRead]
    expiring_credentials: list[FacilityAccessCredentialRead]
    recommendation: str


class FacilityAccessDeviceCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    device_id: str = Field(min_length=2, max_length=160)
    name: str = Field(min_length=2, max_length=180)
    location: str | None = Field(default=None, max_length=240)
    device_type: str = Field(default="door_controller", min_length=2, max_length=80)
    unlock_method: str = Field(default="relay", min_length=2, max_length=80)
    status: str = Field(default="active", pattern="^(active|paused|maintenance|retired)$")
    api_key: str | None = Field(default=None, min_length=16, max_length=200)
    notes: str | None = Field(default=None, max_length=4000)


class FacilityAccessDeviceRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_id: UUID
    device_id: str
    name: str
    location: str | None
    device_type: str
    unlock_method: str
    status: str
    last_seen_at: datetime | None
    last_scan_at: datetime | None
    last_health_at: datetime | None
    battery_percent: int | None
    firmware_version: str | None
    network_status: str | None
    notes: str | None


class FacilityAccessDeviceProvisionRead(BaseModel):
    device: FacilityAccessDeviceRead
    api_key: str


class FacilityAccessCommandRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_id: UUID
    access_device_id: UUID
    access_event_id: UUID | None
    credential_id: UUID | None
    command_type: str
    command_payload: str
    command_signature: str
    status: str
    issued_at: datetime
    valid_until: datetime
    acknowledged_at: datetime | None
    requested_by_person_id: UUID | None
    notes: str | None


class FacilityAccessGatewayScanCreate(BaseModel):
    access_code: str = Field(min_length=1, max_length=120)
    occurred_at: datetime | None = None
    external_reference: str | None = Field(default=None, max_length=240)
    battery_percent: int | None = Field(default=None, ge=0, le=100)
    firmware_version: str | None = Field(default=None, max_length=120)
    network_status: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=4000)


class FacilityAccessGatewayScanRead(BaseModel):
    device: FacilityAccessDeviceRead
    event: FacilityAccessEventRead
    command: FacilityAccessCommandRead | None
    signature_validated: bool


class FacilityAccessDeviceHealthCreate(BaseModel):
    checked_at: datetime | None = None
    battery_percent: int | None = Field(default=None, ge=0, le=100)
    firmware_version: str | None = Field(default=None, max_length=120)
    network_status: str | None = Field(default=None, max_length=80)
    status: str | None = Field(default=None, pattern="^(active|paused|maintenance|retired)$")
    notes: str | None = Field(default=None, max_length=4000)


class FacilityAccessDeviceHealthRead(BaseModel):
    device: FacilityAccessDeviceRead
    signature_validated: bool
    recommendation: str


class FacilityAccessLockdownCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    mode: str = Field(default="lockdown", pattern="^(lockdown|unlock_all)$")
    reason: str = Field(min_length=2, max_length=500)
    command_valid_seconds: int = Field(default=300, ge=10, le=3600)
    notes: str | None = Field(default=None, max_length=4000)


class FacilityAccessLockdownUpdate(BaseModel):
    status: str = Field(pattern="^(active|resolved|cancelled)$")
    notes: str | None = Field(default=None, max_length=4000)


class FacilityAccessLockdownRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_id: UUID
    mode: str
    status: str
    reason: str
    command_count: int
    activated_at: datetime
    resolved_at: datetime | None
    issued_by_person_id: UUID | None
    notes: str | None


class FacilityAccessLockdownResultRead(BaseModel):
    lockdown: FacilityAccessLockdownRead
    commands: list[FacilityAccessCommandRead]
    devices_targeted: int
    recommendation: str


class FacilityAccessLockdownDashboardRead(BaseModel):
    organization_id: UUID
    facility_id: UUID | None
    active_lockdown_count: int
    active_device_count: int
    command_count_last_24h: int
    recent_lockdowns: list[FacilityAccessLockdownRead]
    recent_commands: list[FacilityAccessCommandRead]
    recommendation: str


class FacilityUtilityMeterCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    meter_id: str = Field(min_length=2, max_length=160)
    name: str = Field(min_length=2, max_length=180)
    utility_type: str = Field(default="electricity", pattern="^(electricity|water|gas|solar|waste|other)$")
    unit: str = Field(default="kWh", min_length=1, max_length=40)
    location: str | None = Field(default=None, max_length=240)
    provider: str | None = Field(default=None, max_length=120)
    account_reference: str | None = Field(default=None, max_length=180)
    status: str = Field(default="active", pattern="^(active|paused|maintenance|retired)$")
    api_key: str | None = Field(default=None, min_length=16, max_length=200)
    cost_per_unit: Decimal | None = Field(default=None, ge=0)
    target_daily_usage: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=4000)


class FacilityUtilityMeterRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_id: UUID
    meter_id: str
    name: str
    utility_type: str
    unit: str
    location: str | None
    provider: str | None
    account_reference: str | None
    status: str
    cost_per_unit: Decimal | None
    target_daily_usage: Decimal | None
    last_reading_at: datetime | None
    last_value: Decimal | None
    last_cost_estimate: Decimal | None
    notes: str | None


class FacilityUtilityMeterProvisionRead(BaseModel):
    meter: FacilityUtilityMeterRead
    api_key: str


class FacilityUtilityReadingCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    utility_meter_id: UUID
    reading_value: Decimal = Field(ge=0)
    usage_delta: Decimal | None = Field(default=None)
    cost_estimate: Decimal | None = Field(default=None, ge=0)
    reading_at: datetime | None = None
    source: str = Field(default="manual", min_length=2, max_length=80)
    external_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)


class FacilityUtilityGatewayReadingCreate(BaseModel):
    reading_value: Decimal = Field(ge=0)
    usage_delta: Decimal | None = Field(default=None)
    cost_estimate: Decimal | None = Field(default=None, ge=0)
    reading_at: datetime | None = None
    external_reference: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)


class FacilityUtilityReadingRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_id: UUID
    utility_meter_id: UUID
    meter_id: str
    reading_value: Decimal
    usage_delta: Decimal | None
    unit: str
    cost_estimate: Decimal | None
    reading_at: datetime
    source: str
    anomaly_level: str
    external_reference: str | None
    notes: str | None


class FacilityUtilityAlertUpdate(BaseModel):
    status: str = Field(pattern="^(open|acknowledged|resolved|dismissed)$")
    notes: str | None = Field(default=None, max_length=4000)


class FacilityUtilityAlertRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_id: UUID
    utility_meter_id: UUID
    utility_reading_id: UUID | None
    alert_type: str
    severity: str
    status: str
    message: str
    recommended_action: str | None
    triggered_at: datetime
    resolved_at: datetime | None
    notes: str | None


class FacilityUtilityReadingResultRead(BaseModel):
    meter: FacilityUtilityMeterRead
    reading: FacilityUtilityReadingRead
    alert: FacilityUtilityAlertRead | None
    signature_validated: bool


class FacilityUtilityDashboardRead(BaseModel):
    organization_id: UUID
    facility_id: UUID | None
    meter_count: int
    open_alert_count: int
    total_usage_last_30d: Decimal
    total_cost_last_30d: Decimal
    usage_by_type: dict[str, Decimal]
    recent_readings: list[FacilityUtilityReadingRead]
    open_alerts: list[FacilityUtilityAlertRead]
    recommendation: str


class ClubhouseAmenityCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    name: str = Field(min_length=2, max_length=180)
    amenity_type: str = Field(default="lounge", min_length=2, max_length=80)
    location: str | None = Field(default=None, max_length=240)
    capacity: int | None = Field(default=None, ge=1, le=10000)
    reservation_required: bool = False
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    status: str = Field(default="active", pattern="^(active|maintenance|closed|retired)$")
    notes: str | None = Field(default=None, max_length=4000)


class ClubhouseAmenityRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_id: UUID
    name: str
    amenity_type: str
    location: str | None
    capacity: int | None
    reservation_required: bool
    hourly_rate: Decimal | None
    status: str
    notes: str | None


class ClubhouseVisitCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    person_id: UUID | None = None
    access_event_id: UUID | None = None
    guest_name: str | None = Field(default=None, max_length=180)
    guest_email: str | None = Field(default=None, max_length=255)
    check_in_at: datetime | None = None
    party_size: int = Field(default=1, ge=1, le=500)
    purpose: str | None = Field(default=None, max_length=180)
    notes: str | None = Field(default=None, max_length=4000)


class ClubhouseVisitUpdate(BaseModel):
    status: str = Field(pattern="^(checked_in|checked_out|cancelled)$")
    check_out_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)


class ClubhouseVisitRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_id: UUID
    person_id: UUID | None
    access_event_id: UUID | None
    guest_name: str | None
    guest_email: str | None
    check_in_at: datetime
    check_out_at: datetime | None
    status: str
    party_size: int
    purpose: str | None
    notes: str | None


class ClubhouseAmenityReservationCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    amenity_id: UUID
    person_id: UUID | None = None
    guest_name: str | None = Field(default=None, max_length=180)
    starts_at: datetime
    ends_at: datetime
    party_size: int = Field(default=1, ge=1, le=500)
    expected_fee: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=4000)


class ClubhouseAmenityReservationUpdate(BaseModel):
    status: str = Field(pattern="^(reserved|checked_in|completed|cancelled|no_show)$")
    notes: str | None = Field(default=None, max_length=4000)


class ClubhouseAmenityReservationRead(BaseModel):
    id: UUID
    organization_id: UUID
    facility_id: UUID
    amenity_id: UUID
    person_id: UUID | None
    guest_name: str | None
    starts_at: datetime
    ends_at: datetime
    status: str
    party_size: int
    expected_fee: Decimal | None
    notes: str | None


class ClubhouseDashboardRead(BaseModel):
    organization_id: UUID
    facility_id: UUID | None
    current_occupancy: int
    capacity: int | None
    capacity_remaining: int | None
    active_member_visits: int
    active_guest_visits: int
    amenity_count: int
    reservations_today: int
    expected_revenue_today: Decimal
    active_visits: list[ClubhouseVisitRead]
    upcoming_reservations: list[ClubhouseAmenityReservationRead]
    popular_amenities: list[str]
    recommendation: str


class FacilityBookingCreate(BaseModel):
    organization_id: UUID
    facility_id: UUID
    team_id: UUID | None = None
    event_id: UUID | None = None
    title: str = Field(min_length=2, max_length=220)
    starts_at: datetime
    ends_at: datetime
    requester_name: str | None = Field(default=None, max_length=180)
    requester_email: str | None = Field(default=None, max_length=255)
    expected_attendees: int | None = Field(default=None, ge=0)
    rate: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    deposit_required: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    insurance_certificate_ref: str | None = Field(default=None, max_length=240)
    special_requirements: str | None = Field(default=None, max_length=4000)
    access_code: str | None = Field(default=None, max_length=80)
    public_visible: bool = False

    @model_validator(mode="after")
    def valid_period(self) -> "FacilityBookingCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class FacilityBookingRead(FacilityBookingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: FacilityBookingStatus
    requested_by_person_id: UUID | None
    finance_invoice_id: UUID | None
    recurrence_group_id: str | None
    occurrence_index: int | None
    booking_source: str
    public_booking_reference: str | None
    payment_status: str
    payment_checkout_url: str | None
    access_starts_at: datetime | None
    access_ends_at: datetime | None
    conflict_note: str | None


class FacilityRecurringBookingCreate(FacilityBookingCreate):
    recurrence_frequency: str = Field(default="weekly", pattern="^(daily|weekly)$")
    occurrence_count: int = Field(default=4, ge=1, le=52)


class FacilityPublicBookingCreate(BaseModel):
    facility_id: UUID
    activity_type: str = Field(default="training", min_length=2, max_length=120)
    title: str = Field(min_length=2, max_length=220)
    starts_at: datetime
    ends_at: datetime
    requester_name: str = Field(min_length=2, max_length=180)
    requester_email: str = Field(min_length=5, max_length=255)
    requester_phone: str | None = Field(default=None, max_length=80)
    expected_attendees: int | None = Field(default=None, ge=0)
    insurance_certificate_ref: str | None = Field(default=None, max_length=240)
    special_requirements: str | None = Field(default=None, max_length=4000)
    add_ons: str | None = Field(default=None, max_length=1000)
    provider: str = Field(default="manual_gateway", min_length=2, max_length=80)
    checkout_base_url: str = Field(default="/pay/sessions", min_length=1, max_length=800)

    @model_validator(mode="after")
    def valid_period(self) -> "FacilityPublicBookingCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class FacilityAvailabilitySlotRead(BaseModel):
    starts_at: datetime
    ends_at: datetime
    status: str
    booking_id: UUID | None = None
    title: str | None = None
    conflict_note: str | None = None


class FacilityAvailabilityRead(BaseModel):
    organization_id: UUID
    facility_id: UUID
    starts_at: datetime
    ends_at: datetime
    rule: FacilityBookingRuleRead | None
    slots: list[FacilityAvailabilitySlotRead]
    conflict_count: int


class FacilityUtilizationRead(BaseModel):
    organization_id: UUID
    facility_id: UUID
    starts_at: datetime
    ends_at: datetime
    available_hours: float
    booked_hours: float
    utilization_percent: int
    booking_count: int
    projected_revenue: Decimal
    average_attendance: float | None
    recommendation: str


class FacilityBookingCheckoutRead(BaseModel):
    booking: FacilityBookingRead
    invoice: FinanceInvoiceRead
    checkout_url: str
    session_id: str
    access_window_summary: str


class FacilityBookingStatusUpdate(BaseModel):
    status: FacilityBookingStatus
    notes: str | None = Field(default=None, max_length=2000)


class FacilityBookingWaitlistCreate(BaseModel):
    facility_id: UUID
    activity_type: str = Field(default="training", min_length=2, max_length=120)
    title: str = Field(min_length=2, max_length=220)
    desired_starts_at: datetime
    desired_ends_at: datetime
    requester_name: str = Field(min_length=2, max_length=180)
    requester_email: str = Field(min_length=5, max_length=255)
    requester_phone: str | None = Field(default=None, max_length=80)
    expected_attendees: int | None = Field(default=None, ge=0)
    insurance_certificate_ref: str | None = Field(default=None, max_length=240)
    special_requirements: str | None = Field(default=None, max_length=4000)
    add_ons: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def valid_period(self) -> "FacilityBookingWaitlistCreate":
        if self.desired_ends_at <= self.desired_starts_at:
            raise ValueError("desired_ends_at must be after desired_starts_at")
        return self


class FacilityBookingWaitlistUpdate(BaseModel):
    status: str = Field(default="offered", pattern="^(pending|offered|converted|declined|cancelled)$")
    priority_score: int | None = Field(default=None, ge=0, le=1000)
    expires_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)


class FacilityBookingWaitlistConversionCreate(BaseModel):
    provider: str = Field(default="manual_gateway", min_length=2, max_length=80)
    checkout_base_url: str = Field(default="/pay/sessions", min_length=1, max_length=800)


class FacilityBookingWaitlistRead(FacilityBookingWaitlistCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    offered_booking_id: UUID | None
    status: str
    priority_score: int
    notified_at: datetime | None
    expires_at: datetime | None


class FacilityHireHostedCheckoutRead(BaseModel):
    invoice_id: UUID
    booking_id: UUID
    invoice_number: str
    organization_id: UUID
    facility_id: UUID
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


class FacilityHireCheckoutSettlementCreate(BaseModel):
    invoice_id: UUID
    booking_id: UUID
    provider: str = Field(default="manual_gateway", min_length=2, max_length=80)
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    method: str = Field(default="card", min_length=2, max_length=80)
    status: str = Field(default="succeeded", min_length=2, max_length=40)
    external_payment_id: str | None = Field(default=None, max_length=240)
    raw_reference: str | None = Field(default=None, max_length=2000)


class FacilityHireCheckoutSettlementRead(BaseModel):
    booking_id: UUID
    invoice_id: UUID
    payment_id: UUID | None
    provider: str
    amount_paid: Decimal
    open_amount: Decimal
    currency: str
    invoice_status: str
    booking_status: FacilityBookingStatus
    payment_status: str
    session_status: str
    access_code: str | None
    access_starts_at: datetime | None
    access_ends_at: datetime | None


class AssetSummaryRead(BaseModel):
    organization_id: UUID
    facilities: int
    equipment_items: int
    stock_alerts: int
    open_checkouts: int
    overdue_checkouts: int
    open_work_orders: int
    safety_work_orders: int
    upcoming_bookings: int
    booked_hours: float
    projected_booking_revenue: Decimal
