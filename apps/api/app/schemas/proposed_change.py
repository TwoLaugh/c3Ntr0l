from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import ProposedChangeStatus, ProposedChangeType, SourceType
from app.schemas.today import DailyPlanItemRead


class ProposedChangeCreate(BaseModel):
    change_type: ProposedChangeType
    title: str
    rationale: str | None = None
    payload: dict = Field(default_factory=dict)
    source_type: SourceType = SourceType.ai
    source_id: UUID | None = None


class InsertItemTodayPayload(BaseModel):
    item_id: UUID
    plan_date: date | None = None
    suggested_start: datetime | None = None
    suggested_end: datetime | None = None
    position: int | None = None


class ProposedChangeRead(BaseModel):
    id: UUID
    source_type: SourceType
    source_id: UUID | None = None
    change_type: ProposedChangeType
    status: ProposedChangeStatus
    title: str
    rationale: str | None = None
    payload: dict
    result: dict | None = None
    decided_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProposedChangeDecisionResponse(BaseModel):
    proposed_change: ProposedChangeRead
    plan_item: DailyPlanItemRead | None = None
    message: str
