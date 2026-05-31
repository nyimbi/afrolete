"""add grant award records

Revision ID: a501b20260531
Revises: a500b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a501b20260531"
down_revision: str | Sequence[str] | None = "a500b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grant_award_records",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("grant_application_id", GUID(), nullable=False),
        sa.Column("record_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("occurred_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("requirement", sa.Text(), nullable=True),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("external_reference", sa.String(length=240), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["grant_application_id"],
            ["grant_applications.id"],
            name=op.f("fk_grant_award_records_grant_application_id_grant_applications"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_grant_award_records_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grant_award_records")),
    )
    for column in (
        "category",
        "due_on",
        "external_reference",
        "grant_application_id",
        "occurred_on",
        "organization_id",
        "record_type",
        "status",
        "title",
    ):
        op.create_index(op.f(f"ix_grant_award_records_{column}"), "grant_award_records", [column])


def downgrade() -> None:
    for column in (
        "title",
        "status",
        "record_type",
        "organization_id",
        "occurred_on",
        "grant_application_id",
        "external_reference",
        "due_on",
        "category",
    ):
        op.drop_index(op.f(f"ix_grant_award_records_{column}"), table_name="grant_award_records")
    op.drop_table("grant_award_records")
