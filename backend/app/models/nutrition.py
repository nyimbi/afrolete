from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin


class AthleteNutritionProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_nutrition_profiles"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "athlete_profile_id",
            name="uq_athlete_nutrition_profiles_athlete",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    recorded_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    dietary_pattern: Mapped[str] = mapped_column(String(120), default="balanced", nullable=False, index=True)
    allergies: Mapped[str | None] = mapped_column(Text)
    medical_notes: Mapped[str | None] = mapped_column(Text)
    hydration_target_liters: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    daily_calorie_target: Mapped[int] = mapped_column(Integer, default=2200, nullable=False)
    protein_target_grams: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    carbohydrate_target_grams: Mapped[int] = mapped_column(Integer, default=280, nullable=False)
    fat_target_grams: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    supplement_policy: Mapped[str | None] = mapped_column(Text)
    travel_food_risk: Mapped[str] = mapped_column(String(40), default="normal", nullable=False, index=True)
    consent_to_share_with_caterers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class AthleteMealPlan(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_meal_plans"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    created_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    plan_type: Mapped[str] = mapped_column(String(80), default="training_day", nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(nullable=False, index=True)
    daily_calorie_target: Mapped[int] = mapped_column(Integer, nullable=False)
    hydration_target_liters: Mapped[float] = mapped_column(Float, nullable=False)
    menu_summary: Mapped[str] = mapped_column(Text, nullable=False)
    shopping_list: Mapped[str | None] = mapped_column(Text)
    caterer_notes: Mapped[str | None] = mapped_column(Text)
    risk_flags: Mapped[str | None] = mapped_column(Text)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)


class AthleteMealLog(IdMixin, TimestampMixin, Base):
    __tablename__ = "athlete_meal_logs"

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    meal_plan_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("athlete_meal_plans.id"), index=True)
    logged_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    meal_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    calories: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    protein_grams: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    carbohydrate_grams: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fat_grams: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hydration_liters: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    perceived_energy_score: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    gut_comfort_score: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    compliance_status: Mapped[str] = mapped_column(String(40), default="logged", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class NutritionEducationAssignment(IdMixin, TimestampMixin, Base):
    __tablename__ = "nutrition_education_assignments"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "athlete_profile_id",
            "module_code",
            name="uq_nutrition_education_assignments_module",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=False, index=True
    )
    athlete_profile_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("athlete_profiles.id"), nullable=False, index=True
    )
    assigned_by_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    module_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="assigned", nullable=False, index=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    due_on: Mapped[date | None] = mapped_column(index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    evidence_notes: Mapped[str | None] = mapped_column(Text)
