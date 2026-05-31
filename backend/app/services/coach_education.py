import json
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CommunicationChannel, CommunicationMessageType, CommunicationScopeType, MemberSubjectType, MembershipRole
from app.models.coach_education import CoachEducationActivity, CoachEducationEnrollment
from app.models.identity import Person
from app.models.organization import Membership, Organization
from app.schemas.coach_education import (
    CoachEducationActivityCreate,
    CoachEducationCertificationReviewCreate,
    CoachEducationEnrollmentCreate,
    CoachEducationRenewalReminderItemRead,
    CoachEducationRenewalReminderRunCreate,
    CoachEducationRenewalReminderRunRead,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.communications import create_message_for_recipients, destination_for_channel
from app.services.training import ensure_manage_training


def coach_education_programs() -> list[dict[str, object]]:
    return [
        {
            "key": "foundation_coach",
            "title": "Foundation Coach",
            "level": 1,
            "certification_badge": "Foundation Coach Badge",
            "accreditation_provider": "AfroLete Coach Academy",
            "cpd_hours_required": 20,
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
            "accreditation_provider": "AfroLete Performance Institute",
            "cpd_hours_required": 30,
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
            "accreditation_provider": "AfroLete Tactical Academy",
            "cpd_hours_required": 40,
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
        existing.accreditation_provider = payload.accreditation_provider or str(program["accreditation_provider"])
        existing.cpd_hours_required = float(payload.cpd_hours_required or program["cpd_hours_required"])
        existing.mentor_person_id = payload.mentor_person_id
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
        accreditation_provider=payload.accreditation_provider or str(program["accreditation_provider"]),
        cpd_hours_required=float(payload.cpd_hours_required or program["cpd_hours_required"]),
        mentor_person_id=payload.mentor_person_id,
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
    review_status = payload.review_status.lower()
    accepted = review_status == "accepted"
    xp_awarded = int(payload.xp_awarded if payload.xp_awarded is not None else module_detail["xp"]) if accepted else 0
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
        cpd_hours=payload.cpd_hours if accepted else 0.0,
        reviewer_person_id=identity.person_id,
        review_status=review_status,
        feedback=payload.feedback,
        completed_at=completed_at,
    )
    db.add(activity)
    enrollment.last_activity_at = completed_at
    module_keys = [str(item["key"]) for item in program["modules"]]
    completed_modules = decode_string_list(enrollment.completed_modules_json)
    if accepted:
        completed_modules = append_unique(completed_modules, str(module_detail["key"]))
        enrollment.completed_modules_json = json.dumps(completed_modules)
        enrollment.xp_points += xp_awarded
        enrollment.cpd_hours_completed = float(enrollment.cpd_hours_completed or 0.0) + float(payload.cpd_hours or 0.0)
        if payload.evidence_ref:
            enrollment.portfolio_evidence_ref = payload.evidence_ref
        remaining = [key for key in module_keys if key not in completed_modules]
        enrollment.current_module_key = remaining[0] if remaining else None
        if not remaining:
            enrollment.status = "certified"
            today = date.today()
            enrollment.certification_issued_on = today
            enrollment.certification_expires_on = today + timedelta(days=365)
            enrollment.renewal_due_on = today + timedelta(days=335)
            enrollment.certificate_number = enrollment.certificate_number or coach_education_certificate_number(enrollment, today)
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
    renewal_due = [item for item in reads if item["certification_state"] == "renewal_due"]
    expired = [item for item in reads if item["certification_state"] == "expired"]
    cpd_gaps = [item for item in reads if float(item["cpd_gap_hours"]) > 0 and item["status"] == "certified"]
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
        "renewal_due_count": len(renewal_due),
        "expired_count": len(expired),
        "cpd_gap_count": len(cpd_gaps),
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
    mentor = await db.get(Person, enrollment.mentor_person_id) if enrollment.mentor_person_id else None
    program = coach_education_program(enrollment.program_key)
    completed = decode_string_list(enrollment.completed_modules_json)
    modules = [dict(item) for item in program["modules"]]
    next_module = next((module for module in modules if module["key"] == enrollment.current_module_key), None)
    progress_percent = round(len(completed) / len(modules) * 100) if modules else 100
    certification_state = coach_education_certification_state(enrollment)
    days_until_expiry = (
        (enrollment.certification_expires_on - date.today()).days if enrollment.certification_expires_on else None
    )
    cpd_gap_hours = max(float(enrollment.cpd_hours_required or 0.0) - float(enrollment.cpd_hours_completed or 0.0), 0.0)
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
        "accreditation_provider": enrollment.accreditation_provider,
        "certificate_number": enrollment.certificate_number,
        "certification_issued_on": enrollment.certification_issued_on,
        "certification_expires_on": enrollment.certification_expires_on,
        "renewal_due_on": enrollment.renewal_due_on,
        "certification_state": certification_state,
        "days_until_expiry": days_until_expiry,
        "cpd_hours_required": enrollment.cpd_hours_required,
        "cpd_hours_completed": enrollment.cpd_hours_completed,
        "cpd_gap_hours": cpd_gap_hours,
        "portfolio_evidence_ref": enrollment.portfolio_evidence_ref,
        "mentor_person_id": enrollment.mentor_person_id,
        "mentor_name": mentor.display_name if mentor is not None else None,
        "last_reviewed_by_person_id": enrollment.last_reviewed_by_person_id,
        "last_reviewed_at": enrollment.last_reviewed_at,
        "review_notes": enrollment.review_notes,
        "renewal_last_reminded_at": enrollment.renewal_last_reminded_at,
        "renewal_reminder_message_id": enrollment.renewal_reminder_message_id,
        "renewal_reminder_count": enrollment.renewal_reminder_count,
        "progress_percent": progress_percent,
        "next_module": next_module,
        "last_activity_at": enrollment.last_activity_at,
        "created_at": enrollment.created_at,
    }


async def run_coach_education_renewal_reminders(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: CoachEducationRenewalReminderRunCreate,
    authz: AuthorizationService,
) -> CoachEducationRenewalReminderRunRead:
    await ensure_manage_training(authz, identity, payload.organization_id)
    return await run_coach_education_renewal_reminder_worker(
        db,
        organization_id=payload.organization_id,
        channel=CommunicationChannel(payload.channel),
        as_of=payload.as_of,
        horizon_days=payload.horizon_days,
        repeat_after_days=payload.repeat_after_days,
        limit=payload.limit,
        dry_run=payload.dry_run,
    )


async def run_coach_education_renewal_reminder_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    *,
    channel: CommunicationChannel = CommunicationChannel.EMAIL,
    as_of: date | None = None,
    horizon_days: int = 45,
    repeat_after_days: int = 14,
    limit: int = 100,
    dry_run: bool = False,
) -> CoachEducationRenewalReminderRunRead:
    effective_as_of = as_of or date.today()
    rows = await coach_education_enrollments_due_for_renewal_reminder(
        db,
        organization_id=organization_id,
        as_of=effective_as_of,
        horizon_days=horizon_days,
        limit=limit,
    )
    enrollment_ids: list[UUID] = []
    message_ids: list[UUID] = []
    items: list[CoachEducationRenewalReminderItemRead] = []
    executed_count = 0
    skipped_count = 0
    failed_count = 0

    for enrollment, person in rows:
        executed_count += 1
        state = coach_education_certification_state(enrollment)
        if coach_education_recently_reminded(enrollment, repeat_after_days):
            skipped_count += 1
            items.append(
                coach_education_renewal_reminder_item(
                    enrollment,
                    person,
                    effective_as_of,
                    action="skipped",
                    reason=f"Coach certification renewal reminder already sent within {repeat_after_days} days.",
                    message_id=enrollment.renewal_reminder_message_id,
                )
            )
            continue
        recipients = await coach_education_manager_recipients(db, enrollment.organization_id, channel)
        if not recipients:
            skipped_count += 1
            items.append(
                coach_education_renewal_reminder_item(
                    enrollment,
                    person,
                    effective_as_of,
                    action="skipped",
                    reason=f"No organization manager has a destination for {channel.value}.",
                )
            )
            continue
        if dry_run:
            skipped_count += 1
            items.append(
                coach_education_renewal_reminder_item(
                    enrollment,
                    person,
                    effective_as_of,
                    action="dry_run",
                    reason=f"Would remind {len(recipients)} manager(s); certification state is {state}.",
                    recipient_count=len(recipients),
                )
            )
            continue
        try:
            message = await create_message_for_recipients(
                db,
                organization_id=enrollment.organization_id,
                message_type=CommunicationMessageType.REMINDER,
                channel=channel,
                scope_type=CommunicationScopeType.PERSON,
                scope_id=enrollment.person_id,
                recipient_person_ids=[recipient.id for recipient in recipients],
                subject=f"Coach certification renewal due: {enrollment.program_title}",
                body=coach_education_renewal_reminder_body(enrollment, person, effective_as_of),
                urgent=state in {"expired", "renewal_due"},
                created_by_person_id=None,
            )
            now = datetime.now(UTC)
            enrollment.renewal_last_reminded_at = now
            enrollment.renewal_reminder_message_id = message.id
            enrollment.renewal_reminder_count = int(enrollment.renewal_reminder_count or 0) + 1
            await db.commit()
            await db.refresh(enrollment)
            enrollment_ids.append(enrollment.id)
            message_ids.append(message.id)
            items.append(
                coach_education_renewal_reminder_item(
                    enrollment,
                    person,
                    effective_as_of,
                    action="reminded",
                    reason=f"Coach certification renewal reminder sent to {len(recipients)} manager(s).",
                    recipient_count=len(recipients),
                    message_id=message.id,
                )
            )
        except Exception:
            failed_count += 1
            await db.rollback()
            items.append(
                coach_education_renewal_reminder_item(
                    enrollment,
                    person,
                    effective_as_of,
                    action="failed",
                    reason="Failed to create coach certification renewal reminder message.",
                    recipient_count=len(recipients),
                )
            )

    return CoachEducationRenewalReminderRunRead(
        organization_id=organization_id,
        channel=channel.value,
        as_of=effective_as_of,
        horizon_days=horizon_days,
        repeat_after_days=repeat_after_days,
        eligible_count=len(rows),
        executed_count=executed_count,
        reminded_count=len(message_ids),
        skipped_count=skipped_count,
        failed_count=failed_count,
        dry_run=dry_run,
        enrollment_ids=enrollment_ids,
        message_ids=message_ids,
        items=items,
    )


