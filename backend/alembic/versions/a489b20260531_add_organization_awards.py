"""add organization awards

Revision ID: a489b20260531
Revises: a488b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.models.base import GUID


revision: str = "a489b20260531"
down_revision: str | None = "a488b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_award_programs",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("season_label", sa.String(length=80), nullable=True),
        sa.Column("level", sa.String(length=80), nullable=False),
        sa.Column("frequency", sa.String(length=80), nullable=False),
        sa.Column("nomination_opens_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("nomination_closes_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voting_opens_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voting_closes_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("eligibility_summary", sa.Text(), nullable=True),
        sa.Column("ceremony_name", sa.String(length=180), nullable=True),
        sa.Column("ceremony_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ceremony_venue", sa.String(length=240), nullable=True),
        sa.Column("certificate_template", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_award_programs_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_award_programs")),
        sa.UniqueConstraint(
            "organization_id",
            "name",
            "season_label",
            name=op.f("uq_organization_award_programs_organization_id"),
        ),
    )
    for column in [
        "organization_id",
        "name",
        "season_label",
        "level",
        "frequency",
        "nomination_opens_at",
        "nomination_closes_at",
        "voting_opens_at",
        "voting_closes_at",
        "ceremony_at",
        "status",
    ]:
        op.create_index(op.f(f"ix_organization_award_programs_{column}"), "organization_award_programs", [column])

    op.create_table(
        "organization_award_categories",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("program_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("award_type", sa.String(length=80), nullable=False),
        sa.Column("judging_method", sa.String(length=80), nullable=False),
        sa.Column("criteria", sa.Text(), nullable=True),
        sa.Column("max_recipients", sa.Integer(), nullable=False),
        sa.Column("voter_roles", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_award_categories_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["program_id"],
            ["organization_award_programs.id"],
            name=op.f("fk_organization_award_categories_program_id_organization_award_programs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_award_categories")),
        sa.UniqueConstraint("program_id", "name", name=op.f("uq_organization_award_categories_program_id")),
    )
    for column in ["organization_id", "program_id", "name", "award_type", "judging_method", "status"]:
        op.create_index(op.f(f"ix_organization_award_categories_{column}"), "organization_award_categories", [column])

    op.create_table(
        "organization_award_nominations",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("program_id", GUID(), nullable=False),
        sa.Column("category_id", GUID(), nullable=False),
        sa.Column("nominee_subject_type", sa.String(length=12), nullable=False),
        sa.Column("nominee_subject_id", GUID(), nullable=False),
        sa.Column("nominated_by_person_id", GUID(), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("nomination_summary", sa.Text(), nullable=False),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("finalist", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Numeric(8, 2), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["organization_award_categories.id"],
            name=op.f("fk_organization_award_nominations_category_id_organization_award_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["nominated_by_person_id"],
            ["persons.id"],
            name=op.f("fk_organization_award_nominations_nominated_by_person_id_persons"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_award_nominations_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["program_id"],
            ["organization_award_programs.id"],
            name=op.f("fk_organization_award_nominations_program_id_organization_award_programs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_award_nominations")),
        sa.UniqueConstraint(
            "category_id",
            "nominee_subject_type",
            "nominee_subject_id",
            name="uq_organization_award_nominations_nominee",
        ),
    )
    for column in [
        "organization_id",
        "program_id",
        "category_id",
        "nominee_subject_type",
        "nominee_subject_id",
        "nominated_by_person_id",
        "title",
        "status",
        "finalist",
    ]:
        op.create_index(
            op.f(f"ix_organization_award_nominations_{column}"),
            "organization_award_nominations",
            [column],
        )

    op.create_table(
        "organization_award_votes",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("nomination_id", GUID(), nullable=False),
        sa.Column("voter_person_id", GUID(), nullable=False),
        sa.Column("score", sa.Numeric(8, 2), nullable=False),
        sa.Column("weight", sa.Numeric(8, 2), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["nomination_id"],
            ["organization_award_nominations.id"],
            name=op.f("fk_organization_award_votes_nomination_id_organization_award_nominations"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_award_votes_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["voter_person_id"],
            ["persons.id"],
            name=op.f("fk_organization_award_votes_voter_person_id_persons"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_award_votes")),
        sa.UniqueConstraint("nomination_id", "voter_person_id", name="uq_organization_award_votes_voter"),
    )
    for column in ["organization_id", "nomination_id", "voter_person_id"]:
        op.create_index(op.f(f"ix_organization_award_votes_{column}"), "organization_award_votes", [column])

    op.create_table(
        "organization_award_recipients",
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("program_id", GUID(), nullable=False),
        sa.Column("category_id", GUID(), nullable=False),
        sa.Column("nomination_id", GUID(), nullable=True),
        sa.Column("recipient_subject_type", sa.String(length=12), nullable=False),
        sa.Column("recipient_subject_id", GUID(), nullable=False),
        sa.Column("certificate_number", sa.String(length=120), nullable=False),
        sa.Column("awarded_on", sa.Date(), nullable=False),
        sa.Column("public_citation", sa.Text(), nullable=False),
        sa.Column("certificate_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["organization_award_categories.id"],
            name=op.f("fk_organization_award_recipients_category_id_organization_award_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["nomination_id"],
            ["organization_award_nominations.id"],
            name=op.f("fk_organization_award_recipients_nomination_id_organization_award_nominations"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_award_recipients_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["program_id"],
            ["organization_award_programs.id"],
            name=op.f("fk_organization_award_recipients_program_id_organization_award_programs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_award_recipients")),
        sa.UniqueConstraint("organization_id", "certificate_number", name=op.f("uq_organization_award_recipients_organization_id")),
        sa.UniqueConstraint(
            "category_id",
            "recipient_subject_type",
            "recipient_subject_id",
            name="uq_organization_award_recipients_subject",
        ),
    )
    for column in [
        "organization_id",
        "program_id",
        "category_id",
        "nomination_id",
        "recipient_subject_type",
        "recipient_subject_id",
        "certificate_number",
        "awarded_on",
        "status",
    ]:
        op.create_index(
            op.f(f"ix_organization_award_recipients_{column}"),
            "organization_award_recipients",
            [column],
        )


def downgrade() -> None:
    for column in [
        "status",
        "awarded_on",
        "certificate_number",
        "recipient_subject_id",
        "recipient_subject_type",
        "nomination_id",
        "category_id",
        "program_id",
        "organization_id",
    ]:
        op.drop_index(op.f(f"ix_organization_award_recipients_{column}"), table_name="organization_award_recipients")
    op.drop_table("organization_award_recipients")

    for column in ["voter_person_id", "nomination_id", "organization_id"]:
        op.drop_index(op.f(f"ix_organization_award_votes_{column}"), table_name="organization_award_votes")
    op.drop_table("organization_award_votes")

    for column in [
        "finalist",
        "status",
        "title",
        "nominated_by_person_id",
        "nominee_subject_id",
        "nominee_subject_type",
        "category_id",
        "program_id",
        "organization_id",
    ]:
        op.drop_index(op.f(f"ix_organization_award_nominations_{column}"), table_name="organization_award_nominations")
    op.drop_table("organization_award_nominations")

    for column in ["status", "judging_method", "award_type", "name", "program_id", "organization_id"]:
        op.drop_index(op.f(f"ix_organization_award_categories_{column}"), table_name="organization_award_categories")
    op.drop_table("organization_award_categories")

    for column in [
        "status",
        "ceremony_at",
        "voting_closes_at",
        "voting_opens_at",
        "nomination_closes_at",
        "nomination_opens_at",
        "frequency",
        "level",
        "season_label",
        "name",
        "organization_id",
    ]:
        op.drop_index(op.f(f"ix_organization_award_programs_{column}"), table_name="organization_award_programs")
    op.drop_table("organization_award_programs")
