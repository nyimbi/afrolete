"""add event travel driver ratings

Revision ID: a7d9c3e5b621
Revises: f3c8b2a719d4
Create Date: 2026-05-28 06:40:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a7d9c3e5b621"
down_revision: str | None = "f3c8b2a719d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_travel_driver_ratings",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("travel_plan_id", app.models.base.GUID(), nullable=False),
        sa.Column("driver_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("reviewer_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("driver_name", sa.String(length=160), nullable=False),
        sa.Column("vehicle_label", sa.String(length=180), nullable=True),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("safety_score", sa.Integer(), nullable=True),
        sa.Column("punctuality_score", sa.Integer(), nullable=True),
        sa.Column("communication_score", sa.Integer(), nullable=True),
        sa.Column("vehicle_condition_score", sa.Integer(), nullable=True),
        sa.Column("would_use_again", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("incident_reported", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["driver_person_id"],
            ["persons.id"],
            name=op.f("fk_event_travel_driver_ratings_driver_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_travel_driver_ratings_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_person_id"],
            ["persons.id"],
            name=op.f("fk_event_travel_driver_ratings_reviewer_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["travel_plan_id"],
            ["event_travel_plans.id"],
            name=op.f("fk_event_travel_driver_ratings_travel_plan_id_event_travel_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_travel_driver_ratings")),
    )
    for column in [
        "driver_name",
        "driver_person_id",
        "incident_reported",
        "organization_id",
        "overall_score",
        "reviewed_at",
        "reviewer_person_id",
        "travel_plan_id",
        "vehicle_label",
        "would_use_again",
    ]:
        op.create_index(
            op.f(f"ix_event_travel_driver_ratings_{column}"),
            "event_travel_driver_ratings",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "would_use_again",
        "vehicle_label",
        "travel_plan_id",
        "reviewer_person_id",
        "reviewed_at",
        "overall_score",
        "organization_id",
        "incident_reported",
        "driver_person_id",
        "driver_name",
    ]:
        op.drop_index(op.f(f"ix_event_travel_driver_ratings_{column}"), table_name="event_travel_driver_ratings")
    op.drop_table("event_travel_driver_ratings")
