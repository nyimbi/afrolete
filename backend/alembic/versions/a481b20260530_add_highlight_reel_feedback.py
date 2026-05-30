"""add highlight reel feedback

Revision ID: a481b20260530
Revises: a480b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a481b20260530"
down_revision: str | Sequence[str] | None = "a480b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_highlight_reel_feedback",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("highlight_reel_id", GUID(), nullable=False),
        sa.Column("highlight_reel_export_id", GUID(), nullable=True),
        sa.Column("share_audit_id", GUID(), nullable=False),
        sa.Column("message_id", GUID(), nullable=False),
        sa.Column("message_recipient_id", GUID(), nullable=False),
        sa.Column("person_id", GUID(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("priority_focus", sa.String(length=120), nullable=True),
        sa.Column("requested_follow_up", sa.Boolean(), nullable=False),
        sa.Column("clip_time_seconds", sa.Float(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["highlight_reel_export_id"], ["performance_highlight_reel_exports.id"]),
        sa.ForeignKeyConstraint(["highlight_reel_id"], ["performance_highlight_reels.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["communication_messages.id"]),
        sa.ForeignKeyConstraint(["message_recipient_id"], ["message_recipients.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["share_audit_id"], ["performance_highlight_reel_share_audits.id"]),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_highlight_reel_feedback")),
        sa.UniqueConstraint("message_recipient_id", name="uq_performance_highlight_reel_feedback_recipient"),
    )
    for column in [
        "highlight_reel_id",
        "highlight_reel_export_id",
        "message_id",
        "message_recipient_id",
        "organization_id",
        "person_id",
        "requested_follow_up",
        "share_audit_id",
        "status",
        "submitted_at",
    ]:
        op.create_index(
            op.f(f"ix_performance_highlight_reel_feedback_{column}"),
            "performance_highlight_reel_feedback",
            [column],
        )


def downgrade() -> None:
    for column in [
        "submitted_at",
        "status",
        "share_audit_id",
        "requested_follow_up",
        "person_id",
        "organization_id",
        "message_recipient_id",
        "message_id",
        "highlight_reel_export_id",
        "highlight_reel_id",
    ]:
        op.drop_index(
            op.f(f"ix_performance_highlight_reel_feedback_{column}"),
            table_name="performance_highlight_reel_feedback",
        )
    op.drop_table("performance_highlight_reel_feedback")
