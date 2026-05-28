from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models.daily_review import DailyReview
from app.models.user import User
from app.schemas.review import DailyReviewPromptRead, DailyReviewRead, DailyReviewSubmit
from app.services.reviews import build_daily_review_prompts, submit_daily_review
from app.services.openai_review import interpret_review_with_openai

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


@router.post("/daily/{review_date}", response_model=DailyReviewRead)
def submit_review(
    review_date: date,
    payload: DailyReviewSubmit,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DailyReview:
    interpretation = None
    if settings.openai_api_key and payload.responses:
        interpretation = interpret_review_with_openai(
            db,
            settings=settings,
            user=current_user,
            review_date=review_date,
            responses=payload.responses,
        )
    review = submit_daily_review(db, user=current_user, review_date=review_date, payload=payload, interpretation=interpretation)
    db.commit()
    db.refresh(review)
    return review


@router.get("/daily/{review_date}", response_model=DailyReviewRead)
def get_review(
    review_date: date,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DailyReview:
    review = db.scalar(select(DailyReview).where(DailyReview.user_id == current_user.id, DailyReview.review_date == review_date))
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Daily review not found")
    return review
