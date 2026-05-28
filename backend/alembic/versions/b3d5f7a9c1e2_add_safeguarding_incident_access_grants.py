"""add safeguarding incident access grants

Revision ID: b3d5f7a9c1e2
Revises: a2c4e6f8b0d1
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "b3d5f7a9c1e2"
down_revision: str | None = "a2c4e6f8b0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "safeguarding_incident_access_grants",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("incident_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=False),
        sa.Column("relation", sa.String(length=80), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("granted_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("revoked_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("granted_reason", sa.Text(), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["granted_by_person_id"],
            ["persons.id"],
            name=op.f("fk_safeguarding_incident_access_grants_granted_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["safeguarding_incidents.id"],
            name=op.f("fk_safeguarding_incident_access_grants_incident_id_safeguarding_incidents"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_safeguarding_incident_access_grants_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["persons.id"],
            name=op.f("fk_safeguarding_incident_access_grants_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["revoked_by_person_id"],
            ["persons.id"],
            name=op.f("fk_safeguarding_incident_access_grants_revoked_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_safeguarding_incident_access_grants")),
    )
    for column in [
        "active",
        "granted_by_person_id",
        "incident_id",
        "organization_id",
        "person_id",
        "relation",
        "revoked_at",
        "revoked_by_person_id",
    ]:
        op.create_index(
            op.f(f"ix_safeguarding_incident_access_grants_{column}"),
            "safeguarding_incident_access_grants",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "revoked_by_person_id",
        "revoked_at",
        "relation",
        "person_id",
        "organization_id",
        "incident_id",
        "granted_by_person_id",
        "active",
    ]:
        op.drop_index(
            op.f(f"ix_safeguarding_incident_access_grants_{column}"),
            table_name="safeguarding_incident_access_grants",
        )
    op.drop_table("safeguarding_incident_access_grants")
