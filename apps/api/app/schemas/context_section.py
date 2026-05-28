from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import (
    AIChangeLevel,
    ConfidenceLevel,
    ContextRevisionSource,
    ContextSectionType,
    ContextStatus,
)


class ContextSectionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    section_type: ContextSectionType = ContextSectionType.custom
    summary: str | None = None
    body: str = ""
    structured_facts: dict = Field(default_factory=dict)
    confidence_level: ConfidenceLevel = ConfidenceLevel.low
    confidence_notes: str | None = None
    created_by: ContextRevisionSource = ContextRevisionSource.user
    metadata_json: dict = Field(default_factory=dict, alias="metadata")
    change_reason: str | None = None
    change_level: AIChangeLevel = AIChangeLevel.report
    evidence_entry_ids: list[UUID] = Field(default_factory=list)


class ContextSectionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    section_type: ContextSectionType | None = None
    summary: str | None = None
    body: str | None = None
    structured_facts: dict | None = None
    confidence_level: ConfidenceLevel | None = None
    confidence_notes: str | None = None
    status: ContextStatus | None = None
    updated_by: ContextRevisionSource = ContextRevisionSource.user
    metadata_json: dict | None = Field(default=None, alias="metadata")
    change_reason: str | None = None
    change_level: AIChangeLevel = AIChangeLevel.report
    evidence_entry_ids: list[UUID] = Field(default_factory=list)


class ContextSectionRead(BaseModel):
    id: UUID
    title: str
    section_type: ContextSectionType
    summary: str | None = None
    body: str
    structured_facts: dict
    confidence_level: ConfidenceLevel
    confidence_notes: str | None = None
    status: ContextStatus
    created_by: ContextRevisionSource
    updated_by: ContextRevisionSource
    metadata_json: dict = Field(validation_alias="metadata_json", serialization_alias="metadata")
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class ContextSectionRevisionRead(BaseModel):
    id: UUID
    context_section_id: UUID
    revision_number: int
    title_snapshot: str
    summary_snapshot: str | None = None
    body_snapshot: str
    structured_facts_snapshot: dict
    confidence_level_snapshot: ConfidenceLevel
    confidence_notes_snapshot: str | None = None
    change_reason: str | None = None
    changed_by: ContextRevisionSource
    change_level: AIChangeLevel
    created_at: datetime

    model_config = {"from_attributes": True}


class ContextEvidenceLinkCreate(BaseModel):
    entry_id: UUID
    context_section_revision_id: UUID | None = None
    relevance: ConfidenceLevel = ConfidenceLevel.medium
    evidence_note: str | None = None


class ContextEvidenceLinkRead(BaseModel):
    id: UUID
    context_section_id: UUID
    context_section_revision_id: UUID | None = None
    entry_id: UUID
    relevance: ConfidenceLevel
    evidence_note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
