"""add sponsor stewardship

Revision ID: a445b20260530
Revises: a443b20260530
Create Date: 2026-05-30 07:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a445b20260530"
down_revision: str | None = "a443b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sponsorship_deliverable_milestones",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("sponsor_id", app.models.base.GUID(), nullable=False),
        sa.Column("sponsorship_agreement_id", app.models.base.GUID(), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("deliverable_type", sa.String(length=80), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("completed_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("owner_name", sa.String(length=180), nullable=True),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_sponsorship_deliverable_milestones_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["sponsor_id"],
            ["sponsors.id"],
            name=op.f("fk_sponsorship_deliverable_milestones_sponsor_id_sponsors"),
        ),
        sa.ForeignKeyConstraint(
            ["sponsorship_agreement_id"],
            ["sponsorship_agreements.id"],
            name=op.f("fk_sponsorship_deliverable_milestones_sponsorship_agreement_id_sponsorship_agreements"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sponsorship_deliverable_milestones")),
    )
    op.create_index(op.f("ix_sponsorship_deliverable_milestones_completed_on"), "sponsorship_deliverable_milestones", ["completed_on"])
    op.create_index(op.f("ix_sponsorship_deliverable_milestones_deliverable_type"), "sponsorship_deliverable_milestones", ["deliverable_type"])
    op.create_index(op.f("ix_sponsorship_deliverable_milestones_due_on"), "sponsorship_deliverable_milestones", ["due_on"])
    op.create_index(op.f("ix_sponsorship_deliverable_milestones_organization_id"), "sponsorship_deliverable_milestones", ["organization_id"])
    op.create_index(op.f("ix_sponsorship_deliverable_milestones_owner_name"), "sponsorship_deliverable_milestones", ["owner_name"])
    op.create_index(op.f("ix_sponsorship_deliverable_milestones_sponsor_id"), "sponsorship_deliverable_milestones", ["sponsor_id"])
    op.create_index(op.f("ix_sponsorship_deliverable_milestones_sponsorship_agreement_id"), "sponsorship_deliverable_milestones", ["sponsorship_agreement_id"])
    op.create_index(op.f("ix_sponsorship_deliverable_milestones_status"), "sponsorship_deliverable_milestones", ["status"])
    op.create_index(op.f("ix_sponsorship_deliverable_milestones_title"), "sponsorship_deliverable_milestones", ["title"])

    op.create_table(
        "sponsor_interaction_logs",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("sponsor_id", app.models.base.GUID(), nullable=False),
        sa.Column("sponsorship_agreement_id", app.models.base.GUID(), nullable=True),
        sa.Column("contact_name", sa.String(length=180), nullable=False),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("interaction_type", sa.String(length=80), nullable=False),
        sa.Column("subject", sa.String(length=220), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("sentiment", sa.String(length=40), nullable=False),
        sa.Column("follow_up_on", sa.Date(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_sponsor_interaction_logs_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["sponsor_id"],
            ["sponsors.id"],
            name=op.f("fk_sponsor_interaction_logs_sponsor_id_sponsors"),
        ),
        sa.ForeignKeyConstraint(
            ["sponsorship_agreement_id"],
            ["sponsorship_agreements.id"],
            name=op.f("fk_sponsor_interaction_logs_sponsorship_agreement_id_sponsorship_agreements"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sponsor_interaction_logs")),
    )
    op.create_index(op.f("ix_sponsor_interaction_logs_contact_email"), "sponsor_interaction_logs", ["contact_email"])
    op.create_index(op.f("ix_sponsor_interaction_logs_contact_name"), "sponsor_interaction_logs", ["contact_name"])
    op.create_index(op.f("ix_sponsor_interaction_logs_follow_up_on"), "sponsor_interaction_logs", ["follow_up_on"])
    op.create_index(op.f("ix_sponsor_interaction_logs_interaction_type"), "sponsor_interaction_logs", ["interaction_type"])
    op.create_index(op.f("ix_sponsor_interaction_logs_occurred_at"), "sponsor_interaction_logs", ["occurred_at"])
    op.create_index(op.f("ix_sponsor_interaction_logs_organization_id"), "sponsor_interaction_logs", ["organization_id"])
    op.create_index(op.f("ix_sponsor_interaction_logs_sentiment"), "sponsor_interaction_logs", ["sentiment"])
    op.create_index(op.f("ix_sponsor_interaction_logs_sponsor_id"), "sponsor_interaction_logs", ["sponsor_id"])
    op.create_index(op.f("ix_sponsor_interaction_logs_sponsorship_agreement_id"), "sponsor_interaction_logs", ["sponsorship_agreement_id"])
    op.create_index(op.f("ix_sponsor_interaction_logs_subject"), "sponsor_interaction_logs", ["subject"])


def downgrade() -> None:
    op.drop_index(op.f("ix_sponsor_interaction_logs_subject"), table_name="sponsor_interaction_logs")
    op.drop_index(op.f("ix_sponsor_interaction_logs_sponsorship_agreement_id"), table_name="sponsor_interaction_logs")
    op.drop_index(op.f("ix_sponsor_interaction_logs_sponsor_id"), table_name="sponsor_interaction_logs")
    op.drop_index(op.f("ix_sponsor_interaction_logs_sentiment"), table_name="sponsor_interaction_logs")
    op.drop_index(op.f("ix_sponsor_interaction_logs_organization_id"), table_name="sponsor_interaction_logs")
    op.drop_index(op.f("ix_sponsor_interaction_logs_occurred_at"), table_name="sponsor_interaction_logs")
    op.drop_index(op.f("ix_sponsor_interaction_logs_interaction_type"), table_name="sponsor_interaction_logs")
    op.drop_index(op.f("ix_sponsor_interaction_logs_follow_up_on"), table_name="sponsor_interaction_logs")
    op.drop_index(op.f("ix_sponsor_interaction_logs_contact_name"), table_name="sponsor_interaction_logs")
    op.drop_index(op.f("ix_sponsor_interaction_logs_contact_email"), table_name="sponsor_interaction_logs")
    op.drop_table("sponsor_interaction_logs")

    op.drop_index(op.f("ix_sponsorship_deliverable_milestones_title"), table_name="sponsorship_deliverable_milestones")
    op.drop_index(op.f("ix_sponsorship_deliverable_milestones_status"), table_name="sponsorship_deliverable_milestones")
    op.drop_index(op.f("ix_sponsorship_deliverable_milestones_sponsorship_agreement_id"), table_name="sponsorship_deliverable_milestones")
    op.drop_index(op.f("ix_sponsorship_deliverable_milestones_sponsor_id"), table_name="sponsorship_deliverable_milestones")
    op.drop_index(op.f("ix_sponsorship_deliverable_milestones_owner_name"), table_name="sponsorship_deliverable_milestones")
    op.drop_index(op.f("ix_sponsorship_deliverable_milestones_organization_id"), table_name="sponsorship_deliverable_milestones")
    op.drop_index(op.f("ix_sponsorship_deliverable_milestones_due_on"), table_name="sponsorship_deliverable_milestones")
    op.drop_index(op.f("ix_sponsorship_deliverable_milestones_deliverable_type"), table_name="sponsorship_deliverable_milestones")
    op.drop_index(op.f("ix_sponsorship_deliverable_milestones_completed_on"), table_name="sponsorship_deliverable_milestones")
    op.drop_table("sponsorship_deliverable_milestones")
