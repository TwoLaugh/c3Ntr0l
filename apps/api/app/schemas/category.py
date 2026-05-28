from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import CategoryStatus


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    description: str | None = None
    sort_order: int = 0
    metadata_json: dict = Field(default_factory=dict, alias="metadata")


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = None
    status: CategoryStatus | None = None
    sort_order: int | None = None
    metadata_json: dict | None = Field(default=None, alias="metadata")


class CategoryRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    status: CategoryStatus
    sort_order: int
    metadata_json: dict = Field(validation_alias="metadata_json", serialization_alias="metadata")
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
