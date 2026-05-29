"""add agent task review assignments

Revision ID: a2d9f4c7e8b1
Revises: f1b2c3d4e5f6
Create Date: 2026-05-29 13:20:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a2d9f4c7e8b1"
down_revision: str | None = "f1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent_tasks",
        sa.Column("review_assigned_to_person_id", app.models.base.GUID(), nullable=True),
    )
    op.add_column("agent_tasks", sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "agent_tasks",
        sa.Column("review_priority", sa.String(length=40), nullable=False, server_default="normal"),
    )
    op.add_column("agent_tasks", sa.Column("review_assignment_notes", sa.Text(), nullable=True))
    op.create_foreign_key(
        op.f("fk_agent_tasks_review_assigned_to_person_id_persons"),
        "agent_tasks",
        "persons",
        ["review_assigned_to_person_id"],
        ["id"],
    )
    for column in ["review_assigned_to_person_id", "review_due_at", "review_priority"]:
        op.create_index(op.f(f"ix_agent_tasks_{column}"), "agent_tasks", [column])


def downgrade() -> None:
    for column in ["review_priority", "review_due_at", "review_assigned_to_person_id"]:
        op.drop_index(op.f(f"ix_agent_tasks_{column}"), table_name="agent_tasks")
    op.drop_constraint(
        op.f("fk_agent_tasks_review_assigned_to_person_id_persons"),
        "agent_tasks",
        type_="foreignkey",
    )
    op.drop_column("agent_tasks", "review_assignment_notes")
    op.drop_column("agent_tasks", "review_priority")
    op.drop_column("agent_tasks", "review_due_at")
    op.drop_column("agent_tasks", "review_assigned_to_person_id")
