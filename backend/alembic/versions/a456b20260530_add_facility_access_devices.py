"""add facility access devices

Revision ID: a456b20260530
Revises: a455b20260530
Create Date: 2026-05-30 19:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a456b20260530"
down_revision: str | None = "a455b20260530"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "facility_access_devices",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("device_id", sa.String(length=160), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("location", sa.String(length=240), nullable=True),
        sa.Column("device_type", sa.String(length=80), nullable=False),
        sa.Column("unlock_method", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("api_key_hash", sa.String(length=64), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_scan_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_health_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("battery_percent", sa.Integer(), nullable=True),
        sa.Column("firmware_version", sa.String(length=120), nullable=True),
        sa.Column("network_status", sa.String(length=80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_facility_access_devices_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_facility_access_devices_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_access_devices")),
        sa.UniqueConstraint("organization_id", "device_id", name=op.f("uq_facility_access_devices_organization_id")),
    )
    for column in [
        "device_id",
        "device_type",
        "facility_id",
        "last_health_at",
        "last_scan_at",
        "last_seen_at",
        "location",
        "name",
        "network_status",
        "organization_id",
        "status",
        "unlock_method",
    ]:
        op.create_index(op.f(f"ix_facility_access_devices_{column}"), "facility_access_devices", [column])

    op.create_table(
        "facility_access_commands",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("facility_id", app.models.base.GUID(), nullable=False),
        sa.Column("access_device_id", app.models.base.GUID(), nullable=False),
        sa.Column("access_event_id", app.models.base.GUID(), nullable=True),
        sa.Column("credential_id", app.models.base.GUID(), nullable=True),
        sa.Column("command_type", sa.String(length=40), nullable=False),
        sa.Column("command_payload", sa.Text(), nullable=False),
        sa.Column("command_signature", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["access_device_id"], ["facility_access_devices.id"], name=op.f("fk_facility_access_commands_access_device_id_facility_access_devices")),
        sa.ForeignKeyConstraint(["access_event_id"], ["facility_access_events.id"], name=op.f("fk_facility_access_commands_access_event_id_facility_access_events")),
        sa.ForeignKeyConstraint(["credential_id"], ["facility_access_credentials.id"], name=op.f("fk_facility_access_commands_credential_id_facility_access_credentials")),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], name=op.f("fk_facility_access_commands_facility_id_facilities")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_facility_access_commands_organization_id_organizations")),
        sa.ForeignKeyConstraint(["requested_by_person_id"], ["persons.id"], name=op.f("fk_facility_access_commands_requested_by_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_access_commands")),
    )
    for column in [
        "access_device_id",
        "access_event_id",
        "acknowledged_at",
        "command_type",
        "credential_id",
        "facility_id",
        "issued_at",
        "organization_id",
        "requested_by_person_id",
        "status",
        "valid_until",
    ]:
        op.create_index(op.f(f"ix_facility_access_commands_{column}"), "facility_access_commands", [column])


def downgrade() -> None:
    for column in [
        "valid_until",
        "status",
        "requested_by_person_id",
        "organization_id",
        "issued_at",
        "facility_id",
        "credential_id",
        "command_type",
        "acknowledged_at",
        "access_event_id",
        "access_device_id",
    ]:
        op.drop_index(op.f(f"ix_facility_access_commands_{column}"), table_name="facility_access_commands")
    op.drop_table("facility_access_commands")
    for column in [
        "unlock_method",
        "status",
        "organization_id",
        "network_status",
        "name",
        "location",
        "last_seen_at",
        "last_scan_at",
        "last_health_at",
        "facility_id",
        "device_type",
        "device_id",
    ]:
        op.drop_index(op.f(f"ix_facility_access_devices_{column}"), table_name="facility_access_devices")
    op.drop_table("facility_access_devices")
