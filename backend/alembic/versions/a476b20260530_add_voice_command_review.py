"""add voice command review

Revision ID: a476b20260530
Revises: a475b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a476b20260530"
down_revision: str | Sequence[str] | None = "a475b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("coach_voice_commands", sa.Column("reviewed_by_person_id", GUID(), nullable=True))
    op.add_column(
        "coach_voice_commands",
        sa.Column("review_result_json", sa.Text(), server_default="{}", nullable=False),
    )
    op.add_column("coach_voice_commands", sa.Column("review_decision", sa.String(length=40), nullable=True))
    op.add_column("coach_voice_commands", sa.Column("review_notes", sa.Text(), nullable=True))
    op.create_foreign_key(
        op.f("fk_coach_voice_commands_reviewed_by_person_id_persons"),
        "coach_voice_commands",
        "persons",
        ["reviewed_by_person_id"],
        ["id"],
    )
    for column in ["review_decision", "reviewed_by_person_id"]:
        op.create_index(op.f(f"ix_coach_voice_commands_{column}"), "coach_voice_commands", [column])


def downgrade() -> None:
    for column in ["reviewed_by_person_id", "review_decision"]:
        op.drop_index(op.f(f"ix_coach_voice_commands_{column}"), table_name="coach_voice_commands")
    op.drop_constraint(
        op.f("fk_coach_voice_commands_reviewed_by_person_id_persons"),
        "coach_voice_commands",
        type_="foreignkey",
    )
    op.drop_column("coach_voice_commands", "review_notes")
    op.drop_column("coach_voice_commands", "review_decision")
    op.drop_column("coach_voice_commands", "review_result_json")
    op.drop_column("coach_voice_commands", "reviewed_by_person_id")
