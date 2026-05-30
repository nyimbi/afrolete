"""add facility access control

Revision ID: a455b20260530
Revises: a454b20260530
Create Date: 2026-05-30 18:15:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a455b20260530"
down_revision: str | None = "a454b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "facility_access_credentials",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("booking_id", app.models.base.GUID(), nullable=True),
        sa.Column("lease_agreement_id", app.models.base.GUID(), nullable=True),
        sa.Column("person_id", app.models.base.GUID(), nullable=True),
        sa.Column("guest_name", sa.String(length=180), nullable=True),
        sa.Column("guest_email", sa.String(length=255), nullable=True),
        sa.Column("credential_type", sa.String(length=40), nullable=False),
        sa.Column("access_code", sa.String(length=120), nullable=False),
        sa.Column("access_level", sa.String(length=80), nullable=False),
        sa.Column("zones", sa.Text(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("uses_count", sa.Integer(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["facility_bookings.id"], name=op.f("fk_facility_access_credentials_booking_id_facility_bookings")),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_facility_access_credentials_facility_id_facilities")),
        sa.ForeignKeyConstraint(["issued_by_person_id"], ["persons.id"], name=op.f("fk_facility_access_credentials_issued_by_person_id_persons")),
        sa.ForeignKeyConstraint(["lease_agreement_id"], ["facility_lease_agreements.id"], name=op.f("fk_facility_access_credentials_lease_agreement_id_facility_lease_agreements")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_facility_access_credentials_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_facility_access_credentials_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_access_credentials")),
    )
    for column in [
        "access_code",
        "access_level",
        "booking_id",
        "credential_type",
        "facility_id",
        "guest_email",
        "guest_name",
        "issued_by_person_id",
        "last_used_at",
        "lease_agreement_id",
        "organization_id",
        "person_id",
        "status",
        "valid_from",
        "valid_until",
    ]:
        op.create_index(op.f(f"ix_facility_access_credentials_{column}"), "facility_access_credentials", [column])

    op.create_table(
        "facility_access_events",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("credential_id", app.models.base.GUID(), nullable=True),
        sa.Column("booking_id", app.models.base.GUID(), nullable=True),
        sa.Column("lease_agreement_id", app.models.base.GUID(), nullable=True),
        sa.Column("access_code", sa.String(length=120), nullable=True),
        sa.Column("reader_id", sa.String(length=160), nullable=False),
        sa.Column("reader_location", sa.String(length=240), nullable=True),
        sa.Column("subject_summary", sa.String(length=240), nullable=True),
        sa.Column("decision", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["facility_bookings.id"], name=op.f("fk_facility_access_events_booking_id_facility_bookings")),
        sa.ForeignKeyConstraint(["credential_id"], ["facility_access_credentials.id"], name=op.f("fk_facility_access_events_credential_id_facility_access_credentials")),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_facility_access_events_facility_id_facilities")),
        sa.ForeignKeyConstraint(["lease_agreement_id"], ["facility_lease_agreements.id"], name=op.f("fk_facility_access_events_lease_agreement_id_facility_lease_agreements")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_facility_access_events_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_access_events")),
    )
    for column in [
        "access_code",
        "booking_id",
        "credential_id",
        "decision",
        "facility_id",
        "lease_agreement_id",
        "occurred_at",
        "organization_id",
        "reader_id",
        "reader_location",
    ]:
        op.create_index(op.f(f"ix_facility_access_events_{column}"), "facility_access_events", [column])


def downgrade() -> None:
    for column in [
        "reader_location",
        "reader_id",
        "organization_id",
        "occurred_at",
        "lease_agreement_id",
        "facility_id",
        "decision",
        "credential_id",
        "booking_id",
        "access_code",
    ]:
        op.drop_index(op.f(f"ix_facility_access_events_{column}"), table_name="facility_access_events")
    op.drop_table("facility_access_events")
    for column in [
        "valid_until",
        "valid_from",
        "status",
        "person_id",
        "organization_id",
        "lease_agreement_id",
        "last_used_at",
        "issued_by_person_id",
        "guest_name",
        "guest_email",
        "facility_id",
        "credential_type",
        "booking_id",
        "access_level",
        "access_code",
    ]:
        op.drop_index(op.f(f"ix_facility_access_credentials_{column}"), table_name="facility_access_credentials")
    op.drop_table("facility_access_credentials")
