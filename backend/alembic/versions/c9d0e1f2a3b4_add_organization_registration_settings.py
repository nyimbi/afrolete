"""add organization registration settings

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2
Create Date: 2026-05-29 23:35:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "c9d0e1f2a3b4"
down_revision: str | None = "b7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("registration_open", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column("organizations", sa.Column("registration_fee_amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("organizations", sa.Column("registration_fee_currency", sa.String(length=3), nullable=True))
    op.add_column("organizations", sa.Column("registration_payment_instructions", sa.Text(), nullable=True))
    op.add_column("organizations", sa.Column("registration_required_documents_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("organizations", "registration_required_documents_json")
    op.drop_column("organizations", "registration_payment_instructions")
    op.drop_column("organizations", "registration_fee_currency")
    op.drop_column("organizations", "registration_fee_amount")
    op.drop_column("organizations", "registration_open")
