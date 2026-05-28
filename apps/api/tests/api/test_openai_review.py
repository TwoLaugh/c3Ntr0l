from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.schemas.review import ReviewAdjustmentIntent, ReviewInterpretation


pytestmark = pytest.mark.db


def test_ai_review_interpreter_applies_safe_adjustment(
    db_client: TestClient,
    auth_headers: dict[str, str],
    test_settings: Settings,
) -> None:
    test_settings.openai_api_key = "test-openai-key"
    task = db_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"title": "Finish work task", "due_at": "2026-06-01T17:00:00Z"},
    ).json()
    db_client.post("/api/v1/today/regenerate?plan_date=2026-06-01", headers=auth_headers)
    interpretation = ReviewInterpretation(
        summary="Too tired after work.",
        adjustments=[
            ReviewAdjustmentIntent(
                action="defer_task",
                task_id=task["id"],
                target_date="2026-06-03",
                note="Schedule earlier in the day",
            )
        ],
    )

    with patch("app.api.v1.routes.reviews.interpret_review_with_openai", return_value=interpretation):
        response = db_client.post(
            "/api/v1/reviews/daily/2026-06-01",
            headers=auth_headers,
            json={"responses": {"missed": "too tired after work"}},
        )

    assert response.status_code == 200
    assert response.json()["ai_summary"] == "Too tired after work."
    updated_task = db_client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers).json()
    assert updated_task["do_window_start"].startswith("2026-06-03")
    assert "Schedule earlier" in updated_task["notes"]

    actions = db_client.get("/api/v1/ai-actions", headers=auth_headers).json()
    assert actions[0]["action_type"] == "defer_task"
