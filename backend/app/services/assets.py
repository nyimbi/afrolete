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
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assets import (
    ClubhouseAmenity,
    ClubhouseAmenityReservation,
    ClubhouseVisit,
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
    FacilityAccessCommand,
    FacilityAccessCredential,
    FacilityAccessDevice,
    FacilityAccessEvent,
    FacilityAccessLockdown,
    FacilityBooking,
    FacilityBookingRule,
    FacilityBookingWaitlistEntry,
    FacilityLeaseAgreement,
    FacilityMaintenanceSchedule,
    FacilityUtilityAlert,
    FacilityUtilityMeter,
    FacilityUtilityReading,
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
    WorkOrderPriority,
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
    ClubhouseAmenityCreate,
    ClubhouseAmenityRead,
    ClubhouseAmenityReservationCreate,
    ClubhouseAmenityReservationRead,
    ClubhouseAmenityReservationUpdate,
    ClubhouseDashboardRead,
    ClubhouseVisitCreate,
    ClubhouseVisitRead,
    ClubhouseVisitUpdate,
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
    FacilityAvailabilityRead,
    FacilityAvailabilitySlotRead,
    FacilityBookingCheckoutRead,
    FacilityBookingCreate,
    FacilityBookingRuleCreate,
    FacilityBookingStatusUpdate,
    FacilityBookingWaitlistConversionCreate,
    FacilityBookingWaitlistCreate,
    FacilityBookingWaitlistRead,
    FacilityBookingWaitlistUpdate,
    FacilityCreate,
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
    FacilityHireCheckoutSettlementCreate,
    FacilityHireCheckoutSettlementRead,
    FacilityHireHostedCheckoutRead,
    FacilityLeaseAgreementCreate,
    FacilityLeaseAgreementRead,
    FacilityLeaseAgreementUpdate,
    FacilityLeaseInvoiceCreate,
    FacilityLeaseInvoiceRead,
    FacilityMaintenanceCostRead,
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
    FacilityUtilityReadingRead,
    FacilityUtilityReadingResultRead,
    FacilityPublicBookingCreate,
    FacilityPublicListingRead,
    FacilityRecurringBookingCreate,
    FacilityUtilizationRead,
    MaintenanceWorkOrderCreate,
    MaintenanceWorkOrderRead,
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
from app.services.organizations import get_public_site_organization
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


async def upsert_facility_booking_rule(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FacilityBookingRuleCreate,
    authz: AuthorizationService,
) -> FacilityBookingRule:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    rule = await db.scalar(
        select(FacilityBookingRule)
        .where(FacilityBookingRule.organization_id == payload.organization_id)
        .where(FacilityBookingRule.facility_id == payload.facility_id)
    )
    if rule is None:
        rule = FacilityBookingRule(organization_id=payload.organization_id, facility_id=payload.facility_id)
        db.add(rule)
    rule.min_booking_minutes = payload.min_booking_minutes
    rule.max_booking_minutes = payload.max_booking_minutes
    rule.buffer_minutes = payload.buffer_minutes
    rule.advance_booking_days = payload.advance_booking_days
    rule.requires_approval = payload.requires_approval
    rule.allow_public_booking = payload.allow_public_booking
    rule.cancellation_notice_hours = payload.cancellation_notice_hours
    rule.peak_hour_rate_multiplier = payload.peak_hour_rate_multiplier
    rule.public_booking_note = payload.public_booking_note
    rule.status = payload.status.strip().lower()
    await db.commit()
    await db.refresh(rule)
    return rule


async def get_facility_booking_rule(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID,
) -> FacilityBookingRule | None:
    await get_facility_for_organization(db, facility_id, organization_id)
    return await db.scalar(
        select(FacilityBookingRule)
        .where(FacilityBookingRule.organization_id == organization_id)
        .where(FacilityBookingRule.facility_id == facility_id)
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


async def create_facility_maintenance_schedule(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FacilityMaintenanceScheduleCreate,
    authz: AuthorizationService,
) -> FacilityMaintenanceScheduleRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    if payload.equipment_item_id is not None:
        await get_equipment_for_organization(db, payload.equipment_item_id, payload.organization_id)
    if payload.assigned_to_person_id is not None:
        await get_person_member_for_organization(db, payload.assigned_to_person_id, payload.organization_id)

    schedule = FacilityMaintenanceSchedule(
        status="active",
        **payload.model_dump(),
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return facility_maintenance_schedule_read(schedule)


async def list_facility_maintenance_schedules(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
    status_filter: str | None = None,
) -> list[FacilityMaintenanceScheduleRead]:
    await get_organization(db, organization_id)
    statement = select(FacilityMaintenanceSchedule).where(
        FacilityMaintenanceSchedule.organization_id == organization_id
    )
    if facility_id is not None:
        statement = statement.where(FacilityMaintenanceSchedule.facility_id == facility_id)
    if status_filter is not None:
        statement = statement.where(FacilityMaintenanceSchedule.status == status_filter)
    rows = list(
        (
            await db.scalars(
                statement.order_by(
                    FacilityMaintenanceSchedule.next_due_at.asc(),
                    FacilityMaintenanceSchedule.title.asc(),
                )
            )
        ).all()
    )
    return [facility_maintenance_schedule_read(row) for row in rows]


async def update_facility_maintenance_schedule(
    db: AsyncSession,
    identity: CurrentIdentity,
    schedule_id: UUID,
    payload: FacilityMaintenanceScheduleUpdate,
    authz: AuthorizationService,
) -> FacilityMaintenanceScheduleRead:
    schedule = await get_facility_maintenance_schedule(db, schedule_id)
    await ensure_manage_assets(authz, identity, schedule.organization_id)
    for field in ["status", "next_due_at", "interval_days", "estimated_cost", "notes"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(schedule, field, value)
    await db.commit()
    await db.refresh(schedule)
    return facility_maintenance_schedule_read(schedule)


async def generate_facility_maintenance_work_order(
    db: AsyncSession,
    identity: CurrentIdentity,
    schedule_id: UUID,
    authz: AuthorizationService,
) -> FacilityMaintenanceScheduleRunRead:
    schedule = await get_facility_maintenance_schedule(db, schedule_id)
    await ensure_manage_assets(authz, identity, schedule.organization_id)
    if schedule.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Maintenance schedule is not active")
    due_at = schedule.next_due_at
    work_order = MaintenanceWorkOrder(
        organization_id=schedule.organization_id,
        facility_maintenance_schedule_id=schedule.id,
        facility_id=schedule.facility_id,
        equipment_item_id=schedule.equipment_item_id,
        assigned_to_person_id=schedule.assigned_to_person_id,
        title=schedule.title,
        priority=WorkOrderPriority.HIGH if schedule.safety_related else WorkOrderPriority.MEDIUM,
        due_at=due_at,
        vendor=schedule.vendor,
        estimated_cost=schedule.estimated_cost,
        safety_related=schedule.safety_related,
        compliance_reference=schedule.compliance_reference,
        notes=maintenance_work_order_notes(schedule),
    )
    db.add(work_order)
    now = datetime.now(UTC)
    schedule.last_generated_at = now
    schedule.next_due_at = advance_schedule_due_at(schedule.next_due_at, schedule.interval_days)
    await db.commit()
    await db.refresh(work_order)
    await db.refresh(schedule)
    return FacilityMaintenanceScheduleRunRead(
        schedule=facility_maintenance_schedule_read(schedule),
        work_order=maintenance_work_order_read(work_order),
        next_due_at=schedule.next_due_at,
    )


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
        if work_order.facility_maintenance_schedule_id is not None:
            schedule = await db.get(FacilityMaintenanceSchedule, work_order.facility_maintenance_schedule_id)
            if schedule is not None:
                schedule.last_completed_at = work_order.completed_at
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


async def facility_maintenance_dashboard(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
) -> FacilityMaintenanceDashboardRead:
    await get_organization(db, organization_id)
    now = datetime.now(UTC)
    soon = now + timedelta(days=14)
    schedule_statement = select(FacilityMaintenanceSchedule).where(
        FacilityMaintenanceSchedule.organization_id == organization_id,
        FacilityMaintenanceSchedule.status == "active",
    )
    work_order_statement = select(MaintenanceWorkOrder).where(MaintenanceWorkOrder.organization_id == organization_id)
    facility_statement = select(Facility).where(Facility.organization_id == organization_id)
    if facility_id is not None:
        schedule_statement = schedule_statement.where(FacilityMaintenanceSchedule.facility_id == facility_id)
        work_order_statement = work_order_statement.where(MaintenanceWorkOrder.facility_id == facility_id)
        facility_statement = facility_statement.where(Facility.id == facility_id)

    schedules = list((await db.scalars(schedule_statement)).all())
    work_orders = list((await db.scalars(work_order_statement)).all())
    facilities = list((await db.scalars(facility_statement)).all())

    upcoming = sorted(
        [schedule for schedule in schedules if normalize_datetime(schedule.next_due_at) <= soon],
        key=lambda item: item.next_due_at,
    )[:8]
    recent = sorted(
        [order for order in work_orders if order.completed_at is not None],
        key=lambda item: item.completed_at or item.updated_at,
        reverse=True,
    )[:8]
    year_start = datetime(now.year, 1, 1, tzinfo=UTC)
    cost_orders = [order for order in work_orders if normalize_datetime(order.created_at) >= year_start]
    actual_cost = sum((order.actual_cost or Decimal("0") for order in cost_orders), Decimal("0")).quantize(Decimal("0.01"))
    estimated_open = sum(
        (
            order.estimated_cost or Decimal("0")
            for order in work_orders
            if order.status != WorkOrderStatus.COMPLETED
        ),
        Decimal("0"),
    ).quantize(Decimal("0.01"))
    total_budget = sum((facility.maintenance_budget or Decimal("0") for facility in facilities), Decimal("0")).quantize(Decimal("0.01"))
    budget_remaining = (total_budget - actual_cost).quantize(Decimal("0.01")) if total_budget > 0 else None
    cost_by_facility = facility_maintenance_costs(facilities, work_orders)
    overdue_count = len([schedule for schedule in schedules if normalize_datetime(schedule.next_due_at) < now])
    safety_due_count = len([schedule for schedule in upcoming if schedule.safety_related])
    return FacilityMaintenanceDashboardRead(
        organization_id=organization_id,
        due_count=len(upcoming),
        overdue_count=overdue_count,
        safety_due_count=safety_due_count,
        maintenance_cost_ytd=actual_cost,
        estimated_open_cost=estimated_open,
        budget_remaining=budget_remaining,
        upcoming_schedules=[facility_maintenance_schedule_read(schedule) for schedule in upcoming],
        recent_work_orders=[maintenance_work_order_read(order) for order in recent],
        cost_by_facility=cost_by_facility,
        recommendation=facility_maintenance_recommendation(overdue_count, safety_due_count, budget_remaining),
    )


async def create_facility_lease_agreement(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FacilityLeaseAgreementCreate,
    authz: AuthorizationService,
) -> FacilityLeaseAgreementRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    lease = FacilityLeaseAgreement(
        status="active" if payload.compliance_status == "compliant" else "draft",
        **payload.model_dump(),
    )
    lease.next_invoice_on = lease.next_invoice_on or lease.starts_on
    db.add(lease)
    await db.commit()
    await db.refresh(lease)
    return facility_lease_agreement_read(lease)


async def list_facility_lease_agreements(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
    status_filter: str | None = None,
) -> list[FacilityLeaseAgreementRead]:
    await get_organization(db, organization_id)
    statement = select(FacilityLeaseAgreement).where(FacilityLeaseAgreement.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(FacilityLeaseAgreement.facility_id == facility_id)
    if status_filter is not None:
        statement = statement.where(FacilityLeaseAgreement.status == status_filter)
    rows = list(
        (
            await db.scalars(
                statement.order_by(
                    FacilityLeaseAgreement.status.asc(),
                    FacilityLeaseAgreement.next_invoice_on.asc(),
                    FacilityLeaseAgreement.lessee_name.asc(),
                )
            )
        ).all()
    )
    return [facility_lease_agreement_read(row) for row in rows]


async def update_facility_lease_agreement(
    db: AsyncSession,
    identity: CurrentIdentity,
    lease_id: UUID,
    payload: FacilityLeaseAgreementUpdate,
    authz: AuthorizationService,
) -> FacilityLeaseAgreementRead:
    lease = await get_facility_lease_agreement(db, lease_id)
    await ensure_manage_assets(authz, identity, lease.organization_id)
    for field in [
        "status",
        "deposit_status",
        "compliance_status",
        "next_invoice_on",
        "renewal_notice_on",
        "signed_at",
        "terminated_at",
        "document_url",
        "compliance_notes",
        "notes",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(lease, field, value)
    if payload.status == "active" and lease.signed_at is None:
        lease.signed_at = datetime.now(UTC)
    if payload.status == "terminated" and lease.terminated_at is None:
        lease.terminated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(lease)
    return facility_lease_agreement_read(lease)


async def generate_facility_lease_invoice(
    db: AsyncSession,
    identity: CurrentIdentity,
    lease_id: UUID,
    payload: FacilityLeaseInvoiceCreate,
    authz: AuthorizationService,
) -> FacilityLeaseInvoiceRead:
    lease = await get_facility_lease_agreement(db, lease_id)
    await ensure_manage_assets(authz, identity, lease.organization_id)
    if lease.status not in {"active", "invoicing", "draft"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Facility lease is not invoiceable")
    amount_due = (lease.monthly_rent + payload.extra_amount + payload.late_fee).quantize(Decimal("0.01"))
    invoice = FinanceInvoice(
        organization_id=lease.organization_id,
        invoice_number=facility_lease_invoice_number(lease, payload.period_start),
        title=f"Facility lease: {lease.lessee_name}",
        amount_due=amount_due,
        amount_paid=Decimal("0"),
        currency=payload.currency,
        due_on=payload.due_on or payload.period_start,
        status=CommercialStatus.DRAFT,
        memo=payload.memo or facility_lease_invoice_memo(lease, payload),
    )
    db.add(invoice)
    await db.flush()
    lease.finance_invoice_id = invoice.id
    lease.status = "invoicing"
    lease.next_invoice_on = add_month(payload.period_start)
    await db.commit()
    await db.refresh(invoice)
    await db.refresh(lease)
    return FacilityLeaseInvoiceRead(
        lease=facility_lease_agreement_read(lease),
        invoice=finance_invoice_read(invoice),
        period_label=f"{payload.period_start.isoformat()} to {payload.period_end.isoformat()}",
    )


async def create_facility_access_credential(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FacilityAccessCredentialCreate,
    authz: AuthorizationService,
) -> FacilityAccessCredentialRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    booking: FacilityBooking | None = None
    lease: FacilityLeaseAgreement | None = None
    if payload.booking_id is not None:
        booking = await get_facility_booking(db, payload.booking_id)
        if booking.organization_id != payload.organization_id or booking.facility_id != payload.facility_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility booking not found")
    if payload.lease_agreement_id is not None:
        lease = await get_facility_lease_agreement(db, payload.lease_agreement_id)
        if lease.organization_id != payload.organization_id or lease.facility_id != payload.facility_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility lease agreement not found")
    if payload.person_id is not None:
        await get_person_member_for_organization(db, payload.person_id, payload.organization_id)

    valid_from, valid_until = facility_access_window(payload, booking, lease)
    credential = FacilityAccessCredential(
        organization_id=payload.organization_id,
        facility_id=payload.facility_id,
        booking_id=payload.booking_id,
        lease_agreement_id=payload.lease_agreement_id,
        person_id=payload.person_id,
        guest_name=payload.guest_name,
        guest_email=payload.guest_email,
        credential_type=payload.credential_type,
        access_code=payload.access_code or f"ACCESS-{token_urlsafe(6).upper()}",
        access_level=payload.access_level,
        zones=payload.zones,
        valid_from=valid_from,
        valid_until=valid_until,
        max_uses=payload.max_uses,
        issued_by_person_id=identity.person_id,
        notes=payload.notes,
    )
    db.add(credential)
    await db.commit()
    await db.refresh(credential)
    return facility_access_credential_read(credential)


async def list_facility_access_credentials(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
    status_filter: str | None = None,
) -> list[FacilityAccessCredentialRead]:
    await get_organization(db, organization_id)
    statement = select(FacilityAccessCredential).where(FacilityAccessCredential.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(FacilityAccessCredential.facility_id == facility_id)
    if status_filter is not None:
        statement = statement.where(FacilityAccessCredential.status == status_filter)
    rows = list(
        (
            await db.scalars(
                statement.order_by(
                    FacilityAccessCredential.status.asc(),
                    FacilityAccessCredential.valid_until.asc(),
                )
            )
        ).all()
    )
    return [facility_access_credential_read(row) for row in rows]


async def update_facility_access_credential(
    db: AsyncSession,
    identity: CurrentIdentity,
    credential_id: UUID,
    payload: FacilityAccessCredentialUpdate,
    authz: AuthorizationService,
) -> FacilityAccessCredentialRead:
    credential = await get_facility_access_credential(db, credential_id)
    await ensure_manage_assets(authz, identity, credential.organization_id)
    credential.status = payload.status
    if payload.valid_until is not None:
        credential.valid_until = payload.valid_until
    if payload.notes:
        credential.notes = append_note(credential.notes, payload.notes)
    await db.commit()
    await db.refresh(credential)
    return facility_access_credential_read(credential)


async def record_facility_access_scan(
    db: AsyncSession,
    payload: FacilityAccessScanCreate,
) -> FacilityAccessEventRead:
    await get_organization(db, payload.organization_id)
    await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    occurred_at = payload.occurred_at or datetime.now(UTC)
    credential = await db.scalar(
        select(FacilityAccessCredential)
        .where(FacilityAccessCredential.organization_id == payload.organization_id)
        .where(FacilityAccessCredential.facility_id == payload.facility_id)
        .where(FacilityAccessCredential.access_code == payload.access_code)
        .order_by(FacilityAccessCredential.created_at.desc())
    )
    decision, reason = facility_access_decision(credential, occurred_at)
    if credential is not None and decision == "granted":
        credential.uses_count += 1
        credential.last_used_at = occurred_at
    event = FacilityAccessEvent(
        organization_id=payload.organization_id,
        facility_id=payload.facility_id,
        credential_id=credential.id if credential else None,
        booking_id=credential.booking_id if credential else None,
        lease_agreement_id=credential.lease_agreement_id if credential else None,
        access_code=payload.access_code,
        reader_id=payload.reader_id,
        reader_location=payload.reader_location,
        subject_summary=facility_access_subject(credential),
        decision=decision,
        reason=reason,
        occurred_at=occurred_at,
        notes=payload.notes,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return facility_access_event_read(event)


async def facility_access_dashboard(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
) -> FacilityAccessDashboardRead:
    await get_organization(db, organization_id)
    now = datetime.now(UTC)
    since = now - timedelta(hours=24)
    credential_statement = select(FacilityAccessCredential).where(
        FacilityAccessCredential.organization_id == organization_id
    )
    event_statement = select(FacilityAccessEvent).where(FacilityAccessEvent.organization_id == organization_id)
    if facility_id is not None:
        credential_statement = credential_statement.where(FacilityAccessCredential.facility_id == facility_id)
        event_statement = event_statement.where(FacilityAccessEvent.facility_id == facility_id)
    credentials = list((await db.scalars(credential_statement)).all())
    events = list((await db.scalars(event_statement.order_by(FacilityAccessEvent.occurred_at.desc()).limit(25))).all())
    recent_events = [event for event in events if normalize_datetime(event.occurred_at) >= since]
    active_credentials = [
        credential
        for credential in credentials
        if credential.status == "active"
        and normalize_datetime(credential.valid_from) <= now <= normalize_datetime(credential.valid_until)
    ]
    expiring = sorted(
        [
            credential
            for credential in active_credentials
            if normalize_datetime(credential.valid_until) <= now + timedelta(days=7)
        ],
        key=lambda item: item.valid_until,
    )[:8]
    denials = len([event for event in recent_events if event.decision == "denied"])
    grants = len([event for event in recent_events if event.decision == "granted"])
    return FacilityAccessDashboardRead(
        organization_id=organization_id,
        facility_id=facility_id,
        active_credentials=len(active_credentials),
        guest_credentials=len([credential for credential in active_credentials if credential.guest_name]),
        grants_last_24h=grants,
        denials_last_24h=denials,
        recent_events=[facility_access_event_read(event) for event in events[:10]],
        expiring_credentials=[facility_access_credential_read(credential) for credential in expiring],
        recommendation=facility_access_recommendation(denials, expiring),
    )


async def provision_facility_access_device(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FacilityAccessDeviceCreate,
    authz: AuthorizationService,
) -> FacilityAccessDeviceProvisionRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    device_id = payload.device_id.strip()
    existing = await db.scalar(
        select(FacilityAccessDevice).where(
            FacilityAccessDevice.organization_id == payload.organization_id,
            FacilityAccessDevice.device_id == device_id,
        )
    )
    api_key = payload.api_key or token_urlsafe(32)
    if existing is None:
        device = FacilityAccessDevice(
            organization_id=payload.organization_id,
            facility_id=payload.facility_id,
            device_id=device_id,
            name=payload.name,
            location=payload.location,
            device_type=payload.device_type.strip().lower(),
            unlock_method=payload.unlock_method.strip().lower(),
            status=payload.status.strip().lower(),
            api_key_hash=hash_reader_key(api_key),
            notes=payload.notes,
        )
        db.add(device)
    else:
        device = existing
        device.facility_id = payload.facility_id
        device.name = payload.name
        device.location = payload.location
        device.device_type = payload.device_type.strip().lower()
        device.unlock_method = payload.unlock_method.strip().lower()
        device.status = payload.status.strip().lower()
        device.api_key_hash = hash_reader_key(api_key)
        device.notes = payload.notes
    await db.commit()
    await db.refresh(device)
    return FacilityAccessDeviceProvisionRead(device=facility_access_device_read(device), api_key=api_key)


async def list_facility_access_devices(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    facility_id: UUID | None = None,
) -> list[FacilityAccessDeviceRead]:
    await ensure_manage_assets(authz, identity, organization_id)
    statement = select(FacilityAccessDevice).where(FacilityAccessDevice.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(FacilityAccessDevice.facility_id == facility_id)
    devices = await db.scalars(statement.order_by(FacilityAccessDevice.location, FacilityAccessDevice.name))
    return [facility_access_device_read(device) for device in devices.all()]


async def list_facility_access_commands(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    facility_id: UUID | None = None,
    device_id: UUID | None = None,
) -> list[FacilityAccessCommandRead]:
    await ensure_manage_assets(authz, identity, organization_id)
    statement = select(FacilityAccessCommand).where(FacilityAccessCommand.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(FacilityAccessCommand.facility_id == facility_id)
    if device_id is not None:
        statement = statement.where(FacilityAccessCommand.access_device_id == device_id)
    commands = await db.scalars(statement.order_by(FacilityAccessCommand.issued_at.desc()).limit(25))
    return [facility_access_command_read(command) for command in commands.all()]


async def record_gateway_facility_access_scan(
    db: AsyncSession,
    organization_id: UUID,
    device_id: str,
    api_key: str | None,
    payload: FacilityAccessGatewayScanCreate,
) -> FacilityAccessGatewayScanRead:
    device = await get_facility_access_device_by_device_id(db, organization_id, device_id.strip())
    validate_facility_access_device_key(device, api_key)
    occurred_at = payload.occurred_at or datetime.now(UTC)
    device.last_seen_at = occurred_at
    device.last_scan_at = occurred_at
    update_facility_access_device_health_fields(
        device,
        checked_at=occurred_at,
        battery_percent=payload.battery_percent,
        firmware_version=payload.firmware_version,
        network_status=payload.network_status,
    )
    credential = await db.scalar(
        select(FacilityAccessCredential)
        .where(FacilityAccessCredential.organization_id == organization_id)
        .where(FacilityAccessCredential.facility_id == device.facility_id)
        .where(FacilityAccessCredential.access_code == payload.access_code)
        .order_by(FacilityAccessCredential.created_at.desc())
    )
    decision, reason = facility_access_decision(credential, occurred_at)
    if credential is not None and decision == "granted":
        credential.uses_count += 1
        credential.last_used_at = occurred_at
    event = FacilityAccessEvent(
        organization_id=organization_id,
        facility_id=device.facility_id,
        credential_id=credential.id if credential else None,
        booking_id=credential.booking_id if credential else None,
        lease_agreement_id=credential.lease_agreement_id if credential else None,
        access_code=payload.access_code,
        reader_id=device.device_id,
        reader_location=device.location,
        subject_summary=facility_access_subject(credential),
        decision=decision,
        reason=reason,
        occurred_at=occurred_at,
        notes=append_note(payload.notes, f"external_reference={payload.external_reference}") if payload.external_reference else payload.notes,
    )
    db.add(event)
    await db.flush()
    command = facility_access_command_from_event(device, event, credential, api_key or "", occurred_at)
    db.add(command)
    await db.commit()
    await db.refresh(device)
    await db.refresh(event)
    await db.refresh(command)
    return FacilityAccessGatewayScanRead(
        device=facility_access_device_read(device),
        event=facility_access_event_read(event),
        command=facility_access_command_read(command),
        signature_validated=True,
    )


async def record_facility_access_device_health(
    db: AsyncSession,
    organization_id: UUID,
    device_id: str,
    api_key: str | None,
    payload: FacilityAccessDeviceHealthCreate,
) -> FacilityAccessDeviceHealthRead:
    device = await get_facility_access_device_by_device_id(db, organization_id, device_id.strip())
    validate_facility_access_device_key(device, api_key)
    checked_at = payload.checked_at or datetime.now(UTC)
    device.last_seen_at = checked_at
    device.last_health_at = checked_at
    if payload.status is not None:
        device.status = payload.status
    update_facility_access_device_health_fields(
        device,
        checked_at=checked_at,
        battery_percent=payload.battery_percent,
        firmware_version=payload.firmware_version,
        network_status=payload.network_status,
    )
    if payload.notes:
        device.notes = append_note(device.notes, payload.notes)
    await db.commit()
    await db.refresh(device)
    return FacilityAccessDeviceHealthRead(
        device=facility_access_device_read(device),
        signature_validated=True,
        recommendation=facility_access_device_health_recommendation(device),
    )


async def activate_facility_access_lockdown(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FacilityAccessLockdownCreate,
    authz: AuthorizationService,
) -> FacilityAccessLockdownResultRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    issued_at = datetime.now(UTC)
    devices = list(
        (
            await db.scalars(
                select(FacilityAccessDevice)
                .where(FacilityAccessDevice.organization_id == payload.organization_id)
                .where(FacilityAccessDevice.facility_id == payload.facility_id)
                .where(FacilityAccessDevice.status == "active")
                .order_by(FacilityAccessDevice.location, FacilityAccessDevice.name)
            )
        ).all()
    )
    if not devices:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No active facility access devices are provisioned for this facility",
        )
    lockdown = FacilityAccessLockdown(
        organization_id=payload.organization_id,
        facility_id=payload.facility_id,
        mode=payload.mode,
        status="active" if payload.mode == "lockdown" else "resolved",
        reason=payload.reason,
        command_count=len(devices),
        activated_at=issued_at,
        resolved_at=issued_at if payload.mode == "unlock_all" else None,
        issued_by_person_id=identity.person_id,
        notes=payload.notes,
    )
    db.add(lockdown)
    await db.flush()
    commands = [
        facility_access_lockdown_command(lockdown, device, payload.command_valid_seconds, issued_at)
        for device in devices
    ]
    for command in commands:
        db.add(command)
    await db.commit()
    await db.refresh(lockdown)
    for command in commands:
        await db.refresh(command)
    return FacilityAccessLockdownResultRead(
        lockdown=facility_access_lockdown_read(lockdown),
        commands=[facility_access_command_read(command) for command in commands],
        devices_targeted=len(devices),
        recommendation=facility_access_lockdown_recommendation(lockdown, len(devices)),
    )


async def list_facility_access_lockdowns(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    facility_id: UUID | None = None,
) -> list[FacilityAccessLockdownRead]:
    await ensure_manage_assets(authz, identity, organization_id)
    statement = select(FacilityAccessLockdown).where(FacilityAccessLockdown.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(FacilityAccessLockdown.facility_id == facility_id)
    rows = await db.scalars(statement.order_by(FacilityAccessLockdown.activated_at.desc()).limit(25))
    return [facility_access_lockdown_read(row) for row in rows.all()]


async def update_facility_access_lockdown(
    db: AsyncSession,
    identity: CurrentIdentity,
    lockdown_id: UUID,
    payload: FacilityAccessLockdownUpdate,
    authz: AuthorizationService,
) -> FacilityAccessLockdownRead:
    lockdown = await get_facility_access_lockdown(db, lockdown_id)
    await ensure_manage_assets(authz, identity, lockdown.organization_id)
    lockdown.status = payload.status
    if payload.status in {"resolved", "cancelled"}:
        lockdown.resolved_at = datetime.now(UTC)
    elif payload.status == "active":
        lockdown.resolved_at = None
    if payload.notes:
        lockdown.notes = append_note(lockdown.notes, payload.notes)
    await db.commit()
    await db.refresh(lockdown)
    return facility_access_lockdown_read(lockdown)


async def facility_access_lockdown_dashboard(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
) -> FacilityAccessLockdownDashboardRead:
    await get_organization(db, organization_id)
    since = datetime.now(UTC) - timedelta(hours=24)
    lockdown_statement = select(FacilityAccessLockdown).where(FacilityAccessLockdown.organization_id == organization_id)
    device_statement = select(FacilityAccessDevice).where(
        FacilityAccessDevice.organization_id == organization_id,
        FacilityAccessDevice.status == "active",
    )
    command_statement = select(FacilityAccessCommand).where(FacilityAccessCommand.organization_id == organization_id)
    if facility_id is not None:
        lockdown_statement = lockdown_statement.where(FacilityAccessLockdown.facility_id == facility_id)
        device_statement = device_statement.where(FacilityAccessDevice.facility_id == facility_id)
        command_statement = command_statement.where(FacilityAccessCommand.facility_id == facility_id)
    lockdowns = list(
        (await db.scalars(lockdown_statement.order_by(FacilityAccessLockdown.activated_at.desc()).limit(25))).all()
    )
    devices = list((await db.scalars(device_statement)).all())
    commands = list(
        (
            await db.scalars(
                command_statement
                .where(FacilityAccessCommand.command_type.in_(["lockdown", "unlock_all"]))
                .order_by(FacilityAccessCommand.issued_at.desc())
                .limit(25)
            )
        ).all()
    )
    return FacilityAccessLockdownDashboardRead(
        organization_id=organization_id,
        facility_id=facility_id,
        active_lockdown_count=len([item for item in lockdowns if item.status == "active"]),
        active_device_count=len(devices),
        command_count_last_24h=len([command for command in commands if normalize_datetime(command.issued_at) >= since]),
        recent_lockdowns=[facility_access_lockdown_read(item) for item in lockdowns[:10]],
        recent_commands=[facility_access_command_read(command) for command in commands[:10]],
        recommendation=facility_access_lockdown_dashboard_recommendation(lockdowns, devices),
    )


async def provision_facility_utility_meter(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FacilityUtilityMeterCreate,
    authz: AuthorizationService,
) -> FacilityUtilityMeterProvisionRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    meter_id = payload.meter_id.strip()
    existing = await db.scalar(
        select(FacilityUtilityMeter).where(
            FacilityUtilityMeter.organization_id == payload.organization_id,
            FacilityUtilityMeter.meter_id == meter_id,
        )
    )
    api_key = payload.api_key or token_urlsafe(32)
    if existing is None:
        meter = FacilityUtilityMeter(
            organization_id=payload.organization_id,
            facility_id=payload.facility_id,
            meter_id=meter_id,
            name=payload.name,
            utility_type=payload.utility_type,
            unit=payload.unit,
            location=payload.location,
            provider=payload.provider,
            account_reference=payload.account_reference,
            status=payload.status,
            api_key_hash=hash_reader_key(api_key),
            cost_per_unit=payload.cost_per_unit,
            target_daily_usage=payload.target_daily_usage,
            notes=payload.notes,
        )
        db.add(meter)
    else:
        meter = existing
        meter.facility_id = payload.facility_id
        meter.name = payload.name
        meter.utility_type = payload.utility_type
        meter.unit = payload.unit
        meter.location = payload.location
        meter.provider = payload.provider
        meter.account_reference = payload.account_reference
        meter.status = payload.status
        meter.api_key_hash = hash_reader_key(api_key)
        meter.cost_per_unit = payload.cost_per_unit
        meter.target_daily_usage = payload.target_daily_usage
        meter.notes = payload.notes
    await db.commit()
    await db.refresh(meter)
    return FacilityUtilityMeterProvisionRead(meter=facility_utility_meter_read(meter), api_key=api_key)


async def list_facility_utility_meters(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    facility_id: UUID | None = None,
) -> list[FacilityUtilityMeterRead]:
    await ensure_manage_assets(authz, identity, organization_id)
    statement = select(FacilityUtilityMeter).where(FacilityUtilityMeter.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(FacilityUtilityMeter.facility_id == facility_id)
    rows = await db.scalars(statement.order_by(FacilityUtilityMeter.utility_type, FacilityUtilityMeter.name))
    return [facility_utility_meter_read(row) for row in rows.all()]


async def record_facility_utility_reading(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FacilityUtilityReadingCreate,
    authz: AuthorizationService,
) -> FacilityUtilityReadingResultRead:
    meter = await get_facility_utility_meter(db, payload.utility_meter_id)
    if meter.organization_id != payload.organization_id or meter.facility_id != payload.facility_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility utility meter not found")
    await ensure_manage_assets(authz, identity, meter.organization_id)
    return await persist_facility_utility_reading(
        db,
        meter,
        reading_value=payload.reading_value,
        usage_delta=payload.usage_delta,
        cost_estimate=payload.cost_estimate,
        reading_at=payload.reading_at or datetime.now(UTC),
        source=payload.source,
        external_reference=payload.external_reference,
        notes=payload.notes,
        signature_validated=False,
    )


async def record_gateway_facility_utility_reading(
    db: AsyncSession,
    organization_id: UUID,
    meter_id: str,
    api_key: str | None,
    payload: FacilityUtilityGatewayReadingCreate,
) -> FacilityUtilityReadingResultRead:
    meter = await get_facility_utility_meter_by_meter_id(db, organization_id, meter_id.strip())
    validate_facility_utility_meter_key(meter, api_key)
    return await persist_facility_utility_reading(
        db,
        meter,
        reading_value=payload.reading_value,
        usage_delta=payload.usage_delta,
        cost_estimate=payload.cost_estimate,
        reading_at=payload.reading_at or datetime.now(UTC),
        source="utility_gateway",
        external_reference=payload.external_reference,
        notes=payload.notes,
        signature_validated=True,
    )


async def facility_utility_dashboard(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
) -> FacilityUtilityDashboardRead:
    await get_organization(db, organization_id)
    meter_statement = select(FacilityUtilityMeter).where(FacilityUtilityMeter.organization_id == organization_id)
    reading_statement = select(FacilityUtilityReading).where(FacilityUtilityReading.organization_id == organization_id)
    alert_statement = select(FacilityUtilityAlert).where(FacilityUtilityAlert.organization_id == organization_id)
    if facility_id is not None:
        meter_statement = meter_statement.where(FacilityUtilityMeter.facility_id == facility_id)
        reading_statement = reading_statement.where(FacilityUtilityReading.facility_id == facility_id)
        alert_statement = alert_statement.where(FacilityUtilityAlert.facility_id == facility_id)
    meters = list((await db.scalars(meter_statement)).all())
    since = datetime.now(UTC) - timedelta(days=30)
    readings = list(
        (
            await db.scalars(
                reading_statement
                .where(FacilityUtilityReading.reading_at >= since)
                .order_by(FacilityUtilityReading.reading_at.desc())
            )
        ).all()
    )
    alerts = list(
        (
            await db.scalars(
                alert_statement
                .where(FacilityUtilityAlert.status.in_(["open", "acknowledged"]))
                .order_by(FacilityUtilityAlert.triggered_at.desc())
            )
        ).all()
    )
    usage_by_type: dict[str, Decimal] = {}
    total_usage = Decimal("0")
    total_cost = Decimal("0")
    meter_types = {meter.id: meter.utility_type for meter in meters}
    for reading in readings:
        usage = reading.usage_delta or Decimal("0")
        cost = reading.cost_estimate or Decimal("0")
        total_usage += usage
        total_cost += cost
        utility_type = meter_types.get(reading.utility_meter_id, "unknown")
        usage_by_type[utility_type] = usage_by_type.get(utility_type, Decimal("0")) + usage
    return FacilityUtilityDashboardRead(
        organization_id=organization_id,
        facility_id=facility_id,
        meter_count=len(meters),
        open_alert_count=len(alerts),
        total_usage_last_30d=total_usage,
        total_cost_last_30d=total_cost,
        usage_by_type=usage_by_type,
        recent_readings=[facility_utility_reading_read(reading) for reading in readings[:10]],
        open_alerts=[facility_utility_alert_read(alert) for alert in alerts[:10]],
        recommendation=facility_utility_dashboard_recommendation(alerts, meters),
    )


async def update_facility_utility_alert(
    db: AsyncSession,
    identity: CurrentIdentity,
    alert_id: UUID,
    payload: FacilityUtilityAlertUpdate,
    authz: AuthorizationService,
) -> FacilityUtilityAlertRead:
    alert = await get_facility_utility_alert(db, alert_id)
    await ensure_manage_assets(authz, identity, alert.organization_id)
    alert.status = payload.status
    if payload.status in {"resolved", "dismissed"}:
        alert.resolved_at = datetime.now(UTC)
    if payload.notes:
        alert.notes = append_note(alert.notes, payload.notes)
    await db.commit()
    await db.refresh(alert)
    return facility_utility_alert_read(alert)


async def create_clubhouse_amenity(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: ClubhouseAmenityCreate,
    authz: AuthorizationService,
) -> ClubhouseAmenityRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    amenity = ClubhouseAmenity(
        organization_id=payload.organization_id,
        facility_id=payload.facility_id,
        name=payload.name,
        amenity_type=payload.amenity_type.strip().lower(),
        location=payload.location,
        capacity=payload.capacity,
        reservation_required=payload.reservation_required,
        hourly_rate=payload.hourly_rate,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(amenity)
    await db.commit()
    await db.refresh(amenity)
    return clubhouse_amenity_read(amenity)


async def list_clubhouse_amenities(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    facility_id: UUID | None = None,
) -> list[ClubhouseAmenityRead]:
    await ensure_manage_assets(authz, identity, organization_id)
    statement = select(ClubhouseAmenity).where(ClubhouseAmenity.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(ClubhouseAmenity.facility_id == facility_id)
    rows = await db.scalars(statement.order_by(ClubhouseAmenity.amenity_type, ClubhouseAmenity.name))
    return [clubhouse_amenity_read(row) for row in rows.all()]


async def create_clubhouse_visit(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: ClubhouseVisitCreate,
    authz: AuthorizationService,
) -> ClubhouseVisitRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    facility = await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    if payload.person_id is not None:
        await get_person_member_for_organization(db, payload.person_id, payload.organization_id)
    if payload.access_event_id is not None:
        event = await db.get(FacilityAccessEvent, payload.access_event_id)
        if event is None or event.organization_id != payload.organization_id or event.facility_id != payload.facility_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility access event not found")
    check_in_at = payload.check_in_at or datetime.now(UTC)
    projected = await clubhouse_current_occupancy(db, payload.organization_id, payload.facility_id)
    if facility.capacity is not None and projected + payload.party_size > facility.capacity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Clubhouse capacity would be exceeded")
    visit = ClubhouseVisit(
        organization_id=payload.organization_id,
        facility_id=payload.facility_id,
        person_id=payload.person_id,
        access_event_id=payload.access_event_id,
        guest_name=payload.guest_name,
        guest_email=payload.guest_email,
        check_in_at=check_in_at,
        party_size=payload.party_size,
        purpose=payload.purpose,
        notes=payload.notes,
    )
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    return clubhouse_visit_read(visit)


async def list_clubhouse_visits(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    facility_id: UUID | None = None,
    status_filter: str | None = None,
) -> list[ClubhouseVisitRead]:
    await ensure_manage_assets(authz, identity, organization_id)
    statement = select(ClubhouseVisit).where(ClubhouseVisit.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(ClubhouseVisit.facility_id == facility_id)
    if status_filter is not None:
        statement = statement.where(ClubhouseVisit.status == status_filter)
    rows = await db.scalars(statement.order_by(ClubhouseVisit.check_in_at.desc()).limit(50))
    return [clubhouse_visit_read(row) for row in rows.all()]


async def update_clubhouse_visit(
    db: AsyncSession,
    identity: CurrentIdentity,
    visit_id: UUID,
    payload: ClubhouseVisitUpdate,
    authz: AuthorizationService,
) -> ClubhouseVisitRead:
    visit = await get_clubhouse_visit(db, visit_id)
    await ensure_manage_assets(authz, identity, visit.organization_id)
    visit.status = payload.status
    if payload.status == "checked_out":
        visit.check_out_at = payload.check_out_at or datetime.now(UTC)
    elif payload.status == "checked_in":
        visit.check_out_at = None
    if payload.notes:
        visit.notes = append_note(visit.notes, payload.notes)
    await db.commit()
    await db.refresh(visit)
    return clubhouse_visit_read(visit)


async def create_clubhouse_amenity_reservation(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: ClubhouseAmenityReservationCreate,
    authz: AuthorizationService,
) -> ClubhouseAmenityReservationRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    amenity = await get_clubhouse_amenity(db, payload.amenity_id)
    if amenity.organization_id != payload.organization_id or amenity.facility_id != payload.facility_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clubhouse amenity not found")
    if amenity.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clubhouse amenity is not active")
    if payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ends_at must be after starts_at")
    if payload.person_id is not None:
        await get_person_member_for_organization(db, payload.person_id, payload.organization_id)
    overlapping = await clubhouse_amenity_reserved_party_size(db, amenity.id, payload.starts_at, payload.ends_at)
    if amenity.capacity is not None and overlapping + payload.party_size > amenity.capacity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Amenity capacity would be exceeded")
    reservation = ClubhouseAmenityReservation(
        organization_id=payload.organization_id,
        facility_id=payload.facility_id,
        amenity_id=payload.amenity_id,
        person_id=payload.person_id,
        guest_name=payload.guest_name,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        party_size=payload.party_size,
        expected_fee=payload.expected_fee if payload.expected_fee is not None else clubhouse_amenity_fee(amenity, payload),
        notes=payload.notes,
    )
    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)
    return clubhouse_reservation_read(reservation)


async def list_clubhouse_amenity_reservations(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    facility_id: UUID | None = None,
    amenity_id: UUID | None = None,
    status_filter: str | None = None,
) -> list[ClubhouseAmenityReservationRead]:
    await ensure_manage_assets(authz, identity, organization_id)
    statement = select(ClubhouseAmenityReservation).where(ClubhouseAmenityReservation.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(ClubhouseAmenityReservation.facility_id == facility_id)
    if amenity_id is not None:
        statement = statement.where(ClubhouseAmenityReservation.amenity_id == amenity_id)
    if status_filter is not None:
        statement = statement.where(ClubhouseAmenityReservation.status == status_filter)
    rows = await db.scalars(statement.order_by(ClubhouseAmenityReservation.starts_at.desc()).limit(50))
    return [clubhouse_reservation_read(row) for row in rows.all()]


async def update_clubhouse_amenity_reservation(
    db: AsyncSession,
    identity: CurrentIdentity,
    reservation_id: UUID,
    payload: ClubhouseAmenityReservationUpdate,
    authz: AuthorizationService,
) -> ClubhouseAmenityReservationRead:
    reservation = await get_clubhouse_reservation(db, reservation_id)
    await ensure_manage_assets(authz, identity, reservation.organization_id)
    reservation.status = payload.status
    if payload.notes:
        reservation.notes = append_note(reservation.notes, payload.notes)
    await db.commit()
    await db.refresh(reservation)
    return clubhouse_reservation_read(reservation)


async def clubhouse_dashboard(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
) -> ClubhouseDashboardRead:
    await get_organization(db, organization_id)
    facility: Facility | None = None
    if facility_id is not None:
        facility = await get_facility_for_organization(db, facility_id, organization_id)
    amenity_statement = select(ClubhouseAmenity).where(ClubhouseAmenity.organization_id == organization_id)
    visit_statement = select(ClubhouseVisit).where(ClubhouseVisit.organization_id == organization_id)
    reservation_statement = select(ClubhouseAmenityReservation).where(
        ClubhouseAmenityReservation.organization_id == organization_id
    )
    if facility_id is not None:
        amenity_statement = amenity_statement.where(ClubhouseAmenity.facility_id == facility_id)
        visit_statement = visit_statement.where(ClubhouseVisit.facility_id == facility_id)
        reservation_statement = reservation_statement.where(ClubhouseAmenityReservation.facility_id == facility_id)
    amenities = list((await db.scalars(amenity_statement)).all())
    active_visits = list(
        (
            await db.scalars(
                visit_statement
                .where(ClubhouseVisit.status == "checked_in")
                .order_by(ClubhouseVisit.check_in_at.desc())
                .limit(25)
            )
        ).all()
    )
    now = datetime.now(UTC)
    day_start = datetime.combine(now.date(), datetime.min.time(), tzinfo=UTC)
    day_end = day_start + timedelta(days=1)
    reservations_today = list(
        (
            await db.scalars(
                reservation_statement
                .where(ClubhouseAmenityReservation.starts_at >= day_start)
                .where(ClubhouseAmenityReservation.starts_at < day_end)
                .where(ClubhouseAmenityReservation.status.in_(["reserved", "checked_in"]))
                .order_by(ClubhouseAmenityReservation.starts_at.asc())
                .limit(25)
            )
        ).all()
    )
    occupancy = sum(visit.party_size for visit in active_visits)
    capacity = facility.capacity if facility is not None else None
    return ClubhouseDashboardRead(
        organization_id=organization_id,
        facility_id=facility_id,
        current_occupancy=occupancy,
        capacity=capacity,
        capacity_remaining=max(capacity - occupancy, 0) if capacity is not None else None,
        active_member_visits=len([visit for visit in active_visits if visit.person_id is not None]),
        active_guest_visits=len([visit for visit in active_visits if visit.person_id is None]),
        amenity_count=len(amenities),
        reservations_today=len(reservations_today),
        expected_revenue_today=sum((reservation.expected_fee or Decimal("0")) for reservation in reservations_today),
        active_visits=[clubhouse_visit_read(visit) for visit in active_visits[:10]],
        upcoming_reservations=[clubhouse_reservation_read(row) for row in reservations_today[:10]],
        popular_amenities=clubhouse_popular_amenities(amenities, reservations_today),
        recommendation=clubhouse_dashboard_recommendation(occupancy, capacity, reservations_today, amenities),
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
    rule = await get_facility_booking_rule(db, payload.organization_id, payload.facility_id)
    validate_booking_against_rule(payload.starts_at, payload.ends_at, rule)
    await ensure_facility_available(db, payload.facility_id, payload.starts_at, payload.ends_at, rule=rule)

    booking = FacilityBooking(
        requested_by_person_id=identity.person_id,
        status=FacilityBookingStatus.REQUESTED if rule and rule.requires_approval else FacilityBookingStatus.CONFIRMED,
        **payload.model_dump(),
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


async def create_recurring_facility_bookings(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FacilityRecurringBookingCreate,
    authz: AuthorizationService,
) -> list[FacilityBooking]:
    await get_organization(db, payload.organization_id)
    await ensure_manage_assets(authz, identity, payload.organization_id)
    await get_facility_for_organization(db, payload.facility_id, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    if payload.event_id is not None:
        await get_event_for_organization(db, payload.event_id, payload.organization_id)
    rule = await get_facility_booking_rule(db, payload.organization_id, payload.facility_id)
    delta = timedelta(days=1 if payload.recurrence_frequency == "daily" else 7)
    recurrence_group_id = f"rec-{token_urlsafe(8)}"
    bookings: list[FacilityBooking] = []
    for index in range(payload.occurrence_count):
        starts_at = payload.starts_at + delta * index
        ends_at = payload.ends_at + delta * index
        validate_booking_against_rule(starts_at, ends_at, rule)
        await ensure_facility_available(db, payload.facility_id, starts_at, ends_at, rule=rule)
        booking = FacilityBooking(
            organization_id=payload.organization_id,
            facility_id=payload.facility_id,
            team_id=payload.team_id,
            event_id=payload.event_id,
            requested_by_person_id=identity.person_id,
            title=f"{payload.title} #{index + 1}",
            starts_at=starts_at,
            ends_at=ends_at,
            status=FacilityBookingStatus.REQUESTED if rule and rule.requires_approval else FacilityBookingStatus.CONFIRMED,
            requester_name=payload.requester_name,
            requester_email=payload.requester_email,
            expected_attendees=payload.expected_attendees,
            rate=payload.rate,
            deposit_required=payload.deposit_required,
            insurance_certificate_ref=payload.insurance_certificate_ref,
            special_requirements=payload.special_requirements,
            access_code=f"{payload.access_code}-{index + 1}" if payload.access_code else None,
            public_visible=payload.public_visible,
            recurrence_group_id=recurrence_group_id,
            occurrence_index=index + 1,
            conflict_note="Created from recurring booking pattern.",
        )
        db.add(booking)
        bookings.append(booking)
    await db.commit()
    for booking in bookings:
        await db.refresh(booking)
    return bookings


async def list_facility_bookings(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
) -> list[FacilityBooking]:
    statement = select(FacilityBooking).where(FacilityBooking.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(FacilityBooking.facility_id == facility_id)
    return list((await db.scalars(statement.order_by(FacilityBooking.starts_at.desc()))).all())


async def facility_availability(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID,
    starts_at: datetime,
    ends_at: datetime,
) -> FacilityAvailabilityRead:
    await get_facility_for_organization(db, facility_id, organization_id)
    if ends_at <= starts_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ends_at must be after starts_at")
    rule = await get_facility_booking_rule(db, organization_id, facility_id)
    bookings = await bookings_between(db, facility_id, starts_at, ends_at)
    slots = [
        FacilityAvailabilitySlotRead(
            starts_at=booking.starts_at,
            ends_at=booking.ends_at,
            status="booked" if booking.status != FacilityBookingStatus.REQUESTED else "requested",
            booking_id=booking.id,
            title=booking.title,
            conflict_note=booking.conflict_note,
        )
        for booking in bookings
    ]
    conflict_count = count_booking_conflicts(bookings, rule.buffer_minutes if rule else 0)
    return FacilityAvailabilityRead(
        organization_id=organization_id,
        facility_id=facility_id,
        starts_at=starts_at,
        ends_at=ends_at,
        rule=rule,
        slots=slots,
        conflict_count=conflict_count,
    )


async def facility_utilization(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID,
    starts_at: datetime,
    ends_at: datetime,
) -> FacilityUtilizationRead:
    await get_facility_for_organization(db, facility_id, organization_id)
    if ends_at <= starts_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ends_at must be after starts_at")
    bookings = await bookings_between(db, facility_id, starts_at, ends_at)
    booked_hours = sum(max((booking.ends_at - booking.starts_at).total_seconds() / 3600, 0) for booking in bookings)
    available_hours = max((ends_at - starts_at).total_seconds() / 3600, 0)
    projected_revenue = sum(
        (
            Decimal(str(max((booking.ends_at - booking.starts_at).total_seconds() / 3600, 0)))
            * (booking.rate or Decimal("0"))
            for booking in bookings
        ),
        Decimal("0"),
    )
    attendee_values = [booking.expected_attendees for booking in bookings if booking.expected_attendees is not None]
    utilization_percent = round(booked_hours / available_hours * 100) if available_hours else 0
    return FacilityUtilizationRead(
        organization_id=organization_id,
        facility_id=facility_id,
        starts_at=starts_at,
        ends_at=ends_at,
        available_hours=round(available_hours, 2),
        booked_hours=round(booked_hours, 2),
        utilization_percent=max(0, min(100, utilization_percent)),
        booking_count=len(bookings),
        projected_revenue=projected_revenue.quantize(Decimal("0.01")),
        average_attendance=round(sum(attendee_values) / len(attendee_values), 1) if attendee_values else None,
        recommendation=facility_utilization_recommendation(utilization_percent, projected_revenue),
    )


async def list_public_facility_hire(
    db: AsyncSession,
    site: str,
    starts_at: datetime,
    ends_at: datetime,
) -> list[FacilityPublicListingRead]:
    organization = await get_public_site_organization(db, site)
    if ends_at <= starts_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ends_at must be after starts_at")
    rules = list(
        (
            await db.scalars(
                select(FacilityBookingRule)
                .where(FacilityBookingRule.organization_id == organization.id)
                .where(FacilityBookingRule.allow_public_booking.is_(True))
                .where(FacilityBookingRule.status == "active")
                .order_by(FacilityBookingRule.created_at.desc())
            )
        ).all()
    )
    listings: list[FacilityPublicListingRead] = []
    for rule in rules:
        facility = await get_facility_for_organization(db, rule.facility_id, organization.id)
        availability = await facility_availability(db, organization.id, facility.id, starts_at, ends_at)
        public_rate = facility_public_hourly_rate(facility, rule, starts_at)
        listings.append(
            FacilityPublicListingRead(
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
                rule=rule,
                availability=availability,
                public_rate=public_rate,
                rate_summary=facility_rate_summary(public_rate, rule),
                next_available_slot=next_available_public_slot(
                    availability.slots,
                    starts_at,
                    ends_at,
                    rule.min_booking_minutes,
                    rule.buffer_minutes,
                ),
            )
        )
    return listings


async def create_public_facility_booking(
    db: AsyncSession,
    site: str,
    payload: FacilityPublicBookingCreate,
) -> FacilityBookingCheckoutRead:
    organization = await get_public_site_organization(db, site)
    facility = await get_facility_for_organization(db, payload.facility_id, organization.id)
    rule = await get_facility_booking_rule(db, organization.id, facility.id)
    if rule is None or not rule.allow_public_booking or rule.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility is not publicly bookable")
    validate_booking_against_rule(payload.starts_at, payload.ends_at, rule)
    await ensure_facility_available(db, facility.id, payload.starts_at, payload.ends_at, rule=rule)

    reference = f"FAC-{token_urlsafe(6).upper()}"
    rate = facility_public_hourly_rate(facility, rule, payload.starts_at)
    duration_hours = Decimal(str(max((payload.ends_at - payload.starts_at).total_seconds() / 3600, 0)))
    amount_due = (duration_hours * rate).quantize(Decimal("0.01"))
    invoice = FinanceInvoice(
        organization_id=organization.id,
        invoice_number=f"{reference}-{payload.starts_at:%m%d}",
        title=f"Facility hire: {facility.name}",
        amount_due=amount_due,
        amount_paid=Decimal("0"),
        currency="USD",
        due_on=payload.starts_at.date(),
        status=CommercialStatus.DRAFT,
        memo=(
            f"Public facility hire for {payload.requester_name} ({payload.requester_email}). "
            f"Activity: {payload.activity_type}. Facility: {facility.name}. "
            f"Add-ons: {payload.add_ons or 'none'}."
        ),
    )
    db.add(invoice)
    await db.flush()

    session_id = facility_checkout_session_id(invoice.id, payload.provider)
    booking = FacilityBooking(
        organization_id=organization.id,
        facility_id=facility.id,
        requested_by_person_id=None,
        title=payload.title,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        status=FacilityBookingStatus.REQUESTED if rule.requires_approval else FacilityBookingStatus.APPROVED,
        requester_name=payload.requester_name,
        requester_email=payload.requester_email,
        expected_attendees=payload.expected_attendees,
        rate=rate,
        deposit_required=amount_due,
        finance_invoice_id=invoice.id,
        insurance_certificate_ref=payload.insurance_certificate_ref,
        special_requirements=public_booking_requirements(payload),
        access_code=None,
        public_visible=True,
        booking_source="public_site",
        public_booking_reference=reference,
        payment_status="payment_pending",
        payment_checkout_url=None,
        conflict_note="Public booking created from branded site; payment and approval state tracked by invoice.",
    )
    db.add(booking)
    await db.flush()
    checkout_url = facility_checkout_url(payload.checkout_base_url, session_id, invoice.id, booking.id, payload.provider)
    booking.payment_checkout_url = checkout_url
    await db.commit()
    await db.refresh(invoice)
    await db.refresh(booking)
    return FacilityBookingCheckoutRead(
        booking=booking,
        invoice=finance_invoice_read(invoice),
        checkout_url=checkout_url,
        session_id=session_id,
        access_window_summary="Access opens 15 minutes before the booking after payment confirmation.",
    )


async def get_facility_hire_hosted_checkout(
    db: AsyncSession,
    session_id: str,
    invoice_id: UUID,
    booking_id: UUID,
    provider: str,
) -> FacilityHireHostedCheckoutRead:
    invoice, booking = await get_facility_checkout_records(db, invoice_id, booking_id)
    expected_session_id = facility_checkout_session_id(invoice.id, provider)
    if not hmac.compare_digest(expected_session_id, session_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid facility checkout session")
    return facility_hire_checkout_read(invoice, booking, provider, session_id)


async def settle_facility_hire_checkout(
    db: AsyncSession,
    session_id: str,
    payload: FacilityHireCheckoutSettlementCreate,
) -> FacilityHireCheckoutSettlementRead:
    invoice, booking = await get_facility_checkout_records(db, payload.invoice_id, payload.booking_id)
    expected_session_id = facility_checkout_session_id(invoice.id, payload.provider)
    if not hmac.compare_digest(expected_session_id, session_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid facility checkout session")
    if payload.currency != invoice.currency:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Currency does not match invoice")

    open_amount = invoice_open_amount(invoice)
    payment: FinancePayment | None = None
    if payload.status == "succeeded" and open_amount > 0:
        amount = min(payload.amount, open_amount)
        if amount <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Payment amount must be positive")
        if payload.external_payment_id:
            existing = await db.scalar(
                select(FinancePayment)
                .where(FinancePayment.invoice_id == invoice.id)
                .where(FinancePayment.external_reference == payload.external_payment_id)
            )
            if existing is not None:
                return facility_settlement_read(invoice, booking, existing, payload.provider)
        payment = FinancePayment(
            organization_id=invoice.organization_id,
            invoice_id=invoice.id,
            amount=amount,
            currency=invoice.currency,
            method=payload.method,
            external_reference=payload.external_payment_id,
            received_at=datetime.now(UTC),
            notes=payload.raw_reference,
        )
        db.add(payment)
        invoice.amount_paid += amount
        invoice.status = CommercialStatus.PAID if invoice_open_amount(invoice) <= 0 else CommercialStatus.PARTIAL
    if invoice_open_amount(invoice) <= 0:
        booking.payment_status = "paid"
        if booking.status != FacilityBookingStatus.CANCELLED:
            apply_facility_access_window(booking)
    elif invoice.amount_paid > 0:
        booking.payment_status = "partial"
    else:
        booking.payment_status = "payment_pending"
    await db.commit()
    if payment is not None:
        await db.refresh(payment)
    await db.refresh(invoice)
    await db.refresh(booking)
    return facility_settlement_read(invoice, booking, payment, payload.provider)


async def update_facility_booking_status(
    db: AsyncSession,
    identity: CurrentIdentity,
    booking_id: UUID,
    payload: FacilityBookingStatusUpdate,
    authz: AuthorizationService,
) -> FacilityBooking:
    booking = await get_facility_booking(db, booking_id)
    await ensure_manage_assets(authz, identity, booking.organization_id)
    if payload.status == FacilityBookingStatus.CONFIRMED and booking.payment_status in {"payment_pending", "partial"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking still has unpaid facility hire balance")
    booking.status = payload.status
    if payload.status == FacilityBookingStatus.CONFIRMED and booking.payment_status == "paid":
        apply_facility_access_window(booking)
    if payload.status == FacilityBookingStatus.CANCELLED:
        booking.access_code = None
        booking.access_starts_at = None
        booking.access_ends_at = None
        if booking.finance_invoice_id is not None:
            invoice = await db.get(FinanceInvoice, booking.finance_invoice_id)
            if invoice is not None and invoice.status not in {CommercialStatus.PAID, CommercialStatus.PARTIAL}:
                invoice.status = CommercialStatus.CANCELLED
    if payload.notes:
        booking.conflict_note = append_note(booking.conflict_note, payload.notes)
    await db.commit()
    await db.refresh(booking)
    return booking


async def create_public_facility_waitlist_entry(
    db: AsyncSession,
    site: str,
    payload: FacilityBookingWaitlistCreate,
) -> FacilityBookingWaitlistRead:
    organization = await get_public_site_organization(db, site)
    facility = await get_facility_for_organization(db, payload.facility_id, organization.id)
    rule = await get_facility_booking_rule(db, organization.id, facility.id)
    if rule is None or not rule.allow_public_booking or rule.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility is not publicly bookable")
    validate_booking_against_rule(payload.desired_starts_at, payload.desired_ends_at, rule)
    entry = FacilityBookingWaitlistEntry(
        organization_id=organization.id,
        priority_score=waitlist_priority_score(payload),
        status="pending",
        **payload.model_dump(),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return facility_waitlist_read(entry)


async def list_facility_waitlist_entries(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID | None = None,
    status_filter: str | None = None,
) -> list[FacilityBookingWaitlistRead]:
    await get_organization(db, organization_id)
    statement = select(FacilityBookingWaitlistEntry).where(FacilityBookingWaitlistEntry.organization_id == organization_id)
    if facility_id is not None:
        statement = statement.where(FacilityBookingWaitlistEntry.facility_id == facility_id)
    if status_filter is not None:
        statement = statement.where(FacilityBookingWaitlistEntry.status == status_filter)
    rows = list(
        (
            await db.scalars(
                statement.order_by(
                    FacilityBookingWaitlistEntry.priority_score.desc(),
                    FacilityBookingWaitlistEntry.created_at.asc(),
                )
            )
        ).all()
    )
    return [facility_waitlist_read(row) for row in rows]


async def update_facility_waitlist_entry(
    db: AsyncSession,
    identity: CurrentIdentity,
    entry_id: UUID,
    payload: FacilityBookingWaitlistUpdate,
    authz: AuthorizationService,
) -> FacilityBookingWaitlistRead:
    entry = await get_facility_waitlist_entry(db, entry_id)
    await ensure_manage_assets(authz, identity, entry.organization_id)
    entry.status = payload.status
    entry.priority_score = payload.priority_score if payload.priority_score is not None else entry.priority_score
    entry.expires_at = payload.expires_at if payload.expires_at is not None else entry.expires_at
    entry.notes = append_note(entry.notes, payload.notes) if payload.notes else entry.notes
    if payload.status == "offered":
        entry.notified_at = datetime.now(UTC)
        entry.expires_at = entry.expires_at or datetime.now(UTC) + timedelta(hours=24)
    await db.commit()
    await db.refresh(entry)
    return facility_waitlist_read(entry)


async def convert_facility_waitlist_entry(
    db: AsyncSession,
    identity: CurrentIdentity,
    entry_id: UUID,
    payload: FacilityBookingWaitlistConversionCreate,
    authz: AuthorizationService,
) -> FacilityBookingCheckoutRead:
    entry = await get_facility_waitlist_entry(db, entry_id)
    await ensure_manage_assets(authz, identity, entry.organization_id)
    if entry.status not in {"pending", "offered"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Waitlist entry is not convertible")
    facility = await get_facility_for_organization(db, entry.facility_id, entry.organization_id)
    rule = await get_facility_booking_rule(db, entry.organization_id, facility.id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility booking rule not found")
    await ensure_facility_available(db, facility.id, entry.desired_starts_at, entry.desired_ends_at, rule=rule)
    rate = facility_public_hourly_rate(facility, rule, entry.desired_starts_at)
    duration_hours = Decimal(str(max((entry.desired_ends_at - entry.desired_starts_at).total_seconds() / 3600, 0)))
    amount_due = (duration_hours * rate).quantize(Decimal("0.01"))
    reference = f"FAC-WL-{token_urlsafe(5).upper()}"
    invoice = FinanceInvoice(
        organization_id=entry.organization_id,
        invoice_number=f"{reference}-{entry.desired_starts_at:%m%d}",
        title=f"Waitlist facility hire: {facility.name}",
        amount_due=amount_due,
        amount_paid=Decimal("0"),
        currency="USD",
        due_on=entry.desired_starts_at.date(),
        status=CommercialStatus.DRAFT,
        memo=f"Converted waitlist entry for {entry.requester_name} ({entry.requester_email}).",
    )
    db.add(invoice)
    await db.flush()
    session_id = facility_checkout_session_id(invoice.id, payload.provider)
    booking = FacilityBooking(
        organization_id=entry.organization_id,
        facility_id=facility.id,
        title=entry.title,
        starts_at=entry.desired_starts_at,
        ends_at=entry.desired_ends_at,
        status=FacilityBookingStatus.REQUESTED if rule.requires_approval else FacilityBookingStatus.APPROVED,
        requester_name=entry.requester_name,
        requester_email=entry.requester_email,
        expected_attendees=entry.expected_attendees,
        rate=rate,
        deposit_required=amount_due,
        finance_invoice_id=invoice.id,
        insurance_certificate_ref=entry.insurance_certificate_ref,
        special_requirements=waitlist_requirements(entry),
        public_visible=True,
        booking_source="waitlist",
        public_booking_reference=reference,
        payment_status="payment_pending",
        conflict_note="Converted from public facility waitlist.",
    )
    db.add(booking)
    await db.flush()
    booking.payment_checkout_url = facility_checkout_url(payload.checkout_base_url, session_id, invoice.id, booking.id, payload.provider)
    entry.status = "converted"
    entry.offered_booking_id = booking.id
    entry.notified_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(invoice)
    await db.refresh(booking)
    await db.refresh(entry)
    return FacilityBookingCheckoutRead(
        booking=booking,
        invoice=finance_invoice_read(invoice),
        checkout_url=booking.payment_checkout_url or "",
        session_id=session_id,
        access_window_summary="Converted from waitlist; access opens after payment confirmation.",
    )


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


async def get_facility_booking(db: AsyncSession, booking_id: UUID) -> FacilityBooking:
    booking = await db.get(FacilityBooking, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility booking not found")
    return booking


async def get_facility_waitlist_entry(
    db: AsyncSession,
    entry_id: UUID,
) -> FacilityBookingWaitlistEntry:
    entry = await db.get(FacilityBookingWaitlistEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility waitlist entry not found")
    return entry


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


async def get_facility_maintenance_schedule(
    db: AsyncSession,
    schedule_id: UUID,
) -> FacilityMaintenanceSchedule:
    schedule = await db.get(FacilityMaintenanceSchedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance schedule not found")
    return schedule


async def get_facility_lease_agreement(
    db: AsyncSession,
    lease_id: UUID,
) -> FacilityLeaseAgreement:
    lease = await db.get(FacilityLeaseAgreement, lease_id)
    if lease is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility lease agreement not found")
    return lease


async def get_facility_access_credential(
    db: AsyncSession,
    credential_id: UUID,
) -> FacilityAccessCredential:
    credential = await db.get(FacilityAccessCredential, credential_id)
    if credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility access credential not found")
    return credential


async def get_facility_access_device_by_device_id(
    db: AsyncSession,
    organization_id: UUID,
    device_id: str,
) -> FacilityAccessDevice:
    device = await db.scalar(
        select(FacilityAccessDevice).where(
            FacilityAccessDevice.organization_id == organization_id,
            FacilityAccessDevice.device_id == device_id,
        )
    )
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility access device not found")
    return device


async def get_facility_access_lockdown(
    db: AsyncSession,
    lockdown_id: UUID,
) -> FacilityAccessLockdown:
    lockdown = await db.get(FacilityAccessLockdown, lockdown_id)
    if lockdown is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility access lockdown not found")
    return lockdown


async def get_facility_utility_meter(
    db: AsyncSession,
    meter_pk: UUID,
) -> FacilityUtilityMeter:
    meter = await db.get(FacilityUtilityMeter, meter_pk)
    if meter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility utility meter not found")
    return meter


async def get_facility_utility_meter_by_meter_id(
    db: AsyncSession,
    organization_id: UUID,
    meter_id: str,
) -> FacilityUtilityMeter:
    meter = await db.scalar(
        select(FacilityUtilityMeter).where(
            FacilityUtilityMeter.organization_id == organization_id,
            FacilityUtilityMeter.meter_id == meter_id,
        )
    )
    if meter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility utility meter not found")
    return meter


async def get_facility_utility_alert(
    db: AsyncSession,
    alert_id: UUID,
) -> FacilityUtilityAlert:
    alert = await db.get(FacilityUtilityAlert, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility utility alert not found")
    return alert


async def get_clubhouse_amenity(db: AsyncSession, amenity_id: UUID) -> ClubhouseAmenity:
    amenity = await db.get(ClubhouseAmenity, amenity_id)
    if amenity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clubhouse amenity not found")
    return amenity


async def get_clubhouse_visit(db: AsyncSession, visit_id: UUID) -> ClubhouseVisit:
    visit = await db.get(ClubhouseVisit, visit_id)
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clubhouse visit not found")
    return visit


async def get_clubhouse_reservation(
    db: AsyncSession,
    reservation_id: UUID,
) -> ClubhouseAmenityReservation:
    reservation = await db.get(ClubhouseAmenityReservation, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clubhouse amenity reservation not found")
    return reservation


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
    rule: FacilityBookingRule | None = None,
) -> None:
    buffer_delta = timedelta(minutes=rule.buffer_minutes if rule else 0)
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
            FacilityBooking.starts_at < ends_at + buffer_delta,
            FacilityBooking.ends_at > starts_at - buffer_delta,
        )
    )
    if conflict is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Facility is already booked")


async def bookings_between(
    db: AsyncSession,
    facility_id: UUID,
    starts_at: datetime,
    ends_at: datetime,
) -> list[FacilityBooking]:
    return list(
        (
            await db.scalars(
                select(FacilityBooking)
                .where(FacilityBooking.facility_id == facility_id)
                .where(
                    FacilityBooking.status.in_(
                        [
                            FacilityBookingStatus.REQUESTED,
                            FacilityBookingStatus.APPROVED,
                            FacilityBookingStatus.CONFIRMED,
                            FacilityBookingStatus.CHECKED_IN,
                        ]
                    )
                )
                .where(FacilityBooking.starts_at < ends_at)
                .where(FacilityBooking.ends_at > starts_at)
                .order_by(FacilityBooking.starts_at.asc())
            )
        ).all()
    )


def validate_booking_against_rule(
    starts_at: datetime,
    ends_at: datetime,
    rule: FacilityBookingRule | None,
) -> None:
    if rule is None:
        return
    duration_minutes = int((ends_at - starts_at).total_seconds() / 60)
    if duration_minutes < rule.min_booking_minutes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Booking shorter than facility minimum")
    if duration_minutes > rule.max_booking_minutes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Booking exceeds facility maximum")
    if starts_at > datetime.now(UTC) + timedelta(days=rule.advance_booking_days):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Booking exceeds advance booking window")


def count_booking_conflicts(bookings: list[FacilityBooking], buffer_minutes: int) -> int:
    conflicts = 0
    buffer_delta = timedelta(minutes=buffer_minutes)
    ordered = sorted(bookings, key=lambda booking: booking.starts_at)
    for previous, current in zip(ordered, ordered[1:]):
        if previous.ends_at + buffer_delta > current.starts_at:
            conflicts += 1
    return conflicts


def facility_utilization_recommendation(utilization_percent: int, projected_revenue: Decimal) -> str:
    if utilization_percent >= 85:
        return "High utilization; protect buffer time and consider peak pricing for public bookings."
    if utilization_percent >= 55:
        return "Healthy utilization; fill shoulder hours with clinics, rentals, or community sessions."
    if projected_revenue > 0:
        return "Revenue exists but capacity remains; market open slots and bundle facility time with programs."
    return "Low utilization; publish availability, seed recurring training blocks, and review pricing."


def facility_public_hourly_rate(
    facility: Facility,
    rule: FacilityBookingRule,
    starts_at: datetime,
) -> Decimal:
    base_rate = facility.hourly_rate or Decimal("0")
    multiplier = rule.peak_hour_rate_multiplier or Decimal("1.00")
    if starts_at.weekday() >= 5 or 17 <= starts_at.hour <= 21:
        return (base_rate * multiplier).quantize(Decimal("0.01"))
    return base_rate.quantize(Decimal("0.01"))


def facility_rate_summary(public_rate: Decimal, rule: FacilityBookingRule) -> str:
    approval = "approval required" if rule.requires_approval else "instant confirmation after payment"
    return (
        f"USD {public_rate}/hr · {rule.min_booking_minutes}-{rule.max_booking_minutes} min · "
        f"{rule.buffer_minutes} min buffer · {approval}"
    )


def next_available_public_slot(
    booked_slots: list[FacilityAvailabilitySlotRead],
    starts_at: datetime,
    ends_at: datetime,
    min_booking_minutes: int,
    buffer_minutes: int,
) -> datetime | None:
    cursor = starts_at
    slot_delta = timedelta(minutes=min_booking_minutes)
    buffer_delta = timedelta(minutes=buffer_minutes)
    for booked in sorted(booked_slots, key=lambda slot: slot.starts_at):
        if cursor + slot_delta <= booked.starts_at - buffer_delta:
            return cursor
        cursor = max(cursor, booked.ends_at + buffer_delta)
    return cursor if cursor + slot_delta <= ends_at else None


def public_booking_requirements(payload: FacilityPublicBookingCreate) -> str:
    parts = [payload.special_requirements or "No special requirements."]
    if payload.requester_phone:
        parts.append(f"Requester phone: {payload.requester_phone}.")
    if payload.add_ons:
        parts.append(f"Requested add-ons: {payload.add_ons}.")
    return " ".join(parts)


def waitlist_requirements(entry: FacilityBookingWaitlistEntry) -> str:
    parts = [entry.special_requirements or "No special requirements."]
    if entry.requester_phone:
        parts.append(f"Requester phone: {entry.requester_phone}.")
    if entry.add_ons:
        parts.append(f"Requested add-ons: {entry.add_ons}.")
    return " ".join(parts)


def waitlist_priority_score(payload: FacilityBookingWaitlistCreate) -> int:
    attendee_score = min(payload.expected_attendees or 0, 100)
    insurance_score = 15 if payload.insurance_certificate_ref else 0
    contact_score = 10 if payload.requester_phone else 0
    return 100 + attendee_score + insurance_score + contact_score


def append_note(existing: str | None, note: str) -> str:
    timestamp = datetime.now(UTC).isoformat()
    line = f"{timestamp}: {note}"
    return f"{existing}\n{line}" if existing else line


def apply_facility_access_window(booking: FacilityBooking) -> None:
    booking.status = FacilityBookingStatus.CONFIRMED
    booking.access_code = booking.access_code or f"FAC-{token_urlsafe(4).upper()}"
    booking.access_starts_at = booking.starts_at - timedelta(minutes=15)
    booking.access_ends_at = booking.ends_at + timedelta(minutes=15)
    booking.conflict_note = append_note(
        booking.conflict_note,
        "Payment received; booking confirmed with access window.",
    )


def facility_checkout_session_id(invoice_id: UUID, provider: str) -> str:
    digest = sha256(f"facility-hire:{invoice_id}:{provider}".encode()).hexdigest()[:24]
    return f"fac_{digest}"


def facility_checkout_url(base_url: str, session_id: str, invoice_id: UUID, booking_id: UUID, provider: str) -> str:
    normalized_base = base_url.rstrip("/") or "/pay/sessions"
    query = urlencode(
        {
            "kind": "facility",
            "invoice_id": str(invoice_id),
            "booking_id": str(booking_id),
            "provider": provider,
        }
    )
    return f"{normalized_base}/{session_id}?{query}"


def invoice_open_amount(invoice: FinanceInvoice) -> Decimal:
    return max((invoice.amount_due - invoice.amount_paid).quantize(Decimal("0.01")), Decimal("0"))


async def get_facility_checkout_records(
    db: AsyncSession,
    invoice_id: UUID,
    booking_id: UUID,
) -> tuple[FinanceInvoice, FacilityBooking]:
    invoice = await db.get(FinanceInvoice, invoice_id)
    booking = await db.get(FacilityBooking, booking_id)
    if (
        invoice is None
        or booking is None
        or booking.finance_invoice_id != invoice.id
        or booking.organization_id != invoice.organization_id
        or booking.booking_source not in {"public_site", "waitlist"}
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility checkout session not found")
    return invoice, booking


def facility_hire_checkout_read(
    invoice: FinanceInvoice,
    booking: FacilityBooking,
    provider: str,
    session_id: str,
) -> FacilityHireHostedCheckoutRead:
    open_amount = invoice_open_amount(invoice)
    return FacilityHireHostedCheckoutRead(
        invoice_id=invoice.id,
        booking_id=booking.id,
        invoice_number=invoice.invoice_number,
        organization_id=invoice.organization_id,
        facility_id=booking.facility_id,
        title=invoice.title,
        memo=invoice.memo,
        due_on=invoice.due_on,
        amount_due=invoice.amount_due,
        amount_paid=invoice.amount_paid,
        open_amount=open_amount,
        currency=invoice.currency,
        status=invoice.status.value,
        provider=provider,
        session_id=session_id,
        session_status="paid" if open_amount <= 0 else "open",
        client_reference=f"facility-hire:{booking.id}",
        payment_methods=["card", "mobile_money", "bank_transfer"],
        settlement_endpoint=f"/api/v1/assets/facility-checkout-sessions/{session_id}/settle",
        checkout_summary=f"{booking.title} from {booking.starts_at:%Y-%m-%d %H:%M} to {booking.ends_at:%H:%M}.",
    )


def facility_settlement_read(
    invoice: FinanceInvoice,
    booking: FacilityBooking,
    payment: FinancePayment | None,
    provider: str,
) -> FacilityHireCheckoutSettlementRead:
    open_amount = invoice_open_amount(invoice)
    return FacilityHireCheckoutSettlementRead(
        booking_id=booking.id,
        invoice_id=invoice.id,
        payment_id=payment.id if payment else None,
        provider=provider,
        amount_paid=invoice.amount_paid,
        open_amount=open_amount,
        currency=invoice.currency,
        invoice_status=invoice.status.value,
        booking_status=booking.status,
        payment_status=booking.payment_status,
        session_status="paid" if open_amount <= 0 else "open",
        access_code=booking.access_code,
        access_starts_at=booking.access_starts_at,
        access_ends_at=booking.access_ends_at,
    )


def facility_waitlist_read(entry: FacilityBookingWaitlistEntry) -> FacilityBookingWaitlistRead:
    return FacilityBookingWaitlistRead(
        id=entry.id,
        organization_id=entry.organization_id,
        facility_id=entry.facility_id,
        offered_booking_id=entry.offered_booking_id,
        activity_type=entry.activity_type,
        title=entry.title,
        desired_starts_at=entry.desired_starts_at,
        desired_ends_at=entry.desired_ends_at,
        requester_name=entry.requester_name,
        requester_email=entry.requester_email,
        requester_phone=entry.requester_phone,
        expected_attendees=entry.expected_attendees,
        insurance_certificate_ref=entry.insurance_certificate_ref,
        special_requirements=entry.special_requirements,
        add_ons=entry.add_ons,
        status=entry.status,
        priority_score=entry.priority_score,
        notified_at=entry.notified_at,
        expires_at=entry.expires_at,
        notes=entry.notes,
    )


def maintenance_work_order_read(work_order: MaintenanceWorkOrder) -> MaintenanceWorkOrderRead:
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


def facility_maintenance_schedule_read(schedule: FacilityMaintenanceSchedule) -> FacilityMaintenanceScheduleRead:
    return FacilityMaintenanceScheduleRead(
        id=schedule.id,
        organization_id=schedule.organization_id,
        facility_id=schedule.facility_id,
        equipment_item_id=schedule.equipment_item_id,
        assigned_to_person_id=schedule.assigned_to_person_id,
        title=schedule.title,
        category=schedule.category,
        frequency=schedule.frequency,
        interval_days=schedule.interval_days,
        next_due_at=schedule.next_due_at,
        last_generated_at=schedule.last_generated_at,
        last_completed_at=schedule.last_completed_at,
        vendor=schedule.vendor,
        estimated_cost=schedule.estimated_cost,
        safety_related=schedule.safety_related,
        compliance_reference=schedule.compliance_reference,
        condition_metric=schedule.condition_metric,
        condition_threshold=schedule.condition_threshold,
        warranty_expires_on=schedule.warranty_expires_on,
        status=schedule.status,
        notes=schedule.notes,
    )


def facility_lease_agreement_read(lease: FacilityLeaseAgreement) -> FacilityLeaseAgreementRead:
    return FacilityLeaseAgreementRead(
        id=lease.id,
        organization_id=lease.organization_id,
        facility_id=lease.facility_id,
        finance_invoice_id=lease.finance_invoice_id,
        lessor_name=lease.lessor_name,
        lessee_name=lease.lessee_name,
        lessee_contact_name=lease.lessee_contact_name,
        lessee_contact_email=lease.lessee_contact_email,
        usage_terms=lease.usage_terms,
        included_services=lease.included_services,
        extra_charges=lease.extra_charges,
        starts_on=lease.starts_on,
        ends_on=lease.ends_on,
        monthly_rent=lease.monthly_rent,
        security_deposit=lease.security_deposit,
        deposit_status=lease.deposit_status,
        next_invoice_on=lease.next_invoice_on,
        auto_renew=lease.auto_renew,
        renewal_notice_on=lease.renewal_notice_on,
        status=lease.status,
        compliance_status=lease.compliance_status,
        compliance_notes=lease.compliance_notes,
        document_url=lease.document_url,
        signed_at=lease.signed_at,
        terminated_at=lease.terminated_at,
        version=lease.version,
        notes=lease.notes,
    )


def facility_lease_invoice_number(lease: FacilityLeaseAgreement, period_start: date) -> str:
    return f"FLEASE-{period_start:%Y%m}-{str(lease.id)[:8]}".upper()


def facility_lease_invoice_memo(
    lease: FacilityLeaseAgreement,
    payload: FacilityLeaseInvoiceCreate,
) -> str:
    parts = [
        f"Lease period {payload.period_start.isoformat()} to {payload.period_end.isoformat()}.",
        f"Base rent {lease.monthly_rent}.",
    ]
    if payload.extra_amount > 0:
        parts.append(f"Extra charges {payload.extra_amount}: {lease.extra_charges or 'per agreement'}.")
    if payload.late_fee > 0:
        parts.append(f"Late fee {payload.late_fee}.")
    if lease.included_services:
        parts.append(f"Included services: {lease.included_services}.")
    return " ".join(parts)


def add_month(value: date) -> date:
    year = value.year + (1 if value.month == 12 else 0)
    month = 1 if value.month == 12 else value.month + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def facility_access_credential_read(credential: FacilityAccessCredential) -> FacilityAccessCredentialRead:
    return FacilityAccessCredentialRead(
        id=credential.id,
        organization_id=credential.organization_id,
        facility_id=credential.facility_id,
        booking_id=credential.booking_id,
        lease_agreement_id=credential.lease_agreement_id,
        person_id=credential.person_id,
        guest_name=credential.guest_name,
        guest_email=credential.guest_email,
        credential_type=credential.credential_type,
        access_code=credential.access_code,
        access_level=credential.access_level,
        zones=credential.zones,
        valid_from=credential.valid_from,
        valid_until=credential.valid_until,
        status=credential.status,
        max_uses=credential.max_uses,
        uses_count=credential.uses_count,
        last_used_at=credential.last_used_at,
        issued_by_person_id=credential.issued_by_person_id,
        notes=credential.notes,
    )


def facility_access_event_read(event: FacilityAccessEvent) -> FacilityAccessEventRead:
    return FacilityAccessEventRead(
        id=event.id,
        organization_id=event.organization_id,
        facility_id=event.facility_id,
        credential_id=event.credential_id,
        booking_id=event.booking_id,
        lease_agreement_id=event.lease_agreement_id,
        access_code=event.access_code,
        reader_id=event.reader_id,
        reader_location=event.reader_location,
        subject_summary=event.subject_summary,
        decision=event.decision,
        reason=event.reason,
        occurred_at=event.occurred_at,
        notes=event.notes,
    )


def facility_access_device_read(device: FacilityAccessDevice) -> FacilityAccessDeviceRead:
    return FacilityAccessDeviceRead(
        id=device.id,
        organization_id=device.organization_id,
        facility_id=device.facility_id,
        device_id=device.device_id,
        name=device.name,
        location=device.location,
        device_type=device.device_type,
        unlock_method=device.unlock_method,
        status=device.status,
        last_seen_at=device.last_seen_at,
        last_scan_at=device.last_scan_at,
        last_health_at=device.last_health_at,
        battery_percent=device.battery_percent,
        firmware_version=device.firmware_version,
        network_status=device.network_status,
        notes=device.notes,
    )


def facility_access_command_read(command: FacilityAccessCommand) -> FacilityAccessCommandRead:
    return FacilityAccessCommandRead(
        id=command.id,
        organization_id=command.organization_id,
        facility_id=command.facility_id,
        access_device_id=command.access_device_id,
        access_event_id=command.access_event_id,
        credential_id=command.credential_id,
        command_type=command.command_type,
        command_payload=command.command_payload,
        command_signature=command.command_signature,
        status=command.status,
        issued_at=command.issued_at,
        valid_until=command.valid_until,
        acknowledged_at=command.acknowledged_at,
        requested_by_person_id=command.requested_by_person_id,
        notes=command.notes,
    )


def facility_access_lockdown_read(lockdown: FacilityAccessLockdown) -> FacilityAccessLockdownRead:
    return FacilityAccessLockdownRead(
        id=lockdown.id,
        organization_id=lockdown.organization_id,
        facility_id=lockdown.facility_id,
        mode=lockdown.mode,
        status=lockdown.status,
        reason=lockdown.reason,
        command_count=lockdown.command_count,
        activated_at=lockdown.activated_at,
        resolved_at=lockdown.resolved_at,
        issued_by_person_id=lockdown.issued_by_person_id,
        notes=lockdown.notes,
    )


def facility_access_window(
    payload: FacilityAccessCredentialCreate,
    booking: FacilityBooking | None,
    lease: FacilityLeaseAgreement | None,
) -> tuple[datetime, datetime]:
    if payload.valid_from is not None and payload.valid_until is not None:
        if payload.valid_until <= payload.valid_from:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="valid_until must be after valid_from")
        return payload.valid_from, payload.valid_until
    if booking is not None:
        valid_from = booking.access_starts_at or booking.starts_at - timedelta(minutes=15)
        valid_until = booking.access_ends_at or booking.ends_at + timedelta(minutes=15)
        return normalize_datetime(valid_from), normalize_datetime(valid_until)
    if lease is not None:
        return (
            datetime.combine(lease.starts_on, datetime.min.time(), tzinfo=UTC),
            datetime.combine(lease.ends_on, datetime.max.time(), tzinfo=UTC),
        )
    now = datetime.now(UTC)
    return payload.valid_from or now, payload.valid_until or now + timedelta(hours=8)


def facility_access_decision(
    credential: FacilityAccessCredential | None,
    occurred_at: datetime,
) -> tuple[str, str]:
    if credential is None:
        return "denied", "No matching active credential was found for this facility."
    now = normalize_datetime(occurred_at)
    if credential.status != "active":
        return "denied", f"Credential is {credential.status}."
    if now < normalize_datetime(credential.valid_from):
        return "denied", "Credential is not active yet."
    if now > normalize_datetime(credential.valid_until):
        credential.status = "expired"
        return "denied", "Credential has expired."
    if credential.max_uses is not None and credential.uses_count >= credential.max_uses:
        return "denied", "Credential use limit has been reached."
    return "granted", "Access granted."


def facility_access_subject(credential: FacilityAccessCredential | None) -> str | None:
    if credential is None:
        return None
    if credential.guest_name:
        return credential.guest_name
    if credential.person_id:
        return f"person:{credential.person_id}"
    if credential.booking_id:
        return f"booking:{credential.booking_id}"
    if credential.lease_agreement_id:
        return f"lease:{credential.lease_agreement_id}"
    return credential.access_level


def facility_access_recommendation(
    denials: int,
    expiring: list[FacilityAccessCredential],
) -> str:
    if denials >= 3:
        return "Review denied scans and reader placement before peak facility use."
    if expiring:
        return "Renew or revoke expiring credentials before the next scheduled access window."
    return "Access control is stable; keep temporary guest credentials time-boxed."


def validate_facility_access_device_key(device: FacilityAccessDevice, api_key: str | None) -> None:
    if device.status not in {"active", "maintenance"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Facility access device is not active")
    if not api_key or not compare_digest(device.api_key_hash, hash_reader_key(api_key)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid facility access device key")


def update_facility_access_device_health_fields(
    device: FacilityAccessDevice,
    *,
    checked_at: datetime,
    battery_percent: int | None,
    firmware_version: str | None,
    network_status: str | None,
) -> None:
    if battery_percent is not None:
        device.battery_percent = battery_percent
    if firmware_version:
        device.firmware_version = firmware_version
    if network_status:
        device.network_status = network_status.strip().lower()
    if battery_percent is not None or firmware_version or network_status:
        device.last_health_at = checked_at


def facility_access_command_from_event(
    device: FacilityAccessDevice,
    event: FacilityAccessEvent,
    credential: FacilityAccessCredential | None,
    api_key: str,
    issued_at: datetime,
) -> FacilityAccessCommand:
    command_type = "unlock" if event.decision == "granted" else "deny"
    valid_until = issued_at + timedelta(seconds=30 if command_type == "unlock" else 10)
    payload = {
        "command_type": command_type,
        "device_id": device.device_id,
        "facility_id": str(device.facility_id),
        "event_id": str(event.id),
        "credential_id": str(credential.id) if credential else None,
        "subject": facility_access_subject(credential),
        "unlock_method": device.unlock_method,
        "issued_at": issued_at.isoformat(),
        "valid_until": valid_until.isoformat(),
        "nonce": token_urlsafe(12),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    signature = facility_access_command_signature(api_key, encoded)
    return FacilityAccessCommand(
        organization_id=device.organization_id,
        facility_id=device.facility_id,
        access_device_id=device.id,
        access_event_id=event.id,
        credential_id=credential.id if credential else None,
        command_type=command_type,
        command_payload=encoded,
        command_signature=signature,
        status="issued",
        issued_at=issued_at,
        valid_until=valid_until,
        notes=event.reason,
    )


def facility_access_command_signature(api_key: str, payload: str) -> str:
    digest = hmac.new(api_key.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()
    return f"sha256={digest}"


def facility_access_device_health_recommendation(device: FacilityAccessDevice) -> str:
    if device.status != "active":
        return "Device is not active; keep a staffed manual entry fallback until service is restored."
    if device.battery_percent is not None and device.battery_percent < 20:
        return "Battery is low; charge or swap the controller before the next booking window."
    if device.network_status and device.network_status not in {"online", "good", "connected"}:
        return "Network status needs attention before relying on unattended entry."
    return "Device is ready for controlled access windows."


def facility_access_lockdown_command(
    lockdown: FacilityAccessLockdown,
    device: FacilityAccessDevice,
    valid_seconds: int,
    issued_at: datetime,
) -> FacilityAccessCommand:
    command_type = lockdown.mode
    valid_until = issued_at + timedelta(seconds=valid_seconds)
    payload = {
        "command_type": command_type,
        "device_id": device.device_id,
        "facility_id": str(device.facility_id),
        "lockdown_id": str(lockdown.id),
        "reason": lockdown.reason,
        "issued_at": issued_at.isoformat(),
        "valid_until": valid_until.isoformat(),
        "nonce": token_urlsafe(12),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    signature = facility_access_command_signature(device.api_key_hash, encoded)
    return FacilityAccessCommand(
        organization_id=device.organization_id,
        facility_id=device.facility_id,
        access_device_id=device.id,
        command_type=command_type,
        command_payload=encoded,
        command_signature=signature,
        status="issued",
        issued_at=issued_at,
        valid_until=valid_until,
        requested_by_person_id=lockdown.issued_by_person_id,
        notes=lockdown.reason,
    )


def facility_access_lockdown_recommendation(lockdown: FacilityAccessLockdown, device_count: int) -> str:
    if lockdown.mode == "lockdown":
        return f"Lockdown command issued to {device_count} active device(s); verify staff have started emergency response."
    return f"Unlock-all command issued to {device_count} active device(s); confirm all entrances are staffed before reopening."


def facility_access_lockdown_dashboard_recommendation(
    lockdowns: list[FacilityAccessLockdown],
    devices: list[FacilityAccessDevice],
) -> str:
    if any(lockdown.status == "active" for lockdown in lockdowns):
        return "Active lockdown in effect; keep emergency communications and staffed manual override ready."
    if not devices:
        return "No active access-control devices are available for remote lockdown."
    return "Remote lockdown coverage is ready; test commands during scheduled safety drills."


async def persist_facility_utility_reading(
    db: AsyncSession,
    meter: FacilityUtilityMeter,
    *,
    reading_value: Decimal,
    usage_delta: Decimal | None,
    cost_estimate: Decimal | None,
    reading_at: datetime,
    source: str,
    external_reference: str | None,
    notes: str | None,
    signature_validated: bool,
) -> FacilityUtilityReadingResultRead:
    if meter.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Facility utility meter is not active")
    normalized_at = normalize_datetime(reading_at)
    computed_delta = facility_utility_usage_delta(meter, reading_value, usage_delta)
    computed_cost = facility_utility_cost_estimate(meter, computed_delta, cost_estimate)
    anomaly_level, alert_type, message, action = facility_utility_anomaly(meter, computed_delta, normalized_at)
    reading = FacilityUtilityReading(
        organization_id=meter.organization_id,
        facility_id=meter.facility_id,
        utility_meter_id=meter.id,
        meter_id=meter.meter_id,
        reading_value=reading_value,
        usage_delta=computed_delta,
        unit=meter.unit,
        cost_estimate=computed_cost,
        reading_at=normalized_at,
        source=source.strip().lower(),
        anomaly_level=anomaly_level,
        external_reference=external_reference,
        notes=notes,
    )
    db.add(reading)
    await db.flush()
    alert: FacilityUtilityAlert | None = None
    if anomaly_level != "normal":
        alert = FacilityUtilityAlert(
            organization_id=meter.organization_id,
            facility_id=meter.facility_id,
            utility_meter_id=meter.id,
            utility_reading_id=reading.id,
            alert_type=alert_type,
            severity=anomaly_level,
            status="open",
            message=message,
            recommended_action=action,
            triggered_at=normalized_at,
        )
        db.add(alert)
    if meter.last_reading_at is None or normalized_at >= normalize_datetime(meter.last_reading_at):
        meter.last_reading_at = normalized_at
        meter.last_value = reading_value
        meter.last_cost_estimate = computed_cost
    await db.commit()
    await db.refresh(meter)
    await db.refresh(reading)
    if alert is not None:
        await db.refresh(alert)
    return FacilityUtilityReadingResultRead(
        meter=facility_utility_meter_read(meter),
        reading=facility_utility_reading_read(reading),
        alert=facility_utility_alert_read(alert) if alert else None,
        signature_validated=signature_validated,
    )


def facility_utility_meter_read(meter: FacilityUtilityMeter) -> FacilityUtilityMeterRead:
    return FacilityUtilityMeterRead(
        id=meter.id,
        organization_id=meter.organization_id,
        facility_id=meter.facility_id,
        meter_id=meter.meter_id,
        name=meter.name,
        utility_type=meter.utility_type,
        unit=meter.unit,
        location=meter.location,
        provider=meter.provider,
        account_reference=meter.account_reference,
        status=meter.status,
        cost_per_unit=meter.cost_per_unit,
        target_daily_usage=meter.target_daily_usage,
        last_reading_at=meter.last_reading_at,
        last_value=meter.last_value,
        last_cost_estimate=meter.last_cost_estimate,
        notes=meter.notes,
    )


def facility_utility_reading_read(reading: FacilityUtilityReading) -> FacilityUtilityReadingRead:
    return FacilityUtilityReadingRead(
        id=reading.id,
        organization_id=reading.organization_id,
        facility_id=reading.facility_id,
        utility_meter_id=reading.utility_meter_id,
        meter_id=reading.meter_id,
        reading_value=reading.reading_value,
        usage_delta=reading.usage_delta,
        unit=reading.unit,
        cost_estimate=reading.cost_estimate,
        reading_at=reading.reading_at,
        source=reading.source,
        anomaly_level=reading.anomaly_level,
        external_reference=reading.external_reference,
        notes=reading.notes,
    )


def facility_utility_alert_read(alert: FacilityUtilityAlert) -> FacilityUtilityAlertRead:
    return FacilityUtilityAlertRead(
        id=alert.id,
        organization_id=alert.organization_id,
        facility_id=alert.facility_id,
        utility_meter_id=alert.utility_meter_id,
        utility_reading_id=alert.utility_reading_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        status=alert.status,
        message=alert.message,
        recommended_action=alert.recommended_action,
        triggered_at=alert.triggered_at,
        resolved_at=alert.resolved_at,
        notes=alert.notes,
    )


def validate_facility_utility_meter_key(meter: FacilityUtilityMeter, api_key: str | None) -> None:
    if meter.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Facility utility meter is not active")
    if not api_key or not compare_digest(meter.api_key_hash, hash_reader_key(api_key)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid facility utility meter key")


def facility_utility_usage_delta(
    meter: FacilityUtilityMeter,
    reading_value: Decimal,
    supplied_delta: Decimal | None,
) -> Decimal | None:
    if supplied_delta is not None:
        return supplied_delta
    if meter.last_value is None:
        return Decimal("0")
    return reading_value - meter.last_value


def facility_utility_cost_estimate(
    meter: FacilityUtilityMeter,
    usage_delta: Decimal | None,
    supplied_cost: Decimal | None,
) -> Decimal | None:
    if supplied_cost is not None:
        return supplied_cost
    if usage_delta is None or meter.cost_per_unit is None:
        return None
    return (usage_delta * meter.cost_per_unit).quantize(Decimal("0.01"))


def facility_utility_anomaly(
    meter: FacilityUtilityMeter,
    usage_delta: Decimal | None,
    reading_at: datetime,
) -> tuple[str, str, str, str]:
    if usage_delta is None:
        return ("normal", "normal", "Utility reading recorded.", "Keep monitoring scheduled usage.")
    if usage_delta < 0:
        return (
            "critical",
            "meter_reset_or_bad_reading",
            f"{meter.name} reported a negative usage delta.",
            "Inspect the meter for reset, rollover, tampering, or bad gateway data.",
        )
    if meter.target_daily_usage is not None and meter.target_daily_usage > 0:
        expected = meter.target_daily_usage * facility_utility_elapsed_days(meter, reading_at)
        if expected > 0 and usage_delta > expected * Decimal("2"):
            return (
                "critical",
                "usage_spike",
                f"{meter.name} usage is more than double the target for this interval.",
                "Check for leaks, lights left on, abnormal irrigation, or equipment running after hours.",
            )
        if expected > 0 and usage_delta > expected * Decimal("1.5"):
            return (
                "warning",
                "usage_above_target",
                f"{meter.name} usage is materially above target for this interval.",
                "Review bookings, weather, and maintenance activity before the next reading.",
            )
    return ("normal", "normal", "Utility reading recorded.", "Keep monitoring scheduled usage.")


def facility_utility_elapsed_days(meter: FacilityUtilityMeter, reading_at: datetime) -> Decimal:
    if meter.last_reading_at is None:
        return Decimal("1")
    seconds = max((reading_at - normalize_datetime(meter.last_reading_at)).total_seconds(), 0)
    return max(Decimal(str(seconds / 86400)), Decimal("1"))


def facility_utility_dashboard_recommendation(
    alerts: list[FacilityUtilityAlert],
    meters: list[FacilityUtilityMeter],
) -> str:
    if any(alert.severity == "critical" for alert in alerts):
        return "Investigate critical utility anomalies before approving additional high-load bookings."
    if alerts:
        return "Review open utility alerts and compare them with bookings, weather, and maintenance activity."
    if any(meter.last_reading_at is None for meter in meters):
        return "Seed initial readings for all active meters so cost and usage trends become reliable."
    return "Utility monitoring is stable; keep gateway readings on a daily cadence."


def clubhouse_amenity_read(amenity: ClubhouseAmenity) -> ClubhouseAmenityRead:
    return ClubhouseAmenityRead(
        id=amenity.id,
        organization_id=amenity.organization_id,
        facility_id=amenity.facility_id,
        name=amenity.name,
        amenity_type=amenity.amenity_type,
        location=amenity.location,
        capacity=amenity.capacity,
        reservation_required=amenity.reservation_required,
        hourly_rate=amenity.hourly_rate,
        status=amenity.status,
        notes=amenity.notes,
    )


def clubhouse_visit_read(visit: ClubhouseVisit) -> ClubhouseVisitRead:
    return ClubhouseVisitRead(
        id=visit.id,
        organization_id=visit.organization_id,
        facility_id=visit.facility_id,
        person_id=visit.person_id,
        access_event_id=visit.access_event_id,
        guest_name=visit.guest_name,
        guest_email=visit.guest_email,
        check_in_at=visit.check_in_at,
        check_out_at=visit.check_out_at,
        status=visit.status,
        party_size=visit.party_size,
        purpose=visit.purpose,
        notes=visit.notes,
    )


def clubhouse_reservation_read(
    reservation: ClubhouseAmenityReservation,
) -> ClubhouseAmenityReservationRead:
    return ClubhouseAmenityReservationRead(
        id=reservation.id,
        organization_id=reservation.organization_id,
        facility_id=reservation.facility_id,
        amenity_id=reservation.amenity_id,
        person_id=reservation.person_id,
        guest_name=reservation.guest_name,
        starts_at=reservation.starts_at,
        ends_at=reservation.ends_at,
        status=reservation.status,
        party_size=reservation.party_size,
        expected_fee=reservation.expected_fee,
        notes=reservation.notes,
    )


async def clubhouse_current_occupancy(
    db: AsyncSession,
    organization_id: UUID,
    facility_id: UUID,
) -> int:
    visits = await db.scalars(
        select(ClubhouseVisit)
        .where(ClubhouseVisit.organization_id == organization_id)
        .where(ClubhouseVisit.facility_id == facility_id)
        .where(ClubhouseVisit.status == "checked_in")
    )
    return sum(visit.party_size for visit in visits.all())


async def clubhouse_amenity_reserved_party_size(
    db: AsyncSession,
    amenity_id: UUID,
    starts_at: datetime,
    ends_at: datetime,
) -> int:
    rows = await db.scalars(
        select(ClubhouseAmenityReservation)
        .where(ClubhouseAmenityReservation.amenity_id == amenity_id)
        .where(ClubhouseAmenityReservation.status.in_(["reserved", "checked_in"]))
        .where(ClubhouseAmenityReservation.starts_at < ends_at)
        .where(ClubhouseAmenityReservation.ends_at > starts_at)
    )
    return sum(row.party_size for row in rows.all())


def clubhouse_amenity_fee(
    amenity: ClubhouseAmenity,
    payload: ClubhouseAmenityReservationCreate,
) -> Decimal | None:
    if amenity.hourly_rate is None:
        return None
    seconds = max((payload.ends_at - payload.starts_at).total_seconds(), 0)
    hours = Decimal(str(seconds / 3600)).quantize(Decimal("0.01"))
    return (amenity.hourly_rate * hours).quantize(Decimal("0.01"))


def clubhouse_popular_amenities(
    amenities: list[ClubhouseAmenity],
    reservations: list[ClubhouseAmenityReservation],
) -> list[str]:
    names = {amenity.id: amenity.name for amenity in amenities}
    counts: dict[str, int] = {}
    for reservation in reservations:
        name = names.get(reservation.amenity_id, str(reservation.amenity_id))
        counts[name] = counts.get(name, 0) + reservation.party_size
    if not counts:
        return [amenity.name for amenity in amenities[:3]]
    return [name for name, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:3]]


def clubhouse_dashboard_recommendation(
    occupancy: int,
    capacity: int | None,
    reservations: list[ClubhouseAmenityReservation],
    amenities: list[ClubhouseAmenity],
) -> str:
    if capacity is not None and capacity > 0 and occupancy >= int(capacity * 0.9):
        return "Clubhouse is near capacity; pause guest entry and prioritize reservation holders."
    if reservations and not amenities:
        return "Reservations exist without configured amenities; review clubhouse setup."
    if not amenities:
        return "Add bookable clubhouse amenities so members can reserve spaces without staff back-and-forth."
    if reservations:
        return "Clubhouse operations are active; monitor check-ins against reservation capacity."
    return "Clubhouse is ready; promote bookable amenities to members and families."


def maintenance_work_order_notes(schedule: FacilityMaintenanceSchedule) -> str:
    parts = [schedule.notes or f"Generated from {schedule.frequency} preventive maintenance schedule."]
    if schedule.condition_metric or schedule.condition_threshold:
        parts.append(
            f"Condition trigger: {schedule.condition_metric or 'metric'} "
            f"{schedule.condition_threshold or 'threshold'}."
        )
    if schedule.warranty_expires_on:
        parts.append(f"Warranty expires on {schedule.warranty_expires_on.isoformat()}.")
    return " ".join(parts)


def advance_schedule_due_at(next_due_at: datetime, interval_days: int) -> datetime:
    due_at = normalize_datetime(next_due_at) + timedelta(days=interval_days)
    now = datetime.now(UTC)
    interval = timedelta(days=interval_days)
    while due_at <= now:
        due_at += interval
    return due_at


def facility_maintenance_costs(
    facilities: list[Facility],
    work_orders: list[MaintenanceWorkOrder],
) -> list[FacilityMaintenanceCostRead]:
    costs: list[FacilityMaintenanceCostRead] = []
    for facility in facilities:
        facility_orders = [order for order in work_orders if order.facility_id == facility.id]
        actual_cost = sum((order.actual_cost or Decimal("0") for order in facility_orders), Decimal("0")).quantize(Decimal("0.01"))
        estimated_open = sum(
            (
                order.estimated_cost or Decimal("0")
                for order in facility_orders
                if order.status != WorkOrderStatus.COMPLETED
            ),
            Decimal("0"),
        ).quantize(Decimal("0.01"))
        budget_remaining = (
            (facility.maintenance_budget - actual_cost).quantize(Decimal("0.01"))
            if facility.maintenance_budget is not None
            else None
        )
        costs.append(
            FacilityMaintenanceCostRead(
                facility_id=facility.id,
                facility_name=facility.name,
                maintenance_budget=facility.maintenance_budget,
                actual_cost=actual_cost,
                estimated_open_cost=estimated_open,
                net_budget_remaining=budget_remaining,
            )
        )
    return sorted(costs, key=lambda item: item.actual_cost + item.estimated_open_cost, reverse=True)


def facility_maintenance_recommendation(
    overdue_count: int,
    safety_due_count: int,
    budget_remaining: Decimal | None,
) -> str:
    if safety_due_count:
        return "Prioritize safety-related preventive work before approving heavy facility use."
    if overdue_count:
        return "Clear overdue preventive tasks and review staffing or vendor capacity."
    if budget_remaining is not None and budget_remaining < 0:
        return "Maintenance spend is above budget; review vendor costs and defer non-critical tasks."
    return "Preventive schedule is current; keep generating work orders ahead of peak usage windows."


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
