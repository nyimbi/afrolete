"""add grant opportunity matches

Revision ID: a502b20260531
Revises: a501b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a502b20260531"
down_revision: str | Sequence[str] | None = "a501b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grant_opportunity_matches",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("grant_opportunity_id", GUID(), nullable=False),
        sa.Column("profile_name", sa.String(length=160), nullable=False),
        sa.Column("match_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("fit_band", sa.String(length=40), nullable=False),
        sa.Column("success_probability", sa.Numeric(5, 2), nullable=False),
        sa.Column("matched_terms_json", sa.Text(), nullable=True),
        sa.Column("missing_terms_json", sa.Text(), nullable=True),
        sa.Column("focus_terms_json", sa.Text(), nullable=True),
        sa.Column("excluded_terms_json", sa.Text(), nullable=True),
        sa.Column("alert_status", sa.String(length=40), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["grant_opportunity_id"],
            ["grant_opportunities.id"],
            name=op.f("fk_grant_opportunity_matches_grant_opportunity_id_grant_opportunities"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_grant_opportunity_matches_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grant_opportunity_matches")),
        sa.UniqueConstraint(
            "organization_id",
            "grant_opportunity_id",
            "profile_name",
            name="uq_grant_opportunity_matches_profile",
        ),
    )
    for column in (
        "alert_status",
        "fit_band",
        "generated_at",
        "grant_opportunity_id",
        "match_score",
        "organization_id",
        "profile_name",
    ):
        op.create_index(op.f(f"ix_grant_opportunity_matches_{column}"), "grant_opportunity_matches", [column])


def downgrade() -> None:
    for column in (
        "profile_name",
        "organization_id",
        "match_score",
        "grant_opportunity_id",
        "generated_at",
        "fit_band",
        "alert_status",
    ):
        op.drop_index(op.f(f"ix_grant_opportunity_matches_{column}"), table_name="grant_opportunity_matches")
    op.drop_table("grant_opportunity_matches")
