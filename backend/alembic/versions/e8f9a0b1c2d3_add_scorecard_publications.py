"""add scorecard publications

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-05-27 01:25:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "e8f9a0b1c2d3"
down_revision: str | None = "d7e8f9a0b1c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_scorecard_publications",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("period_label", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("grade", sa.String(length=8), nullable=False),
        sa.Column("total_models", sa.Integer(), nullable=False),
        sa.Column("approved_models", sa.Integer(), nullable=False),
        sa.Column("bias_audits", sa.Integer(), nullable=False),
        sa.Column("pending_appeals", sa.Integer(), nullable=False),
        sa.Column("ledger_valid", sa.Boolean(), nullable=False),
        sa.Column("public_summary", sa.Text(), nullable=False),
        sa.Column("improvement_actions", sa.Text(), nullable=False),
        sa.Column("published_comment_count", sa.Integer(), nullable=False),
        sa.Column("flagged_comment_count", sa.Integer(), nullable=False),
        sa.Column("snapshot_hash", sa.String(length=128), nullable=False),
        sa.Column("published_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_agent_scorecard_publications_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["published_by_person_id"],
            ["persons.id"],
            name=op.f("fk_agent_scorecard_publications_published_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_scorecard_publications")),
        sa.UniqueConstraint("organization_id", "period_label", name="uq_agent_scorecard_publications_org_period"),
    )
    op.create_index(op.f("ix_agent_scorecard_publications_grade"), "agent_scorecard_publications", ["grade"])
    op.create_index(op.f("ix_agent_scorecard_publications_organization_id"), "agent_scorecard_publications", ["organization_id"])
    op.create_index(op.f("ix_agent_scorecard_publications_period_label"), "agent_scorecard_publications", ["period_label"])
    op.create_index(op.f("ix_agent_scorecard_publications_published_at"), "agent_scorecard_publications", ["published_at"])
    op.create_index(
        op.f("ix_agent_scorecard_publications_published_by_person_id"),
        "agent_scorecard_publications",
        ["published_by_person_id"],
    )
    op.create_index(op.f("ix_agent_scorecard_publications_score"), "agent_scorecard_publications", ["score"])
    op.create_index(op.f("ix_agent_scorecard_publications_snapshot_hash"), "agent_scorecard_publications", ["snapshot_hash"])
    op.create_index(op.f("ix_agent_scorecard_publications_status"), "agent_scorecard_publications", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_scorecard_publications_status"), table_name="agent_scorecard_publications")
    op.drop_index(op.f("ix_agent_scorecard_publications_snapshot_hash"), table_name="agent_scorecard_publications")
    op.drop_index(op.f("ix_agent_scorecard_publications_score"), table_name="agent_scorecard_publications")
    op.drop_index(op.f("ix_agent_scorecard_publications_published_by_person_id"), table_name="agent_scorecard_publications")
    op.drop_index(op.f("ix_agent_scorecard_publications_published_at"), table_name="agent_scorecard_publications")
    op.drop_index(op.f("ix_agent_scorecard_publications_period_label"), table_name="agent_scorecard_publications")
    op.drop_index(op.f("ix_agent_scorecard_publications_organization_id"), table_name="agent_scorecard_publications")
    op.drop_index(op.f("ix_agent_scorecard_publications_grade"), table_name="agent_scorecard_publications")
    op.drop_table("agent_scorecard_publications")
