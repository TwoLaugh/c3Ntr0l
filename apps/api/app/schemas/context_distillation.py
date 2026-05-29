from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import AIChangeLevel, ConfidenceLevel, ContextSectionType
from app.schemas.context_section import ContextSectionRead


class ContextSectionDistillationUpdate(BaseModel):
    target_section_id: UUID | None = None
    title: str = Field(min_length=1, max_length=240)
    section_type: ContextSectionType = ContextSectionType.custom
    summary: str | None = None
    body: str
    structured_facts: dict = Field(default_factory=dict)
    confidence_level: ConfidenceLevel = ConfidenceLevel.low
    confidence_notes: str | None = None
    change_reason: str
    change_level: AIChangeLevel = AIChangeLevel.report


class ContextDistillationResult(BaseModel):
    message: str | None = None
    section_updates: list[ContextSectionDistillationUpdate] = []


class ContextDistillationResponse(BaseModel):
    entry_id: UUID
    message: str | None = None
    sections: list[ContextSectionRead]
