from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.domain import Domain
from app.models.routine import Routine, RoutineInstance
from app.models.task import Task
from app.models.user import User
from app.api.v1.routes.tasks import _task_read
from app.schemas.routine import (
    RoutineCreate,
    RoutineGenerateResponse,
    RoutineInstanceRead,
    RoutineRead,
    RoutineUpdate,
)
from app.services.routines import generate_routine_instances

router = APIRouter()


@router.get("", response_model=list[RoutineRead])
def list_routines(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    include_archived: bool = False,
) -> list[RoutineRead]:
    query = select(Routine).where(Routine.user_id == current_user.id)
    if not include_archived:
        query = query.where(Routine.archived_at.is_(None))
    return [_routine_read(routine) for routine in db.scalars(query.order_by(Routine.created_at.desc())).all()]


@router.post("", response_model=RoutineRead, status_code=status.HTTP_201_CREATED)
def create_routine(
    payload: RoutineCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RoutineRead:
    _validate_domain_owner(db, current_user, payload.domain_id)
    routine = Routine(user_id=current_user.id, **payload.model_dump(by_alias=False))
    db.add(routine)
    db.commit()
    db.refresh(routine)
    return _routine_read(routine)


@router.get("/{routine_id}", response_model=RoutineRead)
def get_routine(
    routine_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RoutineRead:
    return _routine_read(_get_owned_routine(db, current_user, routine_id))


@router.patch("/{routine_id}", response_model=RoutineRead)
def update_routine(
    routine_id: UUID,
    payload: RoutineUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RoutineRead:
    routine = _get_owned_routine(db, current_user, routine_id)
    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    if "domain_id" in changes:
        _validate_domain_owner(db, current_user, changes["domain_id"])
    for key, value in changes.items():
        setattr(routine, key, value)
    db.commit()
    db.refresh(routine)
    return _routine_read(routine)


@router.post("/{routine_id}/archive", response_model=RoutineRead)
def archive_routine(
    routine_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RoutineRead:
    routine = _get_owned_routine(db, current_user, routine_id)
    routine.active = False
    routine.archived_at = datetime.now(UTC)
    db.commit()
    db.refresh(routine)
    return _routine_read(routine)


@router.get("/{routine_id}/instances", response_model=list[RoutineInstanceRead])
def list_routine_instances(
    routine_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[RoutineInstanceRead]:
    routine = _get_owned_routine(db, current_user, routine_id)
    instances = db.scalars(
        select(RoutineInstance)
        .where(RoutineInstance.user_id == current_user.id, RoutineInstance.routine_id == routine.id)
        .order_by(RoutineInstance.scheduled_for_date)
    ).all()
    return [_instance_read(db, instance) for instance in instances]


@router.post("/{routine_id}/instances/generate", response_model=RoutineGenerateResponse)
def generate_instances(
    routine_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
) -> RoutineGenerateResponse:
    routine = _get_owned_routine(db, current_user, routine_id)
    try:
        instances = generate_routine_instances(
            db,
            user_id=current_user.id,
            routine=routine,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    db.commit()
    return RoutineGenerateResponse(instances=[_instance_read(db, instance) for instance in instances])


def _get_owned_routine(db: Session, current_user: User, routine_id: UUID) -> Routine:
    routine = db.get(Routine, routine_id)
    if routine is None or routine.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
    return routine


def _validate_domain_owner(db: Session, current_user: User, domain_id: UUID | None) -> None:
    if domain_id is None:
        return
    domain = db.get(Domain, domain_id)
    if domain is None or domain.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Domain does not exist")


def _routine_read(routine: Routine) -> RoutineRead:
    return RoutineRead(
        id=routine.id,
        domain_id=routine.domain_id,
        title=routine.title,
        notes=routine.notes,
        recurrence_rule=routine.recurrence_rule,
        preferred_time_window=routine.preferred_time_window,
        effort_estimate_minutes=routine.effort_estimate_minutes,
        energy_required=routine.energy_required,
        active=routine.active,
        metadata_json=routine.metadata_json,
        archived_at=routine.archived_at,
        created_at=routine.created_at,
        updated_at=routine.updated_at,
    )


def _instance_read(db: Session, instance: RoutineInstance) -> RoutineInstanceRead:
    task = db.get(Task, instance.task_id)
    return RoutineInstanceRead(
        id=instance.id,
        routine_id=instance.routine_id,
        task_id=instance.task_id,
        scheduled_for_date=instance.scheduled_for_date,
        generated_at=instance.generated_at,
        task=_task_read(task) if task else None,
    )
