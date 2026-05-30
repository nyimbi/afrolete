from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin


class CoachEducationEnrollment(IdMixin, TimestampMixin, Base):
    __tablename__ = "coach_education_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "person_id",
            "program_key",
            name="uq_coach_education_enrollments_org_person_program",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), nullable=False, index=True)
    program_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    program_title: Mapped[str] = mapped_column(String(220), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(120), default="coach", nullable=False, index=True)
    skill_level: Mapped[str] = mapped_column(String(80), default="intermediate", nullable=False)
    learning_style: Mapped[str] = mapped_column(String(80), default="hands_on", nullable=False)
    xp_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    current_module_key: Mapped[str | None] = mapped_column(String(120), index=True)
    completed_modules_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    badges_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    certification_expires_on: Mapped[date | None] = mapped_column(Date, index=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class CoachEducationActivity(IdMixin, TimestampMixin, Base):
    __tablename__ = "coach_education_activities"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    enrollment_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("coach_education_enrollments.id"),
        nullable=False,
        index=True,
    )
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(80), default="module_completion", nullable=False, index=True)
    module_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_ref: Mapped[str | None] = mapped_column(String(500))
    score_percent: Mapped[float | None] = mapped_column(Float)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
