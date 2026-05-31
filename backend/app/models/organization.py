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


class OrganizationAwardProgram(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_award_programs"
    __table_args__ = (UniqueConstraint("organization_id", "name", "season_label"),)

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    season_label: Mapped[str | None] = mapped_column(String(80), index=True)
    level: Mapped[str] = mapped_column(String(80), default="club", nullable=False, index=True)
    frequency: Mapped[str] = mapped_column(
        String(80), default="seasonal", nullable=False, index=True
    )
    nomination_opens_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    nomination_closes_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    voting_opens_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    voting_closes_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    eligibility_summary: Mapped[str | None] = mapped_column(Text)
    ceremony_name: Mapped[str | None] = mapped_column(String(180))
    ceremony_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    ceremony_venue: Mapped[str | None] = mapped_column(String(240))
    certificate_template: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class OrganizationAwardCategory(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_award_categories"
    __table_args__ = (UniqueConstraint("program_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    program_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organization_award_programs.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    award_type: Mapped[str] = mapped_column(
        String(80), default="individual", nullable=False, index=True
    )
    judging_method: Mapped[str] = mapped_column(
        String(80), default="committee", nullable=False, index=True
    )
    criteria: Mapped[str | None] = mapped_column(Text)
    max_recipients: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    voter_roles: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class OrganizationAwardNomination(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_award_nominations"
    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "nominee_subject_type",
            "nominee_subject_id",
            name="uq_organization_award_nominations_nominee",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    program_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organization_award_programs.id"), index=True
    )
    category_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organization_award_categories.id"), index=True
    )
    nominee_subject_type: Mapped[MemberSubjectType] = mapped_column(
        enum_type(MemberSubjectType), nullable=False, index=True
    )
    nominee_subject_id: Mapped[UUID] = mapped_column(GUID(), index=True)
    nominated_by_person_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("persons.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    nomination_summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String(40), default="submitted", nullable=False, index=True
    )
    finalist: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))


class OrganizationAwardVote(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_award_votes"
    __table_args__ = (
        UniqueConstraint("nomination_id", "voter_person_id", name="uq_organization_award_votes_voter"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    nomination_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organization_award_nominations.id"), index=True
    )
    voter_person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    score: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("1"), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)


class OrganizationAwardRecipient(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_award_recipients"
    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "recipient_subject_type",
            "recipient_subject_id",
            name="uq_organization_award_recipients_subject",
        ),
        UniqueConstraint("organization_id", "certificate_number"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    program_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organization_award_programs.id"), index=True
    )
    category_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organization_award_categories.id"), index=True
    )
    nomination_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("organization_award_nominations.id"), index=True
    )
    recipient_subject_type: Mapped[MemberSubjectType] = mapped_column(
        enum_type(MemberSubjectType), nullable=False, index=True
    )
    recipient_subject_id: Mapped[UUID] = mapped_column(GUID(), index=True)
    certificate_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    awarded_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    public_citation: Mapped[str] = mapped_column(Text, nullable=False)
    certificate_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(40), default="awarded", nullable=False, index=True)


class OrganizationDataMigrationProject(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_data_migration_projects"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    source_system: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source_format: Mapped[str] = mapped_column(String(80), default="csv", nullable=False, index=True)
    migration_type: Mapped[str] = mapped_column(String(80), default="initial_import", nullable=False, index=True)
    data_domains: Mapped[str | None] = mapped_column(Text)
    owner_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="planning", nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(40), default="medium", nullable=False, index=True)
    records_expected: Mapped[int | None] = mapped_column(Integer)
    records_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class OrganizationDataMigrationRun(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_data_migration_runs"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    project_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organization_data_migration_projects.id"), index=True)
    run_type: Mapped[str] = mapped_column(String(80), default="validation", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False, index=True)
    input_artifact_url: Mapped[str | None] = mapped_column(String(500))
    mapping_summary: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    records_seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), index=True)
    report_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)


