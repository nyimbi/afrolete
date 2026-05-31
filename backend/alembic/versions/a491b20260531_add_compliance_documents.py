"""add compliance documents

Revision ID: a491b20260531
Revises: a490b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.models.base import GUID


revision: str = "a491b20260531"
down_revision: str | None = "a490b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


DOCUMENT_INDEXES = [
    "organization_id",
    "title",
    "category",
    "document_type",
    "subject_type",
    "subject_id",
    "owner_person_id",
    "issuer",
    "reference_number",
    "status",
    "renewal_status",
    "effective_on",
    "expires_on",
    "next_review_on",
    "retention_until",
    "auto_renewal_enabled",
    "checksum",
    "confidentiality",
]

VERSION_INDEXES = [
    "organization_id",
    "document_id",
    "version_number",
    "checksum",
    "uploaded_by_person_id",
    "verified_by_person_id",
    "verified_at",
    "status",
]


def create_indexes(table_name: str, columns: list[str]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table_name}_{column}"), table_name, [column])


def drop_indexes(table_name: str, columns: list[str]) -> None:
    for column in reversed(columns):
        op.drop_index(op.f(f"ix_{table_name}_{column}"), table_name=table_name)


def upgrade() -> None:
    op.create_table(
        "organization_compliance_documents",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("document_type", sa.String(length=120), nullable=False),
        sa.Column("subject_type", sa.String(length=80), nullable=True),
        sa.Column("subject_id", GUID(), nullable=True),
        sa.Column("owner_person_id", GUID(), nullable=True),
        sa.Column("issuer", sa.String(length=180), nullable=True),
        sa.Column("reference_number", sa.String(length=180), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("renewal_status", sa.String(length=40), nullable=False),
        sa.Column("effective_on", sa.Date(), nullable=True),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("next_review_on", sa.Date(), nullable=True),
        sa.Column("retention_until", sa.Date(), nullable=True),
        sa.Column("auto_renewal_enabled", sa.Boolean(), nullable=False),
        sa.Column("storage_url", sa.String(length=500), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("confidentiality", sa.String(length=40), nullable=False),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_compliance_documents_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_person_id"],
            ["persons.id"],
            name=op.f("fk_organization_compliance_documents_owner_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_compliance_documents")),
        sa.UniqueConstraint(
            "organization_id",
            "title",
            "document_type",
            name=op.f("uq_organization_compliance_documents_organization_id"),
        ),
    )
    create_indexes("organization_compliance_documents", DOCUMENT_INDEXES)

    op.create_table(
        "organization_compliance_document_versions",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("document_id", GUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("storage_url", sa.String(length=500), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("filename", sa.String(length=240), nullable=True),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("uploaded_by_person_id", GUID(), nullable=True),
        sa.Column("verified_by_person_id", GUID(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_compliance_document_versions_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["organization_compliance_documents.id"],
            name=op.f("fk_organization_compliance_document_versions_document_id_organization_compliance_documents"),
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_person_id"],
            ["persons.id"],
            name=op.f("fk_organization_compliance_document_versions_uploaded_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["verified_by_person_id"],
            ["persons.id"],
            name=op.f("fk_organization_compliance_document_versions_verified_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_compliance_document_versions")),
        sa.UniqueConstraint(
            "document_id",
            "version_number",
            name=op.f("uq_organization_compliance_document_versions_document_id"),
        ),
    )
    create_indexes("organization_compliance_document_versions", VERSION_INDEXES)


def downgrade() -> None:
    drop_indexes("organization_compliance_document_versions", VERSION_INDEXES)
    op.drop_table("organization_compliance_document_versions")
    drop_indexes("organization_compliance_documents", DOCUMENT_INDEXES)
    op.drop_table("organization_compliance_documents")
