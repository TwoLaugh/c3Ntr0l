from datetime import date
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import EnergyLevel


class DailyReviewPromptItem(BaseModel):
    plan_item_id: UUID
    task_id: UUID | None = None
    title: str
    prompt_type: str
    question: str
    importance_score: int


class DailyReviewPromptRead(BaseModel):
    review_date: date
    prompts: list[DailyReviewPromptItem]
    quick_checks: list[str]


class DailyReviewTaskAdjustment(BaseModel):
    task_id: UUID
    action: Literal["defer", "move"]
    target_date: date | None = None
    note: str | None = None


class DailyReviewSubmit(BaseModel):
    responses: dict = {}
    energy_level: EnergyLevel | None = None
    load_fit: str | None = None
    mood: str | None = None
    task_adjustments: list[DailyReviewTaskAdjustment] = []


class DailyReviewRead(BaseModel):
    id: UUID
    review_date: date
    prompts: list
    responses: dict
    energy_level: EnergyLevel | None = None
    load_fit: str | None = None
    mood: str | None = None
    ai_summary: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewAdjustmentIntent(BaseModel):
    action: Literal["defer_task", "add_note", "split_follow_up", "reduce_tomorrow_load"]
    task_id: UUID | None = None
    title: str | None = None
    target_date: date | None = None
    note: str | None = None


class ReviewInterpretation(BaseModel):
    summary: str | None = None
    adjustments: list[ReviewAdjustmentIntent] = []
