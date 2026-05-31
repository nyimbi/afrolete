"""add donor crm stewardship

Revision ID: a497b20260531
Revises: a496b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a497b20260531"
down_revision: str | Sequence[str] | None = "a496b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "donor_profiles",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("donor_type", sa.String(length=80), nullable=False),
        sa.Column("segment", sa.String(length=80), nullable=False),
        sa.Column("preferred_channel", sa.String(length=80), nullable=False),
        sa.Column("giving_capacity", sa.Numeric(12, 2), nullable=True),
        sa.Column("lifetime_giving", sa.Numeric(12, 2), nullable=False),
        sa.Column("last_gift_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("last_gift_on", sa.Date(), nullable=True),
        sa.Column("next_ask_on", sa.Date(), nullable=True),
        sa.Column("tags_json", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_donor_profiles_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_donor_profiles")),
        sa.UniqueConstraint("organization_id", "email", name="uq_donor_profiles_org_email"),
    )
    for column in (
        "donor_type",
        "email",
        "last_gift_on",
        "name",
        "next_ask_on",
        "organization_id",
        "phone",
        "preferred_channel",
        "segment",
        "status",
    ):
        op.create_index(op.f(f"ix_donor_profiles_{column}"), "donor_profiles", [column], unique=False)

    op.add_column("donations", sa.Column("donor_profile_id", GUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_donations_donor_profile_id_donor_profiles"),
        "donations",
        "donor_profiles",
        ["donor_profile_id"],
        ["id"],
    )
    op.create_index(op.f("ix_donations_donor_profile_id"), "donations", ["donor_profile_id"], unique=False)

    op.create_table(
        "donor_interactions",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("donor_profile_id", GUID(), nullable=False),
        sa.Column("campaign_id", GUID(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interaction_type", sa.String(length=80), nullable=False),
        sa.Column("channel", sa.String(length=80), nullable=False),
        sa.Column("subject", sa.String(length=220), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("sentiment", sa.String(length=40), nullable=False),
        sa.Column("outcome", sa.String(length=120), nullable=True),
        sa.Column("owner_name", sa.String(length=180), nullable=True),
        sa.Column("next_follow_up_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["fundraising_campaigns.id"], name=op.f("fk_donor_interactions_campaign_id_fundraising_campaigns")),
        sa.ForeignKeyConstraint(["donor_profile_id"], ["donor_profiles.id"], name=op.f("fk_donor_interactions_donor_profile_id_donor_profiles")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_donor_interactions_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_donor_interactions")),
    )
    for column in (
        "campaign_id",
        "channel",
        "donor_profile_id",
        "interaction_type",
        "next_follow_up_on",
        "occurred_at",
        "organization_id",
        "outcome",
        "owner_name",
        "sentiment",
        "status",
        "subject",
    ):
        op.create_index(op.f(f"ix_donor_interactions_{column}"), "donor_interactions", [column], unique=False)

    op.create_table(
        "donor_stewardship_plans",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("donor_profile_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=220), nullable=False),
        sa.Column("stage", sa.String(length=80), nullable=False),
        sa.Column("priority", sa.String(length=40), nullable=False),
        sa.Column("target_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("completed_on", sa.Date(), nullable=True),
        sa.Column("next_step", sa.Text(), nullable=False),
        sa.Column("recognition_level", sa.String(length=120), nullable=True),
        sa.Column("impact_story_needed", sa.Boolean(), nullable=False),
        sa.Column("owner_name", sa.String(length=180), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["donor_profile_id"], ["donor_profiles.id"], name=op.f("fk_donor_stewardship_plans_donor_profile_id_donor_profiles")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_donor_stewardship_plans_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_donor_stewardship_plans")),
    )
    for column in (
        "completed_on",
        "donor_profile_id",
        "due_on",
        "impact_story_needed",
        "name",
        "organization_id",
        "owner_name",
        "priority",
        "recognition_level",
        "stage",
        "status",
    ):
        op.create_index(op.f(f"ix_donor_stewardship_plans_{column}"), "donor_stewardship_plans", [column], unique=False)


def downgrade() -> None:
    for column in (
        "status",
        "stage",
        "recognition_level",
        "priority",
        "owner_name",
        "organization_id",
        "name",
        "impact_story_needed",
        "due_on",
        "donor_profile_id",
        "completed_on",
    ):
        op.drop_index(op.f(f"ix_donor_stewardship_plans_{column}"), table_name="donor_stewardship_plans")
    op.drop_table("donor_stewardship_plans")
    for column in (
        "subject",
        "status",
        "sentiment",
        "owner_name",
        "outcome",
        "organization_id",
        "occurred_at",
        "next_follow_up_on",
        "interaction_type",
        "donor_profile_id",
        "channel",
        "campaign_id",
    ):
        op.drop_index(op.f(f"ix_donor_interactions_{column}"), table_name="donor_interactions")
    op.drop_table("donor_interactions")
    op.drop_index(op.f("ix_donations_donor_profile_id"), table_name="donations")
    op.drop_constraint(op.f("fk_donations_donor_profile_id_donor_profiles"), "donations", type_="foreignkey")
    op.drop_column("donations", "donor_profile_id")
    for column in (
        "status",
        "segment",
        "preferred_channel",
        "phone",
        "organization_id",
        "next_ask_on",
        "name",
        "last_gift_on",
        "email",
        "donor_type",
    ):
        op.drop_index(op.f(f"ix_donor_profiles_{column}"), table_name="donor_profiles")
    op.drop_table("donor_profiles")
