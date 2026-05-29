from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.daily_plan import DailyPlanItem
from app.models.enums import PlanBlockType, ProposedChangeStatus, ProposedChangeType, SourceType
from app.models.item import Item
from app.models.proposed_change import ProposedChange
from app.models.user import User
from app.schemas.proposed_change import (
    InsertItemTodayPayload,
    ProposedChangeCreate,
    ProposedChangeDecisionResponse,
    ProposedChangeRead,
)
from app.services.ai_actions import log_action
from app.services.daily_plans import get_or_create_daily_plan

router = APIRouter()


@router.get("", response_model=list[ProposedChangeRead])
def list_proposed_changes(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: Annotated[ProposedChangeStatus | None, Query(alias="status")] = None,
) -> list[ProposedChange]:
    query = select(ProposedChange).where(ProposedChange.user_id == current_user.id)
    if status_filter:
        query = query.where(ProposedChange.status == status_filter)
    return list(db.scalars(query.order_by(ProposedChange.created_at.desc())).all())


@router.post("", response_model=ProposedChangeRead, status_code=status.HTTP_201_CREATED)
def create_proposed_change(
    payload: ProposedChangeCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProposedChange:
    change = ProposedChange(
        user_id=current_user.id,
        source_type=payload.source_type,
        source_id=payload.source_id,
        change_type=payload.change_type,
        title=payload.title,
        rationale=payload.rationale,
        payload=payload.payload,
    )
    db.add(change)
    db.commit()
    db.refresh(change)
    return change


@router.get("/{change_id}", response_model=ProposedChangeRead)
def get_proposed_change(
    change_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProposedChange:
    return _get_owned_change(db, current_user, change_id)


@router.post("/{change_id}/accept", response_model=ProposedChangeDecisionResponse)
def accept_proposed_change(
    change_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProposedChangeDecisionResponse:
    change = _get_pending_change(db, current_user, change_id)
    plan_item = None
    if change.change_type == ProposedChangeType.insert_item_today:
        plan_item = _accept_insert_item_today(db, current_user, change)
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported proposed change type")

    change.status = ProposedChangeStatus.accepted
    change.decided_at = datetime.now(UTC)
    change.result = {"plan_item_id": str(plan_item.id) if plan_item else None}
    log_action(
        db,
        user_id=current_user.id,
        source_type=SourceType.user,
        source_id=change.id,
        action_type="accept_proposed_change",
        target_type="proposed_change",
        target_id=change.id,
        after_state={"status": change.status, "result": change.result},
        reason=change.rationale,
    )
    db.commit()
    db.refresh(change)
    if plan_item is not None:
        db.refresh(plan_item)
    return ProposedChangeDecisionResponse(
        proposed_change=change,
        plan_item=plan_item,
        message="Accepted proposed change.",
    )


@router.post("/{change_id}/reject", response_model=ProposedChangeDecisionResponse)
def reject_proposed_change(
    change_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProposedChangeDecisionResponse:
    change = _get_pending_change(db, current_user, change_id)
    change.status = ProposedChangeStatus.rejected
    change.decided_at = datetime.now(UTC)
    change.result = {"rejected": True}
    log_action(
        db,
        user_id=current_user.id,
        source_type=SourceType.user,
        source_id=change.id,
        action_type="reject_proposed_change",
        target_type="proposed_change",
        target_id=change.id,
        after_state={"status": change.status},
        reason=change.rationale,
    )
    db.commit()
    db.refresh(change)
    return ProposedChangeDecisionResponse(
        proposed_change=change,
        message="Rejected proposed change.",
    )


def _accept_insert_item_today(db: Session, current_user: User, change: ProposedChange) -> DailyPlanItem:
    payload = _insert_item_payload(change.payload)
    item = db.get(Item, payload.item_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Item does not exist")
    if payload.suggested_start and payload.suggested_end and payload.suggested_end <= payload.suggested_start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid suggested timing")

    plan_date = payload.plan_date or datetime.now(UTC).date()
    plan = get_or_create_daily_plan(db, user_id=current_user.id, plan_date=plan_date)
    existing = db.scalar(
        select(DailyPlanItem).where(DailyPlanItem.daily_plan_id == plan.id, DailyPlanItem.item_id == item.id)
    )
    if existing is not None:
        return existing

    position = payload.position if payload.position is not None else _next_position(db, plan.id)
    plan_item = DailyPlanItem(
        user_id=current_user.id,
        daily_plan_id=plan.id,
        item_id=item.id,
        title_snapshot=item.title,
        suggested_start=payload.suggested_start,
        suggested_end=payload.suggested_end,
        do_window_start=item.do_window_start,
        do_window_end=item.do_window_end,
        block_type=PlanBlockType.fixed if "fixed_time" in item.flags else PlanBlockType.suggested,
        position=position,
        is_fixed_time="fixed_time" in item.flags,
        is_optional="soft" in item.flags,
        reason_selected=f"Accepted proposal: {change.title}",
    )
    db.add(plan_item)
    db.flush()
    return plan_item


def _insert_item_payload(payload: dict) -> InsertItemTodayPayload:
    try:
        return InsertItemTodayPayload.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc


def _get_owned_change(db: Session, current_user: User, change_id: UUID) -> ProposedChange:
    change = db.get(ProposedChange, change_id)
    if change is None or change.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposed change not found")
    return change


def _get_pending_change(db: Session, current_user: User, change_id: UUID) -> ProposedChange:
    change = _get_owned_change(db, current_user, change_id)
    if change.status != ProposedChangeStatus.pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Proposed change has already been decided")
    return change


def _next_position(db: Session, daily_plan_id: UUID) -> int:
    return int(
        db.scalar(select(func.coalesce(func.max(DailyPlanItem.position), -1)).where(DailyPlanItem.daily_plan_id == daily_plan_id))
        or -1
    ) + 1
