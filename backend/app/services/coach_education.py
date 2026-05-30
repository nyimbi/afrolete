import json
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coach_education import CoachEducationActivity, CoachEducationEnrollment
from app.models.identity import Person
from app.models.organization import Organization
from app.schemas.coach_education import CoachEducationActivityCreate, CoachEducationEnrollmentCreate
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.training import ensure_manage_training


def coach_education_programs() -> list[dict[str, object]]:
    return [
        {
            "key": "foundation_coach",
            "title": "Foundation Coach",
            "level": 1,
            "certification_badge": "Foundation Coach Badge",
            "specialization": None,
            "modules": [
                module("platform_basics", "Platform Basics", 180, "guided sandbox", "Navigate the workspace and read team context.", "Set up a team view and identify one player support action.", 120),
                module("player_management", "Player Management", 240, "hands-on lab", "Manage rosters, guardians, consent, and attendance.", "Create a safe roster workflow for a youth activity.", 160),
                module("basic_analytics", "Basic Analytics", 300, "visual walkthrough", "Interpret ALS, readiness, goals, and coaching cues.", "Explain one athlete trend and one next coaching action.", 200),
            ],
        },
        {
            "key": "performance_analyst",
            "title": "Performance Analyst",
            "level": 2,
            "certification_badge": "Performance Analyst Certification",
            "specialization": "video_analysis",
            "modules": [
                module("video_analysis_mastery", "Video Analysis Mastery", 360, "video lab", "Use pose, gait, match tracking, and annotations safely.", "Upload or review a clip and tag two coaching moments.", 240),
                module("data_driven_decisions", "Data-Driven Decision Making", 300, "case simulation", "Combine tracking, wearable, and coach evidence.", "Build a recommendation from three evidence sources.", 220),
                module("training_load_management", "Training Load Management", 240, "scenario drill", "Balance load, readiness, and recovery risk.", "Adjust a weekly plan after a high-load match.", 180),
            ],
        },
        {
            "key": "tactical_strategist",
            "title": "Tactical Strategist",
            "level": 3,
            "certification_badge": "Tactical Strategist Diploma",
            "specialization": "opposition_analysis",
            "modules": [
                module("opposition_analysis", "Opposition Analysis", 420, "match lab", "Read scouting evidence, shapes, pressure, and actions.", "Turn a tracking report into three match-plan cues.", 260),
                module("tactical_system_design", "Tactical System Design", 360, "whiteboard simulation", "Design team principles from player strengths.", "Create one phase-of-play coaching script.", 240),
                module("match_day_management", "Match Day Management", 300, "live scenario", "Use signals, substitutions, and communications during competition.", "Prepare a matchday decision checklist.", 220),
            ],
        },
    ]


def module(
    key: str,
    title: str,
    duration_minutes: int,
    format: str,
    objective: str,
    practice_task: str,
    xp: int,
) -> dict[str, object]:
    return {
        "key": key,
        "title": title,
        "duration_minutes": duration_minutes,
        "format": format,
        "objective": objective,
        "practice_task": practice_task,
        "xp": xp,
    }


def coach_education_daily_challenges() -> list[dict[str, object]]:
    return [
        {
            "key": "analyze_training_session",
            "title": "Analyze one training session",
            "xp": 100,
            "cadence": "daily",
            "action": "Review readiness, feedback, and one coaching cue before the next session.",
        },
        {
            "key": "message_players",
            "title": "Message three players or guardians",
            "xp": 75,
            "cadence": "daily",
            "action": "Send a scoped update with the next training focus and welfare reminder.",
        },
        {
            "key": "set_team_goal",
            "title": "Set a performance goal",
            "xp": 150,
            "cadence": "weekly",
            "action": "Create a measurable athlete or team goal tied to recent evidence.",
        },
    ]


def coach_education_catalog() -> dict[str, object]:
    return {
        "programs": coach_education_programs(),
        "daily_challenges": coach_education_daily_challenges(),
    }


