"""add agent bias mitigation tracking

Revision ID: cc9e7d2a5f10
Revises: bb7d2f4a9c18
Create Date: 2026-05-29 00:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "cc9e7d2a5f10"
down_revision: str | None = "bb7d2f4a9c18"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("agent_bias_audits", sa.Column("mitigation_action", sa.Text(), nullable=True))
    op.add_column("agent_bias_audits", sa.Column("mitigation_evidence_ref", sa.String(length=500), nullable=True))
    op.add_column("agent_bias_audits", sa.Column("mitigated_by_person_id", app.models.base.GUID(), nullable=True))
    op.add_column("agent_bias_audits", sa.Column("mitigated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        op.f("fk_agent_bias_audits_mitigated_by_person_id_persons"),
        "agent_bias_audits",
        "persons",
        ["mitigated_by_person_id"],
        ["id"],
    )
    op.create_index(op.f("ix_agent_bias_audits_mitigated_by_person_id"), "agent_bias_audits", ["mitigated_by_person_id"], unique=False)
    op.create_index(op.f("ix_agent_bias_audits_mitigated_at"), "agent_bias_audits", ["mitigated_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_bias_audits_mitigated_at"), table_name="agent_bias_audits")
    op.drop_index(op.f("ix_agent_bias_audits_mitigated_by_person_id"), table_name="agent_bias_audits")
    op.drop_constraint(op.f("fk_agent_bias_audits_mitigated_by_person_id_persons"), "agent_bias_audits", type_="foreignkey")
    op.drop_column("agent_bias_audits", "mitigated_at")
    op.drop_column("agent_bias_audits", "mitigated_by_person_id")
    op.drop_column("agent_bias_audits", "mitigation_evidence_ref")
    op.drop_column("agent_bias_audits", "mitigation_action")
