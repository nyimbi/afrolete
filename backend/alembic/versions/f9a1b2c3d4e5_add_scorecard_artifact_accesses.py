"""add scorecard artifact accesses

Revision ID: f9a1b2c3d4e5
Revises: e8f9a0b1c2d3
Create Date: 2026-05-28 01:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "f9a1b2c3d4e5"
down_revision: str | None = "e8f9a0b1c2d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_scorecard_artifact_accesses",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("publication_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("artifact_format", sa.String(length=24), nullable=False),
        sa.Column("filename", sa.String(length=240), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("signed_url", sa.String(length=1000), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_agent_scorecard_artifact_accesses_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["publication_id"],
            ["agent_scorecard_publications.id"],
            name=op.f("fk_agent_scorecard_artifact_accesses_publication_id_agent_scorecard_publications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_scorecard_artifact_accesses")),
    )
    op.create_index(
        op.f("ix_agent_scorecard_artifact_accesses_accessed_at"),
        "agent_scorecard_artifact_accesses",
        ["accessed_at"],
    )
    op.create_index(
        op.f("ix_agent_scorecard_artifact_accesses_artifact_format"),
        "agent_scorecard_artifact_accesses",
        ["artifact_format"],
    )
    op.create_index(
        op.f("ix_agent_scorecard_artifact_accesses_checksum"),
        "agent_scorecard_artifact_accesses",
        ["checksum"],
    )
    op.create_index(
        op.f("ix_agent_scorecard_artifact_accesses_event_type"),
        "agent_scorecard_artifact_accesses",
        ["event_type"],
    )
    op.create_index(
        op.f("ix_agent_scorecard_artifact_accesses_expires_at"),
        "agent_scorecard_artifact_accesses",
        ["expires_at"],
    )
    op.create_index(
        op.f("ix_agent_scorecard_artifact_accesses_organization_id"),
        "agent_scorecard_artifact_accesses",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_agent_scorecard_artifact_accesses_publication_id"),
        "agent_scorecard_artifact_accesses",
        ["publication_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_scorecard_artifact_accesses_publication_id"), table_name="agent_scorecard_artifact_accesses")
    op.drop_index(op.f("ix_agent_scorecard_artifact_accesses_organization_id"), table_name="agent_scorecard_artifact_accesses")
    op.drop_index(op.f("ix_agent_scorecard_artifact_accesses_expires_at"), table_name="agent_scorecard_artifact_accesses")
    op.drop_index(op.f("ix_agent_scorecard_artifact_accesses_event_type"), table_name="agent_scorecard_artifact_accesses")
    op.drop_index(op.f("ix_agent_scorecard_artifact_accesses_checksum"), table_name="agent_scorecard_artifact_accesses")
    op.drop_index(op.f("ix_agent_scorecard_artifact_accesses_artifact_format"), table_name="agent_scorecard_artifact_accesses")
    op.drop_index(op.f("ix_agent_scorecard_artifact_accesses_accessed_at"), table_name="agent_scorecard_artifact_accesses")
    op.drop_table("agent_scorecard_artifact_accesses")
