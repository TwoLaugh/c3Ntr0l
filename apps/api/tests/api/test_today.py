import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.db


def test_today_returns_empty_plan(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.get("/api/v1/today?plan_date=2026-06-01", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["plan_date"] == "2026-06-01"
    assert response.json()["items"] == []


def test_today_regenerate_selects_tasks_and_allows_manual_move(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    task = db_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Finish app auth bug",
            "due_at": "2026-06-01T17:00:00Z",
            "effort_estimate_minutes": 45,
        },
    ).json()

    plan = db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers)
    assert plan.status_code == 200
    assert len(plan.json()["items"]) == 1
    item = plan.json()["items"][0]
    assert item["task_id"] == task["id"]

    moved = db_client.patch(
        f"/api/v1/today/items/{item['id']}",
        headers=auth_headers,
        json={"suggested_start": "2026-06-01T13:00:00Z", "suggested_end": "2026-06-01T13:45:00Z"},
    )
    assert moved.status_code == 200
    assert moved.json()["user_edited_at"] is not None

    regenerated = db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers)
    assert len(regenerated.json()["items"]) == 1
    assert regenerated.json()["items"][0]["suggested_start"] == "2026-06-01T13:00:00Z"


def test_today_regenerate_selects_items_and_records_partial_event(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    source_item = db_client.post(
        "/api/v1/items",
        headers=auth_headers,
        json={
            "title": "Pressure wash paths",
            "priority": "high",
            "due_at": "2026-06-01T17:00:00Z",
            "effort_estimate_minutes": 45,
        },
    ).json()

    plan = db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers)

    assert plan.status_code == 200
    plan_item = plan.json()["items"][0]
    assert plan_item["item_id"] == source_item["id"]
    assert plan_item["task_id"] is None
    assert plan_item["reason_selected"] == "High-priority item selected within capacity"

    partial = db_client.post(
        f"/api/v1/today/items/{plan_item['id']}/partial",
        headers=auth_headers,
        json={"amount_done": "Half the path", "note": "Ran out of daylight."},
    )
    assert partial.status_code == 200
    assert partial.json()["status"] == "partial"

    events = db_client.get(f"/api/v1/items/{source_item['id']}/events", headers=auth_headers).json()
    assert events[0]["event_type"] == "partial"
    assert events[0]["amount_done"] == "Half the path"


def test_today_regenerate_includes_routine_generated_task(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    routine = db_client.post(
        "/api/v1/routines",
        headers=auth_headers,
        json={"title": "Back rehab", "recurrence_rule": "FREQ=DAILY"},
    ).json()
    db_client.post(
        f"/api/v1/routines/{routine['id']}/instances/generate?start_date=2026-06-01&end_date=2026-06-01",
        headers=auth_headers,
    )

    plan = db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers)

    assert len(plan.json()["items"]) == 1
    assert plan.json()["items"][0]["block_type"] == "routine"
    assert plan.json()["items"][0]["reason_selected"] == "Routine instance due today"
