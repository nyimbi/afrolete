from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import AgentKind, AgentTaskStatus, CommunicationChannel


class AgentCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    kind: AgentKind
    purpose: str = Field(min_length=8, max_length=4000)
    model_policy: str | None = Field(default=None, max_length=120)


class AgentRead(BaseModel):
    id: UUID
    organization_id: UUID | None
    name: str
    kind: AgentKind
    purpose: str
    status: str
    model_policy: str | None


class AgentAssignmentCreate(BaseModel):
    organization_id: UUID
    scope_type: str = Field(min_length=2, max_length=80)
    scope_id: str = Field(min_length=1, max_length=120)


class AgentAssignmentRead(BaseModel):
    id: UUID
    agent_id: UUID
    organization_id: UUID
    scope_type: str
    scope_id: str
    granted_by_person_id: UUID | None


class AgentTaskCreate(BaseModel):
    organization_id: UUID
    task_type: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=2, max_length=240)
    input_ref: str | None = Field(default=None, max_length=500)


class AgentTaskRead(BaseModel):
    id: UUID
    agent_id: UUID
    organization_id: UUID
    task_type: str
    title: str
    status: AgentTaskStatus
    requested_by_person_id: UUID | None
    input_ref: str | None
    output_ref: str | None
    review_notes: str | None


class AgentTaskUpdate(BaseModel):
    status: AgentTaskStatus | None = None
    output_ref: str | None = Field(default=None, max_length=500)
    review_notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "AgentTaskUpdate":
        if self.status is None and self.output_ref is None and self.review_notes is None:
            raise ValueError("status, output_ref, or review_notes is required")
        return self


class AgentWorkerCallbackCreate(BaseModel):
    task_id: UUID
    status: AgentTaskStatus = AgentTaskStatus.WAITING_FOR_REVIEW
    output_ref: str | None = Field(default=None, max_length=500)
    review_notes: str | None = Field(default=None, max_length=4000)
    idempotency_key: str = Field(min_length=8, max_length=180)
    external_event_id: str | None = Field(default=None, max_length=180)
    raw_payload: dict[str, object] | None = None


class AgentWorkerCallbackRead(BaseModel):
    accepted: bool
    duplicate: bool
    signature_required: bool
    signature_validated: bool
    run_record_id: UUID | None
    message: str
    task: AgentTaskRead


class AgentModelRegistryCreate(BaseModel):
    organization_id: UUID
    model_policy: str = Field(min_length=2, max_length=120)
    provider: str = Field(default="local", min_length=2, max_length=120)
    model_family: str | None = Field(default=None, max_length=120)
    version: str | None = Field(default=None, max_length=120)
    use_case: str = Field(min_length=8, max_length=4000)
    risk_tier: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    review_status: str = Field(default="draft", pattern="^(draft|in_review|approved|retired|blocked)$")
    documentation_url: str | None = Field(default=None, max_length=500)
    evaluation_summary: str | None = Field(default=None, max_length=4000)
    limitations: str | None = Field(default=None, max_length=4000)
    bias_notes: str | None = Field(default=None, max_length=4000)
    data_residency: str | None = Field(default=None, max_length=120)


class AgentModelRegistryUpdate(BaseModel):
    provider: str | None = Field(default=None, min_length=2, max_length=120)
    model_family: str | None = Field(default=None, max_length=120)
    version: str | None = Field(default=None, max_length=120)
    use_case: str | None = Field(default=None, min_length=8, max_length=4000)
    risk_tier: str | None = Field(default=None, pattern="^(low|medium|high|critical)$")
    review_status: str | None = Field(default=None, pattern="^(draft|in_review|approved|retired|blocked)$")
    documentation_url: str | None = Field(default=None, max_length=500)
    evaluation_summary: str | None = Field(default=None, max_length=4000)
    limitations: str | None = Field(default=None, max_length=4000)
    bias_notes: str | None = Field(default=None, max_length=4000)
    data_residency: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "AgentModelRegistryUpdate":
        if all(value is None for value in self.model_dump().values()):
            raise ValueError("at least one model registry field is required")
        return self


class AgentModelRegistryRead(BaseModel):
    id: UUID
    organization_id: UUID
    model_policy: str
    provider: str
    model_family: str | None
    version: str | None
    use_case: str
    risk_tier: str
    review_status: str
    documentation_url: str | None
    evaluation_summary: str | None
    limitations: str | None
    bias_notes: str | None
    data_residency: str | None
    owner_person_id: UUID | None
    approved_by_person_id: UUID | None
    approved_at: datetime | None


