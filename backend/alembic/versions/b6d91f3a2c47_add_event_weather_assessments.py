"""add event weather assessments

Revision ID: b6d91f3a2c47
Revises: 79c1e2d3f4a5
Create Date: 2026-05-28 04:35:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "b6d91f3a2c47"
down_revision: str | None = "79c1e2d3f4a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


weather_alert_level = sa.Enum(
    "information",
    "advisory",
    "warning",
    "critical",
    name="weatheralertlevel",
    native_enum=False,
    create_constraint=True,
)
weather_decision = sa.Enum(
    "proceed",
    "monitor",
    "modify",
    "delay",
    "cancel",
    "evacuate",
    name="weatherdecision",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "event_weather_assessments",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("event_id", app.models.base.GUID(), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature_c", sa.Numeric(5, 2), nullable=True),
        sa.Column("heat_index_c", sa.Numeric(5, 2), nullable=True),
        sa.Column("wbgt_c", sa.Numeric(5, 2), nullable=True),
        sa.Column("humidity_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("aqi", sa.Integer(), nullable=True),
        sa.Column("lightning_distance_km", sa.Numeric(6, 2), nullable=True),
        sa.Column("wind_speed_kph", sa.Numeric(6, 2), nullable=True),
        sa.Column("wind_gust_kph", sa.Numeric(6, 2), nullable=True),
        sa.Column("precipitation_mm_per_hr", sa.Numeric(6, 2), nullable=True),
        sa.Column("alert_level", weather_alert_level, nullable=False),
        sa.Column("decision", weather_decision, nullable=False),
        sa.Column("recommended_actions", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_event_weather_assessments_event_id_events"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_event_weather_assessments_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_weather_assessments")),
    )
    for column in [
        "alert_level",
        "aqi",
        "decision",
        "event_id",
        "lightning_distance_km",
        "observed_at",
        "organization_id",
        "source",
    ]:
        op.create_index(
            op.f(f"ix_event_weather_assessments_{column}"),
            "event_weather_assessments",
            [column],
        )


def downgrade() -> None:
    for column in [
        "source",
        "organization_id",
        "observed_at",
        "lightning_distance_km",
        "event_id",
        "decision",
        "aqi",
        "alert_level",
    ]:
        op.drop_index(op.f(f"ix_event_weather_assessments_{column}"), table_name="event_weather_assessments")
    op.drop_table("event_weather_assessments")
