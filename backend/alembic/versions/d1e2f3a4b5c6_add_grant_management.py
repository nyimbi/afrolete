"""add grant management

Revision ID: d1e2f3a4b5c6
Revises: d0e1f2a3b4c5
Create Date: 2026-05-30 00:30:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d1e2f3a4b5c6"
down_revision: str | None = "d0e1f2a3b4c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grant_opportunities",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("funder_name", sa.String(length=180), nullable=False),
        sa.Column("program_name", sa.String(length=220), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("impact_area", sa.String(length=220), nullable=False),
        sa.Column("award_ceiling", sa.Numeric(12, 2), nullable=False),
        sa.Column("matching_required", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("opens_on", sa.Date(), nullable=True),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("eligibility_summary", sa.Text(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_grant_opportunities_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grant_opportunities")),
    )
    op.create_index(op.f("ix_grant_opportunities_category"), "grant_opportunities", ["category"])
    op.create_index(op.f("ix_grant_opportunities_due_on"), "grant_opportunities", ["due_on"])
    op.create_index(op.f("ix_grant_opportunities_funder_name"), "grant_opportunities", ["funder_name"])
    op.create_index(op.f("ix_grant_opportunities_organization_id"), "grant_opportunities", ["organization_id"])
    op.create_index(op.f("ix_grant_opportunities_program_name"), "grant_opportunities", ["program_name"])
    op.create_index(op.f("ix_grant_opportunities_status"), "grant_opportunities", ["status"])

    op.create_table(
        "grant_applications",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("grant_opportunity_id", app.models.base.GUID(), nullable=False),
        sa.Column("project_title", sa.String(length=220), nullable=False),
        sa.Column("requested_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("awarded_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("submitted_on", sa.Date(), nullable=True),
        sa.Column("decision_on", sa.Date(), nullable=True),
        sa.Column("reporting_due_on", sa.Date(), nullable=True),
        sa.Column("lead_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("budget_summary", sa.Text(), nullable=True),
        sa.Column("impact_metrics", sa.Text(), nullable=True),
        sa.Column("external_reference", sa.String(length=240), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["grant_opportunity_id"], ["grant_opportunities.id"], name=op.f("fk_grant_applications_grant_opportunity_id_grant_opportunities")),
        sa.ForeignKeyConstraint(["lead_person_id"], ["persons.id"], name=op.f("fk_grant_applications_lead_person_id_persons")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_grant_applications_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grant_applications")),
    )
    op.create_index(op.f("ix_grant_applications_decision_on"), "grant_applications", ["decision_on"])
    op.create_index(op.f("ix_grant_applications_external_reference"), "grant_applications", ["external_reference"])
    op.create_index(op.f("ix_grant_applications_grant_opportunity_id"), "grant_applications", ["grant_opportunity_id"])
    op.create_index(op.f("ix_grant_applications_lead_person_id"), "grant_applications", ["lead_person_id"])
    op.create_index(op.f("ix_grant_applications_organization_id"), "grant_applications", ["organization_id"])
    op.create_index(op.f("ix_grant_applications_project_title"), "grant_applications", ["project_title"])
    op.create_index(op.f("ix_grant_applications_reporting_due_on"), "grant_applications", ["reporting_due_on"])
    op.create_index(op.f("ix_grant_applications_status"), "grant_applications", ["status"])
    op.create_index(op.f("ix_grant_applications_submitted_on"), "grant_applications", ["submitted_on"])

    op.create_table(
        "grant_reports",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("grant_application_id", app.models.base.GUID(), nullable=False),
        sa.Column("report_type", sa.String(length=80), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("submitted_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("metrics_summary", sa.Text(), nullable=True),
        sa.Column("artifact_url", sa.String(length=500), nullable=True),
        sa.Column("external_reference", sa.String(length=240), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["grant_application_id"], ["grant_applications.id"], name=op.f("fk_grant_reports_grant_application_id_grant_applications")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_grant_reports_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grant_reports")),
    )
    op.create_index(op.f("ix_grant_reports_due_on"), "grant_reports", ["due_on"])
    op.create_index(op.f("ix_grant_reports_external_reference"), "grant_reports", ["external_reference"])
    op.create_index(op.f("ix_grant_reports_grant_application_id"), "grant_reports", ["grant_application_id"])
    op.create_index(op.f("ix_grant_reports_organization_id"), "grant_reports", ["organization_id"])
    op.create_index(op.f("ix_grant_reports_report_type"), "grant_reports", ["report_type"])
    op.create_index(op.f("ix_grant_reports_status"), "grant_reports", ["status"])
    op.create_index(op.f("ix_grant_reports_submitted_on"), "grant_reports", ["submitted_on"])


def downgrade() -> None:
    op.drop_index(op.f("ix_grant_reports_submitted_on"), table_name="grant_reports")
    op.drop_index(op.f("ix_grant_reports_status"), table_name="grant_reports")
    op.drop_index(op.f("ix_grant_reports_report_type"), table_name="grant_reports")
    op.drop_index(op.f("ix_grant_reports_organization_id"), table_name="grant_reports")
    op.drop_index(op.f("ix_grant_reports_grant_application_id"), table_name="grant_reports")
    op.drop_index(op.f("ix_grant_reports_external_reference"), table_name="grant_reports")
    op.drop_index(op.f("ix_grant_reports_due_on"), table_name="grant_reports")
    op.drop_table("grant_reports")

    op.drop_index(op.f("ix_grant_applications_submitted_on"), table_name="grant_applications")
    op.drop_index(op.f("ix_grant_applications_status"), table_name="grant_applications")
    op.drop_index(op.f("ix_grant_applications_reporting_due_on"), table_name="grant_applications")
    op.drop_index(op.f("ix_grant_applications_project_title"), table_name="grant_applications")
    op.drop_index(op.f("ix_grant_applications_organization_id"), table_name="grant_applications")
    op.drop_index(op.f("ix_grant_applications_lead_person_id"), table_name="grant_applications")
    op.drop_index(op.f("ix_grant_applications_grant_opportunity_id"), table_name="grant_applications")
    op.drop_index(op.f("ix_grant_applications_external_reference"), table_name="grant_applications")
    op.drop_index(op.f("ix_grant_applications_decision_on"), table_name="grant_applications")
    op.drop_table("grant_applications")

    op.drop_index(op.f("ix_grant_opportunities_status"), table_name="grant_opportunities")
    op.drop_index(op.f("ix_grant_opportunities_program_name"), table_name="grant_opportunities")
    op.drop_index(op.f("ix_grant_opportunities_organization_id"), table_name="grant_opportunities")
    op.drop_index(op.f("ix_grant_opportunities_funder_name"), table_name="grant_opportunities")
    op.drop_index(op.f("ix_grant_opportunities_due_on"), table_name="grant_opportunities")
    op.drop_index(op.f("ix_grant_opportunities_category"), table_name="grant_opportunities")
    op.drop_table("grant_opportunities")
