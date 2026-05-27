"""add equipment file uploads

Revision ID: f6b87d22aa41
Revises: d16e2bc91c4a
Create Date: 2026-05-27 19:40:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "f6b87d22aa41"
down_revision: str | None = "d16e2bc91c4a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "equipment_files",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("equipment_item_id", app.models.base.GUID(), nullable=False),
        sa.Column("uploaded_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("filename", sa.String(length=240), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("storage_url", sa.String(length=500), nullable=False),
        sa.Column("storage_path", sa.String(length=700), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["equipment_item_id"],
            ["equipment_items.id"],
            name=op.f("fk_equipment_files_equipment_item_id_equipment_items"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_equipment_files_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_person_id"],
            ["persons.id"],
            name=op.f("fk_equipment_files_uploaded_by_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_equipment_files")),
    )
    op.create_index(op.f("ix_equipment_files_checksum"), "equipment_files", ["checksum"], unique=False)
    op.create_index(op.f("ix_equipment_files_equipment_item_id"), "equipment_files", ["equipment_item_id"], unique=False)
    op.create_index(op.f("ix_equipment_files_organization_id"), "equipment_files", ["organization_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_equipment_files_organization_id"), table_name="equipment_files")
    op.drop_index(op.f("ix_equipment_files_equipment_item_id"), table_name="equipment_files")
    op.drop_index(op.f("ix_equipment_files_checksum"), table_name="equipment_files")
    op.drop_table("equipment_files")
