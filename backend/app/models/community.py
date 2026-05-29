from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
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
