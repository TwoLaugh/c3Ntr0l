from uuid import UUID

from openai import OpenAI
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.context_section import ContextEvidenceLink, ContextSection, ContextSectionRevision
from app.models.entry import Entry
from app.models.enums import (
    AIChangeLevel,
    ConfidenceLevel,
    ContextRevisionSource,
    ContextSectionType,
    ContextStatus,
    SourceType,
)
from app.models.user import User
from app.schemas.context_distillation import ContextDistillationResult, ContextSectionDistillationUpdate
from app.services.ai_actions import log_action
from app.services.context_index import select_relevant_context


def distill_entry_to_context(
    db: Session,
    *,
    settings: Settings,
    user: User,
    entry: Entry,
) -> tuple[str | None, list[ContextSection]]:
    if settings.openai_api_key:
        result = _distill_with_openai(db, settings=settings, user=user, entry=entry)
    else:
        result = _deterministic_distillation(entry)

    sections = [_apply_update(db, user=user, entry=entry, update=update) for update in result.section_updates]
    return result.message, sections


def _distill_with_openai(db: Session, *, settings: Settings, user: User, entry: Entry) -> ContextDistillationResult:
    selection = select_relevant_context(db, user_id=user.id, raw_text=entry.raw_text)
    sections = []
    if selection.context_section_ids:
        sections = list(
            db.scalars(
                select(ContextSection).where(
                    ContextSection.user_id == user.id,
                    ContextSection.id.in_(selection.context_section_ids),
                    ContextSection.status == ContextStatus.active,
                )
            ).all()
        )

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.parse(
        model=settings.openai_model,
        text_format=ContextDistillationResult,
        instructions=_instructions(),
        input=_context(entry, sections, selection.reason),
    )
    return response.output_parsed


def _instructions() -> str:
    return (
        "Distill the raw entry into inspectable life context. "
        "Update only context that is relevant. Preserve nuance and avoid overclaiming. "
        "One-off observations should usually be low confidence. "
        "Return complete replacement body text for any updated section. "
        "Create a new section only when no existing section fits. "
        "Use change_level='confirm' only for major rewrites or sensitive claims; otherwise use 'report'."
    )


def _context(entry: Entry, sections: list[ContextSection], selection_reason: str) -> str:
    section_payload = [
        {
            "id": str(section.id),
            "title": section.title,
            "section_type": section.section_type.value,
            "summary": section.summary,
            "body": section.body,
            "structured_facts": section.structured_facts,
            "confidence_level": section.confidence_level.value,
            "confidence_notes": section.confidence_notes,
        }
        for section in sections
    ]
    return "\n".join(
        [
            f"Entry id: {entry.id}",
            f"Entry source: {entry.source_type.value}",
            f"Entry text: {entry.raw_text}",
            f"Context selection reason: {selection_reason}",
            f"Relevant existing sections: {section_payload}",
        ]
    )


def _deterministic_distillation(entry: Entry) -> ContextDistillationResult:
    title, section_type = _default_section(entry.raw_text)
    return ContextDistillationResult(
        message="Stored as low-confidence context.",
        section_updates=[
            ContextSectionDistillationUpdate(
                title=title,
                section_type=section_type,
                summary=f"Notes related to {title.lower()}.",
                body=f"Low-confidence note from entry: {entry.raw_text}",
                structured_facts={"raw_observations": [entry.raw_text]},
                confidence_level=ConfidenceLevel.low,
                confidence_notes="Created from a single entry without AI distillation.",
                change_reason="Entry stored as low-confidence context fallback.",
                change_level=AIChangeLevel.report,
            )
        ],
    )


def _default_section(raw_text: str) -> tuple[str, ContextSectionType]:
    lowered = raw_text.lower()
    if any(keyword in lowered for keyword in ["health", "back", "skin", "sleep", "rehab", "pain"]):
        return "Health", ContextSectionType.health
    if any(keyword in lowered for keyword in ["house", "home", "renovation", "clean", "maintenance"]):
        return "Home", ContextSectionType.home
    if any(keyword in lowered for keyword in ["work", "job", "bug", "promotion"]):
        return "Work", ContextSectionType.work
    return "General life overview", ContextSectionType.general


def _apply_update(
    db: Session,
    *,
    user: User,
    entry: Entry,
    update: ContextSectionDistillationUpdate,
) -> ContextSection:
    section = _find_target_section(db, user_id=user.id, update=update)
    before_state = None
    action_type = "create_context_section"

    if section is None:
        section = ContextSection(
            user_id=user.id,
            title=update.title,
            section_type=update.section_type,
            summary=update.summary,
            body=update.body,
            structured_facts=update.structured_facts,
            confidence_level=update.confidence_level,
            confidence_notes=update.confidence_notes,
            created_by=ContextRevisionSource.ai,
            updated_by=ContextRevisionSource.ai,
        )
        db.add(section)
        db.flush()
    else:
        action_type = "update_context_section"
        before_state = _section_state(section)
        section.title = update.title
        section.section_type = update.section_type
        section.summary = update.summary
        section.body = update.body
        section.structured_facts = update.structured_facts
        section.confidence_level = update.confidence_level
        section.confidence_notes = update.confidence_notes
        section.updated_by = ContextRevisionSource.ai
        db.flush()

    revision = _create_revision(db, section=section, update=update)
    db.flush()
    db.add(
        ContextEvidenceLink(
            user_id=user.id,
            context_section_id=section.id,
            context_section_revision_id=revision.id,
            entry_id=entry.id,
            relevance=update.confidence_level,
            evidence_note=update.change_reason,
        )
    )
    log_action(
        db,
        user_id=user.id,
        source_type=SourceType.ai,
        source_id=entry.id,
        action_type=action_type,
        target_type="context_section",
        target_id=section.id,
        before_state=before_state,
        after_state=_section_state(section),
        reason=update.change_reason,
    )
    return section


def _find_target_section(
    db: Session,
    *,
    user_id: UUID,
    update: ContextSectionDistillationUpdate,
) -> ContextSection | None:
    if update.target_section_id:
        section = db.get(ContextSection, update.target_section_id)
        if section is not None and section.user_id == user_id and section.status == ContextStatus.active:
            return section
    return db.scalar(
        select(ContextSection).where(
            ContextSection.user_id == user_id,
            ContextSection.title == update.title,
            ContextSection.status == ContextStatus.active,
        )
    )


def _create_revision(
    db: Session,
    *,
    section: ContextSection,
    update: ContextSectionDistillationUpdate,
) -> ContextSectionRevision:
    revision_number = int(
        db.scalar(
            select(func.coalesce(func.max(ContextSectionRevision.revision_number), 0)).where(
                ContextSectionRevision.context_section_id == section.id
            )
        )
        or 0
    ) + 1
    revision = ContextSectionRevision(
        user_id=section.user_id,
        context_section_id=section.id,
        revision_number=revision_number,
        title_snapshot=section.title,
        summary_snapshot=section.summary,
        body_snapshot=section.body,
        structured_facts_snapshot=section.structured_facts,
        confidence_level_snapshot=section.confidence_level,
        confidence_notes_snapshot=section.confidence_notes,
        change_reason=update.change_reason,
        changed_by=ContextRevisionSource.ai,
        change_level=update.change_level,
    )
    db.add(revision)
    return revision


def _section_state(section: ContextSection) -> dict:
    return {
        "id": section.id,
        "title": section.title,
        "section_type": section.section_type,
        "summary": section.summary,
        "body": section.body,
        "structured_facts": section.structured_facts,
        "confidence_level": section.confidence_level,
        "confidence_notes": section.confidence_notes,
    }
