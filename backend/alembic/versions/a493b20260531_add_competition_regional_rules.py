"""add competition regional rules

Revision ID: a493b20260531
Revises: a492b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.models.base import GUID


revision: str = "a493b20260531"
down_revision: str | None = "a492b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PROFILE_INDEXES = [
    "organization_id",
    "competition_id",
    "name",
    "country_code",
    "region_code",
    "governing_body",
    "sport",
    "age_group",
    "competition_format",
    "effective_from",
    "effective_until",
    "status",
]

RULE_INDEXES = [
    "organization_id",
    "profile_id",
    "category",
    "rule_key",
    "applies_to",
    "severity",
    "status",
]


def create_indexes(table_name: str, columns: list[str]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table_name}_{column}"), table_name, [column])


def drop_indexes(table_name: str, columns: list[str]) -> None:
    for column in reversed(columns):
        op.drop_index(op.f(f"ix_{table_name}_{column}"), table_name=table_name)


def upgrade() -> None:
    op.create_table(
        "competition_regional_rule_profiles",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("competition_id", GUID(), nullable=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("region_code", sa.String(length=80), nullable=True),
        sa.Column("governing_body", sa.String(length=180), nullable=True),
        sa.Column("sport", sa.String(length=80), nullable=False),
        sa.Column("age_group", sa.String(length=80), nullable=True),
        sa.Column("competition_format", sa.String(length=80), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("min_age", sa.Integer(), nullable=True),
        sa.Column("max_age", sa.Integer(), nullable=True),
        sa.Column("roster_limit", sa.Integer(), nullable=True),
        sa.Column("match_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("substitution_limit", sa.Integer(), nullable=True),
        sa.Column("heat_policy", sa.Text(), nullable=True),
        sa.Column("eligibility_policy", sa.Text(), nullable=True),
        sa.Column("compliance_requirements", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_competition_regional_rule_profiles_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["competition_id"],
            ["competitions.id"],
            name=op.f("fk_competition_regional_rule_profiles_competition_id_competitions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_competition_regional_rule_profiles")),
        sa.UniqueConstraint(
            "organization_id",
            "country_code",
            "region_code",
            "sport",
            "age_group",
            "competition_format",
            name=op.f("uq_competition_regional_rule_profiles_scope"),
        ),
    )
    create_indexes("competition_regional_rule_profiles", PROFILE_INDEXES)

    op.create_table(
        "competition_regional_rules",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("profile_id", GUID(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("rule_key", sa.String(length=120), nullable=False),
        sa.Column("rule_value", sa.Text(), nullable=False),
        sa.Column("applies_to", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_competition_regional_rules_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["competition_regional_rule_profiles.id"],
            name=op.f("fk_competition_regional_rules_profile_id_competition_regional_rule_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_competition_regional_rules")),
        sa.UniqueConstraint(
            "profile_id",
            "category",
            "rule_key",
            name=op.f("uq_competition_regional_rules_profile_id"),
        ),
    )
    create_indexes("competition_regional_rules", RULE_INDEXES)


def downgrade() -> None:
    drop_indexes("competition_regional_rules", RULE_INDEXES)
    op.drop_table("competition_regional_rules")
    drop_indexes("competition_regional_rule_profiles", PROFILE_INDEXES)
    op.drop_table("competition_regional_rule_profiles")
