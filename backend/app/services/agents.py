import hashlib
import hmac
import json
import re
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.agent import (
    Agent,
    AgentAssignment,
    AgentBiasAudit,
    AgentDecisionAppeal,
    AgentModelRegistry,
    AgentRunRecord,
    AgentScorecardComment,
    AgentScorecardPublication,
    AgentTask,
)
from app.models.enums import AgentTaskStatus
from app.models.event import Event
from app.models.identity import Person
from app.models.organization import Organization
from app.models.team import AthleteProfile, GuardianRelationship, Team
from app.schemas.agent import (
    AgentAssignmentCreate,
    AgentBiasAuditCreate,
    AgentCreate,
    AgentDecisionAppealCreate,
    AgentDecisionAppealUpdate,
    AgentMyDecisionAppealCreate,
    AgentModelRegistryCreate,
    AgentModelRegistryUpdate,
    AgentScorecardCommentCreate,
    AgentScorecardCommentUpdate,
    AgentScorecardPublicationCreate,
    AgentTaskCreate,
    AgentTaskUpdate,
    AgentWorkerCallbackCreate,
)
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


async def list_agent_model_registry(
    db: AsyncSession,
    organization_id: UUID,
) -> list[AgentModelRegistry]:
    return list(
        (
            await db.scalars(
                select(AgentModelRegistry)
                .where(AgentModelRegistry.organization_id == organization_id)
                .order_by(AgentModelRegistry.review_status, AgentModelRegistry.model_policy)
            )
        ).all()
    )


async def list_agent_bias_audits(
    db: AsyncSession,
    organization_id: UUID,
    model_registry_id: UUID | None = None,
) -> list[AgentBiasAudit]:
    statement = select(AgentBiasAudit).where(AgentBiasAudit.organization_id == organization_id)
    if model_registry_id is not None:
        statement = statement.where(AgentBiasAudit.model_registry_id == model_registry_id)
    return list(
        (
            await db.scalars(
                statement.order_by(AgentBiasAudit.audited_at.desc(), AgentBiasAudit.created_at.desc())
            )
        ).all()
    )


async def list_agent_decision_appeals(
    db: AsyncSession,
    organization_id: UUID,
    status_value: str | None = None,
) -> list[AgentDecisionAppeal]:
    statement = select(AgentDecisionAppeal).where(AgentDecisionAppeal.organization_id == organization_id)
    if status_value is not None:
        statement = statement.where(AgentDecisionAppeal.status == status_value)
    return list(
        (
            await db.scalars(
                statement.order_by(AgentDecisionAppeal.created_at.desc(), AgentDecisionAppeal.due_at)
            )
        ).all()
    )


