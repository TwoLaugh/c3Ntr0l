import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.domain import Domain
from app.models.project import Project
from app.models.user import LearnedCapabilityProfile, User, UserProfile


pytestmark = pytest.mark.db


def test_domain_crud_and_project_count(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    created = db_client.post(
        "/api/v1/domains",
        headers=auth_headers,
        json={"name": "Health Repair", "description": "Body maintenance"},
    )

    assert created.status_code == 201
    domain_id = created.json()["id"]

    updated = db_client.patch(
        f"/api/v1/domains/{domain_id}",
        headers=auth_headers,
        json={"weight": "1.5", "metadata": {"tone": "gentle"}},
    )
    assert updated.status_code == 200
    assert updated.json()["metadata"] == {"tone": "gentle"}

    project = db_client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"domain_id": domain_id, "title": "Back rehab", "desired_outcome": "Less pain"},
    )
    assert project.status_code == 201

    detail = db_client.get(f"/api/v1/domains/{domain_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["project_count"] == 1


def test_domain_ownership_is_enforced(
    db_client: TestClient,
    db_session: Session,
    auth_headers: dict[str, str],
) -> None:
    other = _create_user(db_session)
    other_domain = Domain(user_id=other.id, name="Other domain")
    db_session.add(other_domain)
    db_session.commit()

    response = db_client.get(f"/api/v1/domains/{other_domain.id}", headers=auth_headers)

    assert response.status_code == 404


def test_project_crud_archive_and_default_filter(db_client: TestClient, auth_headers: dict[str, str]) -> None:
    domain = db_client.post("/api/v1/domains", headers=auth_headers, json={"name": "Work"}).json()
    created = db_client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"domain_id": domain["id"], "title": "Ship auth", "notes": "Backend first"},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    patched = db_client.patch(f"/api/v1/projects/{project_id}", headers=auth_headers, json={"status": "paused"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "paused"

    archived = db_client.post(f"/api/v1/projects/{project_id}/archive", headers=auth_headers)
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    assert archived.json()["archived_at"] is not None

    active_list = db_client.get("/api/v1/projects", headers=auth_headers)
    assert active_list.status_code == 200
    assert active_list.json() == []

    full_list = db_client.get("/api/v1/projects?include_archived=true", headers=auth_headers)
    assert len(full_list.json()) == 1


def test_project_rejects_domain_owned_by_another_user(
    db_client: TestClient,
    db_session: Session,
    auth_headers: dict[str, str],
) -> None:
    other = _create_user(db_session)
    other_domain = Domain(user_id=other.id, name="Other")
    db_session.add(other_domain)
    db_session.commit()

    response = db_client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"domain_id": str(other_domain.id), "title": "Bad assignment"},
    )

    assert response.status_code == 422


def test_project_ownership_is_enforced(
    db_client: TestClient,
    db_session: Session,
    auth_headers: dict[str, str],
) -> None:
    other = _create_user(db_session)
    other_project = Project(user_id=other.id, title="Other project")
    db_session.add(other_project)
    db_session.commit()

    response = db_client.get(f"/api/v1/projects/{other_project.id}", headers=auth_headers)

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
