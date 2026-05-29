from base64 import b64decode
from binascii import Error as Base64Error
from calendar import monthrange
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import hmac
import json
import time
from hmac import compare_digest
from hashlib import sha256
from pathlib import Path
from re import sub
from secrets import token_urlsafe
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assets import (
    EmergencyActionPlan,
    EmergencyPlanActivation,
    EquipmentCheckout,
    EquipmentFile,
    EquipmentItem,
    EquipmentLeaseInstallment,
    EquipmentLeaseSchedule,
    EquipmentReader,
    EquipmentScanEvent,
    Facility,
    FacilityBooking,
    MaintenanceWorkOrder,
    SupplierOrder,
)
from app.models.commercial import FinanceInvoice, FinancePayment
from app.models.communication import CommunicationMessage, MessageRecipient
from app.models.enums import (
    AssetCondition,
    CheckoutStatus,
    CommunicationMessageType,
    CommunicationScopeType,
    EquipmentStatus,
    EmergencyActivationStatus,
    FacilityBookingStatus,
    MemberSubjectType,
    SafeguardingIncidentSeverity,
    SafeguardingIncidentType,
    WorkOrderStatus,
)
from app.models.enums import CommercialStatus
from app.models.event import Event, SafeguardingIncident
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.team import Team
from app.core.config import Settings, get_settings
from app.schemas.assets import (
    AssetAccountingExportRead,
    AssetAccountingExportRow,
    AssetAccountingSyncRead,
    AssetSummaryRead,
    EmergencyActivationAlertCreate,
    EmergencyActivationIncidentCreate,
    EmergencyActionPlanCreate,
    EmergencyActionPlanUpdate,
    EmergencyEscalationTimerRunCreate,
    EmergencyEscalationTimerRunRead,
    EmergencyPlanActivationCreate,
    EmergencyPlanActivationUpdate,
    EquipmentCheckoutCreate,
    EquipmentCheckoutReturn,
    EquipmentLeaseQuoteRead,
    EquipmentFileUploadCreate,
    EquipmentLeaseInvoiceCreate,
    EquipmentLeaseInvoiceRead,
    EquipmentLeaseInstallmentRead,
    EquipmentLeasePaymentCreate,
    EquipmentLeasePaymentRead,
    EquipmentPhotoUpdate,
    EquipmentLeaseScheduleCreate,
    EquipmentLeaseScheduleRead,
    EquipmentReaderCreate,
    EquipmentReaderGatewayScanCreate,
    EquipmentReaderProvisionRead,
    EquipmentReaderRead,
    EquipmentScanEventCreate,
    EquipmentScanEventRead,
    EquipmentScanRead,
    EquipmentItemCreate,
    FacilityBookingCreate,
    FacilityCreate,
    MaintenanceWorkOrderCreate,
    MaintenanceWorkOrderUpdate,
    ProcurementRecommendationRead,
    SupplierOrderCreate,
    SupplierInvoiceSyncRead,
    SupplierOrderReceive,
    SupplierOrderRead,
    SupplierOrderSubmissionRead,
    SupplierScoreRead,
    AssetUtilizationRecommendationRead,
)
from app.schemas.commercial import FinanceInvoiceRead, FinancePaymentRead
from app.schemas.communication import CommunicationMessageCreate
from app.schemas.safeguarding import SafeguardingIncidentCreate
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.communications import create_message
from app.services.safeguarding import create_safeguarding_incident
from app.services.secrets import resolve_secret
from app.services.storage.objects import get_object, put_object


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


async def create_emergency_action_plan(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: EmergencyActionPlanCreate,
    authz: AuthorizationService,
) -> EmergencyActionPlan:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    if payload.facility_id is not None:
        await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    plan = EmergencyActionPlan(**payload.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def list_emergency_action_plans(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
) -> list[EmergencyActionPlan]:
    statement = select(EmergencyActionPlan).where(EmergencyActionPlan.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(EmergencyActionPlan.facility_id == facility_id)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    EmergencyActionPlan.status,
                    EmergencyActionPlan.review_due_on.nulls_last(),
                    EmergencyActionPlan.title,
                )
            )
        ).all()
    )


async def update_emergency_action_plan(
    db: AsyncSession,
    identity: CurrentIdentity,
    plan_id: UUID,
    payload: EmergencyActionPlanUpdate,
    authz: AuthorizationService,
) -> EmergencyActionPlan:
    plan = await db.get(EmergencyActionPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergency action plan not found")
    await ensure_manage_assets(authz, identity, plan.organization_id)
    for field in [
        "status",
        "review_due_on",
        "emergency_contacts",
        "evacuation_routes",
        "medical_protocols",
        "weather_protocols",
        "communication_protocols",
        "incident_command_roles",
        "escalation_matrix",
        "external_agency_contacts",
        "equipment_locations",
        "assembly_points",
        "special_needs_plan",
        "notes",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(plan, field, value)
    await db.commit()
    await db.refresh(plan)
    return plan


async def activate_emergency_action_plan(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: EmergencyPlanActivationCreate,
    authz: AuthorizationService,
) -> EmergencyPlanActivation:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    plan = await db.get(EmergencyActionPlan, payload.plan_id)
    if plan is None or plan.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergency action plan not found")
    facility_id = payload.facility_id or plan.facility_id
    if facility_id is not None:
        await get_facility_for_organization(db, facility_id, payload.organization_id)
    if payload.incident_id is not None:
        incident = await db.get(SafeguardingIncident, payload.incident_id)
        if incident is None or incident.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    activation = EmergencyPlanActivation(
        facility_id=facility_id,
        activated_by_person_id=identity.person_id,
        activated_at=payload.activated_at or datetime.now(UTC),
        guidance_steps=payload.guidance_steps or plan.medical_protocols or plan.evacuation_routes,
        communication_log=payload.communication_log or emergency_communication_plan(plan),
        **payload.model_dump(exclude={"facility_id", "activated_at", "guidance_steps", "communication_log"}),
    )
    db.add(activation)
    await db.commit()
    await db.refresh(activation)
    return activation


async def list_emergency_plan_activations(
    db: AsyncSession,
    organization_id: UUID,
    status_filter: EmergencyActivationStatus | None = None,
) -> list[EmergencyPlanActivation]:
    statement = select(EmergencyPlanActivation).where(
        EmergencyPlanActivation.organization_id == organization_id
    )
    if status_filter is not None:
        statement = statement.where(EmergencyPlanActivation.status == status_filter)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    EmergencyPlanActivation.status,
                    EmergencyPlanActivation.activated_at.desc(),
                )
            )
        ).all()
    )


