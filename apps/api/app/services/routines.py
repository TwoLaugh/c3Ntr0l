from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.routine import Routine, RoutineInstance
from app.models.task import Task
from app.schemas.routine import parse_recurrence_rule

WEEKDAY_CODES = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def generate_routine_instances(
    db: Session,
    *,
    user_id: UUID,
    routine: Routine,
    start_date: date,
    end_date: date,
) -> list[RoutineInstance]:
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")
    if not routine.active or routine.archived_at is not None:
        return []

    instances = []
    for scheduled_date in _matching_dates(routine.recurrence_rule, start_date, end_date):
        existing = db.scalar(
            select(RoutineInstance).where(
                RoutineInstance.routine_id == routine.id,
                RoutineInstance.scheduled_for_date == scheduled_date,
            )
        )
        if existing is not None:
            instances.append(existing)
            continue

        task = Task(
            user_id=user_id,
            domain_id=routine.domain_id,
            title=routine.title,
            notes=routine.notes,
            effort_estimate_minutes=routine.effort_estimate_minutes,
            energy_required=routine.energy_required,
            metadata_json={"routine_id": str(routine.id), "scheduled_for_date": scheduled_date.isoformat()},
        )
        db.add(task)
        db.flush()
        instance = RoutineInstance(
            user_id=user_id,
            routine_id=routine.id,
            task_id=task.id,
            scheduled_for_date=scheduled_date,
        )
        db.add(instance)
        db.flush()
        instances.append(instance)

    return instances


def _matching_dates(rule: str, start_date: date, end_date: date) -> list[date]:
    parts = parse_recurrence_rule(rule)
    dates = []
    current = start_date
    weekly_days = set(parts.get("BYDAY", "").split(",")) if parts.get("BYDAY") else set(WEEKDAY_CODES)

    while current <= end_date:
        if parts["FREQ"] == "DAILY" or WEEKDAY_CODES[current.weekday()] in weekly_days:
            dates.append(current)
        current += timedelta(days=1)

    return dates
