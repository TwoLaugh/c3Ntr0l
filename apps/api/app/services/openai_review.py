from sqlalchemy import select
from sqlalchemy.orm import Session
from openai import OpenAI

from app.core.config import Settings
from app.models.daily_plan import DailyPlan, DailyPlanItem
from app.models.user import User, UserProfile
from app.schemas.review import ReviewInterpretation


def interpret_review_with_openai(
    db: Session,
    *,
    settings: Settings,
    user: User,
    review_date: str,
    responses: dict,
) -> ReviewInterpretation:
    if not settings.openai_api_key:
        return ReviewInterpretation()

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.parse(
        model=settings.openai_model,
        text_format=ReviewInterpretation,
        instructions=(
            "Interpret a daily review into safe planning adjustments. "
            "Never delete. Prefer defer_task, add_note, split_follow_up, or reduce_tomorrow_load. "
            "Keep the summary terse."
        ),
        input=_context(db, user, review_date, responses),
    )
    return response.output_parsed


def _context(db: Session, user: User, review_date: str, responses: dict) -> str:
    profile = db.get(UserProfile, user.id)
    plan = db.scalar(select(DailyPlan).where(DailyPlan.user_id == user.id, DailyPlan.plan_date == review_date))
    items = []
    if plan:
        items = db.scalars(select(DailyPlanItem).where(DailyPlanItem.daily_plan_id == plan.id)).all()
    return "\n".join(
        [
            f"User timezone: {profile.timezone if profile else 'Europe/London'}",
            f"Review date: {review_date}",
            f"Plan items: {[{'id': str(item.task_id), 'title': item.title_snapshot, 'status': item.status.value} for item in items]}",
            f"Responses: {responses}",
        ]
    )
