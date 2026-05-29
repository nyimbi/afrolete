from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin


class VolunteerProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "volunteer_profiles"
    __table_args__ = (
        UniqueConstraint("organization_id", "person_id", name="uq_volunteer_profiles_org_person"),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), nullable=False, index=True)
    volunteer_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    certification_level: Mapped[str | None] = mapped_column(String(120), index=True)
    availability_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    skills_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    background_check_status: Mapped[str] = mapped_column(String(40), default="not_started", nullable=False, index=True)
    background_check_expires_on: Mapped[date | None] = mapped_column(Date, index=True)
    training_status: Mapped[str] = mapped_column(String(40), default="not_started", nullable=False, index=True)
    onboarding_status: Mapped[str] = mapped_column(String(40), default="invited", nullable=False, index=True)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    emergency_contact: Mapped[str | None] = mapped_column(String(240))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class VolunteerOpportunity(IdMixin, TimestampMixin, Base):
    __tablename__ = "volunteer_opportunities"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    role_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    required_skills_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    location: Mapped[str | None] = mapped_column(String(240))
    slots_required: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    min_age: Mapped[int | None] = mapped_column(Integer)
    background_check_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    training_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    public_signup: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(40), default="normal", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False, index=True)


class VolunteerNeedRequest(IdMixin, TimestampMixin, Base):
    __tablename__ = "volunteer_need_requests"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("events.id"), index=True)
    requested_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    role_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    needed_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    required_skills_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    needed_by: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    priority: Mapped[str] = mapped_column(String(40), default="normal", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="requested", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    opportunity_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("volunteer_opportunities.id"), index=True)


class VolunteerAssignment(IdMixin, TimestampMixin, Base):
    __tablename__ = "volunteer_assignments"
    __table_args__ = (
        UniqueConstraint("opportunity_id", "volunteer_profile_id", name="uq_volunteer_assignments_opportunity_profile"),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    opportunity_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("volunteer_opportunities.id"), nullable=False, index=True)
    volunteer_profile_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("volunteer_profiles.id"), nullable=False, index=True)
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), nullable=False, index=True)
    assigned_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="assigned", nullable=False, index=True)
    match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checked_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hours_logged: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class VolunteerGroupApplication(IdMixin, TimestampMixin, Base):
    __tablename__ = "volunteer_group_applications"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    opportunity_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("volunteer_opportunities.id"), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    coordinator_name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    coordinator_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    coordinator_phone: Mapped[str | None] = mapped_column(String(64))
    group_size: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_slots: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_slots: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skills_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    availability_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False, index=True)
    reviewed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    review_notes: Mapped[str | None] = mapped_column(Text)


class VolunteerTrainingRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "volunteer_training_records"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    volunteer_profile_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("volunteer_profiles.id"), nullable=False, index=True)
    module_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    role_type: Mapped[str | None] = mapped_column(String(80), index=True)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="assigned", nullable=False, index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    expires_on: Mapped[date | None] = mapped_column(Date, index=True)
    score: Mapped[float | None] = mapped_column(Float)
    certificate_url: Mapped[str | None] = mapped_column(String(500))


class VolunteerObligation(IdMixin, TimestampMixin, Base):
    __tablename__ = "volunteer_obligations"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "person_id",
            "season_label",
            "category",
            name="uq_volunteer_obligations_org_person_season_category",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), nullable=False, index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    season_label: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), default="family_service", nullable=False, index=True)
    required_hours: Mapped[float] = mapped_column(Float, nullable=False)
    completed_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    waived_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    due_on: Mapped[date | None] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class VolunteerRecognition(IdMixin, TimestampMixin, Base):
    __tablename__ = "volunteer_recognitions"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    volunteer_profile_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("volunteer_profiles.id"), nullable=False, index=True)
    recognition_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    badge_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    awarded_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source_summary: Mapped[str | None] = mapped_column(Text)
