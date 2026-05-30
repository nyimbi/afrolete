"""add facility access lockdowns

Revision ID: a458b20260530
Revises: a457b20260530
Create Date: 2026-05-30 20:45:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a458b20260530"
down_revision: str | None = "a457b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "facility_access_lockdowns",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("mode", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("command_count", sa.Integer(), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_facility_access_lockdowns_facility_id_facilities")),
        sa.ForeignKeyConstraint(["issued_by_person_id"], ["persons.id"], name=op.f("fk_facility_access_lockdowns_issued_by_person_id_persons")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_facility_access_lockdowns_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_access_lockdowns")),
    )
    for column in [
        "activated_at",
        "facility_id",
        "issued_by_person_id",
        "mode",
        "organization_id",
        "resolved_at",
        "status",
    ]:
        op.create_index(op.f(f"ix_facility_access_lockdowns_{column}"), "facility_access_lockdowns", [column])


def downgrade() -> None:
    for column in [
        "status",
        "resolved_at",
        "organization_id",
        "mode",
        "issued_by_person_id",
        "facility_id",
        "activated_at",
    ]:
        op.drop_index(op.f(f"ix_facility_access_lockdowns_{column}"), table_name="facility_access_lockdowns")
    op.drop_table("facility_access_lockdowns")
