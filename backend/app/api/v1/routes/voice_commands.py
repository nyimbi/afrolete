from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.voice_commands import (
    CoachVoiceCommandCreate,
    CoachVoiceCommandRead,
    CoachVoiceCommandSessionCreate,
    CoachVoiceCommandSessionRead,
    CoachVoiceCommandShortcutCreate,
    CoachVoiceCommandShortcutRead,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.voice_commands import (
    create_coach_voice_command_session,
    create_coach_voice_command_shortcut,
    decode_dict,
    decode_list,
    list_coach_voice_command_sessions,
    list_coach_voice_command_shortcuts,
    process_coach_voice_command,
)

router = APIRouter(prefix="/voice-commands", tags=["voice-commands"])


def command_read(command) -> CoachVoiceCommandRead:
    return CoachVoiceCommandRead(
        id=command.id,
        organization_id=command.organization_id,
        session_id=command.session_id,
        issued_by_person_id=command.issued_by_person_id,
        transcript=command.transcript,
        normalized_transcript=command.normalized_transcript,
        intent=command.intent,
        confidence=command.confidence,
        command_status=command.command_status,
        response_text=command.response_text,
        entities=decode_dict(command.entities_json),
        action_result=decode_dict(command.action_result_json),
        safety_flags=decode_list(command.safety_flags_json),
        permission_scope=command.permission_scope,
        requires_confirmation=command.requires_confirmation,
        confirmed_at=command.confirmed_at,
        source_device=command.source_device,
        latency_ms=command.latency_ms,
        model_policy=command.model_policy,
        processed_at=command.processed_at,
    )


def session_read(result: dict[str, object]) -> CoachVoiceCommandSessionRead:
    session = result["session"]
    commands = result["commands"]
    return CoachVoiceCommandSessionRead(
        id=session.id,
        organization_id=session.organization_id,
        person_id=session.person_id,
        team_id=session.team_id,
        event_id=session.event_id,
        session_label=session.session_label,
        context_type=session.context_type,
        input_device=session.input_device,
        language=session.language,
        listening_mode=session.listening_mode,
        consent_recorded=session.consent_recorded,
        raw_audio_retention_policy=session.raw_audio_retention_policy,
        command_count=session.command_count,
        status=session.status,
        model_policy=session.model_policy,
        started_at=session.started_at,
        last_command_at=session.last_command_at,
        commands=[command_read(command) for command in commands],
    )


def shortcut_read(shortcut) -> CoachVoiceCommandShortcutRead:
    return CoachVoiceCommandShortcutRead(
        id=shortcut.id,
        organization_id=shortcut.organization_id,
        created_by_person_id=shortcut.created_by_person_id,
        phrase=shortcut.phrase,
        intent=shortcut.intent,
        action_sequence=decode_list(shortcut.action_sequence_json),
        parameters=decode_dict(shortcut.parameters_json),
        notification_policy=shortcut.notification_policy,
        auto_log=shortcut.auto_log,
        trained_sample_count=shortcut.trained_sample_count,
        sensitivity=shortcut.sensitivity,
        status=shortcut.status,
        created_at=shortcut.created_at,
    )


@router.post("/sessions", response_model=CoachVoiceCommandSessionRead, status_code=status.HTTP_201_CREATED)
async def create_coach_voice_command_session_route(
    payload: CoachVoiceCommandSessionCreate,
    db: AsyncSession = Depends(get_db),
    identity: CurrentIdentity = Depends(get_current_identity),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CoachVoiceCommandSessionRead:
    return session_read(await create_coach_voice_command_session(db, identity, payload, authz))


@router.get("/sessions", response_model=list[CoachVoiceCommandSessionRead])
async def list_coach_voice_command_sessions_route(
    organization_id: UUID = Query(),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    identity: CurrentIdentity = Depends(get_current_identity),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[CoachVoiceCommandSessionRead]:
    return [
        session_read(result)
        for result in await list_coach_voice_command_sessions(db, identity, organization_id, authz, limit)
    ]


@router.post(
    "/sessions/{session_id}/commands",
    response_model=CoachVoiceCommandRead,
    status_code=status.HTTP_201_CREATED,
)
async def process_coach_voice_command_route(
    session_id: UUID,
    payload: CoachVoiceCommandCreate,
    db: AsyncSession = Depends(get_db),
    identity: CurrentIdentity = Depends(get_current_identity),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CoachVoiceCommandRead:
    return command_read((await process_coach_voice_command(db, identity, session_id, payload, authz))["command"])


@router.post("/shortcuts", response_model=CoachVoiceCommandShortcutRead, status_code=status.HTTP_201_CREATED)
async def create_coach_voice_command_shortcut_route(
    payload: CoachVoiceCommandShortcutCreate,
    db: AsyncSession = Depends(get_db),
    identity: CurrentIdentity = Depends(get_current_identity),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> CoachVoiceCommandShortcutRead:
    return shortcut_read(await create_coach_voice_command_shortcut(db, identity, payload, authz))


@router.get("/shortcuts", response_model=list[CoachVoiceCommandShortcutRead])
async def list_coach_voice_command_shortcuts_route(
    organization_id: UUID = Query(),
    db: AsyncSession = Depends(get_db),
    identity: CurrentIdentity = Depends(get_current_identity),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[CoachVoiceCommandShortcutRead]:
    return [
        shortcut_read(shortcut)
        for shortcut in await list_coach_voice_command_shortcuts(db, identity, organization_id, authz)
    ]
