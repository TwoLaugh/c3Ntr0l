from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import EnergyLevel
from app.schemas.task import TaskRead


class RoutineCreate(BaseModel):
    domain_id: UUID | None = None
    title: str = Field(min_length=1, max_length=240)
    notes: str | None = None
    recurrence_rule: str = Field(min_length=1)
    preferred_time_window: dict = Field(default_factory=dict)
    effort_estimate_minutes: int | None = Field(default=None, ge=1)
    energy_required: EnergyLevel | None = None
    active: bool = True
    metadata_json: dict = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="after")
    def validate_recurrence_rule(self) -> "RoutineCreate":
        parse_recurrence_rule(self.recurrence_rule)
        return self


class RoutineUpdate(BaseModel):
    domain_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=240)
    notes: str | None = None
    recurrence_rule: str | None = Field(default=None, min_length=1)
    preferred_time_window: dict | None = None
    effort_estimate_minutes: int | None = Field(default=None, ge=1)
    energy_required: EnergyLevel | None = None
    active: bool | None = None
    metadata_json: dict | None = Field(default=None, alias="metadata")

    @model_validator(mode="after")
    def validate_recurrence_rule(self) -> "RoutineUpdate":
        if self.recurrence_rule is not None:
            parse_recurrence_rule(self.recurrence_rule)
        return self


class RoutineRead(BaseModel):
    id: UUID
    domain_id: UUID | None = None
    title: str
    notes: str | None = None
    recurrence_rule: str
    preferred_time_window: dict
    effort_estimate_minutes: int | None = None
    energy_required: EnergyLevel | None = None
    active: bool
    metadata_json: dict = Field(alias="metadata")
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class RoutineInstanceRead(BaseModel):
    id: UUID
    routine_id: UUID
    task_id: UUID
    scheduled_for_date: date
    generated_at: datetime
    task: TaskRead | None = None

    model_config = {"from_attributes": True}


class RoutineGenerateResponse(BaseModel):
    instances: list[RoutineInstanceRead]


def parse_recurrence_rule(rule: str) -> dict[str, str]:
    parts = {}
    for raw_part in rule.split(";"):
        if "=" not in raw_part:
            raise ValueError("Recurrence rule parts must be KEY=VALUE")
        key, value = raw_part.split("=", 1)
        parts[key.upper()] = value.upper()

    frequency = parts.get("FREQ")
    if frequency not in {"DAILY", "WEEKLY"}:
        raise ValueError("Only FREQ=DAILY and FREQ=WEEKLY are supported in V1")

    if frequency == "WEEKLY" and "BYDAY" in parts:
        valid_days = {"MO", "TU", "WE", "TH", "FR", "SA", "SU"}
        days = {day.strip() for day in parts["BYDAY"].split(",") if day.strip()}
        if not days or not days.issubset(valid_days):
            raise ValueError("BYDAY must contain valid weekday codes")

    return parts
