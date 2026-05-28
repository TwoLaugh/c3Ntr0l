import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.db


def test_task_archive_creates_reversible_action_and_undoes(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    task = db_client.post("/api/v1/tasks", headers=auth_headers, json={"title": "Maybe message Will"}).json()

    archived = db_client.post(f"/api/v1/tasks/{task['id']}/archive", headers=auth_headers)
    assert archived.status_code == 200

    actions = db_client.get("/api/v1/ai-actions", headers=auth_headers)
    assert actions.status_code == 200
    assert len(actions.json()) == 1
    action = actions.json()[0]
    assert action["action_type"] == "archive_task"
    assert action["reversible"] is True
    assert action["before_state"]["status"] == "active"
    assert action["after_state"]["status"] == "archived"

    undo = db_client.post(f"/api/v1/ai-actions/{action['id']}/undo", headers=auth_headers)
    assert undo.status_code == 200
    assert undo.json()["undone"] is True

    restored = db_client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers)
    assert restored.json()["status"] == "active"
    assert restored.json()["archived_at"] is None


def test_ai_action_ownership_is_enforced(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = db_client.get("/api/v1/ai-actions/00000000-0000-0000-0000-000000000000", headers=auth_headers)

    assert response.status_code == 404
