import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import ProposedChangeStatus, ProposedChangeType, SourceType


class ProposedChange(Base):
    __tablename__ = "proposed_changes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType, name="source_type"), nullable=False, default=SourceType.ai)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    change_type: Mapped[ProposedChangeType] = mapped_column(
        Enum(ProposedChangeType, name="proposed_change_type"), nullable=False
    )
    status: Mapped[ProposedChangeStatus] = mapped_column(
        Enum(ProposedChangeStatus, name="proposed_change_status"), nullable=False, default=ProposedChangeStatus.pending
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result: Mapped[dict | None] = mapped_column(JSONB)
    decided_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
