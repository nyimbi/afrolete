"""add grant submission packages

Revision ID: a500b20260531
Revises: a499b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a500b20260531"
down_revision: str | Sequence[str] | None = "a499b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grant_submission_packages",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("grant_application_id", GUID(), nullable=False),
        sa.Column("package_name", sa.String(length=220), nullable=False),
        sa.Column("submission_method", sa.String(length=80), nullable=False),
        sa.Column("portal_url", sa.String(length=500), nullable=True),
        sa.Column("checklist_json", sa.Text(), nullable=False),
        sa.Column("completed_checklist_json", sa.Text(), nullable=False),
        sa.Column("document_manifest_json", sa.Text(), nullable=False),
        sa.Column("prepared_by_name", sa.String(length=180), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("confirmation_reference", sa.String(length=240), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blockers_json", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["grant_application_id"],
            ["grant_applications.id"],
            name=op.f("fk_grant_submission_packages_grant_application_id_grant_applications"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_grant_submission_packages_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grant_submission_packages")),
        sa.UniqueConstraint(
            "organization_id",
            "grant_application_id",
            "package_name",
            name="uq_grant_submission_packages_name",
        ),
    )
    for column in (
        "confirmation_reference",
        "confirmed_at",
        "grant_application_id",
        "organization_id",
        "package_name",
        "prepared_by_name",
        "status",
        "submission_method",
        "submitted_at",
    ):
        op.create_index(op.f(f"ix_grant_submission_packages_{column}"), "grant_submission_packages", [column])


def downgrade() -> None:
    for column in (
        "submitted_at",
        "submission_method",
        "status",
        "prepared_by_name",
        "package_name",
        "organization_id",
        "grant_application_id",
        "confirmed_at",
        "confirmation_reference",
    ):
        op.drop_index(op.f(f"ix_grant_submission_packages_{column}"), table_name="grant_submission_packages")
    op.drop_table("grant_submission_packages")
