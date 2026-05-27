"""add emergency escalation matrix

Revision ID: 79c1e2d3f4a5
Revises: 2b74c9e1a6f3
Create Date: 2026-05-28 04:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "79c1e2d3f4a5"
down_revision: str | None = "2b74c9e1a6f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("emergency_action_plans", sa.Column("incident_command_roles", sa.Text(), nullable=True))
    op.add_column("emergency_action_plans", sa.Column("escalation_matrix", sa.Text(), nullable=True))
    op.add_column("emergency_action_plans", sa.Column("external_agency_contacts", sa.Text(), nullable=True))
    op.add_column(
        "emergency_plan_activations",
        sa.Column("escalation_level", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_index(
        op.f("ix_emergency_plan_activations_escalation_level"),
        "emergency_plan_activations",
        ["escalation_level"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_emergency_plan_activations_escalation_level"),
        table_name="emergency_plan_activations",
    )
    op.drop_column("emergency_plan_activations", "escalation_level")
    op.drop_column("emergency_action_plans", "external_agency_contacts")
    op.drop_column("emergency_action_plans", "escalation_matrix")
    op.drop_column("emergency_action_plans", "incident_command_roles")
