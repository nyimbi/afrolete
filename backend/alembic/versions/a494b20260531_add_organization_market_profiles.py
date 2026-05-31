"""add organization market profiles

Revision ID: a494b20260531
Revises: a493b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a494b20260531"
down_revision: str | Sequence[str] | None = "a493b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name in ("competition_regional_rule_profiles", "competition_regional_rules"):
        op.alter_column(
            table_name,
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        )
        op.alter_column(
            table_name,
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        )

    op.create_table(
        "organization_market_profiles",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("region_code", sa.String(length=80), nullable=True),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("default_currency", sa.String(length=3), nullable=False),
        sa.Column("reporting_currency", sa.String(length=3), nullable=False),
        sa.Column("exchange_rate_source", sa.String(length=160), nullable=True),
        sa.Column("exchange_rate_margin_bps", sa.Integer(), nullable=False),
        sa.Column("season_rate_lock", sa.Boolean(), nullable=False),
        sa.Column("primary_payment_method", sa.String(length=80), nullable=False),
        sa.Column("supported_payment_methods_json", sa.Text(), nullable=True),
        sa.Column("mobile_money_providers_json", sa.Text(), nullable=True),
        sa.Column("cash_collection_points_json", sa.Text(), nullable=True),
        sa.Column("bank_integrations_json", sa.Text(), nullable=True),
        sa.Column("tax_authority", sa.String(length=180), nullable=True),
        sa.Column("tax_registration_number", sa.String(length=120), nullable=True),
        sa.Column("tax_profile", sa.String(length=120), nullable=True),
        sa.Column("tax_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("tax_exempt_categories_json", sa.Text(), nullable=True),
        sa.Column("government_reporting_agencies_json", sa.Text(), nullable=True),
        sa.Column("federation_reporting_templates_json", sa.Text(), nullable=True),
        sa.Column("compliance_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_market_profiles_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_market_profiles")),
        sa.UniqueConstraint(
            "organization_id",
            "country_code",
            "region_code",
            name=op.f("uq_organization_market_profiles_scope"),
        ),
    )
    for column in (
        "country_code",
        "default_currency",
        "locale",
        "name",
        "organization_id",
        "primary_payment_method",
        "region_code",
        "reporting_currency",
        "status",
        "tax_authority",
        "tax_profile",
        "tax_registration_number",
    ):
        op.create_index(
            op.f(f"ix_organization_market_profiles_{column}"),
            "organization_market_profiles",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in (
        "tax_registration_number",
        "tax_profile",
        "tax_authority",
        "status",
        "reporting_currency",
        "region_code",
        "primary_payment_method",
        "organization_id",
        "name",
        "locale",
        "default_currency",
        "country_code",
    ):
        op.drop_index(op.f(f"ix_organization_market_profiles_{column}"), table_name="organization_market_profiles")
    op.drop_table("organization_market_profiles")
    for table_name in ("competition_regional_rules", "competition_regional_rule_profiles"):
        op.alter_column(
            table_name,
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            server_default=None,
        )
        op.alter_column(
            table_name,
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            server_default=None,
        )
