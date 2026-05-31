"""add coach education certification lifecycle

Revision ID: a519b20260531
Revises: a518b20260531
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID


revision: str = "a519b20260531"
down_revision: str | Sequence[str] | None = "a518b20260531"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("coach_education_enrollments", sa.Column("accreditation_provider", sa.String(180), nullable=True))
    op.add_column("coach_education_enrollments", sa.Column("certificate_number", sa.String(120), nullable=True))
    op.add_column("coach_education_enrollments", sa.Column("certification_issued_on", sa.Date(), nullable=True))
    op.add_column("coach_education_enrollments", sa.Column("renewal_due_on", sa.Date(), nullable=True))
    op.add_column("coach_education_enrollments", sa.Column("cpd_hours_required", sa.Float(), nullable=False, server_default="20"))
    op.add_column("coach_education_enrollments", sa.Column("cpd_hours_completed", sa.Float(), nullable=False, server_default="0"))
    op.add_column("coach_education_enrollments", sa.Column("portfolio_evidence_ref", sa.String(500), nullable=True))
    op.add_column("coach_education_enrollments", sa.Column("mentor_person_id", GUID(), nullable=True))
    op.add_column("coach_education_enrollments", sa.Column("last_reviewed_by_person_id", GUID(), nullable=True))
    op.add_column("coach_education_enrollments", sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("coach_education_enrollments", sa.Column("review_notes", sa.Text(), nullable=True))
    op.create_foreign_key(
        op.f("fk_coach_education_enrollments_mentor_person_id_persons"),
        "coach_education_enrollments",
        "persons",
        ["mentor_person_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_coach_education_enrollments_last_reviewed_by_person_id_persons"),
        "coach_education_enrollments",
        "persons",
        ["last_reviewed_by_person_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_coach_education_enrollments_accreditation_provider"),
        "coach_education_enrollments",
        ["accreditation_provider"],
    )
    op.create_index(
        op.f("ix_coach_education_enrollments_certificate_number"),
        "coach_education_enrollments",
        ["certificate_number"],
    )
    op.create_index(
        op.f("ix_coach_education_enrollments_certification_issued_on"),
        "coach_education_enrollments",
        ["certification_issued_on"],
    )
    op.create_index(op.f("ix_coach_education_enrollments_renewal_due_on"), "coach_education_enrollments", ["renewal_due_on"])
    op.create_index(
        op.f("ix_coach_education_enrollments_mentor_person_id"),
        "coach_education_enrollments",
        ["mentor_person_id"],
    )
    op.create_index(
        op.f("ix_coach_education_enrollments_last_reviewed_by_person_id"),
        "coach_education_enrollments",
        ["last_reviewed_by_person_id"],
    )
    op.create_index(
        op.f("ix_coach_education_enrollments_last_reviewed_at"),
        "coach_education_enrollments",
        ["last_reviewed_at"],
    )

    op.add_column("coach_education_activities", sa.Column("cpd_hours", sa.Float(), nullable=False, server_default="0"))
    op.add_column("coach_education_activities", sa.Column("reviewer_person_id", GUID(), nullable=True))
    op.add_column("coach_education_activities", sa.Column("review_status", sa.String(40), nullable=False, server_default="accepted"))
    op.add_column("coach_education_activities", sa.Column("feedback", sa.Text(), nullable=True))
    op.create_foreign_key(
        op.f("fk_coach_education_activities_reviewer_person_id_persons"),
        "coach_education_activities",
        "persons",
        ["reviewer_person_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_coach_education_activities_reviewer_person_id"),
        "coach_education_activities",
        ["reviewer_person_id"],
    )
    op.create_index(
        op.f("ix_coach_education_activities_review_status"),
        "coach_education_activities",
        ["review_status"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_coach_education_activities_review_status"), table_name="coach_education_activities")
    op.drop_index(op.f("ix_coach_education_activities_reviewer_person_id"), table_name="coach_education_activities")
    op.drop_constraint(
        op.f("fk_coach_education_activities_reviewer_person_id_persons"),
        "coach_education_activities",
        type_="foreignkey",
    )
    op.drop_column("coach_education_activities", "feedback")
    op.drop_column("coach_education_activities", "review_status")
    op.drop_column("coach_education_activities", "reviewer_person_id")
    op.drop_column("coach_education_activities", "cpd_hours")

    op.drop_index(op.f("ix_coach_education_enrollments_last_reviewed_at"), table_name="coach_education_enrollments")
    op.drop_index(op.f("ix_coach_education_enrollments_last_reviewed_by_person_id"), table_name="coach_education_enrollments")
    op.drop_index(op.f("ix_coach_education_enrollments_mentor_person_id"), table_name="coach_education_enrollments")
    op.drop_index(op.f("ix_coach_education_enrollments_renewal_due_on"), table_name="coach_education_enrollments")
    op.drop_index(op.f("ix_coach_education_enrollments_certification_issued_on"), table_name="coach_education_enrollments")
    op.drop_index(op.f("ix_coach_education_enrollments_certificate_number"), table_name="coach_education_enrollments")
    op.drop_index(op.f("ix_coach_education_enrollments_accreditation_provider"), table_name="coach_education_enrollments")
    op.drop_constraint(
        op.f("fk_coach_education_enrollments_last_reviewed_by_person_id_persons"),
        "coach_education_enrollments",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_coach_education_enrollments_mentor_person_id_persons"),
        "coach_education_enrollments",
        type_="foreignkey",
    )
    op.drop_column("coach_education_enrollments", "review_notes")
    op.drop_column("coach_education_enrollments", "last_reviewed_at")
    op.drop_column("coach_education_enrollments", "last_reviewed_by_person_id")
    op.drop_column("coach_education_enrollments", "mentor_person_id")
    op.drop_column("coach_education_enrollments", "portfolio_evidence_ref")
    op.drop_column("coach_education_enrollments", "cpd_hours_completed")
    op.drop_column("coach_education_enrollments", "cpd_hours_required")
    op.drop_column("coach_education_enrollments", "renewal_due_on")
    op.drop_column("coach_education_enrollments", "certification_issued_on")
    op.drop_column("coach_education_enrollments", "certificate_number")
    op.drop_column("coach_education_enrollments", "accreditation_provider")