async def update_emergency_plan_activation(
    db: AsyncSession,
    identity: CurrentIdentity,
    activation_id: UUID,
    payload: EmergencyPlanActivationUpdate,
    authz: AuthorizationService,
) -> EmergencyPlanActivation:
    activation = await db.get(EmergencyPlanActivation, activation_id)
    if activation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergency activation not found")
    await ensure_manage_assets(authz, identity, activation.organization_id)
    if payload.status is not None:
        activation.status = payload.status
        if payload.status in {
            EmergencyActivationStatus.RESOLVED,
            EmergencyActivationStatus.CANCELLED,
            EmergencyActivationStatus.REVIEWED,
        }:
            activation.closed_by_person_id = identity.person_id
            activation.closed_at = payload.closed_at or activation.closed_at or datetime.now(UTC)
    for field in [
        "closed_at",
        "escalation_level",
        "assigned_responders",
        "guidance_steps",
        "communication_log",
        "outcome_summary",
        "response_time_seconds",
        "notes",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(activation, field, value)
    await db.commit()
    await db.refresh(activation)
    return activation


async def run_emergency_escalation_timer_scheduler(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: EmergencyEscalationTimerRunCreate,
    authz: AuthorizationService,
) -> EmergencyEscalationTimerRunRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    return await run_emergency_escalation_timer_worker(
        db,
        organization_id=payload.organization_id,
        unresolved_after_minutes=payload.unresolved_after_minutes,
        repeat_after_minutes=payload.repeat_after_minutes,
        limit=payload.limit,
        dry_run=payload.dry_run,
    )


async def run_emergency_escalation_timer_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    *,
    unresolved_after_minutes: int = 15,
    repeat_after_minutes: int = 15,
    limit: int = 50,
    dry_run: bool = False,
) -> EmergencyEscalationTimerRunRead:
    due_activations = await emergency_activations_due_for_escalation(
        db,
        organization_id,
        unresolved_after_minutes=unresolved_after_minutes,
        repeat_after_minutes=repeat_after_minutes,
        limit=limit,
    )
    escalated_ids: list[UUID] = []
    skipped_count = 0
    failed_count = 0
    max_level_count = 0
    now = datetime.now(UTC)

    for activation in due_activations:
        if activation.escalation_level >= 5:
            max_level_count += 1
            skipped_count += 1
            continue
        if dry_run:
            skipped_count += 1
            continue
        try:
            activation.escalation_level = min(5, activation.escalation_level + 1)
            activation.communication_log = append_emergency_escalation_log(
                activation.communication_log,
                activation.escalation_level,
                now,
            )
            activation.notes = "Automated emergency escalation timer advanced this activation."
            escalated_ids.append(activation.id)
        except Exception:
            failed_count += 1
            await db.rollback()

    if escalated_ids:
        await db.commit()

    return EmergencyEscalationTimerRunRead(
        organization_id=organization_id,
        eligible_count=len(due_activations),
        executed_count=len(due_activations) - skipped_count,
        escalated_count=len(escalated_ids),
        skipped_count=skipped_count,
        failed_count=failed_count,
        dry_run=dry_run,
        activation_ids=escalated_ids,
        max_level_count=max_level_count,
    )


async def emergency_activations_due_for_escalation(
    db: AsyncSession,
    organization_id: UUID | None,
    *,
    unresolved_after_minutes: int,
    repeat_after_minutes: int,
    limit: int,
) -> list[EmergencyPlanActivation]:
    now = datetime.now(UTC)
    statement = (
        select(EmergencyPlanActivation)
        .where(EmergencyPlanActivation.status == EmergencyActivationStatus.ACTIVE)
        .where(EmergencyPlanActivation.activated_at <= now - timedelta(minutes=unresolved_after_minutes))
        .where(EmergencyPlanActivation.escalation_level < 5)
        .order_by(EmergencyPlanActivation.activated_at.asc())
        .limit(limit)
    )
    if organization_id is not None:
        statement = statement.where(EmergencyPlanActivation.organization_id == organization_id)
    rows = list((await db.scalars(statement)).all())
    repeat_window = timedelta(minutes=repeat_after_minutes)
    return [
        activation
        for activation in rows
        if normalize_datetime(
            activation.activated_at if activation.escalation_level <= 1 else activation.updated_at
        )
        <= now - repeat_window
    ]


def append_emergency_escalation_log(
    existing_log: str | None,
    escalation_level: int,
    escalated_at: datetime,
) -> str:
    line = (
        f"{escalated_at.isoformat()}: automated emergency escalation timer "
        f"raised response to level {escalation_level}."
    )
    return f"{existing_log}\n{line}" if existing_log else line


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


async def dispatch_emergency_activation_alert(
    db: AsyncSession,
    identity: CurrentIdentity,
    activation_id: UUID,
    payload: EmergencyActivationAlertCreate,
    authz: AuthorizationService,
) -> tuple[CommunicationMessage, int]:
    activation = await db.get(EmergencyPlanActivation, activation_id)
    if activation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergency activation not found")
    await ensure_manage_assets(authz, identity, activation.organization_id)

    scope_id = payload.scope_id
    if scope_id is None and payload.scope_type == CommunicationScopeType.ORGANIZATION:
        scope_id = activation.organization_id
    if scope_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="scope_id is required for non-organization emergency alerts",
        )

    subject = payload.subject or emergency_alert_subject(activation)
    plan = await db.get(EmergencyActionPlan, activation.plan_id)
    body = payload.body or emergency_alert_body(activation, plan)
    message = await create_message(
        db,
        identity,
        CommunicationMessageCreate(
            organization_id=activation.organization_id,
            message_type=CommunicationMessageType.ALERT,
            channel=payload.channel,
            scope_type=payload.scope_type,
            scope_id=scope_id,
            recipient_person_ids=payload.recipient_person_ids,
            subject=subject,
            body=body,
            urgent=True,
            quiet_hours_override=True,
            copy_guardians_for_minors=payload.copy_guardians_for_minors,
        ),
        authz,
    )
    recipient_count = await db.scalar(
        select(func.count(MessageRecipient.id)).where(MessageRecipient.message_id == message.id)
    )
    return message, int(recipient_count or 0)


async def create_incident_from_emergency_activation(
    db: AsyncSession,
    identity: CurrentIdentity,
    activation_id: UUID,
    payload: EmergencyActivationIncidentCreate,
    authz: AuthorizationService,
) -> SafeguardingIncident:
    activation = await db.get(EmergencyPlanActivation, activation_id)
    if activation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergency activation not found")
    await ensure_manage_assets(authz, identity, activation.organization_id)

    if activation.incident_id is not None:
        incident = await db.get(SafeguardingIncident, activation.incident_id)
        if incident is not None:
            return incident

    incident = await create_safeguarding_incident(
        db,
        identity,
        SafeguardingIncidentCreate(
            organization_id=activation.organization_id,
            incident_type=payload.incident_type or incident_type_for_emergency(activation.emergency_type),
            severity=payload.severity or severity_for_activation(activation),
            occurred_at=activation.activated_at,
            location=activation.location_detail,
            title=payload.title or f"{activation.emergency_type.value.title()} emergency response",
            description=payload.description or emergency_incident_description(activation),
            immediate_action=payload.immediate_action or emergency_immediate_action(activation),
            medical_follow_up_required=payload.medical_follow_up_required,
            regulatory_report_required=payload.regulatory_report_required,
        ),
        authz,
    )
    activation.incident_id = incident.id
    await db.commit()
    await db.refresh(activation)
    return incident


def emergency_alert_subject(activation: EmergencyPlanActivation) -> str:
    return f"Emergency alert: {activation.emergency_type.value} at {activation.location_detail}"[:240]


def emergency_alert_body(
    activation: EmergencyPlanActivation,
    plan: EmergencyActionPlan | None = None,
) -> str:
    lines = [
        f"Emergency type: {activation.emergency_type.value}",
        f"Status: {activation.status.value}",
        f"Escalation level: {activation.escalation_level}",
        f"Location: {activation.location_detail}",
    ]
    if activation.assigned_responders:
        lines.append(f"Responders: {activation.assigned_responders}")
    if activation.guidance_steps:
        lines.append(f"Guidance: {activation.guidance_steps}")
    if activation.communication_log:
        lines.append(f"Communication plan: {activation.communication_log}")
    if plan is not None and plan.incident_command_roles:
        lines.append(f"Incident command: {plan.incident_command_roles}")
    if plan is not None and plan.escalation_matrix:
        lines.append(f"Escalation matrix: {plan.escalation_matrix}")
    if plan is not None and plan.external_agency_contacts:
        lines.append(f"External agencies: {plan.external_agency_contacts}")
    if activation.notes:
        lines.append(f"Notes: {activation.notes}")
    lines.append("Follow the emergency action plan and keep the area clear unless assigned to respond.")
    return "\n".join(lines)[:8000]


