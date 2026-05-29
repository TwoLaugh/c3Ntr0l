from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.daily_plan import DailyPlan, DailyPlanItem
from app.models.enums import CompletionEventType, ItemEventType, ItemStatus, PlanItemStatus, TaskStatus
from app.models.item import Item, ItemCompletionEvent
from app.models.task import Task, TaskCompletionEvent
from app.models.user import User
from app.schemas.today import (
    DailyPlanItemRead,
    DailyPlanRead,
    TodayItemMoveAction,
    TodayItemNoteAction,
    TodayItemPartialAction,
    TodayItemUpdate,
)
from app.services.daily_plans import get_or_create_daily_plan, regenerate_daily_plan

router = APIRouter()


@router.get("", response_model=DailyPlanRead)
def get_today(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    plan_date: Annotated[date | None, Query()] = None,
) -> DailyPlanRead:
    target_date = plan_date or datetime.now(UTC).date()
    plan = get_or_create_daily_plan(db, user_id=current_user.id, plan_date=target_date)
    db.commit()
    db.refresh(plan)
    return _plan_read(db, plan)


@router.post("/regenerate", response_model=DailyPlanRead)
def regenerate_today(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    plan_date: Annotated[date | None, Query()] = None,
) -> DailyPlanRead:
    target_date = plan_date or datetime.now(UTC).date()
    plan = regenerate_daily_plan(db, user_id=current_user.id, plan_date=target_date)
    db.commit()
    db.refresh(plan)
    return _plan_read(db, plan)


