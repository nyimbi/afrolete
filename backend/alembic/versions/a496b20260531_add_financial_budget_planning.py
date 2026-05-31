"""add financial budget planning

Revision ID: a496b20260531
Revises: a495b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a496b20260531"
down_revision: str | Sequence[str] | None = "a495b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "financial_budgets",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("budget_type", sa.String(length=80), nullable=False),
        sa.Column("scope_type", sa.String(length=80), nullable=False),
        sa.Column("scope_id", GUID(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("beginning_cash_balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("minimum_cash_reserve", sa.Numeric(12, 2), nullable=False),
        sa.Column("assumptions_json", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_financial_budgets_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_financial_budgets")),
        sa.UniqueConstraint("organization_id", "name", "fiscal_year", name="uq_financial_budgets_org_name_year"),
    )
    for column in ("budget_type", "fiscal_year", "name", "organization_id", "period_end", "period_start", "scope_id", "scope_type", "status"):
        op.create_index(op.f(f"ix_financial_budgets_{column}"), "financial_budgets", [column], unique=False)

    op.create_table(
        "financial_budget_lines",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("budget_id", GUID(), nullable=False),
        sa.Column("line_type", sa.String(length=40), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("amount_budgeted", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_actual", sa.Numeric(12, 2), nullable=False),
        sa.Column("forecast_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("cash_timing_month", sa.String(length=20), nullable=True),
        sa.Column("funding_source", sa.String(length=120), nullable=True),
        sa.Column("restricted", sa.Boolean(), nullable=False),
        sa.Column("variance_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["budget_id"], ["financial_budgets.id"], name=op.f("fk_financial_budget_lines_budget_id_financial_budgets")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_financial_budget_lines_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_financial_budget_lines")),
    )
    for column in ("budget_id", "cash_timing_month", "category", "department", "funding_source", "line_type", "organization_id", "restricted", "status"):
        op.create_index(op.f(f"ix_financial_budget_lines_{column}"), "financial_budget_lines", [column], unique=False)

    op.create_table(
        "financial_forecast_scenarios",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("budget_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("scenario_type", sa.String(length=60), nullable=False),
        sa.Column("revenue_adjustment_percent", sa.Numeric(6, 2), nullable=False),
        sa.Column("expense_adjustment_percent", sa.Numeric(6, 2), nullable=False),
        sa.Column("cash_adjustment_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("membership_growth_percent", sa.Numeric(6, 2), nullable=False),
        sa.Column("facility_utilization_percent", sa.Numeric(6, 2), nullable=True),
        sa.Column("assumptions_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["budget_id"], ["financial_budgets.id"], name=op.f("fk_financial_forecast_scenarios_budget_id_financial_budgets")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_financial_forecast_scenarios_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_financial_forecast_scenarios")),
        sa.UniqueConstraint("budget_id", "name", name="uq_financial_forecast_scenarios_budget_name"),
    )
    for column in ("budget_id", "name", "organization_id", "scenario_type", "status"):
        op.create_index(op.f(f"ix_financial_forecast_scenarios_{column}"), "financial_forecast_scenarios", [column], unique=False)


def downgrade() -> None:
    for column in ("status", "scenario_type", "organization_id", "name", "budget_id"):
        op.drop_index(op.f(f"ix_financial_forecast_scenarios_{column}"), table_name="financial_forecast_scenarios")
    op.drop_table("financial_forecast_scenarios")
    for column in ("status", "restricted", "organization_id", "line_type", "funding_source", "department", "category", "cash_timing_month", "budget_id"):
        op.drop_index(op.f(f"ix_financial_budget_lines_{column}"), table_name="financial_budget_lines")
    op.drop_table("financial_budget_lines")
    for column in ("status", "scope_type", "scope_id", "period_start", "period_end", "organization_id", "name", "fiscal_year", "budget_type"):
        op.drop_index(op.f(f"ix_financial_budgets_{column}"), table_name="financial_budgets")
    op.drop_table("financial_budgets")
