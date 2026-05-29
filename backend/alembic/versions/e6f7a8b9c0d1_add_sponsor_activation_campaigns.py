"""add sponsor activation campaigns

Revision ID: e6f7a8b9c0d1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-30 05:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "e6f7a8b9c0d1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


commercial_status = sa.Enum(
    "draft",
    "active",
    "pledged",
    "paid",
    "partial",
    "overdue",
    "completed",
    "cancelled",
    name="commercialstatus",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "sponsor_activation_campaigns",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("sponsor_id", app.models.base.GUID(), nullable=False),
        sa.Column("sponsorship_agreement_id", app.models.base.GUID(), nullable=True),
        sa.Column("fan_challenge_id", app.models.base.GUID(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("objective", sa.String(length=240), nullable=False),
        sa.Column("offer_summary", sa.Text(), nullable=False),
        sa.Column("coupon_code", sa.String(length=80), nullable=False),
        sa.Column("discount_type", sa.String(length=40), nullable=False),
        sa.Column("discount_value", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("target_url", sa.String(length=500), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", commercial_status, nullable=False),
        sa.Column("impression_count", sa.Integer(), nullable=False),
        sa.Column("signup_count", sa.Integer(), nullable=False),
        sa.Column("redemption_count", sa.Integer(), nullable=False),
        sa.Column("conversion_value", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(
            ["fan_challenge_id"],
            ["fan_engagement_challenges.id"],
            name=op.f("fk_sponsor_activation_campaigns_fan_challenge_id_fan_engagement_challenges"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_sponsor_activation_campaigns_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["sponsor_id"],
            ["sponsors.id"],
            name=op.f("fk_sponsor_activation_campaigns_sponsor_id_sponsors"),
        ),
        sa.ForeignKeyConstraint(
            ["sponsorship_agreement_id"],
            ["sponsorship_agreements.id"],
            name=op.f("fk_sponsor_activation_campaigns_sponsorship_agreement_id_sponsorship_agreements"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sponsor_activation_campaigns")),
        sa.UniqueConstraint("organization_id", "coupon_code", name=op.f("uq_sponsor_activation_campaigns_organization_id")),
    )
    op.create_index(op.f("ix_sponsor_activation_campaigns_coupon_code"), "sponsor_activation_campaigns", ["coupon_code"])
    op.create_index(op.f("ix_sponsor_activation_campaigns_discount_type"), "sponsor_activation_campaigns", ["discount_type"])
    op.create_index(op.f("ix_sponsor_activation_campaigns_ends_at"), "sponsor_activation_campaigns", ["ends_at"])
    op.create_index(op.f("ix_sponsor_activation_campaigns_fan_challenge_id"), "sponsor_activation_campaigns", ["fan_challenge_id"])
    op.create_index(op.f("ix_sponsor_activation_campaigns_organization_id"), "sponsor_activation_campaigns", ["organization_id"])
    op.create_index(op.f("ix_sponsor_activation_campaigns_sponsor_id"), "sponsor_activation_campaigns", ["sponsor_id"])
    op.create_index(
        op.f("ix_sponsor_activation_campaigns_sponsorship_agreement_id"),
        "sponsor_activation_campaigns",
        ["sponsorship_agreement_id"],
    )
    op.create_index(op.f("ix_sponsor_activation_campaigns_starts_at"), "sponsor_activation_campaigns", ["starts_at"])
    op.create_index(op.f("ix_sponsor_activation_campaigns_status"), "sponsor_activation_campaigns", ["status"])
    op.create_index(op.f("ix_sponsor_activation_campaigns_title"), "sponsor_activation_campaigns", ["title"])

    op.create_table(
        "sponsor_coupon_redemptions",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("activation_campaign_id", app.models.base.GUID(), nullable=False),
        sa.Column("supporter_profile_id", app.models.base.GUID(), nullable=True),
        sa.Column("redeemer_name", sa.String(length=180), nullable=False),
        sa.Column("redeemer_email", sa.String(length=320), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("order_reference", sa.String(length=240), nullable=True),
        sa.Column("discount_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("purchase_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("status", commercial_status, nullable=False),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(
            ["activation_campaign_id"],
            ["sponsor_activation_campaigns.id"],
            name=op.f("fk_sponsor_coupon_redemptions_activation_campaign_id_sponsor_activation_campaigns"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_sponsor_coupon_redemptions_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["supporter_profile_id"],
            ["supporter_profiles.id"],
            name=op.f("fk_sponsor_coupon_redemptions_supporter_profile_id_supporter_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sponsor_coupon_redemptions")),
    )
    op.create_index(op.f("ix_sponsor_coupon_redemptions_activation_campaign_id"), "sponsor_coupon_redemptions", ["activation_campaign_id"])
    op.create_index(op.f("ix_sponsor_coupon_redemptions_order_reference"), "sponsor_coupon_redemptions", ["order_reference"])
    op.create_index(op.f("ix_sponsor_coupon_redemptions_organization_id"), "sponsor_coupon_redemptions", ["organization_id"])
    op.create_index(op.f("ix_sponsor_coupon_redemptions_redeemed_at"), "sponsor_coupon_redemptions", ["redeemed_at"])
    op.create_index(op.f("ix_sponsor_coupon_redemptions_redeemer_email"), "sponsor_coupon_redemptions", ["redeemer_email"])
    op.create_index(op.f("ix_sponsor_coupon_redemptions_redeemer_name"), "sponsor_coupon_redemptions", ["redeemer_name"])
    op.create_index(op.f("ix_sponsor_coupon_redemptions_source"), "sponsor_coupon_redemptions", ["source"])
    op.create_index(op.f("ix_sponsor_coupon_redemptions_status"), "sponsor_coupon_redemptions", ["status"])
    op.create_index(op.f("ix_sponsor_coupon_redemptions_supporter_profile_id"), "sponsor_coupon_redemptions", ["supporter_profile_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_sponsor_coupon_redemptions_supporter_profile_id"), table_name="sponsor_coupon_redemptions")
    op.drop_index(op.f("ix_sponsor_coupon_redemptions_status"), table_name="sponsor_coupon_redemptions")
    op.drop_index(op.f("ix_sponsor_coupon_redemptions_source"), table_name="sponsor_coupon_redemptions")
    op.drop_index(op.f("ix_sponsor_coupon_redemptions_redeemer_name"), table_name="sponsor_coupon_redemptions")
    op.drop_index(op.f("ix_sponsor_coupon_redemptions_redeemer_email"), table_name="sponsor_coupon_redemptions")
    op.drop_index(op.f("ix_sponsor_coupon_redemptions_redeemed_at"), table_name="sponsor_coupon_redemptions")
    op.drop_index(op.f("ix_sponsor_coupon_redemptions_organization_id"), table_name="sponsor_coupon_redemptions")
    op.drop_index(op.f("ix_sponsor_coupon_redemptions_order_reference"), table_name="sponsor_coupon_redemptions")
    op.drop_index(op.f("ix_sponsor_coupon_redemptions_activation_campaign_id"), table_name="sponsor_coupon_redemptions")
    op.drop_table("sponsor_coupon_redemptions")

    op.drop_index(op.f("ix_sponsor_activation_campaigns_title"), table_name="sponsor_activation_campaigns")
    op.drop_index(op.f("ix_sponsor_activation_campaigns_status"), table_name="sponsor_activation_campaigns")
    op.drop_index(op.f("ix_sponsor_activation_campaigns_starts_at"), table_name="sponsor_activation_campaigns")
    op.drop_index(op.f("ix_sponsor_activation_campaigns_sponsorship_agreement_id"), table_name="sponsor_activation_campaigns")
    op.drop_index(op.f("ix_sponsor_activation_campaigns_sponsor_id"), table_name="sponsor_activation_campaigns")
    op.drop_index(op.f("ix_sponsor_activation_campaigns_organization_id"), table_name="sponsor_activation_campaigns")
    op.drop_index(op.f("ix_sponsor_activation_campaigns_fan_challenge_id"), table_name="sponsor_activation_campaigns")
    op.drop_index(op.f("ix_sponsor_activation_campaigns_ends_at"), table_name="sponsor_activation_campaigns")
    op.drop_index(op.f("ix_sponsor_activation_campaigns_discount_type"), table_name="sponsor_activation_campaigns")
    op.drop_index(op.f("ix_sponsor_activation_campaigns_coupon_code"), table_name="sponsor_activation_campaigns")
    op.drop_table("sponsor_activation_campaigns")
