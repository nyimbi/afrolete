"""add event attendance policies

Revision ID: c4e6f8a0b2d3
Revises: b3d5f7a9c1e2
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "c4e6f8a0b2d3"
down_revision: str | None = "b3d5f7a9c1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_attendance_policies",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_id", app.models.base.GUID(), nullable=False),
        sa.Column("policy_code", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("participation_statuses", sa.String(length=240), nullable=False),
        sa.Column("require_minor_consent", sa.Boolean(), nullable=False),
        sa.Column("require_medical_clearance", sa.Boolean(), nullable=False),
        sa.Column("minor_consent_action", sa.String(length=40), nullable=False),
        sa.Column("no_guardian_action", sa.String(length=40), nullable=False),
        sa.Column("denied_consent_action", sa.String(length=40), nullable=False),
        sa.Column("expired_consent_action", sa.String(length=40), nullable=False),
        sa.Column("missing_medical_action", sa.String(length=40), nullable=False),
        sa.Column("not_cleared_medical_action", sa.String(length=40), nullable=False),
        sa.Column("expired_medical_action", sa.String(length=40), nullable=False),
        sa.Column("restricted_medical_action", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_event_attendance_policies_event_id_events"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_attendance_policies_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_attendance_policies")),
        sa.UniqueConstraint("event_id", name="uq_event_attendance_policies_event"),
    )
    for column in ["active", "event_id", "organization_id", "policy_code"]:
        op.create_index(
            op.f(f"ix_event_attendance_policies_{column}"),
            "event_attendance_policies",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in ["policy_code", "organization_id", "event_id", "active"]:
        op.drop_index(op.f(f"ix_event_attendance_policies_{column}"), table_name="event_attendance_policies")
    op.drop_table("event_attendance_policies")
