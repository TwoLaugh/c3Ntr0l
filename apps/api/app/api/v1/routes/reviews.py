from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.review import DailyReviewPromptRead
from app.services.reviews import build_daily_review_prompts

router = APIRouter()


@router.get("/daily/{review_date}/prompt", response_model=DailyReviewPromptRead)
def get_daily_review_prompt(
    review_date: date,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DailyReviewPromptRead:
    prompts = build_daily_review_prompts(db, user_id=current_user.id, review_date=review_date)
    return DailyReviewPromptRead(
        review_date=review_date,
        prompts=prompts,
        quick_checks=["energy", "mood", "load_fit"],
    )
