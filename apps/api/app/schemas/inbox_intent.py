from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import EnergyLevel, TaskPriority


IntentType = Literal["create_task", "create_routine", "clarification"]


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
    clarification_question: str | None = None


class InboxParseResult(BaseModel):
    confirmation: str | None = None
    clarification_question: str | None = None
    intents: list[InboxIntent] = []
