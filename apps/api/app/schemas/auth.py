from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class GoogleAuthRequest(BaseModel):
    id_token: str


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str | None = None
    auth_provider: str
    auth_subject: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class MeResponse(BaseModel):
    authenticated: bool
    user: UserRead
