"""add movement reference profiles

Revision ID: f1b2c3d4e5f6
Revises: e9f2a1c4b6d8
Create Date: 2026-05-29 09:25:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "f1b2c3d4e5f6"
down_revision: str | None = "e9f2a1c4b6d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_movement_reference_profiles",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("created_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("sport", sa.String(length=80), nullable=False, server_default="athletics"),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("benchmark_profile", sa.String(length=120), nullable=False, server_default="world_class_sprint"),
        sa.Column("performer_name", sa.String(length=180), nullable=True),
        sa.Column("source_label", sa.String(length=240), nullable=False),
        sa.Column("competition_context", sa.String(length=240), nullable=True),
        sa.Column("consent_basis", sa.String(length=240), nullable=True),
        sa.Column("visibility", sa.String(length=40), nullable=False, server_default="tenant"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("metric_targets_json", sa.Text(), nullable=False),
        sa.Column("pose_samples_json", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_person_id"],
            ["persons.id"],
            name=op.f("fk_performance_movement_reference_profiles_created_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_performance_movement_reference_profiles_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_movement_reference_profiles")),
        sa.UniqueConstraint(
            "organization_id",
            "sport",
            "benchmark_profile",
            "name",
            name="uq_performance_movement_reference_profiles_name",
        ),
    )
    for column in [
        "benchmark_profile",
        "created_by_person_id",
        "name",
        "organization_id",
        "performer_name",
        "sport",
        "status",
        "visibility",
    ]:
        op.create_index(
            op.f(f"ix_performance_movement_reference_profiles_{column}"),
            "performance_movement_reference_profiles",
            [column],
        )


def downgrade() -> None:
    for column in [
        "visibility",
        "status",
        "sport",
        "performer_name",
        "organization_id",
        "name",
        "created_by_person_id",
        "benchmark_profile",
    ]:
        op.drop_index(
            op.f(f"ix_performance_movement_reference_profiles_{column}"),
            table_name="performance_movement_reference_profiles",
        )
    op.drop_table("performance_movement_reference_profiles")
