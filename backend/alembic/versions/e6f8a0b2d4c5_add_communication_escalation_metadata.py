"""add communication escalation metadata

Revision ID: e6f8a0b2d4c5
Revises: d5f7a9c1e3f
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "e6f8a0b2d4c5"
down_revision: str | None = "d5f7a9c1e3f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("communication_messages", sa.Column("escalates_message_id", app.models.base.GUID(), nullable=True))
    op.add_column("communication_messages", sa.Column("escalation_level", sa.Integer(), server_default="0", nullable=False))
    op.add_column("communication_messages", sa.Column("escalation_triggered_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("communication_messages", sa.Column("escalation_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        op.f("fk_communication_messages_escalates_message_id_communication_messages"),
        "communication_messages",
        "communication_messages",
        ["escalates_message_id"],
        ["id"],
    )
    for column in ["escalates_message_id", "escalation_level", "escalation_triggered_at"]:
        op.create_index(
            op.f(f"ix_communication_messages_{column}"),
            "communication_messages",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in ["escalation_triggered_at", "escalation_level", "escalates_message_id"]:
        op.drop_index(op.f(f"ix_communication_messages_{column}"), table_name="communication_messages")
    op.drop_constraint(
        op.f("fk_communication_messages_escalates_message_id_communication_messages"),
        "communication_messages",
        type_="foreignkey",
    )
    op.drop_column("communication_messages", "escalation_reason")
    op.drop_column("communication_messages", "escalation_triggered_at")
    op.drop_column("communication_messages", "escalation_level")
    op.drop_column("communication_messages", "escalates_message_id")
