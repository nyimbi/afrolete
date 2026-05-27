"""add agent model registry

Revision ID: 3f9a2c8d1b77
Revises: f0a6c2b9d8e4
Create Date: 2026-05-27 00:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "3f9a2c8d1b77"
down_revision: str | None = "f0a6c2b9d8e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_model_registry",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("model_policy", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=120), nullable=False),
        sa.Column("model_family", sa.String(length=120), nullable=True),
        sa.Column("version", sa.String(length=120), nullable=True),
        sa.Column("use_case", sa.Text(), nullable=False),
        sa.Column("risk_tier", sa.String(length=40), nullable=False),
        sa.Column("review_status", sa.String(length=40), nullable=False),
        sa.Column("documentation_url", sa.String(length=500), nullable=True),
        sa.Column("evaluation_summary", sa.Text(), nullable=True),
        sa.Column("limitations", sa.Text(), nullable=True),
        sa.Column("bias_notes", sa.Text(), nullable=True),
        sa.Column("data_residency", sa.String(length=120), nullable=True),
        sa.Column("owner_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("approved_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["approved_by_person_id"],
            ["persons.id"],
            name=op.f("fk_agent_model_registry_approved_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_agent_model_registry_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_person_id"],
            ["persons.id"],
            name=op.f("fk_agent_model_registry_owner_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_model_registry")),
        sa.UniqueConstraint("organization_id", "model_policy", name="uq_agent_model_registry_org_policy"),
    )
    op.create_index(op.f("ix_agent_model_registry_approved_at"), "agent_model_registry", ["approved_at"], unique=False)
    op.create_index(
        op.f("ix_agent_model_registry_approved_by_person_id"),
        "agent_model_registry",
        ["approved_by_person_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_model_registry_data_residency"),
        "agent_model_registry",
        ["data_residency"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_model_registry_model_family"),
        "agent_model_registry",
        ["model_family"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_model_registry_model_policy"),
        "agent_model_registry",
        ["model_policy"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_model_registry_organization_id"),
        "agent_model_registry",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_model_registry_owner_person_id"),
        "agent_model_registry",
        ["owner_person_id"],
        unique=False,
    )
    op.create_index(op.f("ix_agent_model_registry_provider"), "agent_model_registry", ["provider"], unique=False)
    op.create_index(
        op.f("ix_agent_model_registry_review_status"),
        "agent_model_registry",
        ["review_status"],
        unique=False,
    )
    op.create_index(op.f("ix_agent_model_registry_risk_tier"), "agent_model_registry", ["risk_tier"], unique=False)
    op.create_index(op.f("ix_agent_model_registry_version"), "agent_model_registry", ["version"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_model_registry_version"), table_name="agent_model_registry")
    op.drop_index(op.f("ix_agent_model_registry_risk_tier"), table_name="agent_model_registry")
    op.drop_index(op.f("ix_agent_model_registry_review_status"), table_name="agent_model_registry")
    op.drop_index(op.f("ix_agent_model_registry_provider"), table_name="agent_model_registry")
    op.drop_index(op.f("ix_agent_model_registry_owner_person_id"), table_name="agent_model_registry")
    op.drop_index(op.f("ix_agent_model_registry_organization_id"), table_name="agent_model_registry")
    op.drop_index(op.f("ix_agent_model_registry_model_policy"), table_name="agent_model_registry")
    op.drop_index(op.f("ix_agent_model_registry_model_family"), table_name="agent_model_registry")
    op.drop_index(op.f("ix_agent_model_registry_data_residency"), table_name="agent_model_registry")
    op.drop_index(op.f("ix_agent_model_registry_approved_by_person_id"), table_name="agent_model_registry")
    op.drop_index(op.f("ix_agent_model_registry_approved_at"), table_name="agent_model_registry")
    op.drop_table("agent_model_registry")
