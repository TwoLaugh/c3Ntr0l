import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import EnergyLevel, ItemEventType, ItemPriority, ItemStatus, ItemType, RecurrenceStatus


class Item(Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    primary_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL")
    )
    source_entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("entries.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    item_type: Mapped[ItemType] = mapped_column(Enum(ItemType, name="item_type"), nullable=False, default=ItemType.action)
    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus, name="item_status"), nullable=False, default=ItemStatus.active)
    priority: Mapped[ItemPriority] = mapped_column(
        Enum(ItemPriority, name="item_priority"), nullable=False, default=ItemPriority.normal
    )
    flags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    due_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    do_window_start: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    do_window_end: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    effort_estimate_minutes: Mapped[int | None] = mapped_column(Integer)
    energy_required: Mapped[EnergyLevel | None] = mapped_column(Enum(EnergyLevel, name="energy_level"))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ItemRecurrence(Base):
    __tablename__ = "item_recurrence"
    __table_args__ = (UniqueConstraint("item_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    recurrence_rule: Mapped[str] = mapped_column(String, nullable=False)
    preferred_time_window: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[RecurrenceStatus] = mapped_column(
        Enum(RecurrenceStatus, name="recurrence_status"), nullable=False, default=RecurrenceStatus.active
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ItemContextLink(Base):
    __tablename__ = "item_context_links"
    __table_args__ = (UniqueConstraint("item_id", "context_section_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    context_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("context_sections.id", ondelete="CASCADE"), nullable=False
    )
    link_type: Mapped[str] = mapped_column(String, nullable=False, default="related")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ItemCategoryLink(Base):
    __tablename__ = "item_category_links"
    __table_args__ = (UniqueConstraint("item_id", "category_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    link_type: Mapped[str] = mapped_column(String, nullable=False, default="related")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ItemCompletionEvent(Base):
    __tablename__ = "item_completion_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    plan_instance_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    event_type: Mapped[ItemEventType] = mapped_column(Enum(ItemEventType, name="item_event_type"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    amount_done: Mapped[str | None] = mapped_column(Text)
    ai_interpretation: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
