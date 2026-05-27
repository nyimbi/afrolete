"""add event travel checklists

Revision ID: 3c27e8f91b04
Revises: 0f4b9e2d8c61
Create Date: 2026-05-28 03:45:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "3c27e8f91b04"
down_revision: str | None = "0f4b9e2d8c61"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_travel_checklist_items",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("travel_plan_id", app.models.base.GUID(), nullable=False),
        sa.Column("checklist_type", sa.String(length=80), nullable=False, server_default="pre_trip_inspection"),
        sa.Column("item_label", sa.String(length=240), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("completed_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["completed_by_person_id"],
            ["persons.id"],
            name=op.f("fk_event_travel_checklist_items_completed_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_travel_checklist_items_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["travel_plan_id"],
            ["event_travel_plans.id"],
            name=op.f("fk_event_travel_checklist_items_travel_plan_id_event_travel_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_travel_checklist_items")),
        sa.UniqueConstraint(
            "travel_plan_id",
            "checklist_type",
            "item_label",
            name=op.f("uq_event_travel_checklist_items_travel_plan_id"),
        ),
    )
    for column in [
        "checklist_type",
        "completed_at",
        "completed_by_person_id",
        "item_label",
        "organization_id",
        "status",
        "travel_plan_id",
    ]:
        op.create_index(
            op.f(f"ix_event_travel_checklist_items_{column}"),
            "event_travel_checklist_items",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "travel_plan_id",
        "status",
        "organization_id",
        "item_label",
        "completed_by_person_id",
        "completed_at",
        "checklist_type",
    ]:
        op.drop_index(op.f(f"ix_event_travel_checklist_items_{column}"), table_name="event_travel_checklist_items")
    op.drop_table("event_travel_checklist_items")