async def coach_education_enrollments_due_for_renewal_reminder(
    db: AsyncSession,
    *,
    organization_id: UUID | None,
    as_of: date,
    horizon_days: int,
    limit: int,
) -> list[tuple[CoachEducationEnrollment, Person]]:
    horizon = as_of + timedelta(days=horizon_days)
    statement = (
        select(CoachEducationEnrollment, Person)
        .join(Person, Person.id == CoachEducationEnrollment.person_id)
        .where(CoachEducationEnrollment.status == "certified")
        .where(
            or_(
                CoachEducationEnrollment.renewal_due_on <= horizon,
                CoachEducationEnrollment.certification_expires_on <= horizon,
            )
        )
        .order_by(
            CoachEducationEnrollment.renewal_due_on.asc().nulls_last(),
            CoachEducationEnrollment.certification_expires_on.asc().nulls_last(),
            Person.display_name.asc(),
        )
        .limit(limit)
    )
    if organization_id is not None:
        statement = statement.where(CoachEducationEnrollment.organization_id == organization_id)
    return [(enrollment, person) for enrollment, person in (await db.execute(statement)).all()]


def coach_education_recently_reminded(enrollment: CoachEducationEnrollment, repeat_after_days: int) -> bool:
    if enrollment.renewal_last_reminded_at is None or repeat_after_days <= 0:
        return False
    last_reminded = (
        enrollment.renewal_last_reminded_at.replace(tzinfo=UTC)
        if enrollment.renewal_last_reminded_at.tzinfo is None
        else enrollment.renewal_last_reminded_at.astimezone(UTC)
    )
    return last_reminded >= datetime.now(UTC) - timedelta(days=repeat_after_days)


