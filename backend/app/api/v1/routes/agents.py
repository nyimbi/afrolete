from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.agent import (
    AgentAssignmentCreate,
    AgentAssignmentRead,
    AgentBiasAuditCreate,
    AgentBiasAuditMitigationUpdate,
    AgentBiasAuditRead,
    AgentDecisionAppealCreate,
    AgentDecisionAppealFormRead,
    AgentDecisionAppealRead,
    AgentDecisionAppealUpdate,
    AgentEthicalScorecardRead,
    AgentFamilyTaskRead,
    AgentGovernancePolicyHistoryExportRead,
    AgentGovernancePolicyHistoryRead,
    AgentGovernancePolicyHistorySnapshotCreate,
    AgentGovernancePolicyHistorySnapshotRead,
    AgentGovernancePolicyRuleCreate,
    AgentGovernancePolicyReportRead,
    AgentGovernancePolicyRuleRead,
    AgentGovernancePolicySimulationCreate,
    AgentGovernancePolicySimulationRead,
    AgentGovernancePolicyRuleUpdate,
    AgentGovernanceSummaryRead,
    AgentModelRegistryCreate,
    AgentModelGovernanceEvidenceArtifactRead,
    AgentModelRegistryRead,
    AgentModelRegistryUpdate,
    AgentModelTransparencyReportRead,
    AgentMyDecisionAppealCreate,
    AgentRunLedgerVerificationRead,
    AgentRunRecordRead,
    AgentScorecardAutomationRunCreate,
    AgentScorecardAutomationRunRead,
    AgentScorecardCommentCreate,
    AgentScorecardCommentModerationRead,
    AgentScorecardCommentRead,
    AgentScorecardCommentUpdate,
    AgentScorecardArtifactAccessRead,
    AgentScorecardArtifactAccessSummaryRead,
    AgentScorecardArtifactAnomalyAlertCreate,
    AgentScorecardArtifactAnomalyAlertRead,
    AgentScorecardArtifactAnomalyAlertRunCreate,
    AgentScorecardArtifactAnomalyAlertRunRead,
    AgentScorecardPublicationCreate,
    AgentScorecardPublicationArtifactLinkRead,
    AgentScorecardPublicationArtifactRead,
    AgentScorecardPublicationReadinessRead,
    AgentScorecardPublicationRead,
    AgentScorecardPublicationReminderCreate,
    AgentScorecardPublicationReminderRead,
    AgentScorecardPublicationReminderRunCreate,
    AgentScorecardPublicationReminderRunRead,
    AgentCreate,
    AgentRead,
    AgentTaskCreate,
    AgentTaskApprovalDecisionUpdate,
    AgentTaskApprovalRead,
    AgentTaskApprovalRequestCreate,
    AgentTaskReviewAssignmentUpdate,
    AgentTaskReviewQueueItemRead,
    AgentTaskReviewQueueSummaryRead,
    AgentTaskRead,
    AgentTaskUpdate,
    AgentWorkerCallbackCreate,
    AgentWorkerCallbackRead,
)
from app.services.agents import (
    apply_agent_worker_callback,
    agent_ethical_scorecard,
    agent_governance_policy_report,
    agent_governance_policy_history,
    agent_governance_summary,
    agent_model_transparency_report,
    agent_scorecard_publication_readiness,
    agent_run_records,
    assign_agent,
    create_agent,
    create_agent_governance_policy_history_snapshot,
    create_agent_governance_policy_rule,
    create_agent_model_registry,
    create_agent_scorecard_comment,
    deliver_scorecard_artifact_anomaly_alert,
    deliver_agent_scorecard_publication_reminder,
    execute_agent_task,
    export_agent_governance_policy_history,
    get_agent_scorecard_publication_artifact,
    get_agent_model_governance_evidence_artifact,
    get_my_agent_decision_appeal_form,
    list_scorecard_artifact_accesses,
    list_agent_assignments,
    list_agent_bias_audits,
    list_agent_decision_appeals,
    list_agent_governance_policy_history_snapshots,
    list_agent_governance_policy_rules,
    list_agent_model_registry,
    list_agent_task_approvals,
    list_agent_task_review_queue,
    list_agent_scorecard_comments,
    list_agent_scorecard_comments_for_moderation,
    list_agent_scorecard_publications,
    list_agent_tasks,
    list_agents,
    list_my_agent_family_tasks,
    list_my_agent_decision_appeals,
    queue_agent_task,
    request_agent_task_approvals,
    decide_agent_task_approval,
    publish_agent_scorecard,
    read_signed_agent_scorecard_publication_artifact,
    record_scorecard_artifact_access,
    run_agent_scorecard_automation,
    run_agent_scorecard_publication_reminder,
    run_agent_bias_audit,
    run_scorecard_artifact_anomaly_alert,
    scorecard_artifact_access_summary,
    signed_agent_scorecard_publication_artifact_access,
    simulate_agent_governance_policy,
    submit_agent_decision_appeal,
    submit_my_agent_decision_appeal,
    update_agent_decision_appeal,
    update_agent_bias_audit_mitigation,
    update_agent_governance_policy_rule,
    update_agent_model_registry,
    update_agent_scorecard_comment,
    update_agent_task,
    update_agent_task_review_assignment,
    validate_agent_worker_callback_signature,
    verify_agent_run_ledger,
    scorecard_publication_actions,
    agent_task_review_queue_summary,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service

router = APIRouter(prefix="/agents", tags=["agents"])


def requester_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()[:80]
    return request.client.host[:80] if request.client else None


def request_user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    user_agent = request.headers.get("user-agent")
    return user_agent[:500] if user_agent else None


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


def to_task_review_queue_item_read(item: dict[str, object]) -> AgentTaskReviewQueueItemRead:
    return AgentTaskReviewQueueItemRead(
        task=to_task_read(item["task"]),
        agent_name=str(item["agent_name"]),
        review_assigned_to_name=(
            str(item["review_assigned_to_name"]) if item["review_assigned_to_name"] else None
        ),
        review_sla_state=str(item["review_sla_state"]),
        review_age_hours=int(item["review_age_hours"]),
        pending_approval_count=int(item["pending_approval_count"]),
    )


def to_task_approval_read(approval) -> AgentTaskApprovalRead:
    return AgentTaskApprovalRead(
        id=approval.id,
        organization_id=approval.organization_id,
        task_id=approval.task_id,
        reviewer_person_id=approval.reviewer_person_id,
        reviewer_label=approval.reviewer_label,
        requested_by_person_id=approval.requested_by_person_id,
        status=approval.status,
        request_notes=approval.request_notes,
        decision_notes=approval.decision_notes,
        decided_by_person_id=approval.decided_by_person_id,
        decided_at=approval.decided_at,
        sequence=approval.sequence,
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
        mitigation_action=audit.mitigation_action,
        mitigation_evidence_ref=audit.mitigation_evidence_ref,
        mitigated_by_person_id=audit.mitigated_by_person_id,
        mitigated_at=audit.mitigated_at,
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


def to_scorecard_comment_read(comment) -> AgentScorecardCommentRead:
    return AgentScorecardCommentRead(
        id=comment.id,
        organization_id=comment.organization_id,
        display_name=comment.display_name,
        affiliation=comment.affiliation,
        comment=comment.comment,
        status=comment.status,
        consent_to_publish=comment.consent_to_publish,
        submitted_at=comment.submitted_at,
    )


def to_scorecard_comment_moderation_read(comment) -> AgentScorecardCommentModerationRead:
    return AgentScorecardCommentModerationRead(
        id=comment.id,
        organization_id=comment.organization_id,
        display_name=comment.display_name,
        affiliation=comment.affiliation,
        contact_email=comment.contact_email,
        comment=comment.comment,
        status=comment.status,
        consent_to_publish=comment.consent_to_publish,
        abuse_score=comment.abuse_score,
        abuse_reason=comment.abuse_reason,
        submitted_at=comment.submitted_at,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


def to_scorecard_publication_read(publication) -> AgentScorecardPublicationRead:
    return AgentScorecardPublicationRead(
        id=publication.id,
        organization_id=publication.organization_id,
        period_label=publication.period_label,
        status=publication.status,
        score=publication.score,
        grade=publication.grade,
        total_models=publication.total_models,
        approved_models=publication.approved_models,
        bias_audits=publication.bias_audits,
        pending_appeals=publication.pending_appeals,
        ledger_valid=publication.ledger_valid,
        public_summary=publication.public_summary,
        improvement_actions=scorecard_publication_actions(publication),
        published_comment_count=publication.published_comment_count,
        flagged_comment_count=publication.flagged_comment_count,
        snapshot_hash=publication.snapshot_hash,
        published_by_person_id=publication.published_by_person_id,
        published_at=publication.published_at,
    )


def to_policy_history_snapshot_read(snapshot) -> AgentGovernancePolicyHistorySnapshotRead:
    return AgentGovernancePolicyHistorySnapshotRead(
        id=snapshot.id,
        organization_id=snapshot.organization_id,
        snapshot_label=snapshot.snapshot_label,
        artifact_format=snapshot.artifact_format,
        content_type=snapshot.content_type,
        download_filename=snapshot.download_filename,
        content=snapshot.content,
        checksum=snapshot.checksum,
        size_bytes=snapshot.size_bytes,
        governed_task_count=snapshot.governed_task_count,
        approval_required_count=snapshot.approval_required_count,
        completed_count=snapshot.completed_count,
        waiting_for_review_count=snapshot.waiting_for_review_count,
        failed_count=snapshot.failed_count,
        policy_count=snapshot.policy_count,
        latest_policy_code=snapshot.latest_policy_code,
        recommendation=snapshot.recommendation,
        generated_by_person_id=snapshot.generated_by_person_id,
        generated_at=snapshot.generated_at,
        created_at=snapshot.created_at,
        updated_at=snapshot.updated_at,
    )


def to_scorecard_artifact_access_read(access) -> AgentScorecardArtifactAccessRead:
    return AgentScorecardArtifactAccessRead(
        id=access.id,
        organization_id=access.organization_id,
        publication_id=access.publication_id,
        event_type=access.event_type,
        artifact_format=access.artifact_format,
        filename=access.filename,
        content_type=access.content_type,
        checksum=access.checksum,
        size_bytes=access.size_bytes,
        signed_url=access.signed_url,
        expires_at=access.expires_at,
        request_ip=access.request_ip,
        user_agent=access.user_agent,
        request_source=access.request_source,
        accessed_at=access.accessed_at,
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


@router.get("/my-appeals", response_model=list[AgentDecisionAppealRead])
async def list_my_agent_decision_appeals_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[AgentDecisionAppealRead]:
    return [
        to_decision_appeal_read(appeal)
        for appeal in await list_my_agent_decision_appeals(db, identity, organization_id)
    ]


@router.get("/my-family-tasks", response_model=list[AgentFamilyTaskRead])
async def list_my_agent_family_tasks_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[AgentFamilyTaskRead]:
    return [
        AgentFamilyTaskRead(**task)
        for task in await list_my_agent_family_tasks(db, identity, organization_id)
    ]


@router.get("/my-family-tasks/{task_id}/appeal-form", response_model=AgentDecisionAppealFormRead)
async def get_my_agent_decision_appeal_form_route(
    task_id: UUID,
    organization_id: UUID = Query(),
    artifact_format: str = Query(default="markdown", pattern="^(markdown|pdf)$"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> AgentDecisionAppealFormRead:
    return AgentDecisionAppealFormRead(
        **await get_my_agent_decision_appeal_form(db, identity, organization_id, task_id, artifact_format)
    )


@router.post("/my-appeals", response_model=AgentDecisionAppealRead, status_code=status.HTTP_201_CREATED)
async def submit_my_agent_decision_appeal_route(
    payload: AgentMyDecisionAppealCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> AgentDecisionAppealRead:
    return to_decision_appeal_read(
        await submit_my_agent_decision_appeal(db, identity, payload)
    )


@router.get("/ethical-scorecard", response_model=AgentEthicalScorecardRead)
async def agent_ethical_scorecard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> AgentEthicalScorecardRead:
    return AgentEthicalScorecardRead(**await agent_ethical_scorecard(db, organization_id))


@router.get("/ethical-scorecard/comments", response_model=list[AgentScorecardCommentRead])
async def list_agent_scorecard_comments_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AgentScorecardCommentRead]:
    return [
        to_scorecard_comment_read(comment)
        for comment in await list_agent_scorecard_comments(db, organization_id)
    ]


@router.post("/ethical-scorecard/comments", response_model=AgentScorecardCommentRead, status_code=201)
async def create_agent_scorecard_comment_route(
    payload: AgentScorecardCommentCreate,
    db: AsyncSession = Depends(get_db),
) -> AgentScorecardCommentRead:
    return to_scorecard_comment_read(await create_agent_scorecard_comment(db, payload))


@router.get("/ethical-scorecard/comments/moderation", response_model=list[AgentScorecardCommentModerationRead])
async def list_agent_scorecard_comments_for_moderation_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[AgentScorecardCommentModerationRead]:
    return [
        to_scorecard_comment_moderation_read(comment)
        for comment in await list_agent_scorecard_comments_for_moderation(db, identity, organization_id, authz)
    ]


@router.patch("/ethical-scorecard/comments/{comment_id}", response_model=AgentScorecardCommentModerationRead)
async def update_agent_scorecard_comment_route(
    comment_id: UUID,
    payload: AgentScorecardCommentUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentScorecardCommentModerationRead:
    return to_scorecard_comment_moderation_read(
        await update_agent_scorecard_comment(db, identity, comment_id, payload, authz)
    )


@router.get("/ethical-scorecard/publications", response_model=list[AgentScorecardPublicationRead])
async def list_agent_scorecard_publications_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AgentScorecardPublicationRead]:
    return [
        to_scorecard_publication_read(publication)
        for publication in await list_agent_scorecard_publications(db, organization_id)
    ]


@router.get("/ethical-scorecard/artifact-accesses", response_model=list[AgentScorecardArtifactAccessRead])
async def list_scorecard_artifact_accesses_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[AgentScorecardArtifactAccessRead]:
    return [
        to_scorecard_artifact_access_read(access)
        for access in await list_scorecard_artifact_accesses(db, identity, organization_id, authz)
    ]


@router.get("/ethical-scorecard/artifact-accesses/summary", response_model=AgentScorecardArtifactAccessSummaryRead)
async def scorecard_artifact_access_summary_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentScorecardArtifactAccessSummaryRead:
    return AgentScorecardArtifactAccessSummaryRead(
        **await scorecard_artifact_access_summary(db, identity, organization_id, authz)
    )


@router.post("/ethical-scorecard/artifact-accesses/anomaly-alert", response_model=AgentScorecardArtifactAnomalyAlertRead)
async def deliver_scorecard_artifact_anomaly_alert_route(
    payload: AgentScorecardArtifactAnomalyAlertCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentScorecardArtifactAnomalyAlertRead:
    return AgentScorecardArtifactAnomalyAlertRead(
        **await deliver_scorecard_artifact_anomaly_alert(db, identity, payload, authz)
    )


@router.post(
    "/ethical-scorecard/artifact-accesses/anomaly-alert-run",
    response_model=AgentScorecardArtifactAnomalyAlertRunRead,
)
async def run_scorecard_artifact_anomaly_alert_route(
    payload: AgentScorecardArtifactAnomalyAlertRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentScorecardArtifactAnomalyAlertRunRead:
    return AgentScorecardArtifactAnomalyAlertRunRead(
        **await run_scorecard_artifact_anomaly_alert(db, identity, payload, authz)
    )


@router.get("/ethical-scorecard/publications/readiness", response_model=AgentScorecardPublicationReadinessRead)
async def agent_scorecard_publication_readiness_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> AgentScorecardPublicationReadinessRead:
    return AgentScorecardPublicationReadinessRead(
        **await agent_scorecard_publication_readiness(db, organization_id)
    )


@router.post("/ethical-scorecard/publications/reminder", response_model=AgentScorecardPublicationReminderRead)
async def deliver_agent_scorecard_publication_reminder_route(
    payload: AgentScorecardPublicationReminderCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentScorecardPublicationReminderRead:
    return AgentScorecardPublicationReminderRead(
        **await deliver_agent_scorecard_publication_reminder(db, identity, payload, authz)
    )


@router.post("/ethical-scorecard/publications/reminder-run", response_model=AgentScorecardPublicationReminderRunRead)
async def run_agent_scorecard_publication_reminder_route(
    payload: AgentScorecardPublicationReminderRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentScorecardPublicationReminderRunRead:
    return AgentScorecardPublicationReminderRunRead(
        **await run_agent_scorecard_publication_reminder(db, identity, payload, authz)
    )


@router.post("/ethical-scorecard/automation/run", response_model=AgentScorecardAutomationRunRead)
async def run_agent_scorecard_automation_route(
    payload: AgentScorecardAutomationRunCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentScorecardAutomationRunRead:
    return AgentScorecardAutomationRunRead(
        **await run_agent_scorecard_automation(db, identity, payload, authz)
    )


@router.get("/ethical-scorecard/publications/{publication_id}/artifact", response_model=AgentScorecardPublicationArtifactRead)
async def get_agent_scorecard_publication_artifact_route(
    publication_id: UUID,
    artifact_format: str = Query(default="markdown", pattern="^(markdown|pdf)$"),
    db: AsyncSession = Depends(get_db),
) -> AgentScorecardPublicationArtifactRead:
    return AgentScorecardPublicationArtifactRead(
        **await get_agent_scorecard_publication_artifact(db, publication_id, artifact_format)
    )


@router.post(
    "/ethical-scorecard/publications/{publication_id}/artifact-link",
    response_model=AgentScorecardPublicationArtifactLinkRead,
)
async def create_agent_scorecard_publication_artifact_link_route(
    publication_id: UUID,
    request: Request,
    artifact_format: str = Query(default="pdf", pattern="^(markdown|pdf)$"),
    ttl_seconds: int | None = Query(default=None, ge=60, le=86400),
    db: AsyncSession = Depends(get_db),
) -> AgentScorecardPublicationArtifactLinkRead:
    return AgentScorecardPublicationArtifactLinkRead(
        **await signed_agent_scorecard_publication_artifact_access(
            db,
            publication_id,
            artifact_format,
            ttl_seconds,
            requester_ip(request),
            request_user_agent(request),
            "artifact_link_created",
        )
    )


@router.get("/ethical-scorecard/artifacts/{organization_id}/{publication_id}/{filename}")
async def read_agent_scorecard_artifact_route(
    organization_id: UUID,
    publication_id: UUID,
    filename: str,
    request: Request,
    expires: int = Query(),
    signature: str = Query(),
    db: AsyncSession = Depends(get_db),
) -> Response:
    artifact = read_signed_agent_scorecard_publication_artifact(
        organization_id,
        publication_id,
        filename,
        expires,
        signature,
    )
    await record_scorecard_artifact_access(
        db,
        organization_id=organization_id,
        publication_id=publication_id,
        event_type="artifact_opened",
        artifact_format="pdf" if filename.endswith(".pdf") else "markdown",
        filename=str(artifact["filename"]),
        content_type=str(artifact["content_type"]),
        checksum=str(artifact["checksum"]),
        size_bytes=len(bytes(artifact["content"])),
        signed_url=None,
        expires_at=None,
        request_ip=requester_ip(request),
        user_agent=request_user_agent(request),
        request_source="signed_artifact_opened",
    )
    return Response(
        content=artifact["content"],
        media_type=str(artifact["content_type"]),
        headers={
            "Content-Disposition": f"inline; filename={artifact['filename']}",
            "X-Afrolete-Scorecard-Checksum": str(artifact["checksum"]),
        },
    )


@router.post("/ethical-scorecard/publications", response_model=AgentScorecardPublicationRead, status_code=201)
async def publish_agent_scorecard_route(
    payload: AgentScorecardPublicationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentScorecardPublicationRead:
    return to_scorecard_publication_read(
        await publish_agent_scorecard(db, identity, payload, authz)
    )


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


@router.get("/model-registry/{registry_id}/evidence-artifact", response_model=AgentModelGovernanceEvidenceArtifactRead)
async def get_agent_model_governance_evidence_artifact_route(
    registry_id: UUID,
    artifact_format: str = Query(default="markdown", pattern="^(markdown|csv)$"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentModelGovernanceEvidenceArtifactRead:
    return AgentModelGovernanceEvidenceArtifactRead(
        **await get_agent_model_governance_evidence_artifact(
            db,
            identity,
            registry_id,
            authz,
            artifact_format=artifact_format,
        )
    )


@router.patch("/bias-audits/{audit_id}/mitigation", response_model=AgentBiasAuditRead)
async def update_agent_bias_audit_mitigation_route(
    audit_id: UUID,
    payload: AgentBiasAuditMitigationUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentBiasAuditRead:
    return to_bias_audit_read(
        await update_agent_bias_audit_mitigation(db, identity, audit_id, payload, authz)
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


@router.post("/governance-policy-rules", response_model=AgentGovernancePolicyRuleRead, status_code=201)
async def create_agent_governance_policy_rule_route(
    payload: AgentGovernancePolicyRuleCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentGovernancePolicyRuleRead:
    return AgentGovernancePolicyRuleRead(
        **await create_agent_governance_policy_rule(db, identity, payload, authz)
    )


@router.get("/governance-policy-rules", response_model=list[AgentGovernancePolicyRuleRead])
async def list_agent_governance_policy_rules_route(
    organization_id: UUID = Query(),
    active: bool | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[AgentGovernancePolicyRuleRead]:
    return [
        AgentGovernancePolicyRuleRead(**rule)
        for rule in await list_agent_governance_policy_rules(db, identity, organization_id, authz, active=active)
    ]


@router.get("/governance-policy-rules/report", response_model=AgentGovernancePolicyReportRead)
async def agent_governance_policy_report_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentGovernancePolicyReportRead:
    return AgentGovernancePolicyReportRead(
        **await agent_governance_policy_report(db, identity, organization_id, authz)
    )


@router.get("/governance-policy-rules/history", response_model=AgentGovernancePolicyHistoryRead)
async def agent_governance_policy_history_route(
    organization_id: UUID = Query(),
    limit: int = Query(default=120, ge=10, le=500),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentGovernancePolicyHistoryRead:
    return AgentGovernancePolicyHistoryRead(
        **await agent_governance_policy_history(db, identity, organization_id, authz, limit=limit)
    )


@router.get("/governance-policy-rules/history/export", response_model=AgentGovernancePolicyHistoryExportRead)
async def export_agent_governance_policy_history_route(
    organization_id: UUID = Query(),
    artifact_format: str = Query(default="csv", pattern="^(csv|markdown)$"),
    limit: int = Query(default=120, ge=10, le=500),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentGovernancePolicyHistoryExportRead:
    return AgentGovernancePolicyHistoryExportRead(
        **await export_agent_governance_policy_history(
            db,
            identity,
            organization_id,
            authz,
            artifact_format=artifact_format,
            limit=limit,
        )
    )


@router.post(
    "/governance-policy-rules/history/snapshots",
    response_model=AgentGovernancePolicyHistorySnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent_governance_policy_history_snapshot_route(
    payload: AgentGovernancePolicyHistorySnapshotCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentGovernancePolicyHistorySnapshotRead:
    return to_policy_history_snapshot_read(
        await create_agent_governance_policy_history_snapshot(db, identity, payload, authz)
    )


@router.get(
    "/governance-policy-rules/history/snapshots",
    response_model=list[AgentGovernancePolicyHistorySnapshotRead],
)
async def list_agent_governance_policy_history_snapshots_route(
    organization_id: UUID = Query(),
    limit: int = Query(default=20, ge=1, le=100),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[AgentGovernancePolicyHistorySnapshotRead]:
    return [
        to_policy_history_snapshot_read(snapshot)
        for snapshot in await list_agent_governance_policy_history_snapshots(
            db,
            identity,
            organization_id,
            authz,
            limit=limit,
        )
    ]


@router.post("/governance-policy-rules/simulate", response_model=AgentGovernancePolicySimulationRead)
async def simulate_agent_governance_policy_route(
    payload: AgentGovernancePolicySimulationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentGovernancePolicySimulationRead:
    return AgentGovernancePolicySimulationRead(
        **await simulate_agent_governance_policy(db, identity, payload, authz)
    )


@router.patch("/governance-policy-rules/{rule_id}", response_model=AgentGovernancePolicyRuleRead)
async def update_agent_governance_policy_rule_route(
    rule_id: UUID,
    payload: AgentGovernancePolicyRuleUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentGovernancePolicyRuleRead:
    return AgentGovernancePolicyRuleRead(
        **await update_agent_governance_policy_rule(db, identity, rule_id, payload, authz)
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


@router.get("/tasks/review-queue", response_model=list[AgentTaskReviewQueueItemRead])
async def list_agent_task_review_queue_route(
    organization_id: UUID = Query(),
    assignment: str = Query(default="all", pattern="^(all|mine|assigned|unassigned)$"),
    sla: str = Query(default="all", pattern="^(all|unassigned|overdue|due_soon|on_track)$"),
    priority: str = Query(default="all", pattern="^(all|low|normal|high|urgent)$"),
    limit: int = Query(default=25, ge=1, le=100),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[AgentTaskReviewQueueItemRead]:
    return [
        to_task_review_queue_item_read(item)
        for item in await list_agent_task_review_queue(
            db,
            identity,
            organization_id,
            authz,
            limit=limit,
            assignment=assignment,
            sla=sla,
            priority=priority,
        )
    ]


@router.get("/tasks/review-summary", response_model=AgentTaskReviewQueueSummaryRead)
async def agent_task_review_queue_summary_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentTaskReviewQueueSummaryRead:
    return AgentTaskReviewQueueSummaryRead(
        **await agent_task_review_queue_summary(db, identity, organization_id, authz)
    )


@router.get("/tasks/{task_id}/approvals", response_model=list[AgentTaskApprovalRead])
async def list_agent_task_approvals_route(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[AgentTaskApprovalRead]:
    return [
        to_task_approval_read(approval)
        for approval in await list_agent_task_approvals(db, task_id)
    ]


@router.post("/tasks/{task_id}/approvals", response_model=list[AgentTaskApprovalRead], status_code=201)
async def request_agent_task_approvals_route(
    task_id: UUID,
    payload: AgentTaskApprovalRequestCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[AgentTaskApprovalRead]:
    return [
        to_task_approval_read(approval)
        for approval in await request_agent_task_approvals(db, identity, task_id, payload, authz)
    ]


@router.patch("/approvals/{approval_id}", response_model=AgentTaskApprovalRead)
async def decide_agent_task_approval_route(
    approval_id: UUID,
    payload: AgentTaskApprovalDecisionUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentTaskApprovalRead:
    return to_task_approval_read(
        await decide_agent_task_approval(db, identity, approval_id, payload, authz)
    )


@router.patch("/tasks/{task_id}/review-assignment", response_model=AgentTaskRead)
async def update_agent_task_review_assignment_route(
    task_id: UUID,
    payload: AgentTaskReviewAssignmentUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AgentTaskRead:
    return to_task_read(
        await update_agent_task_review_assignment(db, identity, task_id, payload, authz)
    )


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
    signature_required, signature_validated = await validate_agent_worker_callback_signature(
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
