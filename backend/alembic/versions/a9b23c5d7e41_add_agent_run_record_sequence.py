"""add agent run record sequence

Revision ID: a9b23c5d7e41
Revises: f7a18b63d4e2
Create Date: 2026-05-28 00:18:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "a9b23c5d7e41"
down_revision: str | None = "f7a18b63d4e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent_run_records",
        sa.Column("ledger_sequence", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        op.f("ix_agent_run_records_ledger_sequence"),
        "agent_run_records",
        ["ledger_sequence"],
        unique=False,
    )
    op.alter_column("agent_run_records", "ledger_sequence", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_run_records_ledger_sequence"), table_name="agent_run_records")
    op.drop_column("agent_run_records", "ledger_sequence")
