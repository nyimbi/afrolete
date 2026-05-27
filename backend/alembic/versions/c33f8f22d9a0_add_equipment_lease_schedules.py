"""add equipment lease schedules

Revision ID: c33f8f22d9a0
Revises: b94c2a0e7f5d
Create Date: 2026-05-27 21:45:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "c33f8f22d9a0"
down_revision: str | None = "b94c2a0e7f5d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "equipment_lease_schedules",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("equipment_item_id", app.models.base.GUID(), nullable=False),
        sa.Column("finance_invoice_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=True),
        sa.Column("team_id", app.models.base.GUID(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("term_months", sa.Integer(), nullable=False),
        sa.Column("monthly_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["equipment_item_id"],
            ["equipment_items.id"],
            name=op.f("fk_equipment_lease_schedules_equipment_item_id_equipment_items"),
        ),
        sa.ForeignKeyConstraint(
            ["finance_invoice_id"],
            ["finance_invoices.id"],
            name=op.f("fk_equipment_lease_schedules_finance_invoice_id_finance_invoices"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_equipment_lease_schedules_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["persons.id"],
            name=op.f("fk_equipment_lease_schedules_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["teams.id"],
            name=op.f("fk_equipment_lease_schedules_team_id_teams"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_equipment_lease_schedules")),
    )
    op.create_index(op.f("ix_equipment_lease_schedules_equipment_item_id"), "equipment_lease_schedules", ["equipment_item_id"], unique=False)
    op.create_index(op.f("ix_equipment_lease_schedules_finance_invoice_id"), "equipment_lease_schedules", ["finance_invoice_id"], unique=False)
    op.create_index(op.f("ix_equipment_lease_schedules_organization_id"), "equipment_lease_schedules", ["organization_id"], unique=False)
    op.create_index(op.f("ix_equipment_lease_schedules_person_id"), "equipment_lease_schedules", ["person_id"], unique=False)
    op.create_index(op.f("ix_equipment_lease_schedules_starts_on"), "equipment_lease_schedules", ["starts_on"], unique=False)
    op.create_index(op.f("ix_equipment_lease_schedules_status"), "equipment_lease_schedules", ["status"], unique=False)
    op.create_index(op.f("ix_equipment_lease_schedules_team_id"), "equipment_lease_schedules", ["team_id"], unique=False)

    op.create_table(
        "equipment_lease_installments",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("lease_schedule_id", app.models.base.GUID(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["lease_schedule_id"],
            ["equipment_lease_schedules.id"],
            name=op.f("fk_equipment_lease_installments_lease_schedule_id_equipment_lease_schedules"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_equipment_lease_installments_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_equipment_lease_installments")),
    )
    op.create_index(op.f("ix_equipment_lease_installments_due_on"), "equipment_lease_installments", ["due_on"], unique=False)
    op.create_index(op.f("ix_equipment_lease_installments_lease_schedule_id"), "equipment_lease_installments", ["lease_schedule_id"], unique=False)
    op.create_index(op.f("ix_equipment_lease_installments_organization_id"), "equipment_lease_installments", ["organization_id"], unique=False)
    op.create_index(op.f("ix_equipment_lease_installments_paid_at"), "equipment_lease_installments", ["paid_at"], unique=False)
    op.create_index(op.f("ix_equipment_lease_installments_sequence_number"), "equipment_lease_installments", ["sequence_number"], unique=False)
    op.create_index(op.f("ix_equipment_lease_installments_status"), "equipment_lease_installments", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_equipment_lease_installments_status"), table_name="equipment_lease_installments")
    op.drop_index(op.f("ix_equipment_lease_installments_sequence_number"), table_name="equipment_lease_installments")
    op.drop_index(op.f("ix_equipment_lease_installments_paid_at"), table_name="equipment_lease_installments")
    op.drop_index(op.f("ix_equipment_lease_installments_organization_id"), table_name="equipment_lease_installments")
    op.drop_index(op.f("ix_equipment_lease_installments_lease_schedule_id"), table_name="equipment_lease_installments")
    op.drop_index(op.f("ix_equipment_lease_installments_due_on"), table_name="equipment_lease_installments")
    op.drop_table("equipment_lease_installments")
    op.drop_index(op.f("ix_equipment_lease_schedules_team_id"), table_name="equipment_lease_schedules")
    op.drop_index(op.f("ix_equipment_lease_schedules_status"), table_name="equipment_lease_schedules")
    op.drop_index(op.f("ix_equipment_lease_schedules_starts_on"), table_name="equipment_lease_schedules")
    op.drop_index(op.f("ix_equipment_lease_schedules_person_id"), table_name="equipment_lease_schedules")
    op.drop_index(op.f("ix_equipment_lease_schedules_organization_id"), table_name="equipment_lease_schedules")
    op.drop_index(op.f("ix_equipment_lease_schedules_finance_invoice_id"), table_name="equipment_lease_schedules")
    op.drop_index(op.f("ix_equipment_lease_schedules_equipment_item_id"), table_name="equipment_lease_schedules")
    op.drop_table("equipment_lease_schedules")
