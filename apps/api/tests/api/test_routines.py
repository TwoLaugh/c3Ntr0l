import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.db


def test_routine_crud_and_daily_instance_generation(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    domain = db_client.post("/api/v1/domains", headers=auth_headers, json={"name": "Foundations"}).json()
    created = db_client.post(
        "/api/v1/routines",
        headers=auth_headers,
        json={
            "domain_id": domain["id"],
            "title": "Meditation",
            "recurrence_rule": "FREQ=DAILY",
            "effort_estimate_minutes": 15,
        },
    )
    assert created.status_code == 201
    routine_id = created.json()["id"]

    patched = db_client.patch(
        f"/api/v1/routines/{routine_id}",
        headers=auth_headers,
        json={"preferred_time_window": {"start": "07:00", "end": "08:00"}},
    )
    assert patched.status_code == 200
    assert patched.json()["preferred_time_window"]["start"] == "07:00"

    generated = db_client.post(
        f"/api/v1/routines/{routine_id}/instances/generate?start_date=2026-06-01&end_date=2026-06-03",
        headers=auth_headers,
    )
    assert generated.status_code == 200
    assert len(generated.json()["instances"]) == 3
    assert generated.json()["instances"][0]["task"]["title"] == "Meditation"

    again = db_client.post(
        f"/api/v1/routines/{routine_id}/instances/generate?start_date=2026-06-01&end_date=2026-06-03",
        headers=auth_headers,
    )
    assert again.status_code == 200
    assert [item["id"] for item in again.json()["instances"]] == [item["id"] for item in generated.json()["instances"]]


def test_weekly_routine_generation_respects_byday(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    routine = db_client.post(
        "/api/v1/routines",
        headers=auth_headers,
        json={"title": "Lifting", "recurrence_rule": "FREQ=WEEKLY;BYDAY=MO,WE"},
    ).json()

    generated = db_client.post(
        f"/api/v1/routines/{routine['id']}/instances/generate?start_date=2026-06-01&end_date=2026-06-07",
        headers=auth_headers,
    )

    assert [item["scheduled_for_date"] for item in generated.json()["instances"]] == ["2026-06-01", "2026-06-03"]


def test_routine_rejects_invalid_recurrence(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.post(
        "/api/v1/routines",
        headers=auth_headers,
        json={"title": "Odd routine", "recurrence_rule": "FREQ=YEARLY"},
    )

    assert response.status_code == 422


def test_archived_routine_does_not_generate_future_instances(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    routine = db_client.post(
        "/api/v1/routines",
        headers=auth_headers,
        json={"title": "Skincare", "recurrence_rule": "FREQ=DAILY"},
    ).json()
    archived = db_client.post(f"/api/v1/routines/{routine['id']}/archive", headers=auth_headers)
    assert archived.status_code == 200
    assert archived.json()["active"] is False

    generated = db_client.post(
        f"/api/v1/routines/{routine['id']}/instances/generate?start_date=2026-06-01&end_date=2026-06-02",
        headers=auth_headers,
    )

    assert generated.status_code == 200
    assert generated.json()["instances"] == []
