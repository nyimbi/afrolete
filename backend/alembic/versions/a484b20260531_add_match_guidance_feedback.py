"""add match guidance feedback

Revision ID: a484b20260531
Revises: a483b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a484b20260531"
down_revision: str | Sequence[str] | None = "a483b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "performance_match_player_guidance_feedback",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("tracking_run_id", GUID(), nullable=False),
        sa.Column("video_asset_id", GUID(), nullable=False),
        sa.Column("publish_audit_id", GUID(), nullable=False),
        sa.Column("message_id", GUID(), nullable=False),
        sa.Column("message_recipient_id", GUID(), nullable=False),
        sa.Column("person_id", GUID(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("priority_focus", sa.String(length=120), nullable=True),
        sa.Column("requested_follow_up", sa.Boolean(), nullable=False),
        sa.Column("completed_action_count", sa.Integer(), nullable=False),
        sa.Column("agent_task_id", GUID(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_task_id"], ["agent_tasks.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["communication_messages.id"]),
        sa.ForeignKeyConstraint(["message_recipient_id"], ["message_recipients.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["publish_audit_id"], ["performance_match_player_guidance_publish_audits.id"]),
        sa.ForeignKeyConstraint(["tracking_run_id"], ["performance_match_tracking_runs.id"]),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"]),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_match_player_guidance_feedback")),
        sa.UniqueConstraint(
            "message_recipient_id",
            name="uq_performance_match_player_guidance_feedback_recipient",
        ),
    )
    for column in [
        "agent_task_id",
        "message_id",
        "message_recipient_id",
        "organization_id",
        "person_id",
        "publish_audit_id",
        "requested_follow_up",
        "status",
        "submitted_at",
        "tracking_run_id",
        "video_asset_id",
    ]:
        op.create_index(
            op.f(f"ix_performance_match_player_guidance_feedback_{column}"),
            "performance_match_player_guidance_feedback",
            [column],
        )


def downgrade() -> None:
    for column in [
        "video_asset_id",
        "tracking_run_id",
        "submitted_at",
        "status",
        "requested_follow_up",
        "publish_audit_id",
        "person_id",
        "organization_id",
        "message_recipient_id",
        "message_id",
        "agent_task_id",
    ]:
        op.drop_index(
            op.f(f"ix_performance_match_player_guidance_feedback_{column}"),
            table_name="performance_match_player_guidance_feedback",
        )
    op.drop_table("performance_match_player_guidance_feedback")
