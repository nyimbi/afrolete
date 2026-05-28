"""add commercial settlement payouts

Revision ID: a2f6d8c4b9e1
Revises: f18c2a9d7b64
Create Date: 2026-05-28 19:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a2f6d8c4b9e1"
down_revision: str | None = "f18c2a9d7b64"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "commercial_settlement_payouts",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("payout_reference", sa.String(length=180), nullable=False),
        sa.Column("payout_batch_reference", sa.String(length=180), nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="prepared"),
        sa.Column("delivery_mode", sa.String(length=40), nullable=False, server_default="record_only"),
        sa.Column("delivery_attempted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("delivered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("gross_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("fee_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("net_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_count", sa.Integer(), nullable=False),
        sa.Column("destination", sa.String(length=500), nullable=True),
        sa.Column("provider_status_code", sa.Integer(), nullable=True),
        sa.Column("provider_response", sa.Text(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("processed_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_event_id", sa.String(length=180), nullable=True),
        sa.Column("callback_payload", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_commercial_settlement_payouts_organization_id_organizations")),
        sa.ForeignKeyConstraint(["processed_by_person_id"], ["persons.id"], name=op.f("fk_commercial_settlement_payouts_processed_by_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_commercial_settlement_payouts")),
        sa.UniqueConstraint("organization_id", "provider", "payout_batch_reference", name=op.f("uq_commercial_settlement_payouts_organization_id")),
    )
    for column in [
        "delivered",
        "delivery_attempted",
        "delivery_mode",
        "executed_at",
        "external_event_id",
        "idempotency_key",
        "organization_id",
        "payout_batch_reference",
        "payout_reference",
        "processed_by_person_id",
        "provider",
        "reconciled_at",
        "status",
    ]:
        op.create_index(op.f(f"ix_commercial_settlement_payouts_{column}"), "commercial_settlement_payouts", [column], unique=False)


def downgrade() -> None:
    for column in [
        "status",
        "reconciled_at",
        "provider",
        "processed_by_person_id",
        "payout_reference",
        "payout_batch_reference",
        "organization_id",
        "idempotency_key",
        "external_event_id",
        "executed_at",
        "delivery_mode",
        "delivery_attempted",
        "delivered",
    ]:
        op.drop_index(op.f(f"ix_commercial_settlement_payouts_{column}"), table_name="commercial_settlement_payouts")
    op.drop_table("commercial_settlement_payouts")
