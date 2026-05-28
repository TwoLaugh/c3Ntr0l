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
from app.models.task import Task, TaskCompletionEvent
from app.models.user import User
from app.schemas.task import TaskCompletionEventRead, TaskCreate, TaskRead, TaskUpdate

router = APIRouter()


@router.get("", response_model=list[TaskRead])
def list_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    domain_id: UUID | None = None,
    project_id: UUID | None = None,
    due_before: datetime | None = None,
    due_after: datetime | None = None,
    do_window_start_before: datetime | None = None,
    do_window_end_after: datetime | None = None,
    search: str | None = None,
    include_archived: bool = False,
) -> list[TaskRead]:
    query = select(Task).where(Task.user_id == current_user.id)

    if status_filter:
        query = query.where(Task.status == status_filter)
    elif not include_archived:
        query = query.where(Task.status != "archived")
    if domain_id:
        query = query.where(Task.domain_id == domain_id)
    if project_id:
        query = query.where(Task.project_id == project_id)
    if due_before:
        query = query.where(Task.due_at <= due_before)
    if due_after:
        query = query.where(Task.due_at >= due_after)
    if do_window_start_before:
        query = query.where(Task.do_window_start <= do_window_start_before)
    if do_window_end_after:
        query = query.where(Task.do_window_end >= do_window_end_after)
    if search:
        query = query.where(Task.title.ilike(f"%{search}%"))

    return [_task_read(task) for task in db.scalars(query.order_by(Task.created_at.desc())).all()]


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TaskRead:
    _validate_domain_owner(db, current_user, payload.domain_id)
    _validate_project_owner(db, current_user, payload.project_id)
    task = Task(user_id=current_user.id, **payload.model_dump(by_alias=False))
    db.add(task)
    db.commit()
    db.refresh(task)
    return _task_read(task)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TaskRead:
    return _task_read(_get_owned_task(db, current_user, task_id))


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TaskRead:
    task = _get_owned_task(db, current_user, task_id)
    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    if "domain_id" in changes:
        _validate_domain_owner(db, current_user, changes["domain_id"])
    if "project_id" in changes:
        _validate_project_owner(db, current_user, changes["project_id"])

    next_start = changes.get("do_window_start", task.do_window_start)
    next_end = changes.get("do_window_end", task.do_window_end)
    if next_start and next_end and next_end <= next_start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid do window")

    for key, value in changes.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return _task_read(task)


@router.post("/{task_id}/archive", response_model=TaskRead)
def archive_task(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TaskRead:
    task = _get_owned_task(db, current_user, task_id)
    task.status = "archived"
    task.archived_at = datetime.now(UTC)
    db.commit()
    db.refresh(task)
    return _task_read(task)


@router.get("/{task_id}/events", response_model=list[TaskCompletionEventRead])
def list_task_events(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TaskCompletionEvent]:
    task = _get_owned_task(db, current_user, task_id)
    return list(
        db.scalars(
            select(TaskCompletionEvent)
            .where(TaskCompletionEvent.user_id == current_user.id, TaskCompletionEvent.task_id == task.id)
            .order_by(TaskCompletionEvent.created_at.desc())
        ).all()
    )


def _get_owned_task(db: Session, current_user: User, task_id: UUID) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def _validate_domain_owner(db: Session, current_user: User, domain_id: UUID | None) -> None:
    if domain_id is None:
        return
    domain = db.get(Domain, domain_id)
    if domain is None or domain.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Domain does not exist")


def _validate_project_owner(db: Session, current_user: User, project_id: UUID | None) -> None:
    if project_id is None:
        return
    project = db.get(Project, project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project does not exist")


def _task_read(task: Task) -> TaskRead:
    return TaskRead(
        id=task.id,
        domain_id=task.domain_id,
        project_id=task.project_id,
        source_inbox_message_id=task.source_inbox_message_id,
        title=task.title,
        notes=task.notes,
        status=task.status,
        priority=task.priority,
        due_at=task.due_at,
        do_window_start=task.do_window_start,
        do_window_end=task.do_window_end,
        effort_estimate_minutes=task.effort_estimate_minutes,
        energy_required=task.energy_required,
        metadata_json=task.metadata_json,
        archived_at=task.archived_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )
