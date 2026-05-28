import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.db


def test_complete_today_item_marks_task_complete_and_records_event(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    task = _planned_task(db_client, auth_headers)
    item = _regenerated_item(db_client, auth_headers)

    response = db_client.post(f"/api/v1/today/items/{item['id']}/complete", headers=auth_headers, json={"note": "Done"})

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert db_client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers).json()["status"] == "completed"
    events = db_client.get(f"/api/v1/tasks/{task['id']}/events", headers=auth_headers).json()
    assert events[0]["event_type"] == "complete"
    assert events[0]["note"] == "Done"


def test_partial_today_item_keeps_task_active_and_records_note(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    task = _planned_task(db_client, auth_headers, title="Prepare for driving test")
    item = _regenerated_item(db_client, auth_headers)

    response = db_client.post(
        f"/api/v1/today/items/{item['id']}/partial",
        headers=auth_headers,
        json={"amount_done": "Read one section", "note": "Need another pass"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "partial"
    assert db_client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers).json()["status"] == "active"
    events = db_client.get(f"/api/v1/tasks/{task['id']}/events", headers=auth_headers).json()
    assert events[0]["event_type"] == "partial"
    assert "Read one section" in events[0]["note"]


def test_skip_and_move_today_items_record_events(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    task = _planned_task(db_client, auth_headers, title="Maybe message Will")
    item = _regenerated_item(db_client, auth_headers)

    skipped = db_client.post(f"/api/v1/today/items/{item['id']}/skip", headers=auth_headers, json={"note": "Not today"})
    assert skipped.status_code == 200
    assert skipped.json()["status"] == "skipped"

    moved = db_client.post(
        f"/api/v1/today/items/{item['id']}/move",
        headers=auth_headers,
        json={"target_plan_date": "2026-06-02", "note": "Better tomorrow"},
    )
    assert moved.status_code == 200
    assert moved.json()["status"] == "moved"

    events = db_client.get(f"/api/v1/tasks/{task['id']}/events", headers=auth_headers).json()
    assert {event["event_type"] for event in events} == {"moved", "skipped"}


def _planned_task(db_client: TestClient, auth_headers: dict[str, str], title: str = "Finish auth bug") -> dict:
    return db_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"title": title, "due_at": "2026-06-01T17:00:00Z"},
    ).json()


def _regenerated_item(db_client: TestClient, auth_headers: dict[str, str]) -> dict:
    plan = db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers).json()
    return plan["items"][0]
