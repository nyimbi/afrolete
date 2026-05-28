"""add performance forecast validation runs

Revision ID: f18c2a9d7b64
Revises: d4a9e7c1b6f2
Create Date: 2026-05-28 18:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
import app.models.base


revision: str = "f18c2a9d7b64"
down_revision: str | None = "d4a9e7c1b6f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_forecast_validation_runs",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=True),
        sa.Column("model_policy", sa.String(length=180), nullable=False),
        sa.Column("forecast_mode", sa.String(length=40), nullable=False),
        sa.Column("metric_count", sa.Integer(), nullable=False),
        sa.Column("evaluated_count", sa.Integer(), nullable=False),
        sa.Column("passed_count", sa.Integer(), nullable=False),
        sa.Column("drift_count", sa.Integer(), nullable=False),
        sa.Column("mean_absolute_error", sa.Float(), nullable=False),
        sa.Column("mean_relative_error", sa.Float(), nullable=False),
        sa.Column("max_absolute_error", sa.Float(), nullable=False),
        sa.Column("drift_level", sa.String(length=40), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_by_person_id", app.models.base.GUID(), nullable=True),
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
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            name=op.f("fk_performance_forecast_validation_runs_athlete_profile_id_athlete_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_person_id"],
            ["persons.id"],
            name=op.f("fk_performance_forecast_validation_runs_created_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_performance_forecast_validation_runs_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_forecast_validation_runs")),
    )
    for column in (
        "athlete_profile_id",
        "created_by_person_id",
        "drift_level",
        "forecast_mode",
        "model_policy",
        "organization_id",
    ):
        op.create_index(
            op.f(f"ix_performance_forecast_validation_runs_{column}"),
            "performance_forecast_validation_runs",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in (
        "organization_id",
        "model_policy",
        "forecast_mode",
        "drift_level",
        "created_by_person_id",
        "athlete_profile_id",
    ):
        op.drop_index(
            op.f(f"ix_performance_forecast_validation_runs_{column}"),
            table_name="performance_forecast_validation_runs",
        )
    op.drop_table("performance_forecast_validation_runs")
