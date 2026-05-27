"""add supplier orders

Revision ID: d16e2bc91c4a
Revises: 7b4c0a9e21d3
Create Date: 2026-05-27 19:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d16e2bc91c4a"
down_revision: str | None = "7b4c0a9e21d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "supplier_orders",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("equipment_item_id", app.models.base.GUID(), nullable=True),
        sa.Column("supplier_name", sa.String(length=180), nullable=False),
        sa.Column("item_name", sa.String(length=180), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("external_reference", sa.String(length=240), nullable=True),
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expected_delivery_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["equipment_item_id"],
            ["equipment_items.id"],
            name=op.f("fk_supplier_orders_equipment_item_id_equipment_items"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_supplier_orders_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_supplier_orders")),
    )
    op.create_index(op.f("ix_supplier_orders_equipment_item_id"), "supplier_orders", ["equipment_item_id"], unique=False)
    op.create_index(op.f("ix_supplier_orders_expected_delivery_at"), "supplier_orders", ["expected_delivery_at"], unique=False)
    op.create_index(op.f("ix_supplier_orders_external_reference"), "supplier_orders", ["external_reference"], unique=False)
    op.create_index(op.f("ix_supplier_orders_item_name"), "supplier_orders", ["item_name"], unique=False)
    op.create_index(op.f("ix_supplier_orders_ordered_at"), "supplier_orders", ["ordered_at"], unique=False)
    op.create_index(op.f("ix_supplier_orders_organization_id"), "supplier_orders", ["organization_id"], unique=False)
    op.create_index(op.f("ix_supplier_orders_received_at"), "supplier_orders", ["received_at"], unique=False)
    op.create_index(op.f("ix_supplier_orders_status"), "supplier_orders", ["status"], unique=False)
    op.create_index(op.f("ix_supplier_orders_supplier_name"), "supplier_orders", ["supplier_name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_supplier_orders_supplier_name"), table_name="supplier_orders")
    op.drop_index(op.f("ix_supplier_orders_status"), table_name="supplier_orders")
    op.drop_index(op.f("ix_supplier_orders_received_at"), table_name="supplier_orders")
    op.drop_index(op.f("ix_supplier_orders_organization_id"), table_name="supplier_orders")
    op.drop_index(op.f("ix_supplier_orders_ordered_at"), table_name="supplier_orders")
    op.drop_index(op.f("ix_supplier_orders_item_name"), table_name="supplier_orders")
    op.drop_index(op.f("ix_supplier_orders_external_reference"), table_name="supplier_orders")
    op.drop_index(op.f("ix_supplier_orders_expected_delivery_at"), table_name="supplier_orders")
    op.drop_index(op.f("ix_supplier_orders_equipment_item_id"), table_name="supplier_orders")
    op.drop_table("supplier_orders")
