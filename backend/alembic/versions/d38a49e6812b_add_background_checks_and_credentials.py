"""add background checks and credentials

Revision ID: d38a49e6812b
Revises: c8f2a7b9d104
Create Date: 2026-05-28 01:20:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d38a49e6812b"
down_revision: str | None = "c8f2a7b9d104"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


background_check_status = sa.Enum(
    "requested",
    "in_progress",
    "clear",
    "review_required",
    "failed",
    "expired",
    name="backgroundcheckstatus",
    native_enum=False,
    create_constraint=True,
)
credential_type = sa.Enum(
    "safeguarding_training",
    "first_aid",
    "coaching_license",
    "officiating_license",
    "driver_certification",
    "background_check",
    "medical_license",
    "other",
    name="compliancecredentialtype",
    native_enum=False,
    create_constraint=True,
)
credential_status = sa.Enum(
    "pending",
    "verified",
    "expiring_soon",
    "expired",
    "revoked",
    name="compliancecredentialstatus",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "background_checks",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=False),
        sa.Column("requested_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("reviewed_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("provider", sa.String(length=120), nullable=False),
        sa.Column("check_type", sa.String(length=120), nullable=False),
        sa.Column("status", background_check_status, nullable=False, server_default="requested"),
        sa.Column("risk_level", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.Date(), nullable=True),
        sa.Column("external_reference", sa.String(length=240), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_background_checks_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["persons.id"],
            name=op.f("fk_background_checks_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_person_id"],
            ["persons.id"],
            name=op.f("fk_background_checks_requested_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_person_id"],
            ["persons.id"],
            name=op.f("fk_background_checks_reviewed_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_background_checks")),
    )
    for column in [
        "check_type",
        "completed_at",
        "expires_at",
        "external_reference",
        "organization_id",
        "person_id",
        "provider",
        "requested_at",
        "requested_by_person_id",
        "reviewed_by_person_id",
        "risk_level",
        "status",
    ]:
        op.create_index(op.f(f"ix_background_checks_{column}"), "background_checks", [column], unique=False)

    op.create_table(
        "compliance_credentials",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=False),
        sa.Column("verified_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("credential_type", credential_type, nullable=False),
        sa.Column("status", credential_status, nullable=False, server_default="pending"),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("issuing_body", sa.String(length=240), nullable=True),
        sa.Column("credential_number", sa.String(length=160), nullable=True),
        sa.Column("issued_at", sa.Date(), nullable=True),
        sa.Column("expires_at", sa.Date(), nullable=True),
        sa.Column("renewal_due_at", sa.Date(), nullable=True),
        sa.Column("verification_url", sa.String(length=500), nullable=True),
        sa.Column("evidence_object_key", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_compliance_credentials_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["persons.id"],
            name=op.f("fk_compliance_credentials_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["verified_by_person_id"],
            ["persons.id"],
            name=op.f("fk_compliance_credentials_verified_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_compliance_credentials")),
    )
    for column in [
        "credential_number",
        "credential_type",
        "evidence_object_key",
        "expires_at",
        "issuing_body",
        "organization_id",
        "person_id",
        "renewal_due_at",
        "status",
        "title",
        "verified_by_person_id",
    ]:
        op.create_index(
            op.f(f"ix_compliance_credentials_{column}"),
            "compliance_credentials",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "verified_by_person_id",
        "title",
        "status",
        "renewal_due_at",
        "person_id",
        "organization_id",
        "issuing_body",
        "expires_at",
        "evidence_object_key",
        "credential_type",
        "credential_number",
    ]:
        op.drop_index(op.f(f"ix_compliance_credentials_{column}"), table_name="compliance_credentials")
    op.drop_table("compliance_credentials")

    for column in [
        "status",
        "risk_level",
        "reviewed_by_person_id",
        "requested_by_person_id",
        "requested_at",
        "provider",
        "person_id",
        "organization_id",
        "external_reference",
        "expires_at",
        "completed_at",
        "check_type",
    ]:
        op.drop_index(op.f(f"ix_background_checks_{column}"), table_name="background_checks")
    op.drop_table("background_checks")
