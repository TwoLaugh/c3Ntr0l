from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InboxMessageCreate(BaseModel):
    raw_text: str = Field(min_length=1)


class InboxActionRead(BaseModel):
    action_type: str
    target_type: str | None = None
    target_id: UUID | None = None
    message: str


class InboxMessageRead(BaseModel):
    id: UUID
    raw_text: str
    processing_status: str
    parsed_intents: dict | None = None
    created_at: datetime
    processed_at: datetime | None = None
    confirmation: str | None = None
    actions: list[InboxActionRead] = []

    model_config = {"from_attributes": True}
