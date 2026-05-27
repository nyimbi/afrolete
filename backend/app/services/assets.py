from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assets import (
    EquipmentCheckout,
    EquipmentItem,
    Facility,
    FacilityBooking,
    MaintenanceWorkOrder,
    SupplierOrder,
)
from app.models.enums import (
    AssetCondition,
    CheckoutStatus,
    EquipmentStatus,
    FacilityBookingStatus,
    MemberSubjectType,
    WorkOrderStatus,
)
from app.models.event import Event
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.team import Team
from app.schemas.assets import (
    AssetSummaryRead,
    EquipmentCheckoutCreate,
    EquipmentCheckoutReturn,
    EquipmentLeaseQuoteRead,
    EquipmentPhotoUpdate,
    EquipmentScanRead,
    EquipmentItemCreate,
    FacilityBookingCreate,
    FacilityCreate,
    MaintenanceWorkOrderCreate,
    MaintenanceWorkOrderUpdate,
    ProcurementRecommendationRead,
    SupplierOrderCreate,
    SupplierOrderReceive,
    SupplierScoreRead,
    AssetUtilizationRecommendationRead,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService


async def ensure_manage_assets(
    authz: AuthorizationService,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> None:
    allowed = await authz.check(
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
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def create_facility(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FacilityCreate,
    authz: AuthorizationService,
) -> Facility:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    facility = Facility(**payload.model_dump())
    db.add(facility)
    await db.commit()
    await db.refresh(facility)
    return facility


async def list_facilities(db: AsyncSession, organization_id: UUID) -> list[Facility]:
    return list(
        (
            await db.scalars(
                select(Facility)
                .where(Facility.organization_id == organization_id)
                .order_by(Facility.name)
            )
        ).all()
    )


async def create_equipment_item(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: EquipmentItemCreate,
    authz: AuthorizationService,
) -> EquipmentItem:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    if payload.facility_id is not None:
        await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)

    data = payload.model_dump()
    quantity_available = data.pop("quantity_available")
    item = EquipmentItem(
        quantity_available=quantity_available,
        status=equipment_status_for_quantity(quantity_available),
        **data,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def list_equipment_items(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
    team_id: UUID | None = None,
) -> list[EquipmentItem]:
    statement = select(EquipmentItem).where(EquipmentItem.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(EquipmentItem.facility_id == facility_id)
    if team_id is not None:
        statement = statement.where(EquipmentItem.team_id == team_id)
    return list((await db.scalars(statement.order_by(EquipmentItem.category, EquipmentItem.name))).all())


async def scan_equipment(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    scanned_code: str,
    authz: AuthorizationService,
) -> EquipmentScanRead:
    await ensure_manage_assets(authz, identity, organization_id)
    code = scanned_code.strip()
    item = await db.scalar(
        select(EquipmentItem)
        .where(EquipmentItem.organization_id == organization_id)
        .where((EquipmentItem.tag_code == code) | (EquipmentItem.serial_number == code))
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return EquipmentScanRead(
        scanned_code=code,
        match_type="tag_code" if item.tag_code == code else "serial_number",
        item=equipment_item_read(item),
    )


async def update_equipment_photo(
    db: AsyncSession,
    identity: CurrentIdentity,
    equipment_item_id: UUID,
    payload: EquipmentPhotoUpdate,
    authz: AuthorizationService,
) -> EquipmentItem:
    item = await get_equipment(db, equipment_item_id)
    await ensure_manage_assets(authz, identity, item.organization_id)
    item.photo_url = payload.photo_url
    if payload.notes is not None:
        item.notes = payload.notes
    await db.commit()
    await db.refresh(item)
    return item


async def checkout_equipment(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: EquipmentCheckoutCreate,
    authz: AuthorizationService,
) -> EquipmentCheckout:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    item = await get_equipment_for_organization(db, payload.equipment_item_id, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    if payload.event_id is not None:
        await get_event_for_organization(db, payload.event_id, payload.organization_id)
    if payload.borrower_person_id is not None:
        await get_person_member_for_organization(db, payload.borrower_person_id, payload.organization_id)
    if payload.quantity > item.quantity_available:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient equipment available")

    item.quantity_available -= payload.quantity
    item.status = equipment_status_for_quantity(item.quantity_available)
    checkout = EquipmentCheckout(
        checked_out_by_person_id=identity.person_id,
        checked_out_at=datetime.now(UTC),
        **payload.model_dump(),
    )
    db.add(checkout)
    await db.commit()
    await db.refresh(checkout)
    return checkout


async def return_equipment(
    db: AsyncSession,
    identity: CurrentIdentity,
    checkout_id: UUID,
    payload: EquipmentCheckoutReturn,
    authz: AuthorizationService,
) -> EquipmentCheckout:
    checkout = await get_checkout(db, checkout_id)
    await ensure_manage_assets(authz, identity, checkout.organization_id)
    item = await get_equipment_for_organization(
        db,
        checkout.equipment_item_id,
        checkout.organization_id,
    )
    if checkout.status != CheckoutStatus.CHECKED_OUT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Checkout is not open")

    returned_at = payload.returned_at or datetime.now(UTC)
    checkout.returned_at = returned_at
    checkout.returned_by_person_id = identity.person_id
    checkout.condition_in = payload.condition_in
    checkout.damage_report = payload.damage_report
    checkout.late_fee = payload.late_fee
    checkout.status = (
        CheckoutStatus.DAMAGED
        if payload.condition_in in {AssetCondition.POOR, AssetCondition.UNUSABLE}
        or bool(payload.damage_report)
        else CheckoutStatus.RETURNED
    )
    item.quantity_available = min(item.quantity_total, item.quantity_available + checkout.quantity)
    item.condition = payload.condition_in
    item.status = equipment_status_for_quantity(item.quantity_available)
    await db.commit()
    await db.refresh(checkout)
    return checkout


async def list_checkouts(
    db: AsyncSession,
    organization_id: UUID,
    open_only: bool = False,
) -> list[EquipmentCheckout]:
    statement = select(EquipmentCheckout).where(EquipmentCheckout.organization_id == organization_id)
    if open_only:
        statement = statement.where(EquipmentCheckout.status == CheckoutStatus.CHECKED_OUT)
    return list((await db.scalars(statement.order_by(EquipmentCheckout.due_at.desc()))).all())


async def create_work_order(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: MaintenanceWorkOrderCreate,
    authz: AuthorizationService,
) -> MaintenanceWorkOrder:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    if payload.facility_id is not None:
        await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    if payload.equipment_item_id is not None:
        await get_equipment_for_organization(db, payload.equipment_item_id, payload.organization_id)
    if payload.assigned_to_person_id is not None:
        await get_person_member_for_organization(db, payload.assigned_to_person_id, payload.organization_id)

    work_order = MaintenanceWorkOrder(**payload.model_dump())
    db.add(work_order)
    await db.commit()
    await db.refresh(work_order)
    return work_order


async def update_work_order(
    db: AsyncSession,
    identity: CurrentIdentity,
    work_order_id: UUID,
    payload: MaintenanceWorkOrderUpdate,
    authz: AuthorizationService,
) -> MaintenanceWorkOrder:
    work_order = await get_work_order(db, work_order_id)
    await ensure_manage_assets(authz, identity, work_order.organization_id)
    work_order.status = payload.status
    work_order.actual_cost = payload.actual_cost
    if payload.notes is not None:
        work_order.notes = payload.notes
    if payload.status == WorkOrderStatus.COMPLETED:
        work_order.completed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(work_order)
    return work_order


async def list_work_orders(
    db: AsyncSession,
    organization_id: UUID,
    open_only: bool = False,
) -> list[MaintenanceWorkOrder]:
    statement = select(MaintenanceWorkOrder).where(
        MaintenanceWorkOrder.organization_id == organization_id
    )
    if open_only:
        statement = statement.where(
            MaintenanceWorkOrder.status.in_(
                [WorkOrderStatus.OPEN, WorkOrderStatus.ASSIGNED, WorkOrderStatus.IN_PROGRESS]
            )
        )
    return list(
        (await db.scalars(statement.order_by(MaintenanceWorkOrder.due_at, MaintenanceWorkOrder.title))).all()
    )


async def create_facility_booking(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FacilityBookingCreate,
    authz: AuthorizationService,
) -> FacilityBooking:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    if payload.event_id is not None:
        await get_event_for_organization(db, payload.event_id, payload.organization_id)
    await ensure_facility_available(db, payload.facility_id, payload.starts_at, payload.ends_at)

    booking = FacilityBooking(
        requested_by_person_id=identity.person_id,
        status=FacilityBookingStatus.CONFIRMED,
        **payload.model_dump(),
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


async def list_facility_bookings(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
) -> list[FacilityBooking]:
    statement = select(FacilityBooking).where(FacilityBooking.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(FacilityBooking.facility_id == facility_id)
    return list((await db.scalars(statement.order_by(FacilityBooking.starts_at.desc()))).all())


async def asset_summary(db: AsyncSession, organization_id: UUID) -> AssetSummaryRead:
    now = datetime.now(UTC)
    facilities = await list_facilities(db, organization_id)
    equipment = await list_equipment_items(db, organization_id)
    checkouts = await list_checkouts(db, organization_id)
    work_orders = await list_work_orders(db, organization_id)
    bookings = await list_facility_bookings(db, organization_id)
    upcoming_bookings = [
        booking
        for booking in bookings
        if not is_before_now(booking.ends_at, now)
        and booking.status
        not in {FacilityBookingStatus.CANCELLED, FacilityBookingStatus.COMPLETED}
    ]
    booked_hours = sum(
        max((booking.ends_at - booking.starts_at).total_seconds() / 3600, 0)
        for booking in upcoming_bookings
    )
    projected_revenue = sum(
        Decimal(str(max((booking.ends_at - booking.starts_at).total_seconds() / 3600, 0)))
        * (booking.rate or Decimal("0"))
        for booking in upcoming_bookings
    )
    open_work_orders = [
        work_order
        for work_order in work_orders
        if work_order.status
        in {WorkOrderStatus.OPEN, WorkOrderStatus.ASSIGNED, WorkOrderStatus.IN_PROGRESS}
    ]

    return AssetSummaryRead(
        organization_id=organization_id,
        facilities=len(facilities),
        equipment_items=len(equipment),
        stock_alerts=sum(1 for item in equipment if item.quantity_available <= item.reorder_point),
        open_checkouts=sum(1 for checkout in checkouts if checkout.status == CheckoutStatus.CHECKED_OUT),
        overdue_checkouts=sum(
            1
            for checkout in checkouts
            if checkout.status == CheckoutStatus.CHECKED_OUT and is_before_now(checkout.due_at, now)
        ),
        open_work_orders=len(open_work_orders),
        safety_work_orders=sum(1 for work_order in open_work_orders if work_order.safety_related),
        upcoming_bookings=len(upcoming_bookings),
        booked_hours=round(booked_hours, 2),
        projected_booking_revenue=projected_revenue.quantize(Decimal("0.01")),
    )


async def procurement_recommendations(
    db: AsyncSession,
    organization_id: UUID,
) -> list[ProcurementRecommendationRead]:
    equipment = await list_equipment_items(db, organization_id)
    recommendations = []
    for item in equipment:
        if item.quantity_available > item.reorder_point:
            continue
        target_stock = max(item.min_stock_level, item.reorder_point * 2, item.quantity_total)
        recommended_quantity = max(target_stock - item.quantity_available, 1)
        unit_value = item.unit_value or Decimal("0")
        urgency = "critical" if item.quantity_available <= item.min_stock_level else "reorder"
        recommendations.append(
            ProcurementRecommendationRead(
                equipment_item_id=item.id,
                item_name=item.name,
                category=item.category,
                quantity_available=item.quantity_available,
                reorder_point=item.reorder_point,
                recommended_quantity=recommended_quantity,
                estimated_cost=(unit_value * recommended_quantity).quantize(Decimal("0.01")),
                supplier_hint=item.brand or item.category,
                urgency=urgency,
                rationale=(
                    f"{item.name} has {item.quantity_available} available against reorder point "
                    f"{item.reorder_point}."
                ),
            )
        )
    return recommendations


async def supplier_scorecard(db: AsyncSession, organization_id: UUID) -> list[SupplierScoreRead]:
    work_orders = [work_order for work_order in await list_work_orders(db, organization_id) if work_order.vendor]
    grouped: dict[str, list[MaintenanceWorkOrder]] = {}
    for work_order in work_orders:
        grouped.setdefault(work_order.vendor or "Unknown", []).append(work_order)

    scorecards = []
    for supplier_name, orders in sorted(grouped.items()):
        estimated = sum((order.estimated_cost or Decimal("0")) for order in orders)
        actual = sum((order.actual_cost or Decimal("0")) for order in orders)
        completed = sum(1 for order in orders if order.status == WorkOrderStatus.COMPLETED)
        safety = sum(1 for order in orders if order.safety_related)
        variance_penalty = 0
        if estimated > 0 and actual > estimated:
            variance_penalty = min(int(((actual - estimated) / estimated) * 100), 35)
        completion_bonus = int((completed / len(orders)) * 20)
        score = max(0, min(100, 70 + completion_bonus - variance_penalty))
        scorecards.append(
            SupplierScoreRead(
                supplier_name=supplier_name,
                work_orders=len(orders),
                completed_orders=completed,
                safety_orders=safety,
                estimated_cost=estimated.quantize(Decimal("0.01")),
                actual_cost=actual.quantize(Decimal("0.01")),
                score=score,
                recommendation=supplier_recommendation(score),
            )
        )
    return scorecards


async def create_supplier_order(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SupplierOrderCreate,
    authz: AuthorizationService,
) -> SupplierOrder:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    if payload.equipment_item_id is not None:
        await get_equipment_for_organization(db, payload.equipment_item_id, payload.organization_id)
    total_cost = (payload.unit_cost * payload.quantity).quantize(Decimal("0.01"))
    order = SupplierOrder(
        organization_id=payload.organization_id,
        equipment_item_id=payload.equipment_item_id,
        supplier_name=payload.supplier_name,
        item_name=payload.item_name,
        quantity=payload.quantity,
        unit_cost=payload.unit_cost,
        total_cost=total_cost,
        currency=payload.currency,
        status="ordered" if payload.submit else "draft",
        external_reference=payload.external_reference,
        ordered_at=datetime.now(UTC) if payload.submit else None,
        expected_delivery_at=payload.expected_delivery_at,
        notes=payload.notes,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def list_supplier_orders(
    db: AsyncSession,
    organization_id: UUID,
    open_only: bool = False,
) -> list[SupplierOrder]:
    statement = select(SupplierOrder).where(SupplierOrder.organization_id == organization_id)
    if open_only:
        statement = statement.where(SupplierOrder.status.in_(["draft", "ordered", "partial"]))
    return list(
        (
            await db.scalars(
                statement.order_by(SupplierOrder.expected_delivery_at.nullslast(), SupplierOrder.created_at.desc())
            )
        ).all()
    )


async def receive_supplier_order(
    db: AsyncSession,
    identity: CurrentIdentity,
    supplier_order_id: UUID,
    payload: SupplierOrderReceive,
    authz: AuthorizationService,
) -> SupplierOrder:
    order = await get_supplier_order(db, supplier_order_id)
    await ensure_manage_assets(authz, identity, order.organization_id)
    if order.status == "received":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Supplier order already received")
    quantity_received = payload.quantity_received or order.quantity
    if quantity_received != order.quantity:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Partial receiving requires split orders",
        )
    order.received_at = payload.received_at or datetime.now(UTC)
    order.status = "received"
    if payload.notes is not None:
        order.notes = payload.notes
    if order.equipment_item_id is not None:
        item = await get_equipment_for_organization(db, order.equipment_item_id, order.organization_id)
        item.quantity_total += quantity_received
        item.quantity_available += quantity_received
        item.status = equipment_status_for_quantity(item.quantity_available)
    await db.commit()
    await db.refresh(order)
    return order


async def equipment_lease_quote(
    db: AsyncSession,
    organization_id: UUID,
    equipment_item_id: UUID,
    quantity: int,
    term_months: int,
) -> EquipmentLeaseQuoteRead:
    item = await get_equipment_for_organization(db, equipment_item_id, organization_id)
    unit_value = item.unit_value or Decimal("0")
    depreciation = item.depreciation_rate or Decimal("20")
    asset_value = unit_value * quantity
    monthly_factor = Decimal("0.035") + (depreciation / Decimal("100") / Decimal("24"))
    monthly_amount = (asset_value * monthly_factor).quantize(Decimal("0.01"))
    total_amount = (monthly_amount * term_months).quantize(Decimal("0.01"))
    residual_value = max(asset_value - total_amount, Decimal("0")).quantize(Decimal("0.01"))
    return EquipmentLeaseQuoteRead(
        equipment_item_id=item.id,
        item_name=item.name,
        quantity=quantity,
        term_months=term_months,
        monthly_amount=monthly_amount,
        total_amount=total_amount,
        residual_value=residual_value,
        rationale=(
            "Lease estimate combines replacement value, expected depreciation, and a platform "
            "utilization factor for planning."
        ),
    )


async def utilization_recommendations(
    db: AsyncSession,
    organization_id: UUID,
) -> list[AssetUtilizationRecommendationRead]:
    equipment = await list_equipment_items(db, organization_id)
    checkouts = await list_checkouts(db, organization_id)
    work_orders = await list_work_orders(db, organization_id)
    now = datetime.now(UTC)
    recommendations: list[AssetUtilizationRecommendationRead] = []

    for item in equipment:
        if item.quantity_available <= item.reorder_point:
            recommendations.append(
                AssetUtilizationRecommendationRead(
                    target_type="equipment",
                    target_id=item.id,
                    title=f"Reorder {item.name}",
                    severity="high",
                    recommendation="Create a procurement order before the next training cycle.",
                    expected_impact="Prevents session disruption from low stock.",
                )
            )
        elif item.quantity_available == item.quantity_total and item.quantity_total > 1:
            recommendations.append(
                AssetUtilizationRecommendationRead(
                    target_type="equipment",
                    target_id=item.id,
                    title=f"Put {item.name} into circulation",
                    severity="medium",
                    recommendation="Assign the surplus to teams or bundle it into checkout kits.",
                    expected_impact="Improves utilization of already-owned assets.",
                )
            )

    for checkout in checkouts:
        if checkout.status == CheckoutStatus.CHECKED_OUT and is_before_now(checkout.due_at, now):
            recommendations.append(
                AssetUtilizationRecommendationRead(
                    target_type="checkout",
                    target_id=checkout.id,
                    title="Recover overdue equipment",
                    severity="high",
                    recommendation="Notify the borrower and block further checkout until returned.",
                    expected_impact="Improves asset availability and accountability.",
                )
            )

    for work_order in work_orders:
        if work_order.safety_related and work_order.status != WorkOrderStatus.COMPLETED:
            recommendations.append(
                AssetUtilizationRecommendationRead(
                    target_type="work_order",
                    target_id=work_order.id,
                    title=f"Close safety work: {work_order.title}",
                    severity="critical",
                    recommendation="Prioritize this work order before facility or equipment use.",
                    expected_impact="Reduces safety and compliance risk.",
                )
            )

    return recommendations[:20]


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def get_facility_for_organization(
    db: AsyncSession,
    facility_id: UUID,
    organization_id: UUID,
) -> Facility:
    facility = await db.get(Facility, facility_id)
    if facility is None or facility.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    return facility


async def get_equipment_for_organization(
    db: AsyncSession,
    equipment_item_id: UUID,
    organization_id: UUID,
) -> EquipmentItem:
    item = await db.get(EquipmentItem, equipment_item_id)
    if item is None or item.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return item


async def get_equipment(db: AsyncSession, equipment_item_id: UUID) -> EquipmentItem:
    item = await db.get(EquipmentItem, equipment_item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return item


async def get_team_for_organization(
    db: AsyncSession,
    team_id: UUID,
    organization_id: UUID,
) -> Team:
    team = await db.get(Team, team_id)
    if team is None or team.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


async def get_event_for_organization(
    db: AsyncSession,
    event_id: UUID,
    organization_id: UUID,
) -> Event:
    event = await db.get(Event, event_id)
    if event is None or event.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


async def get_person_member_for_organization(
    db: AsyncSession,
    person_id: UUID,
    organization_id: UUID,
) -> Person:
    person = await db.get(Person, person_id)
    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == person_id,
            Membership.status == "active",
        )
    )
    if person is None or membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return person


async def get_checkout(db: AsyncSession, checkout_id: UUID) -> EquipmentCheckout:
    checkout = await db.get(EquipmentCheckout, checkout_id)
    if checkout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkout not found")
    return checkout


async def get_work_order(db: AsyncSession, work_order_id: UUID) -> MaintenanceWorkOrder:
    work_order = await db.get(MaintenanceWorkOrder, work_order_id)
    if work_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")
    return work_order


async def get_supplier_order(db: AsyncSession, supplier_order_id: UUID) -> SupplierOrder:
    order = await db.get(SupplierOrder, supplier_order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier order not found")
    return order


async def ensure_facility_available(
    db: AsyncSession,
    facility_id: UUID,
    starts_at: datetime,
    ends_at: datetime,
) -> None:
    conflict = await db.scalar(
        select(FacilityBooking).where(
            FacilityBooking.facility_id == facility_id,
            FacilityBooking.status.in_(
                [
                    FacilityBookingStatus.REQUESTED,
                    FacilityBookingStatus.APPROVED,
                    FacilityBookingStatus.CONFIRMED,
                    FacilityBookingStatus.CHECKED_IN,
                ]
            ),
            FacilityBooking.starts_at < ends_at,
            FacilityBooking.ends_at > starts_at,
        )
    )
    if conflict is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Facility is already booked")


def equipment_status_for_quantity(quantity_available: int) -> EquipmentStatus:
    return EquipmentStatus.AVAILABLE if quantity_available > 0 else EquipmentStatus.CHECKED_OUT


def equipment_item_read(item: EquipmentItem):
    from app.schemas.assets import EquipmentItemRead

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


def supplier_recommendation(score: int) -> str:
    if score >= 85:
        return "Preferred supplier for renewals and urgent work."
    if score >= 65:
        return "Usable supplier; monitor cost and completion variance."
    return "Review supplier before assigning critical work."


def is_before_now(value: datetime, now: datetime) -> bool:
    comparable_now = now.replace(tzinfo=None) if value.tzinfo is None else now
    return value < comparable_now
