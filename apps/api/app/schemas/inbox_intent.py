from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import EnergyLevel, ItemType, TaskPriority


IntentType = Literal["create_task", "create_routine", "create_item", "clarification", "no_op"]


class InboxIntent(BaseModel):
    intent_type: IntentType
    title: str | None = None
    notes: str | None = None
    priority: TaskPriority = TaskPriority.normal
    due_at: datetime | None = None
    do_window_start: datetime | None = None
    do_window_end: datetime | None = None
    effort_estimate_minutes: int | None = Field(default=None, ge=1)
    energy_required: EnergyLevel | None = None
    recurrence_rule: str | None = None
    item_type: ItemType | None = None
    flags: list[str] = []
    primary_category_name: str | None = None
    clarification_question: str | None = None
    existing_task_id: str | None = None
    existing_item_id: str | None = None
    no_op_reason: str | None = None


class InboxParseResult(BaseModel):
    confirmation: str | None = None
    clarification_question: str | None = None
    intents: list[InboxIntent] = []
