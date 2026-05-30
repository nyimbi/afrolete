"""add match guidance feedback followup

Revision ID: a485b20260531
Revises: a484b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a485b20260531"
down_revision: str | Sequence[str] | None = "a484b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "performance_match_player_guidance_feedback",
        sa.Column("coach_followup_message_id", GUID(), nullable=True),
    )
    op.add_column(
        "performance_match_player_guidance_feedback",
        sa.Column("coach_followup_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "performance_match_player_guidance_feedback",
        sa.Column("coach_followup_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_perf_match_guidance_feedback_coach_followup_msg",
        "performance_match_player_guidance_feedback",
        "communication_messages",
        ["coach_followup_message_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_feedback_coach_followup_message_id"),
        "performance_match_player_guidance_feedback",
        ["coach_followup_message_id"],
    )
    op.create_index(
        op.f("ix_performance_match_player_guidance_feedback_coach_followup_sent_at"),
        "performance_match_player_guidance_feedback",
        ["coach_followup_sent_at"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_performance_match_player_guidance_feedback_coach_followup_sent_at"),
        table_name="performance_match_player_guidance_feedback",
    )
    op.drop_index(
        op.f("ix_performance_match_player_guidance_feedback_coach_followup_message_id"),
        table_name="performance_match_player_guidance_feedback",
    )
    op.drop_constraint(
        "fk_perf_match_guidance_feedback_coach_followup_msg",
        "performance_match_player_guidance_feedback",
        type_="foreignkey",
    )
    op.drop_column("performance_match_player_guidance_feedback", "coach_followup_sent_at")
    op.drop_column("performance_match_player_guidance_feedback", "coach_followup_notes")
    op.drop_column("performance_match_player_guidance_feedback", "coach_followup_message_id")
