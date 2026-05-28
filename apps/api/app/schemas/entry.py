from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import EntryActor, EntrySource


class EntryCreate(BaseModel):
    source_type: EntrySource
    source_id: UUID | None = None
    actor: EntryActor = EntryActor.user
    raw_text: str = Field(min_length=1)
    occurred_at: datetime | None = None
    metadata_json: dict = Field(default_factory=dict, alias="metadata")
    ai_interpretation: dict | None = None


class EntryRead(BaseModel):
    id: UUID
    source_type: EntrySource
    source_id: UUID | None = None
    actor: EntryActor
    raw_text: str
    occurred_at: datetime
    metadata_json: dict = Field(validation_alias="metadata_json", serialization_alias="metadata")
    ai_interpretation: dict | None = None
    archived_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
