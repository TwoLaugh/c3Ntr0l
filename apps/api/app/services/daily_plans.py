from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.daily_plan import DailyPlan, DailyPlanItem
from app.models.enums import PlanBlockType, PlanStatus, TaskStatus
from app.models.task import Task
from app.models.user import UserProfile


def get_or_create_daily_plan(db: Session, *, user_id: UUID, plan_date: date) -> DailyPlan:
    plan = db.scalar(select(DailyPlan).where(DailyPlan.user_id == user_id, DailyPlan.plan_date == plan_date))
    if plan is None:
        profile = db.get(UserProfile, user_id)
        plan = DailyPlan(
            user_id=user_id,
            plan_date=plan_date,
            default_view_mode=profile.preferred_day_view if profile else "timeline",
            status=PlanStatus.draft,
        )
        db.add(plan)
        db.flush()
    return plan


def regenerate_daily_plan(db: Session, *, user_id: UUID, plan_date: date) -> DailyPlan:
    plan = get_or_create_daily_plan(db, user_id=user_id, plan_date=plan_date)
    existing_items = db.scalars(select(DailyPlanItem).where(DailyPlanItem.daily_plan_id == plan.id)).all()
    existing_by_task_id = {item.task_id: item for item in existing_items if item.task_id is not None}
    next_position = max((item.position for item in existing_items), default=-1) + 1

    cursor = datetime.combine(plan_date, time(hour=9), tzinfo=UTC)
    for task in _select_tasks_for_day(db, user_id=user_id, plan_date=plan_date):
        if task.id in existing_by_task_id:
            continue

        effort = task.effort_estimate_minutes or 30
        suggested_start = task.do_window_start or cursor
        suggested_end = task.do_window_end or (suggested_start + timedelta(minutes=effort))
        item = DailyPlanItem(
            user_id=user_id,
            daily_plan_id=plan.id,
            task_id=task.id,
            title_snapshot=task.title,
            suggested_start=suggested_start,
            suggested_end=suggested_end,
            do_window_start=task.do_window_start,
            do_window_end=task.do_window_end,
            block_type=PlanBlockType.routine if task.metadata_json.get("routine_id") else PlanBlockType.suggested,
            position=next_position,
            reason_selected=_reason_selected(task, plan_date),
        )
        db.add(item)
        next_position += 1
        cursor = suggested_end + timedelta(minutes=15)

    db.flush()
    return plan


def _select_tasks_for_day(db: Session, *, user_id: UUID, plan_date: date) -> list[Task]:
    tasks = db.scalars(
        select(Task)
        .where(Task.user_id == user_id, Task.status == TaskStatus.active)
        .order_by(Task.due_at.nulls_last(), Task.created_at)
    ).all()
    selected = []
    for task in tasks:
        scheduled_for_date = task.metadata_json.get("scheduled_for_date")
        due_date = task.due_at.date() if task.due_at else None
        window_start_date = task.do_window_start.date() if task.do_window_start else None
        window_end_date = task.do_window_end.date() if task.do_window_end else None
        if scheduled_for_date == plan_date.isoformat():
            selected.append(task)
        elif due_date and due_date <= plan_date:
            selected.append(task)
        elif window_start_date and window_end_date and window_start_date <= plan_date <= window_end_date:
            selected.append(task)
        elif not (task.due_at or task.do_window_start or task.do_window_end) and len(selected) < 5:
            selected.append(task)
    return selected


def _reason_selected(task: Task, plan_date: date) -> str:
    if task.metadata_json.get("routine_id"):
        return "Routine instance due today"
    if task.due_at and task.due_at.date() <= plan_date:
        return "Task is due"
    if task.do_window_start or task.do_window_end:
        return "Task is inside its do window"
    return "Active backlog item selected for today"
