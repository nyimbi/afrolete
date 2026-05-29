from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin


class CommunityPost(IdMixin, TimestampMixin, Base):
    __tablename__ = "community_posts"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    author_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    post_type: Mapped[str] = mapped_column(String(60), default="announcement", nullable=False, index=True)
    visibility: Mapped[str] = mapped_column(String(60), default="organization", nullable=False, index=True)
    media_url: Mapped[str | None] = mapped_column(String(500))
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="published", nullable=False, index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class CommunityComment(IdMixin, TimestampMixin, Base):
    __tablename__ = "community_comments"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    post_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("community_posts.id"), index=True)
    author_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="published", nullable=False, index=True)


class CommunityReaction(IdMixin, TimestampMixin, Base):
    __tablename__ = "community_reactions"
    __table_args__ = (UniqueConstraint("post_id", "person_id", "reaction_type"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    post_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("community_posts.id"), index=True)
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    reaction_type: Mapped[str] = mapped_column(String(40), default="like", nullable=False, index=True)


class FanPoll(IdMixin, TimestampMixin, Base):
    __tablename__ = "fan_polls"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("teams.id"), index=True)
    post_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("community_posts.id"), index=True)
    question: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    audience: Mapped[str] = mapped_column(String(60), default="supporters", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False, index=True)
    closes_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class FanPollOption(IdMixin, TimestampMixin, Base):
    __tablename__ = "fan_poll_options"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    poll_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("fan_polls.id"), index=True)
    label: Mapped[str] = mapped_column(String(180), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)


class FanPollVote(IdMixin, TimestampMixin, Base):
    __tablename__ = "fan_poll_votes"
    __table_args__ = (UniqueConstraint("poll_id", "person_id"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    poll_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("fan_polls.id"), index=True)
    option_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("fan_poll_options.id"), index=True)
    person_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)


class SupporterMembershipTier(IdMixin, TimestampMixin, Base):
    __tablename__ = "supporter_membership_tiers"
    __table_args__ = (UniqueConstraint("organization_id", "slug"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    monthly_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    benefits: Mapped[str] = mapped_column(Text, default="", nullable=False)
    voting_weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    trial_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class SupporterProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "supporter_profiles"
    __table_args__ = (UniqueConstraint("organization_id", "email"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    tier_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("supporter_membership_tiers.id"), index=True)
    display_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    engagement_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    lifetime_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    last_engagement_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class SupporterEngagementActivity(IdMixin, TimestampMixin, Base):
    __tablename__ = "supporter_engagement_activities"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    supporter_profile_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("supporter_profiles.id"), index=True)
    activity_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(120), default="manual", nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    value_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class SupporterReward(IdMixin, TimestampMixin, Base):
    __tablename__ = "supporter_rewards"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    supporter_profile_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("supporter_profiles.id"), index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    reward_type: Mapped[str] = mapped_column(String(80), default="experience", nullable=False, index=True)
    threshold_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="earned", nullable=False, index=True)
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class AlumniProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "alumni_profiles"
    __table_args__ = (UniqueConstraint("organization_id", "email"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    display_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, index=True)
    sports_history: Mapped[str] = mapped_column(Text, default="", nullable=False)
    career_industry: Mapped[str | None] = mapped_column(String(120), index=True)
    current_company: Mapped[str | None] = mapped_column(String(180))
    current_role: Mapped[str | None] = mapped_column(String(180))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    engagement_level: Mapped[str] = mapped_column(String(40), default="new", nullable=False, index=True)
    lifetime_donations: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    privacy_status: Mapped[str] = mapped_column(String(40), default="network_visible", nullable=False, index=True)
    last_engagement_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class MentorshipProgram(IdMixin, TimestampMixin, Base):
    __tablename__ = "mentorship_programs"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    goals: Mapped[str] = mapped_column(Text, nullable=False)
    industry_focus: Mapped[str | None] = mapped_column(String(120), index=True)
    capacity: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    starts_on: Mapped[date | None] = mapped_column(Date, index=True)
    ends_on: Mapped[date | None] = mapped_column(Date, index=True)


class MentorshipMatch(IdMixin, TimestampMixin, Base):
    __tablename__ = "mentorship_matches"

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    program_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("mentorship_programs.id"), index=True)
    alumni_profile_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("alumni_profiles.id"), index=True)
    mentee_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    mentee_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    mentee_interest: Mapped[str] = mapped_column(String(180), default="", nullable=False, index=True)
    match_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    goals: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="proposed", nullable=False, index=True)
    next_meeting_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    feedback_notes: Mapped[str | None] = mapped_column(Text)
