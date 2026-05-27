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
