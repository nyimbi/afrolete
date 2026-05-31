"""add migration and recovery ops

Revision ID: a490b20260531
Revises: a489b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.models.base import GUID


revision: str = "a490b20260531"
down_revision: str | None = "a489b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def create_indexes(table_name: str, columns: list[str]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table_name}_{column}"), table_name, [column])


def drop_indexes(table_name: str, columns: list[str]) -> None:
    for column in reversed(columns):
        op.drop_index(op.f(f"ix_{table_name}_{column}"), table_name=table_name)


def upgrade() -> None:
    op.create_table(
        "organization_data_migration_projects",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("source_system", sa.String(length=120), nullable=False),
        sa.Column("source_format", sa.String(length=80), nullable=False),
        sa.Column("migration_type", sa.String(length=80), nullable=False),
        sa.Column("data_domains", sa.Text(), nullable=True),
        sa.Column("owner_person_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("records_expected", sa.Integer(), nullable=True),
        sa.Column("records_imported", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_data_migration_projects_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_person_id"],
            ["persons.id"],
            name=op.f("fk_organization_data_migration_projects_owner_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_data_migration_projects")),
        sa.UniqueConstraint(
            "organization_id",
            "name",
            name=op.f("uq_organization_data_migration_projects_organization_id"),
        ),
    )
    create_indexes(
        "organization_data_migration_projects",
        [
            "organization_id",
            "name",
            "source_system",
            "source_format",
            "migration_type",
            "owner_person_id",
            "status",
            "risk_level",
            "started_at",
            "completed_at",
        ],
    )

    op.create_table(
        "organization_data_migration_runs",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=False),
        sa.Column("run_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("input_artifact_url", sa.String(length=500), nullable=True),
        sa.Column("mapping_summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_seen", sa.Integer(), nullable=False),
        sa.Column("records_created", sa.Integer(), nullable=False),
        sa.Column("records_updated", sa.Integer(), nullable=False),
        sa.Column("records_skipped", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("report_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_data_migration_runs_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["organization_data_migration_projects.id"],
            name=op.f("fk_organization_data_migration_runs_project_id_organization_data_migration_projects"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_data_migration_runs")),
    )
    create_indexes(
        "organization_data_migration_runs",
        ["organization_id", "project_id", "run_type", "status", "started_at", "finished_at", "checksum"],
    )

    op.create_table(
        "organization_recovery_plans",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("scope", sa.String(length=160), nullable=False),
        sa.Column("rpo_minutes", sa.Integer(), nullable=False),
        sa.Column("rto_minutes", sa.Integer(), nullable=False),
        sa.Column("backup_frequency", sa.String(length=80), nullable=False),
        sa.Column("storage_location", sa.String(length=500), nullable=True),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("encryption_policy", sa.String(length=240), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_test_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_recovery_plans_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_recovery_plans")),
        sa.UniqueConstraint("organization_id", "name", name=op.f("uq_organization_recovery_plans_organization_id")),
    )
    create_indexes(
        "organization_recovery_plans",
        [
            "organization_id",
            "name",
            "scope",
            "backup_frequency",
            "status",
            "last_tested_at",
            "next_test_due_at",
        ],
    )

    op.create_table(
        "organization_recovery_drills",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("recovery_plan_id", GUID(), nullable=False),
        sa.Column("drill_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rpo_minutes_observed", sa.Integer(), nullable=True),
        sa.Column("rto_minutes_observed", sa.Integer(), nullable=True),
        sa.Column("data_loss_summary", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("action_items", sa.Text(), nullable=True),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_recovery_drills_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["recovery_plan_id"],
            ["organization_recovery_plans.id"],
            name=op.f("fk_organization_recovery_drills_recovery_plan_id_organization_recovery_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_recovery_drills")),
    )
    create_indexes(
        "organization_recovery_drills",
        ["organization_id", "recovery_plan_id", "drill_type", "status", "started_at", "finished_at"],
    )


def downgrade() -> None:
    drop_indexes(
        "organization_recovery_drills",
        ["organization_id", "recovery_plan_id", "drill_type", "status", "started_at", "finished_at"],
    )
    op.drop_table("organization_recovery_drills")

    drop_indexes(
        "organization_recovery_plans",
        [
            "organization_id",
            "name",
            "scope",
            "backup_frequency",
            "status",
            "last_tested_at",
            "next_test_due_at",
        ],
    )
    op.drop_table("organization_recovery_plans")

    drop_indexes(
        "organization_data_migration_runs",
        ["organization_id", "project_id", "run_type", "status", "started_at", "finished_at", "checksum"],
    )
    op.drop_table("organization_data_migration_runs")

    drop_indexes(
        "organization_data_migration_projects",
        [
            "organization_id",
            "name",
            "source_system",
            "source_format",
            "migration_type",
            "owner_person_id",
            "status",
            "risk_level",
            "started_at",
            "completed_at",
        ],
    )
    op.drop_table("organization_data_migration_projects")
