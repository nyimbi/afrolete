"""add developer oauth refresh tokens

Revision ID: a9b0c1d2e3f4
Revises: f8a9b0c1d2e3
Create Date: 2026-05-28 07:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "a9b0c1d2e3f4"
down_revision: str | None = "f8a9b0c1d2e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("developer_api_keys", sa.Column("refresh_token_hash", sa.String(length=64), nullable=True))
    op.add_column("developer_api_keys", sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("developer_api_keys", sa.Column("refresh_rotated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint(
        op.f("uq_developer_api_keys_refresh_token_hash"),
        "developer_api_keys",
        ["refresh_token_hash"],
    )
    op.create_index(op.f("ix_developer_api_keys_refresh_expires_at"), "developer_api_keys", ["refresh_expires_at"])
    op.create_index(op.f("ix_developer_api_keys_refresh_rotated_at"), "developer_api_keys", ["refresh_rotated_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_developer_api_keys_refresh_rotated_at"), table_name="developer_api_keys")
    op.drop_index(op.f("ix_developer_api_keys_refresh_expires_at"), table_name="developer_api_keys")
    op.drop_constraint(op.f("uq_developer_api_keys_refresh_token_hash"), "developer_api_keys", type_="unique")
    op.drop_column("developer_api_keys", "refresh_rotated_at")
    op.drop_column("developer_api_keys", "refresh_expires_at")
    op.drop_column("developer_api_keys", "refresh_token_hash")
