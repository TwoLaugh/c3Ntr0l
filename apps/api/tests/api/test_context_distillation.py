from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.models.enums import AIChangeLevel, ConfidenceLevel, ContextSectionType
from app.schemas.context_distillation import ContextDistillationResult, ContextSectionDistillationUpdate


pytestmark = pytest.mark.db


def test_entry_distillation_without_openai_creates_low_confidence_context(
    db_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    entry = db_client.post(
        "/api/v1/entries",
        headers=auth_headers,
        json={"source_type": "inbox", "raw_text": "My back hurts after skipping rehab."},
    ).json()

    response = db_client.post(f"/api/v1/entries/{entry['id']}/distill-context", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Stored as low-confidence context."
    section = body["sections"][0]
    assert section["title"] == "Health"
    assert section["confidence_level"] == "low"

    revisions = db_client.get(f"/api/v1/context-sections/{section['id']}/revisions", headers=auth_headers).json()
    assert revisions[0]["revision_number"] == 1
    evidence = db_client.get(f"/api/v1/context-sections/{section['id']}/evidence", headers=auth_headers).json()
    assert evidence[0]["entry_id"] == entry["id"]


def test_entry_distillation_with_openai_updates_existing_section(
    db_client: TestClient,
    auth_headers: dict[str, str],
    test_settings: Settings,
) -> None:
    test_settings.openai_api_key = "test-openai-key"
    entry = db_client.post(
        "/api/v1/entries",
        headers=auth_headers,
        json={"source_type": "daily_review", "raw_text": "Skin was worse after pizza."},
    ).json()
    section = db_client.post(
        "/api/v1/context-sections",
        headers=auth_headers,
        json={"title": "Health", "section_type": "health", "body": "Existing health context."},
    ).json()
    parsed = ContextDistillationResult(
        message="Updated health context.",
        section_updates=[
            ContextSectionDistillationUpdate(
                target_section_id=section["id"],
                title="Health",
                section_type=ContextSectionType.health,
                summary="Skin and body observations.",
                body="Dairy or pizza may relate to skin flares, but evidence is early.",
                structured_facts={"emerging_patterns": [{"claim": "Pizza may worsen skin.", "confidence": "low"}]},
                confidence_level=ConfidenceLevel.low,
                confidence_notes="One review note only.",
                change_reason="Daily review mentioned worse skin after pizza.",
                change_level=AIChangeLevel.report,
            )
        ],
    )

    with patch("app.services.context_distillation._distill_with_openai", return_value=parsed):
        response = db_client.post(f"/api/v1/entries/{entry['id']}/distill-context", headers=auth_headers)

    assert response.status_code == 200
    updated = response.json()["sections"][0]
    assert updated["body"] == "Dairy or pizza may relate to skin flares, but evidence is early."

    revisions = db_client.get(f"/api/v1/context-sections/{section['id']}/revisions", headers=auth_headers).json()
    assert [revision["revision_number"] for revision in revisions] == [2, 1]
    assert revisions[0]["change_reason"] == "Daily review mentioned worse skin after pizza."

    actions = db_client.get("/api/v1/ai-actions", headers=auth_headers).json()
    assert actions[0]["action_type"] == "update_context_section"
    assert actions[0]["source_id"] == entry["id"]
