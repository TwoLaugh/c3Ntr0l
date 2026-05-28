from datetime import UTC, date, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.daily_plan import DailyPlan
from app.models.user import User
from app.models.weekly_plan import WeeklyPlan
from app.schemas.weekly_plan import WeeklyPlanRead, WeeklyPlanUpdate
from app.api.v1.routes.today import _plan_read
from app.services.daily_plans import regenerate_daily_plan
from app.services.weekly_plans import accept_weekly_plan, generate_weekly_plan, get_or_create_weekly_plan

router = APIRouter()


@router.get("/current", response_model=WeeklyPlanRead)
def get_current_weekly_plan(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    target_date: Annotated[date | None, Query()] = None,
) -> WeeklyPlanRead:
    plan = get_or_create_weekly_plan(db, user_id=current_user.id, target_date=target_date or datetime.now(UTC).date())
    db.commit()
    db.refresh(plan)
    return _weekly_plan_read(db, plan)


@router.post("/generate", response_model=WeeklyPlanRead)
def generate_current_weekly_plan(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    target_date: Annotated[date | None, Query()] = None,
) -> WeeklyPlanRead:
    plan = generate_weekly_plan(db, user_id=current_user.id, target_date=target_date or datetime.now(UTC).date())
    db.commit()
    db.refresh(plan)
    return _weekly_plan_read(db, plan)


@router.post("/{weekly_plan_id}/accept", response_model=WeeklyPlanRead)
def accept_plan(
    weekly_plan_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> WeeklyPlanRead:
    plan = _get_owned_weekly_plan(db, current_user, weekly_plan_id)
    accept_weekly_plan(db, plan)
    db.commit()
    db.refresh(plan)
    return _weekly_plan_read(db, plan)


@router.post("/{weekly_plan_id}/regenerate-day", response_model=WeeklyPlanRead)
def regenerate_day(
    weekly_plan_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    plan_date: Annotated[date, Query()],
) -> WeeklyPlanRead:
    plan = _get_owned_weekly_plan(db, current_user, weekly_plan_id)
    if not plan.week_start_date <= plan_date <= plan.week_start_date + timedelta(days=6):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Day is outside weekly plan")
    daily_plan = regenerate_daily_plan(db, user_id=current_user.id, plan_date=plan_date)
    daily_plan.weekly_plan_id = plan.id
    db.commit()
    db.refresh(plan)
    return _weekly_plan_read(db, plan)


@router.patch("/{weekly_plan_id}", response_model=WeeklyPlanRead)
def update_weekly_plan(
    weekly_plan_id: UUID,
    payload: WeeklyPlanUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> WeeklyPlanRead:
    plan = _get_owned_weekly_plan(db, current_user, weekly_plan_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return _weekly_plan_read(db, plan)


def _get_owned_weekly_plan(db: Session, current_user: User, weekly_plan_id: UUID) -> WeeklyPlan:
    plan = db.get(WeeklyPlan, weekly_plan_id)
    if plan is None or plan.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weekly plan not found")
    return plan


def _weekly_plan_read(db: Session, plan: WeeklyPlan) -> WeeklyPlanRead:
    daily_plans = db.scalars(
        select(DailyPlan).where(DailyPlan.weekly_plan_id == plan.id).order_by(DailyPlan.plan_date)
    ).all()
    return WeeklyPlanRead(
        id=plan.id,
        week_start_date=plan.week_start_date,
        generated_at=plan.generated_at,
        summary=plan.summary,
        focus_notes=plan.focus_notes,
        capacity_snapshot=plan.capacity_snapshot,
        status=plan.status,
        accepted_at=plan.accepted_at,
        daily_plans=[_plan_read(db, daily_plan) for daily_plan in daily_plans],
    )
