"""add clubhouse pos operations

Revision ID: a460b20260530
Revises: a459b20260530
Create Date: 2026-05-30 22:15:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a460b20260530"
down_revision: str | None = "a459b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clubhouse_menu_items",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("stock_quantity", sa.Integer(), nullable=True),
        sa.Column("reorder_point", sa.Integer(), nullable=False),
        sa.Column("nutrition_summary", sa.Text(), nullable=True),
        sa.Column("dietary_tags", sa.String(length=500), nullable=True),
        sa.Column("taxable", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_clubhouse_menu_items_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_menu_items_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_menu_items")),
    )
    for column in ["category", "dietary_tags", "facility_id", "name", "organization_id", "status", "taxable"]:
        op.create_index(op.f(f"ix_clubhouse_menu_items_{column}"), "clubhouse_menu_items", [column])

    op.create_table(
        "clubhouse_pos_orders",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("visit_id", app.models.base.GUID(), nullable=True),
        sa.Column("reservation_id", app.models.base.GUID(), nullable=True),
        sa.Column("person_id", app.models.base.GUID(), nullable=True),
        sa.Column("guest_name", sa.String(length=180), nullable=True),
        sa.Column("guest_email", sa.String(length=255), nullable=True),
        sa.Column("order_type", sa.String(length=40), nullable=False),
        sa.Column("table_label", sa.String(length=80), nullable=True),
        sa.Column("pickup_location", sa.String(length=180), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payment_method", sa.String(length=80), nullable=False),
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finance_invoice_id", app.models.base.GUID(), nullable=True),
        sa.Column("finance_payment_id", app.models.base.GUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_clubhouse_pos_orders_facility_id_facilities")),
        sa.ForeignKeyConstraint(["finance_invoice_id"], ["finance_invoices.id"], name=op.f("fk_clubhouse_pos_orders_finance_invoice_id_finance_invoices")),
        sa.ForeignKeyConstraint(["finance_payment_id"], ["finance_payments.id"], name=op.f("fk_clubhouse_pos_orders_finance_payment_id_finance_payments")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_pos_orders_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_clubhouse_pos_orders_person_id_persons")),
        sa.ForeignKeyConstraint(["reservation_id"], ["clubhouse_amenity_reservations.id"], name=op.f("fk_clubhouse_pos_orders_reservation_id_clubhouse_amenity_reservations")),
        sa.ForeignKeyConstraint(["visit_id"], ["clubhouse_visits.id"], name=op.f("fk_clubhouse_pos_orders_visit_id_clubhouse_visits")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_pos_orders")),
    )
    for column in [
        "facility_id",
        "finance_invoice_id",
        "finance_payment_id",
        "fulfilled_at",
        "guest_email",
        "guest_name",
        "order_type",
        "ordered_at",
        "organization_id",
        "paid_at",
        "payment_method",
        "person_id",
        "pickup_location",
        "reservation_id",
        "status",
        "table_label",
        "visit_id",
    ]:
        op.create_index(op.f(f"ix_clubhouse_pos_orders_{column}"), "clubhouse_pos_orders", [column])

    op.create_table(
        "clubhouse_pos_order_lines",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("order_id", app.models.base.GUID(), nullable=False),
        sa.Column("menu_item_id", app.models.base.GUID(), nullable=False),
        sa.Column("item_name", sa.String(length=180), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["menu_item_id"], ["clubhouse_menu_items.id"], name=op.f("fk_clubhouse_pos_order_lines_menu_item_id_clubhouse_menu_items")),
        sa.ForeignKeyConstraint(["order_id"], ["clubhouse_pos_orders.id"], name=op.f("fk_clubhouse_pos_order_lines_order_id_clubhouse_pos_orders")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_pos_order_lines_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_pos_order_lines")),
    )
    for column in ["menu_item_id", "order_id", "organization_id"]:
        op.create_index(op.f(f"ix_clubhouse_pos_order_lines_{column}"), "clubhouse_pos_order_lines", [column])


def downgrade() -> None:
    for column in ["organization_id", "order_id", "menu_item_id"]:
        op.drop_index(op.f(f"ix_clubhouse_pos_order_lines_{column}"), table_name="clubhouse_pos_order_lines")
    op.drop_table("clubhouse_pos_order_lines")

    for column in [
        "visit_id",
        "table_label",
        "status",
        "reservation_id",
        "pickup_location",
        "person_id",
        "payment_method",
        "paid_at",
        "organization_id",
        "ordered_at",
        "order_type",
        "guest_name",
        "guest_email",
        "fulfilled_at",
        "finance_payment_id",
        "finance_invoice_id",
        "facility_id",
    ]:
        op.drop_index(op.f(f"ix_clubhouse_pos_orders_{column}"), table_name="clubhouse_pos_orders")
    op.drop_table("clubhouse_pos_orders")

    for column in ["taxable", "status", "organization_id", "name", "facility_id", "dietary_tags", "category"]:
        op.drop_index(op.f(f"ix_clubhouse_menu_items_{column}"), table_name="clubhouse_menu_items")
    op.drop_table("clubhouse_menu_items")
