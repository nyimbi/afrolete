"""add credential renewal reminders

Revision ID: a518b20260531
Revises: a517b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a518b20260531"
down_revision: str | Sequence[str] | None = "a517b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "compliance_credentials",
        sa.Column("renewal_last_reminded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "compliance_credentials",
        sa.Column("renewal_reminder_message_id", GUID(), nullable=True),
    )
    op.add_column(
        "compliance_credentials",
        sa.Column("renewal_reminder_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_foreign_key(
        op.f("fk_compliance_credentials_renewal_reminder_message_id_communication_messages"),
        "compliance_credentials",
        "communication_messages",
        ["renewal_reminder_message_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_compliance_credentials_renewal_last_reminded_at"),
        "compliance_credentials",
        ["renewal_last_reminded_at"],
    )
    op.create_index(
        op.f("ix_compliance_credentials_renewal_reminder_message_id"),
        "compliance_credentials",
        ["renewal_reminder_message_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_compliance_credentials_renewal_reminder_message_id"), table_name="compliance_credentials")
    op.drop_index(op.f("ix_compliance_credentials_renewal_last_reminded_at"), table_name="compliance_credentials")
    op.drop_constraint(
        op.f("fk_compliance_credentials_renewal_reminder_message_id_communication_messages"),
        "compliance_credentials",
        type_="foreignkey",
    )
    op.drop_column("compliance_credentials", "renewal_reminder_count")
    op.drop_column("compliance_credentials", "renewal_reminder_message_id")
    op.drop_column("compliance_credentials", "renewal_last_reminded_at")
