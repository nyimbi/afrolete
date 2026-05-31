"""add grant saved searches

Revision ID: a503b20260531
Revises: a502b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a503b20260531"
down_revision: str | Sequence[str] | None = "a502b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grant_saved_searches",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("profile_name", sa.String(length=160), nullable=False),
        sa.Column("focus_terms_json", sa.Text(), nullable=True),
        sa.Column("excluded_terms_json", sa.Text(), nullable=True),
        sa.Column("minimum_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("limit", sa.Integer(), nullable=False),
        sa.Column("alert_enabled", sa.Boolean(), nullable=False),
        sa.Column("alert_frequency", sa.String(length=40), nullable=False),
        sa.Column("alert_channel", sa.String(length=80), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_match_count", sa.Integer(), nullable=False),
        sa.Column("last_high_fit_count", sa.Integer(), nullable=False),
        sa.Column("last_alert_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_grant_saved_searches_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grant_saved_searches")),
        sa.UniqueConstraint("organization_id", "name", name="uq_grant_saved_searches_name"),
    )
    for column in (
        "alert_channel",
        "alert_enabled",
        "alert_frequency",
        "last_run_at",
        "name",
        "organization_id",
        "profile_name",
        "status",
    ):
        op.create_index(op.f(f"ix_grant_saved_searches_{column}"), "grant_saved_searches", [column])


def downgrade() -> None:
    for column in (
        "status",
        "profile_name",
        "organization_id",
        "name",
        "last_run_at",
        "alert_frequency",
        "alert_enabled",
        "alert_channel",
    ):
        op.drop_index(op.f(f"ix_grant_saved_searches_{column}"), table_name="grant_saved_searches")
    op.drop_table("grant_saved_searches")
