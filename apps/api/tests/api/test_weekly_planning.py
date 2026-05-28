import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.db


def test_weekly_plan_generation_is_idempotent_and_creates_daily_shells(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    db_client.post(
        "/api/v1/routines",
        headers=auth_headers,
        json={"title": "Meditation", "recurrence_rule": "FREQ=DAILY"},
    )

    first = db_client.post("/api/v1/weekly-planning/generate?target_date=2026-06-03", headers=auth_headers)
    second = db_client.post("/api/v1/weekly-planning/generate?target_date=2026-06-03", headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["week_start_date"] == "2026-06-01"
    assert len(second.json()["daily_plans"]) == 7
    assert all(len(day["items"]) == 1 for day in second.json()["daily_plans"])


def test_weekly_plan_accept_update_and_regenerate_day(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    plan = db_client.post("/api/v1/weekly-planning/generate?target_date=2026-06-03", headers=auth_headers).json()

    updated = db_client.patch(
        f"/api/v1/weekly-planning/{plan['id']}",
        headers=auth_headers,
        json={"focus_notes": "Protect mornings"},
    )
    assert updated.status_code == 200
    assert updated.json()["focus_notes"] == "Protect mornings"

    accepted = db_client.post(f"/api/v1/weekly-planning/{plan['id']}/accept", headers=auth_headers)
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    assert accepted.json()["accepted_at"] is not None

    regenerated = db_client.post(
        f"/api/v1/weekly-planning/{plan['id']}/regenerate-day?plan_date=2026-06-04",
        headers=auth_headers,
    )
    assert regenerated.status_code == 200


def test_weekly_plan_ownership_is_enforced(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.post(
        "/api/v1/weekly-planning/00000000-0000-0000-0000-000000000000/accept",
        headers=auth_headers,
    )

    assert response.status_code == 404
