from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProductTourStepRead(BaseModel):
    key: str
    title: str
    target: str
    instruction: str
    practice_task: str
    success_criteria: str
    xp: int


class ProductTourDefinitionRead(BaseModel):
    key: str
    surface: str
    role: str
    title: str
    estimated_minutes: int
    objective: str
    steps: list[ProductTourStepRead]


class ProductHelpArticleRead(BaseModel):
    key: str
    surface: str
    role: str
    title: str
    summary: str
    body: str
    tags: list[str] = Field(default_factory=list)
    related_tour_key: str | None = None
    action_label: str | None = None
    action_href: str | None = None


class ProductExperienceCatalogRead(BaseModel):
    tours: list[ProductTourDefinitionRead]
    articles: list[ProductHelpArticleRead]


class ProductTourProgressCreate(BaseModel):
    organization_id: UUID
    tour_key: str = Field(min_length=2, max_length=120)
    surface: str | None = Field(default=None, max_length=120)
    role: str = Field(default="coach", min_length=2, max_length=120)
    restart: bool = False


class ProductTourStepUpdate(BaseModel):
    step_key: str = Field(min_length=2, max_length=120)
    skipped: bool = False
    feedback: str | None = Field(default=None, max_length=2000)


class ProductTourProgressRead(BaseModel):
    id: UUID
    organization_id: UUID
    person_id: UUID
    person_name: str
    tour_key: str
    surface: str
    role: str
    title: str
    current_step_key: str | None
    current_step: ProductTourStepRead | None
    completed_steps: list[str]
    skipped_steps: list[str]
    progress_percent: int
    score: int
    star_count: int
    status: str
    last_feedback: str | None
    completed_at: datetime | None
    last_activity_at: datetime | None
    created_at: datetime


class ProductHelpSearchRead(BaseModel):
    query: str
    surface: str | None
    role: str | None
    result_count: int
    articles: list[ProductHelpArticleRead]
    recommended_tours: list[ProductTourDefinitionRead]
    suggested_actions: list[str]


class ProductExperienceDashboardRead(BaseModel):
    organization_id: UUID
    active_tour_count: int
    completed_tour_count: int
    average_progress_percent: int
    total_score: int
    active_progress: list[ProductTourProgressRead]
    recent_searches: list[dict[str, Any]]
    recommended_tours: list[ProductTourDefinitionRead]
    suggested_actions: list[str]
