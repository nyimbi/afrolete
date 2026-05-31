"""add insurance policy renewal reminders

Revision ID: a506b20260531
Revises: a505b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a506b20260531"
down_revision: str | Sequence[str] | None = "a505b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "insurance_policies",
        sa.Column("renewal_last_reminded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "insurance_policies",
        sa.Column("renewal_reminder_message_id", GUID(), nullable=True),
    )
    op.add_column(
        "insurance_policies",
        sa.Column("renewal_reminder_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_foreign_key(
        op.f("fk_insurance_policies_renewal_reminder_message_id_communication_messages"),
        "insurance_policies",
        "communication_messages",
        ["renewal_reminder_message_id"],
        ["id"],
    )
    for column in (
        "renewal_last_reminded_at",
        "renewal_reminder_message_id",
    ):
        op.create_index(op.f(f"ix_insurance_policies_{column}"), "insurance_policies", [column])
    op.alter_column("insurance_policies", "renewal_reminder_count", server_default=None)


def downgrade() -> None:
    for column in (
        "renewal_reminder_message_id",
        "renewal_last_reminded_at",
    ):
        op.drop_index(op.f(f"ix_insurance_policies_{column}"), table_name="insurance_policies")
    op.drop_constraint(
        op.f("fk_insurance_policies_renewal_reminder_message_id_communication_messages"),
        "insurance_policies",
        type_="foreignkey",
    )
    op.drop_column("insurance_policies", "renewal_reminder_count")
    op.drop_column("insurance_policies", "renewal_reminder_message_id")
    op.drop_column("insurance_policies", "renewal_last_reminded_at")
