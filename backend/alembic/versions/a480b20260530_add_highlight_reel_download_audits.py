"""add highlight reel download audits

Revision ID: a480b20260530
Revises: a479b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a480b20260530"
down_revision: str | Sequence[str] | None = "a479b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_highlight_reel_download_audits",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("highlight_reel_id", GUID(), nullable=False),
        sa.Column("highlight_reel_export_id", GUID(), nullable=False),
        sa.Column("message_id", GUID(), nullable=False),
        sa.Column("message_recipient_id", GUID(), nullable=False),
        sa.Column("person_id", GUID(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["highlight_reel_export_id"], ["performance_highlight_reel_exports.id"]),
        sa.ForeignKeyConstraint(["highlight_reel_id"], ["performance_highlight_reels.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["communication_messages.id"]),
        sa.ForeignKeyConstraint(["message_recipient_id"], ["message_recipients.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_highlight_reel_download_audits")),
    )
    for column in [
        "organization_id",
        "highlight_reel_id",
        "highlight_reel_export_id",
        "message_id",
        "message_recipient_id",
        "person_id",
        "checksum",
        "downloaded_at",
    ]:
        op.create_index(
            op.f(f"ix_performance_highlight_reel_download_audits_{column}"),
            "performance_highlight_reel_download_audits",
            [column],
        )


def downgrade() -> None:
    for column in [
        "downloaded_at",
        "checksum",
        "person_id",
        "message_recipient_id",
        "message_id",
        "highlight_reel_export_id",
        "highlight_reel_id",
        "organization_id",
    ]:
        op.drop_index(
            op.f(f"ix_performance_highlight_reel_download_audits_{column}"),
            table_name="performance_highlight_reel_download_audits",
        )
    op.drop_table("performance_highlight_reel_download_audits")
