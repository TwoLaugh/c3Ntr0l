from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


ProjectStatus = Literal["active", "paused", "completed", "archived"]


class ProjectCreate(BaseModel):
    domain_id: UUID | None = None
    title: str = Field(min_length=1, max_length=240)
    desired_outcome: str | None = None
    status: ProjectStatus = "active"
    deadline: datetime | None = None
    notes: str | None = None
    metadata_json: dict = Field(default_factory=dict, alias="metadata")


class ProjectUpdate(BaseModel):
    domain_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=240)
    desired_outcome: str | None = None
    status: ProjectStatus | None = None
    deadline: datetime | None = None
    notes: str | None = None
    metadata_json: dict | None = Field(default=None, alias="metadata")


class ProjectRead(BaseModel):
    id: UUID
    domain_id: UUID | None = None
    title: str
    desired_outcome: str | None = None
    status: str
    deadline: datetime | None = None
    notes: str | None = None
    metadata_json: dict = Field(alias="metadata")
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
