"""add developer oauth authorizations

Revision ID: e7f8a9b0c1d2
Revises: e4f5a6b7c8d9
Create Date: 2026-05-28 06:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "e7f8a9b0c1d2"
down_revision: str | None = "e4f5a6b7c8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "developer_oauth_authorizations",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("application_id", app.models.base.GUID(), nullable=False),
        sa.Column("user_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("redirect_uri", sa.String(length=500), nullable=False),
        sa.Column("requested_scopes", sa.Text(), nullable=False),
        sa.Column("granted_scopes", sa.Text(), nullable=False),
        sa.Column("state", sa.String(length=500), nullable=True),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="granted", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["developer_applications.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code_hash"),
    )
    for column in [
        "application_id",
        "consented_at",
        "expires_at",
        "organization_id",
        "redeemed_at",
        "status",
        "user_person_id",
    ]:
        op.create_index(
            op.f(f"ix_developer_oauth_authorizations_{column}"),
            "developer_oauth_authorizations",
            [column],
        )


def downgrade() -> None:
    for column in [
        "user_person_id",
        "status",
        "redeemed_at",
        "organization_id",
        "expires_at",
        "consented_at",
        "application_id",
    ]:
        op.drop_index(op.f(f"ix_developer_oauth_authorizations_{column}"), table_name="developer_oauth_authorizations")
    op.drop_table("developer_oauth_authorizations")
