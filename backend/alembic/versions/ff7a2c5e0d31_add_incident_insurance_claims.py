"""add incident insurance claims

Revision ID: ff7a2c5e0d31
Revises: e92b1c0d4a77
Create Date: 2026-05-28 02:40:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "ff7a2c5e0d31"
down_revision: str | None = "e92b1c0d4a77"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


claim_type = sa.Enum(
    "injury_medical",
    "liability",
    "equipment_damage",
    "property_damage",
    "travel",
    "other",
    name="insuranceclaimtype",
    native_enum=False,
    create_constraint=True,
)
claim_status = sa.Enum(
    "draft",
    "ready",
    "submitted",
    "acknowledged",
    "in_review",
    "approved",
    "partially_paid",
    "paid",
    "denied",
    "closed",
    name="insuranceclaimstatus",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "incident_insurance_claims",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("incident_id", app.models.base.GUID(), nullable=False),
        sa.Column("claimant_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("prepared_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("submitted_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("claim_type", claim_type, nullable=False),
        sa.Column("status", claim_status, nullable=False, server_default="draft"),
        sa.Column("provider_name", sa.String(length=240), nullable=False),
        sa.Column("policy_number", sa.String(length=160), nullable=True),
        sa.Column("claim_number", sa.String(length=160), nullable=True),
        sa.Column("coverage_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("paid_amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("reserve_amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tracking_url", sa.String(length=500), nullable=True),
        sa.Column("documentation_checklist_json", sa.Text(), nullable=True),
        sa.Column("submission_payload", sa.Text(), nullable=True),
        sa.Column("communication_log", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["claimant_person_id"],
            ["persons.id"],
            name=op.f("fk_incident_insurance_claims_claimant_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["safeguarding_incidents.id"],
            name=op.f("fk_incident_insurance_claims_incident_id_safeguarding_incidents"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_incident_insurance_claims_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["prepared_by_person_id"],
            ["persons.id"],
            name=op.f("fk_incident_insurance_claims_prepared_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["submitted_by_person_id"],
            ["persons.id"],
            name=op.f("fk_incident_insurance_claims_submitted_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incident_insurance_claims")),
    )
    for column in [
        "claim_number",
        "claim_type",
        "claimant_person_id",
        "closed_at",
        "coverage_verified_at",
        "incident_id",
        "organization_id",
        "policy_number",
        "prepared_by_person_id",
        "provider_name",
        "status",
        "submitted_at",
        "submitted_by_person_id",
    ]:
        op.create_index(
            op.f(f"ix_incident_insurance_claims_{column}"),
            "incident_insurance_claims",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "submitted_by_person_id",
        "submitted_at",
        "status",
        "provider_name",
        "prepared_by_person_id",
        "policy_number",
        "organization_id",
        "incident_id",
        "coverage_verified_at",
        "closed_at",
        "claimant_person_id",
        "claim_type",
        "claim_number",
    ]:
        op.drop_index(op.f(f"ix_incident_insurance_claims_{column}"), table_name="incident_insurance_claims")
    op.drop_table("incident_insurance_claims")
