from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models.inbox_message import InboxMessage
from app.models.user import User
from app.schemas.inbox import InboxActionRead, InboxMessageCreate, InboxMessageRead
from app.services.inbox import process_inbox_message

router = APIRouter()


@router.post("/messages", response_model=InboxMessageRead, status_code=status.HTTP_201_CREATED)
def create_message(
    payload: InboxMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> InboxMessageRead:
    message = InboxMessage(user_id=current_user.id, raw_text=payload.raw_text)
    db.add(message)
    db.flush()
    actions = process_inbox_message(db, settings=settings, user=current_user, message=message)
    db.commit()
    db.refresh(message)
    return _message_read(message, actions)


@router.get("/messages", response_model=list[InboxMessageRead])
def list_messages(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[InboxMessageRead]:
    messages = db.scalars(
        select(InboxMessage).where(InboxMessage.user_id == current_user.id).order_by(InboxMessage.created_at.desc())
    ).all()
    return [_message_read(message, []) for message in messages]


@router.get("/messages/{message_id}", response_model=InboxMessageRead)
def get_message(
    message_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InboxMessageRead:
    message = db.get(InboxMessage, message_id)
    if message is None or message.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inbox message not found")
    return _message_read(message, [])


def _message_read(message: InboxMessage, actions: list[InboxActionRead]) -> InboxMessageRead:
    confirmation = actions[0].message if actions else None
    return InboxMessageRead(
        id=message.id,
        raw_text=message.raw_text,
        processing_status=message.processing_status,
        parsed_intents=message.parsed_intents,
        created_at=message.created_at,
        processed_at=message.processed_at,
        confirmation=confirmation,
        actions=actions,
    )
