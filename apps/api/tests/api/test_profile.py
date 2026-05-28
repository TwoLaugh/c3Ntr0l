import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.db


def test_profile_requires_authentication(db_client: TestClient) -> None:
    response = db_client.get("/api/v1/profile")

    assert response.status_code == 401


def test_profile_returns_defaults(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.get("/api/v1/profile", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["default_tone"] == "terse"
    assert response.json()["preferred_day_view"] == "timeline"
    assert response.json()["ai_change_visibility"] == "quiet"


def test_profile_updates_valid_fields(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.patch(
        "/api/v1/profile",
        headers=auth_headers,
        json={
            "timezone": "Europe/London",
            "preferred_day_view": "list",
            "ai_change_visibility": "prompt",
            "wake_time": "07:30:00",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["preferred_day_view"] == "list"
    assert body["ai_change_visibility"] == "prompt"
    assert body["wake_time"] == "07:30:00"


def test_profile_rejects_invalid_timezone(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.patch("/api/v1/profile", headers=auth_headers, json={"timezone": "Moon/Base"})

    assert response.status_code == 422


def test_learned_capability_is_read_only(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.get("/api/v1/profile/learned-capability", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["confidence_score"] == 0.0

    blocked = db_client.patch("/api/v1/profile/learned-capability", headers=auth_headers, json={"confidence_score": 1})
    assert blocked.status_code == 405