@router.patch("/items/{item_id}", response_model=DailyPlanItemRead)
def update_today_item(
    item_id: UUID,
    payload: TodayItemUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DailyPlanItem:
    item = db.get(DailyPlanItem, item_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Today item not found")

    changes = payload.model_dump(exclude_unset=True)
    next_start = changes.get("suggested_start", item.suggested_start)
    next_end = changes.get("suggested_end", item.suggested_end)
    if next_start and next_end and next_end <= next_start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid suggested timing")

    for key, value in changes.items():
        setattr(item, key, value)
    item.user_edited_at = datetime.now(UTC)
    db.commit()
    db.refresh(item)
    return item


@router.post("/items/{item_id}/complete", response_model=DailyPlanItemRead)
def complete_today_item(
    item_id: UUID,
    payload: TodayItemNoteAction,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DailyPlanItem:
    item = _get_owned_item(db, current_user, item_id)
    item.status = PlanItemStatus.completed
    task = _get_item_task(db, item)
    if task is not None:
        task.status = TaskStatus.completed
        _record_event(db, current_user, item, task, CompletionEventType.complete, payload.note)
    source_item = _get_source_item(db, item)
    if source_item is not None:
        source_item.status = ItemStatus.completed
        _record_item_event(db, current_user, item, source_item, ItemEventType.complete, payload.note, None)
    db.commit()
    db.refresh(item)
    return item


@router.post("/items/{item_id}/partial", response_model=DailyPlanItemRead)
def partially_complete_today_item(
    item_id: UUID,
    payload: TodayItemPartialAction,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DailyPlanItem:
    item = _get_owned_item(db, current_user, item_id)
    item.status = PlanItemStatus.completed if payload.complete_task else PlanItemStatus.partial
    note_parts = [part for part in [payload.amount_done, payload.note] if part]
    task = _get_item_task(db, item)
    if task is not None:
        if payload.complete_task:
            task.status = TaskStatus.completed
        _record_event(db, current_user, item, task, CompletionEventType.partial, "\n".join(note_parts) or None)
    source_item = _get_source_item(db, item)
    if source_item is not None:
        if payload.complete_task:
            source_item.status = ItemStatus.completed
        _record_item_event(
            db,
            current_user,
            item,
            source_item,
            ItemEventType.partial,
            payload.note,
            payload.amount_done,
        )
    db.commit()
    db.refresh(item)
    return item


@router.post("/items/{item_id}/skip", response_model=DailyPlanItemRead)
def skip_today_item(
    item_id: UUID,
    payload: TodayItemNoteAction,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DailyPlanItem:
    item = _get_owned_item(db, current_user, item_id)
    item.status = PlanItemStatus.skipped
    task = _get_item_task(db, item)
    if task is not None:
        _record_event(db, current_user, item, task, CompletionEventType.skipped, payload.note)
    source_item = _get_source_item(db, item)
    if source_item is not None:
        _record_item_event(db, current_user, item, source_item, ItemEventType.skipped, payload.note, None)
    db.commit()
    db.refresh(item)
    return item


@router.post("/items/{item_id}/move", response_model=DailyPlanItemRead)
def move_today_item(
    item_id: UUID,
    payload: TodayItemMoveAction,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DailyPlanItem:
    item = _get_owned_item(db, current_user, item_id)
    task = _get_item_task(db, item)
    if payload.target_plan_date is not None:
        target_plan = get_or_create_daily_plan(db, user_id=current_user.id, plan_date=payload.target_plan_date)
        item.daily_plan_id = target_plan.id
        item.position = _next_position(db, target_plan.id)
    if payload.suggested_start is not None:
        item.suggested_start = payload.suggested_start
    if payload.suggested_end is not None:
        item.suggested_end = payload.suggested_end
    item.status = PlanItemStatus.moved
    item.user_edited_at = datetime.now(UTC)
    if task is not None:
        _record_event(db, current_user, item, task, CompletionEventType.moved, payload.note)
    source_item = _get_source_item(db, item)
    if source_item is not None:
        _record_item_event(db, current_user, item, source_item, ItemEventType.moved, payload.note, None)
    db.commit()
    db.refresh(item)
    return item


def _plan_read(db: Session, plan: DailyPlan) -> DailyPlanRead:
    items = db.scalars(
        select(DailyPlanItem).where(DailyPlanItem.daily_plan_id == plan.id).order_by(DailyPlanItem.position)
    ).all()
    return DailyPlanRead(
        id=plan.id,
        plan_date=plan.plan_date,
        default_view_mode=plan.default_view_mode,
        capacity_snapshot=plan.capacity_snapshot,
        summary=plan.summary,
        status=plan.status,
        generated_at=plan.generated_at,
        items=list(items),
    )


def _get_owned_item(db: Session, current_user: User, item_id: UUID) -> DailyPlanItem:
    item = db.get(DailyPlanItem, item_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Today item not found")
    return item


def _get_item_task(db: Session, item: DailyPlanItem) -> Task | None:
    if item.task_id is None:
        return None
    return db.get(Task, item.task_id)


def _get_source_item(db: Session, item: DailyPlanItem) -> Item | None:
    if item.item_id is None:
        return None
    return db.get(Item, item.item_id)


def _record_event(
    db: Session,
    current_user: User,
    item: DailyPlanItem,
    task: Task,
    event_type: CompletionEventType,
    note: str | None,
) -> None:
    db.add(
        TaskCompletionEvent(
            user_id=current_user.id,
            task_id=task.id,
            plan_item_id=item.id,
            event_type=event_type,
            note=note,
        )
    )


def _record_item_event(
    db: Session,
    current_user: User,
    plan_item: DailyPlanItem,
    item: Item,
    event_type: ItemEventType,
    note: str | None,
    amount_done: str | None,
) -> None:
    db.add(
        ItemCompletionEvent(
            user_id=current_user.id,
            item_id=item.id,
            plan_instance_id=plan_item.id,
            event_type=event_type,
            note=note,
            amount_done=amount_done,
        )
    )


def _next_position(db: Session, daily_plan_id: UUID) -> int:
    positions = db.scalars(select(DailyPlanItem.position).where(DailyPlanItem.daily_plan_id == daily_plan_id)).all()
    return max(positions, default=-1) + 1