class OrganizationRecoveryPlan(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_recovery_plans"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(160), default="tenant_operational_data", nullable=False, index=True)
    rpo_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    rto_minutes: Mapped[int] = mapped_column(Integer, default=240, nullable=False)
    backup_frequency: Mapped[str] = mapped_column(String(80), default="daily", nullable=False, index=True)
    storage_location: Mapped[str | None] = mapped_column(String(500))
    retention_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    encryption_policy: Mapped[str | None] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    next_test_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class OrganizationRecoveryDrill(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_recovery_drills"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    recovery_plan_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organization_recovery_plans.id"), index=True)
    drill_type: Mapped[str] = mapped_column(String(80), default="restore_test", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="planned", nullable=False, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    rpo_minutes_observed: Mapped[int | None] = mapped_column(Integer)
    rto_minutes_observed: Mapped[int | None] = mapped_column(Integer)
    data_loss_summary: Mapped[str | None] = mapped_column(Text)
    result_summary: Mapped[str | None] = mapped_column(Text)
    action_items: Mapped[str | None] = mapped_column(Text)
    evidence_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)


class OrganizationComplianceDocument(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_compliance_documents"
    __table_args__ = (UniqueConstraint("organization_id", "title", "document_type"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), default="legal_regulatory", nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    subject_type: Mapped[str | None] = mapped_column(String(80), index=True)
    subject_id: Mapped[UUID | None] = mapped_column(GUID(), index=True)
    owner_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    issuer: Mapped[str | None] = mapped_column(String(180), index=True)
    reference_number: Mapped[str | None] = mapped_column(String(180), index=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    renewal_status: Mapped[str] = mapped_column(String(40), default="not_required", nullable=False, index=True)
    effective_on: Mapped[date | None] = mapped_column(Date, index=True)
    expires_on: Mapped[date | None] = mapped_column(Date, index=True)
    next_review_on: Mapped[date | None] = mapped_column(Date, index=True)
    retention_until: Mapped[date | None] = mapped_column(Date, index=True)
    auto_renewal_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    storage_url: Mapped[str | None] = mapped_column(String(500))
    checksum: Mapped[str | None] = mapped_column(String(128), index=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    confidentiality: Mapped[str] = mapped_column(String(40), default="internal", nullable=False, index=True)
    tags: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class OrganizationComplianceDocumentVersion(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_compliance_document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version_number"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    document_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organization_compliance_documents.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    storage_url: Mapped[str | None] = mapped_column(String(500))
    checksum: Mapped[str | None] = mapped_column(String(128), index=True)
    filename: Mapped[str | None] = mapped_column(String(240))
    content_type: Mapped[str | None] = mapped_column(String(120))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    change_summary: Mapped[str | None] = mapped_column(Text)
    uploaded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    verified_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(40), default="current", nullable=False, index=True)


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
    dues_last_reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    dues_reminder_message_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("communication_messages.id"), index=True
    )
    dues_reminder_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class MemberSubscriptionCharge(IdMixin, TimestampMixin, Base):
    __tablename__ = "member_subscription_charges"
    __table_args__ = (
        UniqueConstraint(
            "subscription_id",
            "period_start",
            "period_end",
            name="uq_member_subscription_charges_period",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    subscription_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("member_subscriptions.id"), index=True)
    plan_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("member_subscription_plans.id"), index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_on: Mapped[date | None] = mapped_column(Date, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    amount_waived: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    balance_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(80), default="recurring_cycle", nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_payment_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("member_subscription_payments.id"), index=True)
    waived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    waived_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    waiver_reason: Mapped[str | None] = mapped_column(Text)
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)


class MemberSubscriptionPayment(IdMixin, TimestampMixin, Base):
    __tablename__ = "member_subscription_payments"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    subscription_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("member_subscriptions.id"), index=True)
    payment_plan_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("member_subscription_payment_plans.id"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False)
    provider: Mapped[str] = mapped_column(String(80), default="mpesa", nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(80), default="mobile_money", nullable=False, index=True)
    external_payment_id: Mapped[str | None] = mapped_column(String(180), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="succeeded", nullable=False, index=True)
    raw_reference: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class MemberSubscriptionPaymentPlan(IdMixin, TimestampMixin, Base):
    __tablename__ = "member_subscription_payment_plans"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    subscription_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("member_subscriptions.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    plan_type: Mapped[str] = mapped_column(String(80), default="installment", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False)
    installment_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    installment_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    paid_installment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    installment_frequency: Mapped[str] = mapped_column(String(40), default="monthly", nullable=False, index=True)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    next_due_on: Mapped[date | None] = mapped_column(Date, index=True)
    ends_on: Mapped[date | None] = mapped_column(Date, index=True)
    approved_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class OrganizationFinancialAidProgram(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_financial_aid_programs"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    program_type: Mapped[str] = mapped_column(String(80), default="need_based", nullable=False, index=True)
    sport: Mapped[str | None] = mapped_column(String(80), index=True)
    age_group: Mapped[str | None] = mapped_column(String(80), index=True)
    fund_source: Mapped[str | None] = mapped_column(String(180), index=True)
    annual_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    budget_awarded: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False)
    awards_available: Mapped[int | None] = mapped_column(Integer)
    awards_made: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    minimum_score: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    application_opens_on: Mapped[date | None] = mapped_column(Date, index=True)
    application_deadline_on: Mapped[date | None] = mapped_column(Date, index=True)
    awards_announced_on: Mapped[date | None] = mapped_column(Date, index=True)
    eligibility_criteria: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class OrganizationFinancialAidApplication(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_financial_aid_applications"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    program_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organization_financial_aid_programs.id"), index=True)
    applicant_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    athlete_profile_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("athlete_profiles.id"), index=True)
    member_subscription_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("member_subscriptions.id"), index=True)
    household_income: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    household_size: Mapped[int | None] = mapped_column(Integer)
    government_assistance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    academic_summary: Mapped[str | None] = mapped_column(Text)
    athletic_summary: Mapped[str | None] = mapped_column(Text)
    financial_need_summary: Mapped[str | None] = mapped_column(Text)
    personal_statement: Mapped[str | None] = mapped_column(Text)
    amount_requested: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_awarded: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    amount_applied: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False)
    eligibility_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    review_score: Mapped[int | None] = mapped_column(Integer)
    committee_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    decision_reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="submitted", nullable=False, index=True)
    submitted_on: Mapped[date | None] = mapped_column(Date, index=True)
    decided_on: Mapped[date | None] = mapped_column(Date, index=True)
    decided_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class OrganizationMarketProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_market_profiles"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "country_code",
            "region_code",
            name="uq_organization_market_profiles_scope",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    region_code: Mapped[str | None] = mapped_column(String(80), index=True)
    locale: Mapped[str] = mapped_column(String(16), default="en-KE", nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(String(80), default="Africa/Nairobi", nullable=False)
    default_currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False, index=True)
    reporting_currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False, index=True)
    exchange_rate_source: Mapped[str | None] = mapped_column(String(160))
    exchange_rate_margin_bps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    season_rate_lock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    primary_payment_method: Mapped[str] = mapped_column(String(80), default="mpesa", nullable=False, index=True)
    supported_payment_methods_json: Mapped[str | None] = mapped_column(Text)
    mobile_money_providers_json: Mapped[str | None] = mapped_column(Text)
    cash_collection_points_json: Mapped[str | None] = mapped_column(Text)
    bank_integrations_json: Mapped[str | None] = mapped_column(Text)
    tax_authority: Mapped[str | None] = mapped_column(String(180), index=True)
    tax_registration_number: Mapped[str | None] = mapped_column(String(120), index=True)
    tax_profile: Mapped[str | None] = mapped_column(String(120), index=True)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    tax_exempt_categories_json: Mapped[str | None] = mapped_column(Text)
    government_reporting_agencies_json: Mapped[str | None] = mapped_column(Text)
    federation_reporting_templates_json: Mapped[str | None] = mapped_column(Text)
    compliance_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class OrganizationExternalReport(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_external_reports"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "target_agency",
            "report_code",
            "reporting_period_start",
            "reporting_period_end",
            name="uq_organization_external_reports_period",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    market_profile_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("organization_market_profiles.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    report_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(80), default="federation", nullable=False, index=True)
    target_agency: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(80), default="federation", nullable=False, index=True)
    reporting_period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reporting_period_end: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    submission_format: Mapped[str] = mapped_column(String(40), default="pdf", nullable=False, index=True)
    data_elements_json: Mapped[str | None] = mapped_column(Text)
    source_summary: Mapped[str | None] = mapped_column(Text)
    generated_payload: Mapped[str | None] = mapped_column(Text)
    submission_payload: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    external_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
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
