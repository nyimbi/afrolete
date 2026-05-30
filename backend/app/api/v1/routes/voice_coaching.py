from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.voice_coaching import (
    VoiceCoachProfileCreate,
    VoiceCoachProfileRead,
    VoiceCoachingCueRead,
    VoiceCoachingSessionCreate,
    VoiceCoachingSessionRead,
    VoiceMetricQueryCreate,
    VoiceMetricQueryRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.voice_coaching import (
    answer_voice_metric_query,
    create_voice_coach_profile,
    create_voice_coaching_session,
    decode_string_list,
    list_voice_coach_profiles,
    list_voice_coaching_sessions,
    person_name,
)

router = APIRouter(prefix="/voice-coaching", tags=["voice-coaching"])


async def profile_read(db: AsyncSession, profile) -> VoiceCoachProfileRead:
    return VoiceCoachProfileRead(
        id=profile.id,
        organization_id=profile.organization_id,
        person_id=profile.person_id,
        person_name=await person_name(db, profile.person_id),
        athlete_profile_id=profile.athlete_profile_id,
        sport=profile.sport,
        voice_style=profile.voice_style,
        feedback_frequency=profile.feedback_frequency,
        language=profile.language,
        terminology_level=profile.terminology_level,
        preferred_device=profile.preferred_device,
        safety_alerts_enabled=profile.safety_alerts_enabled,
        status=profile.status,
        created_at=profile.created_at,
    )


def cue_read(cue) -> VoiceCoachingCueRead:
    return VoiceCoachingCueRead(
        id=cue.id,
        category=cue.category,
        priority=cue.priority,
        audio_layer=cue.audio_layer,
        trigger=cue.trigger,
        message=cue.message,
        delivery_mode=cue.delivery_mode,
        suppressed_reason=cue.suppressed_reason,
    )


def session_read(result: dict[str, object]) -> VoiceCoachingSessionRead:
    session = result["session"]
    cues = result["cues"]
    return VoiceCoachingSessionRead(
        id=session.id,
        organization_id=session.organization_id,
        profile_id=session.profile_id,
        team_id=session.team_id,
        athlete_profile_id=session.athlete_profile_id,
        activity_type=session.activity_type,
        stage=session.stage,
        intensity=session.intensity,
        elapsed_seconds=session.elapsed_seconds,
        distance_m=session.distance_m,
        heart_rate_bpm=session.heart_rate_bpm,
        speed_mps=session.speed_mps,
        context_note=session.context_note,
        summary=session.summary,
        debrief=session.debrief,
        next_actions=decode_string_list(session.next_actions_json),
        safety_flags=decode_string_list(session.safety_flags_json),
        delivered_count=session.delivered_count,
        suppressed_count=session.suppressed_count,
        model_policy=session.model_policy,
        started_at=session.started_at,
        cues=[cue_read(cue) for cue in cues],
    )


@router.post("/profiles", response_model=VoiceCoachProfileRead, status_code=status.HTTP_201_CREATED)
async def create_voice_coach_profile_route(
    payload: VoiceCoachProfileCreate,
    db: AsyncSession = Depends(get_db),
    identity: CurrentIdentity = Depends(get_current_identity),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> VoiceCoachProfileRead:
    return await profile_read(db, await create_voice_coach_profile(db, identity, payload, authz))


@router.get("/profiles", response_model=list[VoiceCoachProfileRead])
async def list_voice_coach_profiles_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
    identity: CurrentIdentity = Depends(get_current_identity),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[VoiceCoachProfileRead]:
    profiles = await list_voice_coach_profiles(db, identity, organization_id, authz)
    return [await profile_read(db, profile) for profile in profiles]


@router.post("/sessions", response_model=VoiceCoachingSessionRead, status_code=status.HTTP_201_CREATED)
async def create_voice_coaching_session_route(
    payload: VoiceCoachingSessionCreate,
    db: AsyncSession = Depends(get_db),
    identity: CurrentIdentity = Depends(get_current_identity),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> VoiceCoachingSessionRead:
    return session_read(await create_voice_coaching_session(db, identity, payload, authz))


@router.get("/sessions", response_model=list[VoiceCoachingSessionRead])
async def list_voice_coaching_sessions_route(
    organization_id: UUID = Query(),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    identity: CurrentIdentity = Depends(get_current_identity),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[VoiceCoachingSessionRead]:
    rows = await list_voice_coaching_sessions(db, identity, organization_id, authz, limit)
    return [session_read(row) for row in rows]


@router.post("/metric-query", response_model=VoiceMetricQueryRead)
async def answer_voice_metric_query_route(
    payload: VoiceMetricQueryCreate,
    db: AsyncSession = Depends(get_db),
    identity: CurrentIdentity = Depends(get_current_identity),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> VoiceMetricQueryRead:
    return VoiceMetricQueryRead(**await answer_voice_metric_query(db, identity, payload, authz))
