"""add equipment readers

Revision ID: b94c2a0e7f5d
Revises: a87b2e1d9c3f
Create Date: 2026-05-27 21:20:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "b94c2a0e7f5d"
down_revision: str | None = "a87b2e1d9c3f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "equipment_readers",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("reader_id", sa.String(length=160), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("location", sa.String(length=240), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("api_key_hash", sa.String(length=64), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_scan_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_equipment_readers_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_equipment_readers")),
        sa.UniqueConstraint("organization_id", "reader_id", name=op.f("uq_equipment_readers_organization_id")),
    )
    op.create_index(op.f("ix_equipment_readers_last_scan_at"), "equipment_readers", ["last_scan_at"], unique=False)
    op.create_index(op.f("ix_equipment_readers_last_seen_at"), "equipment_readers", ["last_seen_at"], unique=False)
    op.create_index(op.f("ix_equipment_readers_location"), "equipment_readers", ["location"], unique=False)
    op.create_index(op.f("ix_equipment_readers_name"), "equipment_readers", ["name"], unique=False)
    op.create_index(op.f("ix_equipment_readers_organization_id"), "equipment_readers", ["organization_id"], unique=False)
    op.create_index(op.f("ix_equipment_readers_reader_id"), "equipment_readers", ["reader_id"], unique=False)
    op.create_index(op.f("ix_equipment_readers_status"), "equipment_readers", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_equipment_readers_status"), table_name="equipment_readers")
    op.drop_index(op.f("ix_equipment_readers_reader_id"), table_name="equipment_readers")
    op.drop_index(op.f("ix_equipment_readers_organization_id"), table_name="equipment_readers")
    op.drop_index(op.f("ix_equipment_readers_name"), table_name="equipment_readers")
    op.drop_index(op.f("ix_equipment_readers_location"), table_name="equipment_readers")
    op.drop_index(op.f("ix_equipment_readers_last_seen_at"), table_name="equipment_readers")
    op.drop_index(op.f("ix_equipment_readers_last_scan_at"), table_name="equipment_readers")
    op.drop_table("equipment_readers")
