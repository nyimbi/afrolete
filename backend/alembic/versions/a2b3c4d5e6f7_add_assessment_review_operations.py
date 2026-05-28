"""add assessment review operations

Revision ID: a2b3c4d5e6f7
Revises: e0f1a2b3c4d5
Create Date: 2026-05-28 18:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

import app.models.base


revision: str = "a2b3c4d5e6f7"
down_revision: str | None = "e0f1a2b3c4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "athlete_assessments",
        sa.Column("review_assigned_to_person_id", app.models.base.GUID(), nullable=True),
    )
    op.add_column(
        "athlete_assessments",
        sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "athlete_assessments",
        sa.Column("review_priority", sa.String(length=20), server_default="normal", nullable=False),
    )
    op.add_column("athlete_assessments", sa.Column("review_notes", sa.Text(), nullable=True))
    op.add_column(
        "athlete_assessments",
        sa.Column("reviewed_by_person_id", app.models.base.GUID(), nullable=True),
    )
    op.add_column(
        "athlete_assessments",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_athlete_assessments_review_assigned_to_person_id_persons"),
        "athlete_assessments",
        "persons",
        ["review_assigned_to_person_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_athlete_assessments_reviewed_by_person_id_persons"),
        "athlete_assessments",
        "persons",
        ["reviewed_by_person_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_athlete_assessments_review_assigned_to_person_id"),
        "athlete_assessments",
        ["review_assigned_to_person_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_athlete_assessments_review_due_at"),
        "athlete_assessments",
        ["review_due_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_athlete_assessments_review_priority"),
        "athlete_assessments",
        ["review_priority"],
        unique=False,
    )
    op.create_index(
        op.f("ix_athlete_assessments_reviewed_by_person_id"),
        "athlete_assessments",
        ["reviewed_by_person_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_athlete_assessments_reviewed_at"),
        "athlete_assessments",
        ["reviewed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_athlete_assessments_reviewed_at"), table_name="athlete_assessments")
    op.drop_index(op.f("ix_athlete_assessments_reviewed_by_person_id"), table_name="athlete_assessments")
    op.drop_index(op.f("ix_athlete_assessments_review_priority"), table_name="athlete_assessments")
    op.drop_index(op.f("ix_athlete_assessments_review_due_at"), table_name="athlete_assessments")
    op.drop_index(
        op.f("ix_athlete_assessments_review_assigned_to_person_id"),
        table_name="athlete_assessments",
    )
    op.drop_constraint(
        op.f("fk_athlete_assessments_reviewed_by_person_id_persons"),
        "athlete_assessments",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_athlete_assessments_review_assigned_to_person_id_persons"),
        "athlete_assessments",
        type_="foreignkey",
    )
    op.drop_column("athlete_assessments", "reviewed_at")
    op.drop_column("athlete_assessments", "reviewed_by_person_id")
    op.drop_column("athlete_assessments", "review_notes")
    op.drop_column("athlete_assessments", "review_priority")
    op.drop_column("athlete_assessments", "review_due_at")
    op.drop_column("athlete_assessments", "review_assigned_to_person_id")
