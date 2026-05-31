"""add coach education renewal reminders

Revision ID: a520b20260531
Revises: a519b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a520b20260531"
down_revision: str | Sequence[str] | None = "a519b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "coach_education_enrollments",
        sa.Column("renewal_last_reminded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "coach_education_enrollments",
        sa.Column("renewal_reminder_message_id", GUID(), nullable=True),
    )
    op.add_column(
        "coach_education_enrollments",
        sa.Column("renewal_reminder_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_foreign_key(
        op.f("fk_coach_education_enrollments_renewal_reminder_message_id_communication_messages"),
        "coach_education_enrollments",
        "communication_messages",
        ["renewal_reminder_message_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_coach_education_enrollments_renewal_last_reminded_at"),
        "coach_education_enrollments",
        ["renewal_last_reminded_at"],
    )
    op.create_index(
        op.f("ix_coach_education_enrollments_renewal_reminder_message_id"),
        "coach_education_enrollments",
        ["renewal_reminder_message_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_coach_education_enrollments_renewal_reminder_message_id"),
        table_name="coach_education_enrollments",
    )
    op.drop_index(
        op.f("ix_coach_education_enrollments_renewal_last_reminded_at"),
        table_name="coach_education_enrollments",
    )
    op.drop_constraint(
        op.f("fk_coach_education_enrollments_renewal_reminder_message_id_communication_messages"),
        "coach_education_enrollments",
        type_="foreignkey",
    )
    op.drop_column("coach_education_enrollments", "renewal_reminder_count")
    op.drop_column("coach_education_enrollments", "renewal_reminder_message_id")
    op.drop_column("coach_education_enrollments", "renewal_last_reminded_at")
