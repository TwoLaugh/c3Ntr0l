import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.domain import Domain
from app.models.project import Project
from app.models.task import Task
from app.models.user import LearnedCapabilityProfile, User, UserProfile


pytestmark = pytest.mark.db


def test_task_crud_filters_archive_and_events(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    domain = db_client.post("/api/v1/domains", headers=auth_headers, json={"name": "Infrastructure"}).json()
    project = db_client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"domain_id": domain["id"], "title": "House reset"},
    ).json()

    created = db_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={
            "domain_id": domain["id"],
            "project_id": project["id"],
            "title": "Pressure wash paths",
            "priority": "high",
            "due_at": "2026-06-01T10:00:00Z",
            "do_window_start": "2026-05-30T09:00:00Z",
            "do_window_end": "2026-05-30T11:00:00Z",
            "metadata": {"surface": "garden"},
        },
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    patched = db_client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers,
        json={"effort_estimate_minutes": 90, "notes": "Do after breakfast"},
    )
    assert patched.status_code == 200
    assert patched.json()["effort_estimate_minutes"] == 90

    by_search = db_client.get("/api/v1/tasks?search=wash", headers=auth_headers)
    assert [task["id"] for task in by_search.json()] == [task_id]

    by_domain = db_client.get(f"/api/v1/tasks?domain_id={domain['id']}", headers=auth_headers)
    assert len(by_domain.json()) == 1

    events = db_client.get(f"/api/v1/tasks/{task_id}/events", headers=auth_headers)
    assert events.status_code == 200
    assert events.json() == []

    archived = db_client.post(f"/api/v1/tasks/{task_id}/archive", headers=auth_headers)
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"

    active_list = db_client.get("/api/v1/tasks", headers=auth_headers)
    assert active_list.json() == []

    full_list = db_client.get("/api/v1/tasks?include_archived=true", headers=auth_headers)
    assert len(full_list.json()) == 1


def test_task_rejects_invalid_do_window(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    response = db_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Bad window",
            "do_window_start": "2026-05-30T11:00:00Z",
            "do_window_end": "2026-05-30T09:00:00Z",
        },
    )

    assert response.status_code == 422


def test_task_rejects_foreign_domain_and_project(
    db_client: TestClient,
    db_session: Session,
    auth_headers: dict[str, str],
) -> None:
    other = _create_user(db_session)
    other_domain = Domain(user_id=other.id, name="Other domain")
    other_project = Project(user_id=other.id, title="Other project")
    db_session.add_all([other_domain, other_project])
    db_session.commit()

    domain_response = db_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"domain_id": str(other_domain.id), "title": "Wrong domain"},
    )
    project_response = db_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"project_id": str(other_project.id), "title": "Wrong project"},
    )

    assert domain_response.status_code == 422
    assert project_response.status_code == 422


def test_task_ownership_is_enforced(
    db_client: TestClient,
    db_session: Session,
    auth_headers: dict[str, str],
) -> None:
    other = _create_user(db_session)
    other_task = Task(user_id=other.id, title="Other task")
    db_session.add(other_task)
    db_session.commit()

    response = db_client.get(f"/api/v1/tasks/{other_task.id}", headers=auth_headers)

    assert response.status_code == 404


def _create_user(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@example.com",
        auth_provider="google",
        auth_subject=str(uuid.uuid4()),
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(UserProfile(user_id=user.id))
    db_session.add(LearnedCapabilityProfile(user_id=user.id))
    db_session.commit()
    return user
