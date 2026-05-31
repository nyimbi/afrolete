"""add member dues payment callbacks

Revision ID: a521b20260531
Revises: a520b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a521b20260531"
down_revision: str | Sequence[str] | None = "a520b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "member_dues_payment_callbacks",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("collection_rail_id", GUID(), nullable=True),
        sa.Column("subscription_id", GUID(), nullable=True),
        sa.Column("payment_id", GUID(), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("external_payment_id", sa.String(length=180), nullable=True),
        sa.Column("dues_reference", sa.String(length=180), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("method", sa.String(length=80), nullable=True),
        sa.Column("payer_phone", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("duplicate", sa.Boolean(), nullable=False),
        sa.Column("signature_required", sa.Boolean(), nullable=False),
        sa.Column("signature_validated", sa.Boolean(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("raw_payload_json", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_rail_id"],
            ["member_dues_collection_rails.id"],
            name=op.f("fk_member_dues_payment_callbacks_collection_rail_id_member_dues_collection_rails"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_member_dues_payment_callbacks_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["member_subscription_payments.id"],
            name=op.f("fk_member_dues_payment_callbacks_payment_id_member_subscription_payments"),
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["member_subscriptions.id"],
            name=op.f("fk_member_dues_payment_callbacks_subscription_id_member_subscriptions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_dues_payment_callbacks")),
        sa.UniqueConstraint(
            "organization_id",
            "provider",
            "external_payment_id",
            name="uq_member_dues_payment_callbacks_provider_payment",
        ),
    )
    for column in [
        "organization_id",
        "collection_rail_id",
        "subscription_id",
        "payment_id",
        "provider",
        "event_type",
        "external_payment_id",
        "dues_reference",
        "currency",
        "method",
        "payer_phone",
        "status",
        "accepted",
        "duplicate",
        "received_at",
    ]:
        op.create_index(op.f(f"ix_member_dues_payment_callbacks_{column}"), "member_dues_payment_callbacks", [column])


def downgrade() -> None:
    for column in [
        "received_at",
        "duplicate",
        "accepted",
        "status",
        "payer_phone",
        "method",
        "currency",
        "dues_reference",
        "external_payment_id",
        "event_type",
        "provider",
        "payment_id",
        "subscription_id",
        "collection_rail_id",
        "organization_id",
    ]:
        op.drop_index(op.f(f"ix_member_dues_payment_callbacks_{column}"), table_name="member_dues_payment_callbacks")
    op.drop_table("member_dues_payment_callbacks")
