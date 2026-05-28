from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session
from openai import OpenAI

from app.core.config import Settings
from app.models.domain import Domain
from app.models.project import Project
from app.models.task import Task
from app.models.user import User, UserProfile
from app.schemas.inbox_intent import InboxParseResult


def parse_inbox_with_openai(db: Session, *, settings: Settings, user: User, raw_text: str) -> InboxParseResult:
    if not settings.openai_api_key:
        return InboxParseResult(clarification_question="OpenAI is not configured.")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.parse(
        model=settings.openai_model,
        text_format=InboxParseResult,
        instructions=_instructions(),
        input=_context(db, user, raw_text),
    )
    return response.output_parsed


def _instructions() -> str:
    return (
        "Parse the user's inbox message into safe planning intents. "
        "Prefer creating or updating non-destructively; never delete. "
        "Use clarification only when a safe default would be risky. "
        "Resolve relative dates from the supplied current date/time. "
        "When the user gives timing like today, tomorrow, this weekend, before Friday, or after work, "
        "set due_at or do_window_start/do_window_end instead of leaving timing only in notes. "
        "Use effort_estimate_minutes when the task size is obvious. "
        "Use terse confirmations."
    )


def _context(db: Session, user: User, raw_text: str) -> str:
    profile = db.get(UserProfile, user.id)
    now = datetime.now(UTC)
    domains = db.scalars(select(Domain).where(Domain.user_id == user.id, Domain.active.is_(True)).limit(20)).all()
    projects = db.scalars(select(Project).where(Project.user_id == user.id, Project.status != "archived").limit(20)).all()
    tasks = db.scalars(select(Task).where(Task.user_id == user.id, Task.status == "active").limit(30)).all()
    return "\n".join(
        [
            f"Current UTC datetime: {now.isoformat()}",
            f"Current local date: {now.date().isoformat()}",
            f"User timezone: {profile.timezone if profile else 'Europe/London'}",
            f"Domains: {[domain.name for domain in domains]}",
            f"Projects: {[project.title for project in projects]}",
            f"Active tasks: {[task.title for task in tasks]}",
            f"Inbox message: {raw_text}",
        ]
    )
