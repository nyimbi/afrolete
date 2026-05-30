"""add public facility hire fields

Revision ID: a451b20260530
Revises: a450b20260530
Create Date: 2026-05-30 15:30:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a451b20260530"
down_revision: str | None = "a450b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("facility_bookings", sa.Column("finance_invoice_id", app.models.base.GUID(), nullable=True))
    op.add_column(
        "facility_bookings",
        sa.Column("booking_source", sa.String(length=40), server_default="internal", nullable=False),
    )
    op.add_column("facility_bookings", sa.Column("public_booking_reference", sa.String(length=120), nullable=True))
    op.add_column(
        "facility_bookings",
        sa.Column("payment_status", sa.String(length=40), server_default="not_required", nullable=False),
    )
    op.add_column("facility_bookings", sa.Column("payment_checkout_url", sa.String(length=1000), nullable=True))
    op.add_column("facility_bookings", sa.Column("access_starts_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("facility_bookings", sa.Column("access_ends_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        op.f("fk_facility_bookings_finance_invoice_id_finance_invoices"),
        "facility_bookings",
        "finance_invoices",
        ["finance_invoice_id"],
        ["id"],
    )
    op.create_index(op.f("ix_facility_bookings_finance_invoice_id"), "facility_bookings", ["finance_invoice_id"])
    op.create_index(op.f("ix_facility_bookings_booking_source"), "facility_bookings", ["booking_source"])
    op.create_index(
        op.f("ix_facility_bookings_public_booking_reference"),
        "facility_bookings",
        ["public_booking_reference"],
    )
    op.create_index(op.f("ix_facility_bookings_payment_status"), "facility_bookings", ["payment_status"])
    op.create_index(op.f("ix_facility_bookings_access_starts_at"), "facility_bookings", ["access_starts_at"])
    op.create_index(op.f("ix_facility_bookings_access_ends_at"), "facility_bookings", ["access_ends_at"])
    op.alter_column("facility_bookings", "booking_source", server_default=None)
    op.alter_column("facility_bookings", "payment_status", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_facility_bookings_access_ends_at"), table_name="facility_bookings")
    op.drop_index(op.f("ix_facility_bookings_access_starts_at"), table_name="facility_bookings")
    op.drop_index(op.f("ix_facility_bookings_payment_status"), table_name="facility_bookings")
    op.drop_index(op.f("ix_facility_bookings_public_booking_reference"), table_name="facility_bookings")
    op.drop_index(op.f("ix_facility_bookings_booking_source"), table_name="facility_bookings")
    op.drop_index(op.f("ix_facility_bookings_finance_invoice_id"), table_name="facility_bookings")
    op.drop_constraint(
        op.f("fk_facility_bookings_finance_invoice_id_finance_invoices"),
        "facility_bookings",
        type_="foreignkey",
    )
    op.drop_column("facility_bookings", "access_ends_at")
    op.drop_column("facility_bookings", "access_starts_at")
    op.drop_column("facility_bookings", "payment_checkout_url")
    op.drop_column("facility_bookings", "payment_status")
    op.drop_column("facility_bookings", "public_booking_reference")
    op.drop_column("facility_bookings", "booking_source")
    op.drop_column("facility_bookings", "finance_invoice_id")
