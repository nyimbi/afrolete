from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AthleteNutritionProfileCreate(BaseModel):
    organization_id: UUID
    dietary_pattern: str = Field(default="balanced", min_length=2, max_length=120)
    allergies: str | None = Field(default=None, max_length=4000)
    medical_notes: str | None = Field(default=None, max_length=4000)
    hydration_target_liters: float = Field(default=2.5, ge=0.5, le=12)
    daily_calorie_target: int = Field(default=2200, ge=800, le=9000)
    protein_target_grams: int = Field(default=90, ge=10, le=400)
    carbohydrate_target_grams: int = Field(default=280, ge=20, le=1000)
    fat_target_grams: int = Field(default=70, ge=10, le=400)
    supplement_policy: str | None = Field(default=None, max_length=4000)
    travel_food_risk: str = Field(default="normal", min_length=2, max_length=40)
    consent_to_share_with_caterers: bool = False
    status: str = Field(default="active", min_length=2, max_length=40)


class AthleteNutritionProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    recorded_by_person_id: UUID | None
    dietary_pattern: str
    allergies: str | None
    medical_notes: str | None
    hydration_target_liters: float
    daily_calorie_target: int
    protein_target_grams: int
    carbohydrate_target_grams: int
    fat_target_grams: int
    supplement_policy: str | None
    travel_food_risk: str
    consent_to_share_with_caterers: bool
    status: str
    created_at: datetime


class AthleteMealPlanCreate(BaseModel):
    organization_id: UUID
    title: str = Field(min_length=2, max_length=220)
    plan_type: str = Field(default="training_day", min_length=2, max_length=80)
    period_start: date
    period_end: date
    daily_calorie_target: int = Field(default=2200, ge=800, le=9000)
    hydration_target_liters: float = Field(default=2.5, ge=0.5, le=12)
    menu_summary: str = Field(min_length=2, max_length=8000)
    shopping_list: str | None = Field(default=None, max_length=8000)
    caterer_notes: str | None = Field(default=None, max_length=8000)
    risk_flags: str | None = Field(default=None, max_length=4000)
    ai_generated: bool = False
    status: str = Field(default="active", min_length=2, max_length=40)


class AthleteMealPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    created_by_person_id: UUID | None
    title: str
    plan_type: str
    period_start: date
    period_end: date
    daily_calorie_target: int
    hydration_target_liters: float
    menu_summary: str
    shopping_list: str | None
    caterer_notes: str | None
    risk_flags: str | None
    ai_generated: bool
    status: str
    created_at: datetime


class AthleteMealLogCreate(BaseModel):
    organization_id: UUID
    meal_plan_id: UUID | None = None
    logged_at: datetime | None = None
    meal_type: str = Field(default="post_training", min_length=2, max_length=80)
    calories: int = Field(default=0, ge=0, le=9000)
    protein_grams: float = Field(default=0, ge=0, le=400)
    carbohydrate_grams: float = Field(default=0, ge=0, le=1000)
    fat_grams: float = Field(default=0, ge=0, le=400)
    hydration_liters: float = Field(default=0, ge=0, le=12)
    perceived_energy_score: int = Field(default=5, ge=1, le=10)
    gut_comfort_score: int = Field(default=5, ge=1, le=10)
    compliance_status: str = Field(default="logged", min_length=2, max_length=40)
    notes: str | None = Field(default=None, max_length=4000)


class AthleteMealLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    meal_plan_id: UUID | None
    logged_by_person_id: UUID | None
    logged_at: datetime
    meal_type: str
    calories: int
    protein_grams: float
    carbohydrate_grams: float
    fat_grams: float
    hydration_liters: float
    perceived_energy_score: int
    gut_comfort_score: int
    compliance_status: str
    notes: str | None
    created_at: datetime


class NutritionEducationAssignmentCreate(BaseModel):
    organization_id: UUID
    module_code: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=2, max_length=220)
    category: str = Field(default="performance_fueling", min_length=2, max_length=80)
    due_on: date | None = None
    evidence_notes: str | None = Field(default=None, max_length=4000)


class NutritionEducationProgressUpdate(BaseModel):
    status: str = Field(default="in_progress", min_length=2, max_length=40)
    progress_percent: int = Field(ge=0, le=100)
    evidence_notes: str | None = Field(default=None, max_length=4000)


class NutritionEducationAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    athlete_profile_id: UUID
    assigned_by_person_id: UUID | None
    module_code: str
    title: str
    category: str
    status: str
    progress_percent: int
    due_on: date | None
    completed_at: datetime | None
    evidence_notes: str | None
    created_at: datetime


class AthleteNutritionActionRead(BaseModel):
    key: str
    priority: str
    title: str
    detail: str
    owner: str


class AthleteNutritionDashboardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_id: UUID
    athlete_profile_id: UUID
    athlete_name: str
    generated_at: datetime
    nutrition_score: int
    risk_band: str
    hydration_adherence_percent: int
    fueling_adherence_percent: int
    education_progress_percent: int
    profile: AthleteNutritionProfileRead | None
    active_plan: AthleteMealPlanRead | None
    recent_logs: list[AthleteMealLogRead]
    education_assignments: list[NutritionEducationAssignmentRead]
    actions: list[AthleteNutritionActionRead]