def emergency_communication_plan(plan: EmergencyActionPlan) -> str | None:
    parts = [
        plan.communication_protocols,
        f"Incident command: {plan.incident_command_roles}" if plan.incident_command_roles else None,
        f"Escalation matrix: {plan.escalation_matrix}" if plan.escalation_matrix else None,
        f"External agencies: {plan.external_agency_contacts}" if plan.external_agency_contacts else None,
    ]
    return "\n".join(part for part in parts if part) or None


def incident_type_for_emergency(emergency_type) -> SafeguardingIncidentType:
    mapping = {
        "medical": SafeguardingIncidentType.MEDICAL,
        "fire": SafeguardingIncidentType.FACILITY,
        "weather": SafeguardingIncidentType.WEATHER,
        "security": SafeguardingIncidentType.SECURITY,
        "evacuation": SafeguardingIncidentType.FACILITY,
        "missing_person": SafeguardingIncidentType.SAFEGUARDING,
        "other": SafeguardingIncidentType.OTHER,
    }
    return mapping.get(emergency_type.value, SafeguardingIncidentType.OTHER)


def severity_for_activation(activation: EmergencyPlanActivation) -> SafeguardingIncidentSeverity:
    if activation.escalation_level >= 4:
        return SafeguardingIncidentSeverity.CRITICAL
    if activation.escalation_level >= 2:
        return SafeguardingIncidentSeverity.HIGH
    return SafeguardingIncidentSeverity.MEDIUM


def emergency_incident_description(activation: EmergencyPlanActivation) -> str:
    lines = [
        f"Emergency activation {activation.id} was opened for {activation.emergency_type.value}.",
        f"Location: {activation.location_detail}",
        f"Escalation level: {activation.escalation_level}",
        f"Status at report creation: {activation.status.value}",
    ]
    if activation.assigned_responders:
        lines.append(f"Assigned responders: {activation.assigned_responders}")
    if activation.guidance_steps:
        lines.append(f"Guidance followed: {activation.guidance_steps}")
    if activation.communication_log:
        lines.append(f"Communication log: {activation.communication_log}")
    if activation.outcome_summary:
        lines.append(f"Outcome: {activation.outcome_summary}")
    return "\n".join(lines)[:8000]


def emergency_immediate_action(activation: EmergencyPlanActivation) -> str | None:
    action = activation.guidance_steps or activation.assigned_responders
    return action[:4000] if action else None


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
    item, match_type = await match_equipment_code(db, organization_id, code)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return EquipmentScanRead(
        scanned_code=code,
        match_type=match_type or "unknown",
        item=equipment_item_read(item),
    )


async def record_equipment_scan_event(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: EquipmentScanEventCreate,
    authz: AuthorizationService,
) -> EquipmentScanEventRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    code = payload.scanned_code.strip()
    if not code:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Scan code is required")
    item, match_type = await match_equipment_code(db, payload.organization_id, code)
    scanned_at = payload.scanned_at or datetime.now(UTC)
    reader_id = payload.reader_id.strip()
    if not reader_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Reader ID is required")
    reader_location = payload.reader_location.strip() if payload.reader_location else None
    movement = payload.movement.strip().lower() or "audit"
    source = payload.source.strip().lower() or "rfid_reader"
    event = EquipmentScanEvent(
        organization_id=payload.organization_id,
        equipment_item_id=item.id if item else None,
        scanned_code=code,
        match_type=match_type,
        item_name=item.name if item else None,
        reader_id=reader_id,
        reader_location=reader_location,
        source=source,
        movement=movement,
        matched=item is not None,
        scanned_at=scanned_at,
        external_reference=payload.external_reference,
        notes=payload.notes,
    )
    if item is not None:
        item.last_audit_on = scanned_at.date()
        if reader_location and movement in {"audit", "in", "location"}:
            item.storage_location = reader_location
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return equipment_scan_event_read(event)


async def list_equipment_scan_events(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    equipment_item_id: UUID | None = None,
    matched: bool | None = None,
) -> list[EquipmentScanEventRead]:
    await ensure_manage_assets(authz, identity, organization_id)
    statement = select(EquipmentScanEvent).where(EquipmentScanEvent.organization_id == organization_id)
    if equipment_item_id is not None:
        statement = statement.where(EquipmentScanEvent.equipment_item_id == equipment_item_id)
    if matched is not None:
        statement = statement.where(EquipmentScanEvent.matched == matched)
    events = await db.scalars(statement.order_by(EquipmentScanEvent.scanned_at.desc()))
    return [equipment_scan_event_read(event) for event in events.all()]


async def provision_equipment_reader(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: EquipmentReaderCreate,
    authz: AuthorizationService,
) -> EquipmentReaderProvisionRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    reader_id = payload.reader_id.strip()
    existing = await db.scalar(
        select(EquipmentReader).where(
            EquipmentReader.organization_id == payload.organization_id,
            EquipmentReader.reader_id == reader_id,
        )
    )
    api_key = payload.api_key or token_urlsafe(32)
    if existing is None:
        reader = EquipmentReader(
            organization_id=payload.organization_id,
            reader_id=reader_id,
            name=payload.name,
            location=payload.location,
            status=payload.status.strip().lower(),
            api_key_hash=hash_reader_key(api_key),
            notes=payload.notes,
        )
        db.add(reader)
    else:
        reader = existing
        reader.name = payload.name
        reader.location = payload.location
        reader.status = payload.status.strip().lower()
        reader.api_key_hash = hash_reader_key(api_key)
        reader.notes = payload.notes
    await db.commit()
    await db.refresh(reader)
    return EquipmentReaderProvisionRead(reader=equipment_reader_read(reader), api_key=api_key)


