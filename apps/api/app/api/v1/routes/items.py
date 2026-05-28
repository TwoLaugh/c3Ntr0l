from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.category import Category
from app.models.context_section import ContextSection
from app.models.entry import Entry
from app.models.enums import ItemEventType, ItemStatus
from app.models.item import Item, ItemCategoryLink, ItemCompletionEvent, ItemContextLink, ItemRecurrence
from app.models.user import User
from app.schemas.item import (
    ItemCompletionEventCreate,
    ItemCompletionEventRead,
    ItemCreate,
    ItemRead,
    ItemUpdate,
)

router = APIRouter()


@router.get("", response_model=list[ItemRead])
def list_items(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: Annotated[ItemStatus | None, Query(alias="status")] = None,
    primary_category_id: UUID | None = None,
    include_archived: bool = False,
) -> list[Item]:
    query = select(Item).where(Item.user_id == current_user.id)
    if status_filter:
        query = query.where(Item.status == status_filter)
    elif not include_archived:
        query = query.where(Item.status != ItemStatus.archived)
    if primary_category_id:
        query = query.where(Item.primary_category_id == primary_category_id)
    return list(db.scalars(query.order_by(Item.created_at.desc())).all())


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Item:
    _validate_category_owner(db, current_user, payload.primary_category_id)
    _validate_entry_owner(db, current_user, payload.source_entry_id)
    _validate_contexts(db, current_user, payload.linked_context_section_ids)
    _validate_categories(db, current_user, payload.linked_category_ids)

    item = Item(
        user_id=current_user.id,
        primary_category_id=payload.primary_category_id,
        source_entry_id=payload.source_entry_id,
        title=payload.title,
        notes=payload.notes,
        item_type=payload.item_type,
        status=payload.status,
        priority=payload.priority,
        flags=payload.flags,
        due_at=payload.due_at,
        do_window_start=payload.do_window_start,
        do_window_end=payload.do_window_end,
        effort_estimate_minutes=payload.effort_estimate_minutes,
        energy_required=payload.energy_required,
        metadata_json=payload.metadata_json,
    )
    db.add(item)
    db.flush()

    if payload.recurrence:
        db.add(
            ItemRecurrence(
                user_id=current_user.id,
                item_id=item.id,
                recurrence_rule=payload.recurrence.recurrence_rule,
                preferred_time_window=payload.recurrence.preferred_time_window,
                status=payload.recurrence.status,
            )
        )
    _replace_links(db, current_user, item, payload.linked_context_section_ids, payload.linked_category_ids)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=ItemRead)
def get_item(
    item_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Item:
    return _get_owned_item(db, current_user, item_id)


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(
    item_id: UUID,
    payload: ItemUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Item:
    item = _get_owned_item(db, current_user, item_id)
    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    if "primary_category_id" in changes:
        _validate_category_owner(db, current_user, changes["primary_category_id"])
    for key, value in changes.items():
        setattr(item, key, value)
    if item.status == ItemStatus.archived and item.archived_at is None:
        item.archived_at = datetime.now(UTC)
    if item.status != ItemStatus.archived:
        item.archived_at = None
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/archive", response_model=ItemRead)
def archive_item(
    item_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Item:
    item = _get_owned_item(db, current_user, item_id)
    item.status = ItemStatus.archived
    item.archived_at = datetime.now(UTC)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/complete", response_model=ItemCompletionEventRead)
def complete_item(
    item_id: UUID,
    payload: ItemCompletionEventCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ItemCompletionEvent:
    item = _get_owned_item(db, current_user, item_id)
    item.status = ItemStatus.completed
    return _record_event(db, current_user, item, ItemEventType.complete, payload)


@router.post("/{item_id}/partial", response_model=ItemCompletionEventRead)
def partially_complete_item(
    item_id: UUID,
    payload: ItemCompletionEventCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ItemCompletionEvent:
    item = _get_owned_item(db, current_user, item_id)
    return _record_event(db, current_user, item, ItemEventType.partial, payload)


@router.post("/{item_id}/skip", response_model=ItemCompletionEventRead)
def skip_item(
    item_id: UUID,
    payload: ItemCompletionEventCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ItemCompletionEvent:
    item = _get_owned_item(db, current_user, item_id)
    return _record_event(db, current_user, item, ItemEventType.skipped, payload)


@router.post("/{item_id}/reopen", response_model=ItemCompletionEventRead)
def reopen_item(
    item_id: UUID,
    payload: ItemCompletionEventCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ItemCompletionEvent:
    item = _get_owned_item(db, current_user, item_id)
    item.status = ItemStatus.active
    item.archived_at = None
    return _record_event(db, current_user, item, ItemEventType.reopened, payload)


@router.get("/{item_id}/events", response_model=list[ItemCompletionEventRead])
def list_item_events(
    item_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ItemCompletionEvent]:
    item = _get_owned_item(db, current_user, item_id)
    return list(
        db.scalars(
            select(ItemCompletionEvent)
            .where(ItemCompletionEvent.item_id == item.id, ItemCompletionEvent.user_id == current_user.id)
            .order_by(ItemCompletionEvent.created_at.desc())
        ).all()
    )


def _record_event(
    db: Session,
    current_user: User,
    item: Item,
    event_type: ItemEventType,
    payload: ItemCompletionEventCreate,
) -> ItemCompletionEvent:
    event = ItemCompletionEvent(
        user_id=current_user.id,
        item_id=item.id,
        event_type=event_type,
        note=payload.note,
        amount_done=payload.amount_done,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _get_owned_item(db: Session, current_user: User, item_id: UUID) -> Item:
    item = db.get(Item, item_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


def _validate_category_owner(db: Session, current_user: User, category_id: UUID | None) -> None:
    if category_id is None:
        return
    category = db.get(Category, category_id)
    if category is None or category.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Category does not exist")


def _validate_entry_owner(db: Session, current_user: User, entry_id: UUID | None) -> None:
    if entry_id is None:
        return
    entry = db.get(Entry, entry_id)
    if entry is None or entry.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Entry does not exist")


def _validate_contexts(db: Session, current_user: User, context_ids: list[UUID]) -> None:
    for context_id in context_ids:
        context = db.get(ContextSection, context_id)
        if context is None or context.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Context section does not exist")


def _validate_categories(db: Session, current_user: User, category_ids: list[UUID]) -> None:
    for category_id in category_ids:
        _validate_category_owner(db, current_user, category_id)


def _replace_links(
    db: Session,
    current_user: User,
    item: Item,
    context_ids: list[UUID],
    category_ids: list[UUID],
) -> None:
    for context_id in context_ids:
        db.add(
            ItemContextLink(
                user_id=current_user.id,
                item_id=item.id,
                context_section_id=context_id,
            )
        )
    for category_id in category_ids:
        db.add(
            ItemCategoryLink(
                user_id=current_user.id,
                item_id=item.id,
                category_id=category_id,
            )
        )
