"""add lease installment paid amount

Revision ID: e41f2a7b8c9d
Revises: c33f8f22d9a0
Create Date: 2026-05-27 22:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "e41f2a7b8c9d"
down_revision: str | None = "c33f8f22d9a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "equipment_lease_installments",
        sa.Column(
            "amount_paid",
            sa.Numeric(12, 2),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("equipment_lease_installments", "amount_paid")
