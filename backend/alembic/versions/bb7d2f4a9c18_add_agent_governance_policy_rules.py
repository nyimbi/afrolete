"""add agent governance policy rules

Revision ID: bb7d2f4a9c18
Revises: aa8c4e2f1b93
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "bb7d2f4a9c18"
down_revision: str | None = "aa8c4e2f1b93"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_governance_policy_rules",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("rule_code", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("agent_kind", sa.String(length=80), nullable=True),
        sa.Column("task_type_contains", sa.String(length=120), nullable=True),
        sa.Column("model_policy_contains", sa.String(length=120), nullable=True),
        sa.Column("input_ref_contains", sa.String(length=160), nullable=True),
        sa.Column("decision", sa.String(length=40), nullable=False),
        sa.Column("required_approval_count", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_agent_governance_policy_rules_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_governance_policy_rules")),
        sa.UniqueConstraint("organization_id", "rule_code", name="uq_agent_governance_policy_rules_org_code"),
    )
    for column in [
        "organization_id",
        "rule_code",
        "active",
        "agent_kind",
        "task_type_contains",
        "model_policy_contains",
        "input_ref_contains",
        "decision",
        "risk_level",
    ]:
        op.create_index(op.f(f"ix_agent_governance_policy_rules_{column}"), "agent_governance_policy_rules", [column], unique=False)

    op.add_column("agent_tasks", sa.Column("governance_policy_rule_id", app.models.base.GUID(), nullable=True))
    op.add_column("agent_tasks", sa.Column("governance_policy_code", sa.String(length=120), nullable=True))
    op.add_column("agent_tasks", sa.Column("governance_policy_decision", sa.String(length=40), nullable=True))
    op.add_column("agent_tasks", sa.Column("governance_policy_risk_level", sa.String(length=40), nullable=True))
    op.add_column("agent_tasks", sa.Column("governance_policy_rationale", sa.Text(), nullable=True))
    op.create_foreign_key(
        op.f("fk_agent_tasks_governance_policy_rule_id_agent_governance_policy_rules"),
        "agent_tasks",
        "agent_governance_policy_rules",
        ["governance_policy_rule_id"],
        ["id"],
    )
    for column in [
        "governance_policy_rule_id",
        "governance_policy_code",
        "governance_policy_decision",
        "governance_policy_risk_level",
    ]:
        op.create_index(op.f(f"ix_agent_tasks_{column}"), "agent_tasks", [column], unique=False)


def downgrade() -> None:
    for column in [
        "governance_policy_risk_level",
        "governance_policy_decision",
        "governance_policy_code",
        "governance_policy_rule_id",
    ]:
        op.drop_index(op.f(f"ix_agent_tasks_{column}"), table_name="agent_tasks")
    op.drop_constraint(
        op.f("fk_agent_tasks_governance_policy_rule_id_agent_governance_policy_rules"),
        "agent_tasks",
        type_="foreignkey",
    )
    op.drop_column("agent_tasks", "governance_policy_rationale")
    op.drop_column("agent_tasks", "governance_policy_risk_level")
    op.drop_column("agent_tasks", "governance_policy_decision")
    op.drop_column("agent_tasks", "governance_policy_code")
    op.drop_column("agent_tasks", "governance_policy_rule_id")

    for column in [
        "risk_level",
        "decision",
        "input_ref_contains",
        "model_policy_contains",
        "task_type_contains",
        "agent_kind",
        "active",
        "rule_code",
        "organization_id",
    ]:
        op.drop_index(op.f(f"ix_agent_governance_policy_rules_{column}"), table_name="agent_governance_policy_rules")
    op.drop_table("agent_governance_policy_rules")
