from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.context_section import ContextSection
from app.models.enums import CategoryStatus, ContextSectionType, ContextStatus


@dataclass(frozen=True)
class ContextIndexSelection:
    context_section_ids: list[UUID]
    category_ids: list[UUID]
    reason: str


def select_relevant_context(
    db: Session,
    *,
    user_id: UUID,
    raw_text: str,
    max_sections: int = 5,
    max_categories: int = 5,
) -> ContextIndexSelection:
    query_tokens = _tokens(raw_text)
    sections = list(
        db.scalars(
            select(ContextSection)
            .where(ContextSection.user_id == user_id, ContextSection.status == ContextStatus.active)
            .order_by(ContextSection.updated_at.desc())
        ).all()
    )
    categories = list(
        db.scalars(
            select(Category)
            .where(Category.user_id == user_id, Category.status == CategoryStatus.active)
            .order_by(Category.sort_order, Category.name)
        ).all()
    )

    scored_sections = [
        (section, _score(query_tokens, section.title, section.summary, section.body, section.section_type.value))
        for section in sections
    ]
    scored_categories = [(category, _score(query_tokens, category.name, category.description)) for category in categories]

    selected_sections = [section for section, score in scored_sections if score > 0][:max_sections]
    selected_categories = [category for category, score in scored_categories if score > 0][:max_categories]

    if not selected_sections:
        fallback_types = {
            ContextSectionType.general,
            ContextSectionType.capacity,
            ContextSectionType.planning_preference,
        }
        selected_sections = [section for section in sections if section.section_type in fallback_types][:max_sections]

    reason = "Matched text against context/category names and summaries."
    if not selected_sections and not selected_categories:
        reason = "No direct matches; no active fallback context sections exist."
    elif not [section for section, score in scored_sections if score > 0]:
        reason = "No direct context match; loaded general planning context."

    return ContextIndexSelection(
        context_section_ids=[section.id for section in selected_sections],
        category_ids=[category.id for category in selected_categories],
        reason=reason,
    )


def _score(query_tokens: set[str], *values: str | None) -> int:
    haystack = set()
    for value in values:
        haystack.update(_tokens(value or ""))
    return len(query_tokens.intersection(haystack))


def _tokens(value: str) -> set[str]:
    normalized = "".join(character.lower() if character.isalnum() else " " for character in value)
    return {token for token in normalized.split() if len(token) >= 3}
