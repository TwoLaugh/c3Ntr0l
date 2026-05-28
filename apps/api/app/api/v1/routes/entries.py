from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entry import Entry
from app.models.enums import EntrySource
from app.models.user import User
from app.schemas.entry import EntryCreate, EntryRead

router = APIRouter()


@router.get("", response_model=list[EntryRead])
def list_entries(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    source_type: EntrySource | None = None,
    include_archived: Annotated[bool, Query()] = False,
) -> list[Entry]:
    query = select(Entry).where(Entry.user_id == current_user.id)
    if source_type:
        query = query.where(Entry.source_type == source_type)
    if not include_archived:
        query = query.where(Entry.archived_at.is_(None))
    return list(db.scalars(query.order_by(Entry.created_at.desc())).all())


@router.post("", response_model=EntryRead, status_code=status.HTTP_201_CREATED)
def create_entry(
    payload: EntryCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Entry:
    entry = Entry(user_id=current_user.id, **payload.model_dump(exclude_none=True, by_alias=False))
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=EntryRead)
def get_entry(
    entry_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Entry:
    return _get_owned_entry(db, current_user, entry_id)


def _get_owned_entry(db: Session, current_user: User, entry_id: UUID) -> Entry:
    entry = db.get(Entry, entry_id)
    if entry is None or entry.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry
