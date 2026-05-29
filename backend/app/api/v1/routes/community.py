from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.community import (
    AlumniDashboardRead,
    AlumniProfileCreate,
    AlumniProfileRead,
    CommunityCommentCreate,
    CommunityCommentRead,
    CommunityEngagementSummaryRead,
    CommunityPostCreate,
    CommunityPostRead,
    CommunityReactionCreate,
    CommunityReactionRead,
    FanPollCreate,
    FanPollRead,
    FanPollVoteCreate,
    FanPollVoteRead,
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
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.community import (
    add_community_comment,
    add_community_reaction,
    alumni_dashboard,
    alumni_profile_read,
    community_engagement_summary,
    community_post_read,
    create_alumni_profile,
    create_community_post,
    create_fan_poll,
    create_mentorship_match,
    create_mentorship_program,
    create_supporter_membership_tier,
    create_supporter_profile,
    create_supporter_reward,
    list_community_comments,
    list_community_posts,
    list_alumni_profiles,
    list_fan_polls,
    list_mentorship_matches,
    list_mentorship_programs,
    list_supporter_membership_tiers,
    list_supporter_profiles,
    record_supporter_activity,
    supporter_activity_read,
    supporter_dashboard,
    supporter_reward_read,
    supporter_tier_read,
    vote_fan_poll,
)

router = APIRouter(prefix="/community", tags=["community"])


def comment_read(comment) -> CommunityCommentRead:
    return CommunityCommentRead(
        id=comment.id,
        organization_id=comment.organization_id,
        post_id=comment.post_id,
        author_person_id=comment.author_person_id,
        body=comment.body,
        status=comment.status,
        created_at=comment.created_at,
    )


def reaction_read(reaction) -> CommunityReactionRead:
    return CommunityReactionRead(
        id=reaction.id,
        organization_id=reaction.organization_id,
        post_id=reaction.post_id,
        person_id=reaction.person_id,
        reaction_type=reaction.reaction_type,
        created_at=reaction.created_at,
    )


def vote_read(vote) -> FanPollVoteRead:
    return FanPollVoteRead(
        id=vote.id,
        organization_id=vote.organization_id,
        poll_id=vote.poll_id,
        option_id=vote.option_id,
        person_id=vote.person_id,
        created_at=vote.created_at,
    )


@router.post("/posts", response_model=CommunityPostRead, status_code=status.HTTP_201_CREATED)
async def create_post_route(
    payload: CommunityPostCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CommunityPostRead:
    post = await create_community_post(db, identity, payload, authz)
    return community_post_read(post)


@router.get("/posts", response_model=list[CommunityPostRead])
async def list_posts_route(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[CommunityPostRead]:
    return await list_community_posts(db, organization_id, team_id=team_id)


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommunityCommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment_route(
    post_id: UUID,
    payload: CommunityCommentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> CommunityCommentRead:
    return comment_read(await add_community_comment(db, identity, post_id, payload))


@router.get("/posts/{post_id}/comments", response_model=list[CommunityCommentRead])
async def list_comments_route(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[CommunityCommentRead]:
    return [comment_read(comment) for comment in await list_community_comments(db, post_id)]


@router.post(
    "/posts/{post_id}/reactions",
    response_model=CommunityReactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_reaction_route(
    post_id: UUID,
    payload: CommunityReactionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> CommunityReactionRead:
    return reaction_read(await add_community_reaction(db, identity, post_id, payload))


@router.post("/polls", response_model=FanPollRead, status_code=status.HTTP_201_CREATED)
async def create_poll_route(
    payload: FanPollCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FanPollRead:
    return await create_fan_poll(db, identity, payload, authz)


@router.get("/polls", response_model=list[FanPollRead])
async def list_polls_route(
    organization_id: UUID = Query(),
    team_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[FanPollRead]:
    return await list_fan_polls(db, organization_id, team_id=team_id)


@router.post(
    "/polls/{poll_id}/votes",
    response_model=FanPollVoteRead,
    status_code=status.HTTP_201_CREATED,
)
async def vote_poll_route(
    poll_id: UUID,
    payload: FanPollVoteCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> FanPollVoteRead:
    return vote_read(await vote_fan_poll(db, identity, poll_id, payload))


@router.get("/summary", response_model=CommunityEngagementSummaryRead)
async def summary_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> CommunityEngagementSummaryRead:
    return await community_engagement_summary(db, organization_id)


@router.post(
    "/supporter-tiers",
    response_model=SupporterMembershipTierRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_supporter_tier_route(
    payload: SupporterMembershipTierCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SupporterMembershipTierRead:
    tier = await create_supporter_membership_tier(db, identity, payload, authz)
    return supporter_tier_read(tier)


@router.get("/supporter-tiers", response_model=list[SupporterMembershipTierRead])
async def list_supporter_tiers_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SupporterMembershipTierRead]:
    return [
        supporter_tier_read(tier)
        for tier in await list_supporter_membership_tiers(db, organization_id)
    ]


@router.post("/supporters", response_model=SupporterProfileRead, status_code=status.HTTP_201_CREATED)
async def create_supporter_route(
    payload: SupporterProfileCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SupporterProfileRead:
    return await create_supporter_profile(db, identity, payload, authz)


@router.get("/supporters", response_model=list[SupporterProfileRead])
async def list_supporters_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[SupporterProfileRead]:
    return await list_supporter_profiles(db, organization_id)


@router.post(
    "/supporters/{supporter_profile_id}/activities",
    response_model=SupporterEngagementActivityRead,
    status_code=status.HTTP_201_CREATED,
)
async def record_supporter_activity_route(
    supporter_profile_id: UUID,
    payload: SupporterEngagementActivityCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SupporterEngagementActivityRead:
    activity, _ = await record_supporter_activity(db, identity, supporter_profile_id, payload, authz)
    return supporter_activity_read(activity)


@router.post(
    "/supporters/{supporter_profile_id}/rewards",
    response_model=SupporterRewardRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_supporter_reward_route(
    supporter_profile_id: UUID,
    payload: SupporterRewardCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SupporterRewardRead:
    reward = await create_supporter_reward(db, identity, supporter_profile_id, payload, authz)
    return supporter_reward_read(reward)


@router.get("/supporter-dashboard", response_model=SupporterDashboardRead)
async def supporter_dashboard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> SupporterDashboardRead:
    return await supporter_dashboard(db, organization_id)


@router.post("/alumni", response_model=AlumniProfileRead, status_code=status.HTTP_201_CREATED)
async def create_alumni_route(
    payload: AlumniProfileCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> AlumniProfileRead:
    alumni = await create_alumni_profile(db, identity, payload, authz)
    return alumni_profile_read(alumni)


@router.get("/alumni", response_model=list[AlumniProfileRead])
async def list_alumni_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[AlumniProfileRead]:
    return [alumni_profile_read(alumni) for alumni in await list_alumni_profiles(db, organization_id)]


@router.post(
    "/mentorship-programs",
    response_model=MentorshipProgramRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_mentorship_program_route(
    payload: MentorshipProgramCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MentorshipProgramRead:
    return await create_mentorship_program(db, identity, payload, authz)


@router.get("/mentorship-programs", response_model=list[MentorshipProgramRead])
async def list_mentorship_programs_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[MentorshipProgramRead]:
    return await list_mentorship_programs(db, organization_id)


@router.post(
    "/mentorship-programs/{program_id}/matches",
    response_model=MentorshipMatchRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_mentorship_match_route(
    program_id: UUID,
    payload: MentorshipMatchCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> MentorshipMatchRead:
    return await create_mentorship_match(db, identity, program_id, payload, authz)


@router.get("/mentorship-matches", response_model=list[MentorshipMatchRead])
async def list_mentorship_matches_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> list[MentorshipMatchRead]:
    return await list_mentorship_matches(db, organization_id)


@router.get("/alumni-dashboard", response_model=AlumniDashboardRead)
async def alumni_dashboard_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> AlumniDashboardRead:
    return await alumni_dashboard(db, organization_id)
