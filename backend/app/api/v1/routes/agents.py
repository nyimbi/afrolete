from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.agent import (
    AgentAssignmentCreate,
    AgentAssignmentRead,
    AgentGovernanceSummaryRead,
    AgentRunLedgerVerificationRead,
    AgentRunRecordRead,
    AgentCreate,
    AgentRead,
    AgentTaskCreate,
    AgentTaskRead,
    AgentTaskUpdate,
)
from app.services.agents import (
    agent_governance_summary,
    agent_run_records,
    assign_agent,
    create_agent,
    execute_agent_task,
    list_agent_assignments,
    list_agent_tasks,
    list_agents,
    queue_agent_task,
    update_agent_task,
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
