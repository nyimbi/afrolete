"""add developer oauth pkce fields

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-05-28 06:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "f8a9b0c1d2e3"
down_revision: str | None = "e7f8a9b0c1d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "developer_oauth_authorizations",
        sa.Column("code_challenge", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "developer_oauth_authorizations",
        sa.Column("code_challenge_method", sa.String(length=16), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("developer_oauth_authorizations", "code_challenge_method")
    op.drop_column("developer_oauth_authorizations", "code_challenge")
