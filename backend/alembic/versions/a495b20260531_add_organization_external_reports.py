"""add organization external reports

Revision ID: a495b20260531
Revises: a494b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a495b20260531"
down_revision: str | Sequence[str] | None = "a494b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_external_reports",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("market_profile_id", GUID(), nullable=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("report_code", sa.String(length=120), nullable=False),
        sa.Column("report_type", sa.String(length=80), nullable=False),
        sa.Column("target_agency", sa.String(length=180), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=False),
        sa.Column("reporting_period_start", sa.Date(), nullable=False),
        sa.Column("reporting_period_end", sa.Date(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("submission_format", sa.String(length=40), nullable=False),
        sa.Column("data_elements_json", sa.Text(), nullable=True),
        sa.Column("source_summary", sa.Text(), nullable=True),
        sa.Column("generated_payload", sa.Text(), nullable=True),
        sa.Column("submission_payload", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("external_reference", sa.String(length=180), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["market_profile_id"],
            ["organization_market_profiles.id"],
            name=op.f("fk_organization_external_reports_market_profile_id_organization_market_profiles"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_external_reports_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_external_reports")),
        sa.UniqueConstraint(
            "organization_id",
            "target_agency",
            "report_code",
            "reporting_period_start",
            "reporting_period_end",
            name="uq_organization_external_reports_period",
        ),
    )
    for column in (
        "accepted_at",
        "due_on",
        "external_reference",
        "market_profile_id",
        "name",
        "organization_id",
        "report_code",
        "report_type",
        "reporting_period_end",
        "reporting_period_start",
        "status",
        "submission_format",
        "submitted_at",
        "target_agency",
        "target_type",
    ):
        op.create_index(
            op.f(f"ix_organization_external_reports_{column}"),
            "organization_external_reports",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in (
        "target_type",
        "target_agency",
        "submitted_at",
        "submission_format",
        "status",
        "reporting_period_start",
        "reporting_period_end",
        "report_type",
        "report_code",
        "organization_id",
        "name",
        "market_profile_id",
        "external_reference",
        "due_on",
        "accepted_at",
    ):
        op.drop_index(op.f(f"ix_organization_external_reports_{column}"), table_name="organization_external_reports")
    op.drop_table("organization_external_reports")
