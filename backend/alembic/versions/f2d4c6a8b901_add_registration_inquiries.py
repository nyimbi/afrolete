"""add registration inquiries

Revision ID: f2d4c6a8b901
Revises: e41f2a7b8c9d
Create Date: 2026-05-27 23:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "f2d4c6a8b901"
down_revision: str | None = "e41f2a7b8c9d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "registration_inquiries",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("team_id", app.models.base.GUID(), nullable=True),
        sa.Column("athlete_name", sa.String(length=240), nullable=False),
        sa.Column("guardian_name", sa.String(length=240), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("age_group", sa.String(length=80), nullable=True),
        sa.Column("sport_interest", sa.String(length=120), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="new"),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_registration_inquiries_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["teams.id"],
            name=op.f("fk_registration_inquiries_team_id_teams"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_registration_inquiries")),
    )
    op.create_index(
        op.f("ix_registration_inquiries_age_group"),
        "registration_inquiries",
        ["age_group"],
        unique=False,
    )
    op.create_index(
        op.f("ix_registration_inquiries_athlete_name"),
        "registration_inquiries",
        ["athlete_name"],
        unique=False,
    )
    op.create_index(op.f("ix_registration_inquiries_email"), "registration_inquiries", ["email"], unique=False)
    op.create_index(
        op.f("ix_registration_inquiries_organization_id"),
        "registration_inquiries",
        ["organization_id"],
        unique=False,
    )
    op.create_index(op.f("ix_registration_inquiries_phone"), "registration_inquiries", ["phone"], unique=False)
    op.create_index(
        op.f("ix_registration_inquiries_sport_interest"),
        "registration_inquiries",
        ["sport_interest"],
        unique=False,
    )
    op.create_index(op.f("ix_registration_inquiries_status"), "registration_inquiries", ["status"], unique=False)
    op.create_index(op.f("ix_registration_inquiries_team_id"), "registration_inquiries", ["team_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_registration_inquiries_team_id"), table_name="registration_inquiries")
    op.drop_index(op.f("ix_registration_inquiries_status"), table_name="registration_inquiries")
    op.drop_index(op.f("ix_registration_inquiries_sport_interest"), table_name="registration_inquiries")
    op.drop_index(op.f("ix_registration_inquiries_phone"), table_name="registration_inquiries")
    op.drop_index(op.f("ix_registration_inquiries_organization_id"), table_name="registration_inquiries")
    op.drop_index(op.f("ix_registration_inquiries_email"), table_name="registration_inquiries")
    op.drop_index(op.f("ix_registration_inquiries_athlete_name"), table_name="registration_inquiries")
    op.drop_index(op.f("ix_registration_inquiries_age_group"), table_name="registration_inquiries")
    op.drop_table("registration_inquiries")
