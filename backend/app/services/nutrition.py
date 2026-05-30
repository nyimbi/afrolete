from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Person
from app.models.nutrition import (
    AthleteMealLog,
    AthleteMealPlan,
    AthleteNutritionProfile,
    NutritionEducationAssignment,
)
from app.models.team import AthleteProfile
from app.schemas.nutrition import (
    AthleteMealLogCreate,
    AthleteMealPlanCreate,
    AthleteNutritionActionRead,
    AthleteNutritionDashboardRead,
    AthleteNutritionProfileCreate,
    NutritionEducationAssignmentCreate,
    NutritionEducationProgressUpdate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService


async def ensure_manage_nutrition(
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


async def get_nutrition_athlete(
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


async def upsert_nutrition_profile(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: AthleteNutritionProfileCreate,
    authz: AuthorizationService,
) -> AthleteNutritionProfile:
    await ensure_manage_nutrition(authz, identity, payload.organization_id)
    await get_nutrition_athlete(db, payload.organization_id, athlete_profile_id)
    profile = await db.scalar(
        select(AthleteNutritionProfile)
        .where(AthleteNutritionProfile.organization_id == payload.organization_id)
        .where(AthleteNutritionProfile.athlete_profile_id == athlete_profile_id)
    )
    if profile is None:
        profile = AthleteNutritionProfile(
            organization_id=payload.organization_id,
            athlete_profile_id=athlete_profile_id,
            recorded_by_person_id=identity.person_id,
        )
        db.add(profile)
    profile.dietary_pattern = payload.dietary_pattern.strip().lower()
    profile.allergies = payload.allergies
    profile.medical_notes = payload.medical_notes
    profile.hydration_target_liters = payload.hydration_target_liters
    profile.daily_calorie_target = payload.daily_calorie_target
    profile.protein_target_grams = payload.protein_target_grams
    profile.carbohydrate_target_grams = payload.carbohydrate_target_grams
    profile.fat_target_grams = payload.fat_target_grams
    profile.supplement_policy = payload.supplement_policy
    profile.travel_food_risk = payload.travel_food_risk.strip().lower()
    profile.consent_to_share_with_caterers = payload.consent_to_share_with_caterers
    profile.status = payload.status.strip().lower()
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_nutrition_profile(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> AthleteNutritionProfile | None:
    await get_nutrition_athlete(db, organization_id, athlete_profile_id)
    return await db.scalar(
        select(AthleteNutritionProfile)
        .where(AthleteNutritionProfile.organization_id == organization_id)
        .where(AthleteNutritionProfile.athlete_profile_id == athlete_profile_id)
    )


async def create_meal_plan(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: AthleteMealPlanCreate,
    authz: AuthorizationService,
) -> AthleteMealPlan:
    await ensure_manage_nutrition(authz, identity, payload.organization_id)
    await get_nutrition_athlete(db, payload.organization_id, athlete_profile_id)
    if payload.period_end < payload.period_start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="period_end must be after period_start")
    plan = AthleteMealPlan(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile_id,
        created_by_person_id=identity.person_id,
        title=payload.title,
        plan_type=payload.plan_type.strip().lower(),
        period_start=payload.period_start,
        period_end=payload.period_end,
        daily_calorie_target=payload.daily_calorie_target,
        hydration_target_liters=payload.hydration_target_liters,
        menu_summary=payload.menu_summary,
        shopping_list=payload.shopping_list,
        caterer_notes=payload.caterer_notes,
        risk_flags=payload.risk_flags,
        ai_generated=payload.ai_generated,
        status=payload.status.strip().lower(),
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def list_meal_plans(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> list[AthleteMealPlan]:
    await get_nutrition_athlete(db, organization_id, athlete_profile_id)
    return list(
        (
            await db.scalars(
                select(AthleteMealPlan)
                .where(AthleteMealPlan.organization_id == organization_id)
                .where(AthleteMealPlan.athlete_profile_id == athlete_profile_id)
                .order_by(AthleteMealPlan.period_start.desc(), AthleteMealPlan.created_at.desc())
            )
        ).all()
    )


async def record_meal_log(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: AthleteMealLogCreate,
    authz: AuthorizationService,
) -> AthleteMealLog:
    await ensure_manage_nutrition(authz, identity, payload.organization_id)
    await get_nutrition_athlete(db, payload.organization_id, athlete_profile_id)
    if payload.meal_plan_id is not None:
        plan = await db.get(AthleteMealPlan, payload.meal_plan_id)
        if plan is None or plan.organization_id != payload.organization_id or plan.athlete_profile_id != athlete_profile_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found")
    log = AthleteMealLog(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile_id,
        meal_plan_id=payload.meal_plan_id,
        logged_by_person_id=identity.person_id,
        logged_at=payload.logged_at or datetime.now(UTC),
        meal_type=payload.meal_type.strip().lower(),
        calories=payload.calories,
        protein_grams=payload.protein_grams,
        carbohydrate_grams=payload.carbohydrate_grams,
        fat_grams=payload.fat_grams,
        hydration_liters=payload.hydration_liters,
        perceived_energy_score=payload.perceived_energy_score,
        gut_comfort_score=payload.gut_comfort_score,
        compliance_status=payload.compliance_status.strip().lower(),
        notes=payload.notes,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def list_meal_logs(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
    limit: int = 20,
) -> list[AthleteMealLog]:
    await get_nutrition_athlete(db, organization_id, athlete_profile_id)
    return list(
        (
            await db.scalars(
                select(AthleteMealLog)
                .where(AthleteMealLog.organization_id == organization_id)
                .where(AthleteMealLog.athlete_profile_id == athlete_profile_id)
                .order_by(AthleteMealLog.logged_at.desc(), AthleteMealLog.created_at.desc())
                .limit(limit)
            )
        ).all()
    )


async def assign_nutrition_education(
    db: AsyncSession,
    identity: CurrentIdentity,
    athlete_profile_id: UUID,
    payload: NutritionEducationAssignmentCreate,
    authz: AuthorizationService,
) -> NutritionEducationAssignment:
    await ensure_manage_nutrition(authz, identity, payload.organization_id)
    await get_nutrition_athlete(db, payload.organization_id, athlete_profile_id)
    assignment = NutritionEducationAssignment(
        organization_id=payload.organization_id,
        athlete_profile_id=athlete_profile_id,
        assigned_by_person_id=identity.person_id,
        module_code=payload.module_code.strip().lower(),
        title=payload.title,
        category=payload.category.strip().lower(),
        due_on=payload.due_on,
        evidence_notes=payload.evidence_notes,
    )
    db.add(assignment)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nutrition module already assigned") from exc
    await db.refresh(assignment)
    return assignment


async def update_nutrition_education_progress(
    db: AsyncSession,
    identity: CurrentIdentity,
    assignment_id: UUID,
    payload: NutritionEducationProgressUpdate,
    authz: AuthorizationService,
) -> NutritionEducationAssignment:
    assignment = await db.get(NutritionEducationAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nutrition education assignment not found")
    await ensure_manage_nutrition(authz, identity, assignment.organization_id)
    assignment.status = "completed" if payload.progress_percent >= 100 else payload.status.strip().lower()
    assignment.progress_percent = payload.progress_percent
    assignment.completed_at = datetime.now(UTC) if payload.progress_percent >= 100 else None
    if payload.evidence_notes is not None:
        assignment.evidence_notes = payload.evidence_notes
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def list_nutrition_education(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> list[NutritionEducationAssignment]:
    await get_nutrition_athlete(db, organization_id, athlete_profile_id)
    return list(
        (
            await db.scalars(
                select(NutritionEducationAssignment)
                .where(NutritionEducationAssignment.organization_id == organization_id)
                .where(NutritionEducationAssignment.athlete_profile_id == athlete_profile_id)
                .order_by(NutritionEducationAssignment.due_on.asc().nullslast(), NutritionEducationAssignment.created_at.desc())
            )
        ).all()
    )


async def athlete_nutrition_dashboard(
    db: AsyncSession,
    organization_id: UUID,
    athlete_profile_id: UUID,
) -> AthleteNutritionDashboardRead:
    _, person = await get_nutrition_athlete(db, organization_id, athlete_profile_id)
    profile = await get_nutrition_profile(db, organization_id, athlete_profile_id)
    plans = await list_meal_plans(db, organization_id, athlete_profile_id)
    logs = await list_meal_logs(db, organization_id, athlete_profile_id, limit=10)
    education = await list_nutrition_education(db, organization_id, athlete_profile_id)
    active_plan = next((plan for plan in plans if plan.status in {"active", "draft"}), plans[0] if plans else None)
    hydration_adherence = hydration_adherence_percent(profile, active_plan, logs)
    fueling_adherence = fueling_adherence_percent(profile, active_plan, logs)
    education_progress = round(sum(item.progress_percent for item in education) / len(education)) if education else 0
    risk_band = nutrition_risk_band(profile, active_plan, logs, hydration_adherence, fueling_adherence)
    score = nutrition_score(risk_band, hydration_adherence, fueling_adherence, education_progress)
    return AthleteNutritionDashboardRead(
        organization_id=organization_id,
        athlete_profile_id=athlete_profile_id,
        athlete_name=person.display_name or "Athlete",
        generated_at=datetime.now(UTC),
        nutrition_score=score,
        risk_band=risk_band,
        hydration_adherence_percent=hydration_adherence,
        fueling_adherence_percent=fueling_adherence,
        education_progress_percent=education_progress,
        profile=profile,
        active_plan=active_plan,
        recent_logs=logs,
        education_assignments=education[:8],
        actions=nutrition_actions(profile, active_plan, logs, education, risk_band, hydration_adherence, fueling_adherence),
    )


def hydration_adherence_percent(
    profile: AthleteNutritionProfile | None,
    plan: AthleteMealPlan | None,
    logs: list[AthleteMealLog],
) -> int:
    target = plan.hydration_target_liters if plan else profile.hydration_target_liters if profile else 2.5
    if not logs or target <= 0:
        return 0
    actual = sum(item.hydration_liters for item in logs) / len(logs)
    return max(0, min(140, round(actual / target * 100)))


def fueling_adherence_percent(
    profile: AthleteNutritionProfile | None,
    plan: AthleteMealPlan | None,
    logs: list[AthleteMealLog],
) -> int:
    target = plan.daily_calorie_target if plan else profile.daily_calorie_target if profile else 2200
    if not logs or target <= 0:
        return 0
    actual = sum(item.calories for item in logs) / len(logs)
    return max(0, min(140, round(actual / target * 100)))


def nutrition_risk_band(
    profile: AthleteNutritionProfile | None,
    plan: AthleteMealPlan | None,
    logs: list[AthleteMealLog],
    hydration_adherence: int,
    fueling_adherence: int,
) -> str:
    if profile is None:
        return "needs_profile"
    risk = 0
    if profile.allergies and not profile.consent_to_share_with_caterers:
        risk += 28
    if profile.travel_food_risk in {"high", "critical"}:
        risk += 22
    if plan is None:
        risk += 22
    if logs:
        low_energy_logs = sum(1 for item in logs if item.perceived_energy_score <= 4 or item.gut_comfort_score <= 4)
        risk += min(28, low_energy_logs * 7)
    else:
        risk += 18
    if hydration_adherence < 55:
        risk += 18
    elif hydration_adherence < 80:
        risk += 9
    if fueling_adherence < 55:
        risk += 20
    elif fueling_adherence < 80:
        risk += 10
    if risk >= 62:
        return "critical"
    if risk >= 38:
        return "high"
    if risk >= 18:
        return "watch"
    return "steady"


def nutrition_score(
    risk_band: str,
    hydration_adherence: int,
    fueling_adherence: int,
    education_progress: int,
) -> int:
    risk_score = {"steady": 92, "watch": 68, "high": 42, "critical": 18, "needs_profile": 35}.get(risk_band, 50)
    adherence_score = min(100, round((hydration_adherence + fueling_adherence) / 2))
    return round(risk_score * 0.45 + adherence_score * 0.4 + education_progress * 0.15)


def nutrition_actions(
    profile: AthleteNutritionProfile | None,
    plan: AthleteMealPlan | None,
    logs: list[AthleteMealLog],
    education: list[NutritionEducationAssignment],
    risk_band: str,
    hydration_adherence: int,
    fueling_adherence: int,
) -> list[AthleteNutritionActionRead]:
    actions: list[AthleteNutritionActionRead] = []
    if profile is None:
        actions.append(action("nutrition-profile", "urgent", "Capture nutrition profile", "Record allergies, targets, medical notes, supplement policy, and caterer-sharing consent.", "coach"))
    elif profile.allergies and not profile.consent_to_share_with_caterers:
        actions.append(action("allergy-sharing", "urgent", "Confirm catering consent", "Allergy data exists but has not been approved for catering and travel meal coordination.", "family liaison"))
    if plan is None:
        actions.append(action("meal-plan", "high", "Create meal plan", "Build a training, travel, recovery, or return-to-play meal plan for this athlete.", "nutrition lead"))
    if not logs:
        actions.append(action("meal-log", "normal", "Start meal logging", "Capture meals, hydration, energy, and gut comfort to connect nutrition with performance.", "athlete"))
    if hydration_adherence < 80:
        actions.append(action("hydration", "high", "Improve hydration adherence", f"Recent hydration is {hydration_adherence}% of target.", "coach"))
    if fueling_adherence < 80:
        actions.append(action("fueling", "high", "Improve fueling adherence", f"Recent calories are {fueling_adherence}% of target.", "nutrition lead"))
    incomplete_education = [item for item in education if item.progress_percent < 100]
    if not education:
        actions.append(action("education", "normal", "Assign nutrition education", "Start age-appropriate learning on fueling, recovery, allergies, supplements, or travel meals.", "coach"))
    elif incomplete_education:
        next_module = incomplete_education[0]
        actions.append(action("education-progress", "normal", f"Advance {next_module.title}", f"Module is {next_module.progress_percent}% complete.", "athlete"))
    if risk_band in {"critical", "high"}:
        actions.append(action("nutrition-review", "urgent", "Schedule nutrition review", f"Nutrition risk is {risk_band}; review plan, logs, and medical constraints.", "nutrition lead"))
    return actions[:6]


def action(key: str, priority: str, title: str, detail: str, owner: str) -> AthleteNutritionActionRead:
    return AthleteNutritionActionRead(
        key=key,
        priority=priority,
        title=title,
        detail=detail,
        owner=owner,
    )
