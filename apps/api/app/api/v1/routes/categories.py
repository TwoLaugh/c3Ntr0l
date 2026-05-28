from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.category import Category
from app.models.enums import CategoryStatus
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter()


@router.get("", response_model=list[CategoryRead])
def list_categories(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    include_archived: Annotated[bool, Query()] = False,
) -> list[Category]:
    query = select(Category).where(Category.user_id == current_user.id)
    if not include_archived:
        query = query.where(Category.status != CategoryStatus.archived)
    return list(db.scalars(query.order_by(Category.sort_order, Category.name)).all())


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Category:
    category = Category(user_id=current_user.id, **payload.model_dump(by_alias=False))
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(
    category_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Category:
    return _get_owned_category(db, current_user, category_id)


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Category:
    category = _get_owned_category(db, current_user, category_id)
    for key, value in payload.model_dump(exclude_unset=True, by_alias=False).items():
        setattr(category, key, value)
    if category.status == CategoryStatus.archived and category.archived_at is None:
        category.archived_at = datetime.now(UTC)
    if category.status != CategoryStatus.archived:
        category.archived_at = None
    db.commit()
    db.refresh(category)
    return category


@router.post("/{category_id}/archive", response_model=CategoryRead)
def archive_category(
    category_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Category:
    category = _get_owned_category(db, current_user, category_id)
    category.status = CategoryStatus.archived
    category.archived_at = datetime.now(UTC)
    db.commit()
    db.refresh(category)
    return category


def _get_owned_category(db: Session, current_user: User, category_id: UUID) -> Category:
    category = db.get(Category, category_id)
    if category is None or category.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category
