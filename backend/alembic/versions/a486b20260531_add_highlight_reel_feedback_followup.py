"""add highlight reel feedback followup

Revision ID: a486b20260531
Revises: a485b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.models.base import GUID


revision: str = "a486b20260531"
down_revision: str | None = "a485b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "performance_highlight_reel_feedback",
        sa.Column("coach_followup_message_id", GUID(), nullable=True),
    )
    op.add_column(
        "performance_highlight_reel_feedback",
        sa.Column("coach_followup_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "performance_highlight_reel_feedback",
        sa.Column("coach_followup_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_performance_highlight_reel_feedback_coach_followup_message_id_communication_messages"),
        "performance_highlight_reel_feedback",
        "communication_messages",
        ["coach_followup_message_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_performance_highlight_reel_feedback_coach_followup_message_id"),
        "performance_highlight_reel_feedback",
        ["coach_followup_message_id"],
    )
    op.create_index(
        op.f("ix_performance_highlight_reel_feedback_coach_followup_sent_at"),
        "performance_highlight_reel_feedback",
        ["coach_followup_sent_at"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_performance_highlight_reel_feedback_coach_followup_sent_at"),
        table_name="performance_highlight_reel_feedback",
    )
    op.drop_index(
        op.f("ix_performance_highlight_reel_feedback_coach_followup_message_id"),
        table_name="performance_highlight_reel_feedback",
    )
    op.drop_constraint(
        op.f("fk_performance_highlight_reel_feedback_coach_followup_message_id_communication_messages"),
        "performance_highlight_reel_feedback",
        type_="foreignkey",
    )
    op.drop_column("performance_highlight_reel_feedback", "coach_followup_sent_at")
    op.drop_column("performance_highlight_reel_feedback", "coach_followup_notes")
    op.drop_column("performance_highlight_reel_feedback", "coach_followup_message_id")
