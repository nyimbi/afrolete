"""add merchandise store

Revision ID: d2e3f4a5b6c7
Revises: d1e2f3a4b5c6
Create Date: 2026-05-30 01:15:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d2e3f4a5b6c7"
down_revision: str | None = "d1e2f3a4b5c6"
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
    name="commercial_status",
    native_enum=False,
    length=32,
)


def upgrade() -> None:
    op.create_table(
        "merchandise_products",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("team_id", app.models.base.GUID(), nullable=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("sku", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("inventory_count", sa.Integer(), nullable=False),
        sa.Column("reorder_point", sa.Integer(), nullable=False),
        sa.Column("personalization_enabled", sa.Boolean(), nullable=False),
        sa.Column("variants", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("status", commercial_status, nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_merchandise_products_organization_id_organizations")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_merchandise_products_team_id_teams")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_merchandise_products")),
        sa.UniqueConstraint("organization_id", "sku", name=op.f("uq_merchandise_products_organization_id")),
    )
    op.create_index(op.f("ix_merchandise_products_category"), "merchandise_products", ["category"])
    op.create_index(op.f("ix_merchandise_products_name"), "merchandise_products", ["name"])
    op.create_index(op.f("ix_merchandise_products_organization_id"), "merchandise_products", ["organization_id"])
    op.create_index(op.f("ix_merchandise_products_personalization_enabled"), "merchandise_products", ["personalization_enabled"])
    op.create_index(op.f("ix_merchandise_products_sku"), "merchandise_products", ["sku"])
    op.create_index(op.f("ix_merchandise_products_status"), "merchandise_products", ["status"])
    op.create_index(op.f("ix_merchandise_products_team_id"), "merchandise_products", ["team_id"])

    op.create_table(
        "merchandise_orders",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("buyer_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("buyer_name", sa.String(length=180), nullable=False),
        sa.Column("buyer_email", sa.String(length=320), nullable=False),
        sa.Column("delivery_method", sa.String(length=80), nullable=False),
        sa.Column("delivery_address", sa.Text(), nullable=True),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("external_payment_reference", sa.String(length=240), nullable=True),
        sa.Column("status", commercial_status, nullable=False),
        sa.Column("fulfillment_status", sa.String(length=40), nullable=False),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["buyer_person_id"], ["persons.id"], name=op.f("fk_merchandise_orders_buyer_person_id_persons")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_merchandise_orders_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_merchandise_orders")),
    )
    op.create_index(op.f("ix_merchandise_orders_buyer_email"), "merchandise_orders", ["buyer_email"])
    op.create_index(op.f("ix_merchandise_orders_buyer_person_id"), "merchandise_orders", ["buyer_person_id"])
    op.create_index(op.f("ix_merchandise_orders_delivery_method"), "merchandise_orders", ["delivery_method"])
    op.create_index(op.f("ix_merchandise_orders_external_payment_reference"), "merchandise_orders", ["external_payment_reference"])
    op.create_index(op.f("ix_merchandise_orders_fulfilled_at"), "merchandise_orders", ["fulfilled_at"])
    op.create_index(op.f("ix_merchandise_orders_fulfillment_status"), "merchandise_orders", ["fulfillment_status"])
    op.create_index(op.f("ix_merchandise_orders_organization_id"), "merchandise_orders", ["organization_id"])
    op.create_index(op.f("ix_merchandise_orders_status"), "merchandise_orders", ["status"])

    op.create_table(
        "merchandise_order_lines",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("merchandise_order_id", app.models.base.GUID(), nullable=False),
        sa.Column("merchandise_product_id", app.models.base.GUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("size", sa.String(length=40), nullable=True),
        sa.Column("color", sa.String(length=80), nullable=True),
        sa.Column("personalization_name", sa.String(length=120), nullable=True),
        sa.Column("personalization_number", sa.String(length=20), nullable=True),
        sa.Column("fulfillment_status", sa.String(length=40), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["merchandise_order_id"], ["merchandise_orders.id"], name=op.f("fk_merchandise_order_lines_merchandise_order_id_merchandise_orders")),
        sa.ForeignKeyConstraint(["merchandise_product_id"], ["merchandise_products.id"], name=op.f("fk_merchandise_order_lines_merchandise_product_id_merchandise_products")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_merchandise_order_lines_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_merchandise_order_lines")),
    )
    op.create_index(op.f("ix_merchandise_order_lines_color"), "merchandise_order_lines", ["color"])
    op.create_index(op.f("ix_merchandise_order_lines_fulfillment_status"), "merchandise_order_lines", ["fulfillment_status"])
    op.create_index(op.f("ix_merchandise_order_lines_merchandise_order_id"), "merchandise_order_lines", ["merchandise_order_id"])
    op.create_index(op.f("ix_merchandise_order_lines_merchandise_product_id"), "merchandise_order_lines", ["merchandise_product_id"])
    op.create_index(op.f("ix_merchandise_order_lines_organization_id"), "merchandise_order_lines", ["organization_id"])
    op.create_index(op.f("ix_merchandise_order_lines_size"), "merchandise_order_lines", ["size"])


def downgrade() -> None:
    op.drop_index(op.f("ix_merchandise_order_lines_size"), table_name="merchandise_order_lines")
    op.drop_index(op.f("ix_merchandise_order_lines_organization_id"), table_name="merchandise_order_lines")
    op.drop_index(op.f("ix_merchandise_order_lines_merchandise_product_id"), table_name="merchandise_order_lines")
    op.drop_index(op.f("ix_merchandise_order_lines_merchandise_order_id"), table_name="merchandise_order_lines")
    op.drop_index(op.f("ix_merchandise_order_lines_fulfillment_status"), table_name="merchandise_order_lines")
    op.drop_index(op.f("ix_merchandise_order_lines_color"), table_name="merchandise_order_lines")
    op.drop_table("merchandise_order_lines")

    op.drop_index(op.f("ix_merchandise_orders_status"), table_name="merchandise_orders")
    op.drop_index(op.f("ix_merchandise_orders_organization_id"), table_name="merchandise_orders")
    op.drop_index(op.f("ix_merchandise_orders_fulfillment_status"), table_name="merchandise_orders")
    op.drop_index(op.f("ix_merchandise_orders_fulfilled_at"), table_name="merchandise_orders")
    op.drop_index(op.f("ix_merchandise_orders_external_payment_reference"), table_name="merchandise_orders")
    op.drop_index(op.f("ix_merchandise_orders_delivery_method"), table_name="merchandise_orders")
    op.drop_index(op.f("ix_merchandise_orders_buyer_person_id"), table_name="merchandise_orders")
    op.drop_index(op.f("ix_merchandise_orders_buyer_email"), table_name="merchandise_orders")
    op.drop_table("merchandise_orders")

    op.drop_index(op.f("ix_merchandise_products_team_id"), table_name="merchandise_products")
    op.drop_index(op.f("ix_merchandise_products_status"), table_name="merchandise_products")
    op.drop_index(op.f("ix_merchandise_products_sku"), table_name="merchandise_products")
    op.drop_index(op.f("ix_merchandise_products_personalization_enabled"), table_name="merchandise_products")
    op.drop_index(op.f("ix_merchandise_products_organization_id"), table_name="merchandise_products")
    op.drop_index(op.f("ix_merchandise_products_name"), table_name="merchandise_products")
    op.drop_index(op.f("ix_merchandise_products_category"), table_name="merchandise_products")
    op.drop_table("merchandise_products")
