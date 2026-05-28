import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import CompletionEventType, EnergyLevel, TaskPriority, TaskStatus


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    domain_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("domains.id", ondelete="SET NULL"))
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"))
    source_inbox_message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inbox_messages.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.active)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority, name="task_priority"), nullable=False, default=TaskPriority.normal)
    due_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    do_window_start: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    do_window_end: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    effort_estimate_minutes: Mapped[int | None] = mapped_column(Integer)
    energy_required: Mapped[EnergyLevel | None] = mapped_column(Enum(EnergyLevel, name="energy_level"))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TaskCompletionEvent(Base):
    __tablename__ = "task_completion_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    plan_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_plan_items.id", ondelete="SET NULL"))
    event_type: Mapped[CompletionEventType] = mapped_column(Enum(CompletionEventType, name="completion_event_type"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    ai_interpretation: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
