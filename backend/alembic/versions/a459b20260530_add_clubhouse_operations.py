"""add clubhouse operations

Revision ID: a459b20260530
Revises: a458b20260530
Create Date: 2026-05-30 21:30:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a459b20260530"
down_revision: str | None = "a458b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clubhouse_amenities",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("amenity_type", sa.String(length=80), nullable=False),
        sa.Column("location", sa.String(length=240), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("reservation_required", sa.Boolean(), nullable=False),
        sa.Column("hourly_rate", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_clubhouse_amenities_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_amenities_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_amenities")),
    )
    for column in ["amenity_type", "facility_id", "location", "name", "organization_id", "reservation_required", "status"]:
        op.create_index(op.f(f"ix_clubhouse_amenities_{column}"), "clubhouse_amenities", [column])

    op.create_table(
        "clubhouse_visits",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=True),
        sa.Column("access_event_id", app.models.base.GUID(), nullable=True),
        sa.Column("guest_name", sa.String(length=180), nullable=True),
        sa.Column("guest_email", sa.String(length=255), nullable=True),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("party_size", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=180), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["access_event_id"], ["facility_access_events.id"], name=op.f("fk_clubhouse_visits_access_event_id_facility_access_events")),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_clubhouse_visits_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_visits_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_clubhouse_visits_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_visits")),
    )
    for column in [
        "access_event_id",
        "check_in_at",
        "check_out_at",
        "facility_id",
        "guest_email",
        "guest_name",
        "organization_id",
        "person_id",
        "purpose",
        "status",
    ]:
        op.create_index(op.f(f"ix_clubhouse_visits_{column}"), "clubhouse_visits", [column])

    op.create_table(
        "clubhouse_amenity_reservations",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("amenity_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=True),
        sa.Column("guest_name", sa.String(length=180), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("party_size", sa.Integer(), nullable=False),
        sa.Column("expected_fee", sa.Numeric(12, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["amenity_id"], ["clubhouse_amenities.id"], name=op.f("fk_clubhouse_amenity_reservations_amenity_id_clubhouse_amenities")),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_clubhouse_amenity_reservations_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_clubhouse_amenity_reservations_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_clubhouse_amenity_reservations_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubhouse_amenity_reservations")),
    )
    for column in ["amenity_id", "ends_at", "facility_id", "guest_name", "organization_id", "person_id", "starts_at", "status"]:
        op.create_index(
            op.f(f"ix_clubhouse_amenity_reservations_{column}"),
            "clubhouse_amenity_reservations",
            [column],
        )


def downgrade() -> None:
    for column in ["status", "starts_at", "person_id", "organization_id", "guest_name", "facility_id", "ends_at", "amenity_id"]:
        op.drop_index(
            op.f(f"ix_clubhouse_amenity_reservations_{column}"),
            table_name="clubhouse_amenity_reservations",
        )
    op.drop_table("clubhouse_amenity_reservations")
    for column in [
        "status",
        "purpose",
        "person_id",
        "organization_id",
        "guest_name",
        "guest_email",
        "facility_id",
        "check_out_at",
        "check_in_at",
        "access_event_id",
    ]:
        op.drop_index(op.f(f"ix_clubhouse_visits_{column}"), table_name="clubhouse_visits")
    op.drop_table("clubhouse_visits")
    for column in ["status", "reservation_required", "organization_id", "name", "location", "facility_id", "amenity_type"]:
        op.drop_index(op.f(f"ix_clubhouse_amenities_{column}"), table_name="clubhouse_amenities")
    op.drop_table("clubhouse_amenities")
