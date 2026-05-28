import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.db


def test_inbox_task_command_creates_task_and_logs_action(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.post("/api/v1/inbox/messages", headers=auth_headers, json={"raw_text": "task: Buy milk"})

    assert response.status_code == 201
    body = response.json()
    assert body["processing_status"] == "processed"
    assert body["actions"][0]["action_type"] == "create_task"

    task_id = body["actions"][0]["target_id"]
    task = db_client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert task.json()["title"] == "Buy milk"

    actions = db_client.get("/api/v1/ai-actions", headers=auth_headers).json()
    assert actions[0]["action_type"] == "create_task"


def test_inbox_daily_routine_command_creates_routine(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.post(
        "/api/v1/inbox/messages",
        headers=auth_headers,
        json={"raw_text": "routine daily: Back rehab"},
    )

    assert response.status_code == 201
    routine_id = response.json()["actions"][0]["target_id"]
    routine = db_client.get(f"/api/v1/routines/{routine_id}", headers=auth_headers)
    assert routine.json()["title"] == "Back rehab"
    assert routine.json()["recurrence_rule"] == "FREQ=DAILY"


def test_inbox_unsupported_input_is_stored(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.post(
        "/api/v1/inbox/messages",
        headers=auth_headers,
        json={"raw_text": "Think about driving test"},
    )

    assert response.status_code == 201
    assert response.json()["processing_status"] == "unsupported"

    messages = db_client.get("/api/v1/inbox/messages", headers=auth_headers)
    assert len(messages.json()) == 1


def test_inbox_ownership_is_enforced(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.get("/api/v1/inbox/messages/00000000-0000-0000-0000-000000000000", headers=auth_headers)

    assert response.status_code == 404
