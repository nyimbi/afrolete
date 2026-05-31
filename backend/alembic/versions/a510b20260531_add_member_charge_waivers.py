"""add member charge waivers

Revision ID: a510b20260531
Revises: a509b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a510b20260531"
down_revision: str | Sequence[str] | None = "a509b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "member_subscription_charges",
        sa.Column("amount_waived", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "member_subscription_charges",
        sa.Column("waived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "member_subscription_charges",
        sa.Column("waived_by_person_id", GUID(), nullable=True),
    )
    op.add_column(
        "member_subscription_charges",
        sa.Column("waiver_reason", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_member_subscription_charges_waived_by_person_id_persons"),
        "member_subscription_charges",
        "persons",
        ["waived_by_person_id"],
        ["id"],
    )
    for column in ("waived_at", "waived_by_person_id"):
        op.create_index(op.f(f"ix_member_subscription_charges_{column}"), "member_subscription_charges", [column])
    op.alter_column("member_subscription_charges", "amount_waived", server_default=None)


def downgrade() -> None:
    for column in ("waived_by_person_id", "waived_at"):
        op.drop_index(op.f(f"ix_member_subscription_charges_{column}"), table_name="member_subscription_charges")
    op.drop_constraint(
        op.f("fk_member_subscription_charges_waived_by_person_id_persons"),
        "member_subscription_charges",
        type_="foreignkey",
    )
    op.drop_column("member_subscription_charges", "waiver_reason")
    op.drop_column("member_subscription_charges", "waived_by_person_id")
    op.drop_column("member_subscription_charges", "waived_at")
    op.drop_column("member_subscription_charges", "amount_waived")
