"""add facility booking rules

Revision ID: a450b20260530
Revises: a449b20260530
Create Date: 2026-05-30 14:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a450b20260530"
down_revision: str | None = "a449b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "facility_booking_rules",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("min_booking_minutes", sa.Integer(), nullable=False),
        sa.Column("max_booking_minutes", sa.Integer(), nullable=False),
        sa.Column("buffer_minutes", sa.Integer(), nullable=False),
        sa.Column("advance_booking_days", sa.Integer(), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), nullable=False),
        sa.Column("allow_public_booking", sa.Boolean(), nullable=False),
        sa.Column("cancellation_notice_hours", sa.Integer(), nullable=False),
        sa.Column("peak_hour_rate_multiplier", sa.Numeric(5, 2), nullable=True),
        sa.Column("public_booking_note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["facility_id"],
            ["facilities.id"],
            name=op.f("fk_facility_booking_rules_facility_id_facilities"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_facility_booking_rules_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_booking_rules")),
        sa.UniqueConstraint("organization_id", "facility_id", name="uq_facility_booking_rules_facility"),
    )
    op.create_index(op.f("ix_facility_booking_rules_allow_public_booking"), "facility_booking_rules", ["allow_public_booking"])
    op.create_index(op.f("ix_facility_booking_rules_facility_id"), "facility_booking_rules", ["facility_id"])
    op.create_index(op.f("ix_facility_booking_rules_organization_id"), "facility_booking_rules", ["organization_id"])
    op.create_index(op.f("ix_facility_booking_rules_requires_approval"), "facility_booking_rules", ["requires_approval"])
    op.create_index(op.f("ix_facility_booking_rules_status"), "facility_booking_rules", ["status"])

    op.add_column("facility_bookings", sa.Column("recurrence_group_id", sa.String(length=120), nullable=True))
    op.add_column("facility_bookings", sa.Column("occurrence_index", sa.Integer(), nullable=True))
    op.add_column(
        "facility_bookings",
        sa.Column("public_visible", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("facility_bookings", sa.Column("conflict_note", sa.Text(), nullable=True))
    op.create_index(op.f("ix_facility_bookings_recurrence_group_id"), "facility_bookings", ["recurrence_group_id"])
    op.create_index(op.f("ix_facility_bookings_public_visible"), "facility_bookings", ["public_visible"])
    op.alter_column("facility_bookings", "public_visible", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_facility_bookings_public_visible"), table_name="facility_bookings")
    op.drop_index(op.f("ix_facility_bookings_recurrence_group_id"), table_name="facility_bookings")
    op.drop_column("facility_bookings", "conflict_note")
    op.drop_column("facility_bookings", "public_visible")
    op.drop_column("facility_bookings", "occurrence_index")
    op.drop_column("facility_bookings", "recurrence_group_id")

    op.drop_index(op.f("ix_facility_booking_rules_status"), table_name="facility_booking_rules")
    op.drop_index(op.f("ix_facility_booking_rules_requires_approval"), table_name="facility_booking_rules")
    op.drop_index(op.f("ix_facility_booking_rules_organization_id"), table_name="facility_booking_rules")
    op.drop_index(op.f("ix_facility_booking_rules_facility_id"), table_name="facility_booking_rules")
    op.drop_index(op.f("ix_facility_booking_rules_allow_public_booking"), table_name="facility_booking_rules")
    op.drop_table("facility_booking_rules")