class AgentBiasAuditCreate(BaseModel):
    audit_dimension: str = Field(default="age_gender_region_club_school", min_length=2, max_length=120)
    population_slice: str = Field(default="all-participants", min_length=2, max_length=160)


class AgentBiasAuditRead(BaseModel):
    id: UUID
    organization_id: UUID
    model_registry_id: UUID
    model_policy: str
    audit_dimension: str
    population_slice: str
    sample_size: int
    disparity_score: float
    status: str
    severity: str
    findings: str
    recommendation: str
    mitigation_status: str
    audited_by_person_id: UUID | None
    audited_at: datetime


class AgentDecisionAppealCreate(BaseModel):
    reason: str = Field(default="human_review", min_length=2, max_length=120)
    question: str = Field(min_length=8, max_length=4000)
    supporting_evidence_ref: str | None = Field(default=None, max_length=500)


class AgentMyDecisionAppealCreate(AgentDecisionAppealCreate):
    organization_id: UUID
    task_id: UUID


class AgentDecisionAppealUpdate(BaseModel):
    status: str = Field(pattern="^(pending|under_review|upheld|modified|overturned|withdrawn)$")
    resolution_notes: str = Field(min_length=4, max_length=4000)


class AgentDecisionAppealRead(BaseModel):
    id: UUID
    organization_id: UUID
    agent_id: UUID
    task_id: UUID
    model_policy: str
    status: str
    reason: str
    question: str
    simple_explanation: str
    technical_explanation: str
    data_summary: str
    alternative_options: str
    supporting_evidence_ref: str | None
    submitted_by_person_id: UUID | None
    resolved_by_person_id: UUID | None
    resolution_notes: str | None
    due_at: datetime
    resolved_at: datetime | None


class AgentFamilyTaskRead(BaseModel):
    id: UUID
    organization_id: UUID
    agent_id: UUID
    agent_name: str
    agent_kind: AgentKind
    task_type: str
    title: str
    status: AgentTaskStatus
    input_ref: str | None
    output_ref: str | None
    review_notes: str | None
    athlete_name: str | None
    appeal_status: str | None
    simple_explanation: str
    data_summary: str
    alternative_options: str
    governance_note: str


class AgentDecisionAppealFormRead(BaseModel):
    organization_id: UUID
    task_id: UUID
    generated_at: datetime
    download_filename: str
    content_type: str
    content: str


class AgentRunRecordRead(BaseModel):
    id: UUID
    task_id: UUID
    agent_id: UUID
    agent_name: str
    agent_kind: AgentKind
    organization_id: UUID
    event_type: str
    task_type: str
    title: str
    status: AgentTaskStatus
    model_policy: str
    execution_mode: str
    input_ref: str | None
    output_ref: str | None
    review_required: bool
    governance_notes: str
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    ledger_sequence: int
    record_hash: str
    previous_record_hash: str | None


class AgentCredentialStatusRead(BaseModel):
    execution_mode: str
    default_model: str
    webhook_configured: bool
    webhook_key_configured: bool
    credential_boundary: str
    recommendation: str


class AgentGovernanceSummaryRead(BaseModel):
    organization_id: UUID
    agents: int
    queued_tasks: int
    running_tasks: int
    waiting_for_review: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    human_review_required: int
    credential_status: AgentCredentialStatusRead


class AgentRunLedgerVerificationRead(BaseModel):
    organization_id: UUID
    total_records: int
    verified_records: int
    broken_records: list[UUID]
    latest_record_hash: str | None
    valid: bool


class AgentModelTransparencyItemRead(BaseModel):
    model_policy: str
    agent_count: int
    run_count: int
    completed_runs: int
    failed_runs: int
    human_review_runs: int
    execution_modes: list[str]
    latest_run_at: datetime | None
    risk_band: str
    registry_status: str | None
    registered_risk_tier: str | None
    documentation_url: str | None
    transparency_notes: str


class AgentModelTransparencyReportRead(BaseModel):
    organization_id: UUID
    generated_at: datetime
    total_models: int
    total_runs: int
    human_review_required: int
    local_model_count: int
    webhook_model_count: int
    ledger_valid: bool
    latest_record_hash: str | None
    credential_boundary: str
    recommendations: list[str]
    models: list[AgentModelTransparencyItemRead]


