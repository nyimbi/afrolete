from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.agent import (
    AgentAssignmentCreate,
    AgentAssignmentRead,
    AgentBiasAuditCreate,
    AgentBiasAuditRead,
    AgentDecisionAppealCreate,
    AgentDecisionAppealRead,
    AgentDecisionAppealUpdate,
    AgentGovernanceSummaryRead,
    AgentModelRegistryCreate,
    AgentModelRegistryRead,
    AgentModelRegistryUpdate,
    AgentModelTransparencyReportRead,
    AgentRunLedgerVerificationRead,
    AgentRunRecordRead,
    AgentCreate,
    AgentRead,
    AgentTaskCreate,
    AgentTaskRead,
    AgentTaskUpdate,
    AgentWorkerCallbackCreate,
    AgentWorkerCallbackRead,
)
from app.services.agents import (
    apply_agent_worker_callback,
    agent_governance_summary,
    agent_model_transparency_report,
    agent_run_records,
    assign_agent,
    create_agent,
    create_agent_model_registry,
    execute_agent_task,
    list_agent_assignments,
    list_agent_bias_audits,
    list_agent_decision_appeals,
    list_agent_model_registry,
    list_agent_tasks,
    list_agents,
    queue_agent_task,
    run_agent_bias_audit,
    submit_agent_decision_appeal,
    update_agent_decision_appeal,
    update_agent_model_registry,
    update_agent_task,
    validate_agent_worker_callback_signature,
    verify_agent_run_ledger,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service

router = APIRouter(prefix="/agents", tags=["agents"])


def to_agent_read(agent) -> AgentRead:
    return AgentRead(
        id=agent.id,
        organization_id=agent.organization_id,
        name=agent.name,
        kind=agent.kind,
        purpose=agent.purpose,
        status=agent.status,
        model_policy=agent.model_policy,
    )


def to_assignment_read(assignment) -> AgentAssignmentRead:
    return AgentAssignmentRead(
        id=assignment.id,
        agent_id=assignment.agent_id,
        organization_id=assignment.organization_id,
        scope_type=assignment.scope_type,
        scope_id=assignment.scope_id,
        granted_by_person_id=assignment.granted_by_person_id,
    )


def to_task_read(task) -> AgentTaskRead:
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
    )


def to_model_registry_read(registry) -> AgentModelRegistryRead:
    return AgentModelRegistryRead(
        id=registry.id,
        organization_id=registry.organization_id,
        model_policy=registry.model_policy,
        provider=registry.provider,
        model_family=registry.model_family,
        version=registry.version,
        use_case=registry.use_case,
        risk_tier=registry.risk_tier,
        review_status=registry.review_status,
        documentation_url=registry.documentation_url,
        evaluation_summary=registry.evaluation_summary,
        limitations=registry.limitations,
        bias_notes=registry.bias_notes,
        data_residency=registry.data_residency,
        owner_person_id=registry.owner_person_id,
        approved_by_person_id=registry.approved_by_person_id,
        approved_at=registry.approved_at,
    )


def to_bias_audit_read(audit) -> AgentBiasAuditRead:
    return AgentBiasAuditRead(
        id=audit.id,
        organization_id=audit.organization_id,
        model_registry_id=audit.model_registry_id,
        model_policy=audit.model_policy,
        audit_dimension=audit.audit_dimension,
        population_slice=audit.population_slice,
        sample_size=audit.sample_size,
        disparity_score=audit.disparity_score,
        status=audit.status,
        severity=audit.severity,
        findings=audit.findings,
        recommendation=audit.recommendation,
        mitigation_status=audit.mitigation_status,
        audited_by_person_id=audit.audited_by_person_id,
        audited_at=audit.audited_at,
    )


def to_decision_appeal_read(appeal) -> AgentDecisionAppealRead:
    return AgentDecisionAppealRead(
        id=appeal.id,
        organization_id=appeal.organization_id,
        agent_id=appeal.agent_id,
        task_id=appeal.task_id,
        model_policy=appeal.model_policy,
        status=appeal.status,
        reason=appeal.reason,
        question=appeal.question,
        simple_explanation=appeal.simple_explanation,
        technical_explanation=appeal.technical_explanation,
        data_summary=appeal.data_summary,
        alternative_options=appeal.alternative_options,
        supporting_evidence_ref=appeal.supporting_evidence_ref,
        submitted_by_person_id=appeal.submitted_by_person_id,
        resolved_by_person_id=appeal.resolved_by_person_id,
        resolution_notes=appeal.resolution_notes,
        due_at=appeal.due_at,
        resolved_at=appeal.resolved_at,
    )


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent_route(
    payload: AgentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentRead:
    return to_agent_read(await create_agent(db, identity, payload, authz))


@router.get("", response_model=list[AgentRead])
async def list_agents_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AgentRead]:
    return [to_agent_read(agent) for agent in await list_agents(db, organization_id)]


@router.get("/model-registry", response_model=list[AgentModelRegistryRead])
async def list_agent_model_registry_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AgentModelRegistryRead]:
    return [
        to_model_registry_read(registry)
        for registry in await list_agent_model_registry(db, organization_id)
    ]