async def coach_education_manager_recipients(
    db: AsyncSession,
    organization_id: UUID,
    channel: CommunicationChannel,
) -> list[Person]:
    rows = (
        await db.scalars(
            select(Person)
            .join(Membership, Membership.subject_id == Person.id)
            .where(Membership.organization_id == organization_id)
            .where(Membership.subject_type == MemberSubjectType.PERSON)
            .where(Membership.role.in_([MembershipRole.OWNER, MembershipRole.ADMIN, MembershipRole.STAFF]))
            .where(Membership.status == "active")
            .order_by(Membership.role.asc(), Person.display_name.asc())
        )
    ).all()
    return [
        person
        for person in rows
        if channel == CommunicationChannel.IN_APP or destination_for_channel(person, channel) is not None
    ]


def coach_education_renewal_reminder_body(
    enrollment: CoachEducationEnrollment,
    person: Person,
    as_of: date,
) -> str:
    cpd_gap = max(float(enrollment.cpd_hours_required or 0.0) - float(enrollment.cpd_hours_completed or 0.0), 0.0)
    days_until_expiry = (
        (enrollment.certification_expires_on - as_of).days if enrollment.certification_expires_on else "unknown"
    )
    return "\n".join(
        [
            f"{person.display_name}'s {enrollment.program_title} certification needs renewal review.",
            f"State: {coach_education_certification_state(enrollment)}. Certificate: {enrollment.certificate_number or 'not issued'}.",
            f"Accreditor: {enrollment.accreditation_provider or 'not recorded'}.",
            f"Renewal due: {enrollment.renewal_due_on.isoformat() if enrollment.renewal_due_on else 'not recorded'}.",
            f"Expires: {enrollment.certification_expires_on.isoformat() if enrollment.certification_expires_on else 'not recorded'} ({days_until_expiry} days).",
            f"CPD: {enrollment.cpd_hours_completed}/{enrollment.cpd_hours_required} hours; gap {cpd_gap}.",
            f"Portfolio evidence: {enrollment.portfolio_evidence_ref or 'not attached'}.",
            "Record CPD evidence, renew the certificate, or restrict coaching duties before the credential lapses.",
        ]
    )


