from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.daily_plan import DailyPlan, DailyPlanItem
from app.models.enums import PlanItemStatus
from app.models.task import TaskCompletionEvent
from app.schemas.review import DailyReviewPromptItem


def build_daily_review_prompts(db: Session, *, user_id: UUID, review_date: date) -> list[DailyReviewPromptItem]:
    plan = db.scalar(select(DailyPlan).where(DailyPlan.user_id == user_id, DailyPlan.plan_date == review_date))
    if plan is None:
        return []

    items = db.scalars(
        select(DailyPlanItem).where(DailyPlanItem.daily_plan_id == plan.id).order_by(DailyPlanItem.position)
    ).all()
    prompts = []
    for item in items:
        score = _importance_score(db, user_id=user_id, item=item, review_date=review_date)
        if item.status == PlanItemStatus.partial:
            prompts.append(
                DailyReviewPromptItem(
                    plan_item_id=item.id,
                    task_id=item.task_id,
                    title=item.title_snapshot,
                    prompt_type="partial_follow_up",
                    question=f"What remains for {item.title_snapshot}?",
                    importance_score=max(score, 3),
                )
            )
        elif item.status in {PlanItemStatus.planned, PlanItemStatus.in_progress, PlanItemStatus.skipped} and score >= 3:
            prompts.append(
                DailyReviewPromptItem(
                    plan_item_id=item.id,
                    task_id=item.task_id,
                    title=item.title_snapshot,
                    prompt_type="missed_important",
                    question=f"What got in the way of {item.title_snapshot}?",
                    importance_score=score,
                )
            )
    return prompts


def _importance_score(db: Session, *, user_id: UUID, item: DailyPlanItem, review_date: date) -> int:
    score = 0
    if item.is_optional:
        score -= 2
    if item.block_type.value == "routine":
        score += 1
    if item.task_id:
        task_events_last_week = db.scalar(
            select(func.count(TaskCompletionEvent.id)).where(
                TaskCompletionEvent.user_id == user_id,
                TaskCompletionEvent.task_id == item.task_id,
                TaskCompletionEvent.created_at >= review_date - timedelta(days=7),
            )
        )
        if task_events_last_week and task_events_last_week > 1:
            score += 1
    if item.do_window_end and item.do_window_end.date() <= review_date:
        score += 2

    title = item.title_snapshot.lower()
    if any(keyword in title for keyword in ["work", "bug", "deadline", "test", "appointment", "driving"]):
        score += 3
    if any(keyword in title for keyword in ["shower", "skincare", "maybe"]):
        score -= 2

    return score
