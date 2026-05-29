"""add athlete pathway projections

Revision ID: a447b20260530
Revises: a446b20260530
Create Date: 2026-05-30 09:30:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a447b20260530"
down_revision: str | None = "a446b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "athlete_pathway_projections",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("created_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("sport", sa.String(length=80), nullable=False),
        sa.Column("primary_position", sa.String(length=80), nullable=True),
        sa.Column("age_years", sa.Integer(), nullable=True),
        sa.Column("academic_gpa", sa.Float(), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("target_pathway", sa.String(length=80), nullable=False),
        sa.Column("model_policy", sa.String(length=180), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("readiness_score", sa.Integer(), nullable=False),
        sa.Column("projected_level", sa.String(length=80), nullable=False),
        sa.Column("college_fit_score", sa.Float(), nullable=False),
        sa.Column("semi_pro_fit_score", sa.Float(), nullable=False),
        sa.Column("professional_fit_score", sa.Float(), nullable=False),
        sa.Column("scholarship_fit_score", sa.Float(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("pathways_json", sa.Text(), nullable=False),
        sa.Column("milestones_json", sa.Text(), nullable=False),
        sa.Column("scout_actions_json", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.Text(), nullable=False),
        sa.Column("risk_flags_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_athlete_pathway_projections_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_person_id"],
            ["persons.id"],
            name=op.f("fk_athlete_pathway_projections_created_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_athlete_pathway_projections_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_athlete_pathway_projections")),
    )
    op.create_index(op.f("ix_athlete_pathway_projections_age_years"), "athlete_pathway_projections", ["age_years"])
    op.create_index(
        op.f("ix_athlete_pathway_projections_athlete_profile_id"),
        "athlete_pathway_projections",
        ["athlete_profile_id"],
    )
    op.create_index(
        op.f("ix_athlete_pathway_projections_created_by_person_id"),
        "athlete_pathway_projections",
        ["created_by_person_id"],
    )
    op.create_index(
        op.f("ix_athlete_pathway_projections_generated_at"),
        "athlete_pathway_projections",
        ["generated_at"],
    )
    op.create_index(
        op.f("ix_athlete_pathway_projections_graduation_year"),
        "athlete_pathway_projections",
        ["graduation_year"],
    )
    op.create_index(
        op.f("ix_athlete_pathway_projections_model_policy"),
        "athlete_pathway_projections",
        ["model_policy"],
    )
    op.create_index(
        op.f("ix_athlete_pathway_projections_organization_id"),
        "athlete_pathway_projections",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_athlete_pathway_projections_primary_position"),
        "athlete_pathway_projections",
        ["primary_position"],
    )
    op.create_index(
        op.f("ix_athlete_pathway_projections_projected_level"),
        "athlete_pathway_projections",
        ["projected_level"],
    )
    op.create_index(
        op.f("ix_athlete_pathway_projections_readiness_score"),
        "athlete_pathway_projections",
        ["readiness_score"],
    )
    op.create_index(op.f("ix_athlete_pathway_projections_sport"), "athlete_pathway_projections", ["sport"])
    op.create_index(op.f("ix_athlete_pathway_projections_status"), "athlete_pathway_projections", ["status"])
    op.create_index(
        op.f("ix_athlete_pathway_projections_target_pathway"),
        "athlete_pathway_projections",
        ["target_pathway"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_athlete_pathway_projections_target_pathway"), table_name="athlete_pathway_projections")
    op.drop_index(op.f("ix_athlete_pathway_projections_status"), table_name="athlete_pathway_projections")
    op.drop_index(op.f("ix_athlete_pathway_projections_sport"), table_name="athlete_pathway_projections")
    op.drop_index(op.f("ix_athlete_pathway_projections_readiness_score"), table_name="athlete_pathway_projections")
    op.drop_index(op.f("ix_athlete_pathway_projections_projected_level"), table_name="athlete_pathway_projections")
    op.drop_index(op.f("ix_athlete_pathway_projections_primary_position"), table_name="athlete_pathway_projections")
    op.drop_index(op.f("ix_athlete_pathway_projections_organization_id"), table_name="athlete_pathway_projections")
    op.drop_index(op.f("ix_athlete_pathway_projections_model_policy"), table_name="athlete_pathway_projections")
    op.drop_index(op.f("ix_athlete_pathway_projections_graduation_year"), table_name="athlete_pathway_projections")
    op.drop_index(op.f("ix_athlete_pathway_projections_generated_at"), table_name="athlete_pathway_projections")
    op.drop_index(
        op.f("ix_athlete_pathway_projections_created_by_person_id"),
        table_name="athlete_pathway_projections",
    )
    op.drop_index(
        op.f("ix_athlete_pathway_projections_athlete_profile_id"),
        table_name="athlete_pathway_projections",
    )
    op.drop_index(op.f("ix_athlete_pathway_projections_age_years"), table_name="athlete_pathway_projections")
    op.drop_table("athlete_pathway_projections")
