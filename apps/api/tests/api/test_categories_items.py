import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import LearnedCapabilityProfile, User, UserProfile
from app.services.auth import create_session_token


pytestmark = pytest.mark.db


def test_category_crud_and_archive(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    create_response = db_client.post(
        "/api/v1/categories",
        headers=auth_headers,
        json={"name": "Driving test", "description": "Driving prep", "sort_order": 5},
    )

    assert create_response.status_code == 201
    category = create_response.json()
    assert category["name"] == "Driving test"
    assert category["status"] == "active"

    patch_response = db_client.patch(
        f"/api/v1/categories/{category['id']}",
        headers=auth_headers,
        json={"description": "Driving lessons, theory, and admin"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["description"] == "Driving lessons, theory, and admin"

    archive_response = db_client.post(f"/api/v1/categories/{category['id']}/archive", headers=auth_headers)
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "archived"

    list_response = db_client.get("/api/v1/categories", headers=auth_headers)
    assert list_response.json() == []


def test_item_create_with_recurrence_and_events(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    category = db_client.post("/api/v1/categories", headers=auth_headers, json={"name": "Health"}).json()
    entry = db_client.post(
        "/api/v1/entries",
        headers=auth_headers,
        json={"source_type": "inbox", "raw_text": "Add back rehab daily."},
    ).json()
    context = db_client.post(
        "/api/v1/context-sections",
        headers=auth_headers,
        json={"title": "Back rehab", "section_type": "health", "body": "Rehab context."},
    ).json()

    create_response = db_client.post(
        "/api/v1/items",
        headers=auth_headers,
        json={
            "title": "Back rehab",
            "primary_category_id": category["id"],
            "source_entry_id": entry["id"],
            "item_type": "recurring_action",
            "flags": ["recurring", "health"],
            "recurrence": {"recurrence_rule": "FREQ=DAILY"},
            "linked_context_section_ids": [context["id"]],
        },
    )

    assert create_response.status_code == 201
    item = create_response.json()
    assert item["title"] == "Back rehab"
    assert item["flags"] == ["recurring", "health"]

    partial = db_client.post(
        f"/api/v1/items/{item['id']}/partial",
        headers=auth_headers,
        json={"amount_done": "5 minutes", "note": "Minimum version."},
    )
    assert partial.status_code == 200
    assert partial.json()["event_type"] == "partial"

    complete = db_client.post(f"/api/v1/items/{item['id']}/complete", headers=auth_headers, json={})
    assert complete.status_code == 200
    assert complete.json()["event_type"] == "complete"

    fetched = db_client.get(f"/api/v1/items/{item['id']}", headers=auth_headers)
    assert fetched.json()["status"] == "completed"

    events = db_client.get(f"/api/v1/items/{item['id']}/events", headers=auth_headers)
    assert {event["event_type"] for event in events.json()} == {"complete", "partial"}


def test_item_rejects_foreign_category(
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
    other_category = db_client.post("/api/v1/categories", headers=other_headers, json={"name": "Private"}).json()

    response = db_client.post(
        "/api/v1/items",
        headers=auth_headers,
        json={"title": "Should fail", "primary_category_id": other_category["id"]},
    )

    assert response.status_code == 422
