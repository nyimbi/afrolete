from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin, enum_type
from app.models.enums import (
    AssociationLevel,
    CommitteeRole,
    MemberSubjectType,
    MembershipRole,
    OrganizationType,
)


class Organization(IdMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    organization_type: Mapped[OrganizationType] = mapped_column(
        enum_type(OrganizationType), nullable=False
    )
    association_level: Mapped[AssociationLevel | None] = mapped_column(
        enum_type(AssociationLevel), index=True
    )
    parent_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("organizations.id"))
    country_code: Mapped[str | None] = mapped_column(String(2))
    primary_sport: Mapped[str | None] = mapped_column(String(80))
    mission: Mapped[str | None] = mapped_column(Text)
    public_name: Mapped[str | None] = mapped_column(String(240))
    contact_email: Mapped[str | None] = mapped_column(String(320))
    contact_phone: Mapped[str | None] = mapped_column(String(64))
    website_url: Mapped[str | None] = mapped_column(String(500))
    subdomain: Mapped[str | None] = mapped_column(String(120), unique=True, index=True)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    brand_primary_color: Mapped[str | None] = mapped_column(String(16))
    brand_secondary_color: Mapped[str | None] = mapped_column(String(16))
    registration_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    registration_fee_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    registration_fee_currency: Mapped[str | None] = mapped_column(String(3))
    registration_payment_instructions: Mapped[str | None] = mapped_column(Text)
    registration_required_documents_json: Mapped[str | None] = mapped_column(Text)


class OrganizationProgram(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_programs"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    program_type: Mapped[str] = mapped_column(String(80), default="athlete_development", nullable=False, index=True)
    sport: Mapped[str | None] = mapped_column(String(80), index=True)
    age_group: Mapped[str | None] = mapped_column(String(80), index=True)
    gender_category: Mapped[str | None] = mapped_column(String(80), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    capacity: Mapped[int | None] = mapped_column(Integer)
    starts_on: Mapped[date | None] = mapped_column(Date, index=True)
    ends_on: Mapped[date | None] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class OrganizationSeason(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_seasons"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    sport: Mapped[str | None] = mapped_column(String(80), index=True)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    registration_opens_on: Mapped[date | None] = mapped_column(Date, index=True)
    registration_closes_on: Mapped[date | None] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(40), default="planned", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class OrganizationGroup(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_groups"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    program_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("organization_programs.id"), index=True)
    season_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("organization_seasons.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    lead_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    group_type: Mapped[str] = mapped_column(String(80), default="cohort", nullable=False, index=True)
    sport: Mapped[str | None] = mapped_column(String(80), index=True)
    age_group: Mapped[str | None] = mapped_column(String(80), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    capacity: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class OrganizationGroupMembership(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_group_memberships"
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "subject_type",
            "subject_id",
            "role",
            name="uq_organization_group_memberships_subject_role",
        ),
    )

    group_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organization_groups.id"), index=True)
    subject_type: Mapped[MemberSubjectType] = mapped_column(enum_type(MemberSubjectType), nullable=False, index=True)
    subject_id: Mapped[UUID] = mapped_column(GUID(), index=True)
    role: Mapped[str] = mapped_column(String(80), default="member", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class Membership(IdMixin, TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "subject_type",
            "subject_id",
            "role",
            name="uq_memberships_subject_role",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    subject_type: Mapped[MemberSubjectType] = mapped_column(
        enum_type(MemberSubjectType),
        default=MemberSubjectType.PERSON,
        nullable=False,
        index=True,
    )
    subject_id: Mapped[UUID] = mapped_column(GUID(), index=True)
    role: Mapped[MembershipRole] = mapped_column(
        enum_type(MembershipRole), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)


class MemberSubscriptionPlan(IdMixin, TimestampMixin, Base):
    __tablename__ = "member_subscription_plans"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    member_role: Mapped[str | None] = mapped_column(String(80), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False)
    billing_interval: Mapped[str] = mapped_column(String(40), default="monthly", nullable=False, index=True)
    due_day: Mapped[int | None] = mapped_column(Integer)
    grace_period_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    benefits: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class MemberSubscription(IdMixin, TimestampMixin, Base):
    __tablename__ = "member_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "plan_id",
            "subject_type",
            "subject_id",
            name="uq_member_subscriptions_org_plan_subject",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    plan_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("member_subscription_plans.id"), index=True)
    membership_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("memberships.id"), index=True)
    subject_type: Mapped[MemberSubjectType] = mapped_column(enum_type(MemberSubjectType), nullable=False, index=True)
    subject_id: Mapped[UUID] = mapped_column(GUID(), index=True)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    current_period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    current_period_end: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    next_due_on: Mapped[date | None] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    balance_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class MemberSubscriptionPayment(IdMixin, TimestampMixin, Base):
    __tablename__ = "member_subscription_payments"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    subscription_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("member_subscriptions.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False)
    provider: Mapped[str] = mapped_column(String(80), default="mpesa", nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(80), default="mobile_money", nullable=False, index=True)
    external_payment_id: Mapped[str | None] = mapped_column(String(180), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="succeeded", nullable=False, index=True)
    raw_reference: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class RegistrationInquiry(IdMixin, TimestampMixin, Base):
    __tablename__ = "registration_inquiries"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    athlete_name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    guardian_name: Mapped[str | None] = mapped_column(String(240))
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(64), index=True)
    age_group: Mapped[str | None] = mapped_column(String(80), index=True)
    sport_interest: Mapped[str | None] = mapped_column(String(120), index=True)
    message: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(40), default="new", nullable=False, index=True)
    review_notes: Mapped[str | None] = mapped_column(Text)
    follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    reviewed_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    guardian_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    guardian_contact_status: Mapped[str] = mapped_column(String(40), default="pending_account", nullable=False, index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, index=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(240))
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(64))
    medical_notes: Mapped[str | None] = mapped_column(Text)
    consent_signer_name: Mapped[str | None] = mapped_column(String(240))
    guardian_consent_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    privacy_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    required_documents_json: Mapped[str | None] = mapped_column(Text)
    submitted_documents_json: Mapped[str | None] = mapped_column(Text)
    payment_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    payment_currency: Mapped[str | None] = mapped_column(String(3))
    payment_method: Mapped[str | None] = mapped_column(String(80))
    payment_reference: Mapped[str | None] = mapped_column(String(240), index=True)
    payment_status: Mapped[str] = mapped_column(String(40), default="not_required", nullable=False, index=True)
    verification_status: Mapped[str] = mapped_column(String(40), default="inquiry", nullable=False, index=True)
    packet_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class Committee(IdMixin, TimestampMixin, Base):
    __tablename__ = "committees"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    level: Mapped[AssociationLevel | None] = mapped_column(enum_type(AssociationLevel), index=True)
    mandate: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)


class CommitteeMembership(IdMixin, TimestampMixin, Base):
    __tablename__ = "committee_memberships"
    __table_args__ = (
        UniqueConstraint(
            "committee_id",
            "person_id",
            "role",
            name="uq_committee_memberships_person_role",
        ),
    )

    committee_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("committees.id"), index=True)
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    role: Mapped[CommitteeRole] = mapped_column(
        enum_type(CommitteeRole), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)