class AgentEthicalScorecardRead(BaseModel):
    organization_id: UUID
    generated_at: datetime
    score: int
    grade: str
    total_models: int
    approved_models: int
    blocked_models: int
    undocumented_models: int
    bias_audits: int
    passing_bias_audits: int
    failing_bias_audits: int
    open_mitigations: int
    pending_appeals: int
    resolved_appeals: int
    human_review_required: int
    ledger_valid: bool
    public_summary: str
    improvement_actions: list[str]


class AgentScorecardCommentCreate(BaseModel):
    organization_id: UUID
    display_name: str = Field(min_length=2, max_length=160)
    affiliation: str | None = Field(default=None, max_length=160)
    contact_email: str | None = Field(default=None, max_length=320)
    comment: str = Field(min_length=8, max_length=2000)
    consent_to_publish: bool = True


class AgentScorecardCommentRead(BaseModel):
    id: UUID
    organization_id: UUID
    display_name: str
    affiliation: str | None
    comment: str
    status: str
    consent_to_publish: bool
    submitted_at: datetime


class AgentScorecardCommentModerationRead(AgentScorecardCommentRead):
    contact_email: str | None
    abuse_score: int
    abuse_reason: str | None
    created_at: datetime
    updated_at: datetime


class AgentScorecardCommentUpdate(BaseModel):
    status: str = Field(pattern="^(published|hidden|flagged|private_feedback)$")


class AgentScorecardPublicationCreate(BaseModel):
    organization_id: UUID
    period_label: str | None = Field(default=None, max_length=40)


class AgentScorecardPublicationRead(BaseModel):
    id: UUID
    organization_id: UUID
    period_label: str
    status: str
    score: int
    grade: str
    total_models: int
    approved_models: int
    bias_audits: int
    pending_appeals: int
    ledger_valid: bool
    public_summary: str
    improvement_actions: list[str]
    published_comment_count: int
    flagged_comment_count: int
    snapshot_hash: str
    published_by_person_id: UUID | None
    published_at: datetime


class AgentScorecardPublicationArtifactRead(BaseModel):
    publication_id: UUID
    organization_id: UUID
    period_label: str
    artifact_format: str
    generated_at: datetime
    download_filename: str
    content_type: str
    content: str
    content_base64: str | None = None
    checksum: str
    size_bytes: int
    storage_url: str
    storage_key: str


class AgentScorecardPublicationArtifactLinkRead(BaseModel):
    publication_id: UUID
    organization_id: UUID
    period_label: str
    artifact_format: str
    storage_url: str
    signed_url: str
    expires_at: datetime
    content_type: str
    filename: str
    checksum: str
    size_bytes: int


class AgentScorecardPublicationReminderCreate(BaseModel):
    organization_id: UUID
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    recipient_person_ids: list[UUID] = Field(default_factory=list)
    send_to_managers: bool = True
    scheduled_for: datetime | None = None
    urgent: bool = False


class AgentScorecardPublicationReminderRead(BaseModel):
    organization_id: UUID
    period_label: str
    channel: CommunicationChannel
    readiness_status: str
    message_id: UUID | None
    message_status: str | None
    recipient_count: int
    recipient_person_ids: list[UUID]
    subject: str
    body: str
    scheduled_for: datetime | None
    delivered: bool
    failure_reason: str | None


class AgentScorecardPublicationReminderRunCreate(BaseModel):
    organization_id: UUID
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    due_within_days: int = Field(default=14, ge=1, le=120)
    send_reminders: bool = True


class AgentScorecardPublicationReminderRunRead(BaseModel):
    organization_id: UUID
    due_by: datetime
    period_label: str
    due: bool
    current_period_published: bool
    readiness_status: str
    sent: bool
    skipped_reason: str | None
    recipient_count: int
    message_id: UUID | None
    reminder: AgentScorecardPublicationReminderRead | None


class AgentScorecardPublicationReadinessRead(BaseModel):
    organization_id: UUID
    current_period_label: str
    current_period_published: bool
    next_publication_due_at: datetime
    days_until_due: int
    latest_period_label: str | None
    latest_published_at: datetime | None
    flagged_comment_count: int
    pending_appeal_count: int
    score: int
    grade: str
    readiness_status: str
    recommended_action: str
