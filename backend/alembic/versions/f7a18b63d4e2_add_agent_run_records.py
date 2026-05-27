"""add agent run records

Revision ID: f7a18b63d4e2
Revises: c46f58d91a20
Create Date: 2026-05-28 00:05:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "f7a18b63d4e2"
down_revision: str | None = "c46f58d91a20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


agent_task_status = sa.Enum(
    "queued",
    "running",
    "waiting_for_review",
    "completed",
    "failed",
    "cancelled",
    name="agenttaskstatus",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "agent_run_records",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("agent_id", app.models.base.GUID(), nullable=False),
        sa.Column("task_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("status", agent_task_status, nullable=False),
        sa.Column("model_policy", sa.String(length=120), nullable=False),
        sa.Column("execution_mode", sa.String(length=80), nullable=False),
        sa.Column("input_ref", sa.String(length=500), nullable=True),
        sa.Column("output_ref", sa.String(length=500), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("executed_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("governance_notes", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("previous_record_hash", sa.String(length=128), nullable=True),
        sa.Column("record_hash", sa.String(length=128), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name=op.f("fk_agent_run_records_agent_id_agents")),
        sa.ForeignKeyConstraint(
            ["executed_by_person_id"],
            ["persons.id"],
            name=op.f("fk_agent_run_records_executed_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_agent_run_records_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["agent_tasks.id"],
            name=op.f("fk_agent_run_records_task_id_agent_tasks"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_run_records")),
        sa.UniqueConstraint("idempotency_key", name="uq_agent_run_records_idempotency_key"),
    )
    op.create_index(op.f("ix_agent_run_records_agent_id"), "agent_run_records", ["agent_id"], unique=False)
    op.create_index(op.f("ix_agent_run_records_event_type"), "agent_run_records", ["event_type"], unique=False)
    op.create_index(
        op.f("ix_agent_run_records_executed_by_person_id"),
        "agent_run_records",
        ["executed_by_person_id"],
        unique=False,
    )
    op.create_index(op.f("ix_agent_run_records_execution_mode"), "agent_run_records", ["execution_mode"], unique=False)
    op.create_index(op.f("ix_agent_run_records_finished_at"), "agent_run_records", ["finished_at"], unique=False)
    op.create_index(
        op.f("ix_agent_run_records_idempotency_key"),
        "agent_run_records",
        ["idempotency_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_run_records_organization_id"),
        "agent_run_records",
        ["organization_id"],
        unique=False,
    )
    op.create_index(op.f("ix_agent_run_records_record_hash"), "agent_run_records", ["record_hash"], unique=False)
    op.create_index(op.f("ix_agent_run_records_started_at"), "agent_run_records", ["started_at"], unique=False)
    op.create_index(op.f("ix_agent_run_records_status"), "agent_run_records", ["status"], unique=False)
    op.create_index(op.f("ix_agent_run_records_task_id"), "agent_run_records", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_run_records_task_id"), table_name="agent_run_records")
    op.drop_index(op.f("ix_agent_run_records_status"), table_name="agent_run_records")
    op.drop_index(op.f("ix_agent_run_records_started_at"), table_name="agent_run_records")
    op.drop_index(op.f("ix_agent_run_records_record_hash"), table_name="agent_run_records")
    op.drop_index(op.f("ix_agent_run_records_organization_id"), table_name="agent_run_records")
    op.drop_index(op.f("ix_agent_run_records_idempotency_key"), table_name="agent_run_records")
    op.drop_index(op.f("ix_agent_run_records_finished_at"), table_name="agent_run_records")
    op.drop_index(op.f("ix_agent_run_records_execution_mode"), table_name="agent_run_records")
    op.drop_index(op.f("ix_agent_run_records_executed_by_person_id"), table_name="agent_run_records")
    op.drop_index(op.f("ix_agent_run_records_event_type"), table_name="agent_run_records")
    op.drop_index(op.f("ix_agent_run_records_agent_id"), table_name="agent_run_records")
    op.drop_table("agent_run_records")