async def list_equipment_readers(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[EquipmentReaderRead]:
    await ensure_manage_assets(authz, identity, organization_id)
    readers = await db.scalars(
        select(EquipmentReader)
        .where(EquipmentReader.organization_id == organization_id)
        .order_by(EquipmentReader.location, EquipmentReader.name)
    )
    return [equipment_reader_read(reader) for reader in readers.all()]


async def record_gateway_equipment_scan(
    db: AsyncSession,
    organization_id: UUID,
    reader_id: str,
    api_key: str | None,
    payload: EquipmentReaderGatewayScanCreate,
) -> EquipmentScanEventRead:
    reader = await get_equipment_reader_by_reader_id(db, organization_id, reader_id.strip())
    if reader.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Reader is not active")
    if not api_key or not compare_digest(reader.api_key_hash, hash_reader_key(api_key)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reader key")
    code = payload.scanned_code.strip()
    item, match_type = await match_equipment_code(db, reader.organization_id, code)
    scanned_at = payload.scanned_at or datetime.now(UTC)
    reader.last_seen_at = scanned_at
    reader.last_scan_at = scanned_at
    event = EquipmentScanEvent(
        organization_id=reader.organization_id,
        equipment_item_id=item.id if item else None,
        scanned_code=code,
        match_type=match_type,
        item_name=item.name if item else None,
        reader_id=reader.reader_id,
        reader_location=reader.location,
        source="rfid_gateway",
        movement=payload.movement.strip().lower() or "audit",
        matched=item is not None,
        scanned_at=scanned_at,
        external_reference=payload.external_reference,
        notes=payload.notes,
    )
    if item is not None:
        item.last_audit_on = scanned_at.date()
        if reader.location and event.movement in {"audit", "in", "location"}:
            item.storage_location = reader.location
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return equipment_scan_event_read(event)


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


async def upload_equipment_file(
    db: AsyncSession,
    identity: CurrentIdentity,
    equipment_item_id: UUID,
    payload: EquipmentFileUploadCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> EquipmentFile:
    item = await get_equipment(db, equipment_item_id)
    await ensure_manage_assets(authz, identity, item.organization_id)
    content = decode_upload_content(payload.content_base64)
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="File is empty")
    selected_settings = settings or get_settings()
    checksum = sha256(content).hexdigest()
    safe_name = safe_upload_filename(payload.filename)
    storage_name = f"{checksum[:16]}-{safe_name}"
    relative_path = (Path(str(item.organization_id)) / str(item.id) / storage_name).as_posix()
    stored = put_object(
        selected_settings,
        local_root=selected_settings.equipment_file_dir,
        local_url_prefix=selected_settings.equipment_file_url_prefix,
        key=relative_path,
        content=content,
        content_type=payload.content_type or "application/octet-stream",
    )
    file_record = EquipmentFile(
        organization_id=item.organization_id,
        equipment_item_id=item.id,
        uploaded_by_person_id=identity.person_id,
        filename=safe_name,
        content_type=payload.content_type or "application/octet-stream",
        size_bytes=len(content),
        checksum=checksum,
        storage_url=stored.url,
        storage_path=stored.path,
        notes=payload.notes,
    )
    if payload.mark_as_photo or payload.content_type.startswith("image/"):
        item.photo_url = stored.url
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)
    return file_record


async def list_equipment_files(
    db: AsyncSession,
    equipment_item_id: UUID,
) -> list[EquipmentFile]:
    await get_equipment(db, equipment_item_id)
    return list(
        (
            await db.scalars(
                select(EquipmentFile)
                .where(EquipmentFile.equipment_item_id == equipment_item_id)
                .order_by(EquipmentFile.created_at.desc())
            )
        ).all()
    )


async def downloadable_equipment_file(
    db: AsyncSession,
    identity: CurrentIdentity,
    file_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> dict[str, object]:
    file_record = await db.get(EquipmentFile, file_id)
    if file_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment file not found")
    await ensure_manage_assets(authz, identity, file_record.organization_id)
    selected_settings = settings or get_settings()
    content = get_object(
        selected_settings,
        local_root=selected_settings.equipment_file_dir,
        key=equipment_file_object_key(file_record, selected_settings),
    )
    actual_checksum = sha256(content).hexdigest()
    if actual_checksum != file_record.checksum:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Equipment file checksum mismatch")
    return {
        "content": content,
        "filename": file_record.filename,
        "content_type": file_record.content_type,
        "checksum": actual_checksum,
    }


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
        (
            Decimal(str(max((booking.ends_at - booking.starts_at).total_seconds() / 3600, 0)))
            * (booking.rate or Decimal("0"))
            for booking in upcoming_bookings
        ),
        Decimal("0"),
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


async def submit_supplier_order(
    db: AsyncSession,
    identity: CurrentIdentity,
    supplier_order_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> SupplierOrderSubmissionRead:
    order = await get_supplier_order(db, supplier_order_id)
    await ensure_manage_assets(authz, identity, order.organization_id)
    selected_settings = settings or get_settings()
    submitted_at = datetime.now(UTC)
    result = {
        "submission_mode": selected_settings.supplier_order_submission_mode,
        "adapter_profile": supplier_order_adapter_profile(selected_settings, order),
        "delivery_attempted": False,
        "delivered": False,
        "destination": selected_settings.supplier_order_webhook_url or None,
        "provider_status_code": None,
        "submitted_at": submitted_at,
        "failure_reason": None,
    }
    if order.status == "received":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Received orders cannot be resubmitted")

    if selected_settings.supplier_order_submission_mode == "record_only":
        order.status = "submission_pending"
        result["failure_reason"] = "Record-only supplier mode; order prepared for manual submission."
    elif not selected_settings.supplier_order_webhook_url:
        order.status = "submission_pending"
        result["failure_reason"] = "Supplier webhook mode is enabled but no webhook URL is configured."
    else:
        result["delivery_attempted"] = True
        try:
            async with httpx.AsyncClient(timeout=selected_settings.supplier_order_submission_timeout_seconds) as client:
                response = await client.post(
                    selected_settings.supplier_order_webhook_url,
                    json=supplier_order_payload(order, submitted_at, str(result["adapter_profile"])),
                    headers=await supplier_order_headers(selected_settings),
                )
            result["provider_status_code"] = response.status_code
            result["delivered"] = 200 <= response.status_code < 300
            if result["delivered"]:
                order.status = "submitted"
                order.external_reference = order.external_reference or f"SUP-{order.id}"
            else:
                order.status = "submission_failed"
                result["failure_reason"] = f"Supplier webhook returned {response.status_code}: {response.text[:500]}"
        except httpx.HTTPError as error:
            order.status = "submission_failed"
            result["failure_reason"] = f"Supplier webhook failed: {error}"

    order.notes = supplier_order_submission_notes(order.notes, result)
    await db.commit()
    await db.refresh(order)
    return SupplierOrderSubmissionRead(order=supplier_order_read(order), **result)


async def sync_supplier_invoice(
    db: AsyncSession,
    identity: CurrentIdentity,
    supplier_order_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> SupplierInvoiceSyncRead:
    order = await get_supplier_order(db, supplier_order_id)
    await ensure_manage_assets(authz, identity, order.organization_id)
    if order.status not in {"received", "submitted", "ordered"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Supplier order is not ready for invoice sync")
    selected_settings = settings or get_settings()
    synced_at = datetime.now(UTC)
    result = {
        "sync_mode": selected_settings.supplier_invoice_sync_mode,
        "adapter_profile": supplier_invoice_adapter_profile(selected_settings, order),
        "sync_attempted": False,
        "synced": False,
        "destination": selected_settings.supplier_invoice_webhook_url or None,
        "provider_status_code": None,
        "synced_at": synced_at,
        "failure_reason": None,
    }
    if selected_settings.supplier_invoice_sync_mode == "record_only":
        order.status = "invoice_sync_pending" if order.status != "received" else "received_invoice_pending"
        result["failure_reason"] = "Record-only invoice sync mode; supplier invoice prepared for manual entry."
    elif not selected_settings.supplier_invoice_webhook_url:
        order.status = "invoice_sync_pending" if order.status != "received" else "received_invoice_pending"
        result["failure_reason"] = "Supplier invoice webhook mode is enabled but no webhook URL is configured."
    else:
        result["sync_attempted"] = True
        try:
            async with httpx.AsyncClient(timeout=selected_settings.supplier_invoice_sync_timeout_seconds) as client:
                response = await client.post(
                    selected_settings.supplier_invoice_webhook_url,
                    json=supplier_invoice_sync_payload(order, synced_at, str(result["adapter_profile"])),
                    headers=await supplier_invoice_headers(selected_settings),
                )
            result["provider_status_code"] = response.status_code
            result["synced"] = 200 <= response.status_code < 300
            if result["synced"]:
                order.status = "invoice_synced"
            else:
                order.status = "invoice_sync_failed"
                result["failure_reason"] = f"Supplier invoice webhook returned {response.status_code}: {response.text[:500]}"
        except httpx.HTTPError as error:
            order.status = "invoice_sync_failed"
            result["failure_reason"] = f"Supplier invoice webhook failed: {error}"
    order.notes = supplier_invoice_sync_notes(order.notes, result)
    await db.commit()
    await db.refresh(order)
    return SupplierInvoiceSyncRead(order=supplier_order_read(order), **result)


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


async def create_equipment_lease_invoice(
    db: AsyncSession,
    identity: CurrentIdentity,
    equipment_item_id: UUID,
    payload: EquipmentLeaseInvoiceCreate,
    authz: AuthorizationService,
) -> EquipmentLeaseInvoiceRead:
    item = await get_equipment_for_organization(db, equipment_item_id, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    if payload.person_id is not None:
        await get_person_member_for_organization(db, payload.person_id, payload.organization_id)
    quote = await equipment_lease_quote(
        db,
        payload.organization_id,
        equipment_item_id,
        payload.quantity,
        payload.term_months,
    )
    today = datetime.now(UTC).date()
    invoice = FinanceInvoice(
        organization_id=payload.organization_id,
        person_id=payload.person_id,
        team_id=payload.team_id,
        sponsor_id=None,
        invoice_number=f"LEASE-{today.strftime('%Y%m%d')}-{str(item.id)[:8]}",
        title=f"{item.name} lease ({payload.term_months} months)",
        amount_due=quote.total_amount,
        amount_paid=Decimal("0"),
        currency="USD",
        due_on=payload.due_on or today,
        memo=payload.memo
        or (
            f"{payload.quantity} x {item.name}; monthly estimate {quote.monthly_amount}; "
            f"residual value {quote.residual_value}. {quote.rationale}"
        ),
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return EquipmentLeaseInvoiceRead(
        lease_quote=quote,
        invoice=finance_invoice_read(invoice),
    )


async def create_equipment_lease_schedule(
    db: AsyncSession,
    identity: CurrentIdentity,
    equipment_item_id: UUID,
    payload: EquipmentLeaseScheduleCreate,
    authz: AuthorizationService,
) -> EquipmentLeaseScheduleRead:
    item = await get_equipment_for_organization(db, equipment_item_id, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    if payload.person_id is not None:
        await get_person_member_for_organization(db, payload.person_id, payload.organization_id)
    quote = await equipment_lease_quote(
        db,
        payload.organization_id,
        equipment_item_id,
        payload.quantity,
        payload.term_months,
    )
    starts_on = payload.starts_on or datetime.now(UTC).date()
    invoice = FinanceInvoice(
        organization_id=payload.organization_id,
        person_id=payload.person_id,
        team_id=payload.team_id,
        sponsor_id=None,
        invoice_number=f"LEASE-SCH-{starts_on.strftime('%Y%m%d')}-{str(item.id)[:8]}",
        title=f"{item.name} lease schedule ({payload.term_months} months)",
        amount_due=quote.total_amount,
        amount_paid=Decimal("0"),
        currency="USD",
        due_on=starts_on,
        memo=payload.notes
        or (
            f"Scheduled lease for {payload.quantity} x {item.name}; "
            f"{payload.term_months} installments at {quote.monthly_amount}."
        ),
    )
    db.add(invoice)
    await db.flush()
    schedule = EquipmentLeaseSchedule(
        organization_id=payload.organization_id,
        equipment_item_id=item.id,
        finance_invoice_id=invoice.id,
        person_id=payload.person_id,
        team_id=payload.team_id,
        quantity=payload.quantity,
        term_months=payload.term_months,
        monthly_amount=quote.monthly_amount,
        total_amount=quote.total_amount,
        currency="USD",
        starts_on=starts_on,
        status="active",
        notes=payload.notes,
    )
    db.add(schedule)
    await db.flush()
    installments = build_lease_installments(schedule, starts_on)
    db.add_all(installments)
    await db.commit()
    await db.refresh(schedule)
    await db.refresh(invoice)
    return equipment_lease_schedule_read(schedule, invoice, installments)


async def list_equipment_lease_schedules(
    db: AsyncSession,
    organization_id: UUID,
    equipment_item_id: UUID | None = None,
) -> list[EquipmentLeaseScheduleRead]:
    statement = select(EquipmentLeaseSchedule).where(EquipmentLeaseSchedule.organization_id == organization_id)
    if equipment_item_id is not None:
        statement = statement.where(EquipmentLeaseSchedule.equipment_item_id == equipment_item_id)
    schedules = (
        await db.scalars(statement.order_by(EquipmentLeaseSchedule.starts_on.desc(), EquipmentLeaseSchedule.created_at.desc()))
    ).all()
    result = []
    for schedule in schedules:
        invoice = await db.get(FinanceInvoice, schedule.finance_invoice_id)
        installments = await list_lease_installments(db, schedule.id)
        if invoice is not None:
            result.append(equipment_lease_schedule_read(schedule, invoice, installments))
    return result


async def reconcile_equipment_lease_payment(
    db: AsyncSession,
    identity: CurrentIdentity,
    lease_schedule_id: UUID,
    payload: EquipmentLeasePaymentCreate,
    authz: AuthorizationService,
) -> EquipmentLeasePaymentRead:
    schedule = await get_lease_schedule(db, lease_schedule_id)
    await ensure_manage_assets(authz, identity, schedule.organization_id)
    invoice = await db.get(FinanceInvoice, schedule.finance_invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease invoice not found")
    installments = await list_lease_installments(db, schedule.id)
    outstanding_installments = [item for item in installments if item.amount_paid < item.amount]
    if not outstanding_installments:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lease schedule is already paid")
    amount = payload.amount or (outstanding_installments[0].amount - outstanding_installments[0].amount_paid)
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Payment amount must be positive")
    remaining_invoice_balance = max(invoice.amount_due - invoice.amount_paid, Decimal("0")).quantize(Decimal("0.01"))
    if amount > remaining_invoice_balance:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Payment exceeds lease balance")
    payment = FinancePayment(
        organization_id=schedule.organization_id,
        invoice_id=invoice.id,
        amount=amount,
        currency=schedule.currency,
        method=payload.method,
        external_reference=payload.external_reference,
        received_at=datetime.now(UTC),
        notes=payload.notes,
    )
    amount_remaining = amount
    paid_count = 0
    partial_count = 0
    now = datetime.now(UTC)
    for installment in outstanding_installments:
        if amount_remaining <= 0:
            break
        installment_balance = (installment.amount - installment.amount_paid).quantize(Decimal("0.01"))
        applied = min(amount_remaining, installment_balance).quantize(Decimal("0.01"))
        installment.amount_paid = (installment.amount_paid + applied).quantize(Decimal("0.01"))
        amount_remaining = (amount_remaining - applied).quantize(Decimal("0.01"))
        if installment.amount_paid >= installment.amount:
            installment.amount_paid = installment.amount
            installment.status = "paid"
            installment.paid_at = now
            paid_count += 1
        else:
            installment.status = "partial"
            partial_count += 1
    invoice.amount_paid += amount
    invoice.status = CommercialStatus.PAID if invoice.amount_paid >= invoice.amount_due else CommercialStatus.PARTIAL
    if all(item.amount_paid >= item.amount for item in installments):
        schedule.status = "paid"
    elif paid_count > 0 or partial_count > 0:
        schedule.status = "active"
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    await db.refresh(schedule)
    await db.refresh(invoice)
    refreshed_installments = await list_lease_installments(db, schedule.id)
    return EquipmentLeasePaymentRead(
        schedule=equipment_lease_schedule_read(schedule, invoice, refreshed_installments),
        payment=finance_payment_read(payment),
        installments_paid=paid_count,
        installments_partially_paid=partial_count,
        amount_applied=amount,
        remaining_balance=max(invoice.amount_due - invoice.amount_paid, Decimal("0")).quantize(Decimal("0.01")),
    )


async def asset_accounting_export(
    db: AsyncSession,
    organization_id: UUID,
    system: str = "quickbooks",
    basis: str = "accrual",
) -> AssetAccountingExportRead:
    await get_organization(db, organization_id)
    supplier_orders = [
        order
        for order in await list_supplier_orders(db, organization_id)
        if order.status not in {"draft", "submission_failed", "invoice_sync_failed"}
    ]
    lease_schedule_reads = await list_equipment_lease_schedules(db, organization_id)
    rows: list[AssetAccountingExportRow] = []
    for order in supplier_orders:
        label = f"{order.supplier_name} {order.item_name}"
        rows.extend(
            [
                AssetAccountingExportRow(
                    row_type="supplier_equipment_purchase",
                    source_id=order.id,
                    source_label=label,
                    account_code=asset_account_code(system, "equipment_asset"),
                    memo=f"{order.quantity} x {order.item_name} from {order.supplier_name}",
                    debit=order.total_cost,
                    credit=Decimal("0"),
                    currency=order.currency,
                    external_reference=order.external_reference,
                ),
                AssetAccountingExportRow(
                    row_type="supplier_accounts_payable",
                    source_id=order.id,
                    source_label=label,
                    account_code=asset_account_code(system, "accounts_payable"),
                    memo=f"Supplier payable for {order.item_name}",
                    debit=Decimal("0"),
                    credit=order.total_cost,
                    currency=order.currency,
                    external_reference=order.external_reference,
                ),
            ]
        )
    payment_count = 0
    for schedule_read in lease_schedule_reads:
        rows.extend(
            [
                AssetAccountingExportRow(
                    row_type="lease_receivable",
                    source_id=schedule_read.id,
                    source_label=schedule_read.invoice.title,
                    account_code=asset_account_code(system, "lease_receivable"),
                    memo=f"{schedule_read.term_months}-month equipment lease receivable",
                    debit=schedule_read.total_amount,
                    credit=Decimal("0"),
                    currency=schedule_read.currency,
                    external_reference=schedule_read.invoice.invoice_number,
                ),
                AssetAccountingExportRow(
                    row_type="lease_revenue",
                    source_id=schedule_read.id,
                    source_label=schedule_read.invoice.title,
                    account_code=asset_account_code(system, "lease_revenue"),
                    memo=f"Equipment lease revenue for {schedule_read.invoice.title}",
                    debit=Decimal("0"),
                    credit=schedule_read.total_amount,
                    currency=schedule_read.currency,
                    external_reference=schedule_read.invoice.invoice_number,
                ),
            ]
        )
        payments = await db.scalars(
            select(FinancePayment)
            .where(FinancePayment.invoice_id == schedule_read.finance_invoice_id)
            .order_by(FinancePayment.received_at.asc())
        )
        for payment in payments.all():
            payment_count += 1
            rows.extend(
                [
                    AssetAccountingExportRow(
                        row_type="lease_cash_receipt",
                        source_id=payment.id,
                        source_label=schedule_read.invoice.title,
                        account_code=asset_account_code(system, "cash"),
                        memo=payment.notes or f"Lease payment for {schedule_read.invoice.invoice_number}",
                        debit=payment.amount,
                        credit=Decimal("0"),
                        currency=payment.currency,
                        external_reference=payment.external_reference,
                    ),
                    AssetAccountingExportRow(
                        row_type="lease_receivable_reduction",
                        source_id=payment.id,
                        source_label=schedule_read.invoice.title,
                        account_code=asset_account_code(system, "lease_receivable"),
                        memo=f"Receivable reduction for {schedule_read.invoice.invoice_number}",
                        debit=Decimal("0"),
                        credit=payment.amount,
                        currency=payment.currency,
                        external_reference=payment.external_reference,
                    ),
                ]
            )
    debit_total = sum((row.debit for row in rows), Decimal("0")).quantize(Decimal("0.01"))
    credit_total = sum((row.credit for row in rows), Decimal("0")).quantize(Decimal("0.01"))
    return AssetAccountingExportRead(
        organization_id=organization_id,
        basis=basis,
        system=system,
        rows=rows,
        debit_total=debit_total,
        credit_total=credit_total,
        supplier_order_count=len(supplier_orders),
        lease_schedule_count=len(lease_schedule_reads),
        payment_count=payment_count,
    )


async def sync_asset_accounting_export(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    system: str,
    basis: str,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> AssetAccountingSyncRead:
    await ensure_manage_assets(authz, identity, organization_id)
    export = await asset_accounting_export(db, organization_id, system, basis)
    selected_settings = settings or get_settings()
    synced_at = datetime.now(UTC)
    sync_reference = asset_accounting_sync_reference(export)
    webhook_configured = bool(selected_settings.asset_accounting_webhook_url)
    if selected_settings.asset_accounting_sync_mode != "webhook" or not webhook_configured:
        return AssetAccountingSyncRead(
            organization_id=organization_id,
            basis=basis,
            system=system,
            mode=selected_settings.asset_accounting_sync_mode,
            delivered=False,
            row_count=len(export.rows),
            debit_total=export.debit_total,
            credit_total=export.credit_total,
            sync_reference=sync_reference,
            failure_reason=None if webhook_configured else "Asset accounting webhook URL is not configured.",
            webhook_configured=webhook_configured,
            synced_at=synced_at,
        )

    payload = asset_accounting_sync_payload(export, sync_reference, synced_at)
    raw_body = json.dumps(payload, sort_keys=True, default=str).encode()
    timestamp = str(int(time.time()))
    headers = await asset_accounting_sync_headers(selected_settings, raw_body, timestamp)
    provider_status_code: int | None = None
    failure_reason: str | None = None
    delivered = False
    try:
        async with httpx.AsyncClient(timeout=selected_settings.asset_accounting_timeout_seconds) as client:
            response = await client.post(
                selected_settings.asset_accounting_webhook_url,
                json=payload,
                headers=headers,
            )
        provider_status_code = response.status_code
        delivered = 200 <= response.status_code < 300
        if not delivered:
            failure_reason = f"Asset accounting webhook returned {response.status_code}: {response.text[:500]}"
    except httpx.HTTPError as error:
        failure_reason = f"Asset accounting webhook failed: {error}"

    return AssetAccountingSyncRead(
        organization_id=organization_id,
        basis=basis,
        system=system,
        mode=selected_settings.asset_accounting_sync_mode,
        delivered=delivered,
        row_count=len(export.rows),
        debit_total=export.debit_total,
        credit_total=export.credit_total,
        sync_reference=sync_reference,
        provider_status_code=provider_status_code,
        failure_reason=failure_reason,
        webhook_configured=webhook_configured,
        synced_at=synced_at,
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


async def get_equipment_reader_by_reader_id(
    db: AsyncSession,
    organization_id: UUID,
    reader_id: str,
) -> EquipmentReader:
    reader = await db.scalar(
        select(EquipmentReader).where(
            EquipmentReader.organization_id == organization_id,
            EquipmentReader.reader_id == reader_id,
        )
    )
    if reader is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reader not found")
    return reader


async def get_lease_schedule(db: AsyncSession, lease_schedule_id: UUID) -> EquipmentLeaseSchedule:
    schedule = await db.get(EquipmentLeaseSchedule, lease_schedule_id)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease schedule not found")
    return schedule


async def list_lease_installments(
    db: AsyncSession,
    lease_schedule_id: UUID,
) -> list[EquipmentLeaseInstallment]:
    return list(
        (
            await db.scalars(
                select(EquipmentLeaseInstallment)
                .where(EquipmentLeaseInstallment.lease_schedule_id == lease_schedule_id)
                .order_by(EquipmentLeaseInstallment.sequence_number)
            )
        ).all()
    )


async def match_equipment_code(
    db: AsyncSession,
    organization_id: UUID,
    code: str,
) -> tuple[EquipmentItem | None, str | None]:
    item = await db.scalar(
        select(EquipmentItem)
        .where(EquipmentItem.organization_id == organization_id)
        .where((EquipmentItem.tag_code == code) | (EquipmentItem.serial_number == code))
    )
    if item is None:
        return None, None
    return item, "tag_code" if item.tag_code == code else "serial_number"


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


def equipment_scan_event_read(event: EquipmentScanEvent) -> EquipmentScanEventRead:
    return EquipmentScanEventRead(
        id=event.id,
        organization_id=event.organization_id,
        equipment_item_id=event.equipment_item_id,
        scanned_code=event.scanned_code,
        match_type=event.match_type,
        item_name=event.item_name,
        reader_id=event.reader_id,
        reader_location=event.reader_location,
        source=event.source,
        movement=event.movement,
        matched=event.matched,
        scanned_at=event.scanned_at,
        external_reference=event.external_reference,
        notes=event.notes,
    )


def equipment_reader_read(reader: EquipmentReader) -> EquipmentReaderRead:
    return EquipmentReaderRead(
        id=reader.id,
        organization_id=reader.organization_id,
        reader_id=reader.reader_id,
        name=reader.name,
        location=reader.location,
        status=reader.status,
        last_seen_at=reader.last_seen_at,
        last_scan_at=reader.last_scan_at,
        notes=reader.notes,
    )


def supplier_order_read(order: SupplierOrder) -> SupplierOrderRead:
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


def finance_invoice_read(invoice: FinanceInvoice) -> FinanceInvoiceRead:
    return FinanceInvoiceRead(
        id=invoice.id,
        organization_id=invoice.organization_id,
        person_id=invoice.person_id,
        team_id=invoice.team_id,
        sponsor_id=invoice.sponsor_id,
        invoice_number=invoice.invoice_number,
        title=invoice.title,
        amount_due=invoice.amount_due,
        amount_paid=invoice.amount_paid,
        currency=invoice.currency,
        due_on=invoice.due_on,
        status=invoice.status,
        memo=invoice.memo,
    )


def finance_payment_read(payment: FinancePayment) -> FinancePaymentRead:
    return FinancePaymentRead(
        id=payment.id,
        organization_id=payment.organization_id,
        invoice_id=payment.invoice_id,
        amount=payment.amount,
        currency=payment.currency,
        method=payment.method,
        external_reference=payment.external_reference,
        received_at=payment.received_at,
        notes=payment.notes,
    )


def equipment_lease_schedule_read(
    schedule: EquipmentLeaseSchedule,
    invoice: FinanceInvoice,
    installments: list[EquipmentLeaseInstallment],
) -> EquipmentLeaseScheduleRead:
    return EquipmentLeaseScheduleRead(
        id=schedule.id,
        organization_id=schedule.organization_id,
        equipment_item_id=schedule.equipment_item_id,
        finance_invoice_id=schedule.finance_invoice_id,
        person_id=schedule.person_id,
        team_id=schedule.team_id,
        quantity=schedule.quantity,
        term_months=schedule.term_months,
        monthly_amount=schedule.monthly_amount,
        total_amount=schedule.total_amount,
        currency=schedule.currency,
        starts_on=schedule.starts_on,
        status=schedule.status,
        notes=schedule.notes,
        invoice=finance_invoice_read(invoice),
        installments=[equipment_lease_installment_read(item) for item in installments],
    )


def equipment_lease_installment_read(installment: EquipmentLeaseInstallment) -> EquipmentLeaseInstallmentRead:
    return EquipmentLeaseInstallmentRead(
        id=installment.id,
        organization_id=installment.organization_id,
        lease_schedule_id=installment.lease_schedule_id,
        sequence_number=installment.sequence_number,
        due_on=installment.due_on,
        amount=installment.amount,
        amount_paid=installment.amount_paid,
        currency=installment.currency,
        status=installment.status,
        paid_at=installment.paid_at,
    )


def decode_upload_content(content_base64: str) -> bytes:
    encoded = content_base64.split(",", 1)[1] if "," in content_base64 else content_base64
    try:
        return b64decode(encoded, validate=True)
    except (Base64Error, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid file encoding") from exc


def safe_upload_filename(filename: str) -> str:
    cleaned = sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip(".-")
    return cleaned[:180] or "equipment-file"


def equipment_file_object_key(file_record: EquipmentFile, settings: Settings) -> str:
    if file_record.storage_path.startswith("s3://"):
        prefix = f"s3://{settings.object_storage_bucket}/"
        if file_record.storage_path.startswith(prefix):
            return file_record.storage_path[len(prefix):]
        return file_record.storage_path.split("/", 3)[-1]
    path = Path(file_record.storage_path)
    try:
        return path.relative_to(Path(settings.equipment_file_dir)).as_posix()
    except ValueError:
        return (
            Path(str(file_record.organization_id))
            / str(file_record.equipment_item_id)
            / path.name
        ).as_posix()


def hash_reader_key(api_key: str) -> str:
    return sha256(api_key.encode("utf-8")).hexdigest()


def build_lease_installments(
    schedule: EquipmentLeaseSchedule,
    starts_on: date,
) -> list[EquipmentLeaseInstallment]:
    installments = []
    for index in range(schedule.term_months):
        is_final = index == schedule.term_months - 1
        prior_total = schedule.monthly_amount * index
        amount = (schedule.total_amount - prior_total).quantize(Decimal("0.01")) if is_final else schedule.monthly_amount
        installments.append(
            EquipmentLeaseInstallment(
                organization_id=schedule.organization_id,
                lease_schedule_id=schedule.id,
                sequence_number=index + 1,
                due_on=add_months(starts_on, index),
                amount=amount,
                amount_paid=Decimal("0"),
                currency=schedule.currency,
                status="scheduled",
            )
        )
    return installments


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def supplier_recommendation(score: int) -> str:
    if score >= 85:
        return "Preferred supplier for renewals and urgent work."
    if score >= 65:
        return "Usable supplier; monitor cost and completion variance."
    return "Review supplier before assigning critical work."


def supplier_order_payload(order: SupplierOrder, submitted_at: datetime, adapter_profile: str = "generic") -> dict:
    base_payload = {
        "event_type": "assets.supplier_order",
        "adapter_profile": adapter_profile,
        "order_id": str(order.id),
        "organization_id": str(order.organization_id),
        "equipment_item_id": str(order.equipment_item_id) if order.equipment_item_id else None,
        "supplier_name": order.supplier_name,
        "item_name": order.item_name,
        "quantity": order.quantity,
        "unit_cost": str(order.unit_cost),
        "total_cost": str(order.total_cost),
        "currency": order.currency,
        "external_reference": order.external_reference,
        "ordered_at": order.ordered_at.isoformat() if order.ordered_at else None,
        "expected_delivery_at": order.expected_delivery_at.isoformat() if order.expected_delivery_at else None,
        "submitted_at": submitted_at.isoformat(),
        "notes": order.notes,
    }
    if adapter_profile == "teamwear":
        base_payload["teamwear_purchase_order"] = {
            "purchase_order_number": order.external_reference or f"AFROLETE-{str(order.id)[:8]}",
            "supplier": order.supplier_name,
            "requested_delivery_at": order.expected_delivery_at.isoformat() if order.expected_delivery_at else None,
            "lines": [
                {
                    "product_name": order.item_name,
                    "category": "team_equipment",
                    "quantity": order.quantity,
                    "unit_price": str(order.unit_cost),
                    "line_total": str(order.total_cost),
                    "currency": order.currency,
                }
            ],
            "delivery_instructions": order.notes,
        }
    elif adapter_profile == "decathlon_club":
        base_payload["decathlon_club_cart"] = {
            "customer_reference": order.external_reference or str(order.id),
            "currency": order.currency,
            "items": [
                {
                    "sku_or_description": order.item_name,
                    "quantity": order.quantity,
                    "expected_unit_price": str(order.unit_cost),
                    "sport_use": "club_equipment",
                }
            ],
            "requested_fulfillment": {
                "expected_delivery_at": order.expected_delivery_at.isoformat() if order.expected_delivery_at else None,
                "allow_substitutions": True,
            },
        }
    elif adapter_profile == "local_sports_vendor":
        base_payload["vendor_order_request"] = {
            "reference": order.external_reference or f"LOCAL-{str(order.id)[:8]}",
            "vendor_name": order.supplier_name,
            "description": f"{order.quantity} x {order.item_name}",
            "max_authorized_total": str(order.total_cost),
            "currency": order.currency,
            "delivery_deadline": order.expected_delivery_at.isoformat() if order.expected_delivery_at else None,
        }
    return base_payload


def supplier_invoice_sync_payload(order: SupplierOrder, synced_at: datetime, adapter_profile: str = "generic") -> dict:
    base_payload = {
        "event_type": "assets.supplier_invoice",
        "adapter_profile": adapter_profile,
        "order_id": str(order.id),
        "organization_id": str(order.organization_id),
        "equipment_item_id": str(order.equipment_item_id) if order.equipment_item_id else None,
        "supplier_name": order.supplier_name,
        "item_name": order.item_name,
        "quantity": order.quantity,
        "unit_cost": str(order.unit_cost),
        "invoice_total": str(order.total_cost),
        "currency": order.currency,
        "external_reference": order.external_reference,
        "ordered_at": order.ordered_at.isoformat() if order.ordered_at else None,
        "received_at": order.received_at.isoformat() if order.received_at else None,
        "synced_at": synced_at.isoformat(),
        "notes": order.notes,
    }
    if adapter_profile == "quickbooks_bill":
        base_payload["quickbooks_bill"] = {
            "vendor_ref": order.supplier_name,
            "doc_number": order.external_reference or f"BILL-{str(order.id)[:8]}",
            "currency_ref": order.currency,
            "line": [
                {
                    "description": order.item_name,
                    "amount": str(order.total_cost),
                    "detail_type": "AccountBasedExpenseLineDetail",
                    "account_ref": "1500:equipment-assets",
                    "quantity": order.quantity,
                    "unit_price": str(order.unit_cost),
                }
            ],
        }
    elif adapter_profile == "xero_bill":
        base_payload["xero_bill"] = {
            "contact": {"name": order.supplier_name},
            "type": "ACCPAY",
            "reference": order.external_reference or str(order.id),
            "currency_code": order.currency,
            "line_items": [
                {
                    "description": order.item_name,
                    "quantity": order.quantity,
                    "unit_amount": str(order.unit_cost),
                    "account_code": "1500",
                    "line_amount": str(order.total_cost),
                }
            ],
        }
    elif adapter_profile == "sage_bill":
        base_payload["sage_bill"] = {
            "supplier": order.supplier_name,
            "reference": order.external_reference or str(order.id),
            "currency": order.currency,
            "nominal_code": "1500",
            "net_amount": str(order.total_cost),
            "description": order.item_name,
        }
    return base_payload


def supplier_order_adapter_profile(settings: Settings, order: SupplierOrder) -> str:
    configured = settings.supplier_order_adapter_profile
    if configured != "auto":
        return configured
    haystack = f"{order.supplier_name} {order.item_name}".lower()
    if "decathlon" in haystack:
        return "decathlon_club"
    if any(term in haystack for term in ["kit", "jersey", "uniform", "teamwear"]):
        return "teamwear"
    return "local_sports_vendor"


def supplier_invoice_adapter_profile(settings: Settings, order: SupplierOrder) -> str:
    configured = settings.supplier_invoice_adapter_profile
    if configured != "auto":
        return configured
    destination = settings.supplier_invoice_webhook_url.lower()
    if "quickbooks" in destination or "intuit" in destination:
        return "quickbooks_bill"
    if "xero" in destination:
        return "xero_bill"
    if "sage" in destination:
        return "sage_bill"
    if "quickbooks" in order.supplier_name.lower():
        return "quickbooks_bill"
    return "generic"


async def supplier_order_headers(settings: Settings) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    key = await resolve_supplier_secret(
        settings,
        env_value=settings.supplier_order_webhook_key,
        path=settings.supplier_order_webhook_key_secret_path,
        field_name=settings.supplier_order_webhook_key_secret_field,
        label="supplier order webhook key",
    )
    if key:
        headers["X-Afrolete-Supplier-Key"] = key
    return headers


async def supplier_invoice_headers(settings: Settings) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    key = await resolve_supplier_secret(
        settings,
        env_value=settings.supplier_invoice_webhook_key,
        path=settings.supplier_invoice_webhook_key_secret_path,
        field_name=settings.supplier_invoice_webhook_key_secret_field,
        label="supplier invoice webhook key",
    )
    if key:
        headers["X-Afrolete-Supplier-Invoice-Key"] = key
    return headers


def asset_account_code(system: str, key: str) -> str:
    normalized_system = system.strip().lower()
    if normalized_system in {"quickbooks", "xero", "sage", "odoo"}:
        return {
            "equipment_asset": "1500:equipment-assets",
            "accounts_payable": "2100:accounts-payable",
            "lease_receivable": "1210:equipment-lease-receivable",
            "lease_revenue": "4310:equipment-lease-income",
            "cash": "1000:cash",
        }[key]
    return {
        "equipment_asset": "ASSET:EQUIPMENT",
        "accounts_payable": "LIABILITY:ACCOUNTS_PAYABLE",
        "lease_receivable": "ASSET:LEASE_RECEIVABLE",
        "lease_revenue": "REVENUE:EQUIPMENT_LEASE",
        "cash": "ASSET:CASH",
    }[key]


def asset_accounting_sync_reference(export: AssetAccountingExportRead) -> str:
    payload = asset_accounting_sync_payload(export, sync_reference=None, synced_at=None)
    digest = sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    return f"asset_acct_{export.system}_{export.basis}_{digest[:16]}"


def asset_accounting_sync_payload(
    export: AssetAccountingExportRead,
    sync_reference: str | None,
    synced_at: datetime | None,
) -> dict:
    return {
        "event_type": "assets.accounting_export",
        "organization_id": str(export.organization_id),
        "system": export.system,
        "basis": export.basis,
        "sync_reference": sync_reference,
        "synced_at": synced_at.isoformat() if synced_at else None,
        "row_count": len(export.rows),
        "supplier_order_count": export.supplier_order_count,
        "lease_schedule_count": export.lease_schedule_count,
        "payment_count": export.payment_count,
        "debit_total": str(export.debit_total),
        "credit_total": str(export.credit_total),
        "rows": [
            {
                "row_type": row.row_type,
                "source_id": str(row.source_id),
                "source_label": row.source_label,
                "account_code": row.account_code,
                "memo": row.memo,
                "debit": str(row.debit),
                "credit": str(row.credit),
                "currency": row.currency,
                "external_reference": row.external_reference,
            }
            for row in export.rows
        ],
    }


async def asset_accounting_sync_headers(
    settings: Settings,
    raw_body: bytes,
    timestamp: str,
) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "X-Afrolete-Asset-Accounting-Timestamp": timestamp,
    }
    key = await resolve_supplier_secret(
        settings,
        env_value=settings.asset_accounting_webhook_key,
        path=settings.asset_accounting_webhook_key_secret_path,
        field_name=settings.asset_accounting_webhook_key_secret_field,
        label="asset accounting webhook key",
    )
    if key:
        headers["X-Afrolete-Asset-Accounting-Key"] = key
        headers["X-Afrolete-Asset-Accounting-Signature"] = "sha256=" + hmac.new(
            key.encode(),
            timestamp.encode() + b"." + raw_body,
            sha256,
        ).hexdigest()
    return headers


async def resolve_supplier_secret(
    settings: Settings,
    *,
    env_value: str,
    path: str,
    field_name: str,
    label: str,
) -> str:
    return await resolve_secret(
        settings,
        env_value=env_value,
        path=path,
        field_name=field_name,
        label=label,
    )


def supplier_order_submission_notes(notes: str | None, result: dict) -> str:
    status_label = "delivered" if result["delivered"] else "prepared"
    if result["failure_reason"]:
        status_label = f"{status_label}: {result['failure_reason']}"
    line = f"Supplier submission {status_label} at {result['submitted_at'].isoformat()}."
    return f"{notes}\n{line}" if notes else line


def supplier_invoice_sync_notes(notes: str | None, result: dict) -> str:
    status_label = "synced" if result["synced"] else "prepared"
    if result["failure_reason"]:
        status_label = f"{status_label}: {result['failure_reason']}"
    line = f"Supplier invoice {status_label} at {result['synced_at'].isoformat()}."
    return f"{notes}\n{line}" if notes else line


def is_before_now(value: datetime, now: datetime) -> bool:
    comparable_now = now.replace(tzinfo=None) if value.tzinfo is None else now
    return value < comparable_now
