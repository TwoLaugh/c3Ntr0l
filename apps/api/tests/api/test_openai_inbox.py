from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.schemas.inbox_intent import InboxIntent, InboxParseResult


pytestmark = pytest.mark.db


def test_ai_inbox_parse_can_create_task(
    db_client: TestClient,
    auth_headers: dict[str, str],
    test_settings: Settings,
) -> None:
    test_settings.openai_api_key = "test-openai-key"
    parsed = InboxParseResult(
        confirmation="Added pressure washing.",
        intents=[InboxIntent(intent_type="create_task", title="Pressure wash paths", priority="high")],
    )

    with patch("app.services.inbox.parse_inbox_with_openai", return_value=parsed):
        response = db_client.post(
            "/api/v1/inbox/messages",
            headers=auth_headers,
            json={"raw_text": "Need to pressure wash paths this weekend"},
        )

    assert response.status_code == 201
    assert response.json()["processing_status"] == "processed"
    task_id = response.json()["actions"][0]["target_id"]
    task = db_client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers).json()
    assert task["title"] == "Pressure wash paths"
    assert task["priority"] == "high"

    today = db_client.get("/api/v1/today", headers=auth_headers).json()
    assert any(item["task_id"] == task_id for item in today["items"])


def test_ai_inbox_parse_can_create_routine(
    db_client: TestClient,
    auth_headers: dict[str, str],
    test_settings: Settings,
) -> None:
    test_settings.openai_api_key = "test-openai-key"
    parsed = InboxParseResult(
        intents=[
            InboxIntent(
                intent_type="create_routine",
                title="Back rehab",
                recurrence_rule="FREQ=DAILY",
                effort_estimate_minutes=10,
            )
        ],
    )

    with patch("app.services.inbox.parse_inbox_with_openai", return_value=parsed):
        response = db_client.post("/api/v1/inbox/messages", headers=auth_headers, json={"raw_text": "Add back rehab daily"})

    assert response.status_code == 201
    routine_id = response.json()["actions"][0]["target_id"]
    routine = db_client.get(f"/api/v1/routines/{routine_id}", headers=auth_headers).json()
    assert routine["title"] == "Back rehab"

    today = db_client.get("/api/v1/today", headers=auth_headers).json()
    assert any(item["title_snapshot"] == "Back rehab" and item["block_type"] == "routine" for item in today["items"])


def test_ai_inbox_parse_returns_clarification(
    db_client: TestClient,
    auth_headers: dict[str, str],
    test_settings: Settings,
) -> None:
    test_settings.openai_api_key = "test-openai-key"
    parsed = InboxParseResult(clarification_question="Which Will do you mean?", intents=[])

    with patch("app.services.inbox.parse_inbox_with_openai", return_value=parsed):
        response = db_client.post("/api/v1/inbox/messages", headers=auth_headers, json={"raw_text": "Message Will"})

    assert response.status_code == 201
    assert response.json()["processing_status"] == "needs_clarification"
    assert response.json()["actions"][0]["action_type"] == "clarification"


def test_ai_inbox_parse_can_avoid_duplicate_task(
    db_client: TestClient,
    auth_headers: dict[str, str],
    test_settings: Settings,
) -> None:
    test_settings.openai_api_key = "test-openai-key"
    existing = db_client.post("/api/v1/tasks", headers=auth_headers, json={"title": "Prepare for driving test"}).json()
    parsed = InboxParseResult(
        confirmation="Already covered.",
        intents=[
            InboxIntent(
                intent_type="no_op",
                existing_task_id=existing["id"],
                no_op_reason="Already have this as an active task.",
            )
        ],
    )

    with patch("app.services.inbox.parse_inbox_with_openai", return_value=parsed):
        response = db_client.post(
            "/api/v1/inbox/messages",
            headers=auth_headers,
            json={"raw_text": "Need to prepare for driving test"},
        )

    assert response.status_code == 201
    assert response.json()["processing_status"] == "processed"
    assert response.json()["actions"][0]["action_type"] == "no_op"
    assert response.json()["actions"][0]["target_id"] == existing["id"]
