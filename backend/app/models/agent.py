from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin
from app.models.enums import AgentKind, AgentTaskStatus


class Agent(IdMixin, TimestampMixin, Base):
    __tablename__ = "agents"

    organization_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    kind: Mapped[AgentKind] = mapped_column(Enum(AgentKind), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)
    model_policy: Mapped[str | None] = mapped_column(String(120))


class AgentAssignment(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_assignments"

    agent_id: Mapped[str] = mapped_column(GUID(), ForeignKey("agents.id"), index=True)
    organization_id: Mapped[str] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    scope_type: Mapped[str] = mapped_column(String(80), nullable=False)
    scope_id: Mapped[str] = mapped_column(String(120), nullable=False)
    granted_by_person_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("persons.id"))


class AgentTask(IdMixin, TimestampMixin, Base):
    __tablename__ = "agent_tasks"

    agent_id: Mapped[str] = mapped_column(GUID(), ForeignKey("agents.id"), index=True)
    organization_id: Mapped[str] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[AgentTaskStatus] = mapped_column(
        Enum(AgentTaskStatus),
        default=AgentTaskStatus.QUEUED,
        nullable=False,
        index=True,
    )
    requested_by_person_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("persons.id"))
    input_ref: Mapped[str | None] = mapped_column(String(500))
    output_ref: Mapped[str | None] = mapped_column(String(500))
    review_notes: Mapped[str | None] = mapped_column(Text)

