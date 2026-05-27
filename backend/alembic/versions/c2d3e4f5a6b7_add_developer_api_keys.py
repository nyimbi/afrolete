"""add developer api keys

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f6a7
Create Date: 2026-05-28 04:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "c2d3e4f5a6b7"
down_revision: str | None = "b1c2d3e4f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "developer_api_keys",
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("key_prefix", sa.String(length=120), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("scopes", sa.Text(), server_default="", nullable=False),
        sa.Column("environment", sa.String(length=40), server_default="sandbox", nullable=False),
        sa.Column("status", sa.String(length=40), server_default="active", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_ip", sa.String(length=80), nullable=True),
        sa.Column("usage_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rate_limit_per_minute", sa.Integer(), server_default="60", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["developer_applications.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id", "name"),
        sa.UniqueConstraint("key_prefix"),
    )
    op.create_index(op.f("ix_developer_api_keys_application_id"), "developer_api_keys", ["application_id"])
    op.create_index(op.f("ix_developer_api_keys_environment"), "developer_api_keys", ["environment"])
    op.create_index(op.f("ix_developer_api_keys_expires_at"), "developer_api_keys", ["expires_at"])
    op.create_index(op.f("ix_developer_api_keys_key_prefix"), "developer_api_keys", ["key_prefix"])
    op.create_index(op.f("ix_developer_api_keys_last_used_at"), "developer_api_keys", ["last_used_at"])
    op.create_index(op.f("ix_developer_api_keys_name"), "developer_api_keys", ["name"])
    op.create_index(op.f("ix_developer_api_keys_organization_id"), "developer_api_keys", ["organization_id"])
    op.create_index(op.f("ix_developer_api_keys_status"), "developer_api_keys", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_developer_api_keys_status"), table_name="developer_api_keys")
    op.drop_index(op.f("ix_developer_api_keys_organization_id"), table_name="developer_api_keys")
    op.drop_index(op.f("ix_developer_api_keys_name"), table_name="developer_api_keys")
    op.drop_index(op.f("ix_developer_api_keys_last_used_at"), table_name="developer_api_keys")
    op.drop_index(op.f("ix_developer_api_keys_key_prefix"), table_name="developer_api_keys")
    op.drop_index(op.f("ix_developer_api_keys_expires_at"), table_name="developer_api_keys")
    op.drop_index(op.f("ix_developer_api_keys_environment"), table_name="developer_api_keys")
    op.drop_index(op.f("ix_developer_api_keys_application_id"), table_name="developer_api_keys")
    op.drop_table("developer_api_keys")
