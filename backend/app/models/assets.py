from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
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


class Facility(IdMixin, TimestampMixin, Base):
    __tablename__ = "facilities"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    facility_type: Mapped[FacilityType] = mapped_column(
        enum_type(FacilityType), nullable=False, index=True
    )
    status: Mapped[FacilityStatus] = mapped_column(
        enum_type(FacilityStatus),
        default=FacilityStatus.AVAILABLE,
        nullable=False,
        index=True,
    )
    sport: Mapped[str | None] = mapped_column(String(80), index=True)
    surface: Mapped[str | None] = mapped_column(String(120))
    capacity: Mapped[int | None] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(String(240))
    dimensions: Mapped[str | None] = mapped_column(String(120))
    amenities: Mapped[str | None] = mapped_column(Text)
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    maintenance_budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    condition: Mapped[AssetCondition] = mapped_column(
        enum_type(AssetCondition),
        default=AssetCondition.GOOD,
        nullable=False,
        index=True,
    )
    insurance_policy_ref: Mapped[str | None] = mapped_column(String(180))
    last_inspection_on: Mapped[date | None] = mapped_column(index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class EquipmentItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "equipment_items"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    facility_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("facilities.id"), index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100))
    brand: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    tag_code: Mapped[str | None] = mapped_column(String(120), index=True)
    serial_number: Mapped[str | None] = mapped_column(String(160), index=True)
    quantity_total: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    quantity_available: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    condition: Mapped[AssetCondition] = mapped_column(
        enum_type(AssetCondition),
        default=AssetCondition.GOOD,
        nullable=False,
        index=True,
    )
    status: Mapped[EquipmentStatus] = mapped_column(
        enum_type(EquipmentStatus),
        default=EquipmentStatus.AVAILABLE,
        nullable=False,
        index=True,
    )
    storage_location: Mapped[str | None] = mapped_column(String(240))
    min_stock_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    depreciation_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    warranty_expires_on: Mapped[date | None] = mapped_column(index=True)
    last_audit_on: Mapped[date | None] = mapped_column(index=True)
    photo_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)


class EquipmentFile(IdMixin, TimestampMixin, Base):
    __tablename__ = "equipment_files"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    equipment_item_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("equipment_items.id"), index=True
    )
    uploaded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    filename: Mapped[str] = mapped_column(String(240), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_url: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(700), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class EquipmentScanEvent(IdMixin, TimestampMixin, Base):
    __tablename__ = "equipment_scan_events"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    equipment_item_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("equipment_items.id"), index=True
    )
    scanned_code: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    match_type: Mapped[str | None] = mapped_column(String(40), index=True)
    item_name: Mapped[str | None] = mapped_column(String(180))
    reader_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    reader_location: Mapped[str | None] = mapped_column(String(240), index=True)
    source: Mapped[str] = mapped_column(String(40), default="rfid_reader", nullable=False, index=True)
    movement: Mapped[str] = mapped_column(String(40), default="audit", nullable=False, index=True)
    matched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    external_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class EquipmentReader(IdMixin, TimestampMixin, Base):
    __tablename__ = "equipment_readers"
    __table_args__ = (UniqueConstraint("organization_id", "reader_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    reader_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(240), index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    api_key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_scan_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class EquipmentCheckout(IdMixin, TimestampMixin, Base):
    __tablename__ = "equipment_checkouts"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    equipment_item_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("equipment_items.id"), index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    borrower_person_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("persons.id"), index=True
    )
    checked_out_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    returned_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[str] = mapped_column(String(240), nullable=False)
    checked_out_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[CheckoutStatus] = mapped_column(
        enum_type(CheckoutStatus),
        default=CheckoutStatus.CHECKED_OUT,
        nullable=False,
        index=True,
    )
    condition_out: Mapped[AssetCondition] = mapped_column(
        String(40),
        default=AssetCondition.GOOD,
        nullable=False,
    )
    condition_in: Mapped[AssetCondition | None] = mapped_column(String(40))
    condition_notes: Mapped[str | None] = mapped_column(Text)
    damage_report: Mapped[str | None] = mapped_column(Text)
    late_fee: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))


class MaintenanceWorkOrder(IdMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_work_orders"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    facility_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("facilities.id"), index=True
    )
    equipment_item_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("equipment_items.id"), index=True
    )
    assigned_to_person_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("persons.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    priority: Mapped[WorkOrderPriority] = mapped_column(
        enum_type(WorkOrderPriority),
        default=WorkOrderPriority.MEDIUM,
        nullable=False,
        index=True,
    )
    status: Mapped[WorkOrderStatus] = mapped_column(
        enum_type(WorkOrderStatus),
        default=WorkOrderStatus.OPEN,
        nullable=False,
        index=True,
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    vendor: Mapped[str | None] = mapped_column(String(180))
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    actual_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    safety_related: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    compliance_reference: Mapped[str | None] = mapped_column(String(240))
    notes: Mapped[str | None] = mapped_column(Text)


class FacilityBooking(IdMixin, TimestampMixin, Base):
    __tablename__ = "facility_bookings"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    facility_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("facilities.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    requested_by_person_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("persons.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[FacilityBookingStatus] = mapped_column(
        enum_type(FacilityBookingStatus),
        default=FacilityBookingStatus.REQUESTED,
        nullable=False,
        index=True,
    )
    requester_name: Mapped[str | None] = mapped_column(String(180))
    requester_email: Mapped[str | None] = mapped_column(String(255))
    expected_attendees: Mapped[int | None] = mapped_column(Integer)
    rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    deposit_required: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    insurance_certificate_ref: Mapped[str | None] = mapped_column(String(240))
    special_requirements: Mapped[str | None] = mapped_column(Text)
    access_code: Mapped[str | None] = mapped_column(String(80))


class SupplierOrder(IdMixin, TimestampMixin, Base):
    __tablename__ = "supplier_orders"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    equipment_item_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("equipment_items.id"), index=True
    )
    supplier_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    external_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    ordered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    expected_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class EquipmentLeaseSchedule(IdMixin, TimestampMixin, Base):
    __tablename__ = "equipment_lease_schedules"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    equipment_item_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("equipment_items.id"), index=True
    )
    finance_invoice_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("finance_invoices.id"), index=True
    )
    person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    starts_on: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class EquipmentLeaseInstallment(IdMixin, TimestampMixin, Base):
    __tablename__ = "equipment_lease_installments"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    lease_schedule_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("equipment_lease_schedules.id"), index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    due_on: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="scheduled", nullable=False, index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
