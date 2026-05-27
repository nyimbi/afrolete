"""add agent decision appeals

Revision ID: ab74d28e3f60
Revises: 8af42c9e61d0
Create Date: 2026-05-27 00:40:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "ab74d28e3f60"
down_revision: str | None = "8af42c9e61d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_decision_appeals",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("agent_id", app.models.base.GUID(), nullable=False),
        sa.Column("task_id", app.models.base.GUID(), nullable=False),
        sa.Column("model_policy", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("simple_explanation", sa.Text(), nullable=False),
        sa.Column("technical_explanation", sa.Text(), nullable=False),
        sa.Column("data_summary", sa.Text(), nullable=False),
        sa.Column("alternative_options", sa.Text(), nullable=False),
        sa.Column("supporting_evidence_ref", sa.String(length=500), nullable=True),
        sa.Column("submitted_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("resolved_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name=op.f("fk_agent_decision_appeals_agent_id_agents")),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_agent_decision_appeals_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_person_id"],
            ["persons.id"],
            name=op.f("fk_agent_decision_appeals_resolved_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["submitted_by_person_id"],
            ["persons.id"],
            name=op.f("fk_agent_decision_appeals_submitted_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(["task_id"], ["agent_tasks.id"], name=op.f("fk_agent_decision_appeals_task_id_agent_tasks")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_decision_appeals")),
    )
    op.create_index(op.f("ix_agent_decision_appeals_agent_id"), "agent_decision_appeals", ["agent_id"], unique=False)
    op.create_index(op.f("ix_agent_decision_appeals_due_at"), "agent_decision_appeals", ["due_at"], unique=False)
    op.create_index(
        op.f("ix_agent_decision_appeals_model_policy"),
        "agent_decision_appeals",
        ["model_policy"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_decision_appeals_organization_id"),
        "agent_decision_appeals",
        ["organization_id"],
        unique=False,
    )
    op.create_index(op.f("ix_agent_decision_appeals_reason"), "agent_decision_appeals", ["reason"], unique=False)
    op.create_index(
        op.f("ix_agent_decision_appeals_resolved_at"),
        "agent_decision_appeals",
        ["resolved_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_decision_appeals_resolved_by_person_id"),
        "agent_decision_appeals",
        ["resolved_by_person_id"],
        unique=False,
    )
    op.create_index(op.f("ix_agent_decision_appeals_status"), "agent_decision_appeals", ["status"], unique=False)
    op.create_index(
        op.f("ix_agent_decision_appeals_submitted_by_person_id"),
        "agent_decision_appeals",
        ["submitted_by_person_id"],
        unique=False,
    )
    op.create_index(op.f("ix_agent_decision_appeals_task_id"), "agent_decision_appeals", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_decision_appeals_task_id"), table_name="agent_decision_appeals")
    op.drop_index(op.f("ix_agent_decision_appeals_submitted_by_person_id"), table_name="agent_decision_appeals")
    op.drop_index(op.f("ix_agent_decision_appeals_status"), table_name="agent_decision_appeals")
    op.drop_index(op.f("ix_agent_decision_appeals_resolved_by_person_id"), table_name="agent_decision_appeals")
    op.drop_index(op.f("ix_agent_decision_appeals_resolved_at"), table_name="agent_decision_appeals")
    op.drop_index(op.f("ix_agent_decision_appeals_reason"), table_name="agent_decision_appeals")
    op.drop_index(op.f("ix_agent_decision_appeals_organization_id"), table_name="agent_decision_appeals")
    op.drop_index(op.f("ix_agent_decision_appeals_model_policy"), table_name="agent_decision_appeals")
    op.drop_index(op.f("ix_agent_decision_appeals_due_at"), table_name="agent_decision_appeals")
    op.drop_index(op.f("ix_agent_decision_appeals_agent_id"), table_name="agent_decision_appeals")
    op.drop_table("agent_decision_appeals")
