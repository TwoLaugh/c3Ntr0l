import uuid

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import PlanBlockType, PlanItemStatus, PlanStatus


class DailyPlan(Base):
    __tablename__ = "daily_plans"
    __table_args__ = (UniqueConstraint("user_id", "plan_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    weekly_plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("weekly_plans.id", ondelete="SET NULL"))
    plan_date: Mapped[object] = mapped_column(Date, nullable=False)
    generated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    default_view_mode: Mapped[str] = mapped_column(String, nullable=False, default="timeline")
    capacity_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PlanStatus] = mapped_column(Enum(PlanStatus, name="plan_status"), nullable=False, default=PlanStatus.draft)


class DailyPlanItem(Base):
    __tablename__ = "daily_plan_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    daily_plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_plans.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"))
    item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="SET NULL"))
    title_snapshot: Mapped[str] = mapped_column(String, nullable=False)
    suggested_start: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    suggested_end: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    do_window_start: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    do_window_end: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    block_type: Mapped[PlanBlockType] = mapped_column(Enum(PlanBlockType, name="plan_block_type"), nullable=False, default=PlanBlockType.suggested)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_fixed_time: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reason_selected: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PlanItemStatus] = mapped_column(Enum(PlanItemStatus, name="plan_item_status"), nullable=False, default=PlanItemStatus.planned)
    user_edited_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
