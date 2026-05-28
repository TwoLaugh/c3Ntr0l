from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.ai_action_log import AIActionLog
from app.models.task import Task
from app.models.user import User
from app.schemas.ai_action import AIActionLogRead, UndoActionResponse

router = APIRouter()


@router.get("", response_model=list[AIActionLogRead])
def list_ai_actions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AIActionLog]:
    return list(
        db.scalars(
            select(AIActionLog).where(AIActionLog.user_id == current_user.id).order_by(AIActionLog.created_at.desc())
        ).all()
    )


@router.get("/{action_id}", response_model=AIActionLogRead)
def get_ai_action(
    action_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AIActionLog:
    return _get_owned_action(db, current_user, action_id)


@router.post("/{action_id}/undo", response_model=UndoActionResponse)
def undo_ai_action(
    action_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UndoActionResponse:
    action = _get_owned_action(db, current_user, action_id)

    if not action.reversible:
        return UndoActionResponse(action=action, undone=False, message="Action is not reversible")

    if action.action_type == "archive_task" and action.target_type == "task" and action.target_id:
        task = db.get(Task, action.target_id)
        if task is None or task.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target task not found")
        before_status = (action.before_state or {}).get("status")
        task.status = before_status or "active"
        task.archived_at = None
        action.reversible = False
        db.commit()
        db.refresh(action)
        return UndoActionResponse(action=action, undone=True, message="Task archive was undone")

    return UndoActionResponse(action=action, undone=False, message="Undo is not implemented for this action type")


def _get_owned_action(db: Session, current_user: User, action_id: UUID) -> AIActionLog:
    action = db.get(AIActionLog, action_id)
    if action is None or action.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI action not found")
    return action
