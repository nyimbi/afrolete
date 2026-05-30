"""add facility lease agreements

Revision ID: a454b20260530
Revises: a453b20260530
Create Date: 2026-05-30 17:40:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a454b20260530"
down_revision: str | None = "a453b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "facility_lease_agreements",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("finance_invoice_id", app.models.base.GUID(), nullable=True),
        sa.Column("lessor_name", sa.String(length=180), nullable=False),
        sa.Column("lessee_name", sa.String(length=180), nullable=False),
        sa.Column("lessee_contact_name", sa.String(length=180), nullable=True),
        sa.Column("lessee_contact_email", sa.String(length=255), nullable=True),
        sa.Column("usage_terms", sa.Text(), nullable=False),
        sa.Column("included_services", sa.Text(), nullable=True),
        sa.Column("extra_charges", sa.Text(), nullable=True),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("monthly_rent", sa.Numeric(12, 2), nullable=False),
        sa.Column("security_deposit", sa.Numeric(12, 2), nullable=True),
        sa.Column("deposit_status", sa.String(length=40), nullable=False),
        sa.Column("next_invoice_on", sa.Date(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False),
        sa.Column("renewal_notice_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("compliance_status", sa.String(length=40), nullable=False),
        sa.Column("compliance_notes", sa.Text(), nullable=True),
        sa.Column("document_url", sa.String(length=500), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("terminated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_facility_lease_agreements_facility_id_facilities")),
        sa.ForeignKeyConstraint(["finance_invoice_id"], ["finance_invoices.id"], name=op.f("fk_facility_lease_agreements_finance_invoice_id_finance_invoices")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_facility_lease_agreements_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_lease_agreements")),
    )
    for column in [
        "auto_renew",
        "compliance_status",
        "deposit_status",
        "ends_on",
        "facility_id",
        "finance_invoice_id",
        "lessee_contact_email",
        "lessee_name",
        "lessor_name",
        "next_invoice_on",
        "organization_id",
        "renewal_notice_on",
        "signed_at",
        "starts_on",
        "status",
        "terminated_at",
    ]:
        op.create_index(op.f(f"ix_facility_lease_agreements_{column}"), "facility_lease_agreements", [column])


def downgrade() -> None:
    for column in [
        "terminated_at",
        "status",
        "starts_on",
        "signed_at",
        "renewal_notice_on",
        "organization_id",
        "next_invoice_on",
        "lessor_name",
        "lessee_name",
        "lessee_contact_email",
        "finance_invoice_id",
        "facility_id",
        "ends_on",
        "deposit_status",
        "compliance_status",
        "auto_renew",
    ]:
        op.drop_index(op.f(f"ix_facility_lease_agreements_{column}"), table_name="facility_lease_agreements")
    op.drop_table("facility_lease_agreements")
