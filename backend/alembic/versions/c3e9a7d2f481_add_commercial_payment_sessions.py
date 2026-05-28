"""add commercial payment sessions

Revision ID: c3e9a7d2f481
Revises: a2f6d8c4b9e1
Create Date: 2026-05-28 19:25:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "c3e9a7d2f481"
down_revision: str | None = "a2f6d8c4b9e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "commercial_payment_sessions",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("invoice_id", app.models.base.GUID(), nullable=False),
        sa.Column("sponsor_id", app.models.base.GUID(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("mode", sa.String(length=40), nullable=False, server_default="local"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="local_ready"),
        sa.Column("provider_session_id", sa.String(length=180), nullable=False),
        sa.Column("local_session_id", sa.String(length=180), nullable=False),
        sa.Column("client_reference", sa.String(length=240), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("redirect_url", sa.String(length=1000), nullable=False),
        sa.Column("success_url", sa.String(length=800), nullable=True),
        sa.Column("cancel_url", sa.String(length=800), nullable=True),
        sa.Column("customer_email", sa.String(length=320), nullable=True),
        sa.Column("payment_method", sa.String(length=80), nullable=False, server_default="card"),
        sa.Column("webhook_configured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_status_code", sa.Integer(), nullable=True),
        sa.Column("provider_response", sa.Text(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["finance_invoices.id"], name=op.f("fk_commercial_payment_sessions_invoice_id_finance_invoices")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_commercial_payment_sessions_organization_id_organizations")),
        sa.ForeignKeyConstraint(["sponsor_id"], ["sponsors.id"], name=op.f("fk_commercial_payment_sessions_sponsor_id_sponsors")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_commercial_payment_sessions")),
        sa.UniqueConstraint("organization_id", "provider", "local_session_id", name=op.f("uq_commercial_payment_sessions_organization_id")),
    )
    for column in [
        "client_reference",
        "customer_email",
        "invoice_id",
        "local_session_id",
        "mode",
        "organization_id",
        "payment_method",
        "provider",
        "provider_session_id",
        "sponsor_id",
        "status",
        "webhook_configured",
    ]:
        op.create_index(op.f(f"ix_commercial_payment_sessions_{column}"), "commercial_payment_sessions", [column], unique=False)


def downgrade() -> None:
    for column in [
        "webhook_configured",
        "status",
        "sponsor_id",
        "provider_session_id",
        "provider",
        "payment_method",
        "organization_id",
        "mode",
        "local_session_id",
        "invoice_id",
        "customer_email",
        "client_reference",
    ]:
        op.drop_index(op.f(f"ix_commercial_payment_sessions_{column}"), table_name="commercial_payment_sessions")
    op.drop_table("commercial_payment_sessions")
