from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import EnergyLevel, ItemEventType, ItemPriority, ItemStatus, ItemType, RecurrenceStatus


class ItemRecurrencePayload(BaseModel):
    recurrence_rule: str = Field(min_length=1)
    preferred_time_window: dict = Field(default_factory=dict)
    status: RecurrenceStatus = RecurrenceStatus.active


class ItemCreate(BaseModel):
    primary_category_id: UUID | None = None
    source_entry_id: UUID | None = None
    title: str = Field(min_length=1, max_length=300)
    notes: str | None = None
    item_type: ItemType = ItemType.action
    status: ItemStatus = ItemStatus.active
    priority: ItemPriority = ItemPriority.normal
    flags: list[str] = Field(default_factory=list)
    due_at: datetime | None = None
    do_window_start: datetime | None = None
    do_window_end: datetime | None = None
    effort_estimate_minutes: int | None = Field(default=None, ge=1)
    energy_required: EnergyLevel | None = None
    metadata_json: dict = Field(default_factory=dict, alias="metadata")
    recurrence: ItemRecurrencePayload | None = None
    linked_context_section_ids: list[UUID] = Field(default_factory=list)
    linked_category_ids: list[UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_do_window(self) -> "ItemCreate":
        if self.do_window_start and self.do_window_end and self.do_window_end <= self.do_window_start:
            raise ValueError("do_window_end must be after do_window_start")
        return self


class ItemUpdate(BaseModel):
    primary_category_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    notes: str | None = None
    item_type: ItemType | None = None
    status: ItemStatus | None = None
    priority: ItemPriority | None = None
    flags: list[str] | None = None
    due_at: datetime | None = None
    do_window_start: datetime | None = None
    do_window_end: datetime | None = None
    effort_estimate_minutes: int | None = Field(default=None, ge=1)
    energy_required: EnergyLevel | None = None
    metadata_json: dict | None = Field(default=None, alias="metadata")

    @model_validator(mode="after")
    def validate_do_window(self) -> "ItemUpdate":
        if self.do_window_start and self.do_window_end and self.do_window_end <= self.do_window_start:
            raise ValueError("do_window_end must be after do_window_start")
        return self


class ItemRead(BaseModel):
    id: UUID
    primary_category_id: UUID | None = None
    source_entry_id: UUID | None = None
    title: str
    notes: str | None = None
    item_type: ItemType
    status: ItemStatus
    priority: ItemPriority
    flags: list[str]
    due_at: datetime | None = None
    do_window_start: datetime | None = None
    do_window_end: datetime | None = None
    effort_estimate_minutes: int | None = None
    energy_required: EnergyLevel | None = None
    metadata_json: dict = Field(validation_alias="metadata_json", serialization_alias="metadata")
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class ItemRecurrenceRead(BaseModel):
    id: UUID
    item_id: UUID
    recurrence_rule: str
    preferred_time_window: dict
    status: RecurrenceStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ItemCompletionEventCreate(BaseModel):
    note: str | None = None
    amount_done: str | None = None


class ItemCompletionEventRead(BaseModel):
    id: UUID
    item_id: UUID
    plan_instance_id: UUID | None = None
    event_type: ItemEventType
    note: str | None = None
    amount_done: str | None = None
    ai_interpretation: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
