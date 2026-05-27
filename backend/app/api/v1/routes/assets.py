from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.assets import (
    AssetSummaryRead,
    EquipmentCheckoutCreate,
    EquipmentCheckoutRead,
    EquipmentCheckoutReturn,
    EquipmentItemCreate,
    EquipmentItemRead,
    FacilityBookingCreate,
    FacilityBookingRead,
    FacilityCreate,
    FacilityRead,
    MaintenanceWorkOrderCreate,
    MaintenanceWorkOrderRead,
    MaintenanceWorkOrderUpdate,
)
from app.services.assets import (
    asset_summary,
    checkout_equipment,
    create_equipment_item,
    create_facility,
    create_facility_booking,
    create_work_order,
    list_checkouts,
    list_equipment_items,
    list_facilities,
    list_facility_bookings,
    list_work_orders,
    return_equipment,
    update_work_order,
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
        insurance_certificate_ref=booking.insurance_certificate_ref,
        special_requirements=booking.special_requirements,
        access_code=booking.access_code,
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


@router.post("/bookings", response_model=FacilityBookingRead, status_code=status.HTTP_201_CREATED)
async def create_facility_booking_route(
    payload: FacilityBookingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FacilityBookingRead:
    return to_booking_read(await create_facility_booking(db, identity, payload, authz))


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


@router.get("/summary", response_model=AssetSummaryRead)
async def asset_summary_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> AssetSummaryRead:
    return await asset_summary(db, organization_id)
