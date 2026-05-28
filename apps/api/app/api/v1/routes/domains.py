from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.domain import Domain
from app.models.project import Project
from app.models.user import User
from app.schemas.domain import DomainCreate, DomainRead, DomainUpdate

router = APIRouter()


@router.get("", response_model=list[DomainRead])
def list_domains(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[DomainRead]:
    project_counts = (
        select(Project.domain_id, func.count(Project.id).label("project_count"))
        .where(Project.user_id == current_user.id, Project.status != "archived")
        .group_by(Project.domain_id)
        .subquery()
    )
    rows = db.execute(
        select(Domain, func.coalesce(project_counts.c.project_count, 0))
        .outerjoin(project_counts, Domain.id == project_counts.c.domain_id)
        .where(Domain.user_id == current_user.id)
        .order_by(Domain.name)
    ).all()
    return [_domain_read(domain, project_count) for domain, project_count in rows]


@router.post("", response_model=DomainRead, status_code=status.HTTP_201_CREATED)
def create_domain(
    payload: DomainCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DomainRead:
    domain = Domain(user_id=current_user.id, **payload.model_dump(by_alias=False))
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return _domain_read(domain, 0)


@router.get("/{domain_id}", response_model=DomainRead)
def get_domain(
    domain_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DomainRead:
    domain = _get_owned_domain(db, current_user, domain_id)
    project_count = db.scalar(
        select(func.count(Project.id)).where(
            Project.user_id == current_user.id,
            Project.domain_id == domain.id,
            Project.status != "archived",
        )
    )
    return _domain_read(domain, project_count or 0)


@router.patch("/{domain_id}", response_model=DomainRead)
def update_domain(
    domain_id: UUID,
    payload: DomainUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DomainRead:
    domain = _get_owned_domain(db, current_user, domain_id)
    for key, value in payload.model_dump(exclude_unset=True, by_alias=False).items():
        setattr(domain, key, value)
    db.commit()
    db.refresh(domain)
    return _domain_read(domain, 0)


def _get_owned_domain(db: Session, current_user: User, domain_id: UUID) -> Domain:
    domain = db.get(Domain, domain_id)
    if domain is None or domain.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
    return domain


def _domain_read(domain: Domain, project_count: int) -> DomainRead:
    return DomainRead(
        id=domain.id,
        name=domain.name,
        description=domain.description,
        weight=domain.weight,
        active=domain.active,
        metadata_json=domain.metadata_json,
        project_count=project_count,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
