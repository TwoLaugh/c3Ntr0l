import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Time, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String)
    auth_provider: Mapped[str] = mapped_column(String, nullable=False, default="google")
    auth_subject: Mapped[str | None] = mapped_column(String, unique=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    timezone: Mapped[str] = mapped_column(String, nullable=False, default="Europe/London")
    default_tone: Mapped[str] = mapped_column(String, nullable=False, default="terse")
    preferred_day_view: Mapped[str] = mapped_column(String, nullable=False, default="timeline")
    wake_time: Mapped[object | None] = mapped_column(Time)
    sleep_time: Mapped[object | None] = mapped_column(Time)
    work_hours: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    planning_style: Mapped[str | None] = mapped_column(String)
    review_style: Mapped[str | None] = mapped_column(String)
    ai_change_visibility: Mapped[str] = mapped_column(String, nullable=False, default="quiet")
    onboarding_completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class LearnedCapabilityProfile(Base):
    __tablename__ = "learned_capability_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    weekday_focus_minutes_typical: Mapped[int | None] = mapped_column(Integer)
    weekend_focus_minutes_typical: Mapped[int | None] = mapped_column(Integer)
    weekday_maintenance_minutes_typical: Mapped[int | None] = mapped_column(Integer)
    weekend_maintenance_minutes_typical: Mapped[int | None] = mapped_column(Integer)
    morning_reliability: Mapped[float | None] = mapped_column(Numeric(4, 3))
    afternoon_reliability: Mapped[float | None] = mapped_column(Numeric(4, 3))
    evening_reliability: Mapped[float | None] = mapped_column(Numeric(4, 3))
    plan_completion_rate_14d: Mapped[float | None] = mapped_column(Numeric(4, 3))
    plan_completion_rate_30d: Mapped[float | None] = mapped_column(Numeric(4, 3))
    routine_completion_rate_14d: Mapped[float | None] = mapped_column(Numeric(4, 3))
    overload_sensitivity: Mapped[float | None] = mapped_column(Numeric(4, 3))
    confidence_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
