from datetime import UTC, datetime
from secrets import token_urlsafe
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.agent import Agent, AgentTask
from app.models.communication import CommunicationMessage, CommunicationTemplate
from app.models.enums import ConsentRequestStatus, MemberSubjectType, MembershipRole
from app.models.event import ConsentRequest, Event
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.models.performance import AthletePerformanceObservation, PerformanceMetricDefinition
from app.models.team import AthleteProfile, GuardianRelationship, Team, TeamRosterEntry
from app.models.training import TrainingDrill, TrainingPlan, TrainingSessionPlan
from app.schemas.billing import (
    BillingEntitlementRead,
    BillingPlanRead,
    BillingSummaryRead,
    SaaSInvoiceRead,
    SubscriptionRead,
    UsageMeterRead,
    UsageRecordCreate,
    UsageRecordRead,
)
from app.schemas.developer import (
    DeveloperApiKeyInspectionRead,
    DeveloperConsentRequestCreate,
    DeveloperConsentRequestRead,
    DeveloperGuardianRelationshipCreate,
    DeveloperGuardianRelationshipRead,
    DeveloperPersonCreate,
    DeveloperPersonRead,
)
from app.schemas.agent import AgentRead, AgentTaskCreate, AgentTaskRead
from app.schemas.communication import (
    CommunicationDispatchSummary,
    CommunicationMessageCreate,
    CommunicationMessageRead,
    CommunicationTemplateCreate,
    CommunicationTemplateRead,
    MessageRecipientRead,
)
from app.schemas.event import AttendanceRecordRead, AttendanceRecordUpsert, EventCreate, EventRead
from app.schemas.organization import OrganizationRead
from app.schemas.performance import (
    MetricDefinitionRead,
    PerformanceObservationCreate,
    PerformanceObservationRead,
)
from app.schemas.team import TeamCreate, TeamMemberAdd, TeamRead, TeamRosterEntryRead
from app.schemas.training import (
    TrainingAvailabilityCreate,
    TrainingAvailabilityRead,
    TrainingCalendarArtifactRead,
    TrainingDrillCreate,
    TrainingDrillRead,
    TrainingPlanCreate,
    TrainingPlanItemCreate,
    TrainingPlanItemRead,
    TrainingPlanRead,
    TrainingSessionFeedbackCreate,
    TrainingSessionFeedbackRead,
    TrainingSessionPlanCreate,
    TrainingSessionPlanRead,
)
from app.services.authz.service import (
    AuthorizationService,
    Relationship,
    get_authorization_service,
)
from app.services.agents import (
    list_agent_tasks,
    list_agents as list_ai_agents,
    queue_agent_task,
)
from app.services.billing import (
    billing_summary,
    list_entitlements,
    list_invoices,
    list_plans,
    list_subscriptions,
    list_usage_meters,
    list_usage_records,
    record_usage,
)
from app.services.communications import (
    create_message,
    create_template,
    dispatch_message,
    get_message,
    list_messages,
    list_recipients,
    list_templates,
)
from app.services.developer import (
    deliver_developer_webhook_event,
    ensure_developer_api_scope,
    inspect_developer_api_key,
)
from app.services.events import list_attendance, list_events, record_attendance
from app.services.organizations import organization_member_relation
from app.services.performance import list_metric_definitions, list_observations
from app.services.safeguarding import consent_destination, hash_token, normalized_scope_id, utc_now
from app.services.teams import list_teams_for_organization, team_member_relation
from app.services.training import (
    add_training_plan_item,
    create_training_plan,
    create_training_session_plan,
    export_training_calendar_artifact,
    list_training_drills,
    list_training_plan_items,
    list_training_plans,
    list_training_session_feedback,
    list_training_session_plans,
    record_training_session_feedback,
    suggest_training_availability,
)

router = APIRouter(prefix="/sdk", tags=["sdk"])


def read_model(model, schema_type):
    return schema_type(**{name: getattr(model, name) for name in schema_type.model_fields})


def ensure_developer_api_has_scope(
    credential: DeveloperApiKeyInspectionRead,
    required_scopes: set[str],
) -> None:
    granted_scopes = set(credential.scopes)
    if "admin:*" not in granted_scopes and granted_scopes.isdisjoint(required_scopes):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key scope is insufficient")


