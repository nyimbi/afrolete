import hashlib
import hmac
import json
import time
from datetime import UTC, datetime
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.agent import Agent, AgentAssignment, AgentRunRecord, AgentTask
from app.models.enums import AgentTaskStatus
from app.models.event import Event
from app.models.organization import Organization
from app.models.team import AthleteProfile, Team
from app.schemas.agent import AgentAssignmentCreate, AgentCreate, AgentTaskCreate, AgentTaskUpdate
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship

ASSIGNABLE_SCOPES = {"organization", "team", "event", "athlete_profile"}


async def ensure_manage_organization(
    authz: AuthorizationService,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> None:
    can_manage = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not can_manage:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def create_agent(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: AgentCreate,
    authz: AuthorizationService,
) -> Agent:
    organization = await db.get(Organization, payload.organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    await ensure_manage_organization(authz, identity, payload.organization_id)

    agent = Agent(
        organization_id=payload.organization_id,
        name=payload.name,
        kind=payload.kind,
        purpose=payload.purpose,
        model_policy=payload.model_policy,
    )
    db.add(agent)
    await db.flush()
    await authz.touch(
        Relationship(
            resource_type="agent",
            resource_id=str(agent.id),
            relation="owner",
            subject_type="user",
            subject_id=str(identity.user_id),
        )
    )
    await db.commit()
    await db.refresh(agent)
    return agent


async def list_agents(
    db: AsyncSession,
    organization_id: UUID,
) -> list[Agent]:
    return list(
        (
            await db.scalars(
                select(Agent)
                .where(Agent.organization_id == organization_id)
                .order_by(Agent.kind, Agent.name)
            )
        ).all()
    )


async def get_agent_for_organization(
    db: AsyncSession,
    agent_id: UUID,
    organization_id: UUID,
) -> Agent:
    agent = await db.get(Agent, agent_id)
    if agent is None or agent.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


async def assign_agent(
    db: AsyncSession,
    identity: CurrentIdentity,
    agent_id: UUID,
    payload: AgentAssignmentCreate,
    authz: AuthorizationService,
) -> AgentAssignment:
    agent = await get_agent_for_organization(db, agent_id, payload.organization_id)
    await ensure_manage_organization(authz, identity, payload.organization_id)
    await validate_assignment_scope(db, payload.organization_id, payload.scope_type, payload.scope_id)

    existing = await db.scalar(
        select(AgentAssignment).where(
            AgentAssignment.agent_id == agent.id,
            AgentAssignment.organization_id == payload.organization_id,
            AgentAssignment.scope_type == payload.scope_type,
            AgentAssignment.scope_id == payload.scope_id,
        )
    )
    if existing is not None:
        return existing

    assignment = AgentAssignment(
        agent_id=agent.id,
        organization_id=payload.organization_id,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        granted_by_person_id=identity.person_id,
    )
    db.add(assignment)
    await authz.touch(
        Relationship(
            resource_type=payload.scope_type,
            resource_id=payload.scope_id,
            relation="assigned_agent",
            subject_type="agent",
            subject_id=str(agent.id),
        )
    )
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def list_agent_assignments(
    db: AsyncSession,
    agent_id: UUID,
    organization_id: UUID,
) -> list[AgentAssignment]:
    await get_agent_for_organization(db, agent_id, organization_id)
    return list(
        (
            await db.scalars(
                select(AgentAssignment)
                .where(AgentAssignment.agent_id == agent_id)
                .where(AgentAssignment.organization_id == organization_id)
                .order_by(AgentAssignment.scope_type, AgentAssignment.scope_id)
            )
        ).all()
    )


async def queue_agent_task(
    db: AsyncSession,
    identity: CurrentIdentity,
    agent_id: UUID,
    payload: AgentTaskCreate,
    authz: AuthorizationService,
) -> AgentTask:
    agent = await get_agent_for_organization(db, agent_id, payload.organization_id)
    await ensure_manage_organization(authz, identity, payload.organization_id)

    task = AgentTask(
        agent_id=agent.id,
        organization_id=payload.organization_id,
        task_type=payload.task_type,
        title=payload.title,
        requested_by_person_id=identity.person_id,
        input_ref=payload.input_ref,
    )
    db.add(task)
    await db.flush()
    await append_agent_run_record(
        db,
        agent,
        task,
        identity,
        event_type="queued",
        settings=get_settings(),
    )
    await db.commit()
    await db.refresh(task)
    return task


async def list_agent_tasks(
    db: AsyncSession,
    organization_id: UUID,
    agent_id: UUID | None = None,
) -> list[AgentTask]:
    statement = select(AgentTask).where(AgentTask.organization_id == organization_id)
    if agent_id is not None:
        statement = statement.where(AgentTask.agent_id == agent_id)
    return list(
        (
            await db.scalars(
                statement.order_by(AgentTask.status, AgentTask.created_at.desc())
            )
        ).all()
    )


async def agent_run_records(
    db: AsyncSession,
    organization_id: UUID,
) -> list[dict[str, object]]:
    rows = (
        await db.execute(
            select(AgentRunRecord, AgentTask, Agent)
            .join(AgentTask, AgentTask.id == AgentRunRecord.task_id)
            .join(Agent, Agent.id == AgentRunRecord.agent_id)
            .where(AgentRunRecord.organization_id == organization_id)
            .order_by(AgentRunRecord.created_at.desc())
        )
    ).all()
    return [
        {
            "id": record.id,
            "task_id": task.id,
            "agent_id": agent.id,
            "agent_name": agent.name,
            "agent_kind": agent.kind,
            "organization_id": task.organization_id,
            "event_type": record.event_type,
            "task_type": task.task_type,
            "title": task.title,
            "status": record.status,
            "model_policy": record.model_policy,
            "execution_mode": record.execution_mode,
            "input_ref": record.input_ref,
            "output_ref": record.output_ref,
            "review_required": record.status == AgentTaskStatus.WAITING_FOR_REVIEW,
            "governance_notes": record.governance_notes,
            "started_at": record.started_at,
            "finished_at": record.finished_at,
            "duration_ms": record.duration_ms,
            "ledger_sequence": record.ledger_sequence,
            "record_hash": record.record_hash,
            "previous_record_hash": record.previous_record_hash,
        }
        for record, task, agent in rows
    ]


async def agent_governance_summary(
    db: AsyncSession,
    organization_id: UUID,
    settings: Settings | None = None,
) -> dict[str, object]:
    settings = settings or get_settings()
    agents = await list_agents(db, organization_id)
    tasks = await list_agent_tasks(db, organization_id)
    return {
        "organization_id": organization_id,
        "agents": len(agents),
        "queued_tasks": count_tasks(tasks, AgentTaskStatus.QUEUED),
        "running_tasks": count_tasks(tasks, AgentTaskStatus.RUNNING),
        "waiting_for_review": count_tasks(tasks, AgentTaskStatus.WAITING_FOR_REVIEW),
        "completed_tasks": count_tasks(tasks, AgentTaskStatus.COMPLETED),
        "failed_tasks": count_tasks(tasks, AgentTaskStatus.FAILED),
        "cancelled_tasks": count_tasks(tasks, AgentTaskStatus.CANCELLED),
        "human_review_required": sum(1 for task in tasks if task.status == AgentTaskStatus.WAITING_FOR_REVIEW),
        "credential_status": agent_credential_status(settings),
    }


async def verify_agent_run_ledger(
    db: AsyncSession,
    organization_id: UUID,
) -> dict[str, object]:
    records = list(
        (
            await db.scalars(
                select(AgentRunRecord)
                .where(AgentRunRecord.organization_id == organization_id)
                .order_by(AgentRunRecord.ledger_sequence, AgentRunRecord.created_at, AgentRunRecord.id)
            )
        ).all()
    )
    previous_hash = None
    broken_records: list[UUID] = []
    for record in records:
        expected_hash = agent_record_hash(record_hash_payload(record, previous_hash))
        if record.previous_record_hash != previous_hash or record.record_hash != expected_hash:
            broken_records.append(record.id)
        previous_hash = record.record_hash
    return {
        "organization_id": organization_id,
        "total_records": len(records),
        "verified_records": len(records) - len(broken_records),
        "broken_records": broken_records,
        "latest_record_hash": previous_hash,
        "valid": not broken_records,
    }


async def agent_model_transparency_report(
    db: AsyncSession,
    organization_id: UUID,
    settings: Settings | None = None,
) -> dict[str, object]:
    settings = settings or get_settings()
    agents = await list_agents(db, organization_id)
    records = list(
        (
            await db.scalars(
                select(AgentRunRecord)
                .where(AgentRunRecord.organization_id == organization_id)
                .order_by(AgentRunRecord.created_at.desc())
            )
        ).all()
    )
    ledger = await verify_agent_run_ledger(db, organization_id)
    credential_status = agent_credential_status(settings)
    model_names = sorted(
        {
            *(agent.model_policy or settings.agent_default_model for agent in agents),
            *(record.model_policy for record in records),
        }
    )
    model_items = [
        agent_model_transparency_item(model_name, agents, records, settings.agent_default_model)
        for model_name in model_names
    ]
    recommendations = agent_transparency_recommendations(model_items, credential_status, bool(ledger["valid"]))
    return {
        "organization_id": organization_id,
        "generated_at": datetime.now(UTC),
        "total_models": len(model_items),
        "total_runs": len(records),
        "human_review_required": sum(item["human_review_runs"] for item in model_items),
        "local_model_count": sum(1 for item in model_items if "deterministic" in item["execution_modes"]),
        "webhook_model_count": sum(1 for item in model_items if "webhook" in item["execution_modes"]),
        "ledger_valid": ledger["valid"],
        "latest_record_hash": ledger["latest_record_hash"],
        "credential_boundary": credential_status["credential_boundary"],
        "recommendations": recommendations,
        "models": model_items,
    }


async def update_agent_task(
    db: AsyncSession,
    identity: CurrentIdentity,
    task_id: UUID,
    payload: AgentTaskUpdate,
    authz: AuthorizationService,
) -> AgentTask:
    task = await db.get(AgentTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent task not found")
    await ensure_manage_organization(authz, identity, task.organization_id)

    if payload.status is not None:
        task.status = payload.status
    if payload.output_ref is not None:
        task.output_ref = payload.output_ref
    if payload.review_notes is not None:
        task.review_notes = payload.review_notes

    agent = await db.get(Agent, task.agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    await append_agent_run_record(
        db,
        agent,
        task,
        identity,
        event_type="manual_update",
        settings=get_settings(),
    )
    await db.commit()
    await db.refresh(task)
    return task


async def execute_agent_task(
    db: AsyncSession,
    identity: CurrentIdentity,
    task_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> AgentTask:
    task = await db.get(AgentTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent task not found")
    await ensure_manage_organization(authz, identity, task.organization_id)
    if task.status == AgentTaskStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Task cancelled")

    agent = await db.get(Agent, task.agent_id)
    if agent is None or agent.organization_id != task.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    settings = settings or get_settings()
    task.status = AgentTaskStatus.RUNNING
    await db.flush()
    started_at = datetime.now(UTC)
    await append_agent_run_record(
        db,
        agent,
        task,
        identity,
        event_type="execution_started",
        settings=settings,
        started_at=started_at,
    )

    if settings.agent_execution_mode == "webhook":
        await execute_with_webhook(settings, agent, task, identity)
    else:
        execute_with_deterministic_planner(settings, agent, task)

    finished_at = datetime.now(UTC)
    await append_agent_run_record(
        db,
        agent,
        task,
        identity,
        event_type="execution_finished",
        settings=settings,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=int((finished_at - started_at).total_seconds() * 1000),
    )
    await db.commit()
    await db.refresh(task)
    return task


async def append_agent_run_record(
    db: AsyncSession,
    agent: Agent,
    task: AgentTask,
    identity: CurrentIdentity,
    event_type: str,
    settings: Settings,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    duration_ms: int | None = None,
) -> AgentRunRecord:
    sequence = await agent_task_record_sequence(db, task.id)
    ledger_sequence = await next_agent_ledger_sequence(db, task.organization_id)
    previous_hash = await latest_agent_record_hash(db, task.organization_id)
    model_policy = agent.model_policy or settings.agent_default_model
    note = governance_notes(agent, task)
    idempotency_key = f"{task.id}:{event_type}:{sequence}"
    record_hash = agent_record_hash(
        {
            "organization_id": str(task.organization_id),
            "agent_id": str(agent.id),
            "task_id": str(task.id),
            "event_type": event_type,
            "status": task.status.value,
            "model_policy": model_policy,
            "execution_mode": settings.agent_execution_mode,
            "input_ref": task.input_ref,
            "output_ref": task.output_ref,
            "review_notes": task.review_notes,
            "started_at": datetime_digest(started_at),
            "finished_at": datetime_digest(finished_at),
            "duration_ms": duration_ms,
            "executed_by_person_id": str(identity.person_id) if identity.person_id else None,
            "ledger_sequence": ledger_sequence,
            "governance_notes": note,
            "idempotency_key": idempotency_key,
            "previous_record_hash": previous_hash,
        }
    )
    record = AgentRunRecord(
        organization_id=task.organization_id,
        agent_id=agent.id,
        task_id=task.id,
        event_type=event_type,
        status=task.status,
        model_policy=model_policy,
        execution_mode=settings.agent_execution_mode,
        input_ref=task.input_ref,
        output_ref=task.output_ref,
        review_notes=task.review_notes,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        executed_by_person_id=identity.person_id,
        ledger_sequence=ledger_sequence,
        governance_notes=note,
        idempotency_key=idempotency_key,
        previous_record_hash=previous_hash,
        record_hash=record_hash,
    )
    db.add(record)
    await db.flush()
    return record


async def agent_task_record_sequence(db: AsyncSession, task_id: UUID) -> int:
    count = await db.scalar(
        select(func.count(AgentRunRecord.id)).where(AgentRunRecord.task_id == task_id)
    )
    return int(count or 0) + 1


async def latest_agent_record_hash(db: AsyncSession, organization_id: UUID) -> str | None:
    return await db.scalar(
        select(AgentRunRecord.record_hash)
        .where(AgentRunRecord.organization_id == organization_id)
        .order_by(AgentRunRecord.ledger_sequence.desc(), AgentRunRecord.created_at.desc(), AgentRunRecord.id.desc())
        .limit(1)
    )


async def next_agent_ledger_sequence(db: AsyncSession, organization_id: UUID) -> int:
    current = await db.scalar(
        select(func.max(AgentRunRecord.ledger_sequence)).where(
            AgentRunRecord.organization_id == organization_id
        )
    )
    return int(current or 0) + 1


def agent_record_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def record_hash_payload(record: AgentRunRecord, previous_hash: str | None) -> dict[str, object]:
    return {
        "organization_id": str(record.organization_id),
        "agent_id": str(record.agent_id),
        "task_id": str(record.task_id),
        "event_type": record.event_type,
        "status": record.status.value,
        "model_policy": record.model_policy,
        "execution_mode": record.execution_mode,
        "input_ref": record.input_ref,
        "output_ref": record.output_ref,
        "review_notes": record.review_notes,
        "started_at": datetime_digest(record.started_at),
        "finished_at": datetime_digest(record.finished_at),
        "duration_ms": record.duration_ms,
        "executed_by_person_id": str(record.executed_by_person_id) if record.executed_by_person_id else None,
        "ledger_sequence": record.ledger_sequence,
        "governance_notes": record.governance_notes,
        "idempotency_key": record.idempotency_key,
        "previous_record_hash": previous_hash,
    }


def datetime_digest(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


async def validate_assignment_scope(
    db: AsyncSession,
    organization_id: UUID,
    scope_type: str,
    scope_id: str,
) -> None:
    if scope_type not in ASSIGNABLE_SCOPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"scope_type must be one of {', '.join(sorted(ASSIGNABLE_SCOPES))}",
        )

    try:
        scope_uuid = UUID(scope_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="scope_id must be a UUID") from exc

    if scope_type == "organization":
        if scope_uuid != organization_id:
            raise HTTPException(status_code=422, detail="Organization scope must match organization_id")
        organization = await db.get(Organization, scope_uuid)
        if organization is None:
            raise HTTPException(status_code=404, detail="Organization not found")
        return

    model = {
        "team": Team,
        "event": Event,
        "athlete_profile": AthleteProfile,
    }[scope_type]
    item = await db.get(model, scope_uuid)
    if item is None:
        raise HTTPException(status_code=404, detail="Assignment scope not found")
    if item.organization_id != organization_id:
        raise HTTPException(status_code=422, detail="Assignment scope belongs to another organization")


def execute_with_deterministic_planner(
    settings: Settings,
    agent: Agent,
    task: AgentTask,
) -> None:
    model_name = agent.model_policy or settings.agent_default_model
    task.status = AgentTaskStatus.WAITING_FOR_REVIEW
    task.output_ref = f"agent://tasks/{task.id}/outputs/deterministic"
    task.review_notes = (
        f"{agent.name} prepared a deterministic draft using {model_name}. "
        f"Task: {task.title}. Input: {task.input_ref or 'none'}. "
        "Review before applying the recommendation."
    )


async def execute_with_webhook(
    settings: Settings,
    agent: Agent,
    task: AgentTask,
    identity: CurrentIdentity,
) -> None:
    if not settings.agent_webhook_url:
        task.status = AgentTaskStatus.FAILED
        task.review_notes = "Agent webhook execution mode is enabled but no webhook URL is configured."
        return

    try:
        async with httpx.AsyncClient(timeout=settings.agent_execution_timeout_seconds) as client:
            payload = agent_execution_payload(agent, task, identity, settings)
            body = agent_execution_body(payload)
            response = await client.post(
                settings.agent_webhook_url,
                content=body,
                headers=agent_execution_headers(settings, body),
            )
        if not 200 <= response.status_code < 300:
            task.status = AgentTaskStatus.FAILED
            task.review_notes = f"Agent webhook returned {response.status_code}: {response.text[:600]}"
            return
        apply_agent_webhook_response(task, response)
    except httpx.HTTPError as error:
        task.status = AgentTaskStatus.FAILED
        task.review_notes = str(error)[:600]


def agent_execution_payload(
    agent: Agent,
    task: AgentTask,
    identity: CurrentIdentity,
    settings: Settings,
) -> dict[str, object]:
    return {
        "event": "afrolete.agent.execute",
        "provider": "webhook",
        "model": agent.model_policy or settings.agent_default_model,
        "idempotency_key": f"{task.id}:execute",
        "agent": {
            "id": str(agent.id),
            "organization_id": str(agent.organization_id),
            "name": agent.name,
            "kind": agent.kind.value,
            "purpose": agent.purpose,
        },
        "task": {
            "id": str(task.id),
            "organization_id": str(task.organization_id),
            "type": task.task_type,
            "title": task.title,
            "input_ref": task.input_ref,
        },
        "requested_by": {
            "user_id": str(identity.user_id),
            "person_id": str(identity.person_id) if identity.person_id else None,
        },
    }


def agent_execution_headers(settings: Settings, body: bytes) -> dict[str, str]:
    headers = {
        "User-Agent": "AfroLete-Agent-Executor/1.0",
        "Content-Type": "application/json",
    }
    if settings.agent_webhook_key:
        timestamp = str(int(time.time()))
        headers["X-Afrolete-Agent-Key"] = settings.agent_webhook_key
        headers["X-Afrolete-Agent-Timestamp"] = timestamp
        headers["X-Afrolete-Agent-Signature"] = agent_execution_signature(settings.agent_webhook_key, timestamp, body)
    return headers


def agent_execution_body(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()


def agent_execution_signature(signing_key: str, timestamp: str, body: bytes) -> str:
    digest = hmac.new(signing_key.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def apply_agent_webhook_response(task: AgentTask, response: httpx.Response) -> None:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    task.output_ref = str(payload.get("output_ref") or f"agent://tasks/{task.id}/outputs/webhook")
    notes = payload.get("review_notes") or payload.get("summary") or "Agent webhook completed."
    task.review_notes = str(notes)[:4000]
    raw_status = payload.get("status") or AgentTaskStatus.WAITING_FOR_REVIEW.value
    try:
        task.status = AgentTaskStatus(str(raw_status))
    except ValueError:
        task.status = AgentTaskStatus.WAITING_FOR_REVIEW


def count_tasks(tasks: list[AgentTask], status_value: AgentTaskStatus) -> int:
    return sum(1 for task in tasks if task.status == status_value)


def agent_credential_status(settings: Settings) -> dict[str, object]:
    webhook_configured = bool(settings.agent_webhook_url)
    webhook_key_configured = bool(settings.agent_webhook_key)
    if settings.agent_execution_mode == "webhook" and not webhook_configured:
        recommendation = "Configure AGENT_WEBHOOK_URL before enabling live provider execution."
    elif settings.agent_execution_mode == "webhook" and not webhook_key_configured:
        recommendation = "Add AGENT_WEBHOOK_KEY or OpenBao-injected equivalent before production execution."
    else:
        recommendation = "Execution boundary is usable; keep human review enabled for applied actions."
    return {
        "execution_mode": settings.agent_execution_mode,
        "default_model": settings.agent_default_model,
        "webhook_configured": webhook_configured,
        "webhook_key_configured": webhook_key_configured,
        "credential_boundary": "openbao/env" if webhook_key_configured else "local-deterministic",
        "recommendation": recommendation,
    }


def agent_model_transparency_item(
    model_policy: str,
    agents: list[Agent],
    records: list[AgentRunRecord],
    default_model: str,
) -> dict[str, object]:
    model_agents = [agent for agent in agents if (agent.model_policy or default_model) == model_policy]
    model_records = [record for record in records if record.model_policy == model_policy]
    execution_modes = sorted({record.execution_mode for record in model_records})
    completed_runs = sum(1 for record in model_records if record.status == AgentTaskStatus.COMPLETED)
    failed_runs = sum(1 for record in model_records if record.status == AgentTaskStatus.FAILED)
    review_runs = sum(1 for record in model_records if record.status == AgentTaskStatus.WAITING_FOR_REVIEW)
    latest_run_at = max(
        (record.finished_at or record.started_at or record.created_at for record in model_records),
        default=None,
    )
    risk_band = agent_model_risk_band(model_records, execution_modes)
    return {
        "model_policy": model_policy,
        "agent_count": len(model_agents),
        "run_count": len(model_records),
        "completed_runs": completed_runs,
        "failed_runs": failed_runs,
        "human_review_runs": review_runs,
        "execution_modes": execution_modes,
        "latest_run_at": latest_run_at,
        "risk_band": risk_band,
        "transparency_notes": agent_model_transparency_notes(model_policy, model_records, execution_modes, risk_band),
    }


def agent_model_risk_band(records: list[AgentRunRecord], execution_modes: list[str]) -> str:
    if not records:
        return "unproven"
    failed = sum(1 for record in records if record.status == AgentTaskStatus.FAILED)
    waiting = sum(1 for record in records if record.status == AgentTaskStatus.WAITING_FOR_REVIEW)
    if failed > 0 or "webhook" in execution_modes:
        return "high_review"
    if waiting > 0:
        return "human_review"
    return "controlled"


def agent_model_transparency_notes(
    model_policy: str,
    records: list[AgentRunRecord],
    execution_modes: list[str],
    risk_band: str,
) -> str:
    if not records:
        return f"{model_policy} is assigned but has no recorded runs yet; collect governed evidence before automation."
    if "webhook" in execution_modes:
        return f"{model_policy} uses external webhook execution; keep OpenBao-backed credentials and human review active."
    if risk_band == "high_review":
        return f"{model_policy} has failed runs or external execution and needs operator review before applied actions."
    if risk_band == "human_review":
        return f"{model_policy} has outputs waiting for review; do not apply recommendations without sign-off."
    return f"{model_policy} is operating inside the controlled local governance boundary."


def agent_transparency_recommendations(
    model_items: list[dict[str, object]],
    credential_status: dict[str, object],
    ledger_valid: bool,
) -> list[str]:
    recommendations: list[str] = []
    if not ledger_valid:
        recommendations.append("Freeze agent automation until the run ledger hash chain is repaired.")
    if not credential_status["webhook_key_configured"] and credential_status["execution_mode"] == "webhook":
        recommendations.append("Configure an OpenBao-injected agent webhook key before live model execution.")
    if any(item["risk_band"] == "unproven" for item in model_items):
        recommendations.append("Run low-risk evaluation tasks for assigned models that have no ledger evidence.")
    if any(item["human_review_runs"] for item in model_items):
        recommendations.append("Clear human review queues before enabling downstream side effects.")
    if not recommendations:
        recommendations.append("Continue periodic transparency review and preserve the hash-chained run ledger.")
    return recommendations


def governance_notes(agent: Agent, task: AgentTask) -> str:
    if task.status == AgentTaskStatus.FAILED:
        return "Failed runs require operator review before retry."
    if task.status == AgentTaskStatus.WAITING_FOR_REVIEW:
        return f"{agent.name} output must be reviewed by a human before side effects are applied."
    if task.status == AgentTaskStatus.COMPLETED:
        return "Task completed after review or explicit operator action."
    return "Task is tracked in the governance ledger for audit and billing."
