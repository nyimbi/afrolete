from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.community import (
    CommunityComment,
    CommunityPost,
    CommunityReaction,
    FanPoll,
    FanPollOption,
    FanPollVote,
)
from app.models.organization import Organization
from app.models.team import Team
from app.schemas.community import (
    CommunityCommentCreate,
    CommunityEngagementSummaryRead,
    CommunityPostCreate,
    CommunityPostRead,
    CommunityReactionCreate,
    FanPollCreate,
    FanPollOptionRead,
    FanPollRead,
    FanPollVoteCreate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService


async def ensure_manage_community(
    authz: AuthorizationService,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> None:
    allowed = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    ) or await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage_roster",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def create_community_post(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: CommunityPostCreate,
    authz: AuthorizationService,
) -> CommunityPost:
    await get_organization(db, payload.organization_id)
    await ensure_manage_community(authz, identity, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    post = CommunityPost(
        **payload.model_dump(),
        author_person_id=identity.person_id,
        published_at=datetime.now(UTC),
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def list_community_posts(
    db: AsyncSession,
    organization_id: UUID,
    *,
    team_id: UUID | None = None,
) -> list[CommunityPostRead]:
    statement = select(CommunityPost).where(CommunityPost.organization_id == organization_id)
    if team_id is not None:
        statement = statement.where(CommunityPost.team_id == team_id)
    posts = list(
        (
            await db.scalars(
                statement.order_by(CommunityPost.pinned.desc(), CommunityPost.published_at.desc())
            )
        ).all()
    )
    if not posts:
        return []
    post_ids = [post.id for post in posts]
    comment_counts = await count_by_post(db, CommunityComment.post_id, CommunityComment, post_ids)
    reaction_counts = await count_by_post(db, CommunityReaction.post_id, CommunityReaction, post_ids)
    poll_counts = await count_by_post(db, FanPoll.post_id, FanPoll, post_ids)
    return [
        community_post_read(
            post,
            comment_count=comment_counts.get(post.id, 0),
            reaction_count=reaction_counts.get(post.id, 0),
            poll_count=poll_counts.get(post.id, 0),
        )
        for post in posts
    ]


async def add_community_comment(
    db: AsyncSession,
    identity: CurrentIdentity,
    post_id: UUID,
    payload: CommunityCommentCreate,
) -> CommunityComment:
    post = await get_community_post(db, post_id)
    comment = CommunityComment(
        organization_id=post.organization_id,
        post_id=post.id,
        author_person_id=identity.person_id,
        body=payload.body,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def list_community_comments(db: AsyncSession, post_id: UUID) -> list[CommunityComment]:
    return list(
        (
            await db.scalars(
                select(CommunityComment)
                .where(CommunityComment.post_id == post_id)
                .order_by(CommunityComment.created_at)
            )
        ).all()
    )


async def add_community_reaction(
    db: AsyncSession,
    identity: CurrentIdentity,
    post_id: UUID,
    payload: CommunityReactionCreate,
) -> CommunityReaction:
    post = await get_community_post(db, post_id)
    existing = await db.scalar(
        select(CommunityReaction).where(
            CommunityReaction.post_id == post.id,
            CommunityReaction.person_id == identity.person_id,
            CommunityReaction.reaction_type == payload.reaction_type,
        )
    )
    if existing is not None:
        return existing
    reaction = CommunityReaction(
        organization_id=post.organization_id,
        post_id=post.id,
        person_id=identity.person_id,
        reaction_type=payload.reaction_type,
    )
    db.add(reaction)
    await db.commit()
    await db.refresh(reaction)
    return reaction


async def create_fan_poll(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FanPollCreate,
    authz: AuthorizationService,
) -> FanPollRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_community(authz, identity, payload.organization_id)
    if payload.team_id is not None:
        await get_team_for_organization(db, payload.team_id, payload.organization_id)
    if payload.post_id is not None:
        post = await get_community_post(db, payload.post_id)
        if post.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community post not found")
    poll = FanPoll(
        organization_id=payload.organization_id,
        team_id=payload.team_id,
        post_id=payload.post_id,
        question=payload.question,
        audience=payload.audience,
        closes_at=payload.closes_at,
    )
    db.add(poll)
    await db.flush()
    options = []
    for index, option in enumerate(payload.options, start=1):
        poll_option = FanPollOption(
            organization_id=payload.organization_id,
            poll_id=poll.id,
            label=option.label,
            sequence=index,
        )
        db.add(poll_option)
        options.append(poll_option)
    await db.commit()
    await db.refresh(poll)
    for option in options:
        await db.refresh(option)
    return fan_poll_read(poll, options, {})


async def list_fan_polls(
    db: AsyncSession,
    organization_id: UUID,
    *,
    team_id: UUID | None = None,
) -> list[FanPollRead]:
    statement = select(FanPoll).where(FanPoll.organization_id == organization_id)
    if team_id is not None:
        statement = statement.where(FanPoll.team_id == team_id)
    polls = list(
        (
            await db.scalars(
                statement.order_by(FanPoll.created_at.desc())
            )
        ).all()
    )
    if not polls:
        return []
    poll_ids = [poll.id for poll in polls]
    options = list(
        (
            await db.scalars(
                select(FanPollOption)
                .where(FanPollOption.poll_id.in_(poll_ids))
                .order_by(FanPollOption.sequence)
            )
        ).all()
    )
    vote_counts = await count_by_option(db, [option.id for option in options])
    options_by_poll: dict[UUID, list[FanPollOption]] = {}
    for option in options:
        options_by_poll.setdefault(option.poll_id, []).append(option)
    return [fan_poll_read(poll, options_by_poll.get(poll.id, []), vote_counts) for poll in polls]


async def vote_fan_poll(
    db: AsyncSession,
    identity: CurrentIdentity,
    poll_id: UUID,
    payload: FanPollVoteCreate,
) -> FanPollVote:
    poll = await db.get(FanPoll, poll_id)
    if poll is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fan poll not found")
    if poll.status != "open":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Fan poll is closed")
    option = await db.get(FanPollOption, payload.option_id)
    if option is None or option.poll_id != poll.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fan poll option not found")
    existing = await db.scalar(
        select(FanPollVote).where(
            FanPollVote.poll_id == poll.id,
            FanPollVote.person_id == identity.person_id,
        )
    )
    if existing is not None:
        existing.option_id = option.id
        await db.commit()
        await db.refresh(existing)
        return existing
    vote = FanPollVote(
        organization_id=poll.organization_id,
        poll_id=poll.id,
        option_id=option.id,
        person_id=identity.person_id,
    )
    db.add(vote)
    await db.commit()
    await db.refresh(vote)
    return vote


async def community_engagement_summary(db: AsyncSession, organization_id: UUID) -> CommunityEngagementSummaryRead:
    post_count = await scalar_count(db, CommunityPost, organization_id)
    pinned_count = await scalar_count(db, CommunityPost, organization_id, CommunityPost.pinned.is_(True))
    comment_count = await scalar_count(db, CommunityComment, organization_id)
    reaction_count = await scalar_count(db, CommunityReaction, organization_id)
    poll_count = await scalar_count(db, FanPoll, organization_id)
    open_poll_count = await scalar_count(db, FanPoll, organization_id, FanPoll.status == "open")
    vote_count = await scalar_count(db, FanPollVote, organization_id)
    engagement_score = min(100, post_count * 15 + comment_count * 4 + reaction_count * 3 + poll_count * 10 + vote_count * 6)
    return CommunityEngagementSummaryRead(
        organization_id=organization_id,
        post_count=post_count,
        pinned_post_count=pinned_count,
        comment_count=comment_count,
        reaction_count=reaction_count,
        poll_count=poll_count,
        open_poll_count=open_poll_count,
        vote_count=vote_count,
        engagement_score=engagement_score,
        recommendations=community_recommendations(post_count, pinned_count, comment_count, poll_count, vote_count),
    )


def community_post_read(
    post: CommunityPost,
    *,
    comment_count: int = 0,
    reaction_count: int = 0,
    poll_count: int = 0,
) -> CommunityPostRead:
    return CommunityPostRead(
        id=post.id,
        organization_id=post.organization_id,
        team_id=post.team_id,
        author_person_id=post.author_person_id,
        title=post.title,
        body=post.body,
        post_type=post.post_type,
        visibility=post.visibility,
        media_url=post.media_url,
        pinned=post.pinned,
        status=post.status,
        published_at=post.published_at,
        comment_count=comment_count,
        reaction_count=reaction_count,
        poll_count=poll_count,
    )


def fan_poll_read(
    poll: FanPoll,
    options: list[FanPollOption],
    vote_counts: dict[UUID, int],
) -> FanPollRead:
    option_reads = [
        FanPollOptionRead(
            id=option.id,
            poll_id=option.poll_id,
            label=option.label,
            sequence=option.sequence,
            vote_count=vote_counts.get(option.id, 0),
        )
        for option in options
    ]
    return FanPollRead(
        id=poll.id,
        organization_id=poll.organization_id,
        team_id=poll.team_id,
        post_id=poll.post_id,
        question=poll.question,
        audience=poll.audience,
        status=poll.status,
        closes_at=poll.closes_at,
        total_votes=sum(option.vote_count for option in option_reads),
        options=option_reads,
    )


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def get_team_for_organization(db: AsyncSession, team_id: UUID, organization_id: UUID) -> Team:
    team = await db.get(Team, team_id)
    if team is None or team.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


async def get_community_post(db: AsyncSession, post_id: UUID) -> CommunityPost:
    post = await db.get(CommunityPost, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community post not found")
    return post


async def count_by_post(db: AsyncSession, field, model, post_ids: list[UUID]) -> dict[UUID, int]:
    rows = (await db.execute(select(field, func.count(model.id)).where(field.in_(post_ids)).group_by(field))).all()
    return {post_id: count for post_id, count in rows}


async def count_by_option(db: AsyncSession, option_ids: list[UUID]) -> dict[UUID, int]:
    if not option_ids:
        return {}
    rows = (
        await db.execute(
            select(FanPollVote.option_id, func.count(FanPollVote.id))
            .where(FanPollVote.option_id.in_(option_ids))
            .group_by(FanPollVote.option_id)
        )
    ).all()
    return {option_id: count for option_id, count in rows}


async def scalar_count(db: AsyncSession, model, organization_id: UUID, *conditions) -> int:
    statement = select(func.count(model.id)).where(model.organization_id == organization_id)
    for condition in conditions:
        statement = statement.where(condition)
    return int(await db.scalar(statement) or 0)


def community_recommendations(
    post_count: int,
    pinned_count: int,
    comment_count: int,
    poll_count: int,
    vote_count: int,
) -> list[str]:
    recommendations: list[str] = []
    if not post_count:
        recommendations.append("Publish a kickoff post with club news, match context, or training highlights.")
    if not pinned_count:
        recommendations.append("Pin one post so families, players, and supporters see the current priority first.")
    if post_count and not comment_count:
        recommendations.append("Invite comments from families or team members to turn announcements into conversation.")
    if not poll_count:
        recommendations.append("Create a fan poll for player of the match, jersey choice, travel interest, or event feedback.")
    if poll_count and not vote_count:
        recommendations.append("Share the poll through communications and the public site to gather supporter input.")
    if not recommendations:
        recommendations.append("Community engagement is active; keep posts, polls, and moderation current.")
    return recommendations[:6]
