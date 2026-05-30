"""add product experience guides

Revision ID: a473b20260530
Revises: a472b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a473b20260530"
down_revision: str | Sequence[str] | None = "a472b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_tour_progress",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("person_id", GUID(), nullable=False),
        sa.Column("tour_key", sa.String(length=120), nullable=False),
        sa.Column("surface", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=False),
        sa.Column("current_step_key", sa.String(length=120), nullable=True),
        sa.Column("completed_steps_json", sa.Text(), nullable=False),
        sa.Column("skipped_steps_json", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("star_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("last_feedback", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "person_id", "tour_key", name="uq_product_tour_progress_org_person_tour"),
    )
    for column in [
        "completed_at",
        "current_step_key",
        "last_activity_at",
        "organization_id",
        "person_id",
        "role",
        "score",
        "status",
        "surface",
        "tour_key",
    ]:
        op.create_index(op.f(f"ix_product_tour_progress_{column}"), "product_tour_progress", [column])

    op.create_table(
        "product_help_interactions",
        sa.Column("organization_id", GUID(), nullable=True),
        sa.Column("person_id", GUID(), nullable=True),
        sa.Column("surface", sa.String(length=120), nullable=True),
        sa.Column("role", sa.String(length=120), nullable=True),
        sa.Column("query", sa.String(length=500), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("selected_article_key", sa.String(length=120), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "organization_id",
        "person_id",
        "query",
        "role",
        "selected_article_key",
        "surface",
    ]:
        op.create_index(op.f(f"ix_product_help_interactions_{column}"), "product_help_interactions", [column])


def downgrade() -> None:
    for column in [
        "surface",
        "selected_article_key",
        "role",
        "query",
        "person_id",
        "organization_id",
    ]:
        op.drop_index(op.f(f"ix_product_help_interactions_{column}"), table_name="product_help_interactions")
    op.drop_table("product_help_interactions")

    for column in [
        "tour_key",
        "surface",
        "status",
        "score",
        "role",
        "person_id",
        "organization_id",
        "last_activity_at",
        "current_step_key",
        "completed_at",
    ]:
        op.drop_index(op.f(f"ix_product_tour_progress_{column}"), table_name="product_tour_progress")
    op.drop_table("product_tour_progress")
