from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import SourceType


class AIActionLogRead(BaseModel):
    id: UUID
    source_type: SourceType
    source_id: UUID | None = None
    action_type: str
    target_type: str
    target_id: UUID | None = None
    before_state: dict | None = None
    after_state: dict | None = None
    reason: str | None = None
    reversible: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UndoActionResponse(BaseModel):
    action: AIActionLogRead
    undone: bool
    message: str
