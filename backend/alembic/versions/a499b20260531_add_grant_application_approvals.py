"""add grant application approvals

Revision ID: a499b20260531
Revises: a498b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a499b20260531"
down_revision: str | Sequence[str] | None = "a498b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grant_application_approvals",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("grant_application_id", GUID(), nullable=False),
        sa.Column("approval_level", sa.String(length=80), nullable=False),
        sa.Column("reviewer_name", sa.String(length=180), nullable=False),
        sa.Column("reviewer_email", sa.String(length=320), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("request_notes", sa.Text(), nullable=True),
        sa.Column("decision_notes", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["grant_application_id"], ["grant_applications.id"], name=op.f("fk_grant_application_approvals_grant_application_id_grant_applications")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_grant_application_approvals_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grant_application_approvals")),
        sa.UniqueConstraint("grant_application_id", "approval_level", name="uq_grant_application_approvals_level"),
    )
    for column in (
        "approval_level",
        "decided_at",
        "grant_application_id",
        "organization_id",
        "requested_at",
        "reviewer_email",
        "reviewer_name",
        "status",
    ):
        op.create_index(op.f(f"ix_grant_application_approvals_{column}"), "grant_application_approvals", [column], unique=False)


def downgrade() -> None:
    for column in (
        "status",
        "reviewer_name",
        "reviewer_email",
        "requested_at",
        "organization_id",
        "grant_application_id",
        "decided_at",
        "approval_level",
    ):
        op.drop_index(op.f(f"ix_grant_application_approvals_{column}"), table_name="grant_application_approvals")
    op.drop_table("grant_application_approvals")
