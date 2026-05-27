"""add travel expense payout fields

Revision ID: e6c4a2d9b813
Revises: d4b7c1a8f2e3
Create Date: 2026-05-28 07:25:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "e6c4a2d9b813"
down_revision: str | None = "d4b7c1a8f2e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("event_travel_expenses", sa.Column("payout_provider", sa.String(length=80), nullable=True))
    op.add_column("event_travel_expenses", sa.Column("payout_reference", sa.String(length=180), nullable=True))
    op.add_column("event_travel_expenses", sa.Column("payout_status", sa.String(length=40), nullable=True))
    op.add_column("event_travel_expenses", sa.Column("payout_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "event_travel_expenses",
        sa.Column("payout_processed_by_person_id", app.models.base.GUID(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_event_travel_expenses_payout_processed_by_person_id_persons"),
        "event_travel_expenses",
        "persons",
        ["payout_processed_by_person_id"],
        ["id"],
    )
    for column in [
        "payout_processed_by_person_id",
        "payout_provider",
        "payout_reference",
        "payout_requested_at",
        "payout_status",
    ]:
        op.create_index(op.f(f"ix_event_travel_expenses_{column}"), "event_travel_expenses", [column], unique=False)


def downgrade() -> None:
    for column in [
        "payout_status",
        "payout_requested_at",
        "payout_reference",
        "payout_provider",
        "payout_processed_by_person_id",
    ]:
        op.drop_index(op.f(f"ix_event_travel_expenses_{column}"), table_name="event_travel_expenses")
    op.drop_constraint(
        op.f("fk_event_travel_expenses_payout_processed_by_person_id_persons"),
        "event_travel_expenses",
        type_="foreignkey",
    )
    op.drop_column("event_travel_expenses", "payout_processed_by_person_id")
    op.drop_column("event_travel_expenses", "payout_requested_at")
    op.drop_column("event_travel_expenses", "payout_status")
    op.drop_column("event_travel_expenses", "payout_reference")
    op.drop_column("event_travel_expenses", "payout_provider")
