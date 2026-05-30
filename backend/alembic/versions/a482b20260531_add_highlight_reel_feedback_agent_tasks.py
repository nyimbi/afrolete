"""add highlight reel feedback agent tasks

Revision ID: a482b20260531
Revises: a481b20260530
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a482b20260531"
down_revision: str | Sequence[str] | None = "a481b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "performance_highlight_reel_feedback",
        sa.Column("agent_task_id", GUID(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_performance_highlight_reel_feedback_agent_task_id_agent_tasks"),
        "performance_highlight_reel_feedback",
        "agent_tasks",
        ["agent_task_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_performance_highlight_reel_feedback_agent_task_id"),
        "performance_highlight_reel_feedback",
        ["agent_task_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_performance_highlight_reel_feedback_agent_task_id"),
        table_name="performance_highlight_reel_feedback",
    )
    op.drop_constraint(
        op.f("fk_performance_highlight_reel_feedback_agent_task_id_agent_tasks"),
        "performance_highlight_reel_feedback",
        type_="foreignkey",
    )
    op.drop_column("performance_highlight_reel_feedback", "agent_task_id")
