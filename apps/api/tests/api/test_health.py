from fastapi.testclient import TestClient


def test_root_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_v1_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_me_placeholder(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["authenticated"] is False


def test_profile_placeholder(client: TestClient) -> None:
    response = client.get("/api/v1/profile")

    assert response.status_code == 200
    assert response.json()["profile"] is None
