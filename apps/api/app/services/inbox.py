from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import SourceType
from app.models.inbox_message import InboxMessage
from app.models.routine import Routine
from app.models.task import Task
from app.models.user import User
from app.schemas.inbox import InboxActionRead
from app.schemas.inbox_intent import InboxParseResult
from app.services.ai_actions import log_action
from app.services.openai_inbox import parse_inbox_with_openai


def process_inbox_message(db: Session, *, settings: Settings, user: User, message: InboxMessage) -> list[InboxActionRead]:
    user_id = user.id
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
        if settings.openai_api_key:
            parse_result = parse_inbox_with_openai(db, settings=settings, user=user, raw_text=text)
            actions = _apply_ai_parse_result(db, user_id=user_id, message=message, parse_result=parse_result)
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


def _apply_ai_parse_result(
    db: Session,
    *,
    user_id: UUID,
    message: InboxMessage,
    parse_result: InboxParseResult,
) -> list[InboxActionRead]:
    if parse_result.clarification_question:
        message.processing_status = "needs_clarification"
        message.parsed_intents = parse_result.model_dump(mode="json")
        return [InboxActionRead(action_type="clarification", message=parse_result.clarification_question)]

    actions: list[InboxActionRead] = []
    for intent in parse_result.intents:
        if intent.intent_type == "create_task" and intent.title:
            task = Task(
                user_id=user_id,
                source_inbox_message_id=message.id,
                title=intent.title,
                notes=intent.notes,
                priority=intent.priority,
                due_at=intent.due_at,
                do_window_start=intent.do_window_start,
                do_window_end=intent.do_window_end,
                effort_estimate_minutes=intent.effort_estimate_minutes,
                energy_required=intent.energy_required,
            )
            db.add(task)
            db.flush()
            log_action(
                db,
                user_id=user_id,
                source_type=SourceType.ai,
                source_id=message.id,
                action_type="create_task",
                target_type="task",
                target_id=task.id,
                after_state={"id": task.id, "title": task.title},
                reason="Created from AI inbox parse",
            )
            actions.append(
                InboxActionRead(
                    action_type="create_task",
                    target_type="task",
                    target_id=task.id,
                    message=f"Created task: {task.title}",
                )
            )
        elif intent.intent_type == "create_routine" and intent.title and intent.recurrence_rule:
            routine = Routine(
                user_id=user_id,
                title=intent.title,
                notes=intent.notes,
                recurrence_rule=intent.recurrence_rule,
                effort_estimate_minutes=intent.effort_estimate_minutes,
                energy_required=intent.energy_required,
            )
            db.add(routine)
            db.flush()
            log_action(
                db,
                user_id=user_id,
                source_type=SourceType.ai,
                source_id=message.id,
                action_type="create_routine",
                target_type="routine",
                target_id=routine.id,
                after_state={"id": routine.id, "title": routine.title},
                reason="Created from AI inbox parse",
            )
            actions.append(
                InboxActionRead(
                    action_type="create_routine",
                    target_type="routine",
                    target_id=routine.id,
                    message=f"Created routine: {routine.title}",
                )
            )

    message.processing_status = "processed" if actions else "unsupported"
    message.parsed_intents = parse_result.model_dump(mode="json")
    if not actions:
        actions.append(InboxActionRead(action_type="unsupported", message="I stored that, but could not apply it safely."))
    return actions
