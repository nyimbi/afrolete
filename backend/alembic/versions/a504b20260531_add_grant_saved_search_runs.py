"""add grant saved search runs

Revision ID: a504b20260531
Revises: a503b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a504b20260531"
down_revision: str | Sequence[str] | None = "a503b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grant_saved_search_runs",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("saved_search_id", GUID(), nullable=False),
        sa.Column("triggered_by", sa.String(length=80), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("match_count", sa.Integer(), nullable=False),
        sa.Column("high_fit_count", sa.Integer(), nullable=False),
        sa.Column("alert_count", sa.Integer(), nullable=False),
        sa.Column("average_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_grant_saved_search_runs_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["saved_search_id"],
            ["grant_saved_searches.id"],
            name=op.f("fk_grant_saved_search_runs_saved_search_id_grant_saved_searches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grant_saved_search_runs")),
    )
    for column in (
        "completed_at",
        "dry_run",
        "organization_id",
        "saved_search_id",
        "started_at",
        "status",
        "triggered_by",
    ):
        op.create_index(op.f(f"ix_grant_saved_search_runs_{column}"), "grant_saved_search_runs", [column])


def downgrade() -> None:
    for column in (
        "triggered_by",
        "status",
        "started_at",
        "saved_search_id",
        "organization_id",
        "dry_run",
        "completed_at",
    ):
        op.drop_index(op.f(f"ix_grant_saved_search_runs_{column}"), table_name="grant_saved_search_runs")
    op.drop_table("grant_saved_search_runs")
