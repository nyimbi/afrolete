"""add agent callback replay audit

Revision ID: aa8c4e2f1b93
Revises: e6f8a0b2d4c5
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "aa8c4e2f1b93"
down_revision: str | None = "e6f8a0b2d4c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("agent_run_records", sa.Column("external_event_id", sa.String(length=180), nullable=True))
    op.add_column("agent_run_records", sa.Column("callback_payload_hash", sa.String(length=128), nullable=True))
    op.add_column("agent_run_records", sa.Column("callback_received_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_agent_run_records_external_event_id"), "agent_run_records", ["external_event_id"], unique=False)
    op.create_index(op.f("ix_agent_run_records_callback_payload_hash"), "agent_run_records", ["callback_payload_hash"], unique=False)
    op.create_index(op.f("ix_agent_run_records_callback_received_at"), "agent_run_records", ["callback_received_at"], unique=False)
    op.create_unique_constraint(
        op.f("uq_agent_run_records_org_external_event"),
        "agent_run_records",
        ["organization_id", "external_event_id"],
    )


def downgrade() -> None:
    op.drop_constraint(op.f("uq_agent_run_records_org_external_event"), "agent_run_records", type_="unique")
    op.drop_index(op.f("ix_agent_run_records_callback_received_at"), table_name="agent_run_records")
    op.drop_index(op.f("ix_agent_run_records_callback_payload_hash"), table_name="agent_run_records")
    op.drop_index(op.f("ix_agent_run_records_external_event_id"), table_name="agent_run_records")
    op.drop_column("agent_run_records", "callback_received_at")
    op.drop_column("agent_run_records", "callback_payload_hash")
    op.drop_column("agent_run_records", "external_event_id")
