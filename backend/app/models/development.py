from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin


class AthleteWellnessCheckIn(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_wellness_check_ins"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    submitted_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    check_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    mood_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    stress_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    sleep_hours: Mapped[float] = mapped_column(Float, nullable=False)
    energy_score: Mapped[int] = mapped_column(Integer, nullable=False)
    soreness_score: Mapped[int] = mapped_column(Integer, nullable=False)
    resilience_score: Mapped[int | None] = mapped_column(Integer)
    support_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    risk_band: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class AthleteAcademicRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_academic_records"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "athlete_profile_id",
            "term_label",
            name="uq_athlete_academic_records_term",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    recorded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    school_name: Mapped[str | None] = mapped_column(String(180), index=True)
    term_label: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    grade_level: Mapped[str | None] = mapped_column(String(80), index=True)
    gpa: Mapped[float | None] = mapped_column(Float)
    attendance_rate: Mapped[float | None] = mapped_column(Float)
    study_hours_weekly: Mapped[float | None] = mapped_column(Float)
    missing_assignment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    eligibility_status: Mapped[str] = mapped_column(String(60), default="pending_review", nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(40), default="watch", nullable=False, index=True)
    next_review_on: Mapped[date | None] = mapped_column(index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class AthleteLifeSkillAssignment(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_life_skill_assignments"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "athlete_profile_id",
            "module_code",
            name="uq_athlete_life_skill_assignments_module",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    assigned_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    module_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(40), default="foundation", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="assigned", nullable=False, index=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    due_on: Mapped[date | None] = mapped_column(index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    evidence_notes: Mapped[str | None] = mapped_column(Text)


class AthleteScholarshipApplication(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_scholarship_applications"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    program_name: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    scholarship_type: Mapped[str] = mapped_column(String(80), default="athletic", nullable=False, index=True)
    donor_or_fund: Mapped[str | None] = mapped_column(String(220), index=True)
    amount_requested: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    amount_awarded: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    eligibility_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    committee_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    deadline_on: Mapped[date | None] = mapped_column(index=True)
    submitted_on: Mapped[date | None] = mapped_column(index=True)
    decided_on: Mapped[date | None] = mapped_column(index=True)
    notes: Mapped[str | None] = mapped_column(Text)
