from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import AgentKind, AgentTaskStatus


class Agent(IdMixin, TimestampMixin, Base):
    __tablename__ = "agents"

    organization_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    kind: Mapped[AgentKind] = mapped_column(enum_type(AgentKind), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)
    model_policy: Mapped[str | None] = mapped_column(String(120))


class AgentAssignment(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_assignments"

    agent_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("agents.id"), index=True)
    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    scope_type: Mapped[str] = mapped_column(String(80), nullable=False)
    scope_id: Mapped[str] = mapped_column(String(120), nullable=False)
    granted_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))


class AgentTask(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_tasks"

    agent_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("agents.id"), index=True)
    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    task_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[AgentTaskStatus] = mapped_column(
        enum_type(AgentTaskStatus),
        default=AgentTaskStatus.QUEUED,
        nullable=False,
        index=True,
    )
    requested_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    input_ref: Mapped[str | None] = mapped_column(String(500))
    output_ref: Mapped[str | None] = mapped_column(String(500))
    review_notes: Mapped[str | None] = mapped_column(Text)
    review_assigned_to_person_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("persons.id"), index=True
    )
    review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    review_priority: Mapped[str] = mapped_column(String(40), default="normal", nullable=False, index=True)
    review_assignment_notes: Mapped[str | None] = mapped_column(Text)
    approval_required_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    approval_approved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    approval_rejected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    approval_status: Mapped[str] = mapped_column(String(40), default="not_requested", nullable=False, index=True)
    approval_last_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    governance_policy_rule_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("agent_governance_policy_rules.id"), index=True
    )
    governance_policy_code: Mapped[str | None] = mapped_column(String(120), index=True)
    governance_policy_decision: Mapped[str | None] = mapped_column(String(40), index=True)
    governance_policy_risk_level: Mapped[str | None] = mapped_column(String(40), index=True)
    governance_policy_rationale: Mapped[str | None] = mapped_column(Text)


class AgentGovernancePolicyRule(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_governance_policy_rules"
    __table_args__ = (
        UniqueConstraint("organization_id", "rule_code", name="uq_agent_governance_policy_rules_org_code"),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    rule_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    agent_kind: Mapped[str | None] = mapped_column(String(80), index=True)
    task_type_contains: Mapped[str | None] = mapped_column(String(120), index=True)
    model_policy_contains: Mapped[str | None] = mapped_column(String(120), index=True)
    input_ref_contains: Mapped[str | None] = mapped_column(String(160), index=True)
    decision: Mapped[str] = mapped_column(String(40), default="require_approval", nullable=False, index=True)
    required_approval_count: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(40), default="high", nullable=False, index=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)


class AgentGovernancePolicyHistorySnapshot(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_governance_policy_history_snapshots"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    snapshot_label: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    artifact_format: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    download_filename: Mapped[str] = mapped_column(String(240), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    governed_task_count: Mapped[int] = mapped_column(Integer, nullable=False)
    approval_required_count: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_count: Mapped[int] = mapped_column(Integer, nullable=False)
    waiting_for_review_count: Mapped[int] = mapped_column(Integer, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False)
    policy_count: Mapped[int] = mapped_column(Integer, nullable=False)
    latest_policy_code: Mapped[str | None] = mapped_column(String(120), index=True)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class AgentTaskApproval(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_task_approvals"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    task_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("agent_tasks.id"), index=True)
    reviewer_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    reviewer_label: Mapped[str | None] = mapped_column(String(160), index=True)
    requested_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False, index=True)
    request_notes: Mapped[str | None] = mapped_column(Text)
    decision_notes: Mapped[str | None] = mapped_column(Text)
    decided_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)


class AgentRunRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_run_records"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_agent_run_records_idempotency_key"),
        UniqueConstraint("organization_id", "external_event_id", name="uq_agent_run_records_org_external_event"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    agent_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("agents.id"), index=True)
    task_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("agent_tasks.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[AgentTaskStatus] = mapped_column(
        enum_type(AgentTaskStatus),
        nullable=False,
        index=True,
    )
    model_policy: Mapped[str] = mapped_column(String(120), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    input_ref: Mapped[str | None] = mapped_column(String(500))
    output_ref: Mapped[str | None] = mapped_column(String(500))
    review_notes: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    executed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    ledger_sequence: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    governance_notes: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    external_event_id: Mapped[str | None] = mapped_column(String(180), index=True)
    callback_payload_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    callback_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    previous_record_hash: Mapped[str | None] = mapped_column(String(128))
    record_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)


class AgentModelRegistry(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_model_registry"
    __table_args__ = (
        UniqueConstraint("organization_id", "model_policy", name="uq_agent_model_registry_org_policy"),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    model_policy: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(120), default="local", nullable=False, index=True)
    model_family: Mapped[str | None] = mapped_column(String(120), index=True)
    version: Mapped[str | None] = mapped_column(String(120), index=True)
    use_case: Mapped[str] = mapped_column(Text, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(40), default="medium", nullable=False, index=True)
    review_status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    documentation_url: Mapped[str | None] = mapped_column(String(500))
    evaluation_summary: Mapped[str | None] = mapped_column(Text)
    limitations: Mapped[str | None] = mapped_column(Text)
    bias_notes: Mapped[str | None] = mapped_column(Text)
    data_residency: Mapped[str | None] = mapped_column(String(120), index=True)
    owner_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    approved_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class AgentBiasAudit(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_bias_audits"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    model_registry_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("agent_model_registry.id"), index=True
    )
    model_policy: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    audit_dimension: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    population_slice: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    disparity_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    findings: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    mitigation_status: Mapped[str] = mapped_column(String(40), default="open", nullable=False, index=True)
    mitigation_action: Mapped[str | None] = mapped_column(Text)
    mitigation_evidence_ref: Mapped[str | None] = mapped_column(String(500))
    mitigated_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    mitigated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    audited_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    audited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class AgentDecisionAppeal(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_decision_appeals"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    agent_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("agents.id"), index=True)
    task_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("agent_tasks.id"), index=True)
    model_policy: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    simple_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    technical_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    data_summary: Mapped[str] = mapped_column(Text, nullable=False)
    alternative_options: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_evidence_ref: Mapped[str | None] = mapped_column(String(500))
    submitted_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    resolved_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class AgentScorecardComment(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_scorecard_comments"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    affiliation: Mapped[str | None] = mapped_column(String(160), index=True)
    contact_email: Mapped[str | None] = mapped_column(String(320))
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="published", nullable=False, index=True)
    consent_to_publish: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    abuse_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    abuse_reason: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class AgentScorecardPublication(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_scorecard_publications"
    __table_args__ = (
        UniqueConstraint("organization_id", "period_label", name="uq_agent_scorecard_publications_org_period"),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    period_label: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="published", nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    grade: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    total_models: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_models: Mapped[int] = mapped_column(Integer, nullable=False)
    bias_audits: Mapped[int] = mapped_column(Integer, nullable=False)
    pending_appeals: Mapped[int] = mapped_column(Integer, nullable=False)
    ledger_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    public_summary: Mapped[str] = mapped_column(Text, nullable=False)
    improvement_actions: Mapped[str] = mapped_column(Text, nullable=False)
    published_comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    flagged_comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    published_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class AgentScorecardArtifactAccess(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_scorecard_artifact_accesses"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    publication_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("agent_scorecard_publications.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    artifact_format: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(240), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    signed_url: Mapped[str | None] = mapped_column(String(1000))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    request_ip: Mapped[str | None] = mapped_column(String(80), index=True)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    request_source: Mapped[str | None] = mapped_column(String(80), index=True)
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
