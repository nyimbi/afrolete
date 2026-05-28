"""add security incident type

Revision ID: c1d2e3f4a5b6
Revises: b0c1d2e3f4a5
Create Date: 2026-05-28 08:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "c1d2e3f4a5b6"
down_revision: str | None = "b0c1d2e3f4a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


INCIDENT_TYPES_WITH_SECURITY = (
    "injury",
    "medical",
    "safeguarding",
    "misconduct",
    "facility",
    "transport",
    "weather",
    "security",
    "other",
)

INCIDENT_TYPES_WITHOUT_SECURITY = (
    "injury",
    "medical",
    "safeguarding",
    "misconduct",
    "facility",
    "transport",
    "weather",
    "other",
)


def replace_incident_type_constraint(values: tuple[str, ...]) -> None:
    with op.batch_alter_table("safeguarding_incidents") as batch_op:
        batch_op.drop_constraint("safeguardingincidenttype", type_="check")
        batch_op.create_check_constraint(
            "safeguardingincidenttype",
            sa.column("incident_type").in_(values),
        )


def upgrade() -> None:
    replace_incident_type_constraint(INCIDENT_TYPES_WITH_SECURITY)


def downgrade() -> None:
    op.execute(
        "UPDATE safeguarding_incidents "
        "SET incident_type = 'safeguarding' "
        "WHERE incident_type = 'security'"
    )
    replace_incident_type_constraint(INCIDENT_TYPES_WITHOUT_SECURITY)
