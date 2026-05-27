"""add event travel approvals

Revision ID: 0f4b9e2d8c61
Revises: c4e7b8a9d210
Create Date: 2026-05-28 03:25:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "0f4b9e2d8c61"
down_revision: str | None = "c4e7b8a9d210"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_travel_approvals",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("travel_plan_id", app.models.base.GUID(), nullable=False),
        sa.Column("approval_level", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("approver_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("decided_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["approver_person_id"],
            ["persons.id"],
            name=op.f("fk_event_travel_approvals_approver_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["decided_by_person_id"],
            ["persons.id"],
            name=op.f("fk_event_travel_approvals_decided_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_travel_approvals_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["travel_plan_id"],
            ["event_travel_plans.id"],
            name=op.f("fk_event_travel_approvals_travel_plan_id_event_travel_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_travel_approvals")),
        sa.UniqueConstraint("travel_plan_id", "approval_level", name=op.f("uq_event_travel_approvals_travel_plan_id")),
    )
    for column in [
        "approval_level",
        "approver_person_id",
        "decided_at",
        "decided_by_person_id",
        "organization_id",
        "status",
        "travel_plan_id",
    ]:
        op.create_index(
            op.f(f"ix_event_travel_approvals_{column}"),
            "event_travel_approvals",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "travel_plan_id",
        "status",
        "organization_id",
        "decided_by_person_id",
        "decided_at",
        "approver_person_id",
        "approval_level",
    ]:
        op.drop_index(op.f(f"ix_event_travel_approvals_{column}"), table_name="event_travel_approvals")
    op.drop_table("event_travel_approvals")
