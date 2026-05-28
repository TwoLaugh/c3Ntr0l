from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.daily_plan import DailyPlan, DailyPlanItem
from app.models.user import User
from app.schemas.today import DailyPlanItemRead, DailyPlanRead, TodayItemUpdate
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
