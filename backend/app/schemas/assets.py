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
