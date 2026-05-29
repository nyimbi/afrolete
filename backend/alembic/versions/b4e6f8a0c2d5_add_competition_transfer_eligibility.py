"""add competition transfer eligibility

Revision ID: b4e6f8a0c2d5
Revises: a2d9f4c7e8b1
Create Date: 2026-05-29 14:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "b4e6f8a0c2d5"
down_revision: str | None = "a2d9f4c7e8b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "athlete_transfer_records",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("from_team_id", app.models.base.GUID(), nullable=True),
        sa.Column("to_team_id", app.models.base.GUID(), nullable=False),
        sa.Column("transfer_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("requested_on", sa.Date(), nullable=False),
        sa.Column("effective_on", sa.Date(), nullable=True),
        sa.Column("window_label", sa.String(length=120), nullable=True),
        sa.Column("previous_registration_ref", sa.String(length=180), nullable=True),
        sa.Column("clearance_reference", sa.String(length=180), nullable=True),
        sa.Column("reviewed_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["athlete_profile_id"], ["athlete_profiles.id"], name=op.f("fk_athlete_transfer_records_athlete_profile_id_athlete_profiles")),
        sa.ForeignKeyConstraint(["from_team_id"], ["teams.id"], name=op.f("fk_athlete_transfer_records_from_team_id_teams")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_athlete_transfer_records_organization_id_organizations")),
        sa.ForeignKeyConstraint(["reviewed_by_person_id"], ["persons.id"], name=op.f("fk_athlete_transfer_records_reviewed_by_person_id_persons")),
        sa.ForeignKeyConstraint(["to_team_id"], ["teams.id"], name=op.f("fk_athlete_transfer_records_to_team_id_teams")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_athlete_transfer_records")),
    )
    for column in [
        "athlete_profile_id",
        "clearance_reference",
        "decided_at",
        "effective_on",
        "from_team_id",
        "organization_id",
        "previous_registration_ref",
        "requested_on",
        "reviewed_by_person_id",
        "status",
        "to_team_id",
        "transfer_type",
        "window_label",
    ]:
        op.create_index(op.f(f"ix_athlete_transfer_records_{column}"), "athlete_transfer_records", [column])

    op.create_table(
        "competition_eligibility_certificates",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("competition_id", app.models.base.GUID(), nullable=False),
        sa.Column("athlete_profile_id", app.models.base.GUID(), nullable=False),
        sa.Column("team_id", app.models.base.GUID(), nullable=False),
        sa.Column("transfer_record_id", app.models.base.GUID(), nullable=True),
        sa.Column("issued_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("certificate_number", sa.String(length=80), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("blocker_count", sa.Integer(), nullable=False),
        sa.Column("warning_count", sa.Integer(), nullable=False),
        sa.Column("eligibility_summary", sa.Text(), nullable=False),
        sa.Column("checks_json", sa.Text(), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["athlete_profile_id"], ["athlete_profiles.id"], name=op.f("fk_competition_eligibility_certificates_athlete_profile_id_athlete_profiles")),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"], name=op.f("fk_competition_eligibility_certificates_competition_id_competitions")),
        sa.ForeignKeyConstraint(["issued_by_person_id"], ["persons.id"], name=op.f("fk_competition_eligibility_certificates_issued_by_person_id_persons")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_competition_eligibility_certificates_organization_id_organizations")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_competition_eligibility_certificates_team_id_teams")),
        sa.ForeignKeyConstraint(["transfer_record_id"], ["athlete_transfer_records.id"], name=op.f("fk_competition_eligibility_certificates_transfer_record_id_athlete_transfer_records")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_competition_eligibility_certificates")),
        sa.UniqueConstraint("certificate_number", name="uq_competition_eligibility_certificates_number"),
        sa.UniqueConstraint(
            "competition_id",
            "athlete_profile_id",
            "team_id",
            name="uq_competition_eligibility_certificates_scope",
        ),
    )
    for column in [
        "athlete_profile_id",
        "certificate_number",
        "competition_id",
        "issued_by_person_id",
        "organization_id",
        "status",
        "team_id",
        "transfer_record_id",
        "valid_from",
        "valid_until",
    ]:
        op.create_index(
            op.f(f"ix_competition_eligibility_certificates_{column}"),
            "competition_eligibility_certificates",
            [column],
        )


def downgrade() -> None:
    for column in [
        "valid_until",
        "valid_from",
        "transfer_record_id",
        "team_id",
        "status",
        "organization_id",
        "issued_by_person_id",
        "competition_id",
        "certificate_number",
        "athlete_profile_id",
    ]:
        op.drop_index(op.f(f"ix_competition_eligibility_certificates_{column}"), table_name="competition_eligibility_certificates")
    op.drop_table("competition_eligibility_certificates")
    for column in [
        "window_label",
        "transfer_type",
        "to_team_id",
        "status",
        "reviewed_by_person_id",
        "requested_on",
        "previous_registration_ref",
        "organization_id",
        "from_team_id",
        "effective_on",
        "decided_at",
        "clearance_reference",
        "athlete_profile_id",
    ]:
        op.drop_index(op.f(f"ix_athlete_transfer_records_{column}"), table_name="athlete_transfer_records")
    op.drop_table("athlete_transfer_records")
