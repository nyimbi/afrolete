"""add scorecard artifact request attribution

Revision ID: a0b1c2d3e4f5
Revises: f9a1b2c3d4e5
Create Date: 2026-05-28 02:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "a0b1c2d3e4f5"
down_revision: str | None = "f9a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("agent_scorecard_artifact_accesses", sa.Column("request_ip", sa.String(length=80), nullable=True))
    op.add_column("agent_scorecard_artifact_accesses", sa.Column("user_agent", sa.String(length=500), nullable=True))
    op.add_column("agent_scorecard_artifact_accesses", sa.Column("request_source", sa.String(length=80), nullable=True))
    op.create_index(
        op.f("ix_agent_scorecard_artifact_accesses_request_ip"),
        "agent_scorecard_artifact_accesses",
        ["request_ip"],
    )
    op.create_index(
        op.f("ix_agent_scorecard_artifact_accesses_request_source"),
        "agent_scorecard_artifact_accesses",
        ["request_source"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_scorecard_artifact_accesses_request_source"), table_name="agent_scorecard_artifact_accesses")
    op.drop_index(op.f("ix_agent_scorecard_artifact_accesses_request_ip"), table_name="agent_scorecard_artifact_accesses")
    op.drop_column("agent_scorecard_artifact_accesses", "request_source")
    op.drop_column("agent_scorecard_artifact_accesses", "user_agent")
    op.drop_column("agent_scorecard_artifact_accesses", "request_ip")