def coach_education_renewal_reminder_item(
    enrollment: CoachEducationEnrollment,
    person: Person,
    as_of: date,
    *,
    action: str,
    reason: str,
    recipient_count: int = 0,
    message_id: UUID | None = None,
) -> CoachEducationRenewalReminderItemRead:
    cpd_gap = max(float(enrollment.cpd_hours_required or 0.0) - float(enrollment.cpd_hours_completed or 0.0), 0.0)
    days_until_expiry = (
        (enrollment.certification_expires_on - as_of).days if enrollment.certification_expires_on else None
    )
    return CoachEducationRenewalReminderItemRead(
        enrollment_id=enrollment.id,
        person_id=person.id,
        person_name=person.display_name,
        program_key=enrollment.program_key,
        program_title=enrollment.program_title,
        certification_state=coach_education_certification_state(enrollment),
        renewal_due_on=enrollment.renewal_due_on,
        certification_expires_on=enrollment.certification_expires_on,
        days_until_expiry=days_until_expiry,
        cpd_gap_hours=cpd_gap,
        recipient_count=recipient_count,
        action=action,
        reason=reason,
        message_id=message_id,
    )


async def review_coach_education_certification(
    db: AsyncSession,
    identity: CurrentIdentity,
    enrollment_id: UUID,
    payload: CoachEducationCertificationReviewCreate,
    authz: AuthorizationService,
) -> dict[str, object]:
    enrollment = await get_coach_education_enrollment(db, enrollment_id)
    await ensure_manage_training(authz, identity, enrollment.organization_id)
    if payload.mentor_person_id is not None and await db.get(Person, payload.mentor_person_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor person not found")
    now = datetime.now(UTC)
    renewed = False
    if payload.cpd_hours_completed is not None:
        enrollment.cpd_hours_completed = float(payload.cpd_hours_completed)
    if payload.portfolio_evidence_ref is not None:
        enrollment.portfolio_evidence_ref = payload.portfolio_evidence_ref
    if payload.mentor_person_id is not None:
        enrollment.mentor_person_id = payload.mentor_person_id
    if payload.action == "renew":
        if enrollment.status != "certified":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only certified enrollments can renew")
        if float(enrollment.cpd_hours_completed or 0.0) < float(enrollment.cpd_hours_required or 0.0):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="CPD hours are below the renewal requirement")
        renewed_on = date.today()
        enrollment.certification_issued_on = renewed_on
        enrollment.certification_expires_on = payload.certification_expires_on or renewed_on + timedelta(days=365)
        enrollment.renewal_due_on = enrollment.certification_expires_on - timedelta(days=30)
        enrollment.status = "certified"
        enrollment.certificate_number = enrollment.certificate_number or coach_education_certificate_number(enrollment, renewed_on)
        enrollment.cpd_hours_completed = 0.0
        renewed = True
    elif payload.action == "suspend":
        enrollment.status = "suspended"
    elif payload.action == "revoke":
        enrollment.status = "revoked"
    enrollment.last_reviewed_by_person_id = identity.person_id
    enrollment.last_reviewed_at = now
    enrollment.review_notes = payload.review_notes
    await db.commit()
    await db.refresh(enrollment)
    read = await coach_education_enrollment_read(db, enrollment)
    return {
        "enrollment": read,
        "action": payload.action,
        "certification_state": read["certification_state"],
        "cpd_gap_hours": read["cpd_gap_hours"],
        "renewed": renewed,
        "message": coach_education_review_message(payload.action, read, renewed),
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


def coach_education_certificate_number(enrollment: CoachEducationEnrollment, issued_on: date) -> str:
    prefix = enrollment.program_key.upper().replace("_", "-")[:24]
    return f"CE-{prefix}-{issued_on.strftime('%Y%m%d')}-{str(enrollment.id)[:8]}"


def coach_education_certification_state(enrollment: CoachEducationEnrollment) -> str:
    if enrollment.status in {"suspended", "revoked"}:
        return enrollment.status
    if enrollment.status != "certified":
        return "in_progress"
    today = date.today()
    if enrollment.certification_expires_on and enrollment.certification_expires_on < today:
        return "expired"
    if enrollment.renewal_due_on and enrollment.renewal_due_on <= today:
        return "renewal_due"
    return "current"


def coach_education_review_message(action: str, enrollment: dict[str, object], renewed: bool) -> str:
    if renewed:
        return f"{enrollment['person_name']} renewed {enrollment['program_title']}."
    if action == "record_cpd":
        return f"CPD evidence recorded; {enrollment['cpd_gap_hours']} hour(s) remain."
    if action == "suspend":
        return f"{enrollment['program_title']} certification suspended."
    if action == "revoke":
        return f"{enrollment['program_title']} certification revoked."
    return "Certification review recorded."


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
    renewal_due = [item for item in enrollments if item.get("certification_state") in {"renewal_due", "expired"}]
    if renewal_due:
        actions.append(f"Review {len(renewal_due)} coach certification renewal(s) before session assignments.")
    cpd_gap = [item for item in enrollments if float(item.get("cpd_gap_hours", 0.0)) > 0 and item["status"] == "certified"]
    if cpd_gap:
        actions.append(f"Close CPD evidence gaps for {len(cpd_gap)} certified coach(es).")
    actions.append("Review the leaderboard during staff meetings and recognize completed badges.")
    return list(dict.fromkeys(actions))
