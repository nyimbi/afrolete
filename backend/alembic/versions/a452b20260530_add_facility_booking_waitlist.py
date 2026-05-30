"""add facility booking waitlist

Revision ID: a452b20260530
Revises: a451b20260530
Create Date: 2026-05-30 16:15:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a452b20260530"
down_revision: str | None = "a451b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "facility_booking_waitlist_entries",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("offered_booking_id", app.models.base.GUID(), nullable=True),
        sa.Column("requester_name", sa.String(length=180), nullable=False),
        sa.Column("requester_email", sa.String(length=255), nullable=False),
        sa.Column("requester_phone", sa.String(length=80), nullable=True),
        sa.Column("activity_type", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("desired_starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("desired_ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_attendees", sa.Integer(), nullable=True),
        sa.Column("insurance_certificate_ref", sa.String(length=240), nullable=True),
        sa.Column("special_requirements", sa.Text(), nullable=True),
        sa.Column("add_ons", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_facility_booking_waitlist_entries_facility_id_facilities")),
        sa.ForeignKeyConstraint(["offered_booking_id"], ["facility_bookings.id"], name=op.f("fk_facility_booking_waitlist_entries_offered_booking_id_facility_bookings")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_facility_booking_waitlist_entries_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_booking_waitlist_entries")),
    )
    op.create_index(op.f("ix_facility_booking_waitlist_entries_activity_type"), "facility_booking_waitlist_entries", ["activity_type"])
    op.create_index(op.f("ix_facility_booking_waitlist_entries_desired_ends_at"), "facility_booking_waitlist_entries", ["desired_ends_at"])
    op.create_index(op.f("ix_facility_booking_waitlist_entries_desired_starts_at"), "facility_booking_waitlist_entries", ["desired_starts_at"])
    op.create_index(op.f("ix_facility_booking_waitlist_entries_expires_at"), "facility_booking_waitlist_entries", ["expires_at"])
    op.create_index(op.f("ix_facility_booking_waitlist_entries_facility_id"), "facility_booking_waitlist_entries", ["facility_id"])
    op.create_index(op.f("ix_facility_booking_waitlist_entries_notified_at"), "facility_booking_waitlist_entries", ["notified_at"])
    op.create_index(op.f("ix_facility_booking_waitlist_entries_offered_booking_id"), "facility_booking_waitlist_entries", ["offered_booking_id"])
    op.create_index(op.f("ix_facility_booking_waitlist_entries_organization_id"), "facility_booking_waitlist_entries", ["organization_id"])
    op.create_index(op.f("ix_facility_booking_waitlist_entries_priority_score"), "facility_booking_waitlist_entries", ["priority_score"])
    op.create_index(op.f("ix_facility_booking_waitlist_entries_requester_email"), "facility_booking_waitlist_entries", ["requester_email"])
    op.create_index(op.f("ix_facility_booking_waitlist_entries_requester_name"), "facility_booking_waitlist_entries", ["requester_name"])
    op.create_index(op.f("ix_facility_booking_waitlist_entries_status"), "facility_booking_waitlist_entries", ["status"])
    op.create_index(op.f("ix_facility_booking_waitlist_entries_title"), "facility_booking_waitlist_entries", ["title"])


def downgrade() -> None:
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_title"), table_name="facility_booking_waitlist_entries")
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_status"), table_name="facility_booking_waitlist_entries")
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_requester_name"), table_name="facility_booking_waitlist_entries")
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_requester_email"), table_name="facility_booking_waitlist_entries")
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_priority_score"), table_name="facility_booking_waitlist_entries")
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_organization_id"), table_name="facility_booking_waitlist_entries")
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_offered_booking_id"), table_name="facility_booking_waitlist_entries")
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_notified_at"), table_name="facility_booking_waitlist_entries")
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_facility_id"), table_name="facility_booking_waitlist_entries")
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_expires_at"), table_name="facility_booking_waitlist_entries")
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_desired_starts_at"), table_name="facility_booking_waitlist_entries")
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_desired_ends_at"), table_name="facility_booking_waitlist_entries")
    op.drop_index(op.f("ix_facility_booking_waitlist_entries_activity_type"), table_name="facility_booking_waitlist_entries")
    op.drop_table("facility_booking_waitlist_entries")
