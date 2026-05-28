import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import LearnedCapabilityProfile, User, UserProfile
from app.services.auth import create_session_token
from app.core.config import Settings


pytestmark = pytest.mark.db


def test_entries_can_be_created_and_listed(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.post(
        "/api/v1/entries",
        headers=auth_headers,
        json={
            "source_type": "inbox",
            "raw_text": "I think dairy may be making my skin worse.",
            "metadata": {"mood": "uncertain"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["raw_text"] == "I think dairy may be making my skin worse."
    assert body["metadata"] == {"mood": "uncertain"}

    list_response = db_client.get("/api/v1/entries?source_type=inbox", headers=auth_headers)
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == body["id"]


def test_context_section_create_update_revisions_and_evidence(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    entry = db_client.post(
        "/api/v1/entries",
        headers=auth_headers,
        json={"source_type": "daily_review", "raw_text": "Back pain was worse after skipping rehab."},
    ).json()

    create_response = db_client.post(
        "/api/v1/context-sections",
        headers=auth_headers,
        json={
            "title": "Health",
            "section_type": "health",
            "body": "Back rehab seems important for pain stability.",
            "confidence_level": "low",
            "evidence_entry_ids": [entry["id"]],
        },
    )

    assert create_response.status_code == 201
    section = create_response.json()
    assert section["title"] == "Health"

    update_response = db_client.patch(
        f"/api/v1/context-sections/{section['id']}",
        headers=auth_headers,
        json={
            "body": "Back rehab seems important for pain stability. Misses may correlate with worse pain.",
            "confidence_level": "medium",
            "change_reason": "Daily review added more detail.",
            "evidence_entry_ids": [entry["id"]],
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["confidence_level"] == "medium"

    revisions = db_client.get(f"/api/v1/context-sections/{section['id']}/revisions", headers=auth_headers).json()
    assert [revision["revision_number"] for revision in revisions] == [2, 1]
    assert revisions[0]["change_reason"] == "Daily review added more detail."

    evidence = db_client.get(f"/api/v1/context-sections/{section['id']}/evidence", headers=auth_headers).json()
    assert {link["entry_id"] for link in evidence} == {entry["id"]}


def test_context_section_rejects_other_users_entry(
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
    other_entry = db_client.post(
        "/api/v1/entries",
        headers=other_headers,
        json={"source_type": "inbox", "raw_text": "Private note"},
    ).json()

    response = db_client.post(
        "/api/v1/context-sections",
        headers=auth_headers,
        json={
            "title": "Other evidence",
            "section_type": "custom",
            "body": "Should not link.",
            "evidence_entry_ids": [other_entry["id"]],
        },
    )

    assert response.status_code == 422
