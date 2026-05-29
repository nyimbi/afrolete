from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CommunityPostCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    title: str = Field(min_length=2, max_length=220)
    body: str = Field(min_length=2, max_length=8000)
    post_type: str = Field(default="announcement", min_length=2, max_length=60)
    visibility: str = Field(default="organization", min_length=2, max_length=60)
    media_url: str | None = Field(default=None, max_length=500)
    pinned: bool = False


class CommunityPostRead(CommunityPostCreate):
    id: UUID
    author_person_id: UUID | None
    status: str
    published_at: datetime
    comment_count: int = 0
    reaction_count: int = 0
    poll_count: int = 0


class CommunityCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class CommunityCommentRead(BaseModel):
    id: UUID
    organization_id: UUID
    post_id: UUID
    author_person_id: UUID | None
    body: str
    status: str
    created_at: datetime


class CommunityReactionCreate(BaseModel):
    reaction_type: str = Field(default="like", min_length=2, max_length=40)


class CommunityReactionRead(BaseModel):
    id: UUID
    organization_id: UUID
    post_id: UUID
    person_id: UUID
    reaction_type: str
    created_at: datetime


class FanPollOptionCreate(BaseModel):
    label: str = Field(min_length=1, max_length=180)


class FanPollCreate(BaseModel):
    organization_id: UUID
    team_id: UUID | None = None
    post_id: UUID | None = None
    question: str = Field(min_length=2, max_length=240)
    audience: str = Field(default="supporters", min_length=2, max_length=60)
    closes_at: datetime | None = None
    options: list[FanPollOptionCreate] = Field(min_length=2, max_length=8)


class FanPollOptionRead(BaseModel):
    id: UUID
    poll_id: UUID
    label: str
    sequence: int
    vote_count: int = 0


class FanPollRead(BaseModel):
    id: UUID
    organization_id: UUID
    team_id: UUID | None
    post_id: UUID | None
    question: str
    audience: str
    status: str
    closes_at: datetime | None
    total_votes: int
    options: list[FanPollOptionRead]


class FanPollVoteCreate(BaseModel):
    option_id: UUID


class FanPollVoteRead(BaseModel):
    id: UUID
    organization_id: UUID
    poll_id: UUID
    option_id: UUID
    person_id: UUID
    created_at: datetime


class CommunityEngagementSummaryRead(BaseModel):
    organization_id: UUID
    post_count: int
    pinned_post_count: int
    comment_count: int
    reaction_count: int
    poll_count: int
    open_poll_count: int
    vote_count: int
    engagement_score: int
    recommendations: list[str]


class SupporterMembershipTierCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=120)
    monthly_price: Decimal = Decimal("0.00")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    benefits: str = Field(default="", max_length=4000)
    voting_weight: int = Field(default=1, ge=1, le=100)
    trial_days: int = Field(default=0, ge=0, le=365)


class SupporterMembershipTierRead(SupporterMembershipTierCreate):
    id: UUID
    status: str


class SupporterProfileCreate(BaseModel):
    organization_id: UUID
    person_id: UUID | None = None
    tier_id: UUID | None = None
    display_name: str = Field(min_length=2, max_length=180)
    email: str = Field(min_length=3, max_length=320)
    lifetime_value: Decimal = Decimal("0.00")
    notes: str | None = Field(default=None, max_length=4000)


class SupporterProfileRead(SupporterProfileCreate):
    id: UUID
    engagement_points: int
    status: str
    joined_at: datetime
    last_engagement_at: datetime | None
    tier_name: str | None = None
    tier_voting_weight: int | None = None


class SupporterEngagementActivityCreate(BaseModel):
    activity_type: str = Field(min_length=2, max_length=80)
    source: str = Field(default="manual", min_length=2, max_length=120)
    description: str = Field(default="", max_length=4000)
    points: int = Field(default=0, ge=0, le=100000)
    value_amount: Decimal = Decimal("0.00")
    occurred_at: datetime | None = None


class SupporterEngagementActivityRead(BaseModel):
    id: UUID
    organization_id: UUID
    supporter_profile_id: UUID
    activity_type: str
    source: str
    description: str
    points: int
    value_amount: Decimal
    occurred_at: datetime


class SupporterRewardCreate(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    reward_type: str = Field(default="experience", min_length=2, max_length=80)
    threshold_points: int = Field(default=0, ge=0, le=1000000)


class SupporterRewardRead(BaseModel):
    id: UUID
    organization_id: UUID
    supporter_profile_id: UUID
    title: str
    reward_type: str
    threshold_points: int
    status: str
    redeemed_at: datetime | None


class SupporterDashboardRead(BaseModel):
    organization_id: UUID
    tier_count: int
    supporter_count: int
    active_supporter_count: int
    total_points: int
    total_lifetime_value: Decimal
    reward_count: int
    top_supporter_name: str | None
    recommendations: list[str]


class AlumniProfileCreate(BaseModel):
    organization_id: UUID
    person_id: UUID | None = None
    display_name: str = Field(min_length=2, max_length=180)
    email: str = Field(min_length=3, max_length=320)
    graduation_year: int | None = Field(default=None, ge=1900, le=2200)
    sports_history: str = Field(default="", max_length=4000)
    career_industry: str | None = Field(default=None, max_length=120)
    current_company: str | None = Field(default=None, max_length=180)
    current_role: str | None = Field(default=None, max_length=180)
    linkedin_url: str | None = Field(default=None, max_length=500)
    engagement_level: str = Field(default="new", min_length=2, max_length=40)
    lifetime_donations: Decimal = Decimal("0.00")
    privacy_status: str = Field(default="network_visible", min_length=2, max_length=40)
    notes: str | None = Field(default=None, max_length=4000)


class AlumniProfileRead(AlumniProfileCreate):
    id: UUID
    last_engagement_at: datetime | None


class MentorshipProgramCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    goals: str = Field(min_length=2, max_length=4000)
    industry_focus: str | None = Field(default=None, max_length=120)
    capacity: int = Field(default=20, ge=1, le=10000)
    starts_on: date | None = None
    ends_on: date | None = None


class MentorshipProgramRead(MentorshipProgramCreate):
    id: UUID
    status: str
    match_count: int = 0


class MentorshipMatchCreate(BaseModel):
    alumni_profile_id: UUID
    mentee_person_id: UUID | None = None
    mentee_name: str = Field(min_length=2, max_length=180)
    mentee_interest: str = Field(default="", max_length=180)
    goals: str = Field(default="", max_length=4000)
    next_meeting_at: datetime | None = None


class MentorshipMatchRead(BaseModel):
    id: UUID
    organization_id: UUID
    program_id: UUID
    alumni_profile_id: UUID
    alumni_name: str | None = None
    mentee_person_id: UUID | None
    mentee_name: str
    mentee_interest: str
    match_score: int
    goals: str
    status: str
    next_meeting_at: datetime | None
    feedback_notes: str | None


class AlumniDashboardRead(BaseModel):
    organization_id: UUID
    alumni_count: int
    active_alumni_count: int
    mentorship_program_count: int
    mentorship_match_count: int
    lifetime_donations: Decimal
    mentor_capacity: int
    recommendations: list[str]