@router.get("/bias-audits", response_model=list[AgentBiasAuditRead])
async def list_agent_bias_audits_route(
    organization_id: UUID = Query(),
    model_registry_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[AgentBiasAuditRead]:
    return [
        to_bias_audit_read(audit)
        for audit in await list_agent_bias_audits(db, organization_id, model_registry_id)
    ]


@router.get("/appeals", response_model=list[AgentDecisionAppealRead])
async def list_agent_decision_appeals_route(
    organization_id: UUID = Query(),
    status_value: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[AgentDecisionAppealRead]:
    return [
        to_decision_appeal_read(appeal)
        for appeal in await list_agent_decision_appeals(db, organization_id, status_value)
    ]


@router.post("/model-registry", response_model=AgentModelRegistryRead, status_code=status.HTTP_201_CREATED)
async def create_agent_model_registry_route(
    payload: AgentModelRegistryCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentModelRegistryRead:
    return to_model_registry_read(
        await create_agent_model_registry(db, identity, payload, authz)
    )


@router.post(
    "/model-registry/{registry_id}/bias-audits",
    response_model=AgentBiasAuditRead,
    status_code=status.HTTP_201_CREATED,
)
async def run_agent_bias_audit_route(
    registry_id: UUID,
    payload: AgentBiasAuditCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentBiasAuditRead:
    return to_bias_audit_read(
        await run_agent_bias_audit(db, identity, registry_id, payload, authz)
    )


@router.patch("/model-registry/{registry_id}", response_model=AgentModelRegistryRead)
async def update_agent_model_registry_route(
    registry_id: UUID,
    payload: AgentModelRegistryUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentModelRegistryRead:
    return to_model_registry_read(
        await update_agent_model_registry(db, identity, registry_id, payload, authz)
    )


@router.post("/tasks/{task_id}/appeals", response_model=AgentDecisionAppealRead, status_code=status.HTTP_201_CREATED)
async def submit_agent_decision_appeal_route(
    task_id: UUID,
    payload: AgentDecisionAppealCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentDecisionAppealRead:
    return to_decision_appeal_read(
        await submit_agent_decision_appeal(db, identity, task_id, payload, authz)
    )


@router.patch("/appeals/{appeal_id}", response_model=AgentDecisionAppealRead)
async def update_agent_decision_appeal_route(
    appeal_id: UUID,
    payload: AgentDecisionAppealUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentDecisionAppealRead:
    return to_decision_appeal_read(
        await update_agent_decision_appeal(db, identity, appeal_id, payload, authz)
    )


@router.post("/{agent_id}/assignments", response_model=AgentAssignmentRead, status_code=201)
async def assign_agent_route(
    agent_id: UUID,
    payload: AgentAssignmentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentAssignmentRead:
    return to_assignment_read(await assign_agent(db, identity, agent_id, payload, authz))


@router.get("/{agent_id}/assignments", response_model=list[AgentAssignmentRead])
async def list_agent_assignments_route(
    agent_id: UUID,
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AgentAssignmentRead]:
    return [
        to_assignment_read(assignment)
        for assignment in await list_agent_assignments(db, agent_id, organization_id)
    ]


@router.post("/{agent_id}/tasks", response_model=AgentTaskRead, status_code=201)
async def queue_agent_task_route(
    agent_id: UUID,
    payload: AgentTaskCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentTaskRead:
    return to_task_read(await queue_agent_task(db, identity, agent_id, payload, authz))


@router.get("/tasks", response_model=list[AgentTaskRead])
async def list_agent_tasks_route(
    organization_id: UUID = Query(),
    agent_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[AgentTaskRead]:
    return [
        to_task_read(task)
        for task in await list_agent_tasks(db, organization_id, agent_id=agent_id)
    ]


@router.get("/runs", response_model=list[AgentRunRecordRead])
async def list_agent_runs_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AgentRunRecordRead]:
    return [AgentRunRecordRead(**record) for record in await agent_run_records(db, organization_id)]


@router.get("/runs/verify", response_model=AgentRunLedgerVerificationRead)
async def verify_agent_runs_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> AgentRunLedgerVerificationRead:
    return AgentRunLedgerVerificationRead(**await verify_agent_run_ledger(db, organization_id))


@router.get("/governance", response_model=AgentGovernanceSummaryRead)
async def agent_governance_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> AgentGovernanceSummaryRead:
    return AgentGovernanceSummaryRead(**await agent_governance_summary(db, organization_id))


@router.get("/model-transparency", response_model=AgentModelTransparencyReportRead)
async def agent_model_transparency_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> AgentModelTransparencyReportRead:
    return AgentModelTransparencyReportRead(**await agent_model_transparency_report(db, organization_id))


@router.post("/worker-callbacks", response_model=AgentWorkerCallbackRead)
async def agent_worker_callback_route(
    request: Request,
    payload: AgentWorkerCallbackCreate,
    x_afrolete_agent_timestamp: str | None = Header(default=None, alias="X-Afrolete-Agent-Timestamp"),
    x_afrolete_agent_signature: str | None = Header(default=None, alias="X-Afrolete-Agent-Signature"),
    db: AsyncSession = Depends(get_db),
) -> AgentWorkerCallbackRead:
    signature_required, signature_validated = validate_agent_worker_callback_signature(
        await request.body(),
        x_afrolete_agent_timestamp,
        x_afrolete_agent_signature,
    )
    task, duplicate, message, run_record_id = await apply_agent_worker_callback(db, payload)
    return AgentWorkerCallbackRead(
        accepted=not duplicate,
        duplicate=duplicate,
        signature_required=signature_required,
        signature_validated=signature_validated,
        run_record_id=run_record_id,
        message=message,
        task=to_task_read(task),
    )


@router.post("/tasks/{task_id}/execute", response_model=AgentTaskRead)
async def execute_agent_task_route(
    task_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentTaskRead:
    return to_task_read(await execute_agent_task(db, identity, task_id, authz))


@router.patch("/tasks/{task_id}", response_model=AgentTaskRead)
async def update_agent_task_route(
    task_id: UUID,
    payload: AgentTaskUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentTaskRead:
    return to_task_read(await update_agent_task(db, identity, task_id, payload, authz))
