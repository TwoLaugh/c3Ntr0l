import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import LearnedCapabilityProfile, User


pytestmark = pytest.mark.db


def test_planner_limits_backlog_to_buffered_capacity(
    db_client: TestClient,
    db_session: Session,
    auth_headers: dict[str, str],
    user: User,
) -> None:
    learned = db_session.get(LearnedCapabilityProfile, user.id)
    learned.weekday_focus_minutes_typical = 120
    db_session.commit()

    for index in range(4):
        db_client.post(
            "/api/v1/tasks",
            headers=auth_headers,
            json={"title": f"Backlog {index}", "effort_estimate_minutes": 60},
        )

    plan = db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers).json()

    assert plan["capacity_snapshot"]["base_minutes"] == 120
    assert plan["capacity_snapshot"]["target_minutes"] == 96
    assert len(plan["items"]) == 1


def test_planner_prioritizes_due_and_high_priority_tasks(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    db_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"title": "Normal backlog", "effort_estimate_minutes": 60},
    )
    urgent = db_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Important deadline",
            "priority": "urgent",
            "due_at": "2026-06-01T17:00:00Z",
            "effort_estimate_minutes": 60,
        },
    ).json()

    plan = db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers).json()

    assert plan["items"][0]["task_id"] == urgent["id"]
    assert plan["items"][0]["reason_selected"] == "High-priority task selected within capacity"
