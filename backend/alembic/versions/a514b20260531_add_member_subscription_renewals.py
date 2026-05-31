"""add member subscription renewals

Revision ID: a514b20260531
Revises: a513b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID, enum_type
from app.models.enums import MemberSubjectType


revision: str = "a514b20260531"
down_revision: str | Sequence[str] | None = "a513b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "member_subscription_renewal_campaigns",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("plan_id", GUID(), nullable=True),
        sa.Column("target_member_role", sa.String(80), nullable=True),
        sa.Column("renewal_window_start", sa.Date(), nullable=False),
        sa.Column("renewal_window_end", sa.Date(), nullable=False),
        sa.Column("offer_due_on", sa.Date(), nullable=False),
        sa.Column("early_bird_deadline", sa.Date(), nullable=True),
        sa.Column("early_bird_discount_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="draft"),
        sa.Column("generated_offer_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_offer_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_member_subscription_renewal_campaigns_organization_id_organizations")),
        sa.ForeignKeyConstraint(["plan_id"], ["member_subscription_plans.id"], name=op.f("fk_member_subscription_renewal_campaigns_plan_id_member_subscription_plans")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_subscription_renewal_campaigns")),
        sa.UniqueConstraint("organization_id", "name", name=op.f("uq_member_subscription_renewal_campaigns_organization_id")),
    )
    for column in (
        "organization_id",
        "name",
        "plan_id",
        "target_member_role",
        "renewal_window_start",
        "renewal_window_end",
        "offer_due_on",
        "early_bird_deadline",
        "status",
    ):
        op.create_index(op.f(f"ix_member_subscription_renewal_campaigns_{column}"), "member_subscription_renewal_campaigns", [column])

    op.create_table(
        "member_subscription_renewal_offers",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("campaign_id", GUID(), nullable=False),
        sa.Column("subscription_id", GUID(), nullable=False),
        sa.Column("plan_id", GUID(), nullable=False),
        sa.Column("subject_type", enum_type(MemberSubjectType), nullable=False),
        sa.Column("subject_id", GUID(), nullable=False),
        sa.Column("renewal_period_start", sa.Date(), nullable=False),
        sa.Column("renewal_period_end", sa.Date(), nullable=False),
        sa.Column("base_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("final_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="KES"),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="offered"),
        sa.Column("accepted_on", sa.Date(), nullable=True),
        sa.Column("accepted_by_person_id", GUID(), nullable=True),
        sa.Column("charge_id", GUID(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["accepted_by_person_id"], ["persons.id"], name=op.f("fk_member_subscription_renewal_offers_accepted_by_person_id_persons")),
        sa.ForeignKeyConstraint(["campaign_id"], ["member_subscription_renewal_campaigns.id"], name=op.f("fk_member_subscription_renewal_offers_campaign_id_member_subscription_renewal_campaigns")),
        sa.ForeignKeyConstraint(["charge_id"], ["member_subscription_charges.id"], name=op.f("fk_member_subscription_renewal_offers_charge_id_member_subscription_charges")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_member_subscription_renewal_offers_organization_id_organizations")),
        sa.ForeignKeyConstraint(["plan_id"], ["member_subscription_plans.id"], name=op.f("fk_member_subscription_renewal_offers_plan_id_member_subscription_plans")),
        sa.ForeignKeyConstraint(["subscription_id"], ["member_subscriptions.id"], name=op.f("fk_member_subscription_renewal_offers_subscription_id_member_subscriptions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_subscription_renewal_offers")),
        sa.UniqueConstraint("campaign_id", "subscription_id", name="uq_member_subscription_renewal_offers_campaign_subscription"),
    )
    for column in (
        "organization_id",
        "campaign_id",
        "subscription_id",
        "plan_id",
        "subject_type",
        "subject_id",
        "renewal_period_start",
        "renewal_period_end",
        "due_on",
        "status",
        "accepted_on",
        "accepted_by_person_id",
        "charge_id",
    ):
        op.create_index(op.f(f"ix_member_subscription_renewal_offers_{column}"), "member_subscription_renewal_offers", [column])


def downgrade() -> None:
    for column in (
        "charge_id",
        "accepted_by_person_id",
        "accepted_on",
        "status",
        "due_on",
        "renewal_period_end",
        "renewal_period_start",
        "subject_id",
        "subject_type",
        "plan_id",
        "subscription_id",
        "campaign_id",
        "organization_id",
    ):
        op.drop_index(op.f(f"ix_member_subscription_renewal_offers_{column}"), table_name="member_subscription_renewal_offers")
    op.drop_table("member_subscription_renewal_offers")
    for column in (
        "status",
        "early_bird_deadline",
        "offer_due_on",
        "renewal_window_end",
        "renewal_window_start",
        "target_member_role",
        "plan_id",
        "name",
        "organization_id",
    ):
        op.drop_index(op.f(f"ix_member_subscription_renewal_campaigns_{column}"), table_name="member_subscription_renewal_campaigns")
    op.drop_table("member_subscription_renewal_campaigns")
