import json
import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.voice_commands import (
    CoachVoiceCommand,
    CoachVoiceCommandSession,
    CoachVoiceCommandShortcut,
)
from app.schemas.voice_commands import (
    CoachVoiceCommandCreate,
    CoachVoiceCommandSessionCreate,
    CoachVoiceCommandShortcutCreate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.training import ensure_manage_training
from app.services.voice_coaching import get_organization


OFFICIAL_RECORD_INTENTS = {
    "score_event",
    "card_event",
    "substitution",
    "stat_event",
    "injury_log",
    "time_played",
}


async def create_coach_voice_command_session(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: CoachVoiceCommandSessionCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    await get_organization(db, payload.organization_id)
    await ensure_manage_training(authz, identity, payload.organization_id)
    session = CoachVoiceCommandSession(
        organization_id=payload.organization_id,
        person_id=identity.person_id,
        team_id=payload.team_id,
        event_id=payload.event_id,
        session_label=payload.session_label.strip(),
        context_type=payload.context_type,
        input_device=payload.input_device.strip(),
        language=payload.language.lower(),
        listening_mode=payload.listening_mode,
        consent_recorded=payload.consent_recorded,
        raw_audio_retention_policy=payload.raw_audio_retention_policy.strip(),
        started_at=datetime.now(UTC),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"session": session, "commands": []}


async def list_coach_voice_command_sessions(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    limit: int = 20,
) -> list[dict[str, object]]:
    await get_organization(db, organization_id)
    await ensure_manage_training(authz, identity, organization_id)
    sessions = list(
        (
            await db.scalars(
                select(CoachVoiceCommandSession)
                .where(CoachVoiceCommandSession.organization_id == organization_id)
                .order_by(CoachVoiceCommandSession.created_at.desc())
                .limit(limit)
            )
        ).all()
    )
    if not sessions:
        return []
    commands = list(
        (
            await db.scalars(
                select(CoachVoiceCommand)
                .where(CoachVoiceCommand.session_id.in_([session.id for session in sessions]))
                .order_by(CoachVoiceCommand.processed_at.desc())
            )
        ).all()
    )
    commands_by_session: dict[UUID, list[CoachVoiceCommand]] = {}
    for command in commands:
        commands_by_session.setdefault(command.session_id, []).append(command)
    return [
        {"session": session, "commands": commands_by_session.get(session.id, [])}
        for session in sessions
    ]


async def process_coach_voice_command(
    db: AsyncSession,
    identity: CurrentIdentity,
    session_id: UUID,
    payload: CoachVoiceCommandCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    session = await db.get(CoachVoiceCommandSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice command session not found")
    await ensure_manage_training(authz, identity, session.organization_id)
    if not session.consent_recorded:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Voice command session requires recorded consent before processing transcripts",
        )
    shortcut = await matching_shortcut(db, session.organization_id, payload.transcript)
    parsed = parse_coach_voice_command(payload.transcript, session, payload.context, shortcut)
    now = datetime.now(UTC)
    command = CoachVoiceCommand(
        organization_id=session.organization_id,
        session_id=session.id,
        issued_by_person_id=identity.person_id,
        transcript=payload.transcript.strip(),
        normalized_transcript=normalize_transcript(payload.transcript),
        intent=parsed["intent"],
        confidence=parsed["confidence"],
        command_status=parsed["command_status"],
        response_text=parsed["response_text"],
        entities_json=json.dumps(parsed["entities"], default=str),
        action_result_json=json.dumps(parsed["action_result"], default=str),
        safety_flags_json=json.dumps(parsed["safety_flags"], default=str),
        permission_scope=parsed["permission_scope"],
        requires_confirmation=parsed["requires_confirmation"],
        source_device=payload.source_device or session.input_device,
        latency_ms=payload.latency_ms,
        processed_at=now,
    )
    session.command_count += 1
    session.last_command_at = now
    db.add(command)
    await db.commit()
    await db.refresh(session)
    await db.refresh(command)
    return {"session": session, "command": command}


async def create_coach_voice_command_shortcut(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: CoachVoiceCommandShortcutCreate,
    authz: AuthorizationService,
) -> CoachVoiceCommandShortcut:
    await get_organization(db, payload.organization_id)
    await ensure_manage_training(authz, identity, payload.organization_id)
    shortcut = CoachVoiceCommandShortcut(
        organization_id=payload.organization_id,
        created_by_person_id=identity.person_id,
        phrase=payload.phrase.strip(),
        intent=normalize_key(payload.intent),
        action_sequence_json=json.dumps(payload.action_sequence),
        parameters_json=json.dumps(payload.parameters, default=str),
        notification_policy=normalize_key(payload.notification_policy),
        auto_log=payload.auto_log,
        trained_sample_count=payload.trained_sample_count,
        sensitivity=payload.sensitivity,
    )
    db.add(shortcut)
    await db.commit()
    await db.refresh(shortcut)
    return shortcut


async def list_coach_voice_command_shortcuts(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[CoachVoiceCommandShortcut]:
    await get_organization(db, organization_id)
    await ensure_manage_training(authz, identity, organization_id)
    return list(
        (
            await db.scalars(
                select(CoachVoiceCommandShortcut)
                .where(CoachVoiceCommandShortcut.organization_id == organization_id)
                .order_by(CoachVoiceCommandShortcut.created_at.desc())
            )
        ).all()
    )


async def matching_shortcut(
    db: AsyncSession,
    organization_id: UUID,
    transcript: str,
) -> CoachVoiceCommandShortcut | None:
    normalized = normalize_transcript(transcript)
    shortcuts = list(
        (
            await db.scalars(
                select(CoachVoiceCommandShortcut)
                .where(CoachVoiceCommandShortcut.organization_id == organization_id)
                .where(CoachVoiceCommandShortcut.status == "active")
                .order_by(CoachVoiceCommandShortcut.created_at.desc())
            )
        ).all()
    )
    for shortcut in shortcuts:
        phrase = normalize_transcript(shortcut.phrase)
        if phrase and (normalized == phrase or phrase in normalized):
            return shortcut
    return None


def parse_coach_voice_command(
    transcript: str,
    session: CoachVoiceCommandSession,
    context: dict[str, Any],
    shortcut: CoachVoiceCommandShortcut | None,
) -> dict[str, Any]:
    normalized = normalize_transcript(transcript)
    entities: dict[str, Any] = {
        "context_type": session.context_type,
        "language": session.language,
        "minute": extract_match_minute(normalized, context),
    }
    if shortcut is not None:
        intent = shortcut.intent
        entities["shortcut_id"] = str(shortcut.id)
        entities["shortcut_phrase"] = shortcut.phrase
        entities["action_sequence"] = decode_list(shortcut.action_sequence_json)
        entities["parameters"] = decode_dict(shortcut.parameters_json)
        confidence = max(0.82, shortcut.sensitivity)
    else:
        intent, confidence = classify_command_intent(normalized)
        entities.update(extract_entities(normalized, intent))
    safety_flags = command_safety_flags(normalized, intent)
    requires_confirmation = intent in OFFICIAL_RECORD_INTENTS or bool(safety_flags)
    command_status = "needs_confirmation" if requires_confirmation else "completed"
    action_result = build_action_result(intent, entities, session, safety_flags, shortcut)
    response_text = command_response_text(intent, entities, action_result, safety_flags)
    return {
        "intent": intent,
        "confidence": confidence,
        "entities": entities,
        "safety_flags": safety_flags,
        "requires_confirmation": requires_confirmation,
        "command_status": command_status,
        "permission_scope": permission_scope_for_intent(intent),
        "action_result": action_result,
        "response_text": response_text,
    }


def classify_command_intent(normalized: str) -> tuple[str, float]:
    if any(token in normalized for token in ["goal for", "scored", "penalty awarded"]):
        return "score_event", 0.9
    if any(token in normalized for token in ["yellow card", "red card", "card for"]):
        return "card_event", 0.88
    if any(token in normalized for token in ["substitution", " sub ", " substitute ", " out ", " in "]):
        return "substitution", 0.86
    if any(token in normalized for token in ["shot by", "foul", "corner", "possession lost"]):
        return "stat_event", 0.84
    if any(token in normalized for token in ["injury", "sprain", "concussion", "hurt", "medical"]):
        return "injury_log", 0.9
    if any(token in normalized for token in ["water", "heart rate", "fatigue", "needs a break", "check "]):
        return "player_management", 0.82
    if any(token in normalized for token in ["switch to", "push defense", "man mark", "counter attack", "press high"]):
        return "tactical_instruction", 0.82
    if any(token in normalized for token in ["what is", "what's", "show me", "how many", "time remaining", "score"]):
        return "information_request", 0.8
    if any(token in normalized for token in ["highlight", "clip", "bookmark", "tag video"]):
        return "video_marker", 0.82
    if "time played" in normalized or "minutes for" in normalized:
        return "time_played", 0.78
    if any(token in normalized for token in ["emergency", "stop play", "evacuate"]):
        return "emergency_command", 0.92
    return "coach_note", 0.58


def extract_entities(normalized: str, intent: str) -> dict[str, Any]:
    entities: dict[str, Any] = {}
    if intent in {"score_event", "card_event", "player_management", "injury_log", "time_played"}:
        entities["player_label"] = extract_player_label(normalized)
    if intent == "score_event":
        entities["event_type"] = "goal" if "goal" in normalized or "scored" in normalized else "penalty"
    if intent == "card_event":
        entities["card_type"] = "red" if "red card" in normalized else "yellow"
    if intent == "substitution":
        out_player, in_player = extract_substitution_players(normalized)
        entities["player_out_label"] = out_player
        entities["player_in_label"] = in_player
    if intent == "stat_event":
        entities["stat_type"] = stat_type(normalized)
        entities["player_label"] = extract_player_label(normalized)
    if intent == "tactical_instruction":
        entities["instruction"] = normalized
        formation = re.search(r"\b(\d-\d-\d(?:-\d)?)\b", normalized)
        if formation:
            entities["formation"] = formation.group(1)
    if intent == "information_request":
        entities["request_type"] = information_request_type(normalized)
    if intent == "video_marker":
        entities["marker_type"] = "highlight"
    if intent == "emergency_command":
        entities["severity"] = "critical"
    return entities


def build_action_result(
    intent: str,
    entities: dict[str, Any],
    session: CoachVoiceCommandSession,
    safety_flags: list[str],
    shortcut: CoachVoiceCommandShortcut | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "session_id": str(session.id),
        "context_type": session.context_type,
        "audit_required": True,
        "raw_audio_retention_policy": session.raw_audio_retention_policy,
        "official_record_mutated": False,
    }
    if shortcut is not None:
        result.update(
            {
                "action": "custom_command_sequence_prepared",
                "shortcut_id": str(shortcut.id),
                "sequence": decode_list(shortcut.action_sequence_json),
                "parameters": decode_dict(shortcut.parameters_json),
                "notification_policy": shortcut.notification_policy,
            }
        )
        return result
    if intent in OFFICIAL_RECORD_INTENTS:
        result.update(
            {
                "action": "prepared_official_record_change",
                "review_queue": "coach_match_log_review",
                "event_payload": entities,
            }
        )
    elif intent == "player_management":
        result.update(
            {
                "action": "prepared_staff_alert",
                "alert_type": "player_check",
                "staff_channel": "assistant_coach",
                "player_label": entities.get("player_label"),
            }
        )
    elif intent == "tactical_instruction":
        result.update({"action": "logged_tactical_instruction", "instruction": entities.get("instruction")})
    elif intent == "information_request":
        result.update(
            {
                "action": "answered_from_current_context",
                "request_type": entities.get("request_type"),
                "answer_source": "latest_match_or_training_state",
            }
        )
    elif intent == "video_marker":
        result.update({"action": "prepared_video_highlight_marker", "marker_type": "highlight"})
    elif intent == "emergency_command":
        result.update({"action": "prepared_emergency_escalation", "severity": "critical"})
    else:
        result.update({"action": "logged_coach_note"})
    if safety_flags:
        result["safety_review_required"] = True
        result["safety_flags"] = safety_flags
    return result


def command_response_text(
    intent: str,
    entities: dict[str, Any],
    action_result: dict[str, Any],
    safety_flags: list[str],
) -> str:
    if safety_flags:
        return f"Safety-sensitive command captured. Review required before action: {safety_flags[0]}."
    if intent == "score_event":
        return f"Goal command captured for {entities.get('player_label') or 'the player'}. Review to update the official record."
    if intent == "card_event":
        return f"{str(entities.get('card_type') or 'Card').title()} card command captured for review."
    if intent == "substitution":
        return f"Substitution captured: {entities.get('player_out_label') or 'player out'} to {entities.get('player_in_label') or 'player in'}."
    if intent == "player_management":
        return f"Player management alert prepared for {entities.get('player_label') or 'the squad'}."
    if intent == "tactical_instruction":
        return "Tactical instruction logged for the coaching staff."
    if intent == "information_request":
        return f"Information request captured: {entities.get('request_type') or 'current status'}."
    if intent == "video_marker":
        return "Highlight marker prepared for the current video timeline."
    if intent == "custom_command":
        return "Custom command sequence prepared for coach confirmation."
    if action_result.get("shortcut_id"):
        return "Custom voice shortcut matched and prepared."
    return "Coach note captured."


def command_safety_flags(normalized: str, intent: str) -> list[str]:
    flags: list[str] = []
    if intent in {"injury_log", "emergency_command"}:
        flags.append("medical_or_emergency_language_detected")
    if any(token in normalized for token in ["concussion", "chest pain", "can't breathe", "collapse"]):
        flags.append("critical_health_phrase_detected")
    if "minor" in normalized or "child" in normalized:
        flags.append("minor_context_requires_guardian_policy_review")
    return flags


def permission_scope_for_intent(intent: str) -> str:
    if intent in OFFICIAL_RECORD_INTENTS:
        return "competition_official_log_review"
    if intent == "emergency_command":
        return "safeguarding_emergency_review"
    if intent == "information_request":
        return "training_read"
    return "training_operations"


def extract_match_minute(normalized: str, context: dict[str, Any]) -> int | None:
    if isinstance(context.get("match_minute"), int):
        return int(context["match_minute"])
    match = re.search(r"\b(?:minute|min)\s+(\d{1,3})\b", normalized)
    if match:
        return int(match.group(1))
    return None


def extract_player_label(normalized: str) -> str | None:
    patterns = [
        r"(?:for|by|check|show me|injury for|heart rate for|water for)\s+([a-z][a-z '\-]+?)(?:\s+(?:in|at|minute|needs|with|saved|$))",
        r"number\s+(\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            return clean_label(match.group(1))
    return None


def extract_substitution_players(normalized: str) -> tuple[str | None, str | None]:
    match = re.search(r"([a-z][a-z '\-]+?)\s+out[, ]+\s*([a-z][a-z '\-]+?)\s+in", normalized)
    if match:
        return clean_label(match.group(1)), clean_label(match.group(2))
    match = re.search(r"substitution[: ]+([a-z][a-z '\-]+?)\s+(?:for|to)\s+([a-z][a-z '\-]+)", normalized)
    if match:
        return clean_label(match.group(1)), clean_label(match.group(2))
    return None, None


def stat_type(normalized: str) -> str:
    if "shot" in normalized:
        return "shot_saved" if "saved" in normalized else "shot"
    if "foul" in normalized:
        return "foul"
    if "corner" in normalized:
        return "corner"
    if "possession lost" in normalized:
        return "possession_lost"
    return "stat"


def information_request_type(normalized: str) -> str:
    if "score" in normalized:
        return "score"
    if "possession" in normalized:
        return "possession"
    if "foul" in normalized:
        return "foul_count"
    if "time" in normalized:
        return "time_remaining"
    if "stats" in normalized:
        return "player_stats"
    return "status"


def normalize_transcript(value: str) -> str:
    return " ".join(value.strip().lower().replace("’", "'").split())


def normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def clean_label(value: str) -> str:
    return " ".join(value.strip(" .,:;").title().split())


def decode_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item)]


def decode_dict(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
