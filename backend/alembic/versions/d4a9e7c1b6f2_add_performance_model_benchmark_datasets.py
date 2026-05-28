"""add performance model benchmark datasets

Revision ID: d4a9e7c1b6f2
Revises: c178ef90ab12
Create Date: 2026-05-28 17:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
import app.models.base


revision: str = "d4a9e7c1b6f2"
down_revision: str | None = "c178ef90ab12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_model_extraction_benchmark_datasets",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("model_policy", sa.String(length=180), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("owner_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_accuracy", sa.Float(), nullable=True),
        sa.Column("last_mean_absolute_error", sa.Float(), nullable=True),
        sa.Column("last_case_count", sa.Integer(), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f(
                "fk_performance_model_extraction_benchmark_datasets_organization_id_organizations"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["owner_person_id"],
            ["persons.id"],
            name=op.f("fk_performance_model_extraction_benchmark_datasets_owner_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("pk_performance_model_extraction_benchmark_datasets")
        ),
        sa.UniqueConstraint(
            "organization_id",
            "slug",
            name="uq_performance_model_extraction_benchmark_datasets_slug",
        ),
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_datasets_model_policy"),
        "performance_model_extraction_benchmark_datasets",
        ["model_policy"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_datasets_organization_id"),
        "performance_model_extraction_benchmark_datasets",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_datasets_owner_person_id"),
        "performance_model_extraction_benchmark_datasets",
        ["owner_person_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_datasets_slug"),
        "performance_model_extraction_benchmark_datasets",
        ["slug"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_datasets_status"),
        "performance_model_extraction_benchmark_datasets",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_datasets_last_run_at"),
        "performance_model_extraction_benchmark_datasets",
        ["last_run_at"],
        unique=False,
    )
    op.create_table(
        "performance_model_extraction_benchmark_cases",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("dataset_id", app.models.base.GUID(), nullable=False),
        sa.Column("case_id", sa.String(length=120), nullable=False),
        sa.Column("metric_code", sa.String(length=80), nullable=False),
        sa.Column("metric_name", sa.String(length=180), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "physical",
                "technical",
                "tactical",
                "mental",
                "wellness",
                "competition",
                name="metriccategory",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("unit", sa.String(length=40), nullable=True),
        sa.Column("min_value", sa.Float(), nullable=True),
        sa.Column("max_value", sa.Float(), nullable=True),
        sa.Column(
            "source",
            sa.Enum(
                "manual",
                "coach_evaluation",
                "self_assessment",
                "official_stats",
                "video_analysis",
                "audio_narration",
                "wearable",
                "agent_extracted",
                name="metricsource",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("source_provider", sa.String(length=80), nullable=True),
        sa.Column("evidence_ref", sa.String(length=500), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("expected_value", sa.Float(), nullable=False),
        sa.Column("tolerance", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["performance_model_extraction_benchmark_datasets.id"],
            name=op.f(
                "fk_performance_model_extraction_benchmark_cases_dataset_id_performance_model_extraction_benchmark_datasets"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f(
                "fk_performance_model_extraction_benchmark_cases_organization_id_organizations"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_model_extraction_benchmark_cases")),
        sa.UniqueConstraint(
            "dataset_id", "case_id", name="uq_performance_model_extraction_benchmark_cases_case_id"
        ),
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_cases_case_id"),
        "performance_model_extraction_benchmark_cases",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_cases_dataset_id"),
        "performance_model_extraction_benchmark_cases",
        ["dataset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_cases_metric_code"),
        "performance_model_extraction_benchmark_cases",
        ["metric_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_cases_organization_id"),
        "performance_model_extraction_benchmark_cases",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_cases_source"),
        "performance_model_extraction_benchmark_cases",
        ["source"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_cases_source_provider"),
        "performance_model_extraction_benchmark_cases",
        ["source_provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_model_extraction_benchmark_cases_status"),
        "performance_model_extraction_benchmark_cases",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_cases_status"),
        table_name="performance_model_extraction_benchmark_cases",
    )
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_cases_source_provider"),
        table_name="performance_model_extraction_benchmark_cases",
    )
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_cases_source"),
        table_name="performance_model_extraction_benchmark_cases",
    )
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_cases_organization_id"),
        table_name="performance_model_extraction_benchmark_cases",
    )
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_cases_metric_code"),
        table_name="performance_model_extraction_benchmark_cases",
    )
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_cases_dataset_id"),
        table_name="performance_model_extraction_benchmark_cases",
    )
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_cases_case_id"),
        table_name="performance_model_extraction_benchmark_cases",
    )
    op.drop_table("performance_model_extraction_benchmark_cases")
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_datasets_last_run_at"),
        table_name="performance_model_extraction_benchmark_datasets",
    )
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_datasets_status"),
        table_name="performance_model_extraction_benchmark_datasets",
    )
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_datasets_slug"),
        table_name="performance_model_extraction_benchmark_datasets",
    )
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_datasets_owner_person_id"),
        table_name="performance_model_extraction_benchmark_datasets",
    )
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_datasets_organization_id"),
        table_name="performance_model_extraction_benchmark_datasets",
    )
    op.drop_index(
        op.f("ix_performance_model_extraction_benchmark_datasets_model_policy"),
        table_name="performance_model_extraction_benchmark_datasets",
    )
    op.drop_table("performance_model_extraction_benchmark_datasets")
