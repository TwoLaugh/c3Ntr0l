import uuid

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import PlanStatus


class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"
    __table_args__ = (UniqueConstraint("user_id", "week_start_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    week_start_date: Mapped[object] = mapped_column(Date, nullable=False)
    generated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    focus_notes: Mapped[str | None] = mapped_column(Text)
    capacity_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[PlanStatus] = mapped_column(Enum(PlanStatus, name="plan_status"), nullable=False, default=PlanStatus.draft)
    accepted_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
