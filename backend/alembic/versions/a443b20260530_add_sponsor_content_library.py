"""add sponsor content library

Revision ID: a443b20260530
Revises: e6f7a8b9c0d1
Create Date: 2026-05-30 06:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a443b20260530"
down_revision: str | None = "e6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sponsor_content_assets",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("sponsor_id", app.models.base.GUID(), nullable=False),
        sa.Column("sponsorship_agreement_id", app.models.base.GUID(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("asset_type", sa.String(length=80), nullable=False),
        sa.Column("channel", sa.String(length=80), nullable=False),
        sa.Column("format", sa.String(length=80), nullable=False),
        sa.Column("asset_url", sa.String(length=500), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
        sa.Column("usage_guidelines", sa.Text(), nullable=True),
        sa.Column("rights_summary", sa.Text(), nullable=True),
        sa.Column("player_rights_required", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("approval_status", sa.String(length=40), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_name", sa.String(length=180), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False),
        sa.Column("impression_count", sa.Integer(), nullable=False),
        sa.Column("engagement_count", sa.Integer(), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_sponsor_content_assets_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["sponsor_id"],
            ["sponsors.id"],
            name=op.f("fk_sponsor_content_assets_sponsor_id_sponsors"),
        ),
        sa.ForeignKeyConstraint(
            ["sponsorship_agreement_id"],
            ["sponsorship_agreements.id"],
            name=op.f("fk_sponsor_content_assets_sponsorship_agreement_id_sponsorship_agreements"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sponsor_content_assets")),
    )
    op.create_index(op.f("ix_sponsor_content_assets_approval_status"), "sponsor_content_assets", ["approval_status"])
    op.create_index(op.f("ix_sponsor_content_assets_approved_at"), "sponsor_content_assets", ["approved_at"])
    op.create_index(op.f("ix_sponsor_content_assets_asset_type"), "sponsor_content_assets", ["asset_type"])
    op.create_index(op.f("ix_sponsor_content_assets_channel"), "sponsor_content_assets", ["channel"])
    op.create_index(op.f("ix_sponsor_content_assets_expires_at"), "sponsor_content_assets", ["expires_at"])
    op.create_index(op.f("ix_sponsor_content_assets_format"), "sponsor_content_assets", ["format"])
    op.create_index(op.f("ix_sponsor_content_assets_organization_id"), "sponsor_content_assets", ["organization_id"])
    op.create_index(op.f("ix_sponsor_content_assets_player_rights_required"), "sponsor_content_assets", ["player_rights_required"])
    op.create_index(op.f("ix_sponsor_content_assets_sponsor_id"), "sponsor_content_assets", ["sponsor_id"])
    op.create_index(op.f("ix_sponsor_content_assets_sponsorship_agreement_id"), "sponsor_content_assets", ["sponsorship_agreement_id"])
    op.create_index(op.f("ix_sponsor_content_assets_title"), "sponsor_content_assets", ["title"])

    op.create_table(
        "sponsor_content_approval_reviews",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("content_asset_id", app.models.base.GUID(), nullable=False),
        sa.Column("reviewer_name", sa.String(length=180), nullable=False),
        sa.Column("reviewer_email", sa.String(length=320), nullable=True),
        sa.Column("decision", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(
            ["content_asset_id"],
            ["sponsor_content_assets.id"],
            name=op.f("fk_sponsor_content_approval_reviews_content_asset_id_sponsor_content_assets"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_sponsor_content_approval_reviews_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sponsor_content_approval_reviews")),
    )
    op.create_index(op.f("ix_sponsor_content_approval_reviews_content_asset_id"), "sponsor_content_approval_reviews", ["content_asset_id"])
    op.create_index(op.f("ix_sponsor_content_approval_reviews_decided_at"), "sponsor_content_approval_reviews", ["decided_at"])
    op.create_index(op.f("ix_sponsor_content_approval_reviews_decision"), "sponsor_content_approval_reviews", ["decision"])
    op.create_index(op.f("ix_sponsor_content_approval_reviews_organization_id"), "sponsor_content_approval_reviews", ["organization_id"])
    op.create_index(op.f("ix_sponsor_content_approval_reviews_reviewer_email"), "sponsor_content_approval_reviews", ["reviewer_email"])
    op.create_index(op.f("ix_sponsor_content_approval_reviews_reviewer_name"), "sponsor_content_approval_reviews", ["reviewer_name"])

    op.create_table(
        "sponsor_activation_placements",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("sponsor_id", app.models.base.GUID(), nullable=False),
        sa.Column("content_asset_id", app.models.base.GUID(), nullable=True),
        sa.Column("activation_campaign_id", app.models.base.GUID(), nullable=True),
        sa.Column("event_id", app.models.base.GUID(), nullable=True),
        sa.Column("placement_name", sa.String(length=220), nullable=False),
        sa.Column("placement_type", sa.String(length=80), nullable=False),
        sa.Column("channel", sa.String(length=80), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location_name", sa.String(length=180), nullable=True),
        sa.Column("staff_requirements", sa.Text(), nullable=True),
        sa.Column("inventory_checklist", sa.Text(), nullable=True),
        sa.Column("weather_contingency", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("expected_impressions", sa.Integer(), nullable=False),
        sa.Column("actual_impressions", sa.Integer(), nullable=False),
        sa.Column("actual_engagements", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(
            ["activation_campaign_id"],
            ["sponsor_activation_campaigns.id"],
            name=op.f("fk_sponsor_activation_placements_activation_campaign_id_sponsor_activation_campaigns"),
        ),
        sa.ForeignKeyConstraint(
            ["content_asset_id"],
            ["sponsor_content_assets.id"],
            name=op.f("fk_sponsor_activation_placements_content_asset_id_sponsor_content_assets"),
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_sponsor_activation_placements_event_id_events"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_sponsor_activation_placements_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["sponsor_id"],
            ["sponsors.id"],
            name=op.f("fk_sponsor_activation_placements_sponsor_id_sponsors"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sponsor_activation_placements")),
    )
    op.create_index(op.f("ix_sponsor_activation_placements_activation_campaign_id"), "sponsor_activation_placements", ["activation_campaign_id"])
    op.create_index(op.f("ix_sponsor_activation_placements_channel"), "sponsor_activation_placements", ["channel"])
    op.create_index(op.f("ix_sponsor_activation_placements_content_asset_id"), "sponsor_activation_placements", ["content_asset_id"])
    op.create_index(op.f("ix_sponsor_activation_placements_event_id"), "sponsor_activation_placements", ["event_id"])
    op.create_index(op.f("ix_sponsor_activation_placements_location_name"), "sponsor_activation_placements", ["location_name"])
    op.create_index(op.f("ix_sponsor_activation_placements_organization_id"), "sponsor_activation_placements", ["organization_id"])
    op.create_index(op.f("ix_sponsor_activation_placements_placement_name"), "sponsor_activation_placements", ["placement_name"])
    op.create_index(op.f("ix_sponsor_activation_placements_placement_type"), "sponsor_activation_placements", ["placement_type"])
    op.create_index(op.f("ix_sponsor_activation_placements_scheduled_at"), "sponsor_activation_placements", ["scheduled_at"])
    op.create_index(op.f("ix_sponsor_activation_placements_sponsor_id"), "sponsor_activation_placements", ["sponsor_id"])
    op.create_index(op.f("ix_sponsor_activation_placements_status"), "sponsor_activation_placements", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_sponsor_activation_placements_status"), table_name="sponsor_activation_placements")
    op.drop_index(op.f("ix_sponsor_activation_placements_sponsor_id"), table_name="sponsor_activation_placements")
    op.drop_index(op.f("ix_sponsor_activation_placements_scheduled_at"), table_name="sponsor_activation_placements")
    op.drop_index(op.f("ix_sponsor_activation_placements_placement_type"), table_name="sponsor_activation_placements")
    op.drop_index(op.f("ix_sponsor_activation_placements_placement_name"), table_name="sponsor_activation_placements")
    op.drop_index(op.f("ix_sponsor_activation_placements_organization_id"), table_name="sponsor_activation_placements")
    op.drop_index(op.f("ix_sponsor_activation_placements_location_name"), table_name="sponsor_activation_placements")
    op.drop_index(op.f("ix_sponsor_activation_placements_event_id"), table_name="sponsor_activation_placements")
    op.drop_index(op.f("ix_sponsor_activation_placements_content_asset_id"), table_name="sponsor_activation_placements")
    op.drop_index(op.f("ix_sponsor_activation_placements_channel"), table_name="sponsor_activation_placements")
    op.drop_index(op.f("ix_sponsor_activation_placements_activation_campaign_id"), table_name="sponsor_activation_placements")
    op.drop_table("sponsor_activation_placements")

    op.drop_index(op.f("ix_sponsor_content_approval_reviews_reviewer_name"), table_name="sponsor_content_approval_reviews")
    op.drop_index(op.f("ix_sponsor_content_approval_reviews_reviewer_email"), table_name="sponsor_content_approval_reviews")
    op.drop_index(op.f("ix_sponsor_content_approval_reviews_organization_id"), table_name="sponsor_content_approval_reviews")
    op.drop_index(op.f("ix_sponsor_content_approval_reviews_decision"), table_name="sponsor_content_approval_reviews")
    op.drop_index(op.f("ix_sponsor_content_approval_reviews_decided_at"), table_name="sponsor_content_approval_reviews")
    op.drop_index(op.f("ix_sponsor_content_approval_reviews_content_asset_id"), table_name="sponsor_content_approval_reviews")
    op.drop_table("sponsor_content_approval_reviews")

    op.drop_index(op.f("ix_sponsor_content_assets_title"), table_name="sponsor_content_assets")
    op.drop_index(op.f("ix_sponsor_content_assets_sponsorship_agreement_id"), table_name="sponsor_content_assets")
    op.drop_index(op.f("ix_sponsor_content_assets_sponsor_id"), table_name="sponsor_content_assets")
    op.drop_index(op.f("ix_sponsor_content_assets_player_rights_required"), table_name="sponsor_content_assets")
    op.drop_index(op.f("ix_sponsor_content_assets_organization_id"), table_name="sponsor_content_assets")
    op.drop_index(op.f("ix_sponsor_content_assets_format"), table_name="sponsor_content_assets")
    op.drop_index(op.f("ix_sponsor_content_assets_expires_at"), table_name="sponsor_content_assets")
    op.drop_index(op.f("ix_sponsor_content_assets_channel"), table_name="sponsor_content_assets")
    op.drop_index(op.f("ix_sponsor_content_assets_asset_type"), table_name="sponsor_content_assets")
    op.drop_index(op.f("ix_sponsor_content_assets_approved_at"), table_name="sponsor_content_assets")
    op.drop_index(op.f("ix_sponsor_content_assets_approval_status"), table_name="sponsor_content_assets")
    op.drop_table("sponsor_content_assets")
