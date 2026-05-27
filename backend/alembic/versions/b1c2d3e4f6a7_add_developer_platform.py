"""add developer platform

Revision ID: b1c2d3e4f6a7
Revises: a0b1c2d3e4f5
Create Date: 2026-05-28 03:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "b1c2d3e4f6a7"
down_revision: str | None = "a0b1c2d3e4f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "developer_applications",
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("owner_person_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("app_type", sa.String(length=80), nullable=False),
        sa.Column("client_id", sa.String(length=120), nullable=False),
        sa.Column("client_secret_hash", sa.String(length=64), nullable=False),
        sa.Column("redirect_uris", sa.Text(), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=False),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["owner_person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name"),
        sa.UniqueConstraint("client_id"),
    )
    op.create_index(op.f("ix_developer_applications_app_type"), "developer_applications", ["app_type"])
    op.create_index(op.f("ix_developer_applications_client_id"), "developer_applications", ["client_id"])
    op.create_index(op.f("ix_developer_applications_contact_email"), "developer_applications", ["contact_email"])
    op.create_index(op.f("ix_developer_applications_name"), "developer_applications", ["name"])
    op.create_index(op.f("ix_developer_applications_organization_id"), "developer_applications", ["organization_id"])
    op.create_index(op.f("ix_developer_applications_owner_person_id"), "developer_applications", ["owner_person_id"])
    op.create_index(op.f("ix_developer_applications_status"), "developer_applications", ["status"])

    op.create_table(
        "developer_webhook_subscriptions",
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("target_url", sa.String(length=500), nullable=False),
        sa.Column("event_types", sa.Text(), nullable=False),
        sa.Column("signing_secret_hash", sa.String(length=64), nullable=False),
        sa.Column("delivery_mode", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("last_delivery_status", sa.String(length=80), nullable=True),
        sa.Column("last_delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["developer_applications.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name"),
    )
    op.create_index(
        op.f("ix_developer_webhook_subscriptions_application_id"),
        "developer_webhook_subscriptions",
        ["application_id"],
    )
    op.create_index(
        op.f("ix_developer_webhook_subscriptions_delivery_mode"),
        "developer_webhook_subscriptions",
        ["delivery_mode"],
    )
    op.create_index(op.f("ix_developer_webhook_subscriptions_name"), "developer_webhook_subscriptions", ["name"])
    op.create_index(
        op.f("ix_developer_webhook_subscriptions_organization_id"),
        "developer_webhook_subscriptions",
        ["organization_id"],
    )
    op.create_index(op.f("ix_developer_webhook_subscriptions_status"), "developer_webhook_subscriptions", ["status"])

    op.create_table(
        "developer_marketplace_listings",
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("install_url", sa.String(length=500), nullable=True),
        sa.Column("support_url", sa.String(length=500), nullable=True),
        sa.Column("pricing_model", sa.String(length=80), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("visibility", sa.String(length=40), nullable=False),
        sa.Column("review_status", sa.String(length=40), nullable=False),
        sa.Column("install_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["developer_applications.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name"),
    )
    op.create_index(
        op.f("ix_developer_marketplace_listings_application_id"),
        "developer_marketplace_listings",
        ["application_id"],
    )
    op.create_index(op.f("ix_developer_marketplace_listings_category"), "developer_marketplace_listings", ["category"])
    op.create_index(op.f("ix_developer_marketplace_listings_name"), "developer_marketplace_listings", ["name"])
    op.create_index(
        op.f("ix_developer_marketplace_listings_organization_id"),
        "developer_marketplace_listings",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_developer_marketplace_listings_pricing_model"),
        "developer_marketplace_listings",
        ["pricing_model"],
    )
    op.create_index(
        op.f("ix_developer_marketplace_listings_review_status"),
        "developer_marketplace_listings",
        ["review_status"],
    )
    op.create_index(op.f("ix_developer_marketplace_listings_visibility"), "developer_marketplace_listings", ["visibility"])


def downgrade() -> None:
    op.drop_index(op.f("ix_developer_marketplace_listings_visibility"), table_name="developer_marketplace_listings")
    op.drop_index(op.f("ix_developer_marketplace_listings_review_status"), table_name="developer_marketplace_listings")
    op.drop_index(op.f("ix_developer_marketplace_listings_pricing_model"), table_name="developer_marketplace_listings")
    op.drop_index(op.f("ix_developer_marketplace_listings_organization_id"), table_name="developer_marketplace_listings")
    op.drop_index(op.f("ix_developer_marketplace_listings_name"), table_name="developer_marketplace_listings")
    op.drop_index(op.f("ix_developer_marketplace_listings_category"), table_name="developer_marketplace_listings")
    op.drop_index(op.f("ix_developer_marketplace_listings_application_id"), table_name="developer_marketplace_listings")
    op.drop_table("developer_marketplace_listings")
    op.drop_index(op.f("ix_developer_webhook_subscriptions_status"), table_name="developer_webhook_subscriptions")
    op.drop_index(op.f("ix_developer_webhook_subscriptions_organization_id"), table_name="developer_webhook_subscriptions")
    op.drop_index(op.f("ix_developer_webhook_subscriptions_name"), table_name="developer_webhook_subscriptions")
    op.drop_index(op.f("ix_developer_webhook_subscriptions_delivery_mode"), table_name="developer_webhook_subscriptions")
    op.drop_index(op.f("ix_developer_webhook_subscriptions_application_id"), table_name="developer_webhook_subscriptions")
    op.drop_table("developer_webhook_subscriptions")
    op.drop_index(op.f("ix_developer_applications_status"), table_name="developer_applications")
    op.drop_index(op.f("ix_developer_applications_owner_person_id"), table_name="developer_applications")
    op.drop_index(op.f("ix_developer_applications_organization_id"), table_name="developer_applications")
    op.drop_index(op.f("ix_developer_applications_name"), table_name="developer_applications")
    op.drop_index(op.f("ix_developer_applications_contact_email"), table_name="developer_applications")
    op.drop_index(op.f("ix_developer_applications_client_id"), table_name="developer_applications")
    op.drop_index(op.f("ix_developer_applications_app_type"), table_name="developer_applications")
    op.drop_table("developer_applications")
