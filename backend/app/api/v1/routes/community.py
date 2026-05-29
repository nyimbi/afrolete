from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.community import (
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
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.community import (
    add_community_comment,
    add_community_reaction,
    community_engagement_summary,
    community_post_read,
    create_community_post,
    create_fan_poll,
    list_community_comments,
    list_community_posts,
    list_fan_polls,
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
