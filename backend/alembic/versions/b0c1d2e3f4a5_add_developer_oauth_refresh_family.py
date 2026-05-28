"""add developer oauth refresh family

Revision ID: b0c1d2e3f4a5
Revises: a9b0c1d2e3f4
Create Date: 2026-05-28 07:30:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "b0c1d2e3f4a5"
down_revision: str | None = "a9b0c1d2e3f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("developer_api_keys", sa.Column("refresh_token_family_id", app.models.base.GUID(), nullable=True))
    op.add_column("developer_api_keys", sa.Column("refresh_parent_key_id", app.models.base.GUID(), nullable=True))
    op.add_column("developer_api_keys", sa.Column("refresh_reused_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        op.f("fk_developer_api_keys_refresh_parent_key_id_developer_api_keys"),
        "developer_api_keys",
        "developer_api_keys",
        ["refresh_parent_key_id"],
        ["id"],
    )
    op.create_index(op.f("ix_developer_api_keys_refresh_token_family_id"), "developer_api_keys", ["refresh_token_family_id"])
    op.create_index(op.f("ix_developer_api_keys_refresh_parent_key_id"), "developer_api_keys", ["refresh_parent_key_id"])
    op.create_index(op.f("ix_developer_api_keys_refresh_reused_at"), "developer_api_keys", ["refresh_reused_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_developer_api_keys_refresh_reused_at"), table_name="developer_api_keys")
    op.drop_index(op.f("ix_developer_api_keys_refresh_parent_key_id"), table_name="developer_api_keys")
    op.drop_index(op.f("ix_developer_api_keys_refresh_token_family_id"), table_name="developer_api_keys")
    op.drop_constraint(
        op.f("fk_developer_api_keys_refresh_parent_key_id_developer_api_keys"),
        "developer_api_keys",
        type_="foreignkey",
    )
    op.drop_column("developer_api_keys", "refresh_reused_at")
    op.drop_column("developer_api_keys", "refresh_parent_key_id")
    op.drop_column("developer_api_keys", "refresh_token_family_id")
