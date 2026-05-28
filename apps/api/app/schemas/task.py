from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import CompletionEventType, EnergyLevel, TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    domain_id: UUID | None = None
    project_id: UUID | None = None
    title: str = Field(min_length=1, max_length=300)
    notes: str | None = None
    status: TaskStatus = TaskStatus.active
    priority: TaskPriority = TaskPriority.normal
    due_at: datetime | None = None
    do_window_start: datetime | None = None
    do_window_end: datetime | None = None
    effort_estimate_minutes: int | None = Field(default=None, ge=1)
    energy_required: EnergyLevel | None = None
    metadata_json: dict = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="after")
    def validate_do_window(self) -> "TaskCreate":
        if self.do_window_start and self.do_window_end and self.do_window_end <= self.do_window_start:
            raise ValueError("do_window_end must be after do_window_start")
        return self


class TaskUpdate(BaseModel):
    domain_id: UUID | None = None
    project_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    notes: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_at: datetime | None = None
    do_window_start: datetime | None = None
    do_window_end: datetime | None = None
    effort_estimate_minutes: int | None = Field(default=None, ge=1)
    energy_required: EnergyLevel | None = None
    metadata_json: dict | None = Field(default=None, alias="metadata")

    @model_validator(mode="after")
    def validate_do_window(self) -> "TaskUpdate":
        if self.do_window_start and self.do_window_end and self.do_window_end <= self.do_window_start:
            raise ValueError("do_window_end must be after do_window_start")
        return self


class TaskRead(BaseModel):
    id: UUID
    domain_id: UUID | None = None
    project_id: UUID | None = None
    source_inbox_message_id: UUID | None = None
    title: str
    notes: str | None = None
    status: TaskStatus
    priority: TaskPriority
    due_at: datetime | None = None
    do_window_start: datetime | None = None
    do_window_end: datetime | None = None
    effort_estimate_minutes: int | None = None
    energy_required: EnergyLevel | None = None
    metadata_json: dict = Field(alias="metadata")
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class TaskCompletionEventRead(BaseModel):
    id: UUID
    task_id: UUID
    plan_item_id: UUID | None = None
    event_type: CompletionEventType
    note: str | None = None
    ai_interpretation: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
