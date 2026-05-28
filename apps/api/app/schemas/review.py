from datetime import date
from uuid import UUID

from pydantic import BaseModel


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
