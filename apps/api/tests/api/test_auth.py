from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import LearnedCapabilityProfile, User, UserProfile


pytestmark = pytest.mark.db


def test_google_login_creates_user_and_profile_rows(db_client: TestClient, db_session: Session) -> None:
    claims = {"sub": "google-sub-1", "email": "person@example.com", "name": "Person Example"}

    with patch("app.api.v1.routes.auth.verify_google_id_token", return_value=claims):
        response = db_client.post("/api/v1/auth/google", json={"id_token": "valid"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "person@example.com"

    user = db_session.scalar(select(User).where(User.auth_subject == "google-sub-1"))
    assert user is not None
    assert db_session.get(UserProfile, user.id) is not None
    assert db_session.get(LearnedCapabilityProfile, user.id) is not None


def test_google_login_rejects_invalid_token(db_client: TestClient) -> None:
    with patch("app.services.auth.id_token.verify_oauth2_token", side_effect=ValueError("bad token")):
        response = db_client.post("/api/v1/auth/google", json={"id_token": "invalid"})

    assert response.status_code == 401


def test_me_requires_bearer_token(db_client: TestClient) -> None:
    response = db_client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_returns_authenticated_user(db_client: TestClient, auth_headers: dict[str, str], user: User) -> None:
    response = db_client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert response.json()["user"]["id"] == str(user.id)