async def create_coach_education_enrollment(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: CoachEducationEnrollmentCreate,
    authz: AuthorizationService,
) -> CoachEducationEnrollment:
    await get_organization(db, payload.organization_id)
    await ensure_manage_training(authz, identity, payload.organization_id)
    person_id = payload.person_id or identity.person_id
    person = await db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    program = coach_education_program(payload.program_key)
    existing = await db.scalar(
        select(CoachEducationEnrollment)
        .where(CoachEducationEnrollment.organization_id == payload.organization_id)
        .where(CoachEducationEnrollment.person_id == person_id)
        .where(CoachEducationEnrollment.program_key == program["key"])
        .limit(1)
    )
    first_module = str(program["modules"][0]["key"]) if program["modules"] else None
    if existing is not None:
        existing.role = payload.role
        existing.skill_level = payload.skill_level
        existing.learning_style = payload.learning_style
        if existing.current_module_key is None and existing.status != "certified":
            existing.current_module_key = first_module
        await db.commit()
        await db.refresh(existing)
        return existing
    enrollment = CoachEducationEnrollment(
        organization_id=payload.organization_id,
        person_id=person_id,
        program_key=str(program["key"]),
        program_title=str(program["title"]),
        level=int(program["level"]),
        role=payload.role,
        skill_level=payload.skill_level,
        learning_style=payload.learning_style,
        current_module_key=first_module,
        completed_modules_json="[]",
        badges_json="[]",
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


async def record_coach_education_activity(
    db: AsyncSession,
    identity: CurrentIdentity,
    enrollment_id: UUID,
    payload: CoachEducationActivityCreate,
    authz: AuthorizationService,
) -> tuple[CoachEducationActivity, CoachEducationEnrollment]:
    enrollment = await get_coach_education_enrollment(db, enrollment_id)
    await ensure_manage_training(authz, identity, enrollment.organization_id)
    program = coach_education_program(enrollment.program_key)
    module_detail = coach_education_module(program, payload.module_key)
    completed_at = datetime.now(UTC)
    xp_awarded = int(payload.xp_awarded if payload.xp_awarded is not None else module_detail["xp"])
    activity = CoachEducationActivity(
        organization_id=enrollment.organization_id,
        enrollment_id=enrollment.id,
        person_id=enrollment.person_id,
        activity_type=payload.activity_type,
        module_key=str(module_detail["key"]),
        title=payload.title or str(module_detail["title"]),
        xp_awarded=xp_awarded,
        evidence_ref=payload.evidence_ref,
        score_percent=payload.score_percent,
        completed_at=completed_at,
    )
    db.add(activity)
    completed_modules = append_unique(decode_string_list(enrollment.completed_modules_json), str(module_detail["key"]))
    enrollment.completed_modules_json = json.dumps(completed_modules)
    enrollment.xp_points += xp_awarded
    enrollment.last_activity_at = completed_at
    module_keys = [str(item["key"]) for item in program["modules"]]
    remaining = [key for key in module_keys if key not in completed_modules]
    enrollment.current_module_key = remaining[0] if remaining else None
    if not remaining:
        enrollment.status = "certified"
        enrollment.certification_expires_on = date.today() + timedelta(days=365)
        enrollment.badges_json = json.dumps(
            append_unique(decode_string_list(enrollment.badges_json), str(program["certification_badge"]))
        )
    elif enrollment.status == "invited":
        enrollment.status = "active"
    await db.commit()
    await db.refresh(activity)
    await db.refresh(enrollment)
    return activity, enrollment


async def list_coach_education_enrollments(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[CoachEducationEnrollment]:
    await ensure_manage_training(authz, identity, organization_id)
    return list(
        (
            await db.scalars(
                select(CoachEducationEnrollment)
                .where(CoachEducationEnrollment.organization_id == organization_id)
                .order_by(CoachEducationEnrollment.xp_points.desc(), CoachEducationEnrollment.created_at.desc())
            )
        ).all()
    )


async def coach_education_dashboard(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> dict[str, object]:
    enrollments = await list_coach_education_enrollments(db, identity, organization_id, authz)
    reads = [await coach_education_enrollment_read(db, enrollment) for enrollment in enrollments]
    total_xp = sum(int(item["xp_points"]) for item in reads)
    certified = [item for item in reads if item["status"] == "certified"]
    leaderboard = [
        {
            "rank": index + 1,
            "person_id": str(item["person_id"]),
            "person_name": item["person_name"],
            "program_title": item["program_title"],
            "level": item["level"],
            "xp_points": item["xp_points"],
            "badges": item["badges"],
        }
        for index, item in enumerate(reads[:10])
    ]
    return {
        "organization_id": organization_id,
        "active_enrollment_count": len([item for item in reads if item["status"] in {"active", "invited"}]),
        "certified_count": len(certified),
        "average_xp": round(total_xp / len(reads)) if reads else 0,
        "total_xp": total_xp,
        "leaderboard": leaderboard,
        "daily_challenges": coach_education_daily_challenges(),
        "recommended_next_actions": coach_education_recommended_actions(reads),
        "enrollments": reads,
    }


async def coach_education_enrollment_read(
    db: AsyncSession,
    enrollment: CoachEducationEnrollment,
) -> dict[str, object]:
    person = await db.get(Person, enrollment.person_id)
    program = coach_education_program(enrollment.program_key)
    completed = decode_string_list(enrollment.completed_modules_json)
    modules = [dict(item) for item in program["modules"]]
    next_module = next((module for module in modules if module["key"] == enrollment.current_module_key), None)
    progress_percent = round(len(completed) / len(modules) * 100) if modules else 100
    return {
        "id": enrollment.id,
        "organization_id": enrollment.organization_id,
        "person_id": enrollment.person_id,
        "person_name": person.display_name if person is not None else "Unknown coach",
        "program_key": enrollment.program_key,
        "program_title": enrollment.program_title,
        "level": enrollment.level,
        "role": enrollment.role,
        "skill_level": enrollment.skill_level,
        "learning_style": enrollment.learning_style,
        "xp_points": enrollment.xp_points,
        "current_module_key": enrollment.current_module_key,
        "completed_modules": completed,
        "badges": decode_string_list(enrollment.badges_json),
        "status": enrollment.status,
        "certification_expires_on": enrollment.certification_expires_on,
        "progress_percent": progress_percent,
        "next_module": next_module,
        "last_activity_at": enrollment.last_activity_at,
        "created_at": enrollment.created_at,
    }


async def get_coach_education_enrollment(db: AsyncSession, enrollment_id: UUID) -> CoachEducationEnrollment:
    enrollment = await db.get(CoachEducationEnrollment, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coach education enrollment not found")
    return enrollment


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


def coach_education_program(program_key: str) -> dict[str, object]:
    for program in coach_education_programs():
        if program["key"] == program_key:
            return program
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown coach education program")


def coach_education_module(program: dict[str, object], module_key: str) -> dict[str, object]:
    modules = [dict(item) for item in program.get("modules", []) if isinstance(item, dict)]
    for item in modules:
        if item.get("key") == module_key:
            return item
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown coach education module")


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


def append_unique(values: list[str], value: str) -> list[str]:
    return list(dict.fromkeys([*values, value]))


def coach_education_recommended_actions(enrollments: list[dict[str, object]]) -> list[str]:
    if not enrollments:
        return [
            "Enroll the first coach in the Foundation Coach pathway.",
            "Use the daily challenge loop to make training analytics part of weekly routines.",
        ]
    actions: list[str] = []
    active = [item for item in enrollments if item["status"] != "certified"]
    if active:
        next_item = active[0]
        next_module = next_item.get("next_module")
        if isinstance(next_module, dict):
            actions.append(f"Coach {next_item['person_name']} should complete {next_module['title']}.")
    if not any(item["status"] == "certified" for item in enrollments):
        actions.append("Complete one certification path to create an internal mentor for new coaches.")
    actions.append("Review the leaderboard during staff meetings and recognize completed badges.")
    return list(dict.fromkeys(actions))
