import uuid

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import EnergyLevel


class DailyReview(Base):
    __tablename__ = "daily_reviews"
    __table_args__ = (UniqueConstraint("user_id", "review_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    review_date: Mapped[object] = mapped_column(Date, nullable=False)
    prompts: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    responses: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    energy_level: Mapped[EnergyLevel | None] = mapped_column(Enum(EnergyLevel, name="energy_level"))
    load_fit: Mapped[str | None] = mapped_column(String)
    mood: Mapped[str | None] = mapped_column(String)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
