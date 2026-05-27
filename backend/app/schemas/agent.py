from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import AgentKind, AgentTaskStatus


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
