"""add incident medical clearances

Revision ID: 1a6fb90d2e4c
Revises: ff7a2c5e0d31
Create Date: 2026-05-28 03:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "1a6fb90d2e4c"
down_revision: str | None = "ff7a2c5e0d31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


clearance_status = sa.Enum(
    "pending_review",
    "restricted",
    "cleared",
    "not_cleared",
    "expired",
    name="medicalclearancestatus",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "incident_medical_clearances",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("incident_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_person_id", app.models.base.GUID(), nullable=False),
        sa.Column("reviewed_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("status", clearance_status, nullable=False, server_default="pending_review"),
        sa.Column("clearance_type", sa.String(length=120), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("restrictions", sa.Text(), nullable=True),
        sa.Column("return_to_play_stage", sa.String(length=120), nullable=True),
        sa.Column("provider_name", sa.String(length=240), nullable=True),
        sa.Column("documentation_object_key", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_person_id"],
            ["persons.id"],
            name=op.f("fk_incident_medical_clearances_athlete_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["safeguarding_incidents.id"],
            name=op.f("fk_incident_medical_clearances_incident_id_safeguarding_incidents"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_incident_medical_clearances_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_person_id"],
            ["persons.id"],
            name=op.f("fk_incident_medical_clearances_reviewed_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incident_medical_clearances")),
    )
    for column in [
        "assessed_at",
        "athlete_person_id",
        "clearance_type",
        "documentation_object_key",
        "incident_id",
        "organization_id",
        "return_to_play_stage",
        "reviewed_by_person_id",
        "status",
        "valid_from",
        "valid_until",
    ]:
        op.create_index(
            op.f(f"ix_incident_medical_clearances_{column}"),
            "incident_medical_clearances",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "valid_until",
        "valid_from",
        "status",
        "reviewed_by_person_id",
        "return_to_play_stage",
        "organization_id",
        "incident_id",
        "documentation_object_key",
        "clearance_type",
        "athlete_person_id",
        "assessed_at",
    ]:
        op.drop_index(op.f(f"ix_incident_medical_clearances_{column}"), table_name="incident_medical_clearances")
    op.drop_table("incident_medical_clearances")
