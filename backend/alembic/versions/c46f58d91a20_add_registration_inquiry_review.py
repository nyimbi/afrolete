"""add registration inquiry review

Revision ID: c46f58d91a20
Revises: f2d4c6a8b901
Create Date: 2026-05-27 23:35:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "c46f58d91a20"
down_revision: str | None = "f2d4c6a8b901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("registration_inquiries", sa.Column("review_notes", sa.Text(), nullable=True))
    op.add_column(
        "registration_inquiries",
        sa.Column("follow_up_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "registration_inquiries",
        sa.Column("reviewed_by_person_id", app.models.base.GUID(), nullable=True),
    )
    op.add_column(
        "registration_inquiries",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_registration_inquiries_reviewed_by_person_id_persons"),
        "registration_inquiries",
        "persons",
        ["reviewed_by_person_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_registration_inquiries_follow_up_at"),
        "registration_inquiries",
        ["follow_up_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_registration_inquiries_reviewed_by_person_id"),
        "registration_inquiries",
        ["reviewed_by_person_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_registration_inquiries_reviewed_by_person_id"), table_name="registration_inquiries")
    op.drop_index(op.f("ix_registration_inquiries_follow_up_at"), table_name="registration_inquiries")
    op.drop_constraint(
        op.f("fk_registration_inquiries_reviewed_by_person_id_persons"),
        "registration_inquiries",
        type_="foreignkey",
    )
    op.drop_column("registration_inquiries", "reviewed_at")
    op.drop_column("registration_inquiries", "reviewed_by_person_id")
    op.drop_column("registration_inquiries", "follow_up_at")
    op.drop_column("registration_inquiries", "review_notes")
