"""add financial aid renewals and appeals

Revision ID: a513b20260531
Revises: a512b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a513b20260531"
down_revision: str | Sequence[str] | None = "a512b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_financial_aid_renewals",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("program_id", GUID(), nullable=False),
        sa.Column("application_id", GUID(), nullable=False),
        sa.Column("member_subscription_id", GUID(), nullable=True),
        sa.Column("requested_by_person_id", GUID(), nullable=True),
        sa.Column("reviewed_by_person_id", GUID(), nullable=True),
        sa.Column("renewal_period_start", sa.Date(), nullable=False),
        sa.Column("renewal_period_end", sa.Date(), nullable=False),
        sa.Column("requested_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("recommended_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("approved_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("amount_applied", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="KES"),
        sa.Column("academic_status", sa.String(80), nullable=True),
        sa.Column("attendance_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("compliance_notes", sa.Text(), nullable=True),
        sa.Column("renewal_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("committee_recommendation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="submitted"),
        sa.Column("submitted_on", sa.Date(), nullable=True),
        sa.Column("decided_on", sa.Date(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["application_id"], ["organization_financial_aid_applications.id"], name=op.f("fk_organization_financial_aid_renewals_application_id_organization_financial_aid_applications")),
        sa.ForeignKeyConstraint(["member_subscription_id"], ["member_subscriptions.id"], name=op.f("fk_organization_financial_aid_renewals_member_subscription_id_member_subscriptions")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_organization_financial_aid_renewals_organization_id_organizations")),
        sa.ForeignKeyConstraint(["program_id"], ["organization_financial_aid_programs.id"], name=op.f("fk_organization_financial_aid_renewals_program_id_organization_financial_aid_programs")),
        sa.ForeignKeyConstraint(["requested_by_person_id"], ["persons.id"], name=op.f("fk_organization_financial_aid_renewals_requested_by_person_id_persons")),
        sa.ForeignKeyConstraint(["reviewed_by_person_id"], ["persons.id"], name=op.f("fk_organization_financial_aid_renewals_reviewed_by_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_financial_aid_renewals")),
    )
    for column in (
        "organization_id",
        "program_id",
        "application_id",
        "member_subscription_id",
        "requested_by_person_id",
        "reviewed_by_person_id",
        "renewal_period_start",
        "renewal_period_end",
        "academic_status",
        "renewal_score",
        "status",
        "submitted_on",
        "decided_on",
    ):
        op.create_index(op.f(f"ix_organization_financial_aid_renewals_{column}"), "organization_financial_aid_renewals", [column])

    op.create_table(
        "organization_financial_aid_appeals",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("program_id", GUID(), nullable=False),
        sa.Column("application_id", GUID(), nullable=False),
        sa.Column("submitted_by_person_id", GUID(), nullable=True),
        sa.Column("resolved_by_person_id", GUID(), nullable=True),
        sa.Column("appeal_reason", sa.Text(), nullable=False),
        sa.Column("requested_outcome", sa.Text(), nullable=True),
        sa.Column("supporting_evidence_ref", sa.String(500), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="pending"),
        sa.Column("submitted_on", sa.Date(), nullable=True),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("resolved_on", sa.Date(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("amount_adjustment", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("final_award_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("amount_applied", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="KES"),
        sa.Column("committee_notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["application_id"], ["organization_financial_aid_applications.id"], name=op.f("fk_organization_financial_aid_appeals_application_id_organization_financial_aid_applications")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_organization_financial_aid_appeals_organization_id_organizations")),
        sa.ForeignKeyConstraint(["program_id"], ["organization_financial_aid_programs.id"], name=op.f("fk_organization_financial_aid_appeals_program_id_organization_financial_aid_programs")),
        sa.ForeignKeyConstraint(["resolved_by_person_id"], ["persons.id"], name=op.f("fk_organization_financial_aid_appeals_resolved_by_person_id_persons")),
        sa.ForeignKeyConstraint(["submitted_by_person_id"], ["persons.id"], name=op.f("fk_organization_financial_aid_appeals_submitted_by_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_financial_aid_appeals")),
    )
    for column in (
        "organization_id",
        "program_id",
        "application_id",
        "submitted_by_person_id",
        "resolved_by_person_id",
        "status",
        "submitted_on",
        "due_on",
        "resolved_on",
    ):
        op.create_index(op.f(f"ix_organization_financial_aid_appeals_{column}"), "organization_financial_aid_appeals", [column])


def downgrade() -> None:
    for column in (
        "resolved_on",
        "due_on",
        "submitted_on",
        "status",
        "resolved_by_person_id",
        "submitted_by_person_id",
        "application_id",
        "program_id",
        "organization_id",
    ):
        op.drop_index(op.f(f"ix_organization_financial_aid_appeals_{column}"), table_name="organization_financial_aid_appeals")
    op.drop_table("organization_financial_aid_appeals")
    for column in (
        "decided_on",
        "submitted_on",
        "status",
        "renewal_score",
        "academic_status",
        "renewal_period_end",
        "renewal_period_start",
        "reviewed_by_person_id",
        "requested_by_person_id",
        "member_subscription_id",
        "application_id",
        "program_id",
        "organization_id",
    ):
        op.drop_index(op.f(f"ix_organization_financial_aid_renewals_{column}"), table_name="organization_financial_aid_renewals")
    op.drop_table("organization_financial_aid_renewals")
