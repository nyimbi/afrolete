"""add match tracking analysis agent task

Revision ID: a483b20260531
Revises: a482b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a483b20260531"
down_revision: str | Sequence[str] | None = "a482b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "performance_match_tracking_runs",
        sa.Column("analysis_agent_task_id", GUID(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_performance_match_tracking_runs_analysis_agent_task_id_agent_tasks"),
        "performance_match_tracking_runs",
        "agent_tasks",
        ["analysis_agent_task_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_performance_match_tracking_runs_analysis_agent_task_id"),
        "performance_match_tracking_runs",
        ["analysis_agent_task_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_performance_match_tracking_runs_analysis_agent_task_id"),
        table_name="performance_match_tracking_runs",
    )
    op.drop_constraint(
        op.f("fk_performance_match_tracking_runs_analysis_agent_task_id_agent_tasks"),
        "performance_match_tracking_runs",
        type_="foreignkey",
    )
    op.drop_column("performance_match_tracking_runs", "analysis_agent_task_id")
