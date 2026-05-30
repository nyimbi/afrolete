"""add clubhouse operations checklists

Revision ID: a461b20260530
Revises: a460b20260530
Create Date: 2026-05-30 22:55:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a461b20260530"
down_revision: str | None = "a460b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clubhouse_operations_checklists",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("checklist_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("assigned_to_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to_person_id"], ["persons.id"], name=op.f("fk_clubhouse_operations_checklists_assigned_to_person_id_persons")),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_clubhouse_operations_checklists_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_operations_checklists_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_operations_checklists")),
    )
    for column in [
        "assigned_to_person_id",
        "checklist_type",
        "completed_at",
        "facility_id",
        "organization_id",
        "scheduled_for",
        "status",
        "title",
    ]:
        op.create_index(op.f(f"ix_clubhouse_operations_checklists_{column}"), "clubhouse_operations_checklists", [column])

    op.create_table(
        "clubhouse_operations_checklist_items",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("checklist_id", app.models.base.GUID(), nullable=False),
        sa.Column("label", sa.String(length=240), nullable=False),
        sa.Column("area", sa.String(length=120), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("priority", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_to_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("work_order_id", app.models.base.GUID(), nullable=True),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to_person_id"], ["persons.id"], name=op.f("fk_clubhouse_operations_checklist_items_assigned_to_person_id_persons")),
        sa.ForeignKeyConstraint(["checklist_id"], ["clubhouse_operations_checklists.id"], name=op.f("fk_clubhouse_operations_checklist_items_checklist_id_clubhouse_operations_checklists")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_operations_checklist_items_organization_id_organizations")),
        sa.ForeignKeyConstraint(["work_order_id"], ["maintenance_work_orders.id"], name=op.f("fk_clubhouse_operations_checklist_items_work_order_id_maintenance_work_orders")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_operations_checklist_items")),
    )
    for column in [
        "area",
        "assigned_to_person_id",
        "category",
        "checklist_id",
        "completed_at",
        "due_at",
        "label",
        "organization_id",
        "priority",
        "status",
        "work_order_id",
    ]:
        op.create_index(
            op.f(f"ix_clubhouse_operations_checklist_items_{column}"),
            "clubhouse_operations_checklist_items",
            [column],
        )

    op.create_table(
        "clubhouse_events",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("amenity_id", app.models.base.GUID(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_attendees", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("budget_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("revenue_target", sa.Numeric(12, 2), nullable=True),
        sa.Column("actual_revenue", sa.Numeric(12, 2), nullable=False),
        sa.Column("vendor_notes", sa.Text(), nullable=True),
        sa.Column("catering_notes", sa.Text(), nullable=True),
        sa.Column("staffing_notes", sa.Text(), nullable=True),
        sa.Column("run_sheet", sa.Text(), nullable=True),
        sa.Column("post_event_summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["amenity_id"], ["clubhouse_amenities.id"], name=op.f("fk_clubhouse_events_amenity_id_clubhouse_amenities")),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_clubhouse_events_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_events_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_events")),
    )
    for column in ["amenity_id", "event_type", "facility_id", "organization_id", "starts_at", "status", "title"]:
        op.create_index(op.f(f"ix_clubhouse_events_{column}"), "clubhouse_events", [column])

    op.create_table(
        "clubhouse_event_guests",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("clubhouse_event_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=True),
        sa.Column("guest_name", sa.String(length=180), nullable=False),
        sa.Column("guest_email", sa.String(length=255), nullable=True),
        sa.Column("party_size", sa.Integer(), nullable=False),
        sa.Column("rsvp_status", sa.String(length=40), nullable=False),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clubhouse_event_id"], ["clubhouse_events.id"], name=op.f("fk_clubhouse_event_guests_clubhouse_event_id_clubhouse_events")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_event_guests_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_clubhouse_event_guests_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_event_guests")),
    )
    for column in ["checked_in_at", "clubhouse_event_id", "guest_email", "guest_name", "organization_id", "person_id", "rsvp_status"]:
        op.create_index(op.f(f"ix_clubhouse_event_guests_{column}"), "clubhouse_event_guests", [column])

    op.create_table(
        "clubhouse_service_offerings",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("service_type", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("billing_period", sa.String(length=40), nullable=False),
        sa.Column("capacity_per_slot", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_clubhouse_service_offerings_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_service_offerings_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_service_offerings")),
    )
    for column in ["billing_period", "facility_id", "name", "organization_id", "service_type", "status"]:
        op.create_index(op.f(f"ix_clubhouse_service_offerings_{column}"), "clubhouse_service_offerings", [column])

    op.create_table(
        "clubhouse_service_bookings",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("service_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=True),
        sa.Column("guest_name", sa.String(length=180), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("finance_invoice_id", app.models.base.GUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_clubhouse_service_bookings_facility_id_facilities")),
        sa.ForeignKeyConstraint(["finance_invoice_id"], ["finance_invoices.id"], name=op.f("fk_clubhouse_service_bookings_finance_invoice_id_finance_invoices")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_service_bookings_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_clubhouse_service_bookings_person_id_persons")),
        sa.ForeignKeyConstraint(["service_id"], ["clubhouse_service_offerings.id"], name=op.f("fk_clubhouse_service_bookings_service_id_clubhouse_service_offerings")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_service_bookings")),
    )
    for column in ["ends_at", "facility_id", "finance_invoice_id", "guest_name", "organization_id", "person_id", "service_id", "starts_at", "status"]:
        op.create_index(op.f(f"ix_clubhouse_service_bookings_{column}"), "clubhouse_service_bookings", [column])

    op.create_table(
        "clubhouse_feedback",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("amenity_id", app.models.base.GUID(), nullable=True),
        sa.Column("person_id", app.models.base.GUID(), nullable=True),
        sa.Column("guest_name", sa.String(length=180), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(length=220), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["amenity_id"], ["clubhouse_amenities.id"], name=op.f("fk_clubhouse_feedback_amenity_id_clubhouse_amenities")),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_clubhouse_feedback_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_feedback_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_clubhouse_feedback_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_feedback")),
    )
    for column in ["amenity_id", "category", "facility_id", "guest_name", "organization_id", "person_id", "rating", "resolved_at", "status", "subject", "submitted_at"]:
        op.create_index(op.f(f"ix_clubhouse_feedback_{column}"), "clubhouse_feedback", [column])


def downgrade() -> None:
    for column in ["submitted_at", "subject", "status", "resolved_at", "rating", "person_id", "organization_id", "guest_name", "facility_id", "category", "amenity_id"]:
        op.drop_index(op.f(f"ix_clubhouse_feedback_{column}"), table_name="clubhouse_feedback")
    op.drop_table("clubhouse_feedback")

    for column in ["status", "starts_at", "service_id", "person_id", "organization_id", "guest_name", "finance_invoice_id", "facility_id", "ends_at"]:
        op.drop_index(op.f(f"ix_clubhouse_service_bookings_{column}"), table_name="clubhouse_service_bookings")
    op.drop_table("clubhouse_service_bookings")

    for column in ["status", "service_type", "organization_id", "name", "facility_id", "billing_period"]:
        op.drop_index(op.f(f"ix_clubhouse_service_offerings_{column}"), table_name="clubhouse_service_offerings")
    op.drop_table("clubhouse_service_offerings")

    for column in ["rsvp_status", "person_id", "organization_id", "guest_name", "guest_email", "clubhouse_event_id", "checked_in_at"]:
        op.drop_index(op.f(f"ix_clubhouse_event_guests_{column}"), table_name="clubhouse_event_guests")
    op.drop_table("clubhouse_event_guests")

    for column in ["title", "status", "starts_at", "organization_id", "facility_id", "event_type", "amenity_id"]:
        op.drop_index(op.f(f"ix_clubhouse_events_{column}"), table_name="clubhouse_events")
    op.drop_table("clubhouse_events")

    for column in [
        "work_order_id",
        "status",
        "priority",
        "organization_id",
        "label",
        "due_at",
        "completed_at",
        "checklist_id",
        "category",
        "assigned_to_person_id",
        "area",
    ]:
        op.drop_index(
            op.f(f"ix_clubhouse_operations_checklist_items_{column}"),
            table_name="clubhouse_operations_checklist_items",
        )
    op.drop_table("clubhouse_operations_checklist_items")

    for column in [
        "title",
        "status",
        "scheduled_for",
        "organization_id",
        "facility_id",
        "completed_at",
        "checklist_type",
        "assigned_to_person_id",
    ]:
        op.drop_index(op.f(f"ix_clubhouse_operations_checklists_{column}"), table_name="clubhouse_operations_checklists")
    op.drop_table("clubhouse_operations_checklists")
