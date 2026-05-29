"""add event ticketing controls

Revision ID: a446b20260530
Revises: a445b20260530
Create Date: 2026-05-30 08:15:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a446b20260530"
down_revision: str | None = "a445b20260530"
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
        "ticket_bundle_offers",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_id", app.models.base.GUID(), nullable=False),
        sa.Column("ticket_product_id", app.models.base.GUID(), nullable=False),
        sa.Column("merchandise_product_id", app.models.base.GUID(), nullable=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("package_type", sa.String(length=80), nullable=False),
        sa.Column("ticket_quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("channel", sa.String(length=80), nullable=False),
        sa.Column("sales_limit", sa.Integer(), nullable=True),
        sa.Column("sold_count", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", commercial_status, nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_ticket_bundle_offers_event_id_events"),
        ),
        sa.ForeignKeyConstraint(
            ["merchandise_product_id"],
            ["merchandise_products.id"],
            name=op.f("fk_ticket_bundle_offers_merchandise_product_id_merchandise_products"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_ticket_bundle_offers_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["ticket_product_id"],
            ["ticket_products.id"],
            name=op.f("fk_ticket_bundle_offers_ticket_product_id_ticket_products"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ticket_bundle_offers")),
    )
    op.create_index(op.f("ix_ticket_bundle_offers_channel"), "ticket_bundle_offers", ["channel"])
    op.create_index(op.f("ix_ticket_bundle_offers_ends_at"), "ticket_bundle_offers", ["ends_at"])
    op.create_index(op.f("ix_ticket_bundle_offers_event_id"), "ticket_bundle_offers", ["event_id"])
    op.create_index(op.f("ix_ticket_bundle_offers_merchandise_product_id"), "ticket_bundle_offers", ["merchandise_product_id"])
    op.create_index(op.f("ix_ticket_bundle_offers_name"), "ticket_bundle_offers", ["name"])
    op.create_index(op.f("ix_ticket_bundle_offers_organization_id"), "ticket_bundle_offers", ["organization_id"])
    op.create_index(op.f("ix_ticket_bundle_offers_package_type"), "ticket_bundle_offers", ["package_type"])
    op.create_index(op.f("ix_ticket_bundle_offers_starts_at"), "ticket_bundle_offers", ["starts_at"])
    op.create_index(op.f("ix_ticket_bundle_offers_status"), "ticket_bundle_offers", ["status"])
    op.create_index(op.f("ix_ticket_bundle_offers_ticket_product_id"), "ticket_bundle_offers", ["ticket_product_id"])

    op.create_table(
        "ticket_seat_assignments",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_id", app.models.base.GUID(), nullable=False),
        sa.Column("ticket_id", app.models.base.GUID(), nullable=False),
        sa.Column("section", sa.String(length=80), nullable=False),
        sa.Column("row", sa.String(length=40), nullable=True),
        sa.Column("seat", sa.String(length=40), nullable=True),
        sa.Column("access_zone", sa.String(length=120), nullable=True),
        sa.Column("accessible", sa.Boolean(), nullable=False),
        sa.Column("companion_seat", sa.Boolean(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_ticket_seat_assignments_event_id_events"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_ticket_seat_assignments_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
            name=op.f("fk_ticket_seat_assignments_ticket_id_tickets"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ticket_seat_assignments")),
        sa.UniqueConstraint("ticket_id", name=op.f("uq_ticket_seat_assignments_ticket_id")),
    )
    op.create_index(op.f("ix_ticket_seat_assignments_access_zone"), "ticket_seat_assignments", ["access_zone"])
    op.create_index(op.f("ix_ticket_seat_assignments_accessible"), "ticket_seat_assignments", ["accessible"])
    op.create_index(op.f("ix_ticket_seat_assignments_assigned_at"), "ticket_seat_assignments", ["assigned_at"])
    op.create_index(op.f("ix_ticket_seat_assignments_companion_seat"), "ticket_seat_assignments", ["companion_seat"])
    op.create_index(op.f("ix_ticket_seat_assignments_event_id"), "ticket_seat_assignments", ["event_id"])
    op.create_index(op.f("ix_ticket_seat_assignments_organization_id"), "ticket_seat_assignments", ["organization_id"])
    op.create_index(op.f("ix_ticket_seat_assignments_row"), "ticket_seat_assignments", ["row"])
    op.create_index(op.f("ix_ticket_seat_assignments_seat"), "ticket_seat_assignments", ["seat"])
    op.create_index(op.f("ix_ticket_seat_assignments_section"), "ticket_seat_assignments", ["section"])
    op.create_index(op.f("ix_ticket_seat_assignments_ticket_id"), "ticket_seat_assignments", ["ticket_id"])

    op.create_table(
        "ticket_resale_listings",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_id", app.models.base.GUID(), nullable=False),
        sa.Column("ticket_id", app.models.base.GUID(), nullable=False),
        sa.Column("seller_name", sa.String(length=180), nullable=False),
        sa.Column("seller_email", sa.String(length=320), nullable=False),
        sa.Column("resale_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("buyer_name", sa.String(length=180), nullable=True),
        sa.Column("buyer_email", sa.String(length=320), nullable=True),
        sa.Column("listed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sold_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_ticket_resale_listings_event_id_events"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_ticket_resale_listings_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
            name=op.f("fk_ticket_resale_listings_ticket_id_tickets"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ticket_resale_listings")),
    )
    op.create_index(op.f("ix_ticket_resale_listings_buyer_email"), "ticket_resale_listings", ["buyer_email"])
    op.create_index(op.f("ix_ticket_resale_listings_buyer_name"), "ticket_resale_listings", ["buyer_name"])
    op.create_index(op.f("ix_ticket_resale_listings_event_id"), "ticket_resale_listings", ["event_id"])
    op.create_index(op.f("ix_ticket_resale_listings_listed_at"), "ticket_resale_listings", ["listed_at"])
    op.create_index(op.f("ix_ticket_resale_listings_organization_id"), "ticket_resale_listings", ["organization_id"])
    op.create_index(op.f("ix_ticket_resale_listings_seller_email"), "ticket_resale_listings", ["seller_email"])
    op.create_index(op.f("ix_ticket_resale_listings_seller_name"), "ticket_resale_listings", ["seller_name"])
    op.create_index(op.f("ix_ticket_resale_listings_sold_at"), "ticket_resale_listings", ["sold_at"])
    op.create_index(op.f("ix_ticket_resale_listings_status"), "ticket_resale_listings", ["status"])
    op.create_index(op.f("ix_ticket_resale_listings_ticket_id"), "ticket_resale_listings", ["ticket_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ticket_resale_listings_ticket_id"), table_name="ticket_resale_listings")
    op.drop_index(op.f("ix_ticket_resale_listings_status"), table_name="ticket_resale_listings")
    op.drop_index(op.f("ix_ticket_resale_listings_sold_at"), table_name="ticket_resale_listings")
    op.drop_index(op.f("ix_ticket_resale_listings_seller_name"), table_name="ticket_resale_listings")
    op.drop_index(op.f("ix_ticket_resale_listings_seller_email"), table_name="ticket_resale_listings")
    op.drop_index(op.f("ix_ticket_resale_listings_organization_id"), table_name="ticket_resale_listings")
    op.drop_index(op.f("ix_ticket_resale_listings_listed_at"), table_name="ticket_resale_listings")
    op.drop_index(op.f("ix_ticket_resale_listings_event_id"), table_name="ticket_resale_listings")
    op.drop_index(op.f("ix_ticket_resale_listings_buyer_name"), table_name="ticket_resale_listings")
    op.drop_index(op.f("ix_ticket_resale_listings_buyer_email"), table_name="ticket_resale_listings")
    op.drop_table("ticket_resale_listings")

    op.drop_index(op.f("ix_ticket_seat_assignments_ticket_id"), table_name="ticket_seat_assignments")
    op.drop_index(op.f("ix_ticket_seat_assignments_section"), table_name="ticket_seat_assignments")
    op.drop_index(op.f("ix_ticket_seat_assignments_seat"), table_name="ticket_seat_assignments")
    op.drop_index(op.f("ix_ticket_seat_assignments_row"), table_name="ticket_seat_assignments")
    op.drop_index(op.f("ix_ticket_seat_assignments_organization_id"), table_name="ticket_seat_assignments")
    op.drop_index(op.f("ix_ticket_seat_assignments_event_id"), table_name="ticket_seat_assignments")
    op.drop_index(op.f("ix_ticket_seat_assignments_companion_seat"), table_name="ticket_seat_assignments")
    op.drop_index(op.f("ix_ticket_seat_assignments_assigned_at"), table_name="ticket_seat_assignments")
    op.drop_index(op.f("ix_ticket_seat_assignments_accessible"), table_name="ticket_seat_assignments")
    op.drop_index(op.f("ix_ticket_seat_assignments_access_zone"), table_name="ticket_seat_assignments")
    op.drop_table("ticket_seat_assignments")

    op.drop_index(op.f("ix_ticket_bundle_offers_ticket_product_id"), table_name="ticket_bundle_offers")
    op.drop_index(op.f("ix_ticket_bundle_offers_status"), table_name="ticket_bundle_offers")
    op.drop_index(op.f("ix_ticket_bundle_offers_starts_at"), table_name="ticket_bundle_offers")
    op.drop_index(op.f("ix_ticket_bundle_offers_package_type"), table_name="ticket_bundle_offers")
    op.drop_index(op.f("ix_ticket_bundle_offers_organization_id"), table_name="ticket_bundle_offers")
    op.drop_index(op.f("ix_ticket_bundle_offers_name"), table_name="ticket_bundle_offers")
    op.drop_index(op.f("ix_ticket_bundle_offers_merchandise_product_id"), table_name="ticket_bundle_offers")
    op.drop_index(op.f("ix_ticket_bundle_offers_event_id"), table_name="ticket_bundle_offers")
    op.drop_index(op.f("ix_ticket_bundle_offers_ends_at"), table_name="ticket_bundle_offers")
    op.drop_index(op.f("ix_ticket_bundle_offers_channel"), table_name="ticket_bundle_offers")
    op.drop_table("ticket_bundle_offers")
