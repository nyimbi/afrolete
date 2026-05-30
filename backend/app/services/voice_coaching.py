import json
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Person
from app.models.organization import Organization
from app.models.team import AthleteProfile
from app.models.voice_coaching import VoiceCoachProfile, VoiceCoachingCue, VoiceCoachingSession
from app.schemas.voice_coaching import VoiceCoachProfileCreate, VoiceCoachingSessionCreate, VoiceMetricQueryCreate
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.training import ensure_manage_training


async def create_voice_coach_profile(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VoiceCoachProfileCreate,
    authz: AuthorizationService,
) -> VoiceCoachProfile:
    await get_organization(db, payload.organization_id)
    await ensure_manage_training(authz, identity, payload.organization_id)
    if payload.athlete_profile_id is not None:
        await get_athlete_profile(db, payload.athlete_profile_id, payload.organization_id)
    profile = VoiceCoachProfile(
        organization_id=payload.organization_id,
        person_id=payload.person_id or identity.person_id,
        athlete_profile_id=payload.athlete_profile_id,
        sport=payload.sport.lower(),
        voice_style=normalize_key(payload.voice_style),
        feedback_frequency=payload.feedback_frequency,
        language=payload.language.lower(),
        terminology_level=normalize_key(payload.terminology_level),
        preferred_device=payload.preferred_device,
        safety_alerts_enabled=payload.safety_alerts_enabled,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def list_voice_coach_profiles(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[VoiceCoachProfile]:
    await get_organization(db, organization_id)
    await ensure_manage_training(authz, identity, organization_id)
    return list(
        (
            await db.scalars(
                select(VoiceCoachProfile)
                .where(VoiceCoachProfile.organization_id == organization_id)
                .order_by(VoiceCoachProfile.created_at.desc())
            )
        ).all()
    )


async def create_voice_coaching_session(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VoiceCoachingSessionCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    await get_organization(db, payload.organization_id)
    await ensure_manage_training(authz, identity, payload.organization_id)
    profile = await resolve_voice_profile(db, identity, payload, authz)
    if payload.athlete_profile_id is not None:
        await get_athlete_profile(db, payload.athlete_profile_id, payload.organization_id)

    engine = build_voice_feedback(payload, profile)
    session = VoiceCoachingSession(
        organization_id=payload.organization_id,
        profile_id=profile.id,
        team_id=payload.team_id,
        athlete_profile_id=payload.athlete_profile_id or profile.athlete_profile_id,
        created_by_person_id=identity.person_id,
        activity_type=normalize_key(payload.activity_type),
        stage=payload.stage,
        intensity=payload.intensity,
        elapsed_seconds=payload.elapsed_seconds,
        distance_m=payload.distance_m,
        heart_rate_bpm=payload.heart_rate_bpm,
        speed_mps=payload.speed_mps,
        context_note=payload.context_note,
        summary=engine["summary"],
        debrief=engine["debrief"],
        next_actions_json=json.dumps(engine["next_actions"]),
        safety_flags_json=json.dumps(engine["safety_flags"]),
        delivered_count=sum(1 for cue in engine["cues"] if cue["delivery_mode"] == "delivered"),
        suppressed_count=sum(1 for cue in engine["cues"] if cue["delivery_mode"] == "suppressed"),
        started_at=datetime.now(UTC),
    )
    db.add(session)
    await db.flush()
    cue_rows: list[VoiceCoachingCue] = []
    for cue in engine["cues"]:
        row = VoiceCoachingCue(
            organization_id=payload.organization_id,
            session_id=session.id,
            profile_id=profile.id,
            category=cue["category"],
            priority=cue["priority"],
            audio_layer=cue["audio_layer"],
            trigger=cue["trigger"],
            message=cue["message"],
            delivery_mode=cue["delivery_mode"],
            suppressed_reason=cue.get("suppressed_reason"),
        )
        db.add(row)
        cue_rows.append(row)
    await db.commit()
    await db.refresh(session)
    for row in cue_rows:
        await db.refresh(row)
    return {"session": session, "cues": cue_rows}


async def list_voice_coaching_sessions(
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
                select(VoiceCoachingSession)
                .where(VoiceCoachingSession.organization_id == organization_id)
                .order_by(VoiceCoachingSession.created_at.desc())
                .limit(limit)
            )
        ).all()
    )
    if not sessions:
        return []
    cue_rows = list(
        (
            await db.scalars(
                select(VoiceCoachingCue)
                .where(VoiceCoachingCue.session_id.in_([session.id for session in sessions]))
                .order_by(VoiceCoachingCue.created_at.asc())
            )
        ).all()
    )
    cues_by_session: dict[UUID, list[VoiceCoachingCue]] = {}
    for cue in cue_rows:
        cues_by_session.setdefault(cue.session_id, []).append(cue)
    return [{"session": session, "cues": cues_by_session.get(session.id, [])} for session in sessions]


async def answer_voice_metric_query(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VoiceMetricQueryCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    await get_organization(db, payload.organization_id)
    await ensure_manage_training(authz, identity, payload.organization_id)
    session = await latest_query_session(db, payload)
    query = payload.query.lower()
    evidence: list[str] = []
    actions: list[str] = []
    query_type = "general"
    if session is None:
        return {
            "organization_id": payload.organization_id,
            "query": payload.query,
            "query_type": "no_session",
            "answer": "I do not have a recent voice-coaching session yet. Start a session so I can answer from live context.",
            "evidence": [],
            "recommended_actions": ["Start a voice coaching session before using hands-free metric queries."],
        }
    if "heart" in query or "hr" in query:
        query_type = "heart_rate"
        answer = (
            f"Current heart rate is {session.heart_rate_bpm} bpm."
            if session.heart_rate_bpm
            else "No heart-rate value is attached to the latest session."
        )
        evidence.append(f"Latest session intensity {session.intensity}/100.")
    elif "far" in query or "distance" in query or "run" in query:
        query_type = "distance"
        answer = (
            f"You have covered {round(session.distance_m)} meters so far."
            if session.distance_m is not None
            else "No distance value is attached to the latest session."
        )
        if session.speed_mps is not None:
            evidence.append(f"Latest speed is {session.speed_mps} m/s.")
    elif "speed" in query or "pace" in query:
        query_type = "speed"
        answer = (
            f"Current speed is {session.speed_mps} m/s."
            if session.speed_mps is not None
            else "No speed value is attached to the latest session."
        )
        if session.distance_m is not None:
            evidence.append(f"Distance covered is {round(session.distance_m)} meters.")
    else:
        answer = session.debrief
        evidence.append(session.summary)
    if session.suppressed_count:
        actions.append("Wait for a receptive moment before adding more cues.")
    actions.extend(decode_string_list(session.next_actions_json)[:2])
    return {
        "organization_id": payload.organization_id,
        "query": payload.query,
        "query_type": query_type,
        "answer": answer,
        "evidence": evidence,
        "recommended_actions": actions,
    }


async def resolve_voice_profile(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: VoiceCoachingSessionCreate,
    authz: AuthorizationService,
) -> VoiceCoachProfile:
    if payload.profile_id is not None:
        profile = await db.get(VoiceCoachProfile, payload.profile_id)
        if profile is None or profile.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice coach profile not found")
        return profile
    profiles = await list_voice_coach_profiles(db, identity, payload.organization_id, authz)
    if profiles:
        return profiles[0]
    return await create_voice_coach_profile(
        db,
        identity,
        VoiceCoachProfileCreate(
            organization_id=payload.organization_id,
            athlete_profile_id=payload.athlete_profile_id,
        ),
        authz,
    )


def build_voice_feedback(
    payload: VoiceCoachingSessionCreate,
    profile: VoiceCoachProfile,
) -> dict[str, object]:
    safety_flags = voice_safety_flags(payload, profile)
    candidates: list[dict[str, str | None]] = []
    if safety_flags:
        candidates.append(
            cue(
                "safety_alert",
                "critical",
                "primary",
                "safety_threshold",
                f"Safety check: {safety_flags[0]} Ease off and confirm with staff before the next repetition.",
            )
        )
    if payload.stage == "warmup":
        candidates.append(cue("form_correction", "normal", "primary", "warmup", "Build rhythm now: tall posture, light contacts, and relaxed shoulders."))
    if "sprint" in payload.activity_type.lower() or (payload.speed_mps or 0) >= 7:
        candidates.append(cue("form_correction", "normal", "primary", "sprint_mechanics", "Drive the knee forward, strike under the hips, and keep the elbows compact."))
    if "football" in profile.sport.lower() or "football" in payload.activity_type.lower():
        candidates.append(cue("tactical_reminder", "normal", "primary", "football_context", "Scan before receiving and curve pressing runs to block the easy pass."))
    if payload.distance_m is not None:
        candidates.append(cue("pacing_guidance", "low", "secondary", "distance_update", f"Distance update: {round(payload.distance_m)} meters completed. Keep the next effort smooth."))
    if payload.heart_rate_bpm is not None:
        candidates.append(cue("pacing_guidance", "normal", "secondary", "heart_rate", f"Heart rate {payload.heart_rate_bpm} bpm. Control breathing before the next high-speed action."))
    candidates.append(cue("motivation", "low", "secondary", "encouragement", "Good focus. Keep one clear cue in mind and finish the rep with quality."))

    limited = candidates[: feedback_limit(profile.feedback_frequency)]
    cues = [apply_receptive_moment_rules(candidate, payload) for candidate in limited]
    delivered = [item for item in cues if item["delivery_mode"] == "delivered"]
    next_actions = [
        "Review suppressed cues with the athlete after the repetition." if any(item["delivery_mode"] == "suppressed" for item in cues) else "Keep cue volume matched to the athlete's feedback frequency.",
        "Add the strongest cue to the next training plan block.",
        "Use coach review before enabling player-facing live audio in competition.",
    ]
    summary = (
        f"Generated {len(delivered)} delivered voice cue(s) for {payload.activity_type} "
        f"at {payload.intensity}/100 intensity using {profile.feedback_frequency} feedback."
    )
    debrief = voice_debrief(payload, delivered, safety_flags)
    return {
        "cues": cues,
        "safety_flags": safety_flags,
        "next_actions": next_actions,
        "summary": summary,
        "debrief": debrief,
    }


def apply_receptive_moment_rules(
    candidate: dict[str, str | None],
    payload: VoiceCoachingSessionCreate,
) -> dict[str, str | None]:
    if payload.intensity > 90 and candidate["priority"] != "critical":
        return {
            **candidate,
            "delivery_mode": "suppressed",
            "suppressed_reason": "Athlete is above 90% intensity; wait until the effort ends.",
        }
    return {**candidate, "delivery_mode": "delivered", "suppressed_reason": None}


def voice_safety_flags(payload: VoiceCoachingSessionCreate, profile: VoiceCoachProfile) -> list[str]:
    if not profile.safety_alerts_enabled:
        return []
    flags: list[str] = []
    if payload.heart_rate_bpm is not None and payload.heart_rate_bpm >= 190:
        flags.append(f"heart rate is {payload.heart_rate_bpm} bpm")
    if payload.intensity >= 96:
        flags.append("reported intensity is maximal")
    return flags


def voice_debrief(
    payload: VoiceCoachingSessionCreate,
    delivered: list[dict[str, str | None]],
    safety_flags: list[str],
) -> str:
    parts = [f"Session reviewed at {payload.intensity}/100 intensity."]
    if payload.distance_m is not None:
        parts.append(f"Distance {round(payload.distance_m)} meters.")
    if payload.speed_mps is not None:
        parts.append(f"Speed {payload.speed_mps} m/s.")
    if payload.heart_rate_bpm is not None:
        parts.append(f"Heart rate {payload.heart_rate_bpm} bpm.")
    if delivered:
        parts.append(f"Primary cue: {delivered[0]['message']}")
    if safety_flags:
        parts.append("Safety review required before more live cues.")
    return " ".join(parts)


def cue(
    category: str,
    priority: str,
    audio_layer: str,
    trigger: str,
    message: str,
) -> dict[str, str | None]:
    return {
        "category": category,
        "priority": priority,
        "audio_layer": audio_layer,
        "trigger": trigger,
        "message": message,
    }


def feedback_limit(frequency: str) -> int:
    return {"minimal": 2, "moderate": 4, "detailed": 6}.get(frequency, 4)


async def latest_query_session(
    db: AsyncSession,
    payload: VoiceMetricQueryCreate,
) -> VoiceCoachingSession | None:
    statement = (
        select(VoiceCoachingSession)
        .where(VoiceCoachingSession.organization_id == payload.organization_id)
        .order_by(VoiceCoachingSession.started_at.desc())
        .limit(1)
    )
    if payload.profile_id is not None:
        statement = statement.where(VoiceCoachingSession.profile_id == payload.profile_id)
    if payload.athlete_profile_id is not None:
        statement = statement.where(VoiceCoachingSession.athlete_profile_id == payload.athlete_profile_id)
    return await db.scalar(statement)


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def get_athlete_profile(
    db: AsyncSession,
    athlete_profile_id: UUID,
    organization_id: UUID,
) -> AthleteProfile:
    profile = await db.get(AthleteProfile, athlete_profile_id)
    if profile is None or profile.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete profile not found")
    return profile


async def person_name(db: AsyncSession, person_id: UUID | None) -> str | None:
    if person_id is None:
        return None
    person = await db.get(Person, person_id)
    if person is None:
        return None
    return person.display_name


def decode_string_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item)]


def normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")
