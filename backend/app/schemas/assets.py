from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    AssetCondition,
    CheckoutStatus,
    EquipmentStatus,
    FacilityBookingStatus,
    FacilityStatus,
    FacilityType,
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
    delivery_attempted: bool
    delivered: bool
    destination: str | None
    provider_status_code: int | None
    submitted_at: datetime
    failure_reason: str | None


class SupplierInvoiceSyncRead(BaseModel):
    order: SupplierOrderRead
    sync_mode: str
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
    amount_applied: Decimal
    remaining_balance: Decimal


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

    @model_validator(mode="after")
    def valid_period(self) -> "FacilityBookingCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class FacilityBookingRead(FacilityBookingCreate):
    id: UUID
    status: FacilityBookingStatus
    requested_by_person_id: UUID | None


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
