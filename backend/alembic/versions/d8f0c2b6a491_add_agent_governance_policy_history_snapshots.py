"""add agent governance policy history snapshots

Revision ID: d8f0c2b6a491
Revises: cc9e7d2a5f10
Create Date: 2026-05-29 01:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d8f0c2b6a491"
down_revision: str | None = "cc9e7d2a5f10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_governance_policy_history_snapshots",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("snapshot_label", sa.String(length=120), nullable=False),
        sa.Column("artifact_format", sa.String(length=24), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("download_filename", sa.String(length=240), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("governed_task_count", sa.Integer(), nullable=False),
        sa.Column("approval_required_count", sa.Integer(), nullable=False),
        sa.Column("completed_count", sa.Integer(), nullable=False),
        sa.Column("waiting_for_review_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("policy_count", sa.Integer(), nullable=False),
        sa.Column("latest_policy_code", sa.String(length=120), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("generated_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["generated_by_person_id"], ["persons.id"], name=op.f("fk_agent_governance_policy_history_snapshots_generated_by_person_id_persons")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_agent_governance_policy_history_snapshots_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_governance_policy_history_snapshots")),
    )
    op.create_index(
        op.f("ix_agent_governance_policy_history_snapshots_artifact_format"),
        "agent_governance_policy_history_snapshots",
        ["artifact_format"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_governance_policy_history_snapshots_checksum"),
        "agent_governance_policy_history_snapshots",
        ["checksum"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_governance_policy_history_snapshots_generated_at"),
        "agent_governance_policy_history_snapshots",
        ["generated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_governance_policy_history_snapshots_generated_by_person_id"),
        "agent_governance_policy_history_snapshots",
        ["generated_by_person_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_governance_policy_history_snapshots_latest_policy_code"),
        "agent_governance_policy_history_snapshots",
        ["latest_policy_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_governance_policy_history_snapshots_organization_id"),
        "agent_governance_policy_history_snapshots",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_governance_policy_history_snapshots_snapshot_label"),
        "agent_governance_policy_history_snapshots",
        ["snapshot_label"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_governance_policy_history_snapshots_snapshot_label"), table_name="agent_governance_policy_history_snapshots")
    op.drop_index(op.f("ix_agent_governance_policy_history_snapshots_organization_id"), table_name="agent_governance_policy_history_snapshots")
    op.drop_index(op.f("ix_agent_governance_policy_history_snapshots_latest_policy_code"), table_name="agent_governance_policy_history_snapshots")
    op.drop_index(op.f("ix_agent_governance_policy_history_snapshots_generated_by_person_id"), table_name="agent_governance_policy_history_snapshots")
    op.drop_index(op.f("ix_agent_governance_policy_history_snapshots_generated_at"), table_name="agent_governance_policy_history_snapshots")
    op.drop_index(op.f("ix_agent_governance_policy_history_snapshots_checksum"), table_name="agent_governance_policy_history_snapshots")
    op.drop_index(op.f("ix_agent_governance_policy_history_snapshots_artifact_format"), table_name="agent_governance_policy_history_snapshots")
    op.drop_table("agent_governance_policy_history_snapshots")
