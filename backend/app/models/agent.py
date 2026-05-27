from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
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


class AgentRunRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_run_records"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_agent_run_records_idempotency_key"),
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
