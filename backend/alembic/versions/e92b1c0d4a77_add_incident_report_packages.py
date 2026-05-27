"""add incident report packages

Revision ID: e92b1c0d4a77
Revises: d38a49e6812b
Create Date: 2026-05-28 02:05:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "e92b1c0d4a77"
down_revision: str | None = "d38a49e6812b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


report_package_status = sa.Enum(
    "draft",
    "ready",
    "submitted",
    "accepted",
    "rejected",
    "withdrawn",
    name="incidentreportpackagestatus",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "incident_report_packages",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("incident_id", app.models.base.GUID(), nullable=False),
        sa.Column("prepared_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("submitted_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("agency_name", sa.String(length=240), nullable=False),
        sa.Column("jurisdiction", sa.String(length=160), nullable=False),
        sa.Column("status", report_package_status, nullable=False, server_default="draft"),
        sa.Column("due_at", sa.Date(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_reference", sa.String(length=240), nullable=True),
        sa.Column("narrative", sa.Text(), nullable=False),
        sa.Column("checklist_json", sa.Text(), nullable=True),
        sa.Column("submission_payload", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["safeguarding_incidents.id"],
            name=op.f("fk_incident_report_packages_incident_id_safeguarding_incidents"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_incident_report_packages_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["prepared_by_person_id"],
            ["persons.id"],
            name=op.f("fk_incident_report_packages_prepared_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["submitted_by_person_id"],
            ["persons.id"],
            name=op.f("fk_incident_report_packages_submitted_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incident_report_packages")),
    )
    for column in [
        "accepted_at",
        "agency_name",
        "due_at",
        "external_reference",
        "incident_id",
        "jurisdiction",
        "organization_id",
        "prepared_by_person_id",
        "status",
        "submitted_at",
        "submitted_by_person_id",
    ]:
        op.create_index(
            op.f(f"ix_incident_report_packages_{column}"),
            "incident_report_packages",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "submitted_by_person_id",
        "submitted_at",
        "status",
        "prepared_by_person_id",
        "organization_id",
        "jurisdiction",
        "incident_id",
        "external_reference",
        "due_at",
        "agency_name",
        "accepted_at",
    ]:
        op.drop_index(op.f(f"ix_incident_report_packages_{column}"), table_name="incident_report_packages")
    op.drop_table("incident_report_packages")
