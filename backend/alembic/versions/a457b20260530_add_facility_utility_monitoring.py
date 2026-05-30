"""add facility utility monitoring

Revision ID: a457b20260530
Revises: a456b20260530
Create Date: 2026-05-30 20:05:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a457b20260530"
down_revision: str | None = "a456b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "facility_utility_meters",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("meter_id", sa.String(length=160), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("utility_type", sa.String(length=40), nullable=False),
        sa.Column("unit", sa.String(length=40), nullable=False),
        sa.Column("location", sa.String(length=240), nullable=True),
        sa.Column("provider", sa.String(length=120), nullable=True),
        sa.Column("account_reference", sa.String(length=180), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("api_key_hash", sa.String(length=64), nullable=False),
        sa.Column("cost_per_unit", sa.Numeric(12, 4), nullable=True),
        sa.Column("target_daily_usage", sa.Numeric(12, 3), nullable=True),
        sa.Column("last_reading_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_value", sa.Numeric(14, 3), nullable=True),
        sa.Column("last_cost_estimate", sa.Numeric(12, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_facility_utility_meters_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_facility_utility_meters_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_utility_meters")),
        sa.UniqueConstraint("organization_id", "meter_id", name=op.f("uq_facility_utility_meters_organization_id")),
    )
    for column in [
        "account_reference",
        "facility_id",
        "last_reading_at",
        "location",
        "meter_id",
        "name",
        "organization_id",
        "provider",
        "status",
        "utility_type",
    ]:
        op.create_index(op.f(f"ix_facility_utility_meters_{column}"), "facility_utility_meters", [column])

    op.create_table(
        "facility_utility_readings",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("utility_meter_id", app.models.base.GUID(), nullable=False),
        sa.Column("meter_id", sa.String(length=160), nullable=False),
        sa.Column("reading_value", sa.Numeric(14, 3), nullable=False),
        sa.Column("usage_delta", sa.Numeric(14, 3), nullable=True),
        sa.Column("unit", sa.String(length=40), nullable=False),
        sa.Column("cost_estimate", sa.Numeric(12, 2), nullable=True),
        sa.Column("reading_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("anomaly_level", sa.String(length=40), nullable=False),
        sa.Column("external_reference", sa.String(length=240), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_facility_utility_readings_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_facility_utility_readings_organization_id_organizations")),
        sa.ForeignKeyConstraint(["utility_meter_id"], ["facility_utility_meters.id"], name=op.f("fk_facility_utility_readings_utility_meter_id_facility_utility_meters")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_utility_readings")),
    )
    for column in [
        "anomaly_level",
        "external_reference",
        "facility_id",
        "meter_id",
        "organization_id",
        "reading_at",
        "source",
        "utility_meter_id",
    ]:
        op.create_index(op.f(f"ix_facility_utility_readings_{column}"), "facility_utility_readings", [column])

    op.create_table(
        "facility_utility_alerts",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("utility_meter_id", app.models.base.GUID(), nullable=False),
        sa.Column("utility_reading_id", app.models.base.GUID(), nullable=True),
        sa.Column("alert_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("recommended_action", sa.String(length=500), nullable=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_facility_utility_alerts_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_facility_utility_alerts_organization_id_organizations")),
        sa.ForeignKeyConstraint(["utility_meter_id"], ["facility_utility_meters.id"], name=op.f("fk_facility_utility_alerts_utility_meter_id_facility_utility_meters")),
        sa.ForeignKeyConstraint(["utility_reading_id"], ["facility_utility_readings.id"], name=op.f("fk_facility_utility_alerts_utility_reading_id_facility_utility_readings")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_utility_alerts")),
    )
    for column in [
        "alert_type",
        "facility_id",
        "organization_id",
        "resolved_at",
        "severity",
        "status",
        "triggered_at",
        "utility_meter_id",
        "utility_reading_id",
    ]:
        op.create_index(op.f(f"ix_facility_utility_alerts_{column}"), "facility_utility_alerts", [column])


def downgrade() -> None:
    for column in [
        "utility_reading_id",
        "utility_meter_id",
        "triggered_at",
        "status",
        "severity",
        "resolved_at",
        "organization_id",
        "facility_id",
        "alert_type",
    ]:
        op.drop_index(op.f(f"ix_facility_utility_alerts_{column}"), table_name="facility_utility_alerts")
    op.drop_table("facility_utility_alerts")
    for column in [
        "utility_meter_id",
        "source",
        "reading_at",
        "organization_id",
        "meter_id",
        "facility_id",
        "external_reference",
        "anomaly_level",
    ]:
        op.drop_index(op.f(f"ix_facility_utility_readings_{column}"), table_name="facility_utility_readings")
    op.drop_table("facility_utility_readings")
    for column in [
        "utility_type",
        "status",
        "provider",
        "organization_id",
        "name",
        "meter_id",
        "location",
        "last_reading_at",
        "facility_id",
        "account_reference",
    ]:
        op.drop_index(op.f(f"ix_facility_utility_meters_{column}"), table_name="facility_utility_meters")
    op.drop_table("facility_utility_meters")