async def get_sdk_credential(
    request: Request,
    x_afrolete_api_key: str = Header(alias="X-Afrolete-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> DeveloperApiKeyInspectionRead:
    return await inspect_developer_api_key(db, x_afrolete_api_key, request.client.host if request.client else None)


def to_organization_read(organization: Organization) -> OrganizationRead:
    return OrganizationRead(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        organization_type=organization.organization_type,
        association_level=organization.association_level,
        country_code=organization.country_code,
        primary_sport=organization.primary_sport,
        mission=organization.mission,
        public_name=organization.public_name,
        contact_email=organization.contact_email,
        contact_phone=organization.contact_phone,
        website_url=organization.website_url,
        subdomain=organization.subdomain,
        logo_url=organization.logo_url,
        brand_primary_color=organization.brand_primary_color,
        brand_secondary_color=organization.brand_secondary_color,
        my_roles=[],
    )


def to_drill_read(drill: TrainingDrill) -> TrainingDrillRead:
    return TrainingDrillRead(
        id=drill.id,
        organization_id=drill.organization_id,
        sport=drill.sport,
        name=drill.name,
        focus_area=drill.focus_area,
        category=drill.category,
        min_age=drill.min_age,
        max_age=drill.max_age,
        equipment=drill.equipment,
        description=drill.description,
        coaching_points=drill.coaching_points,
        default_duration_minutes=drill.default_duration_minutes,
        default_intensity=drill.default_intensity,
        status=drill.status,
    )


def to_training_plan_read(plan: TrainingPlan) -> TrainingPlanRead:
    return TrainingPlanRead(
        id=plan.id,
        organization_id=plan.organization_id,
        team_id=plan.team_id,
        athlete_profile_id=plan.athlete_profile_id,
        created_by_person_id=plan.created_by_person_id,
        title=plan.title,
        focus_area=plan.focus_area,
        period_start=plan.period_start,
        period_end=plan.period_end,
        status=plan.status,
        ai_generated=plan.ai_generated,
        source_summary=plan.source_summary,
        load_guidance=plan.load_guidance,
        recovery_protocol=plan.recovery_protocol,
        progress_checkpoints=plan.progress_checkpoints,
    )


def to_training_plan_item_read(item) -> TrainingPlanItemRead:
    return TrainingPlanItemRead(
        id=item.id,
        plan_id=item.plan_id,
        drill_id=item.drill_id,
        sequence=item.sequence,
        day_label=item.day_label,
        title=item.title,
        focus_area=item.focus_area,
        duration_minutes=item.duration_minutes,
        intensity=item.intensity,
        notes=item.notes,
    )


def to_training_session_plan_read(session_plan: TrainingSessionPlan) -> TrainingSessionPlanRead:
    return TrainingSessionPlanRead(
        id=session_plan.id,
        organization_id=session_plan.organization_id,
        team_id=session_plan.team_id,
        plan_id=session_plan.plan_id,
        event_id=session_plan.event_id,
        title=session_plan.title,
        scheduled_for=session_plan.scheduled_for,
        duration_minutes=session_plan.duration_minutes,
        rpe_target=session_plan.rpe_target,
        load_score=session_plan.load_score,
        objectives=session_plan.objectives,
        status=session_plan.status,
    )


def to_training_session_feedback_read(row: dict[str, object]) -> TrainingSessionFeedbackRead:
    return TrainingSessionFeedbackRead(**row)


def to_communication_template_read(template: CommunicationTemplate) -> CommunicationTemplateRead:
    return CommunicationTemplateRead(
        id=template.id,
        organization_id=template.organization_id,
        name=template.name,
        message_type=template.message_type,
        channel=template.channel,
        subject_template=template.subject_template,
        body_template=template.body_template,
        variables=template.variables,
        status=template.status,
    )


def to_communication_message_read(
    message: CommunicationMessage,
    recipient_count: int = 0,
) -> CommunicationMessageRead:
    return CommunicationMessageRead(
        id=message.id,
        organization_id=message.organization_id,
        template_id=message.template_id,
        created_by_person_id=message.created_by_person_id,
        message_type=message.message_type,
        channel=message.channel,
        scope_type=message.scope_type,
        scope_id=message.scope_id,
        subject=message.subject,
        body=message.body,
        urgent=message.urgent,
        quiet_hours_override=message.quiet_hours_override,
        scheduled_for=message.scheduled_for,
        sent_at=message.sent_at,
        status=message.status,
        recipient_count=recipient_count,
        escalates_message_id=message.escalates_message_id,
        escalation_level=message.escalation_level,
        escalation_triggered_at=message.escalation_triggered_at,
        escalation_reason=message.escalation_reason,
    )


def to_message_recipient_read(recipient, person) -> MessageRecipientRead:
    return MessageRecipientRead(
        id=recipient.id,
        message_id=recipient.message_id,
        person_id=recipient.person_id,
        person_name=person.display_name,
        destination=recipient.destination,
        delivery_status=recipient.delivery_status,
        delivered_at=recipient.delivered_at,
        read_at=recipient.read_at,
        failure_reason=recipient.failure_reason,
    )


def to_event_read(event: Event) -> EventRead:
    return EventRead(
        id=event.id,
        organization_id=event.organization_id,
        team_id=event.team_id,
        event_type=event.event_type,
        title=event.title,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        timezone=event.timezone,
        venue_name=event.venue_name,
        notes=event.notes,
    )


def to_attendance_read(attendance, **policy_fields: object) -> AttendanceRecordRead:
    return AttendanceRecordRead(
        id=attendance.id,
        event_id=attendance.event_id,
        person_id=attendance.person_id,
        status=attendance.status,
        recorded_by_person_id=attendance.recorded_by_person_id,
        guardian_consent_id=attendance.guardian_consent_id,
        note=attendance.note,
        clearance_status=policy_fields.get("clearance_status"),
        medical_clearance_status=policy_fields.get("medical_clearance_status"),
        medical_clearance_id=policy_fields.get("medical_clearance_id"),
        medical_clearance_reason=policy_fields.get("medical_clearance_reason"),
        attendance_policy_code=policy_fields.get("attendance_policy_code"),
        attendance_policy_decision=policy_fields.get("attendance_policy_decision"),
        attendance_policy_warnings=list(policy_fields.get("attendance_policy_warnings") or []),
    )


def to_agent_read(agent: Agent) -> AgentRead:
    return AgentRead(
        id=agent.id,
        organization_id=agent.organization_id,
        name=agent.name,
        kind=agent.kind,
        purpose=agent.purpose,
        status=agent.status,
        model_policy=agent.model_policy,
    )


def to_agent_task_read(task: AgentTask) -> AgentTaskRead:
    approval_pending_count = max(
        int(task.approval_required_count or 0)
        - int(task.approval_approved_count or 0)
        - int(task.approval_rejected_count or 0),
        0,
    )
    return AgentTaskRead(
        id=task.id,
        agent_id=task.agent_id,
        organization_id=task.organization_id,
        task_type=task.task_type,
        title=task.title,
        status=task.status,
        requested_by_person_id=task.requested_by_person_id,
        input_ref=task.input_ref,
        output_ref=task.output_ref,
        review_notes=task.review_notes,
        review_assigned_to_person_id=task.review_assigned_to_person_id,
        review_due_at=task.review_due_at,
        review_priority=task.review_priority or "normal",
        review_assignment_notes=task.review_assignment_notes,
        approval_required_count=task.approval_required_count or 0,
        approval_approved_count=task.approval_approved_count or 0,
        approval_rejected_count=task.approval_rejected_count or 0,
        approval_pending_count=approval_pending_count,
        approval_status=task.approval_status or "not_requested",
        approval_last_decided_at=task.approval_last_decided_at,
        governance_policy_rule_id=task.governance_policy_rule_id,
        governance_policy_code=task.governance_policy_code,
        governance_policy_decision=task.governance_policy_decision,
        governance_policy_risk_level=task.governance_policy_risk_level,
        governance_policy_rationale=task.governance_policy_rationale,
    )


def to_metric_read(metric: PerformanceMetricDefinition) -> MetricDefinitionRead:
    return MetricDefinitionRead(
        id=metric.id,
        organization_id=metric.organization_id,
        sport=metric.sport,
        code=metric.code,
        name=metric.name,
        category=metric.category,
        unit=metric.unit,
        description=metric.description,
        min_value=metric.min_value,
        max_value=metric.max_value,
        weight=metric.weight,
        higher_is_better=metric.higher_is_better,
        status=metric.status,
    )


def to_performance_observation_read(
    observation: AthletePerformanceObservation,
) -> PerformanceObservationRead:
    return PerformanceObservationRead(
        id=observation.id,
        organization_id=observation.organization_id,
        athlete_profile_id=observation.athlete_profile_id,
        metric_definition_id=observation.metric_definition_id,
        event_id=observation.event_id,
        recorded_by_person_id=observation.recorded_by_person_id,
        value=observation.value,
        raw_value=observation.raw_value,
        observed_at=observation.observed_at,
        source=observation.source,
        confidence=observation.confidence,
        verification_status=observation.verification_status,
        notes=observation.notes,
    )


def to_team_read(team: Team) -> TeamRead:
    return TeamRead(
        id=team.id,
        organization_id=team.organization_id,
        name=team.name,
        sport=team.sport,
        sport_format=team.sport_format,
        age_group=team.age_group,
        gender_category=team.gender_category,
        season_label=team.season_label,
    )


def to_developer_person_read(
    person: Person,
    organization_id: UUID,
    membership: Membership | None,
) -> DeveloperPersonRead:
    return DeveloperPersonRead(
        id=person.id,
        organization_id=organization_id,
        membership_id=membership.id if membership is not None else None,
        display_name=person.display_name,
        given_name=person.given_name,
        family_name=person.family_name,
        date_of_birth=person.date_of_birth,
        primary_email=person.primary_email,
        primary_phone=person.primary_phone,
        country_code=person.country_code,
        notes=person.notes,
        membership_role=membership.role if membership is not None else None,
        membership_title=membership.title if membership is not None else None,
    )


def to_developer_guardian_relationship_read(
    relationship: GuardianRelationship,
    organization_id: UUID,
    guardian: Person,
) -> DeveloperGuardianRelationshipRead:
    return DeveloperGuardianRelationshipRead(
        id=relationship.id,
        organization_id=organization_id,
        athlete_person_id=relationship.athlete_person_id,
        guardian_person_id=relationship.guardian_person_id,
        guardian_display_name=guardian.display_name,
        relationship_kind=relationship.relationship_kind,
        relationship=relationship.relationship,
        can_sign_consent=relationship.can_sign_consent,
        can_view_medical=relationship.can_view_medical,
        emergency_contact=relationship.emergency_contact,
        can_pick_up=relationship.can_pick_up,
        is_primary=relationship.is_primary,
        notes=relationship.notes,
    )


def to_developer_consent_request_read(
    request: ConsentRequest,
    one_time_token: str,
) -> DeveloperConsentRequestRead:
    return DeveloperConsentRequestRead(
        id=request.id,
        organization_id=request.organization_id,
        athlete_person_id=request.athlete_person_id,
        guardian_person_id=request.guardian_person_id,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        channel=request.channel,
        destination=request.destination,
        status=request.status,
        expires_at=request.expires_at,
        sent_at=request.sent_at,
        fulfilled_at=request.fulfilled_at,
        external_message_id=request.external_message_id,
        one_time_token=one_time_token,
    )


@router.get("/me", response_model=DeveloperApiKeyInspectionRead)
async def sdk_me(
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
) -> DeveloperApiKeyInspectionRead:
    return credential


@router.get("/organization", response_model=OrganizationRead)
async def sdk_organization(
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> OrganizationRead:
    ensure_developer_api_scope(credential, organization_id, {"read:organization"})
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return to_organization_read(organization)


@router.get("/agents", response_model=list[AgentRead])
async def sdk_list_agents(
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[AgentRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:agents", "write:agents"})
    return [to_agent_read(agent) for agent in await list_ai_agents(db, organization_id)]


@router.get("/agents/tasks", response_model=list[AgentTaskRead])
async def sdk_list_agent_tasks(
    organization_id: UUID = Query(),
    agent_id: UUID | None = Query(default=None),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[AgentTaskRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:agents", "write:agents"})
    if agent_id is not None:
        agent = await db.get(Agent, agent_id)
        if agent is None or agent.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return [
        to_agent_task_read(task)
        for task in await list_agent_tasks(db, organization_id, agent_id=agent_id)
    ]


@router.post("/agents/{agent_id}/tasks", response_model=AgentTaskRead, status_code=status.HTTP_201_CREATED)
async def sdk_queue_agent_task(
    agent_id: UUID,
    payload: AgentTaskCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> AgentTaskRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:agents"})
    task = await queue_agent_task(
        db,
        None,
        agent_id,
        payload,
        None,
        enforce_manage_organization=False,
    )
    await deliver_developer_webhook_event(
        db,
        payload.organization_id,
        "agents.task.queued",
        str(task.id),
        {
            "id": str(task.id),
            "organization_id": str(task.organization_id),
            "agent_id": str(task.agent_id),
            "task_type": task.task_type,
            "title": task.title,
            "status": task.status.value,
            "governance_policy_code": task.governance_policy_code,
            "governance_policy_decision": task.governance_policy_decision,
            "origin": "developer_api",
        },
    )
    return to_agent_task_read(task)


@router.get("/events", response_model=list[EventRead])
async def sdk_list_events(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[EventRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:events", "write:events"})
    return [to_event_read(event) for event in await list_events(db, organization_id, team_id=team_id)]


@router.get("/events/{event_id}/attendance", response_model=list[AttendanceRecordRead])
async def sdk_list_event_attendance(
    event_id: UUID,
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[AttendanceRecordRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:attendance", "write:attendance"})
    event = await db.get(Event, event_id)
    if event is None or event.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return [to_attendance_read(attendance) for attendance in await list_attendance(db, event_id)]


@router.post(
    "/events/{event_id}/attendance",
    response_model=AttendanceRecordRead,
    status_code=status.HTTP_201_CREATED,
)
async def sdk_record_event_attendance(
    event_id: UUID,
    payload: AttendanceRecordUpsert,
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AttendanceRecordRead:
    ensure_developer_api_scope(credential, organization_id, {"write:attendance"})
    event = await db.get(Event, event_id)
    if event is None or event.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    (
        attendance,
        clearance_status,
        medical_clearance_status,
        medical_clearance_id,
        medical_clearance_reason,
        attendance_policy_code,
        attendance_policy_decision,
        attendance_policy_warnings,
    ) = await record_attendance(
        db,
        None,
        event_id,
        payload,
        authz,
        enforce_manage_event=False,
    )
    return to_attendance_read(
        attendance,
        clearance_status=clearance_status,
        medical_clearance_status=medical_clearance_status,
        medical_clearance_id=medical_clearance_id,
        medical_clearance_reason=medical_clearance_reason,
        attendance_policy_code=attendance_policy_code,
        attendance_policy_decision=attendance_policy_decision,
        attendance_policy_warnings=attendance_policy_warnings,
    )


@router.get("/communications/templates", response_model=list[CommunicationTemplateRead])
async def sdk_list_communication_templates(
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[CommunicationTemplateRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:communications", "write:communications"})
    return [
        to_communication_template_read(template)
        for template in await list_templates(db, organization_id)
    ]


@router.post(
    "/communications/templates",
    response_model=CommunicationTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
async def sdk_create_communication_template(
    payload: CommunicationTemplateCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> CommunicationTemplateRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:communications"})
    template = await create_template(
        db,
        None,
        payload,
        None,
        enforce_manage_communications_scope=False,
    )
    return to_communication_template_read(template)


@router.get("/communications/messages", response_model=list[CommunicationMessageRead])
async def sdk_list_communication_messages(
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[CommunicationMessageRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:communications", "write:communications"})
    return [
        to_communication_message_read(message, recipient_count)
        for message, recipient_count in await list_messages(db, organization_id)
    ]


@router.post(
    "/communications/messages",
    response_model=CommunicationMessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def sdk_create_communication_message(
    payload: CommunicationMessageCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> CommunicationMessageRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:communications"})
    message = await create_message(
        db,
        None,
        payload,
        None,
        enforce_manage_communications_scope=False,
    )
    recipients = await list_recipients(db, message.id)
    await deliver_developer_webhook_event(
        db,
        payload.organization_id,
        "communications.message.created",
        str(message.id),
        {
            "id": str(message.id),
            "organization_id": str(message.organization_id),
            "message_type": message.message_type.value,
            "channel": message.channel.value,
            "scope_type": message.scope_type.value,
            "scope_id": str(message.scope_id),
            "recipient_count": len(recipients),
            "origin": "developer_api",
        },
    )
    return to_communication_message_read(message, recipient_count=len(recipients))


@router.get(
    "/communications/messages/{message_id}/recipients",
    response_model=list[MessageRecipientRead],
)
async def sdk_list_communication_message_recipients(
    message_id: UUID,
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[MessageRecipientRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:communications", "write:communications"})
    message = await get_message(db, message_id)
    if message.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return [
        to_message_recipient_read(recipient, person)
        for recipient, person in await list_recipients(db, message_id)
    ]


@router.post(
    "/communications/messages/{message_id}/dispatch",
    response_model=CommunicationDispatchSummary,
)
async def sdk_dispatch_communication_message(
    message_id: UUID,
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> CommunicationDispatchSummary:
    ensure_developer_api_scope(credential, organization_id, {"write:communications"})
    message = await get_message(db, message_id)
    if message.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    summary = await dispatch_message(
        db,
        None,
        message_id,
        None,
        enforce_manage_communications_scope=False,
    )
    await deliver_developer_webhook_event(
        db,
        organization_id,
        "communications.message.dispatched",
        str(message.id),
        {
            "id": str(message.id),
            "organization_id": str(message.organization_id),
            "message_type": message.message_type.value,
            "channel": message.channel.value,
            "attempted": summary.attempted,
            "sent": summary.sent,
            "delivered": summary.delivered,
            "failed": summary.failed,
            "suppressed": summary.suppressed,
            "queued": summary.queued,
            "origin": "developer_api",
        },
    )
    return summary


@router.get("/billing/plans", response_model=list[BillingPlanRead])
async def sdk_list_billing_plans(
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[BillingPlanRead]:
    ensure_developer_api_has_scope(credential, {"read:billing", "write:billing"})
    return [read_model(plan, BillingPlanRead) for plan in await list_plans(db)]


@router.get("/billing/subscriptions", response_model=list[SubscriptionRead])
async def sdk_list_billing_subscriptions(
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[SubscriptionRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:billing", "write:billing"})
    return [
        read_model(subscription, SubscriptionRead)
        for subscription in await list_subscriptions(db, organization_id)
    ]


@router.get("/billing/meters", response_model=list[UsageMeterRead])
async def sdk_list_billing_usage_meters(
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[UsageMeterRead]:
    ensure_developer_api_has_scope(credential, {"read:billing", "write:billing"})
    return [read_model(meter, UsageMeterRead) for meter in await list_usage_meters(db)]


@router.get("/billing/usage", response_model=list[UsageRecordRead])
async def sdk_list_billing_usage_records(
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[UsageRecordRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:billing", "write:billing"})
    return [
        read_model(record, UsageRecordRead)
        for record in await list_usage_records(db, organization_id)
    ]


@router.post("/billing/usage", response_model=UsageRecordRead, status_code=status.HTTP_201_CREATED)
async def sdk_record_billing_usage(
    payload: UsageRecordCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> UsageRecordRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:billing"})
    record = await record_usage(
        db,
        None,
        payload,
        None,
        enforce_manage_billing_scope=False,
    )
    await deliver_developer_webhook_event(
        db,
        payload.organization_id,
        "billing.usage.recorded",
        str(record.id),
        {
            "id": str(record.id),
            "organization_id": str(record.organization_id),
            "subscription_id": str(record.subscription_id),
            "usage_meter_id": str(record.usage_meter_id),
            "quantity": record.quantity,
            "source": record.source,
            "external_reference": record.external_reference,
            "origin": "developer_api",
        },
    )
    return read_model(record, UsageRecordRead)


@router.get("/billing/invoices", response_model=list[SaaSInvoiceRead])
async def sdk_list_billing_invoices(
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[SaaSInvoiceRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:billing", "write:billing"})
    return [
        read_model(invoice, SaaSInvoiceRead)
        for invoice in await list_invoices(db, organization_id)
    ]


@router.get("/billing/entitlements", response_model=list[BillingEntitlementRead])
async def sdk_list_billing_entitlements(
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[BillingEntitlementRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:billing", "write:billing"})
    return [
        read_model(entitlement, BillingEntitlementRead)
        for entitlement in await list_entitlements(db, organization_id)
    ]


@router.get("/billing/summary", response_model=BillingSummaryRead)
async def sdk_get_billing_summary(
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> BillingSummaryRead:
    ensure_developer_api_scope(credential, organization_id, {"read:billing", "write:billing"})
    return BillingSummaryRead(**await billing_summary(db, organization_id))


@router.get("/teams", response_model=list[TeamRead])
async def sdk_list_teams(
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[TeamRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:organization", "read:teams"})
    return [to_team_read(team) for team in await list_teams_for_organization(db, organization_id)]


@router.post("/people", response_model=DeveloperPersonRead, status_code=status.HTTP_201_CREATED)
async def sdk_create_person(
    payload: DeveloperPersonCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperPersonRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:people", "write:roster"})
    organization = await db.get(Organization, payload.organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    person = None
    if payload.primary_email is not None:
        person = await db.scalar(select(Person).where(Person.primary_email == payload.primary_email))
    if person is None:
        person = Person(
            display_name=payload.display_name,
            given_name=payload.given_name,
            family_name=payload.family_name,
            date_of_birth=payload.date_of_birth,
            primary_email=payload.primary_email,
            primary_phone=payload.primary_phone,
            country_code=payload.country_code,
            notes=payload.notes,
        )
        db.add(person)
        await db.flush()
    else:
        person.display_name = person.display_name or payload.display_name
        person.given_name = person.given_name or payload.given_name
        person.family_name = person.family_name or payload.family_name
        person.date_of_birth = person.date_of_birth or payload.date_of_birth
        person.primary_phone = person.primary_phone or payload.primary_phone
        person.country_code = person.country_code or payload.country_code
        person.notes = person.notes or payload.notes

    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == payload.organization_id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == person.id,
            Membership.role == payload.membership_role,
        )
    )
    if membership is None:
        membership = Membership(
            organization_id=payload.organization_id,
            subject_type=MemberSubjectType.PERSON,
            subject_id=person.id,
            role=payload.membership_role,
            title=payload.membership_title,
        )
        db.add(membership)
        await authz.touch(
            Relationship(
                resource_type="organization",
                resource_id=str(payload.organization_id),
                relation=organization_member_relation(
                    MemberSubjectType.PERSON,
                    payload.membership_role,
                ),
                subject_type="person",
                subject_id=str(person.id),
            )
        )
    await db.commit()
    await db.refresh(person)
    if membership is not None:
        await db.refresh(membership)
    return to_developer_person_read(person, payload.organization_id, membership)


@router.post(
    "/people/{athlete_person_id}/guardians",
    response_model=DeveloperGuardianRelationshipRead,
    status_code=status.HTTP_201_CREATED,
)
async def sdk_link_guardian(
    athlete_person_id: UUID,
    payload: DeveloperGuardianRelationshipCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperGuardianRelationshipRead:
    ensure_developer_api_scope(
        credential,
        payload.organization_id,
        {"write:guardians", "write:roster"},
    )
    athlete = await db.get(Person, athlete_person_id)
    if athlete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    athlete_membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == payload.organization_id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == athlete_person_id,
        )
    )
    athlete_profile = await db.scalar(
        select(AthleteProfile).where(
            AthleteProfile.organization_id == payload.organization_id,
            AthleteProfile.person_id == athlete_person_id,
        )
    )
    if athlete_membership is None and athlete_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete is not linked to this organization",
        )

    guardian = None
    if payload.guardian_person_id is not None:
        guardian = await db.get(Person, payload.guardian_person_id)
        if guardian is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guardian not found")
    elif payload.guardian_email is not None:
        guardian = await db.scalar(select(Person).where(Person.primary_email == payload.guardian_email))
    if guardian is None and payload.guardian_phone is not None:
        guardian = await db.scalar(select(Person).where(Person.primary_phone == payload.guardian_phone))
    if guardian is None:
        if payload.guardian_email is None and payload.guardian_phone is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="guardian_person_id, guardian_email, or guardian_phone is required",
            )
        guardian = Person(
            display_name=payload.guardian_display_name
            or payload.guardian_email
            or payload.guardian_phone
            or "Guardian",
            primary_email=payload.guardian_email,
            primary_phone=payload.guardian_phone,
        )
        db.add(guardian)
        await db.flush()
    elif payload.guardian_phone and not guardian.primary_phone:
        guardian.primary_phone = payload.guardian_phone

    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == payload.organization_id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == guardian.id,
            Membership.role == MembershipRole.GUARDIAN,
        )
    )
    if membership is None:
        membership = Membership(
            organization_id=payload.organization_id,
            subject_type=MemberSubjectType.PERSON,
            subject_id=guardian.id,
            role=MembershipRole.GUARDIAN,
            title="Guardian",
        )
        db.add(membership)
        await authz.touch(
            Relationship(
                resource_type="organization",
                resource_id=str(payload.organization_id),
                relation=organization_member_relation(
                    MemberSubjectType.PERSON,
                    MembershipRole.GUARDIAN,
                ),
                subject_type="person",
                subject_id=str(guardian.id),
            )
        )

    relationship = await db.scalar(
        select(GuardianRelationship).where(
            GuardianRelationship.athlete_person_id == athlete_person_id,
            GuardianRelationship.guardian_person_id == guardian.id,
        )
    )
    if relationship is None:
        relationship = GuardianRelationship(
            athlete_person_id=athlete_person_id,
            guardian_person_id=guardian.id,
            relationship_kind=payload.relationship_kind,
            relationship=payload.relationship or payload.relationship_kind.value.replace("_", " "),
            can_sign_consent=payload.can_sign_consent,
            can_view_medical=payload.can_view_medical,
            emergency_contact=payload.emergency_contact,
            can_pick_up=payload.can_pick_up,
            is_primary=payload.is_primary,
            notes=payload.notes,
        )
        db.add(relationship)
        await authz.touch(
            Relationship(
                resource_type="athlete_profile",
                resource_id=str(athlete_person_id),
                relation="guardian",
                subject_type="person",
                subject_id=str(guardian.id),
            )
        )
    await db.commit()
    await db.refresh(guardian)
    await db.refresh(relationship)
    return to_developer_guardian_relationship_read(relationship, payload.organization_id, guardian)


@router.post(
    "/people/{athlete_person_id}/consent-requests",
    response_model=DeveloperConsentRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def sdk_create_consent_request(
    athlete_person_id: UUID,
    payload: DeveloperConsentRequestCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> DeveloperConsentRequestRead:
    ensure_developer_api_scope(
        credential,
        payload.organization_id,
        {"write:consent", "write:guardians", "write:roster"},
    )
    relationship = await db.scalar(
        select(GuardianRelationship).where(
            GuardianRelationship.athlete_person_id == athlete_person_id,
            GuardianRelationship.guardian_person_id == payload.guardian_person_id,
            GuardianRelationship.can_sign_consent.is_(True),
        )
    )
    if relationship is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Guardian cannot sign consent for athlete",
        )
    athlete_membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == payload.organization_id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == athlete_person_id,
        )
    )
    athlete_profile = await db.scalar(
        select(AthleteProfile).where(
            AthleteProfile.organization_id == payload.organization_id,
            AthleteProfile.person_id == athlete_person_id,
        )
    )
    if athlete_membership is None and athlete_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete is not linked to this organization",
        )
    token = token_urlsafe(32)
    request = ConsentRequest(
        organization_id=payload.organization_id,
        athlete_person_id=athlete_person_id,
        guardian_person_id=payload.guardian_person_id,
        scope_type=payload.scope_type,
        scope_id=normalized_scope_id(
            payload.organization_id,
            payload.scope_type,
            payload.scope_id,
        ),
        channel=payload.channel,
        destination=await consent_destination(db, payload),
        token_hash=hash_token(token),
        status=ConsentRequestStatus.PENDING,
        expires_at=payload.expires_at,
        sent_at=utc_now(),
        external_message_id=payload.external_message_id,
        notes=payload.notes,
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return to_developer_consent_request_read(request, token)


@router.post("/teams", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
async def sdk_create_team(
    payload: TeamCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TeamRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:teams"})
    organization = await db.get(Organization, payload.organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    team = Team(**payload.model_dump())
    db.add(team)
    await db.flush()
    await authz.touch(
        Relationship(
            resource_type="organization",
            resource_id=str(payload.organization_id),
            relation="member_team",
            subject_type="team",
            subject_id=str(team.id),
        )
    )
    await db.commit()
    await db.refresh(team)
    return to_team_read(team)


@router.post(
    "/teams/{team_id}/members",
    response_model=TeamRosterEntryRead,
    status_code=status.HTTP_201_CREATED,
)
async def sdk_add_team_member(
    team_id: UUID,
    payload: TeamMemberAdd,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> TeamRosterEntryRead:
    team = await db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    ensure_developer_api_scope(credential, team.organization_id, {"write:roster", "write:teams"})
    person = await db.get(Person, payload.person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    athlete_profile = await db.scalar(
        select(AthleteProfile).where(
            AthleteProfile.organization_id == team.organization_id,
            AthleteProfile.person_id == payload.person_id,
        )
    )
    if athlete_profile is None:
        athlete_profile = AthleteProfile(
            organization_id=team.organization_id,
            person_id=payload.person_id,
        )
        db.add(athlete_profile)
        await db.flush()
    roster_entry = await db.scalar(
        select(TeamRosterEntry).where(
            TeamRosterEntry.team_id == team_id,
            TeamRosterEntry.athlete_profile_id == athlete_profile.id,
        )
    )
    if roster_entry is None:
        roster_entry = TeamRosterEntry(
            team_id=team_id,
            athlete_profile_id=athlete_profile.id,
            role=payload.role,
            status=payload.status,
            primary_position=payload.primary_position,
            jersey_number=payload.jersey_number,
            is_captain=payload.is_captain,
        )
        db.add(roster_entry)
        await authz.touch(
            Relationship(
                resource_type="team",
                resource_id=str(team_id),
                relation=team_member_relation(payload.role),
                subject_type="person",
                subject_id=str(payload.person_id),
            )
        )
        await db.commit()
        await db.refresh(roster_entry)
    return TeamRosterEntryRead(
        id=roster_entry.id,
        team_id=roster_entry.team_id,
        athlete_profile_id=roster_entry.athlete_profile_id,
        role=roster_entry.role,
        primary_position=roster_entry.primary_position,
        jersey_number=roster_entry.jersey_number,
        is_captain=roster_entry.is_captain,
        status=roster_entry.status,
    )


@router.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def sdk_create_event(
    payload: EventCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> EventRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:events"})
    if payload.team_id is not None:
        team = await db.get(Team, payload.team_id)
        if team is None or team.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found for organization")
    event = Event(**payload.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    await deliver_developer_webhook_event(
        db,
        payload.organization_id,
        "events.created",
        str(event.id),
        {
            "id": str(event.id),
            "organization_id": str(event.organization_id),
            "team_id": str(event.team_id) if event.team_id else None,
            "event_type": event.event_type.value,
            "title": event.title,
            "starts_at": event.starts_at.isoformat(),
            "source": "developer_api",
        },
    )
    return to_event_read(event)


@router.get("/performance/metrics", response_model=list[MetricDefinitionRead])
async def sdk_list_performance_metrics(
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[MetricDefinitionRead]:
    ensure_developer_api_scope(
        credential,
        organization_id,
        {"read:performance", "write:performance"},
    )
    return [
        to_metric_read(metric)
        for metric in await list_metric_definitions(db, organization_id, sport=sport)
    ]


@router.get(
    "/performance/athletes/{athlete_profile_id}/observations",
    response_model=list[PerformanceObservationRead],
)
async def sdk_list_performance_observations(
    athlete_profile_id: UUID,
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceObservationRead]:
    ensure_developer_api_scope(
        credential,
        organization_id,
        {"read:performance", "write:performance"},
    )
    return [
        to_performance_observation_read(observation)
        for observation in await list_observations(db, organization_id, athlete_profile_id)
    ]


@router.post(
    "/performance/athletes/{athlete_profile_id}/observations",
    response_model=PerformanceObservationRead,
    status_code=status.HTTP_201_CREATED,
)
async def sdk_create_performance_observation(
    athlete_profile_id: UUID,
    payload: PerformanceObservationCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> PerformanceObservationRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:performance"})
    athlete_profile = await db.get(AthleteProfile, athlete_profile_id)
    if athlete_profile is None or athlete_profile.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    metric = await db.get(PerformanceMetricDefinition, payload.metric_definition_id)
    if metric is None or metric.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    if payload.event_id is not None:
        event = await db.get(Event, payload.event_id)
        if event is None or event.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    observation = AthletePerformanceObservation(
        athlete_profile_id=athlete_profile.id,
        recorded_by_person_id=None,
        observed_at=payload.observed_at or datetime.now(UTC),
        **payload.model_dump(exclude={"observed_at"}),
    )
    db.add(observation)
    await db.commit()
    await db.refresh(observation)
    await deliver_developer_webhook_event(
        db,
        payload.organization_id,
        "performance.observation.created",
        str(observation.id),
        {
            "id": str(observation.id),
            "organization_id": str(observation.organization_id),
            "athlete_profile_id": str(observation.athlete_profile_id),
            "metric_definition_id": str(observation.metric_definition_id),
            "metric_code": metric.code,
            "metric_name": metric.name,
            "unit": metric.unit,
            "value": observation.value,
            "source": observation.source.value,
            "confidence": observation.confidence,
            "verification_status": observation.verification_status.value,
            "observed_at": observation.observed_at.isoformat(),
            "origin": "developer_api",
        },
    )
    return to_performance_observation_read(observation)


@router.get("/training/drills", response_model=list[TrainingDrillRead])
async def sdk_list_training_drills(
    organization_id: UUID = Query(),
    sport: str | None = Query(default=None),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[TrainingDrillRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:organization", "read:training"})
    return [
        to_drill_read(drill)
        for drill in await list_training_drills(db, organization_id, sport=sport)
    ]


@router.post("/training/drills", response_model=TrainingDrillRead, status_code=status.HTTP_201_CREATED)
async def sdk_create_training_drill(
    payload: TrainingDrillCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> TrainingDrillRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:training"})
    drill = TrainingDrill(**payload.model_dump())
    db.add(drill)
    await db.commit()
    await db.refresh(drill)
    await deliver_developer_webhook_event(
        db,
        payload.organization_id,
        "training.drill.created",
        str(drill.id),
        {
            "id": str(drill.id),
            "organization_id": str(drill.organization_id),
            "sport": drill.sport,
            "name": drill.name,
            "focus_area": drill.focus_area,
            "category": drill.category,
            "default_duration_minutes": drill.default_duration_minutes,
            "default_intensity": drill.default_intensity,
        },
    )
    return to_drill_read(drill)


@router.get("/training/plans", response_model=list[TrainingPlanRead])
async def sdk_list_training_plans(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    athlete_profile_id: UUID | None = Query(default=None),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[TrainingPlanRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:training", "write:training"})
    return [
        to_training_plan_read(plan)
        for plan in await list_training_plans(
            db,
            organization_id,
            team_id=team_id,
            athlete_profile_id=athlete_profile_id,
        )
    ]


@router.post("/training/plans", response_model=TrainingPlanRead, status_code=status.HTTP_201_CREATED)
async def sdk_create_training_plan(
    payload: TrainingPlanCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:training"})
    plan = await create_training_plan(
        db,
        None,
        payload,
        None,
        enforce_manage_training_scope=False,
    )
    await deliver_developer_webhook_event(
        db,
        payload.organization_id,
        "training.plan.created",
        str(plan.id),
        {
            "id": str(plan.id),
            "organization_id": str(plan.organization_id),
            "team_id": str(plan.team_id) if plan.team_id else None,
            "athlete_profile_id": str(plan.athlete_profile_id) if plan.athlete_profile_id else None,
            "title": plan.title,
            "focus_area": plan.focus_area,
            "origin": "developer_api",
        },
    )
    return to_training_plan_read(plan)


@router.get("/training/plans/{plan_id}/items", response_model=list[TrainingPlanItemRead])
async def sdk_list_training_plan_items(
    plan_id: UUID,
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[TrainingPlanItemRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:training", "write:training"})
    plan = await db.get(TrainingPlan, plan_id)
    if plan is None or plan.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return [
        to_training_plan_item_read(item)
        for item in await list_training_plan_items(db, plan_id)
    ]


@router.post(
    "/training/plans/{plan_id}/items",
    response_model=TrainingPlanItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def sdk_add_training_plan_item(
    plan_id: UUID,
    payload: TrainingPlanItemCreate,
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanItemRead:
    ensure_developer_api_scope(credential, organization_id, {"write:training"})
    plan = await db.get(TrainingPlan, plan_id)
    if plan is None or plan.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    item = await add_training_plan_item(
        db,
        None,
        plan_id,
        payload,
        None,
        enforce_manage_training_scope=False,
    )
    return to_training_plan_item_read(item)


@router.get("/training/sessions", response_model=list[TrainingSessionPlanRead])
async def sdk_list_training_sessions(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[TrainingSessionPlanRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:training", "write:training"})
    return [
        to_training_session_plan_read(session_plan)
        for session_plan in await list_training_session_plans(db, organization_id, team_id=team_id)
    ]


@router.post("/training/sessions", response_model=TrainingSessionPlanRead, status_code=status.HTTP_201_CREATED)
async def sdk_create_training_session(
    payload: TrainingSessionPlanCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> TrainingSessionPlanRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"write:training"})
    session_plan = await create_training_session_plan(
        db,
        None,
        payload,
        None,
        enforce_manage_training_scope=False,
    )
    await deliver_developer_webhook_event(
        db,
        payload.organization_id,
        "training.session.created",
        str(session_plan.id),
        {
            "id": str(session_plan.id),
            "organization_id": str(session_plan.organization_id),
            "team_id": str(session_plan.team_id),
            "plan_id": str(session_plan.plan_id) if session_plan.plan_id else None,
            "title": session_plan.title,
            "scheduled_for": session_plan.scheduled_for.isoformat(),
            "origin": "developer_api",
        },
    )
    return to_training_session_plan_read(session_plan)


@router.get("/training/calendar-artifact", response_model=TrainingCalendarArtifactRead)
async def sdk_export_training_calendar_artifact(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    starts_at: datetime | None = Query(default=None),
    ends_at: datetime | None = Query(default=None),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> TrainingCalendarArtifactRead:
    ensure_developer_api_scope(credential, organization_id, {"read:training", "write:training"})
    return TrainingCalendarArtifactRead(
        **await export_training_calendar_artifact(
            db,
            None,
            organization_id,
            None,
            team_id=team_id,
            starts_at=starts_at,
            ends_at=ends_at,
            enforce_manage_training_scope=False,
        )
    )


@router.post("/training/availability", response_model=TrainingAvailabilityRead)
async def sdk_suggest_training_availability(
    payload: TrainingAvailabilityCreate,
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> TrainingAvailabilityRead:
    ensure_developer_api_scope(credential, payload.organization_id, {"read:training", "write:training"})
    return TrainingAvailabilityRead(**await suggest_training_availability(db, payload))


@router.get(
    "/training/sessions/{session_plan_id}/feedback",
    response_model=list[TrainingSessionFeedbackRead],
)
async def sdk_list_training_session_feedback(
    session_plan_id: UUID,
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> list[TrainingSessionFeedbackRead]:
    ensure_developer_api_scope(credential, organization_id, {"read:training", "write:training"})
    session_plan = await db.get(TrainingSessionPlan, session_plan_id)
    if session_plan is None or session_plan.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session plan not found")
    return [
        to_training_session_feedback_read(row)
        for row in await list_training_session_feedback(db, session_plan_id)
    ]


@router.post(
    "/training/sessions/{session_plan_id}/feedback",
    response_model=TrainingSessionFeedbackRead,
    status_code=status.HTTP_201_CREATED,
)
async def sdk_record_training_session_feedback(
    session_plan_id: UUID,
    payload: TrainingSessionFeedbackCreate,
    organization_id: UUID = Query(),
    credential: DeveloperApiKeyInspectionRead = Depends(get_sdk_credential),
    db: AsyncSession = Depends(get_db),
) -> TrainingSessionFeedbackRead:
    ensure_developer_api_scope(credential, organization_id, {"write:training"})
    session_plan = await db.get(TrainingSessionPlan, session_plan_id)
    if session_plan is None or session_plan.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session plan not found")
    feedback = await record_training_session_feedback(
        db,
        None,
        session_plan_id,
        payload,
        None,
        enforce_manage_training_scope=False,
    )
    await deliver_developer_webhook_event(
        db,
        organization_id,
        "training.feedback.recorded",
        str(feedback["id"]),
        {
            "id": str(feedback["id"]),
            "organization_id": str(feedback["organization_id"]),
            "session_plan_id": str(feedback["session_plan_id"]),
            "athlete_profile_id": (
                str(feedback["athlete_profile_id"]) if feedback["athlete_profile_id"] else None
            ),
            "readiness_score": feedback["readiness_score"],
            "completed": feedback["completed"],
            "origin": "developer_api",
        },
    )
    return to_training_session_feedback_read(feedback)
