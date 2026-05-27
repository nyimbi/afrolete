"""add travel payout adapter fields

Revision ID: d9f1b7a4c6e8
Revises: c8a4d1f7e2b9
Create Date: 2026-05-28 08:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "d9f1b7a4c6e8"
down_revision: str | None = "c8a4d1f7e2b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("event_travel_expenses", sa.Column("payout_adapter_mode", sa.String(length=80), nullable=True))
    op.add_column("event_travel_expenses", sa.Column("payout_destination", sa.String(length=240), nullable=True))
    op.add_column("event_travel_expenses", sa.Column("payout_idempotency_key", sa.String(length=180), nullable=True))
    op.add_column("event_travel_expenses", sa.Column("payout_provider_status_code", sa.Integer(), nullable=True))
    op.add_column("event_travel_expenses", sa.Column("payout_provider_response", sa.Text(), nullable=True))
    op.create_index(op.f("ix_event_travel_expenses_payout_adapter_mode"), "event_travel_expenses", ["payout_adapter_mode"])
    op.create_index(
        op.f("ix_event_travel_expenses_payout_idempotency_key"),
        "event_travel_expenses",
        ["payout_idempotency_key"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_event_travel_expenses_payout_idempotency_key"), table_name="event_travel_expenses")
    op.drop_index(op.f("ix_event_travel_expenses_payout_adapter_mode"), table_name="event_travel_expenses")
    op.drop_column("event_travel_expenses", "payout_provider_response")
    op.drop_column("event_travel_expenses", "payout_provider_status_code")
    op.drop_column("event_travel_expenses", "payout_idempotency_key")
    op.drop_column("event_travel_expenses", "payout_destination")
    op.drop_column("event_travel_expenses", "payout_adapter_mode")
