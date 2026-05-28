from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import SourceType
from app.models.inbox_message import InboxMessage
from app.models.routine import Routine
from app.models.task import Task
from app.schemas.inbox import InboxActionRead
from app.services.ai_actions import log_action


def process_inbox_message(db: Session, *, user_id: UUID, message: InboxMessage) -> list[InboxActionRead]:
    text = message.raw_text.strip()
    actions: list[InboxActionRead] = []

    if text.lower().startswith("task:"):
        title = text.split(":", 1)[1].strip()
        task = Task(user_id=user_id, title=title, source_inbox_message_id=message.id)
        db.add(task)
        db.flush()
        log_action(
            db,
            user_id=user_id,
            source_type=SourceType.user,
            source_id=message.id,
            action_type="create_task",
            target_type="task",
            target_id=task.id,
            after_state={"id": task.id, "title": task.title},
            reason="Created from deterministic inbox command",
        )
        actions.append(
            InboxActionRead(action_type="create_task", target_type="task", target_id=task.id, message=f"Created task: {title}")
        )
        message.processing_status = "processed"
        message.parsed_intents = {"command": "task", "title": title}
    elif text.lower().startswith("routine daily:"):
        title = text.split(":", 1)[1].strip()
        routine = Routine(user_id=user_id, title=title, recurrence_rule="FREQ=DAILY")
        db.add(routine)
        db.flush()
        log_action(
            db,
            user_id=user_id,
            source_type=SourceType.user,
            source_id=message.id,
            action_type="create_routine",
            target_type="routine",
            target_id=routine.id,
            after_state={"id": routine.id, "title": routine.title, "recurrence_rule": routine.recurrence_rule},
            reason="Created from deterministic inbox command",
        )
        actions.append(
            InboxActionRead(
                action_type="create_routine",
                target_type="routine",
                target_id=routine.id,
                message=f"Created daily routine: {title}",
            )
        )
        message.processing_status = "processed"
        message.parsed_intents = {"command": "routine_daily", "title": title}
    else:
        message.processing_status = "unsupported"
        message.parsed_intents = {"command": "unsupported"}
        actions.append(
            InboxActionRead(
                action_type="unsupported",
                message="I stored that, but deterministic parsing does not support it yet.",
            )
        )

    message.processed_at = datetime.now(UTC)
    return actions
