"""add donation tax receipts

Revision ID: a516b20260531
Revises: a515b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a516b20260531"
down_revision: str | Sequence[str] | None = "a515b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "donation_tax_receipts",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("donation_id", GUID(), nullable=False),
        sa.Column("donor_profile_id", GUID(), nullable=True),
        sa.Column("receipt_number", sa.String(120), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("tax_year", sa.Integer(), nullable=False),
        sa.Column("jurisdiction", sa.String(120), nullable=False, server_default="local"),
        sa.Column("donor_name", sa.String(180), nullable=False),
        sa.Column("donor_email", sa.String(320), nullable=True),
        sa.Column("organization_name", sa.String(240), nullable=False),
        sa.Column("organization_tax_id", sa.String(120), nullable=True),
        sa.Column("deductible_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(40), nullable=False, server_default="issued"),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("content_checksum", sa.String(64), nullable=False),
        sa.Column("download_filename", sa.String(240), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["donation_id"], ["donations.id"], name=op.f("fk_donation_tax_receipts_donation_id_donations")),
        sa.ForeignKeyConstraint(["donor_profile_id"], ["donor_profiles.id"], name=op.f("fk_donation_tax_receipts_donor_profile_id_donor_profiles")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_donation_tax_receipts_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_donation_tax_receipts")),
        sa.UniqueConstraint("donation_id", name="uq_donation_tax_receipts_donation_id"),
        sa.UniqueConstraint("organization_id", "receipt_number", name="uq_donation_tax_receipts_org_number"),
    )
    for column in (
        "organization_id",
        "donation_id",
        "donor_profile_id",
        "receipt_number",
        "issued_on",
        "tax_year",
        "jurisdiction",
        "donor_name",
        "donor_email",
        "organization_tax_id",
        "status",
        "content_checksum",
    ):
        op.create_index(op.f(f"ix_donation_tax_receipts_{column}"), "donation_tax_receipts", [column])


def downgrade() -> None:
    for column in (
        "content_checksum",
        "status",
        "organization_tax_id",
        "donor_email",
        "donor_name",
        "jurisdiction",
        "tax_year",
        "issued_on",
        "receipt_number",
        "donor_profile_id",
        "donation_id",
        "organization_id",
    ):
        op.drop_index(op.f(f"ix_donation_tax_receipts_{column}"), table_name="donation_tax_receipts")
    op.drop_table("donation_tax_receipts")
