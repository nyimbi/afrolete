from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.community import (
    AlumniProfile,
    CommunityComment,
    CommunityPost,
    CommunityReaction,
    FanPoll,
    FanPollOption,
    FanPollVote,
    MentorshipMatch,
    MentorshipProgram,
    SupporterEngagementActivity,
    SupporterMembershipTier,
    SupporterProfile,
    SupporterReward,
)
from app.models.identity import Person
from app.models.organization import Organization
from app.models.team import Team
from app.schemas.community import (
    AlumniDashboardRead,
    AlumniProfileCreate,
    AlumniProfileRead,
    CommunityCommentCreate,
    CommunityEngagementSummaryRead,
    CommunityPostCreate,
    CommunityPostRead,
    CommunityReactionCreate,
    FanPollCreate,
    FanPollOptionRead,
    FanPollRead,
    FanPollVoteCreate,
    MentorshipMatchCreate,
    MentorshipMatchRead,
    MentorshipProgramCreate,
    MentorshipProgramRead,
    SupporterDashboardRead,
    SupporterEngagementActivityCreate,
    SupporterEngagementActivityRead,
    SupporterMembershipTierCreate,
    SupporterMembershipTierRead,
    SupporterProfileCreate,
    SupporterProfileRead,
    SupporterRewardCreate,
    SupporterRewardRead,
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


async def create_supporter_membership_tier(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SupporterMembershipTierCreate,
    authz: AuthorizationService,
) -> SupporterMembershipTier:
    await get_organization(db, payload.organization_id)
    await ensure_manage_community(authz, identity, payload.organization_id)
    existing = await db.scalar(
        select(SupporterMembershipTier).where(
            SupporterMembershipTier.organization_id == payload.organization_id,
            SupporterMembershipTier.slug == payload.slug,
        )
    )
    if existing is not None:
        existing.name = payload.name
        existing.monthly_price = payload.monthly_price
        existing.currency = payload.currency
        existing.benefits = payload.benefits
        existing.voting_weight = payload.voting_weight
        existing.trial_days = payload.trial_days
        await db.commit()
        await db.refresh(existing)
        return existing
    tier = SupporterMembershipTier(**payload.model_dump())
    db.add(tier)
    await db.commit()
    await db.refresh(tier)
    return tier


async def list_supporter_membership_tiers(
    db: AsyncSession,
    organization_id: UUID,
) -> list[SupporterMembershipTier]:
    return list(
        (
            await db.scalars(
                select(SupporterMembershipTier)
                .where(SupporterMembershipTier.organization_id == organization_id)
                .order_by(SupporterMembershipTier.monthly_price, SupporterMembershipTier.name)
            )
        ).all()
    )


async def create_supporter_profile(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SupporterProfileCreate,
    authz: AuthorizationService,
) -> SupporterProfileRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_community(authz, identity, payload.organization_id)
    tier = await get_supporter_tier_for_organization(db, payload.tier_id, payload.organization_id)
    existing = await db.scalar(
        select(SupporterProfile).where(
            SupporterProfile.organization_id == payload.organization_id,
            func.lower(SupporterProfile.email) == payload.email.lower(),
        )
    )
    if existing is not None:
        existing.person_id = payload.person_id
        existing.tier_id = payload.tier_id
        existing.display_name = payload.display_name
        existing.lifetime_value = payload.lifetime_value
        existing.notes = payload.notes
        await db.commit()
        await db.refresh(existing)
        return supporter_profile_read(existing, tier)
    supporter = SupporterProfile(
        **payload.model_dump(),
        joined_at=datetime.now(UTC),
    )
    db.add(supporter)
    await db.commit()
    await db.refresh(supporter)
    return supporter_profile_read(supporter, tier)


async def list_supporter_profiles(
    db: AsyncSession,
    organization_id: UUID,
) -> list[SupporterProfileRead]:
    rows = (
        await db.execute(
            select(SupporterProfile, SupporterMembershipTier)
            .outerjoin(SupporterMembershipTier, SupporterProfile.tier_id == SupporterMembershipTier.id)
            .where(SupporterProfile.organization_id == organization_id)
            .order_by(SupporterProfile.engagement_points.desc(), SupporterProfile.display_name)
        )
    ).all()
    return [supporter_profile_read(supporter, tier) for supporter, tier in rows]


async def record_supporter_activity(
    db: AsyncSession,
    identity: CurrentIdentity,
    supporter_profile_id: UUID,
    payload: SupporterEngagementActivityCreate,
    authz: AuthorizationService,
) -> tuple[SupporterEngagementActivity, list[SupporterReward]]:
    supporter = await get_supporter_profile(db, supporter_profile_id)
    await ensure_manage_community(authz, identity, supporter.organization_id)
    occurred_at = payload.occurred_at or datetime.now(UTC)
    activity = SupporterEngagementActivity(
        organization_id=supporter.organization_id,
        supporter_profile_id=supporter.id,
        activity_type=payload.activity_type,
        source=payload.source,
        description=payload.description,
        points=payload.points,
        value_amount=payload.value_amount,
        occurred_at=occurred_at,
    )
    supporter.engagement_points += payload.points
    supporter.lifetime_value += payload.value_amount
    supporter.last_engagement_at = occurred_at
    db.add(activity)
    rewards = earned_supporter_rewards(supporter)
    for reward in rewards:
        db.add(reward)
    await db.commit()
    await db.refresh(activity)
    for reward in rewards:
        await db.refresh(reward)
    return activity, rewards


async def create_supporter_reward(
    db: AsyncSession,
    identity: CurrentIdentity,
    supporter_profile_id: UUID,
    payload: SupporterRewardCreate,
    authz: AuthorizationService,
) -> SupporterReward:
    supporter = await get_supporter_profile(db, supporter_profile_id)
    await ensure_manage_community(authz, identity, supporter.organization_id)
    reward = SupporterReward(
        organization_id=supporter.organization_id,
        supporter_profile_id=supporter.id,
        title=payload.title,
        reward_type=payload.reward_type,
        threshold_points=payload.threshold_points,
    )
    db.add(reward)
    await db.commit()
    await db.refresh(reward)
    return reward


async def supporter_dashboard(db: AsyncSession, organization_id: UUID) -> SupporterDashboardRead:
    tier_count = await scalar_count(db, SupporterMembershipTier, organization_id)
    supporter_count = await scalar_count(db, SupporterProfile, organization_id)
    active_supporter_count = await scalar_count(
        db,
        SupporterProfile,
        organization_id,
        SupporterProfile.status == "active",
    )
    reward_count = await scalar_count(db, SupporterReward, organization_id)
    total_points = int(
        await db.scalar(
            select(func.coalesce(func.sum(SupporterProfile.engagement_points), 0)).where(
                SupporterProfile.organization_id == organization_id
            )
        )
        or 0
    )
    total_lifetime_value = await db.scalar(
        select(func.coalesce(func.sum(SupporterProfile.lifetime_value), 0)).where(
            SupporterProfile.organization_id == organization_id
        )
    )
    top_supporter = await db.scalar(
        select(SupporterProfile)
        .where(SupporterProfile.organization_id == organization_id)
        .order_by(SupporterProfile.engagement_points.desc())
        .limit(1)
    )
    return SupporterDashboardRead(
        organization_id=organization_id,
        tier_count=tier_count,
        supporter_count=supporter_count,
        active_supporter_count=active_supporter_count,
        total_points=total_points,
        total_lifetime_value=total_lifetime_value or 0,
        reward_count=reward_count,
        top_supporter_name=top_supporter.display_name if top_supporter else None,
        recommendations=supporter_recommendations(tier_count, supporter_count, total_points, reward_count),
    )


async def create_alumni_profile(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: AlumniProfileCreate,
    authz: AuthorizationService,
) -> AlumniProfile:
    await get_organization(db, payload.organization_id)
    await ensure_manage_community(authz, identity, payload.organization_id)
    existing = await db.scalar(
        select(AlumniProfile).where(
            AlumniProfile.organization_id == payload.organization_id,
            func.lower(AlumniProfile.email) == payload.email.lower(),
        )
    )
    if existing is not None:
        for key, value in payload.model_dump().items():
            setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return existing
    alumni = AlumniProfile(**payload.model_dump())
    db.add(alumni)
    await db.commit()
    await db.refresh(alumni)
    return alumni


async def list_alumni_profiles(db: AsyncSession, organization_id: UUID) -> list[AlumniProfile]:
    return list(
        (
            await db.scalars(
                select(AlumniProfile)
                .where(AlumniProfile.organization_id == organization_id)
                .order_by(AlumniProfile.engagement_level, AlumniProfile.display_name)
            )
        ).all()
    )


async def create_mentorship_program(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: MentorshipProgramCreate,
    authz: AuthorizationService,
) -> MentorshipProgramRead:
    await get_organization(db, payload.organization_id)
    await ensure_manage_community(authz, identity, payload.organization_id)
    program = MentorshipProgram(**payload.model_dump())
    db.add(program)
    await db.commit()
    await db.refresh(program)
    return mentorship_program_read(program, 0)


async def list_mentorship_programs(
    db: AsyncSession,
    organization_id: UUID,
) -> list[MentorshipProgramRead]:
    programs = list(
        (
            await db.scalars(
                select(MentorshipProgram)
                .where(MentorshipProgram.organization_id == organization_id)
                .order_by(MentorshipProgram.created_at.desc())
            )
        ).all()
    )
    if not programs:
        return []
    program_ids = [program.id for program in programs]
    counts = await count_by_program(db, program_ids)
    return [mentorship_program_read(program, counts.get(program.id, 0)) for program in programs]


async def create_mentorship_match(
    db: AsyncSession,
    identity: CurrentIdentity,
    program_id: UUID,
    payload: MentorshipMatchCreate,
    authz: AuthorizationService,
) -> MentorshipMatchRead:
    program = await get_mentorship_program(db, program_id)
    await ensure_manage_community(authz, identity, program.organization_id)
    alumni = await get_alumni_profile(db, payload.alumni_profile_id)
    if alumni.organization_id != program.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumni profile not found")
    if payload.mentee_person_id is not None and await db.get(Person, payload.mentee_person_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentee not found")
    match = MentorshipMatch(
        organization_id=program.organization_id,
        program_id=program.id,
        alumni_profile_id=alumni.id,
        mentee_person_id=payload.mentee_person_id,
        mentee_name=payload.mentee_name,
        mentee_interest=payload.mentee_interest,
        match_score=mentorship_match_score(program, alumni, payload),
        goals=payload.goals,
        next_meeting_at=payload.next_meeting_at,
    )
    alumni.engagement_level = "mentor"
    alumni.last_engagement_at = datetime.now(UTC)
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return mentorship_match_read(match, alumni)


async def list_mentorship_matches(db: AsyncSession, organization_id: UUID) -> list[MentorshipMatchRead]:
    rows = (
        await db.execute(
            select(MentorshipMatch, AlumniProfile)
            .join(AlumniProfile, MentorshipMatch.alumni_profile_id == AlumniProfile.id)
            .where(MentorshipMatch.organization_id == organization_id)
            .order_by(MentorshipMatch.match_score.desc(), MentorshipMatch.created_at.desc())
        )
    ).all()
    return [mentorship_match_read(match, alumni) for match, alumni in rows]


async def alumni_dashboard(db: AsyncSession, organization_id: UUID) -> AlumniDashboardRead:
    alumni_count = await scalar_count(db, AlumniProfile, organization_id)
    active_alumni_count = await scalar_count(
        db,
        AlumniProfile,
        organization_id,
        AlumniProfile.engagement_level.in_(["active", "mentor", "donor"]),
    )
    mentorship_program_count = await scalar_count(db, MentorshipProgram, organization_id)
    mentorship_match_count = await scalar_count(db, MentorshipMatch, organization_id)
    lifetime_donations = await db.scalar(
        select(func.coalesce(func.sum(AlumniProfile.lifetime_donations), 0)).where(
            AlumniProfile.organization_id == organization_id
        )
    )
    mentor_capacity = int(
        await db.scalar(
            select(func.coalesce(func.sum(MentorshipProgram.capacity), 0)).where(
                MentorshipProgram.organization_id == organization_id
            )
        )
        or 0
    )
    return AlumniDashboardRead(
        organization_id=organization_id,
        alumni_count=alumni_count,
        active_alumni_count=active_alumni_count,
        mentorship_program_count=mentorship_program_count,
        mentorship_match_count=mentorship_match_count,
        lifetime_donations=lifetime_donations or 0,
        mentor_capacity=mentor_capacity,
        recommendations=alumni_recommendations(
            alumni_count,
            active_alumni_count,
            mentorship_program_count,
            mentorship_match_count,
        ),
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


def supporter_tier_read(tier: SupporterMembershipTier) -> SupporterMembershipTierRead:
    return SupporterMembershipTierRead(
        id=tier.id,
        organization_id=tier.organization_id,
        name=tier.name,
        slug=tier.slug,
        monthly_price=tier.monthly_price,
        currency=tier.currency,
        benefits=tier.benefits,
        voting_weight=tier.voting_weight,
        trial_days=tier.trial_days,
        status=tier.status,
    )


def supporter_profile_read(
    supporter: SupporterProfile,
    tier: SupporterMembershipTier | None = None,
) -> SupporterProfileRead:
    return SupporterProfileRead(
        id=supporter.id,
        organization_id=supporter.organization_id,
        person_id=supporter.person_id,
        tier_id=supporter.tier_id,
        display_name=supporter.display_name,
        email=supporter.email,
        lifetime_value=supporter.lifetime_value,
        notes=supporter.notes,
        engagement_points=supporter.engagement_points,
        status=supporter.status,
        joined_at=supporter.joined_at,
        last_engagement_at=supporter.last_engagement_at,
        tier_name=tier.name if tier else None,
        tier_voting_weight=tier.voting_weight if tier else None,
    )


def supporter_activity_read(activity: SupporterEngagementActivity) -> SupporterEngagementActivityRead:
    return SupporterEngagementActivityRead(
        id=activity.id,
        organization_id=activity.organization_id,
        supporter_profile_id=activity.supporter_profile_id,
        activity_type=activity.activity_type,
        source=activity.source,
        description=activity.description,
        points=activity.points,
        value_amount=activity.value_amount,
        occurred_at=activity.occurred_at,
    )


def supporter_reward_read(reward: SupporterReward) -> SupporterRewardRead:
    return SupporterRewardRead(
        id=reward.id,
        organization_id=reward.organization_id,
        supporter_profile_id=reward.supporter_profile_id,
        title=reward.title,
        reward_type=reward.reward_type,
        threshold_points=reward.threshold_points,
        status=reward.status,
        redeemed_at=reward.redeemed_at,
    )


def alumni_profile_read(alumni: AlumniProfile) -> AlumniProfileRead:
    return AlumniProfileRead(
        id=alumni.id,
        organization_id=alumni.organization_id,
        person_id=alumni.person_id,
        display_name=alumni.display_name,
        email=alumni.email,
        graduation_year=alumni.graduation_year,
        sports_history=alumni.sports_history,
        career_industry=alumni.career_industry,
        current_company=alumni.current_company,
        current_role=alumni.current_role,
        linkedin_url=alumni.linkedin_url,
        engagement_level=alumni.engagement_level,
        lifetime_donations=alumni.lifetime_donations,
        privacy_status=alumni.privacy_status,
        last_engagement_at=alumni.last_engagement_at,
        notes=alumni.notes,
    )


def mentorship_program_read(program: MentorshipProgram, match_count: int) -> MentorshipProgramRead:
    return MentorshipProgramRead(
        id=program.id,
        organization_id=program.organization_id,
        name=program.name,
        goals=program.goals,
        industry_focus=program.industry_focus,
        capacity=program.capacity,
        starts_on=program.starts_on,
        ends_on=program.ends_on,
        status=program.status,
        match_count=match_count,
    )


def mentorship_match_read(match: MentorshipMatch, alumni: AlumniProfile | None = None) -> MentorshipMatchRead:
    return MentorshipMatchRead(
        id=match.id,
        organization_id=match.organization_id,
        program_id=match.program_id,
        alumni_profile_id=match.alumni_profile_id,
        alumni_name=alumni.display_name if alumni else None,
        mentee_person_id=match.mentee_person_id,
        mentee_name=match.mentee_name,
        mentee_interest=match.mentee_interest,
        match_score=match.match_score,
        goals=match.goals,
        status=match.status,
        next_meeting_at=match.next_meeting_at,
        feedback_notes=match.feedback_notes,
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


async def get_supporter_tier_for_organization(
    db: AsyncSession,
    tier_id: UUID | None,
    organization_id: UUID,
) -> SupporterMembershipTier | None:
    if tier_id is None:
        return None
    tier = await db.get(SupporterMembershipTier, tier_id)
    if tier is None or tier.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supporter tier not found")
    return tier


async def get_supporter_profile(db: AsyncSession, supporter_profile_id: UUID) -> SupporterProfile:
    supporter = await db.get(SupporterProfile, supporter_profile_id)
    if supporter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supporter profile not found")
    return supporter


async def get_alumni_profile(db: AsyncSession, alumni_profile_id: UUID) -> AlumniProfile:
    alumni = await db.get(AlumniProfile, alumni_profile_id)
    if alumni is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumni profile not found")
    return alumni


async def get_mentorship_program(db: AsyncSession, program_id: UUID) -> MentorshipProgram:
    program = await db.get(MentorshipProgram, program_id)
    if program is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentorship program not found")
    return program


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


async def count_by_program(db: AsyncSession, program_ids: list[UUID]) -> dict[UUID, int]:
    if not program_ids:
        return {}
    rows = (
        await db.execute(
            select(MentorshipMatch.program_id, func.count(MentorshipMatch.id))
            .where(MentorshipMatch.program_id.in_(program_ids))
            .group_by(MentorshipMatch.program_id)
        )
    ).all()
    return {program_id: count for program_id, count in rows}


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


def earned_supporter_rewards(supporter: SupporterProfile) -> list[SupporterReward]:
    reward_specs = [
        (500, "Community regular", "badge"),
        (1000, "Matchday insider", "experience"),
        (2500, "Meet and greet access", "experience"),
        (5000, "Signed merchandise eligibility", "merchandise"),
    ]
    return [
        SupporterReward(
            organization_id=supporter.organization_id,
            supporter_profile_id=supporter.id,
            title=title,
            reward_type=reward_type,
            threshold_points=threshold,
        )
        for threshold, title, reward_type in reward_specs
        if supporter.engagement_points >= threshold
    ][:1]


def supporter_recommendations(
    tier_count: int,
    supporter_count: int,
    total_points: int,
    reward_count: int,
) -> list[str]:
    recommendations: list[str] = []
    if not tier_count:
        recommendations.append("Create Basic, Premium, and VIP supporter tiers with clear voting and merchandise benefits.")
    if not supporter_count:
        recommendations.append("Add the first supporters from ticket buyers, donors, families, and public-site signups.")
    if supporter_count and not total_points:
        recommendations.append("Record attendance, poll votes, comments, donations, and merchandise purchases as engagement activity.")
    if total_points and not reward_count:
        recommendations.append("Attach rewards so top supporters can redeem experiences, badges, or merchandise.")
    if not recommendations:
        recommendations.append("Supporter CRM is active; review top fans for tier upgrades and campaign targeting.")
    return recommendations[:6]


def mentorship_match_score(
    program: MentorshipProgram,
    alumni: AlumniProfile,
    payload: MentorshipMatchCreate,
) -> int:
    score = 45
    if program.industry_focus and alumni.career_industry:
        if program.industry_focus.lower() in alumni.career_industry.lower():
            score += 25
    if payload.mentee_interest and alumni.career_industry:
        if payload.mentee_interest.lower() in alumni.career_industry.lower():
            score += 20
    if alumni.engagement_level in {"active", "mentor", "donor"}:
        score += 10
    if alumni.privacy_status == "network_visible":
        score += 5
    return min(score, 100)


def alumni_recommendations(
    alumni_count: int,
    active_alumni_count: int,
    mentorship_program_count: int,
    mentorship_match_count: int,
) -> list[str]:
    recommendations: list[str] = []
    if not alumni_count:
        recommendations.append("Import former players with graduation year, sport history, and current career path.")
    if alumni_count and not active_alumni_count:
        recommendations.append("Tag donors, mentors, and event attendees so the alumni network distinguishes active alumni.")
    if not mentorship_program_count:
        recommendations.append("Launch a structured mentorship program for career guidance and post-sport pathways.")
    if mentorship_program_count and not mentorship_match_count:
        recommendations.append("Match current athletes to alumni mentors by industry, goals, and availability.")
    if not recommendations:
        recommendations.append("Alumni mentorship is active; keep match feedback and event follow-up current.")
    return recommendations[:6]
