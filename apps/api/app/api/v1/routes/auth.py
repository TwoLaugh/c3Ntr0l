from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, GoogleAuthRequest, MeResponse
from app.services.auth import create_session_token, get_or_create_dev_user, get_or_create_google_user, verify_google_id_token

router = APIRouter()


@router.post("/google", response_model=AuthResponse)
def login_with_google(
    request: GoogleAuthRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    claims = verify_google_id_token(request.id_token, settings)
    user = get_or_create_google_user(db, claims)
    return AuthResponse(access_token=create_session_token(user.id, settings), user=user)


@router.post("/dev", response_model=AuthResponse)
def login_with_dev_user(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    if settings.app_env.lower() in {"production", "prod"} or not settings.allow_dev_auth:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dev auth is disabled")

    user = get_or_create_dev_user(db)
    return AuthResponse(access_token=create_session_token(user.id, settings), user=user)


@router.get("/me", response_model=MeResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> MeResponse:
    return MeResponse(authenticated=True, user=current_user)
