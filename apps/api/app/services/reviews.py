from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.daily_plan import DailyPlan, DailyPlanItem
from app.models.daily_review import DailyReview
from app.models.enums import PlanItemStatus, TaskStatus
from app.models.task import Task, TaskCompletionEvent
from app.models.user import LearnedCapabilityProfile
from app.schemas.review import DailyReviewPromptItem, DailyReviewSubmit


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


def submit_daily_review(db: Session, *, user_id: UUID, review_date: date, payload: DailyReviewSubmit) -> DailyReview:
    prompts = [prompt.model_dump(mode="json") for prompt in build_daily_review_prompts(db, user_id=user_id, review_date=review_date)]
    review = db.scalar(select(DailyReview).where(DailyReview.user_id == user_id, DailyReview.review_date == review_date))
    if review is None:
        review = DailyReview(user_id=user_id, review_date=review_date)
        db.add(review)

    review.prompts = prompts
    review.responses = payload.responses
    review.energy_level = payload.energy_level
    review.load_fit = payload.load_fit
    review.mood = payload.mood
    review.ai_summary = None

    for adjustment in payload.task_adjustments:
        task = db.get(Task, adjustment.task_id)
        if task is None or task.user_id != user_id:
            continue
        if adjustment.target_date:
            start = datetime.combine(adjustment.target_date, time(hour=9), tzinfo=UTC)
            task.do_window_start = start
            task.do_window_end = start + timedelta(hours=2)
        if adjustment.note:
            task.notes = f"{task.notes}\n{adjustment.note}" if task.notes else adjustment.note

    _update_learned_capability(db, user_id=user_id, review_date=review_date)
    db.flush()
    return review


def _update_learned_capability(db: Session, *, user_id: UUID, review_date: date) -> None:
    learned = db.get(LearnedCapabilityProfile, user_id)
    if learned is None:
        learned = LearnedCapabilityProfile(user_id=user_id)
        db.add(learned)
        db.flush()

    plan = db.scalar(select(DailyPlan).where(DailyPlan.user_id == user_id, DailyPlan.plan_date == review_date))
    if plan is None:
        return

    items = db.scalars(select(DailyPlanItem).where(DailyPlanItem.daily_plan_id == plan.id)).all()
    actionable = [item for item in items if not item.is_optional]
    if not actionable:
        return

    completed = [
        item
        for item in actionable
        if item.status in {PlanItemStatus.completed, PlanItemStatus.partial}
        or (
            item.task_id
            and db.get(Task, item.task_id)
            and db.get(Task, item.task_id).status == TaskStatus.completed
        )
    ]
    observed_rate = Decimal(len(completed)) / Decimal(len(actionable))
    previous = Decimal(learned.plan_completion_rate_14d or 0)
    learned.plan_completion_rate_14d = (previous * Decimal("0.8")) + (observed_rate * Decimal("0.2"))
    learned.confidence_score = min(Decimal("1.0"), Decimal(learned.confidence_score or 0) + Decimal("0.05"))
