from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.daily_plan import DailyPlan, DailyPlanItem
from app.models.enums import ItemPriority, ItemStatus, ItemType, PlanBlockType, PlanStatus, TaskPriority, TaskStatus
from app.models.item import Item
from app.models.task import Task
from app.models.user import LearnedCapabilityProfile, UserProfile


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
    capacity = _capacity_snapshot(db, user_id=user_id, plan_date=plan_date)
    plan.capacity_snapshot = capacity
    existing_items = db.scalars(select(DailyPlanItem).where(DailyPlanItem.daily_plan_id == plan.id)).all()
    existing_by_task_id = {item.task_id: item for item in existing_items if item.task_id is not None}
    existing_by_item_id = {plan_item.item_id: plan_item for plan_item in existing_items if plan_item.item_id is not None}
    next_position = max((item.position for item in existing_items), default=-1) + 1

    cursor = datetime.combine(plan_date, time(hour=9), tzinfo=UTC)
    selected_minutes = 0
    for task in _select_tasks_for_day(db, user_id=user_id, plan_date=plan_date, capacity_minutes=capacity["target_minutes"]):
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
        selected_minutes += effort
        cursor = suggested_end + timedelta(minutes=15)

    remaining_minutes = max(capacity["target_minutes"] - selected_minutes, 0)
    for source_item in _select_items_for_day(
        db,
        user_id=user_id,
        plan_date=plan_date,
        capacity_minutes=remaining_minutes,
    ):
        if source_item.id in existing_by_item_id:
            continue

        effort = source_item.effort_estimate_minutes or 30
        suggested_start = source_item.do_window_start or cursor
        suggested_end = source_item.do_window_end or (suggested_start + timedelta(minutes=effort))
        item = DailyPlanItem(
            user_id=user_id,
            daily_plan_id=plan.id,
            item_id=source_item.id,
            title_snapshot=source_item.title,
            suggested_start=suggested_start,
            suggested_end=suggested_end,
            do_window_start=source_item.do_window_start,
            do_window_end=source_item.do_window_end,
            block_type=_item_block_type(source_item),
            position=next_position,
            is_fixed_time="fixed_time" in source_item.flags,
            is_optional="soft" in source_item.flags,
            reason_selected=_item_reason_selected(source_item, plan_date),
        )
        db.add(item)
        next_position += 1
        selected_minutes += effort
        cursor = suggested_end + timedelta(minutes=15)

    capacity["selected_minutes"] = selected_minutes
    db.flush()
    return plan


def _select_tasks_for_day(db: Session, *, user_id: UUID, plan_date: date, capacity_minutes: int) -> list[Task]:
    tasks = db.scalars(
        select(Task)
        .where(Task.user_id == user_id, Task.status == TaskStatus.active)
        .order_by(Task.created_at)
    ).all()
    routine_tasks = []
    candidate_tasks = []
    for task in tasks:
        scheduled_for_date = task.metadata_json.get("scheduled_for_date")
        due_date = task.due_at.date() if task.due_at else None
        window_start_date = task.do_window_start.date() if task.do_window_start else None
        window_end_date = task.do_window_end.date() if task.do_window_end else None
        if scheduled_for_date == plan_date.isoformat():
            routine_tasks.append(task)
        elif scheduled_for_date:
            continue
        elif due_date and due_date <= plan_date:
            candidate_tasks.append(task)
        elif window_start_date and window_end_date and window_start_date <= plan_date <= window_end_date:
            candidate_tasks.append(task)
        elif not (task.due_at or task.do_window_start or task.do_window_end):
            candidate_tasks.append(task)

    selected = list(routine_tasks)
    selected_minutes = sum(task.effort_estimate_minutes or 30 for task in selected)
    for task in sorted(candidate_tasks, key=lambda candidate: _task_sort_key(candidate, plan_date)):
        effort = task.effort_estimate_minutes or 30
        if selected_minutes + effort > capacity_minutes and task.priority not in {TaskPriority.urgent, TaskPriority.high}:
            continue
        selected.append(task)
        selected_minutes += effort
    return selected


