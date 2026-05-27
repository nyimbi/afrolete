"""add scorecard comment abuse fields

Revision ID: d7e8f9a0b1c2
Revises: c5d4e3f2a1b0
Create Date: 2026-05-27 01:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "d7e8f9a0b1c2"
down_revision: str | None = "c5d4e3f2a1b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent_scorecard_comments",
        sa.Column("abuse_score", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("agent_scorecard_comments", sa.Column("abuse_reason", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix_agent_scorecard_comments_abuse_score"),
        "agent_scorecard_comments",
        ["abuse_score"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_scorecard_comments_abuse_score"), table_name="agent_scorecard_comments")
    op.drop_column("agent_scorecard_comments", "abuse_reason")
    op.drop_column("agent_scorecard_comments", "abuse_score")
