"""add agent scorecard comments

Revision ID: c5d4e3f2a1b0
Revises: ab74d28e3f60
Create Date: 2026-05-27 00:55:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "c5d4e3f2a1b0"
down_revision: str | None = "ab74d28e3f60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_scorecard_comments",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("affiliation", sa.String(length=160), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("consent_to_publish", sa.Boolean(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_agent_scorecard_comments_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_scorecard_comments")),
    )
    op.create_index(
        op.f("ix_agent_scorecard_comments_affiliation"),
        "agent_scorecard_comments",
        ["affiliation"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_scorecard_comments_organization_id"),
        "agent_scorecard_comments",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_scorecard_comments_status"),
        "agent_scorecard_comments",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_scorecard_comments_submitted_at"),
        "agent_scorecard_comments",
        ["submitted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_scorecard_comments_submitted_at"), table_name="agent_scorecard_comments")
    op.drop_index(op.f("ix_agent_scorecard_comments_status"), table_name="agent_scorecard_comments")
    op.drop_index(op.f("ix_agent_scorecard_comments_organization_id"), table_name="agent_scorecard_comments")
    op.drop_index(op.f("ix_agent_scorecard_comments_affiliation"), table_name="agent_scorecard_comments")
    op.drop_table("agent_scorecard_comments")