def _select_items_for_day(db: Session, *, user_id: UUID, plan_date: date, capacity_minutes: int) -> list[Item]:
    items = db.scalars(
        select(Item)
        .where(Item.user_id == user_id, Item.status == ItemStatus.active)
        .order_by(Item.created_at)
    ).all()
    candidate_items = []
    for item in items:
        due_date = item.due_at.date() if item.due_at else None
        window_start_date = item.do_window_start.date() if item.do_window_start else None
        window_end_date = item.do_window_end.date() if item.do_window_end else None
        if due_date and due_date <= plan_date:
            candidate_items.append(item)
        elif window_start_date and window_end_date and window_start_date <= plan_date <= window_end_date:
            candidate_items.append(item)
        elif not (item.due_at or item.do_window_start or item.do_window_end):
            candidate_items.append(item)

    selected = []
    selected_minutes = 0
    for item in sorted(candidate_items, key=lambda candidate: _item_sort_key(candidate, plan_date)):
        effort = item.effort_estimate_minutes or 30
        if selected_minutes + effort > capacity_minutes and item.priority not in {ItemPriority.urgent, ItemPriority.high}:
            continue
        selected.append(item)
        selected_minutes += effort
    return selected


def _reason_selected(task: Task, plan_date: date) -> str:
    if task.metadata_json.get("routine_id"):
        return "Routine instance due today"
    if task.priority in {TaskPriority.urgent, TaskPriority.high}:
        return "High-priority task selected within capacity"
    if task.due_at and task.due_at.date() <= plan_date:
        return "Task is due"
    if task.do_window_start or task.do_window_end:
        return "Task is inside its do window"
    return "Active backlog item selected for today"


def _item_reason_selected(item: Item, plan_date: date) -> str:
    if item.priority in {ItemPriority.urgent, ItemPriority.high}:
        return "High-priority item selected within capacity"
    if item.due_at and item.due_at.date() <= plan_date:
        return "Item is due"
    if item.do_window_start or item.do_window_end:
        return "Item is inside its do window"
    return "Active item selected for today"


def _item_block_type(item: Item) -> PlanBlockType:
    if "fixed_time" in item.flags:
        return PlanBlockType.fixed
    if item.item_type in {ItemType.routine, ItemType.recurring_action} or "recurring" in item.flags:
        return PlanBlockType.routine
    if "soft" in item.flags:
        return PlanBlockType.floating
    return PlanBlockType.suggested


def _capacity_snapshot(db: Session, *, user_id: UUID, plan_date: date) -> dict:
    learned = db.get(LearnedCapabilityProfile, user_id)
    is_weekend = plan_date.weekday() >= 5
    raw_minutes = None
    if learned:
        raw_minutes = (
            learned.weekend_focus_minutes_typical if is_weekend else learned.weekday_focus_minutes_typical
        )
    base_minutes = int(raw_minutes or (120 if is_weekend else 180))
    target_minutes = int(base_minutes * 0.8)
    return {
        "base_minutes": base_minutes,
        "target_minutes": target_minutes,
        "buffer_ratio": 0.2,
        "selected_minutes": 0,
        "source": "learned_profile" if raw_minutes else "default",
    }


def _task_sort_key(task: Task, plan_date: date) -> tuple:
    priority_rank = {
        TaskPriority.urgent: 0,
        TaskPriority.high: 1,
        TaskPriority.normal: 2,
        TaskPriority.low: 3,
    }[task.priority]
    due_rank = 0 if task.due_at and task.due_at.date() <= plan_date else 1
    due_at = task.due_at or datetime.max.replace(tzinfo=UTC)
    return (due_rank, priority_rank, due_at, task.created_at)


def _item_sort_key(item: Item, plan_date: date) -> tuple:
    priority_rank = {
        ItemPriority.urgent: 0,
        ItemPriority.high: 1,
        ItemPriority.normal: 2,
        ItemPriority.low: 3,
    }[item.priority]
    due_rank = 0 if item.due_at and item.due_at.date() <= plan_date else 1
    due_at = item.due_at or datetime.max.replace(tzinfo=UTC)
    return (due_rank, priority_rank, due_at, item.created_at)
