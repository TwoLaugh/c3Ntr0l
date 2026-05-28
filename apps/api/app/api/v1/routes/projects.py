from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.domain import Domain
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter()


@router.get("", response_model=list[ProjectRead])
def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    include_archived: Annotated[bool, Query()] = False,
) -> list[ProjectRead]:
    query = select(Project).where(Project.user_id == current_user.id)
    if not include_archived:
        query = query.where(Project.status != "archived")
    return [_project_read(project) for project in db.scalars(query.order_by(Project.created_at.desc())).all()]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectRead:
    _validate_domain_owner(db, current_user, payload.domain_id)
    project = Project(user_id=current_user.id, **payload.model_dump(by_alias=False))
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_read(project)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectRead:
    return _project_read(_get_owned_project(db, current_user, project_id))


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectRead:
    project = _get_owned_project(db, current_user, project_id)
    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    if "domain_id" in changes:
        _validate_domain_owner(db, current_user, changes["domain_id"])

    for key, value in changes.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return _project_read(project)


@router.post("/{project_id}/archive", response_model=ProjectRead)
def archive_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectRead:
    project = _get_owned_project(db, current_user, project_id)
    project.status = "archived"
    project.archived_at = datetime.now(UTC)
    db.commit()
    db.refresh(project)
    return _project_read(project)


def _get_owned_project(db: Session, current_user: User, project_id: UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _validate_domain_owner(db: Session, current_user: User, domain_id: UUID | None) -> None:
    if domain_id is None:
        return
    domain = db.get(Domain, domain_id)
    if domain is None or domain.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Domain does not exist")


def _project_read(project: Project) -> ProjectRead:
    return ProjectRead(
        id=project.id,
        domain_id=project.domain_id,
        title=project.title,
        desired_outcome=project.desired_outcome,
        status=project.status,
        deadline=project.deadline,
        notes=project.notes,
        metadata_json=project.metadata_json,
        archived_at=project.archived_at,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )
