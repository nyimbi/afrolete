"""add agent bias audits

Revision ID: 8af42c9e61d0
Revises: 3f9a2c8d1b77
Create Date: 2026-05-27 00:20:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "8af42c9e61d0"
down_revision: str | None = "3f9a2c8d1b77"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_bias_audits",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("model_registry_id", app.models.base.GUID(), nullable=False),
        sa.Column("model_policy", sa.String(length=120), nullable=False),
        sa.Column("audit_dimension", sa.String(length=120), nullable=False),
        sa.Column("population_slice", sa.String(length=160), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("disparity_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("findings", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("mitigation_status", sa.String(length=40), nullable=False),
        sa.Column("audited_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("audited_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["audited_by_person_id"],
            ["persons.id"],
            name=op.f("fk_agent_bias_audits_audited_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["model_registry_id"],
            ["agent_model_registry.id"],
            name=op.f("fk_agent_bias_audits_model_registry_id_agent_model_registry"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_agent_bias_audits_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_bias_audits")),
    )
    op.create_index(op.f("ix_agent_bias_audits_audit_dimension"), "agent_bias_audits", ["audit_dimension"], unique=False)
    op.create_index(op.f("ix_agent_bias_audits_audited_at"), "agent_bias_audits", ["audited_at"], unique=False)
    op.create_index(
        op.f("ix_agent_bias_audits_audited_by_person_id"),
        "agent_bias_audits",
        ["audited_by_person_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_bias_audits_mitigation_status"),
        "agent_bias_audits",
        ["mitigation_status"],
        unique=False,
    )
    op.create_index(op.f("ix_agent_bias_audits_model_policy"), "agent_bias_audits", ["model_policy"], unique=False)
    op.create_index(
        op.f("ix_agent_bias_audits_model_registry_id"),
        "agent_bias_audits",
        ["model_registry_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_bias_audits_organization_id"),
        "agent_bias_audits",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_bias_audits_population_slice"),
        "agent_bias_audits",
        ["population_slice"],
        unique=False,
    )
    op.create_index(op.f("ix_agent_bias_audits_severity"), "agent_bias_audits", ["severity"], unique=False)
    op.create_index(op.f("ix_agent_bias_audits_status"), "agent_bias_audits", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_bias_audits_status"), table_name="agent_bias_audits")
    op.drop_index(op.f("ix_agent_bias_audits_severity"), table_name="agent_bias_audits")
    op.drop_index(op.f("ix_agent_bias_audits_population_slice"), table_name="agent_bias_audits")
    op.drop_index(op.f("ix_agent_bias_audits_organization_id"), table_name="agent_bias_audits")
    op.drop_index(op.f("ix_agent_bias_audits_model_registry_id"), table_name="agent_bias_audits")
    op.drop_index(op.f("ix_agent_bias_audits_model_policy"), table_name="agent_bias_audits")
    op.drop_index(op.f("ix_agent_bias_audits_mitigation_status"), table_name="agent_bias_audits")
    op.drop_index(op.f("ix_agent_bias_audits_audited_by_person_id"), table_name="agent_bias_audits")
    op.drop_index(op.f("ix_agent_bias_audits_audited_at"), table_name="agent_bias_audits")
    op.drop_index(op.f("ix_agent_bias_audits_audit_dimension"), table_name="agent_bias_audits")
    op.drop_table("agent_bias_audits")
