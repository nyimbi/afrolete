"""add background check evidence documents

Revision ID: d5f7a9c1e3f
Revises: c4e6f8a0b2d3
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "d5f7a9c1e3f"
down_revision: str | None = "c4e6f8a0b2d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "background_check_evidence_documents",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("background_check_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=False),
        sa.Column("uploaded_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("reviewed_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("filename", sa.String(length=240), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("review_status", sa.String(length=40), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=800), nullable=False),
        sa.Column("evidence_url", sa.String(length=1000), nullable=False),
        sa.Column("provider_reference", sa.String(length=240), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["background_check_id"],
            ["background_checks.id"],
            name=op.f("fk_background_check_evidence_documents_background_check_id_background_checks"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_background_check_evidence_documents_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["persons.id"],
            name=op.f("fk_background_check_evidence_documents_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_person_id"],
            ["persons.id"],
            name=op.f("fk_background_check_evidence_documents_reviewed_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_person_id"],
            ["persons.id"],
            name=op.f("fk_background_check_evidence_documents_uploaded_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_background_check_evidence_documents")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_background_check_evidence_documents_storage_key")),
    )
    for column in [
        "background_check_id",
        "checksum",
        "document_type",
        "filename",
        "organization_id",
        "person_id",
        "provider_reference",
        "review_status",
        "reviewed_at",
        "reviewed_by_person_id",
        "storage_key",
        "uploaded_by_person_id",
    ]:
        op.create_index(
            op.f(f"ix_background_check_evidence_documents_{column}"),
            "background_check_evidence_documents",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "uploaded_by_person_id",
        "storage_key",
        "reviewed_by_person_id",
        "reviewed_at",
        "review_status",
        "provider_reference",
        "person_id",
        "organization_id",
        "filename",
        "document_type",
        "checksum",
        "background_check_id",
    ]:
        op.drop_index(op.f(f"ix_background_check_evidence_documents_{column}"), table_name="background_check_evidence_documents")
    op.drop_table("background_check_evidence_documents")
