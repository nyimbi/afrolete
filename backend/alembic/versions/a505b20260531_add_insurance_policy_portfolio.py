"""add insurance policy portfolio

Revision ID: a505b20260531
Revises: a504b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a505b20260531"
down_revision: str | Sequence[str] | None = "a504b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "insurance_policies",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("policy_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("provider_name", sa.String(length=240), nullable=False),
        sa.Column("policy_number", sa.String(length=160), nullable=False),
        sa.Column("group_number", sa.String(length=160), nullable=True),
        sa.Column("broker_name", sa.String(length=180), nullable=True),
        sa.Column("broker_email", sa.String(length=320), nullable=True),
        sa.Column("broker_phone", sa.String(length=64), nullable=True),
        sa.Column("coverage_summary", sa.Text(), nullable=True),
        sa.Column("covered_subjects", sa.Text(), nullable=True),
        sa.Column("exclusions", sa.Text(), nullable=True),
        sa.Column("coverage_limit_cents", sa.Integer(), nullable=False),
        sa.Column("deductible_cents", sa.Integer(), nullable=False),
        sa.Column("premium_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("effective_on", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=False),
        sa.Column("renewal_notice_days", sa.Integer(), nullable=False),
        sa.Column("certificate_url", sa.String(length=500), nullable=True),
        sa.Column("document_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_insurance_policies_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_insurance_policies")),
        sa.UniqueConstraint("organization_id", "policy_number", name=op.f("uq_insurance_policies_org_policy_number")),
    )
    for column in (
        "broker_name",
        "effective_on",
        "expires_on",
        "group_number",
        "name",
        "organization_id",
        "policy_number",
        "policy_type",
        "provider_name",
        "status",
    ):
        op.create_index(op.f(f"ix_insurance_policies_{column}"), "insurance_policies", [column])

    op.add_column("incident_insurance_claims", sa.Column("insurance_policy_id", GUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_incident_insurance_claims_insurance_policy_id_insurance_policies"),
        "incident_insurance_claims",
        "insurance_policies",
        ["insurance_policy_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_incident_insurance_claims_insurance_policy_id"),
        "incident_insurance_claims",
        ["insurance_policy_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_incident_insurance_claims_insurance_policy_id"), table_name="incident_insurance_claims")
    op.drop_constraint(
        op.f("fk_incident_insurance_claims_insurance_policy_id_insurance_policies"),
        "incident_insurance_claims",
        type_="foreignkey",
    )
    op.drop_column("incident_insurance_claims", "insurance_policy_id")
    for column in (
        "status",
        "provider_name",
        "policy_type",
        "policy_number",
        "organization_id",
        "name",
        "group_number",
        "expires_on",
        "effective_on",
        "broker_name",
    ):
        op.drop_index(op.f(f"ix_insurance_policies_{column}"), table_name="insurance_policies")
    op.drop_table("insurance_policies")
