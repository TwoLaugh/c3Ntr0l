from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import LearnedCapabilityProfile, User


pytestmark = pytest.mark.db


def test_daily_review_submission_persists_and_updates_learned_capability(
    db_client: TestClient,
    db_session: Session,
    auth_headers: dict[str, str],
    user: User,
) -> None:
    db_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"title": "Finish work task", "due_at": "2026-06-01T17:00:00Z"},
    )
    plan = db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers).json()
    item_id = plan["items"][0]["id"]
    db_client.post(f"/api/v1/today/items/{item_id}/complete", headers=auth_headers, json={})

    submitted = db_client.post(
        "/api/v1/reviews/daily/2026-06-01",
        headers=auth_headers,
        json={"responses": {"load": "fine"}, "energy_level": "medium", "load_fit": "right", "mood": "steady"},
    )

    assert submitted.status_code == 200
    assert submitted.json()["responses"]["load"] == "fine"
    assert submitted.json()["energy_level"] == "medium"

    learned = db_session.get(LearnedCapabilityProfile, user.id)
    assert learned.plan_completion_rate_14d > Decimal("0")
    assert learned.confidence_score > Decimal("0")

    fetched = db_client.get("/api/v1/reviews/daily/2026-06-01", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["load_fit"] == "right"


def test_daily_review_can_defer_task_from_response(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    task = db_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"title": "Finish work task", "due_at": "2026-06-01T17:00:00Z"},
    ).json()
    db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers)

    response = db_client.post(
        "/api/v1/reviews/daily/2026-06-01",
        headers=auth_headers,
        json={
            "responses": {"missed": "too tired after work"},
            "task_adjustments": [
                {"task_id": task["id"], "action": "defer", "target_date": "2026-06-03", "note": "Try earlier"}
            ],
        },
    )

    assert response.status_code == 200
    updated_task = db_client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers).json()
    assert updated_task["do_window_start"].startswith("2026-06-03")
    assert "Try earlier" in updated_task["notes"]
