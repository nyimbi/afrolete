"""add agent task approvals

Revision ID: d4f8a9c1b2e3
Revises: c3e9a7d2f481
Create Date: 2026-05-28 20:02:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d4f8a9c1b2e3"
down_revision: str | None = "c3e9a7d2f481"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent_tasks",
        sa.Column("approval_required_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "agent_tasks",
        sa.Column("approval_approved_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "agent_tasks",
        sa.Column("approval_rejected_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "agent_tasks",
        sa.Column("approval_status", sa.String(length=40), server_default="not_requested", nullable=False),
    )
    op.add_column(
        "agent_tasks",
        sa.Column("approval_last_decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_agent_tasks_approval_status"), "agent_tasks", ["approval_status"], unique=False)
    op.create_index(
        op.f("ix_agent_tasks_approval_last_decided_at"),
        "agent_tasks",
        ["approval_last_decided_at"],
        unique=False,
    )

    op.create_table(
        "agent_task_approvals",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("task_id", app.models.base.GUID(), nullable=False),
        sa.Column("reviewer_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("reviewer_label", sa.String(length=160), nullable=True),
        sa.Column("requested_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("status", sa.String(length=40), server_default="pending", nullable=False),
        sa.Column("request_notes", sa.Text(), nullable=True),
        sa.Column("decision_notes", sa.Text(), nullable=True),
        sa.Column("decided_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sequence", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["decided_by_person_id"], ["persons.id"], name=op.f("fk_agent_task_approvals_decided_by_person_id_persons")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_agent_task_approvals_organization_id_organizations")),
        sa.ForeignKeyConstraint(["requested_by_person_id"], ["persons.id"], name=op.f("fk_agent_task_approvals_requested_by_person_id_persons")),
        sa.ForeignKeyConstraint(["reviewer_person_id"], ["persons.id"], name=op.f("fk_agent_task_approvals_reviewer_person_id_persons")),
        sa.ForeignKeyConstraint(["task_id"], ["agent_tasks.id"], name=op.f("fk_agent_task_approvals_task_id_agent_tasks")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_task_approvals")),
    )
    for column in [
        "decided_at",
        "decided_by_person_id",
        "organization_id",
        "reviewer_label",
        "reviewer_person_id",
        "sequence",
        "status",
        "task_id",
    ]:
        op.create_index(op.f(f"ix_agent_task_approvals_{column}"), "agent_task_approvals", [column], unique=False)


def downgrade() -> None:
    for column in [
        "task_id",
        "status",
        "sequence",
        "reviewer_person_id",
        "reviewer_label",
        "organization_id",
        "decided_by_person_id",
        "decided_at",
    ]:
        op.drop_index(op.f(f"ix_agent_task_approvals_{column}"), table_name="agent_task_approvals")
    op.drop_table("agent_task_approvals")
    op.drop_index(op.f("ix_agent_tasks_approval_last_decided_at"), table_name="agent_tasks")
    op.drop_index(op.f("ix_agent_tasks_approval_status"), table_name="agent_tasks")
    op.drop_column("agent_tasks", "approval_last_decided_at")
    op.drop_column("agent_tasks", "approval_status")
    op.drop_column("agent_tasks", "approval_rejected_count")
    op.drop_column("agent_tasks", "approval_approved_count")
    op.drop_column("agent_tasks", "approval_required_count")
