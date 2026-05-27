"""add event travel expenses

Revision ID: 8d13b7f4c2a9
Revises: 6b8f0d4e12a7
Create Date: 2026-05-28 04:20:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "8d13b7f4c2a9"
down_revision: str | None = "6b8f0d4e12a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_travel_expenses",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("travel_plan_id", app.models.base.GUID(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("vendor", sa.String(length=180), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("incurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("reimbursement_status", sa.String(length=40), nullable=False, server_default="submitted"),
        sa.Column("approved_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("reimbursed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("receipt_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["approved_by_person_id"],
            ["persons.id"],
            name=op.f("fk_event_travel_expenses_approved_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_travel_expenses_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["paid_by_person_id"],
            ["persons.id"],
            name=op.f("fk_event_travel_expenses_paid_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["travel_plan_id"],
            ["event_travel_plans.id"],
            name=op.f("fk_event_travel_expenses_travel_plan_id_event_travel_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_travel_expenses")),
    )
    for column in [
        "approved_by_person_id",
        "category",
        "incurred_at",
        "organization_id",
        "paid_by_person_id",
        "reimbursed_at",
        "reimbursement_status",
        "travel_plan_id",
        "vendor",
    ]:
        op.create_index(
            op.f(f"ix_event_travel_expenses_{column}"),
            "event_travel_expenses",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "vendor",
        "travel_plan_id",
        "reimbursement_status",
        "reimbursed_at",
        "paid_by_person_id",
        "organization_id",
        "incurred_at",
        "category",
        "approved_by_person_id",
    ]:
        op.drop_index(op.f(f"ix_event_travel_expenses_{column}"), table_name="event_travel_expenses")
    op.drop_table("event_travel_expenses")