async def list_my_agent_decision_appeals(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> list[AgentDecisionAppeal]:
    return list(
        (
            await db.scalars(
                select(AgentDecisionAppeal)
                .where(AgentDecisionAppeal.organization_id == organization_id)
                .where(AgentDecisionAppeal.submitted_by_person_id == identity.person_id)
                .order_by(AgentDecisionAppeal.created_at.desc(), AgentDecisionAppeal.due_at)
            )
        ).all()
    )


async def list_my_agent_family_tasks(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> list[dict[str, object]]:
    athlete_names, profile_ids, person_ids = await linked_family_athlete_refs(db, identity, organization_id)
    if not profile_ids and not person_ids:
        return []

    profile_ref_values = [f"athlete_profile:{profile_id}" for profile_id in profile_ids]
    person_ref_values = [f"athlete:{person_id}" for person_id in person_ids]
    assigned_agent_ids = list(
        (
            await db.scalars(
                select(AgentAssignment.agent_id)
                .where(AgentAssignment.organization_id == organization_id)
                .where(AgentAssignment.scope_type == "athlete_profile")
                .where(AgentAssignment.scope_id.in_([str(profile_id) for profile_id in profile_ids]))
            )
        ).all()
    )
    conditions = [AgentTask.input_ref.in_([*profile_ref_values, *person_ref_values])]
    if assigned_agent_ids:
        conditions.append(AgentTask.agent_id.in_(assigned_agent_ids))
    rows = (
        await db.execute(
            select(AgentTask, Agent)
            .join(Agent, Agent.id == AgentTask.agent_id)
            .where(AgentTask.organization_id == organization_id)
            .where(or_(*conditions))
            .order_by(AgentTask.created_at.desc())
            .limit(20)
        )
    ).all()

    task_ids = [task.id for task, _ in rows]
    appeal_status_by_task: dict[UUID, str] = {}
    if task_ids:
        appeals = (
            await db.scalars(
                select(AgentDecisionAppeal)
                .where(AgentDecisionAppeal.submitted_by_person_id == identity.person_id)
                .where(AgentDecisionAppeal.task_id.in_(task_ids))
                .order_by(AgentDecisionAppeal.created_at.desc())
            )
        ).all()
        for appeal in appeals:
            appeal_status_by_task.setdefault(appeal.task_id, appeal.status)

    return [
        {
            "id": task.id,
            "organization_id": task.organization_id,
            "agent_id": agent.id,
            "agent_name": agent.name,
            "agent_kind": agent.kind,
            "task_type": task.task_type,
            "title": task.title,
            "status": task.status,
            "input_ref": task.input_ref,
            "output_ref": task.output_ref,
            "review_notes": task.review_notes,
            "athlete_name": athlete_name_for_task_ref(task.input_ref, athlete_names),
            "appeal_status": appeal_status_by_task.get(task.id),
            "simple_explanation": agent_decision_simple_explanation(agent, task),
            "data_summary": agent_decision_data_summary(task),
            "alternative_options": agent_decision_alternative_options(task),
            "governance_note": governance_notes(agent, task),
        }
        for task, agent in rows
    ]


async def get_my_agent_decision_appeal_form(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    task_id: UUID,
    settings: Settings | None = None,
) -> dict[str, object]:
    task = await db.get(AgentTask, task_id)
    if task is None or task.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent task not found")

    visible_tasks = await list_my_agent_family_tasks(db, identity, organization_id)
    visible_task = next((item for item in visible_tasks if item["id"] == task_id), None)
    if visible_task is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent task is not linked to this family")

    agent = await db.get(Agent, task.agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    latest_appeal = await db.scalar(
        select(AgentDecisionAppeal)
        .where(AgentDecisionAppeal.submitted_by_person_id == identity.person_id)
        .where(AgentDecisionAppeal.task_id == task.id)
        .order_by(AgentDecisionAppeal.created_at.desc())
    )
    settings = settings or get_settings()
    generated_at = datetime.now(UTC)
    athlete_name = visible_task.get("athlete_name") or "Linked family athlete"
    filename_name = slug_for_filename(str(athlete_name))
    content = render_agent_decision_appeal_form(
        identity=identity,
        agent=agent,
        task=task,
        visible_task=visible_task,
        latest_appeal=latest_appeal,
        generated_at=generated_at,
        model_policy=agent.model_policy or settings.agent_default_model,
        settings=settings,
    )
    return {
        "organization_id": organization_id,
        "task_id": task.id,
        "generated_at": generated_at,
        "download_filename": f"afrolete-ai-appeal-{filename_name}-{str(task.id)[:8]}.md",
        "content_type": "text/markdown; charset=utf-8",
        "content": content,
    }


async def submit_agent_decision_appeal(
    db: AsyncSession,
    identity: CurrentIdentity,
    task_id: UUID,
    payload: AgentDecisionAppealCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> AgentDecisionAppeal:
    task = await db.get(AgentTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent task not found")
    await ensure_manage_organization(authz, identity, task.organization_id)
    return await create_agent_decision_appeal_record(db, identity, task, payload, settings)


async def submit_my_agent_decision_appeal(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: AgentMyDecisionAppealCreate,
    settings: Settings | None = None,
) -> AgentDecisionAppeal:
    task = await db.get(AgentTask, payload.task_id)
    if task is None or task.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent task not found")
    visible_tasks = await list_my_agent_family_tasks(db, identity, payload.organization_id)
    if task.id not in {item["id"] for item in visible_tasks}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent task is not linked to this family")
    return await create_agent_decision_appeal_record(db, identity, task, payload, settings)


async def create_agent_decision_appeal_record(
    db: AsyncSession,
    identity: CurrentIdentity,
    task: AgentTask,
    payload: AgentDecisionAppealCreate,
    settings: Settings | None = None,
) -> AgentDecisionAppeal:
    agent = await db.get(Agent, task.agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    settings = settings or get_settings()
    model_policy = agent.model_policy or settings.agent_default_model
    appeal = AgentDecisionAppeal(
        organization_id=task.organization_id,
        agent_id=agent.id,
        task_id=task.id,
        model_policy=model_policy,
        status="pending",
        reason=payload.reason,
        question=payload.question,
        simple_explanation=agent_decision_simple_explanation(agent, task),
        technical_explanation=agent_decision_technical_explanation(agent, task, model_policy, settings),
        data_summary=agent_decision_data_summary(task),
        alternative_options=agent_decision_alternative_options(task),
        supporting_evidence_ref=payload.supporting_evidence_ref,
        submitted_by_person_id=identity.person_id,
        due_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(appeal)
    await db.commit()
    await db.refresh(appeal)
    return appeal


async def update_agent_decision_appeal(
    db: AsyncSession,
    identity: CurrentIdentity,
    appeal_id: UUID,
    payload: AgentDecisionAppealUpdate,
    authz: AuthorizationService,
) -> AgentDecisionAppeal:
    appeal = await db.get(AgentDecisionAppeal, appeal_id)
    if appeal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent decision appeal not found")
    await ensure_manage_organization(authz, identity, appeal.organization_id)
    appeal.status = payload.status
    appeal.resolution_notes = payload.resolution_notes
    if payload.status in {"upheld", "modified", "overturned", "withdrawn"}:
        appeal.resolved_by_person_id = identity.person_id
        appeal.resolved_at = datetime.now(UTC)
    else:
        appeal.resolved_by_person_id = None
        appeal.resolved_at = None
    await db.commit()
    await db.refresh(appeal)
    return appeal


async def run_agent_bias_audit(
    db: AsyncSession,
    identity: CurrentIdentity,
    registry_id: UUID,
    payload: AgentBiasAuditCreate,
    authz: AuthorizationService,
) -> AgentBiasAudit:
    registry = await db.get(AgentModelRegistry, registry_id)
    if registry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model registry record not found")
    await ensure_manage_organization(authz, identity, registry.organization_id)

    records = list(
        (
            await db.scalars(
                select(AgentRunRecord)
                .where(AgentRunRecord.organization_id == registry.organization_id)
                .where(AgentRunRecord.model_policy == registry.model_policy)
            )
        ).all()
    )
    score = agent_bias_disparity_score(records, registry)
    audit_status, severity = agent_bias_audit_status(score, len(records))
    findings = agent_bias_findings(registry, records, payload.audit_dimension, payload.population_slice, score)
    audit = AgentBiasAudit(
        organization_id=registry.organization_id,
        model_registry_id=registry.id,
        model_policy=registry.model_policy,
        audit_dimension=payload.audit_dimension,
        population_slice=payload.population_slice,
        sample_size=len(records),
        disparity_score=score,
        status=audit_status,
        severity=severity,
        findings=findings,
        recommendation=agent_bias_recommendation(audit_status, registry),
        mitigation_status="open" if audit_status in {"watch", "fail", "insufficient_data"} else "not_required",
        audited_by_person_id=identity.person_id,
        audited_at=datetime.now(UTC),
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)
    return audit


async def create_agent_model_registry(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: AgentModelRegistryCreate,
    authz: AuthorizationService,
) -> AgentModelRegistry:
    organization = await db.get(Organization, payload.organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    await ensure_manage_organization(authz, identity, payload.organization_id)

    existing = await db.scalar(
        select(AgentModelRegistry).where(
            AgentModelRegistry.organization_id == payload.organization_id,
            AgentModelRegistry.model_policy == payload.model_policy,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model policy is already registered")

    registry = AgentModelRegistry(
        organization_id=payload.organization_id,
        model_policy=payload.model_policy,
        provider=payload.provider,
        model_family=payload.model_family,
        version=payload.version,
        use_case=payload.use_case,
        risk_tier=payload.risk_tier,
        review_status=payload.review_status,
        documentation_url=payload.documentation_url,
        evaluation_summary=payload.evaluation_summary,
        limitations=payload.limitations,
        bias_notes=payload.bias_notes,
        data_residency=payload.data_residency,
        owner_person_id=identity.person_id,
    )
    if payload.review_status == "approved":
        registry.approved_by_person_id = identity.person_id
        registry.approved_at = datetime.now(UTC)
    db.add(registry)
    await db.commit()
    await db.refresh(registry)
    return registry


async def update_agent_model_registry(
    db: AsyncSession,
    identity: CurrentIdentity,
    registry_id: UUID,
    payload: AgentModelRegistryUpdate,
    authz: AuthorizationService,
) -> AgentModelRegistry:
    registry = await db.get(AgentModelRegistry, registry_id)
    if registry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model registry record not found")
    await ensure_manage_organization(authz, identity, registry.organization_id)

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(registry, field, value)
    if changes.get("review_status") == "approved":
        registry.approved_by_person_id = identity.person_id
        registry.approved_at = datetime.now(UTC)
    elif changes.get("review_status") in {"draft", "in_review", "blocked"}:
        registry.approved_by_person_id = None
        registry.approved_at = None
    await db.commit()
    await db.refresh(registry)
    return registry


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
    registry = await list_agent_model_registry(db, organization_id)
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
            *(item.model_policy for item in registry),
        }
    )
    registry_by_model = {item.model_policy: item for item in registry}
    model_items = [
        agent_model_transparency_item(
            model_name,
            agents,
            records,
            settings.agent_default_model,
            registry_by_model.get(model_name),
        )
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


async def agent_ethical_scorecard(
    db: AsyncSession,
    organization_id: UUID,
    settings: Settings | None = None,
) -> dict[str, object]:
    settings = settings or get_settings()
    registry = await list_agent_model_registry(db, organization_id)
    audits = await list_agent_bias_audits(db, organization_id)
    appeals = await list_agent_decision_appeals(db, organization_id)
    tasks = await list_agent_tasks(db, organization_id)
    ledger = await verify_agent_run_ledger(db, organization_id)
    approved_models = sum(1 for item in registry if item.review_status == "approved")
    blocked_models = sum(1 for item in registry if item.review_status == "blocked")
    undocumented_models = sum(1 for item in registry if not item.documentation_url)
    passing_bias_audits = sum(1 for audit in audits if audit.status == "pass")
    failing_bias_audits = sum(1 for audit in audits if audit.status == "fail")
    open_mitigations = sum(1 for audit in audits if audit.mitigation_status == "open")
    pending_appeals = sum(1 for appeal in appeals if appeal.status in {"pending", "under_review"})
    resolved_appeals = sum(1 for appeal in appeals if appeal.resolved_at is not None)
    human_review_required = count_tasks(tasks, AgentTaskStatus.WAITING_FOR_REVIEW)
    score = agent_ethics_score(
        total_models=len(registry),
        approved_models=approved_models,
        undocumented_models=undocumented_models,
        audits=audits,
        failing_bias_audits=failing_bias_audits,
        open_mitigations=open_mitigations,
        pending_appeals=pending_appeals,
        human_review_required=human_review_required,
        ledger_valid=bool(ledger["valid"]),
        webhook_key_configured=bool(agent_credential_status(settings)["webhook_key_configured"]),
    )
    actions = agent_ethics_improvement_actions(
        total_models=len(registry),
        approved_models=approved_models,
        undocumented_models=undocumented_models,
        audits=audits,
        failing_bias_audits=failing_bias_audits,
        open_mitigations=open_mitigations,
        pending_appeals=pending_appeals,
        human_review_required=human_review_required,
        ledger_valid=bool(ledger["valid"]),
    )
    grade = agent_ethics_grade(score)
    return {
        "organization_id": organization_id,
        "generated_at": datetime.now(UTC),
        "score": score,
        "grade": grade,
        "total_models": len(registry),
        "approved_models": approved_models,
        "blocked_models": blocked_models,
        "undocumented_models": undocumented_models,
        "bias_audits": len(audits),
        "passing_bias_audits": passing_bias_audits,
        "failing_bias_audits": failing_bias_audits,
        "open_mitigations": open_mitigations,
        "pending_appeals": pending_appeals,
        "resolved_appeals": resolved_appeals,
        "human_review_required": human_review_required,
        "ledger_valid": ledger["valid"],
        "public_summary": agent_ethics_public_summary(score, grade, len(registry), len(audits), pending_appeals),
        "improvement_actions": actions,
    }


async def list_agent_scorecard_comments(
    db: AsyncSession,
    organization_id: UUID,
) -> list[AgentScorecardComment]:
    return list(
        (
            await db.scalars(
                select(AgentScorecardComment)
                .where(AgentScorecardComment.organization_id == organization_id)
                .where(AgentScorecardComment.status == "published")
                .where(AgentScorecardComment.consent_to_publish.is_(True))
                .order_by(AgentScorecardComment.submitted_at.desc(), AgentScorecardComment.created_at.desc())
                .limit(25)
            )
        ).all()
    )


async def create_agent_scorecard_comment(
    db: AsyncSession,
    payload: AgentScorecardCommentCreate,
) -> AgentScorecardComment:
    organization = await db.get(Organization, payload.organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    abuse_score, abuse_reason = await scorecard_comment_abuse_review(db, payload)
    initial_status = "private_feedback"
    if payload.consent_to_publish:
        initial_status = "flagged" if abuse_score >= 60 else "published"
    comment = AgentScorecardComment(
        organization_id=payload.organization_id,
        display_name=payload.display_name.strip(),
        affiliation=payload.affiliation.strip() if payload.affiliation else None,
        contact_email=payload.contact_email.strip().lower() if payload.contact_email else None,
        comment=payload.comment.strip(),
        status=initial_status,
        consent_to_publish=payload.consent_to_publish,
        abuse_score=abuse_score,
        abuse_reason=abuse_reason,
        submitted_at=datetime.now(UTC),
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def scorecard_comment_abuse_review(
    db: AsyncSession,
    payload: AgentScorecardCommentCreate,
) -> tuple[int, str | None]:
    reasons: list[str] = []
    score = 0
    comment_text = payload.comment.strip()
    normalized = normalize_comment_text(comment_text)
    link_count = len(re.findall(r"https?://|www\.", comment_text, flags=re.IGNORECASE))
    if link_count >= 2:
        score += 45
        reasons.append("multiple_links")
    if re.search(r"\b(crypto|casino|loan|viagra|betting|airdrop|forex)\b", comment_text, flags=re.IGNORECASE):
        score += 40
        reasons.append("spam_keyword")
    if len(comment_text) > 1200:
        score += 20
        reasons.append("very_long")
    if repeated_character_run(comment_text):
        score += 25
        reasons.append("repeated_characters")
    if normalized:
        duplicate = await db.scalar(
            select(AgentScorecardComment)
            .where(AgentScorecardComment.organization_id == payload.organization_id)
            .where(AgentScorecardComment.submitted_at >= datetime.now(UTC) - timedelta(days=1))
            .where(func.lower(AgentScorecardComment.comment) == normalized)
        )
        if duplicate is not None:
            score += 55
            reasons.append("recent_duplicate")
    email_key = payload.contact_email.strip().lower() if payload.contact_email else None
    display_key = payload.display_name.strip().lower()
    recent_count = await db.scalar(
        select(func.count(AgentScorecardComment.id))
        .where(AgentScorecardComment.organization_id == payload.organization_id)
        .where(AgentScorecardComment.submitted_at >= datetime.now(UTC) - timedelta(hours=1))
        .where(
            (func.lower(AgentScorecardComment.contact_email) == email_key)
            if email_key
            else (func.lower(AgentScorecardComment.display_name) == display_key)
        )
    )
    if recent_count and recent_count >= 3:
        score += 50
        reasons.append("rapid_repeat_submission")
    score = min(score, 100)
    return score, ", ".join(reasons) if reasons else None


def normalize_comment_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def repeated_character_run(value: str) -> bool:
    return bool(re.search(r"(.)\1{8,}", value))


async def list_agent_scorecard_comments_for_moderation(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[AgentScorecardComment]:
    await ensure_manage_organization(authz, identity, organization_id)
    return list(
        (
            await db.scalars(
                select(AgentScorecardComment)
                .where(AgentScorecardComment.organization_id == organization_id)
                .order_by(
                    AgentScorecardComment.status,
                    AgentScorecardComment.submitted_at.desc(),
                    AgentScorecardComment.created_at.desc(),
                )
                .limit(100)
            )
        ).all()
    )


async def update_agent_scorecard_comment(
    db: AsyncSession,
    identity: CurrentIdentity,
    comment_id: UUID,
    payload: AgentScorecardCommentUpdate,
    authz: AuthorizationService,
) -> AgentScorecardComment:
    comment = await db.get(AgentScorecardComment, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scorecard comment not found")
    await ensure_manage_organization(authz, identity, comment.organization_id)
    if payload.status == "published" and not comment.consent_to_publish:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish feedback without consent to publish",
        )
    comment.status = payload.status
    await db.commit()
    await db.refresh(comment)
    return comment


async def list_agent_scorecard_publications(
    db: AsyncSession,
    organization_id: UUID,
) -> list[AgentScorecardPublication]:
    return list(
        (
            await db.scalars(
                select(AgentScorecardPublication)
                .where(AgentScorecardPublication.organization_id == organization_id)
                .where(AgentScorecardPublication.status == "published")
                .order_by(AgentScorecardPublication.published_at.desc())
                .limit(8)
            )
        ).all()
    )


async def agent_scorecard_publication_readiness(
    db: AsyncSession,
    organization_id: UUID,
) -> dict[str, object]:
    now = datetime.now(UTC)
    current_period = scorecard_period_label(now)
    due_at = scorecard_period_due_at(now)
    latest_publication = await db.scalar(
        select(AgentScorecardPublication)
        .where(AgentScorecardPublication.organization_id == organization_id)
        .where(AgentScorecardPublication.status == "published")
        .order_by(AgentScorecardPublication.published_at.desc())
    )
    current_publication = await db.scalar(
        select(AgentScorecardPublication)
        .where(AgentScorecardPublication.organization_id == organization_id)
        .where(AgentScorecardPublication.period_label == current_period)
        .where(AgentScorecardPublication.status == "published")
    )
    scorecard = await agent_ethical_scorecard(db, organization_id)
    flagged_comments = await db.scalar(
        select(func.count(AgentScorecardComment.id))
        .where(AgentScorecardComment.organization_id == organization_id)
        .where(AgentScorecardComment.status == "flagged")
    )
    pending_appeals = int(scorecard["pending_appeals"])
    days_until_due = max((due_at.date() - now.date()).days, 0)
    readiness_status, recommended_action = scorecard_publication_readiness_state(
        current_period_published=current_publication is not None,
        days_until_due=days_until_due,
        ledger_valid=bool(scorecard["ledger_valid"]),
        flagged_comment_count=int(flagged_comments or 0),
        pending_appeal_count=pending_appeals,
        approved_models=int(scorecard["approved_models"]),
        total_models=int(scorecard["total_models"]),
    )
    return {
        "organization_id": organization_id,
        "current_period_label": current_period,
        "current_period_published": current_publication is not None,
        "next_publication_due_at": due_at,
        "days_until_due": days_until_due,
        "latest_period_label": latest_publication.period_label if latest_publication else None,
        "latest_published_at": latest_publication.published_at if latest_publication else None,
        "flagged_comment_count": int(flagged_comments or 0),
        "pending_appeal_count": pending_appeals,
        "score": int(scorecard["score"]),
        "grade": str(scorecard["grade"]),
        "readiness_status": readiness_status,
        "recommended_action": recommended_action,
    }


async def publish_agent_scorecard(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: AgentScorecardPublicationCreate,
    authz: AuthorizationService,
) -> AgentScorecardPublication:
    await ensure_manage_organization(authz, identity, payload.organization_id)
    scorecard = await agent_ethical_scorecard(db, payload.organization_id)
    published_comments = await db.scalar(
        select(func.count(AgentScorecardComment.id))
        .where(AgentScorecardComment.organization_id == payload.organization_id)
        .where(AgentScorecardComment.status == "published")
        .where(AgentScorecardComment.consent_to_publish.is_(True))
    )
    flagged_comments = await db.scalar(
        select(func.count(AgentScorecardComment.id))
        .where(AgentScorecardComment.organization_id == payload.organization_id)
        .where(AgentScorecardComment.status == "flagged")
    )
    published_at = datetime.now(UTC)
    period_label = payload.period_label or scorecard_period_label(published_at)
    action_text = json.dumps(scorecard["improvement_actions"], separators=(",", ":"))
    snapshot_payload = {
        "period_label": period_label,
        "score": scorecard["score"],
        "grade": scorecard["grade"],
        "total_models": scorecard["total_models"],
        "approved_models": scorecard["approved_models"],
        "bias_audits": scorecard["bias_audits"],
        "pending_appeals": scorecard["pending_appeals"],
        "ledger_valid": scorecard["ledger_valid"],
        "public_summary": scorecard["public_summary"],
        "improvement_actions": scorecard["improvement_actions"],
        "published_comment_count": published_comments or 0,
        "flagged_comment_count": flagged_comments or 0,
    }
    existing = await db.scalar(
        select(AgentScorecardPublication)
        .where(AgentScorecardPublication.organization_id == payload.organization_id)
        .where(AgentScorecardPublication.period_label == period_label)
    )
    publication = existing or AgentScorecardPublication(
        organization_id=payload.organization_id,
        period_label=period_label,
    )
    publication.status = "published"
    publication.score = int(scorecard["score"])
    publication.grade = str(scorecard["grade"])
    publication.total_models = int(scorecard["total_models"])
    publication.approved_models = int(scorecard["approved_models"])
    publication.bias_audits = int(scorecard["bias_audits"])
    publication.pending_appeals = int(scorecard["pending_appeals"])
    publication.ledger_valid = bool(scorecard["ledger_valid"])
    publication.public_summary = str(scorecard["public_summary"])
    publication.improvement_actions = action_text
    publication.published_comment_count = int(published_comments or 0)
    publication.flagged_comment_count = int(flagged_comments or 0)
    publication.snapshot_hash = hashlib.sha256(
        json.dumps(snapshot_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    publication.published_by_person_id = identity.person_id
    publication.published_at = published_at
    if existing is None:
        db.add(publication)
    await db.commit()
    await db.refresh(publication)
    return publication


def scorecard_period_label(value: datetime) -> str:
    quarter = ((value.month - 1) // 3) + 1
    return f"{value.year}-Q{quarter}"


def scorecard_period_due_at(value: datetime) -> datetime:
    quarter = ((value.month - 1) // 3) + 1
    if quarter == 4:
        next_quarter_start = datetime(value.year + 1, 1, 1, tzinfo=UTC)
    else:
        next_quarter_start = datetime(value.year, quarter * 3 + 1, 1, tzinfo=UTC)
    return next_quarter_start - timedelta(seconds=1)


def scorecard_publication_readiness_state(
    current_period_published: bool,
    days_until_due: int,
    ledger_valid: bool,
    flagged_comment_count: int,
    pending_appeal_count: int,
    approved_models: int,
    total_models: int,
) -> tuple[str, str]:
    if current_period_published:
        return "published", "Current quarter is published; monitor comments and prepare the next snapshot."
    if not ledger_valid:
        return "blocked", "Repair the AI run ledger before publishing a public scorecard."
    if flagged_comment_count:
        return "needs_review", "Moderate flagged public scorecard feedback before publication."
    if pending_appeal_count:
        return "needs_review", "Resolve pending AI decision appeals before publication."
    if total_models and approved_models < total_models:
        return "needs_review", "Approve, block, or retire all registered model policies before publication."
    if days_until_due <= 14:
        return "due_soon", "Publish the current quarter scorecard snapshot before the due date."
    return "on_track", "Publication is on track; keep audits, appeals, and comments current."


def scorecard_publication_actions(publication: AgentScorecardPublication) -> list[str]:
    try:
        parsed = json.loads(publication.improvement_actions)
    except json.JSONDecodeError:
        return [publication.improvement_actions]
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return [str(parsed)]


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


async def apply_agent_worker_callback(
    db: AsyncSession,
    payload: AgentWorkerCallbackCreate,
    settings: Settings | None = None,
) -> tuple[AgentTask, bool, str, UUID | None]:
    existing = await db.scalar(
        select(AgentRunRecord).where(AgentRunRecord.idempotency_key == payload.idempotency_key)
    )
    if existing is not None:
        existing_task = await db.get(AgentTask, existing.task_id)
        if existing_task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent task not found")
        return existing_task, True, "Duplicate agent worker callback ignored.", existing.id
    task = await db.get(AgentTask, payload.task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent task not found")
    agent = await db.get(Agent, task.agent_id)
    if agent is None or agent.organization_id != task.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    task.status = payload.status
    if payload.output_ref is not None:
        task.output_ref = payload.output_ref
    if payload.review_notes is not None:
        task.review_notes = payload.review_notes
    record = await append_agent_run_record(
        db,
        agent,
        task,
        None,
        event_type="worker_callback",
        settings=settings or get_settings(),
        finished_at=datetime.now(UTC),
        idempotency_key=payload.idempotency_key,
        governance_note=agent_worker_callback_governance_note(payload),
    )
    await db.commit()
    await db.refresh(task)
    await db.refresh(record)
    return task, False, "Agent worker callback accepted.", record.id


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
    identity: CurrentIdentity | None,
    event_type: str,
    settings: Settings,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    duration_ms: int | None = None,
    idempotency_key: str | None = None,
    governance_note: str | None = None,
) -> AgentRunRecord:
    sequence = await agent_task_record_sequence(db, task.id)
    ledger_sequence = await next_agent_ledger_sequence(db, task.organization_id)
    previous_hash = await latest_agent_record_hash(db, task.organization_id)
    model_policy = agent.model_policy or settings.agent_default_model
    note = governance_note or governance_notes(agent, task)
    selected_idempotency_key = idempotency_key or f"{task.id}:{event_type}:{sequence}"
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
            "executed_by_person_id": str(identity.person_id) if identity and identity.person_id else None,
            "ledger_sequence": ledger_sequence,
            "governance_notes": note,
            "idempotency_key": selected_idempotency_key,
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
        executed_by_person_id=identity.person_id if identity else None,
        ledger_sequence=ledger_sequence,
        governance_notes=note,
        idempotency_key=selected_idempotency_key,
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


def validate_agent_worker_callback_signature(
    raw_body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
    settings: Settings | None = None,
) -> tuple[bool, bool]:
    selected_settings = settings or get_settings()
    signing_key = selected_settings.agent_webhook_key
    if not signing_key:
        return False, False
    if not timestamp_header or not signature_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing agent worker callback signature")
    try:
        timestamp = int(timestamp_header)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid agent worker callback timestamp") from exc
    if abs(int(time.time()) - timestamp) > selected_settings.agent_webhook_tolerance_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Stale agent worker callback signature")
    expected = agent_execution_signature(signing_key, timestamp_header, raw_body)
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid agent worker callback signature")
    return True, True


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
    registry: AgentModelRegistry | None = None,
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
        "registry_status": registry.review_status if registry else None,
        "registered_risk_tier": registry.risk_tier if registry else None,
        "documentation_url": registry.documentation_url if registry else None,
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
    if any(item["registry_status"] not in {"approved", "retired"} for item in model_items):
        recommendations.append("Register and approve every active model policy before production side effects.")
    if any(item["human_review_runs"] for item in model_items):
        recommendations.append("Clear human review queues before enabling downstream side effects.")
    if not recommendations:
        recommendations.append("Continue periodic transparency review and preserve the hash-chained run ledger.")
    return recommendations


def agent_ethics_score(
    total_models: int,
    approved_models: int,
    undocumented_models: int,
    audits: list[AgentBiasAudit],
    failing_bias_audits: int,
    open_mitigations: int,
    pending_appeals: int,
    human_review_required: int,
    ledger_valid: bool,
    webhook_key_configured: bool,
) -> int:
    score = 100
    if total_models == 0:
        score -= 30
    else:
        score -= int(((total_models - approved_models) / total_models) * 25)
        score -= int((undocumented_models / total_models) * 15)
    if not audits:
        score -= 20
    score -= min(failing_bias_audits * 12, 24)
    score -= min(open_mitigations * 8, 24)
    score -= min(pending_appeals * 5, 20)
    score -= min(human_review_required * 2, 16)
    if not ledger_valid:
        score -= 30
    if not webhook_key_configured:
        score -= 4
    return max(score, 0)


def agent_ethics_grade(score: int) -> str:
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "strong"
    if score >= 60:
        return "watch"
    if score >= 40:
        return "risk"
    return "critical"


def agent_ethics_public_summary(
    score: int,
    grade: str,
    total_models: int,
    bias_audits: int,
    pending_appeals: int,
) -> str:
    return (
        f"Ethical AI score {score}/100 ({grade}) across {total_models} registered model policies, "
        f"{bias_audits} fairness audits, and {pending_appeals} pending appeals."
    )


def agent_ethics_improvement_actions(
    total_models: int,
    approved_models: int,
    undocumented_models: int,
    audits: list[AgentBiasAudit],
    failing_bias_audits: int,
    open_mitigations: int,
    pending_appeals: int,
    human_review_required: int,
    ledger_valid: bool,
) -> list[str]:
    actions: list[str] = []
    if total_models == 0:
        actions.append("Register active model policies before public AI claims.")
    elif approved_models < total_models:
        actions.append("Approve, block, or retire every registered model policy.")
    if undocumented_models:
        actions.append("Attach model documentation URLs for public transparency.")
    if not audits:
        actions.append("Run fairness audits for each active model policy.")
    if failing_bias_audits:
        actions.append("Block or mitigate models with failing bias audits.")
    if open_mitigations:
        actions.append("Close open bias-mitigation actions with documented evidence.")
    if pending_appeals:
        actions.append("Resolve pending AI decision appeals within the due window.")
    if human_review_required:
        actions.append("Clear human-review queues before enabling downstream automation.")
    if not ledger_valid:
        actions.append("Freeze applied AI actions until the run ledger verifies cleanly.")
    if not actions:
        actions.append("Publish the scorecard and keep quarterly fairness monitoring active.")
    return actions


async def linked_family_athlete_refs(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> tuple[dict[str, str], list[UUID], list[UUID]]:
    rows = (
        await db.execute(
            select(AthleteProfile, Person)
            .join(Person, Person.id == AthleteProfile.person_id)
            .join(GuardianRelationship, GuardianRelationship.athlete_person_id == AthleteProfile.person_id)
            .where(AthleteProfile.organization_id == organization_id)
            .where(GuardianRelationship.guardian_person_id == identity.person_id)
            .order_by(Person.display_name)
        )
    ).all()
    names: dict[str, str] = {}
    profile_ids: list[UUID] = []
    person_ids: list[UUID] = []
    for profile, person in rows:
        profile_ids.append(profile.id)
        person_ids.append(profile.person_id)
        names[f"athlete_profile:{profile.id}"] = person.display_name
        names[f"athlete:{profile.person_id}"] = person.display_name
    return names, profile_ids, person_ids


def athlete_name_for_task_ref(input_ref: str | None, athlete_names: dict[str, str]) -> str | None:
    if input_ref is None:
        return None
    return athlete_names.get(input_ref)


def slug_for_filename(value: str) -> str:
    normalized = "".join(character.lower() if character.isalnum() else "-" for character in value)
    parts = [part for part in normalized.split("-") if part]
    return "-".join(parts[:6]) or "family"


def render_agent_decision_appeal_form(
    identity: CurrentIdentity,
    agent: Agent,
    task: AgentTask,
    visible_task: dict[str, object],
    latest_appeal: AgentDecisionAppeal | None,
    generated_at: datetime,
    model_policy: str,
    settings: Settings,
) -> str:
    existing_appeal_status = latest_appeal.status if latest_appeal is not None else "not submitted"
    existing_appeal_due = latest_appeal.due_at.isoformat() if latest_appeal is not None else "not assigned"
    athlete_name = visible_task.get("athlete_name") or "Linked family athlete"
    return "\n".join(
        [
            "# AfroLete AI Decision Appeal Form",
            "",
            f"Generated: {generated_at.isoformat()}",
            f"Family account: {identity.display_name} <{identity.email}>",
            f"Athlete: {athlete_name}",
            "",
            "## AI Recommendation",
            "",
            f"Task: {task.title}",
            f"Task ID: {task.id}",
            f"Task type: {task.task_type}",
            f"Status: {task.status.value}",
            f"Agent: {agent.name} ({agent.kind.value})",
            f"Model policy: {model_policy}",
            f"Execution mode: {settings.agent_execution_mode}",
            f"Input reference: {task.input_ref or 'not recorded'}",
            f"Output reference: {task.output_ref or 'not recorded'}",
            f"Review notes: {task.review_notes or 'not recorded'}",
            "",
            "## Existing Appeal",
            "",
            f"Status: {existing_appeal_status}",
            f"Due date: {existing_appeal_due}",
            "",
            "## What We Need Reviewed",
            "",
            "Question or concern:",
            "",
            "Data that may be missing, wrong, or outdated:",
            "",
            "Family context the reviewer should consider:",
            "",
            "Preferred outcome:",
            "",
            "Supporting evidence references or attachments:",
            "",
            "## Review Rights",
            "",
            "A human reviewer should explain the recommendation in plain language, check the source data, "
            "compare reasonable alternatives, and record whether the AI decision is upheld, modified, or overturned.",
            "",
            "Submit this form through the AfroLete family portal or attach it to the relevant support message.",
        ]
    )


def agent_bias_disparity_score(records: list[AgentRunRecord], registry: AgentModelRegistry) -> float:
    if not records:
        return 1.0
    failed_rate = sum(1 for record in records if record.status == AgentTaskStatus.FAILED) / len(records)
    review_rate = sum(1 for record in records if record.status == AgentTaskStatus.WAITING_FOR_REVIEW) / len(records)
    external_rate = sum(1 for record in records if record.execution_mode == "webhook") / len(records)
    risk_weight = {"low": 0.05, "medium": 0.1, "high": 0.18, "critical": 0.25}.get(registry.risk_tier, 0.1)
    score = failed_rate * 0.35 + review_rate * 0.25 + external_rate * 0.2 + risk_weight
    return round(min(score, 1.0), 3)


def agent_bias_audit_status(score: float, sample_size: int) -> tuple[str, str]:
    if sample_size < 5:
        return "insufficient_data", "medium"
    if score >= 0.55:
        return "fail", "critical"
    if score >= 0.3:
        return "watch", "high"
    return "pass", "low"


def agent_bias_findings(
    registry: AgentModelRegistry,
    records: list[AgentRunRecord],
    audit_dimension: str,
    population_slice: str,
    score: float,
) -> str:
    if not records:
        return (
            f"{registry.model_policy} has no run-ledger evidence for {audit_dimension} across "
            f"{population_slice}; collect reviewed outputs before relying on the model."
        )
    failed = sum(1 for record in records if record.status == AgentTaskStatus.FAILED)
    review = sum(1 for record in records if record.status == AgentTaskStatus.WAITING_FOR_REVIEW)
    return (
        f"{registry.model_policy} audit covered {len(records)} run records for {audit_dimension} "
        f"across {population_slice}. Disparity proxy score {score:.3f}; failed={failed}, "
        f"human_review={review}, risk_tier={registry.risk_tier}."
    )


def agent_bias_recommendation(status_value: str, registry: AgentModelRegistry) -> str:
    if status_value == "insufficient_data":
        return "Run representative evaluation tasks before approving side effects or public claims."
    if status_value == "fail":
        return "Block production side effects, review affected decisions, and document mitigation before re-approval."
    if status_value == "watch":
        return "Keep human review active and compare outcomes across protected cohorts before scaling."
    return f"{registry.model_policy} can remain in governed operation with periodic fairness monitoring."


def agent_decision_simple_explanation(agent: Agent, task: AgentTask) -> str:
    if task.status == AgentTaskStatus.WAITING_FOR_REVIEW:
        return f"{agent.name} produced a recommendation that is waiting for human review before action."
    if task.status == AgentTaskStatus.FAILED:
        return f"{agent.name} could not complete the recommendation and the failure should be reviewed."
    return f"{agent.name} produced an output for {task.title}; the appeal requests human review of that output."


def agent_decision_technical_explanation(
    agent: Agent,
    task: AgentTask,
    model_policy: str,
    settings: Settings,
) -> str:
    return (
        f"Task {task.id} used model policy {model_policy} through {settings.agent_execution_mode} execution. "
        f"Agent kind={agent.kind.value}; task_type={task.task_type}; status={task.status.value}; "
        f"output_ref={task.output_ref or 'none'}."
    )


def agent_decision_data_summary(task: AgentTask) -> str:
    return (
        f"Input reference: {task.input_ref or 'none provided'}. "
        f"Review notes: {task.review_notes or 'no review notes recorded yet'}."
    )


def agent_decision_alternative_options(task: AgentTask) -> str:
    return (
        "Available paths: correct source data, request a human reviewer, rerun the agent after new evidence, "
        f"or mark task {task.id} modified/overturned if the appeal is valid."
    )


def governance_notes(agent: Agent, task: AgentTask) -> str:
    if task.status == AgentTaskStatus.FAILED:
        return "Failed runs require operator review before retry."
    if task.status == AgentTaskStatus.WAITING_FOR_REVIEW:
        return f"{agent.name} output must be reviewed by a human before side effects are applied."
    if task.status == AgentTaskStatus.COMPLETED:
        return "Task completed after review or explicit operator action."
    return "Task is tracked in the governance ledger for audit and billing."


def agent_worker_callback_governance_note(payload: AgentWorkerCallbackCreate) -> str:
    if payload.status == AgentTaskStatus.FAILED:
        return "External worker reported failure; operator review is required before retry."
    if payload.status == AgentTaskStatus.WAITING_FOR_REVIEW:
        return "External worker returned output that requires human review before side effects are applied."
    if payload.status == AgentTaskStatus.COMPLETED:
        return "External worker marked the task complete through a signed callback."
    return "External worker callback updated the governed agent task state."
