"""add registration guardian contact

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-05-29 23:55:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d0e1f2a3b4c5"
down_revision: str | None = "c9d0e1f2a3b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "registration_inquiries",
        sa.Column("guardian_person_id", app.models.base.GUID(), nullable=True),
    )
    op.add_column(
        "registration_inquiries",
        sa.Column(
            "guardian_contact_status",
            sa.String(length=40),
            server_default="pending_account",
            nullable=False,
        ),
    )
    op.create_foreign_key(
        op.f("fk_registration_inquiries_guardian_person_id_persons"),
        "registration_inquiries",
        "persons",
        ["guardian_person_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_registration_inquiries_guardian_contact_status"),
        "registration_inquiries",
        ["guardian_contact_status"],
    )
    op.create_index(
        op.f("ix_registration_inquiries_guardian_person_id"),
        "registration_inquiries",
        ["guardian_person_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_registration_inquiries_guardian_person_id"), table_name="registration_inquiries")
    op.drop_index(op.f("ix_registration_inquiries_guardian_contact_status"), table_name="registration_inquiries")
    op.drop_constraint(
        op.f("fk_registration_inquiries_guardian_person_id_persons"),
        "registration_inquiries",
        type_="foreignkey",
    )
    op.drop_column("registration_inquiries", "guardian_contact_status")
    op.drop_column("registration_inquiries", "guardian_person_id")
