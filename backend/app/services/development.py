from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.development import (
    AthleteAcademicRecord,
    AthleteLifeSkillAssignment,
    AthleteScholarshipApplication,
    AthleteWellnessCheckIn,
)
from app.models.identity import Person
from app.models.team import AthleteProfile
from app.schemas.development import (
    AthleteAcademicRecordCreate,
    AthleteDevelopmentActionRead,
    AthleteDevelopmentDashboardRead,
    AthleteLifeSkillAssignmentCreate,
    AthleteLifeSkillProgressUpdate,
    AthleteScholarshipApplicationCreate,
    AthleteScholarshipApplicationReview,
    AthleteWellnessCheckInCreate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService


async def ensure_manage_development(
    authz: AuthorizationService,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> None:
    allowed = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage_roster",
        subject_type="user",
        subject_id=str(identity.user_id),
    ) or await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def get_development_athlete(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> tuple[AthleteProfile, Person]:
    athlete_profile = await db.get(AthleteProfile, athlete_profile_id)
    if athlete_profile is None or athlete_profile.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    person = await db.get(Person, athlete_profile.person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete person not found")
    return athlete_profile, person


async def create_wellness_check_in(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: AthleteWellnessCheckInCreate,
    authz: AuthorizationService,
) -> AthleteWellnessCheckIn:
    await ensure_manage_development(authz, identity, payload.organization_id)
    await get_development_athlete(db, payload.organization_id, athlete_profile_id)
    check_in = AthleteWellnessCheckIn(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile_id,
        submitted_by_person_id=identity.person_id,
        check_in_at=payload.check_in_at or datetime.now(UTC),
        mood_score=payload.mood_score,
        stress_score=payload.stress_score,
        sleep_hours=payload.sleep_hours,
        energy_score=payload.energy_score,
        soreness_score=payload.soreness_score,
        resilience_score=payload.resilience_score,
        support_requested=payload.support_requested,
        risk_band=wellness_risk_band(payload),
        notes=payload.notes,
    )
    db.add(check_in)
    await db.commit()
    await db.refresh(check_in)
    return check_in


async def list_wellness_check_ins(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
    limit: int = 12,
) -> list[AthleteWellnessCheckIn]:
    await get_development_athlete(db, organization_id, athlete_profile_id)
    return list(
        (
            await db.scalars(
                select(AthleteWellnessCheckIn)
                .where(AthleteWellnessCheckIn.organization_id == organization_id)
                .where(AthleteWellnessCheckIn.athlete_profile_id == athlete_profile_id)
                .order_by(AthleteWellnessCheckIn.check_in_at.desc(), AthleteWellnessCheckIn.created_at.desc())
                .limit(limit)
            )
        ).all()
    )


async def upsert_academic_record(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: AthleteAcademicRecordCreate,
    authz: AuthorizationService,
) -> AthleteAcademicRecord:
    await ensure_manage_development(authz, identity, payload.organization_id)
    await get_development_athlete(db, payload.organization_id, athlete_profile_id)
    eligibility_status, risk_level = academic_eligibility(payload)
    existing = await db.scalar(
        select(AthleteAcademicRecord)
        .where(AthleteAcademicRecord.organization_id == payload.organization_id)
        .where(AthleteAcademicRecord.athlete_profile_id == athlete_profile_id)
        .where(AthleteAcademicRecord.term_label == payload.term_label)
    )
    if existing is None:
        existing = AthleteAcademicRecord(
            organization_id=payload.organization_id,
            athlete_profile_id=athlete_profile_id,
            recorded_by_person_id=identity.person_id,
            term_label=payload.term_label,
        )
        db.add(existing)
    existing.school_name = payload.school_name
    existing.grade_level = payload.grade_level
    existing.gpa = payload.gpa
    existing.attendance_rate = payload.attendance_rate
    existing.study_hours_weekly = payload.study_hours_weekly
    existing.missing_assignment_count = payload.missing_assignment_count
    existing.eligibility_status = eligibility_status
    existing.risk_level = risk_level
    existing.next_review_on = payload.next_review_on
    existing.notes = payload.notes
    await db.commit()
    await db.refresh(existing)
    return existing


async def list_academic_records(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> list[AthleteAcademicRecord]:
    await get_development_athlete(db, organization_id, athlete_profile_id)
    return list(
        (
            await db.scalars(
                select(AthleteAcademicRecord)
                .where(AthleteAcademicRecord.organization_id == organization_id)
                .where(AthleteAcademicRecord.athlete_profile_id == athlete_profile_id)
                .order_by(AthleteAcademicRecord.created_at.desc())
            )
        ).all()
    )


async def assign_life_skill_module(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: AthleteLifeSkillAssignmentCreate,
    authz: AuthorizationService,
) -> AthleteLifeSkillAssignment:
    await ensure_manage_development(authz, identity, payload.organization_id)
    await get_development_athlete(db, payload.organization_id, athlete_profile_id)
    assignment = AthleteLifeSkillAssignment(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile_id,
        assigned_by_person_id=identity.person_id,
        module_code=payload.module_code.strip().lower(),
        title=payload.title,
        category=payload.category.strip().lower(),
        level=payload.level.strip().lower(),
        due_on=payload.due_on,
        evidence_notes=payload.evidence_notes,
    )
    db.add(assignment)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Life skill module already assigned") from exc
    await db.refresh(assignment)
    return assignment


async def update_life_skill_progress(
    db: AsyncSession,
    identity: CurrentIdentity,
    assignment_id: UUID,
    payload: AthleteLifeSkillProgressUpdate,
    authz: AuthorizationService,
) -> AthleteLifeSkillAssignment:
    assignment = await db.get(AthleteLifeSkillAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Life skill assignment not found")
    await ensure_manage_development(authz, identity, assignment.organization_id)
    assignment.status = "completed" if payload.progress_percent >= 100 else payload.status
    assignment.progress_percent = payload.progress_percent
    assignment.completed_at = datetime.now(UTC) if payload.progress_percent >= 100 else None
    if payload.evidence_notes is not None:
        assignment.evidence_notes = payload.evidence_notes
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def list_life_skill_assignments(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> list[AthleteLifeSkillAssignment]:
    await get_development_athlete(db, organization_id, athlete_profile_id)
    return list(
        (
            await db.scalars(
                select(AthleteLifeSkillAssignment)
                .where(AthleteLifeSkillAssignment.organization_id == organization_id)
                .where(AthleteLifeSkillAssignment.athlete_profile_id == athlete_profile_id)
                .order_by(AthleteLifeSkillAssignment.due_on.asc().nullslast(), AthleteLifeSkillAssignment.created_at.desc())
            )
        ).all()
    )


async def create_scholarship_application(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: AthleteScholarshipApplicationCreate,
    authz: AuthorizationService,
) -> AthleteScholarshipApplication:
    await ensure_manage_development(authz, identity, payload.organization_id)
    await get_development_athlete(db, payload.organization_id, athlete_profile_id)
    latest_academic = await latest_academic_record(db, payload.organization_id, athlete_profile_id)
    latest_wellness = await latest_wellness_check_in(db, payload.organization_id, athlete_profile_id)
    eligibility_score = scholarship_eligibility_score(latest_academic, latest_wellness)
    application = AthleteScholarshipApplication(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile_id,
        created_by_person_id=identity.person_id,
        program_name=payload.program_name,
        scholarship_type=payload.scholarship_type.strip().lower(),
        donor_or_fund=payload.donor_or_fund,
        amount_requested=payload.amount_requested,
        currency=payload.currency.upper(),
        status="submitted" if payload.submitted_on else "draft",
        eligibility_score=eligibility_score,
        committee_recommendation=scholarship_recommendation(eligibility_score, latest_academic, latest_wellness),
        deadline_on=payload.deadline_on,
        submitted_on=payload.submitted_on,
        notes=payload.notes,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


async def review_scholarship_application(
    db: AsyncSession,
    identity: CurrentIdentity,
    application_id: UUID,
    payload: AthleteScholarshipApplicationReview,
    authz: AuthorizationService,
) -> AthleteScholarshipApplication:
    application = await db.get(AthleteScholarshipApplication, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scholarship application not found")
    await ensure_manage_development(authz, identity, application.organization_id)
    application.status = payload.status.strip().lower()
    application.amount_awarded = payload.amount_awarded
    application.decided_on = payload.decided_on or (date.today() if payload.status in {"approved", "rejected"} else None)
    if payload.notes is not None:
        application.notes = payload.notes
    await db.commit()
    await db.refresh(application)
    return application


async def list_scholarship_applications(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> list[AthleteScholarshipApplication]:
    await get_development_athlete(db, organization_id, athlete_profile_id)
    return list(
        (
            await db.scalars(
                select(AthleteScholarshipApplication)
                .where(AthleteScholarshipApplication.organization_id == organization_id)
                .where(AthleteScholarshipApplication.athlete_profile_id == athlete_profile_id)
                .order_by(
                    AthleteScholarshipApplication.deadline_on.asc().nullslast(),
                    AthleteScholarshipApplication.created_at.desc(),
                )
            )
        ).all()
    )


async def athlete_development_dashboard(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> AthleteDevelopmentDashboardRead:
    _, person = await get_development_athlete(db, organization_id, athlete_profile_id)
    wellness = await list_wellness_check_ins(db, organization_id, athlete_profile_id, limit=1)
    academics = await list_academic_records(db, organization_id, athlete_profile_id)
    skills = await list_life_skill_assignments(db, organization_id, athlete_profile_id)
    scholarships = await list_scholarship_applications(db, organization_id, athlete_profile_id)
    latest_wellness_row = wellness[0] if wellness else None
    latest_academic_row = academics[0] if academics else None
    scholarship_readiness = scholarship_eligibility_score(latest_academic_row, latest_wellness_row)
    skill_progress = round(
        sum(item.progress_percent for item in skills) / len(skills)
    ) if skills else 0
    development_score = development_index(latest_wellness_row, latest_academic_row, skill_progress, scholarship_readiness)
    return AthleteDevelopmentDashboardRead(
        organization_id=organization_id,
        athlete_profile_id=athlete_profile_id,
        athlete_name=person.display_name or "Athlete",
        generated_at=datetime.now(UTC),
        development_score=development_score,
        wellness_risk_band=latest_wellness_row.risk_band if latest_wellness_row else "no_data",
        academic_eligibility_status=latest_academic_row.eligibility_status if latest_academic_row else "no_record",
        scholarship_readiness_score=scholarship_readiness,
        life_skill_progress_percent=skill_progress,
        latest_wellness=latest_wellness_row,
        latest_academic=latest_academic_row,
        scholarship_applications=scholarships[:6],
        life_skill_assignments=skills[:8],
        actions=development_actions(latest_wellness_row, latest_academic_row, skills, scholarships, scholarship_readiness),
    )


async def latest_academic_record(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> AthleteAcademicRecord | None:
    return await db.scalar(
        select(AthleteAcademicRecord)
        .where(AthleteAcademicRecord.organization_id == organization_id)
        .where(AthleteAcademicRecord.athlete_profile_id == athlete_profile_id)
        .order_by(AthleteAcademicRecord.created_at.desc())
        .limit(1)
    )


async def latest_wellness_check_in(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> AthleteWellnessCheckIn | None:
    return await db.scalar(
        select(AthleteWellnessCheckIn)
        .where(AthleteWellnessCheckIn.organization_id == organization_id)
        .where(AthleteWellnessCheckIn.athlete_profile_id == athlete_profile_id)
        .order_by(AthleteWellnessCheckIn.check_in_at.desc(), AthleteWellnessCheckIn.created_at.desc())
        .limit(1)
    )


def wellness_risk_band(payload: AthleteWellnessCheckInCreate) -> str:
    risk = 0
    if payload.mood_score <= 4:
        risk += 24
    if payload.stress_score >= 8:
        risk += 24
    if payload.sleep_hours < 6:
        risk += 18
    if payload.energy_score <= 4:
        risk += 14
    if payload.soreness_score >= 8:
        risk += 10
    if payload.resilience_score is not None and payload.resilience_score <= 4:
        risk += 10
    if payload.support_requested:
        risk += 16
    if risk >= 56:
        return "critical"
    if risk >= 34:
        return "high"
    if risk >= 16:
        return "watch"
    return "steady"


def academic_eligibility(payload: AthleteAcademicRecordCreate) -> tuple[str, str]:
    risk = 0
    if payload.gpa is None:
        risk += 18
    elif payload.gpa < 2.0:
        risk += 45
    elif payload.gpa < 2.5:
        risk += 22
    if payload.attendance_rate is None:
        risk += 12
    elif payload.attendance_rate < 80:
        risk += 34
    elif payload.attendance_rate < 90:
        risk += 15
    risk += min(30, payload.missing_assignment_count * 5)
    if payload.study_hours_weekly is not None and payload.study_hours_weekly < 4:
        risk += 10
    if risk >= 60:
        return "ineligible", "critical"
    if risk >= 35:
        return "at_risk", "high"
    if risk >= 15:
        return "eligible_watch", "watch"
    return "eligible", "steady"


def scholarship_eligibility_score(
    academic: AthleteAcademicRecord | None,
    wellness: AthleteWellnessCheckIn | None,
) -> int:
    score = 50
    if academic is not None:
        if academic.gpa is not None:
            score += min(30, int(academic.gpa / 4 * 30))
        if academic.attendance_rate is not None:
            score += min(14, int(academic.attendance_rate / 100 * 14))
        score -= min(18, academic.missing_assignment_count * 3)
        if academic.eligibility_status == "eligible":
            score += 8
        elif academic.eligibility_status in {"at_risk", "ineligible"}:
            score -= 18
    if wellness is not None:
        if wellness.risk_band in {"critical", "high"}:
            score -= 10
        elif wellness.risk_band == "steady":
            score += 4
    return max(0, min(100, score))


def scholarship_recommendation(
    score: int,
    academic: AthleteAcademicRecord | None,
    wellness: AthleteWellnessCheckIn | None,
) -> str:
    if academic is None:
        return "Collect academic record before committee review."
    if score >= 82:
        return "Strong scholarship candidate; prepare donor impact story and committee approval packet."
    if score >= 65:
        return "Eligible with support; attach study plan, coach reference, and financial need notes."
    if wellness is not None and wellness.risk_band in {"critical", "high"}:
        return "Hold award decision until wellness support plan is documented."
    return "Needs eligibility support before award recommendation."


def development_index(
    wellness: AthleteWellnessCheckIn | None,
    academic: AthleteAcademicRecord | None,
    skill_progress: int,
    scholarship_readiness: int,
) -> int:
    wellness_score = {"steady": 90, "watch": 68, "high": 42, "critical": 20}.get(
        wellness.risk_band if wellness else "no_data",
        55,
    )
    academic_score = {
        "eligible": 90,
        "eligible_watch": 70,
        "at_risk": 42,
        "ineligible": 20,
    }.get(academic.eligibility_status if academic else "no_record", 50)
    return round(wellness_score * 0.28 + academic_score * 0.28 + skill_progress * 0.2 + scholarship_readiness * 0.24)


def development_actions(
    wellness: AthleteWellnessCheckIn | None,
    academic: AthleteAcademicRecord | None,
    skills: list[AthleteLifeSkillAssignment],
    scholarships: list[AthleteScholarshipApplication],
    scholarship_readiness: int,
) -> list[AthleteDevelopmentActionRead]:
    actions: list[AthleteDevelopmentActionRead] = []
    if wellness is None:
        actions.append(action("wellness", "high", "Capture wellness baseline", "Record mood, stress, sleep, energy, soreness, and support request status.", "coach"))
    elif wellness.risk_band in {"critical", "high"}:
        actions.append(action("wellness-support", "urgent", "Route wellness support", f"Latest check-in is {wellness.risk_band}; schedule private support and reduce avoidable load.", "wellness lead"))
    if academic is None:
        actions.append(action("academic-record", "high", "Add academic record", "GPA, attendance, study hours, and missing assignments are required for eligibility decisions.", "family liaison"))
    elif academic.eligibility_status in {"at_risk", "ineligible"}:
        actions.append(action("academic-support", "urgent", "Create eligibility recovery plan", f"Academic status is {academic.eligibility_status}; coordinate study hours and teacher follow-up.", "academic coordinator"))
    incomplete_skills = [item for item in skills if item.progress_percent < 100]
    if not skills:
        actions.append(action("life-skills", "normal", "Assign life-skills module", "Start leadership, nutrition, media, finance, or career-readiness curriculum.", "coach"))
    elif incomplete_skills:
        next_skill = incomplete_skills[0]
        actions.append(action("life-skills-progress", "normal", f"Advance {next_skill.title}", f"Module is {next_skill.progress_percent}% complete.", "athlete"))
    open_scholarships = [item for item in scholarships if item.status in {"draft", "submitted", "under_review"}]
    if scholarship_readiness >= 70 and not open_scholarships:
        actions.append(action("scholarship", "high", "Open scholarship application", "Readiness is strong enough for committee or donor review.", "scholarship committee"))
    elif open_scholarships:
        actions.append(action("scholarship-review", "normal", "Review scholarship packet", f"{len(open_scholarships)} application(s) need decision tracking.", "scholarship committee"))
    return actions[:6]


def action(key: str, priority: str, title: str, detail: str, owner: str) -> AthleteDevelopmentActionRead:
    return AthleteDevelopmentActionRead(
        key=key,
        priority=priority,
        title=title,
        detail=detail,
        owner=owner,
    )
