from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import LearnedCapabilityProfile, User, UserProfile
from app.schemas.profile import LearnedCapabilityProfileRead, UserProfileRead, UserProfileUpdate

router = APIRouter()


@router.get("", response_model=UserProfileRead)
def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserProfile:
    return _get_profile(db, current_user)


@router.patch("", response_model=UserProfileRead)
def update_profile(
    payload: UserProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserProfile:
    profile = _get_profile(db, current_user)
    changes = payload.model_dump(exclude_unset=True)

    if "timezone" in changes:
        try:
            ZoneInfo(changes["timezone"])
        except ZoneInfoNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid timezone") from exc

    for key, value in changes.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/learned-capability", response_model=LearnedCapabilityProfileRead)
def get_learned_capability(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LearnedCapabilityProfile:
    learned = db.get(LearnedCapabilityProfile, current_user.id)
    if learned is None:
        learned = LearnedCapabilityProfile(user_id=current_user.id)
        db.add(learned)
        db.commit()
        db.refresh(learned)
    return learned


def _get_profile(db: Session, current_user: User) -> UserProfile:
    profile = db.get(UserProfile, current_user.id)
    if profile is None:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile
