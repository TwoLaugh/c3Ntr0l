import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import LearnedCapabilityProfile, User, UserProfile
from app.services.auth import create_session_token


pytestmark = pytest.mark.db


def test_accept_insert_item_today_proposal(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    item = db_client.post(
        "/api/v1/items",
        headers=auth_headers,
        json={"title": "Finish auth bug", "priority": "high"},
    ).json()
    proposal = db_client.post(
        "/api/v1/proposed-changes",
        headers=auth_headers,
        json={
            "change_type": "insert_item_today",
            "title": "Add auth bug to today",
            "rationale": "It is urgent and small enough to fit.",
            "payload": {
                "item_id": item["id"],
                "plan_date": "2026-06-01",
                "suggested_start": "2026-06-01T10:00:00Z",
                "suggested_end": "2026-06-01T10:45:00Z",
            },
        },
    ).json()

    accepted = db_client.post(f"/api/v1/proposed-changes/{proposal['id']}/accept", headers=auth_headers)

    assert accepted.status_code == 200
    body = accepted.json()
    assert body["proposed_change"]["status"] == "accepted"
    assert body["plan_item"]["item_id"] == item["id"]
    assert body["plan_item"]["reason_selected"] == "Accepted proposal: Add auth bug to today"

    today = db_client.get("/api/v1/today?plan_date=2026-06-01", headers=auth_headers).json()
    assert today["items"][0]["id"] == body["plan_item"]["id"]

    actions = db_client.get("/api/v1/ai-actions", headers=auth_headers).json()
    assert actions[0]["action_type"] == "accept_proposed_change"


def test_reject_proposal_keeps_today_unchanged(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    item = db_client.post("/api/v1/items", headers=auth_headers, json={"title": "Optional admin"}).json()
    proposal = db_client.post(
        "/api/v1/proposed-changes",
        headers=auth_headers,
        json={
            "change_type": "insert_item_today",
            "title": "Add optional admin to today",
            "payload": {"item_id": item["id"], "plan_date": "2026-06-01"},
        },
    ).json()

    rejected = db_client.post(f"/api/v1/proposed-changes/{proposal['id']}/reject", headers=auth_headers)

    assert rejected.status_code == 200
    assert rejected.json()["proposed_change"]["status"] == "rejected"
    today = db_client.get("/api/v1/today?plan_date=2026-06-01", headers=auth_headers).json()
    assert today["items"] == []


def test_proposal_decision_is_single_use(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    item = db_client.post("/api/v1/items", headers=auth_headers, json={"title": "Prepare slides"}).json()
    proposal = db_client.post(
        "/api/v1/proposed-changes",
        headers=auth_headers,
        json={
            "change_type": "insert_item_today",
            "title": "Add slides to today",
            "payload": {"item_id": item["id"], "plan_date": "2026-06-01"},
        },
    ).json()

    db_client.post(f"/api/v1/proposed-changes/{proposal['id']}/accept", headers=auth_headers)
    second_accept = db_client.post(f"/api/v1/proposed-changes/{proposal['id']}/accept", headers=auth_headers)

    assert second_accept.status_code == 409


def test_proposed_change_ownership_is_enforced(
    db_client: TestClient,
    db_session: Session,
    auth_headers: dict[str, str],
    test_settings: Settings,
) -> None:
    other_user = User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@example.com",
        display_name="Other User",
        auth_provider="google",
        auth_subject=str(uuid.uuid4()),
    )
    db_session.add(other_user)
    db_session.flush()
    db_session.add(UserProfile(user_id=other_user.id))
    db_session.add(LearnedCapabilityProfile(user_id=other_user.id))
    db_session.commit()
    other_headers = {"Authorization": f"Bearer {create_session_token(other_user.id, test_settings)}"}
    other_item = db_client.post("/api/v1/items", headers=other_headers, json={"title": "Private item"}).json()
    proposal = db_client.post(
        "/api/v1/proposed-changes",
        headers=other_headers,
        json={
            "change_type": "insert_item_today",
            "title": "Private proposal",
            "payload": {"item_id": other_item["id"], "plan_date": "2026-06-01"},
        },
    ).json()

    response = db_client.get(f"/api/v1/proposed-changes/{proposal['id']}", headers=auth_headers)
    accept = db_client.post(f"/api/v1/proposed-changes/{proposal['id']}/accept", headers=auth_headers)

    assert response.status_code == 404
    assert accept.status_code == 404
