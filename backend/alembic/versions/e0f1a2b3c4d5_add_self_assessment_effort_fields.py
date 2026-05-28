"""add self assessment effort fields

Revision ID: e0f1a2b3c4d5
Revises: d5e6f7a8b9c0
Create Date: 2026-05-28 15:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "e0f1a2b3c4d5"
down_revision: str | None = "d5e6f7a8b9c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("athlete_assessments", sa.Column("perceived_exertion", sa.Float(), nullable=True))
    op.add_column("athlete_assessments", sa.Column("effort_rating", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("athlete_assessments", "effort_rating")
    op.drop_column("athlete_assessments", "perceived_exertion")
