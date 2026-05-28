"""add safeguarding evidence policy rules

Revision ID: a2c4e6f8b0d1
Revises: d4f8a9c1b2e3
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a2c4e6f8b0d1"
down_revision: str | None = "d4f8a9c1b2e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "safeguarding_evidence_policy_rules",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("rule_code", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("incident_type", sa.String(length=80), nullable=True),
        sa.Column("minimum_severity", sa.String(length=40), nullable=True),
        sa.Column("evidence_type_contains", sa.String(length=120), nullable=True),
        sa.Column("medical_follow_up_values", sa.String(length=240), nullable=True),
        sa.Column("regulatory_required", sa.Boolean(), nullable=True),
        sa.Column("athlete_linked_required", sa.Boolean(), nullable=True),
        sa.Column("required_approval_level", sa.String(length=80), nullable=False),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("recommended_review_status", sa.String(length=40), nullable=False),
        sa.Column("block_acceptance", sa.Boolean(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_safeguarding_evidence_policy_rules_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_safeguarding_evidence_policy_rules")),
        sa.UniqueConstraint(
            "organization_id",
            "rule_code",
            name="uq_safeguarding_evidence_policy_rules_org_code",
        ),
    )
    for column in [
        "active",
        "athlete_linked_required",
        "block_acceptance",
        "evidence_type_contains",
        "incident_type",
        "minimum_severity",
        "organization_id",
        "recommended_review_status",
        "regulatory_required",
        "required_approval_level",
        "risk_level",
        "rule_code",
    ]:
        op.create_index(
            op.f(f"ix_safeguarding_evidence_policy_rules_{column}"),
            "safeguarding_evidence_policy_rules",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "rule_code",
        "risk_level",
        "required_approval_level",
        "regulatory_required",
        "recommended_review_status",
        "organization_id",
        "minimum_severity",
        "incident_type",
        "evidence_type_contains",
        "block_acceptance",
        "athlete_linked_required",
        "active",
    ]:
        op.drop_index(
            op.f(f"ix_safeguarding_evidence_policy_rules_{column}"),
            table_name="safeguarding_evidence_policy_rules",
        )
    op.drop_table("safeguarding_evidence_policy_rules")
