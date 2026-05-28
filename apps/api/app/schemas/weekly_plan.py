from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import PlanStatus
from app.schemas.today import DailyPlanRead


class WeeklyPlanUpdate(BaseModel):
    summary: str | None = None
    focus_notes: str | None = None
    capacity_snapshot: dict | None = None
    status: PlanStatus | None = None


class WeeklyPlanRead(BaseModel):
    id: UUID
    week_start_date: date
    generated_at: datetime
    summary: str | None = None
    focus_notes: str | None = None
    capacity_snapshot: dict
    status: PlanStatus
    accepted_at: datetime | None = None
    daily_plans: list[DailyPlanRead] = []

    model_config = {"from_attributes": True}
