from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, Field


Tone = Literal["terse", "warm", "direct"]
DayView = Literal["timeline", "list"]
AIChangeVisibility = Literal["quiet", "digest", "prompt"]


class WorkHours(BaseModel):
    monday: list[str] | None = None
    tuesday: list[str] | None = None
    wednesday: list[str] | None = None
    thursday: list[str] | None = None
    friday: list[str] | None = None
    saturday: list[str] | None = None
    sunday: list[str] | None = None


class UserProfileRead(BaseModel):
    timezone: str
    default_tone: Tone
    preferred_day_view: DayView
    wake_time: time | None = None
    sleep_time: time | None = None
    work_hours: dict = Field(default_factory=dict)
    planning_style: str | None = None
    review_style: str | None = None
    ai_change_visibility: AIChangeVisibility
    onboarding_completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    timezone: str | None = None
    default_tone: Tone | None = None
    preferred_day_view: DayView | None = None
    wake_time: time | None = None
    sleep_time: time | None = None
    work_hours: dict | None = None
    planning_style: str | None = None
    review_style: str | None = None
    ai_change_visibility: AIChangeVisibility | None = None


class LearnedCapabilityProfileRead(BaseModel):
    weekday_focus_minutes_typical: int | None = None
    weekend_focus_minutes_typical: int | None = None
    weekday_maintenance_minutes_typical: int | None = None
    weekend_maintenance_minutes_typical: int | None = None
    morning_reliability: float | None = None
    afternoon_reliability: float | None = None
    evening_reliability: float | None = None
    plan_completion_rate_14d: float | None = None
    plan_completion_rate_30d: float | None = None
    routine_completion_rate_14d: float | None = None
    overload_sensitivity: float | None = None
    confidence_score: float
    updated_at: datetime

    model_config = {"from_attributes": True}
