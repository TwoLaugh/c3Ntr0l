from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import PlanBlockType, PlanItemStatus, PlanStatus


class DailyPlanItemRead(BaseModel):
    id: UUID
    task_id: UUID | None = None
    title_snapshot: str
    suggested_start: datetime | None = None
    suggested_end: datetime | None = None
    do_window_start: datetime | None = None
    do_window_end: datetime | None = None
    block_type: PlanBlockType
    position: int
    is_fixed_time: bool
    is_optional: bool
    reason_selected: str | None = None
    status: PlanItemStatus
    user_edited_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DailyPlanRead(BaseModel):
    id: UUID
    plan_date: date
    default_view_mode: str
    capacity_snapshot: dict
    summary: str | None = None
    status: PlanStatus
    generated_at: datetime
    items: list[DailyPlanItemRead]


class TodayItemUpdate(BaseModel):
    suggested_start: datetime | None = None
    suggested_end: datetime | None = None
    do_window_start: datetime | None = None
    do_window_end: datetime | None = None
    position: int | None = Field(default=None, ge=0)
    is_fixed_time: bool | None = None
    is_optional: bool | None = None
    status: PlanItemStatus | None = None

    @model_validator(mode="after")
    def validate_suggested_times(self) -> "TodayItemUpdate":
        if self.suggested_start and self.suggested_end and self.suggested_end <= self.suggested_start:
            raise ValueError("suggested_end must be after suggested_start")
        return self
