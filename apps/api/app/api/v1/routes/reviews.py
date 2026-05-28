from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.daily_review import DailyReview
from app.models.user import User
from app.schemas.review import DailyReviewPromptRead, DailyReviewRead, DailyReviewSubmit
from app.services.reviews import build_daily_review_prompts, submit_daily_review

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
) -> DailyReview:
    review = submit_daily_review(db, user_id=current_user.id, review_date=review_date, payload=payload)
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
