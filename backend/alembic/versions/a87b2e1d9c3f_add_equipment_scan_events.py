"""add equipment scan events

Revision ID: a87b2e1d9c3f
Revises: f6b87d22aa41
Create Date: 2026-05-27 20:25:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "a87b2e1d9c3f"
down_revision: str | None = "f6b87d22aa41"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "equipment_scan_events",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("equipment_item_id", app.models.base.GUID(), nullable=True),
        sa.Column("scanned_code", sa.String(length=160), nullable=False),
        sa.Column("match_type", sa.String(length=40), nullable=True),
        sa.Column("item_name", sa.String(length=180), nullable=True),
        sa.Column("reader_id", sa.String(length=160), nullable=False),
        sa.Column("reader_location", sa.String(length=240), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("movement", sa.String(length=40), nullable=False),
        sa.Column("matched", sa.Boolean(), nullable=False),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("external_reference", sa.String(length=240), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["equipment_item_id"],
            ["equipment_items.id"],
            name=op.f("fk_equipment_scan_events_equipment_item_id_equipment_items"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_equipment_scan_events_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_equipment_scan_events")),
    )
    op.create_index(
        op.f("ix_equipment_scan_events_equipment_item_id"),
        "equipment_scan_events",
        ["equipment_item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_equipment_scan_events_external_reference"),
        "equipment_scan_events",
        ["external_reference"],
        unique=False,
    )
    op.create_index(
        op.f("ix_equipment_scan_events_match_type"),
        "equipment_scan_events",
        ["match_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_equipment_scan_events_matched"),
        "equipment_scan_events",
        ["matched"],
        unique=False,
    )
    op.create_index(
        op.f("ix_equipment_scan_events_movement"),
        "equipment_scan_events",
        ["movement"],
        unique=False,
    )
    op.create_index(
        op.f("ix_equipment_scan_events_organization_id"),
        "equipment_scan_events",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_equipment_scan_events_reader_id"),
        "equipment_scan_events",
        ["reader_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_equipment_scan_events_reader_location"),
        "equipment_scan_events",
        ["reader_location"],
        unique=False,
    )
    op.create_index(
        op.f("ix_equipment_scan_events_scanned_at"),
        "equipment_scan_events",
        ["scanned_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_equipment_scan_events_scanned_code"),
        "equipment_scan_events",
        ["scanned_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_equipment_scan_events_source"),
        "equipment_scan_events",
        ["source"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_equipment_scan_events_source"), table_name="equipment_scan_events")
    op.drop_index(op.f("ix_equipment_scan_events_scanned_code"), table_name="equipment_scan_events")
    op.drop_index(op.f("ix_equipment_scan_events_scanned_at"), table_name="equipment_scan_events")
    op.drop_index(op.f("ix_equipment_scan_events_reader_location"), table_name="equipment_scan_events")
    op.drop_index(op.f("ix_equipment_scan_events_reader_id"), table_name="equipment_scan_events")
    op.drop_index(op.f("ix_equipment_scan_events_organization_id"), table_name="equipment_scan_events")
    op.drop_index(op.f("ix_equipment_scan_events_movement"), table_name="equipment_scan_events")
    op.drop_index(op.f("ix_equipment_scan_events_matched"), table_name="equipment_scan_events")
    op.drop_index(op.f("ix_equipment_scan_events_match_type"), table_name="equipment_scan_events")
    op.drop_index(op.f("ix_equipment_scan_events_external_reference"), table_name="equipment_scan_events")
    op.drop_index(op.f("ix_equipment_scan_events_equipment_item_id"), table_name="equipment_scan_events")
    op.drop_table("equipment_scan_events")
