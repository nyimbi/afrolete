"""add member dues reminders

Revision ID: a507b20260531
Revises: a506b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a507b20260531"
down_revision: str | Sequence[str] | None = "a506b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "member_subscriptions",
        sa.Column("dues_last_reminded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "member_subscriptions",
        sa.Column("dues_reminder_message_id", GUID(), nullable=True),
    )
    op.add_column(
        "member_subscriptions",
        sa.Column("dues_reminder_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_foreign_key(
        op.f("fk_member_subscriptions_dues_reminder_message_id_communication_messages"),
        "member_subscriptions",
        "communication_messages",
        ["dues_reminder_message_id"],
        ["id"],
    )
    for column in ("dues_last_reminded_at", "dues_reminder_message_id"):
        op.create_index(op.f(f"ix_member_subscriptions_{column}"), "member_subscriptions", [column])
    op.alter_column("member_subscriptions", "dues_reminder_count", server_default=None)


def downgrade() -> None:
    for column in ("dues_reminder_message_id", "dues_last_reminded_at"):
        op.drop_index(op.f(f"ix_member_subscriptions_{column}"), table_name="member_subscriptions")
    op.drop_constraint(
        op.f("fk_member_subscriptions_dues_reminder_message_id_communication_messages"),
        "member_subscriptions",
        type_="foreignkey",
    )
    op.drop_column("member_subscriptions", "dues_reminder_count")
    op.drop_column("member_subscriptions", "dues_reminder_message_id")
    op.drop_column("member_subscriptions", "dues_last_reminded_at")
