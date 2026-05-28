from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.context_section import ContextEvidenceLink, ContextSection, ContextSectionRevision
from app.models.entry import Entry
from app.models.enums import ContextStatus
from app.models.user import User
from app.schemas.context_section import (
    ContextEvidenceLinkCreate,
    ContextEvidenceLinkRead,
    ContextSectionCreate,
    ContextSectionRead,
    ContextSectionRevisionRead,
    ContextSectionUpdate,
)

router = APIRouter()


@router.get("", response_model=list[ContextSectionRead])
def list_context_sections(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    include_archived: Annotated[bool, Query()] = False,
) -> list[ContextSection]:
    query = select(ContextSection).where(ContextSection.user_id == current_user.id)
    if not include_archived:
        query = query.where(ContextSection.status != ContextStatus.archived)
    return list(db.scalars(query.order_by(ContextSection.title)).all())


@router.post("", response_model=ContextSectionRead, status_code=status.HTTP_201_CREATED)
def create_context_section(
    payload: ContextSectionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ContextSection:
    _validate_entries(db, current_user, payload.evidence_entry_ids)
    section = ContextSection(
        user_id=current_user.id,
        title=payload.title,
        section_type=payload.section_type,
        summary=payload.summary,
        body=payload.body,
        structured_facts=payload.structured_facts,
        confidence_level=payload.confidence_level,
        confidence_notes=payload.confidence_notes,
        created_by=payload.created_by,
        updated_by=payload.created_by,
        metadata_json=payload.metadata_json,
    )
    db.add(section)
    db.flush()
    revision = _create_revision(
        db,
        section,
        revision_number=1,
        changed_by=payload.created_by,
        change_reason=payload.change_reason or "Context section created",
        change_level=payload.change_level,
    )
    db.flush()
    _add_evidence_links(db, current_user, section, revision.id, payload.evidence_entry_ids)
    db.commit()
    db.refresh(section)
    return section


@router.get("/{section_id}", response_model=ContextSectionRead)
def get_context_section(
    section_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ContextSection:
    return _get_owned_section(db, current_user, section_id)


@router.patch("/{section_id}", response_model=ContextSectionRead)
def update_context_section(
    section_id: UUID,
    payload: ContextSectionUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ContextSection:
    section = _get_owned_section(db, current_user, section_id)
    _validate_entries(db, current_user, payload.evidence_entry_ids)

    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    evidence_entry_ids = changes.pop("evidence_entry_ids", [])
    change_reason = changes.pop("change_reason", None)
    change_level = changes.pop("change_level", "report")
    updated_by = changes.pop("updated_by", payload.updated_by)

    for key, value in changes.items():
        if key == "metadata_json":
            section.metadata_json = value
        else:
            setattr(section, key, value)
    section.updated_by = updated_by
    if section.status == ContextStatus.archived and section.archived_at is None:
        section.archived_at = datetime.now(UTC)
    if section.status != ContextStatus.archived:
        section.archived_at = None

    next_revision = _next_revision_number(db, section.id)
    revision = _create_revision(
        db,
        section,
        revision_number=next_revision,
        changed_by=updated_by,
        change_reason=change_reason,
        change_level=change_level,
    )
    db.flush()
    _add_evidence_links(db, current_user, section, revision.id, evidence_entry_ids)
    db.commit()
    db.refresh(section)
    return section


@router.get("/{section_id}/revisions", response_model=list[ContextSectionRevisionRead])
def list_context_section_revisions(
    section_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ContextSectionRevision]:
    section = _get_owned_section(db, current_user, section_id)
    return list(
        db.scalars(
            select(ContextSectionRevision)
            .where(ContextSectionRevision.context_section_id == section.id)
            .order_by(ContextSectionRevision.revision_number.desc())
        ).all()
    )


@router.get("/{section_id}/evidence", response_model=list[ContextEvidenceLinkRead])
def list_context_evidence(
    section_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ContextEvidenceLink]:
    section = _get_owned_section(db, current_user, section_id)
    return list(
        db.scalars(
            select(ContextEvidenceLink)
            .where(ContextEvidenceLink.context_section_id == section.id)
            .order_by(ContextEvidenceLink.created_at.desc())
        ).all()
    )


@router.post("/{section_id}/evidence", response_model=ContextEvidenceLinkRead, status_code=status.HTTP_201_CREATED)
def create_context_evidence(
    section_id: UUID,
    payload: ContextEvidenceLinkCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ContextEvidenceLink:
    section = _get_owned_section(db, current_user, section_id)
    entry = _get_owned_entry(db, current_user, payload.entry_id)
    if payload.context_section_revision_id:
        revision = db.get(ContextSectionRevision, payload.context_section_revision_id)
        if revision is None or revision.user_id != current_user.id or revision.context_section_id != section.id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Revision does not exist")
    link = ContextEvidenceLink(
        user_id=current_user.id,
        context_section_id=section.id,
        context_section_revision_id=payload.context_section_revision_id,
        entry_id=entry.id,
        relevance=payload.relevance,
        evidence_note=payload.evidence_note,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def _get_owned_section(db: Session, current_user: User, section_id: UUID) -> ContextSection:
    section = db.get(ContextSection, section_id)
    if section is None or section.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Context section not found")
    return section


def _get_owned_entry(db: Session, current_user: User, entry_id: UUID) -> Entry:
    entry = db.get(Entry, entry_id)
    if entry is None or entry.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Entry does not exist")
    return entry


def _validate_entries(db: Session, current_user: User, entry_ids: list[UUID]) -> None:
    for entry_id in entry_ids:
        _get_owned_entry(db, current_user, entry_id)


def _next_revision_number(db: Session, section_id: UUID) -> int:
    current = db.scalar(
        select(func.coalesce(func.max(ContextSectionRevision.revision_number), 0)).where(
            ContextSectionRevision.context_section_id == section_id
        )
    )
    return int(current or 0) + 1


def _create_revision(
    db: Session,
    section: ContextSection,
    *,
    revision_number: int,
    changed_by: object,
    change_reason: str | None,
    change_level: object,
) -> ContextSectionRevision:
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
        change_reason=change_reason,
        changed_by=changed_by,
        change_level=change_level,
    )
    db.add(revision)
    return revision


def _add_evidence_links(
    db: Session,
    current_user: User,
    section: ContextSection,
    revision_id: UUID,
    entry_ids: list[UUID],
) -> None:
    for entry_id in entry_ids:
        entry = _get_owned_entry(db, current_user, entry_id)
        db.add(
            ContextEvidenceLink(
                user_id=current_user.id,
                context_section_id=section.id,
                context_section_revision_id=revision_id,
                entry_id=entry.id,
                evidence_note="Linked during context section update",
            )
        )
