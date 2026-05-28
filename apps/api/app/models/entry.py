import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import EntryActor, EntrySource


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_type: Mapped[EntrySource] = mapped_column(Enum(EntrySource, name="entry_source"), nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    actor: Mapped[EntryActor] = mapped_column(Enum(EntryActor, name="entry_actor"), nullable=False, default=EntryActor.user)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    ai_interpretation: Mapped[dict | None] = mapped_column(JSONB)
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
