from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class DomainCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    weight: Decimal = Field(default=Decimal("1.0"), ge=0)
    active: bool = True
    metadata_json: dict = Field(default_factory=dict, alias="metadata")


class DomainUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    weight: Decimal | None = Field(default=None, ge=0)
    active: bool | None = None
    metadata_json: dict | None = Field(default=None, alias="metadata")


class DomainRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    weight: Decimal
    active: bool
    metadata_json: dict = Field(alias="metadata")
    project_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
