from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import PlanStatus
from app.models.routine import Routine
from app.models.weekly_plan import WeeklyPlan
from app.services.daily_plans import regenerate_daily_plan
from app.services.routines import generate_routine_instances


def week_start_for(target_date: date) -> date:
    return target_date - timedelta(days=target_date.weekday())


def get_or_create_weekly_plan(db: Session, *, user_id: UUID, target_date: date) -> WeeklyPlan:
    week_start = week_start_for(target_date)
    plan = db.scalar(select(WeeklyPlan).where(WeeklyPlan.user_id == user_id, WeeklyPlan.week_start_date == week_start))
    if plan is None:
        plan = WeeklyPlan(
            user_id=user_id,
            week_start_date=week_start,
            status=PlanStatus.draft,
            summary="Generated weekly planning shell",
            capacity_snapshot={"days": 7},
        )
        db.add(plan)
        db.flush()
    return plan


def generate_weekly_plan(db: Session, *, user_id: UUID, target_date: date) -> WeeklyPlan:
    plan = get_or_create_weekly_plan(db, user_id=user_id, target_date=target_date)
    routines = db.scalars(
        select(Routine).where(Routine.user_id == user_id, Routine.active.is_(True), Routine.archived_at.is_(None))
    ).all()
    week_end = plan.week_start_date + timedelta(days=6)
    for routine in routines:
        generate_routine_instances(
            db,
            user_id=user_id,
            routine=routine,
            start_date=plan.week_start_date,
            end_date=week_end,
        )

    for offset in range(7):
        day = plan.week_start_date + timedelta(days=offset)
        daily_plan = regenerate_daily_plan(db, user_id=user_id, plan_date=day)
        daily_plan.weekly_plan_id = plan.id

    db.flush()
    return plan


def accept_weekly_plan(db: Session, plan: WeeklyPlan) -> WeeklyPlan:
    plan.status = PlanStatus.accepted
    plan.accepted_at = datetime.now(UTC)
    db.flush()
    return plan
