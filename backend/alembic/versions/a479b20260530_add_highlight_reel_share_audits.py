"""add highlight reel share audits

Revision ID: a479b20260530
Revises: a478b20260530
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a479b20260530"
down_revision: str | Sequence[str] | None = "a478b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


communication_channel = sa.Enum(
    "in_app",
    "push",
    "email",
    "sms",
    "whatsapp",
    "telegram",
    name="communicationchannel",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "performance_highlight_reel_share_audits",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("highlight_reel_id", GUID(), nullable=False),
        sa.Column("highlight_reel_export_id", GUID(), nullable=True),
        sa.Column("video_asset_id", GUID(), nullable=False),
        sa.Column("tracking_run_id", GUID(), nullable=True),
        sa.Column("message_id", GUID(), nullable=False),
        sa.Column("channel", communication_channel, nullable=False),
        sa.Column("audience", sa.String(length=80), nullable=False),
        sa.Column("share_policy", sa.String(length=80), nullable=False),
        sa.Column("recipient_count", sa.Integer(), nullable=False),
        sa.Column("player_recipient_count", sa.Integer(), nullable=False),
        sa.Column("guardian_recipient_count", sa.Integer(), nullable=False),
        sa.Column("explicit_recipient_count", sa.Integer(), nullable=False),
        sa.Column("published_by_person_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["highlight_reel_export_id"], ["performance_highlight_reel_exports.id"]),
        sa.ForeignKeyConstraint(["highlight_reel_id"], ["performance_highlight_reels.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["communication_messages.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["published_by_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["tracking_run_id"], ["performance_match_tracking_runs.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_highlight_reel_share_audits")),
    )
    for column in [
        "organization_id",
        "highlight_reel_id",
        "highlight_reel_export_id",
        "video_asset_id",
        "tracking_run_id",
        "message_id",
        "channel",
        "audience",
        "share_policy",
        "published_by_person_id",
        "status",
        "published_at",
    ]:
        op.create_index(
            op.f(f"ix_performance_highlight_reel_share_audits_{column}"),
            "performance_highlight_reel_share_audits",
            [column],
        )


def downgrade() -> None:
    for column in [
        "published_at",
        "status",
        "published_by_person_id",
        "share_policy",
        "audience",
        "channel",
        "message_id",
        "tracking_run_id",
        "video_asset_id",
        "highlight_reel_export_id",
        "highlight_reel_id",
        "organization_id",
    ]:
        op.drop_index(
            op.f(f"ix_performance_highlight_reel_share_audits_{column}"),
            table_name="performance_highlight_reel_share_audits",
        )
    op.drop_table("performance_highlight_reel_share_audits")
