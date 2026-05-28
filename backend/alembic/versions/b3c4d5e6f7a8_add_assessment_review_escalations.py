"""add assessment review escalations

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-05-28 18:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

import app.models.base


revision: str = "b3c4d5e6f7a8"
down_revision: str | None = "a2b3c4d5e6f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "athlete_assessments",
        sa.Column("review_last_escalated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "athlete_assessments",
        sa.Column("review_escalation_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "athlete_assessments",
        sa.Column("review_escalation_message_id", app.models.base.GUID(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_athlete_assessments_review_escalation_message_id_communication_messages"),
        "athlete_assessments",
        "communication_messages",
        ["review_escalation_message_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_athlete_assessments_review_last_escalated_at"),
        "athlete_assessments",
        ["review_last_escalated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_athlete_assessments_review_escalation_message_id"),
        "athlete_assessments",
        ["review_escalation_message_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_athlete_assessments_review_escalation_message_id"),
        table_name="athlete_assessments",
    )
    op.drop_index(
        op.f("ix_athlete_assessments_review_last_escalated_at"),
        table_name="athlete_assessments",
    )
    op.drop_constraint(
        op.f("fk_athlete_assessments_review_escalation_message_id_communication_messages"),
        "athlete_assessments",
        type_="foreignkey",
    )
    op.drop_column("athlete_assessments", "review_escalation_message_id")
    op.drop_column("athlete_assessments", "review_escalation_count")
    op.drop_column("athlete_assessments", "review_last_escalated_at")
