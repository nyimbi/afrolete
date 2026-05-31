"""add recurring donations

Revision ID: a517b20260531
Revises: a516b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a517b20260531"
down_revision: str | Sequence[str] | None = "a516b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recurring_donations",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("campaign_id", GUID(), nullable=False),
        sa.Column("donor_profile_id", GUID(), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("frequency", sa.String(40), nullable=False, server_default="monthly"),
        sa.Column("started_on", sa.Date(), nullable=False),
        sa.Column("next_charge_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("payment_provider", sa.String(80), nullable=False, server_default="manual"),
        sa.Column("payment_method", sa.String(80), nullable=False, server_default="recurring_pledge"),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
        sa.Column("total_collected", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("donation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_donation_id", GUID(), nullable=True),
        sa.Column("tax_receipt_auto_issue", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["campaign_id"], ["fundraising_campaigns.id"], name=op.f("fk_recurring_donations_campaign_id_fundraising_campaigns")),
        sa.ForeignKeyConstraint(["donor_profile_id"], ["donor_profiles.id"], name=op.f("fk_recurring_donations_donor_profile_id_donor_profiles")),
        sa.ForeignKeyConstraint(["last_donation_id"], ["donations.id"], name=op.f("fk_recurring_donations_last_donation_id_donations")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_recurring_donations_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recurring_donations")),
        sa.UniqueConstraint("organization_id", "name", "donor_profile_id", name="uq_recurring_donations_org_name_donor"),
    )
    for column in (
        "organization_id",
        "campaign_id",
        "donor_profile_id",
        "name",
        "frequency",
        "started_on",
        "next_charge_on",
        "ends_on",
        "payment_provider",
        "payment_method",
        "status",
        "last_donation_id",
    ):
        op.create_index(op.f(f"ix_recurring_donations_{column}"), "recurring_donations", [column])


def downgrade() -> None:
    for column in (
        "last_donation_id",
        "status",
        "payment_method",
        "payment_provider",
        "ends_on",
        "next_charge_on",
        "started_on",
        "frequency",
        "name",
        "donor_profile_id",
        "campaign_id",
        "organization_id",
    ):
        op.drop_index(op.f(f"ix_recurring_donations_{column}"), table_name="recurring_donations")
    op.drop_table("recurring_donations")
