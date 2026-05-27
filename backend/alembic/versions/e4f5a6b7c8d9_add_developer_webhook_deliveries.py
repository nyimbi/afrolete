"""add developer webhook deliveries

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-05-28 05:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "e4f5a6b7c8d9"
down_revision: str | None = "d3e4f5a6b7c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "developer_webhook_deliveries",
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("subscription_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(length=160), nullable=False),
        sa.Column("event_id", sa.String(length=160), nullable=False),
        sa.Column("target_url", sa.String(length=500), nullable=False),
        sa.Column("delivery_mode", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="queued", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["developer_applications.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["subscription_id"], ["developer_webhook_subscriptions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_developer_webhook_deliveries_application_id"),
        "developer_webhook_deliveries",
        ["application_id"],
    )
    op.create_index(
        op.f("ix_developer_webhook_deliveries_delivered_at"),
        "developer_webhook_deliveries",
        ["delivered_at"],
    )
    op.create_index(
        op.f("ix_developer_webhook_deliveries_delivery_mode"),
        "developer_webhook_deliveries",
        ["delivery_mode"],
    )
    op.create_index(op.f("ix_developer_webhook_deliveries_event_id"), "developer_webhook_deliveries", ["event_id"])
    op.create_index(
        op.f("ix_developer_webhook_deliveries_event_type"),
        "developer_webhook_deliveries",
        ["event_type"],
    )
    op.create_index(
        op.f("ix_developer_webhook_deliveries_organization_id"),
        "developer_webhook_deliveries",
        ["organization_id"],
    )
    op.create_index(op.f("ix_developer_webhook_deliveries_status"), "developer_webhook_deliveries", ["status"])
    op.create_index(
        op.f("ix_developer_webhook_deliveries_subscription_id"),
        "developer_webhook_deliveries",
        ["subscription_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_developer_webhook_deliveries_subscription_id"), table_name="developer_webhook_deliveries")
    op.drop_index(op.f("ix_developer_webhook_deliveries_status"), table_name="developer_webhook_deliveries")
    op.drop_index(op.f("ix_developer_webhook_deliveries_organization_id"), table_name="developer_webhook_deliveries")
    op.drop_index(op.f("ix_developer_webhook_deliveries_event_type"), table_name="developer_webhook_deliveries")
    op.drop_index(op.f("ix_developer_webhook_deliveries_event_id"), table_name="developer_webhook_deliveries")
    op.drop_index(op.f("ix_developer_webhook_deliveries_delivery_mode"), table_name="developer_webhook_deliveries")
    op.drop_index(op.f("ix_developer_webhook_deliveries_delivered_at"), table_name="developer_webhook_deliveries")
    op.drop_index(op.f("ix_developer_webhook_deliveries_application_id"), table_name="developer_webhook_deliveries")
    op.drop_table("developer_webhook_deliveries")
