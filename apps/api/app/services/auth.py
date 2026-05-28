from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
from typing import Any
import uuid

from fastapi import HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import LearnedCapabilityProfile, User, UserProfile


def verify_google_id_token(token: str, settings: Settings) -> dict[str, Any]:
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID is not configured",
        )

    try:
        claims = id_token.verify_oauth2_token(token, requests.Request(), settings.google_client_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token") from exc

    if not claims.get("sub") or not claims.get("email"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google token missing required claims")

    return claims


def get_or_create_google_user(db: Session, claims: dict[str, Any]) -> User:
    auth_subject = claims["sub"]
    email = claims["email"]
    display_name = claims.get("name")

    user = db.scalar(select(User).where(User.auth_provider == "google", User.auth_subject == auth_subject))
    if user is None:
        user = User(email=email, display_name=display_name, auth_provider="google", auth_subject=auth_subject)
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id))
        db.add(LearnedCapabilityProfile(user_id=user.id))
    else:
        user.email = email
        user.display_name = display_name
        ensure_profile_rows(db, user.id)

    db.commit()
    db.refresh(user)
    return user


def get_or_create_dev_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.auth_provider == "dev", User.auth_subject == "local-dev-user"))
    if user is None:
        user = User(
            email="dev@example.com",
            display_name="Local Dev",
            auth_provider="dev",
            auth_subject="local-dev-user",
        )
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id))
        db.add(LearnedCapabilityProfile(user_id=user.id))
    else:
        ensure_profile_rows(db, user.id)

    db.commit()
    db.refresh(user)
    return user


def ensure_profile_rows(db: Session, user_id: uuid.UUID) -> None:
    if db.get(UserProfile, user_id) is None:
        db.add(UserProfile(user_id=user_id))
    if db.get(LearnedCapabilityProfile, user_id) is None:
        db.add(LearnedCapabilityProfile(user_id=user_id))


def create_session_token(user_id: uuid.UUID, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.session_token_ttl_seconds)).timestamp()),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode().rstrip("=")
    signature = _sign(payload_b64, settings.session_secret_key)
    return f"{payload_b64}.{signature}"


def parse_session_token(token: str, settings: Settings) -> uuid.UUID:
    try:
        payload_b64, signature = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token") from exc

    if not hmac.compare_digest(signature, _sign(payload_b64, settings.session_secret_key)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")

    try:
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4))
        payload = json.loads(payload_bytes)
        expires_at = int(payload["exp"])
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token") from exc

    if expires_at < int(datetime.now(UTC).timestamp()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired bearer token")

    return user_id


def _sign(payload_b64: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), payload_b64.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")
