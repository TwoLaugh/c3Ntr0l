from fastapi.testclient import TestClient


def test_local_web_origin_is_allowed(client: TestClient) -> None:
    response = client.options(
        "/api/v1/auth/dev",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
