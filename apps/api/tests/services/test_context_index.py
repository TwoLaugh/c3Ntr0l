import pytest
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.context_section import ContextSection
from app.models.enums import ContextSectionType
from app.models.user import User
from app.services.context_index import select_relevant_context


pytestmark = pytest.mark.db


def test_select_relevant_context_matches_health_and_category(db_session: Session, user: User) -> None:
    health = ContextSection(
        user_id=user.id,
        title="Health",
        section_type=ContextSectionType.health,
        summary="Back rehab, skin, sleep and body constraints.",
        body="",
    )
    driving = ContextSection(
        user_id=user.id,
        title="Driving",
        section_type=ContextSectionType.category,
        summary="Driving test preparation.",
        body="",
    )
    category = Category(user_id=user.id, name="Back rehab", description="Daily rehab and body repair")
    db_session.add_all([health, driving, category])
    db_session.commit()

    selection = select_relevant_context(db_session, user_id=user.id, raw_text="My back hurts after skipping rehab")

    assert health.id in selection.context_section_ids
    assert category.id in selection.category_ids
    assert driving.id not in selection.context_section_ids


def test_select_relevant_context_falls_back_to_general(db_session: Session, user: User) -> None:
    general = ContextSection(
        user_id=user.id,
        title="General life overview",
        section_type=ContextSectionType.general,
        summary="Broad planning context.",
        body="",
    )
    db_session.add(general)
    db_session.commit()

    selection = select_relevant_context(db_session, user_id=user.id, raw_text="Something totally new")

    assert selection.context_section_ids == [general.id]
    assert selection.category_ids == []
