from datetime import datetime
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
