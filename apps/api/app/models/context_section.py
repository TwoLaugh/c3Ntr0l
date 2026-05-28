import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import (
    AIChangeLevel,
    ConfidenceLevel,
    ContextRevisionSource,
    ContextSectionType,
    ContextStatus,
)


class ContextSection(Base):
    __tablename__ = "context_sections"
    __table_args__ = (UniqueConstraint("user_id", "title"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    section_type: Mapped[ContextSectionType] = mapped_column(
        Enum(ContextSectionType, name="context_section_type"), nullable=False, default=ContextSectionType.custom
    )
    summary: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    structured_facts: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel, name="confidence_level"), nullable=False, default=ConfidenceLevel.low
    )
    confidence_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ContextStatus] = mapped_column(
        Enum(ContextStatus, name="context_status"), nullable=False, default=ContextStatus.active
    )
    created_by: Mapped[ContextRevisionSource] = mapped_column(
        Enum(ContextRevisionSource, name="context_revision_source"), nullable=False, default=ContextRevisionSource.user
    )
    updated_by: Mapped[ContextRevisionSource] = mapped_column(
        Enum(ContextRevisionSource, name="context_revision_source"), nullable=False, default=ContextRevisionSource.user
    )
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ContextSectionRevision(Base):
    __tablename__ = "context_section_revisions"
    __table_args__ = (UniqueConstraint("context_section_id", "revision_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    context_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("context_sections.id", ondelete="CASCADE"), nullable=False
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title_snapshot: Mapped[str] = mapped_column(String, nullable=False)
    summary_snapshot: Mapped[str | None] = mapped_column(Text)
    body_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    structured_facts_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    confidence_level_snapshot: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel, name="confidence_level"), nullable=False
    )
    confidence_notes_snapshot: Mapped[str | None] = mapped_column(Text)
    change_reason: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[ContextRevisionSource] = mapped_column(
        Enum(ContextRevisionSource, name="context_revision_source"), nullable=False
    )
    change_level: Mapped[AIChangeLevel] = mapped_column(
        Enum(AIChangeLevel, name="ai_change_level"), nullable=False, default=AIChangeLevel.report
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ContextEvidenceLink(Base):
    __tablename__ = "context_evidence_links"
    __table_args__ = (UniqueConstraint("context_section_id", "entry_id", "context_section_revision_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    context_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("context_sections.id", ondelete="CASCADE"), nullable=False
    )
    context_section_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("context_section_revisions.id", ondelete="CASCADE")
    )
    entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entries.id", ondelete="CASCADE"), nullable=False)
    relevance: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel, name="confidence_level"), nullable=False, default=ConfidenceLevel.medium
    )
    evidence_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
