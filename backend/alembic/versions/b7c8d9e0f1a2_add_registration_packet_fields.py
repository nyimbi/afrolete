"""add registration packet fields

Revision ID: b7c8d9e0f1a2
Revises: fa2b3c4d5e6a
Create Date: 2026-05-29 22:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "b7c8d9e0f1a2"
down_revision: str | None = "fa2b3c4d5e6a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("registration_inquiries", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("registration_inquiries", sa.Column("emergency_contact_name", sa.String(length=240), nullable=True))
    op.add_column("registration_inquiries", sa.Column("emergency_contact_phone", sa.String(length=64), nullable=True))
    op.add_column("registration_inquiries", sa.Column("medical_notes", sa.Text(), nullable=True))
    op.add_column("registration_inquiries", sa.Column("consent_signer_name", sa.String(length=240), nullable=True))
    op.add_column(
        "registration_inquiries",
        sa.Column("guardian_consent_acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "registration_inquiries",
        sa.Column("privacy_acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("registration_inquiries", sa.Column("required_documents_json", sa.Text(), nullable=True))
    op.add_column("registration_inquiries", sa.Column("submitted_documents_json", sa.Text(), nullable=True))
    op.add_column("registration_inquiries", sa.Column("payment_amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("registration_inquiries", sa.Column("payment_currency", sa.String(length=3), nullable=True))
    op.add_column("registration_inquiries", sa.Column("payment_method", sa.String(length=80), nullable=True))
    op.add_column("registration_inquiries", sa.Column("payment_reference", sa.String(length=240), nullable=True))
    op.add_column(
        "registration_inquiries",
        sa.Column("payment_status", sa.String(length=40), server_default="not_required", nullable=False),
    )
    op.add_column(
        "registration_inquiries",
        sa.Column("verification_status", sa.String(length=40), server_default="inquiry", nullable=False),
    )
    op.add_column(
        "registration_inquiries",
        sa.Column("packet_submitted_at", sa.DateTime(timezone=True), nullable=True),
    )

    for column in [
        "date_of_birth",
        "guardian_consent_acknowledged_at",
        "packet_submitted_at",
        "payment_reference",
        "payment_status",
        "privacy_acknowledged_at",
        "verification_status",
    ]:
        op.create_index(
            op.f(f"ix_registration_inquiries_{column}"),
            "registration_inquiries",
            [column],
        )


def downgrade() -> None:
    for column in [
        "verification_status",
        "privacy_acknowledged_at",
        "payment_status",
        "payment_reference",
        "packet_submitted_at",
        "guardian_consent_acknowledged_at",
        "date_of_birth",
    ]:
        op.drop_index(op.f(f"ix_registration_inquiries_{column}"), table_name="registration_inquiries")

    for column in [
        "packet_submitted_at",
        "verification_status",
        "payment_status",
        "payment_reference",
        "payment_method",
        "payment_currency",
        "payment_amount",
        "submitted_documents_json",
        "required_documents_json",
        "privacy_acknowledged_at",
        "guardian_consent_acknowledged_at",
        "consent_signer_name",
        "medical_notes",
        "emergency_contact_phone",
        "emergency_contact_name",
        "date_of_birth",
    ]:
        op.drop_column("registration_inquiries", column)
