import pytest
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


pytestmark = pytest.mark.db


def test_initial_migration_created_core_tables(db_engine: Engine) -> None:
    inspector = inspect(db_engine)

    assert {
        "users",
        "user_profiles",
        "tasks",
        "daily_plans",
        "ai_action_logs",
        "entries",
        "context_sections",
        "context_section_revisions",
        "context_evidence_links",
    }.issubset(set(inspector.get_table_names()))
