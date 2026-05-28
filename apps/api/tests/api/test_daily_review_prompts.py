import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.db


def test_daily_review_prompt_ignores_low_stakes_optional_miss(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    db_client.post("/api/v1/tasks", headers=auth_headers, json={"title": "Shower"})
    plan = db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers).json()
    item_id = plan["items"][0]["id"]
    db_client.patch(f"/api/v1/today/items/{item_id}", headers=auth_headers, json={"is_optional": True})

    prompt = db_client.get("/api/v1/reviews/daily/2026-06-01/prompt", headers=auth_headers)

    assert prompt.status_code == 200
    assert prompt.json()["prompts"] == []


def test_daily_review_prompt_surfaces_important_missed_work(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    db_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"title": "Finish work auth bug", "due_at": "2026-06-01T17:00:00Z"},
    )
    db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers)

    prompt = db_client.get("/api/v1/reviews/daily/2026-06-01/prompt", headers=auth_headers)

    assert len(prompt.json()["prompts"]) == 1
    assert prompt.json()["prompts"][0]["prompt_type"] == "missed_important"


def test_daily_review_prompt_asks_about_partial_items(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    db_client.post("/api/v1/tasks", headers=auth_headers, json={"title": "Prepare for driving test"})
    plan = db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers).json()
    item_id = plan["items"][0]["id"]
    db_client.post(f"/api/v1/today/items/{item_id}/partial", headers=auth_headers, json={"note": "Started"})

    prompt = db_client.get("/api/v1/reviews/daily/2026-06-01/prompt", headers=auth_headers)

    assert prompt.json()["prompts"][0]["prompt_type"] == "partial_follow_up"
