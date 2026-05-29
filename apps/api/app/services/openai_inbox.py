from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session
from openai import OpenAI

from app.core.config import Settings
from app.models.category import Category
from app.models.context_section import ContextSection
from app.models.daily_plan import DailyPlan, DailyPlanItem
from app.models.domain import Domain
from app.models.enums import CategoryStatus, ContextStatus, ItemStatus
from app.models.inbox_message import InboxMessage
from app.models.item import Item
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
        "Prefer create_item for new actionable work, reminders, notes, and routines. "
        "Use create_task/create_routine only for compatibility with clearly legacy task/routine requests. "
        "For create_item, set primary_category_name when the item belongs in a visible work bucket. "
        "Create categories only when the user clearly names a useful bucket or project-like area. "
        "Use clarification only when a safe default would be risky. "
        "Resolve relative dates from the supplied current date/time. "
        "When the user gives timing like today, tomorrow, this weekend, before Friday, or after work, "
        "set due_at or do_window_start/do_window_end instead of leaving timing only in notes. "
        "Use effort_estimate_minutes when the task size is obvious. "
        "Look at today's full plan, active items, active backlog tasks, categories, and context section names before creating anything. "
        "If the request duplicates an existing active or planned task, do not create another copy; "
        "return no_op with existing_item_id or existing_task_id when it is clearly the same thing, or ask a clarification question "
        "when the user might mean a new instance. "
        "If adding work would overload today, still create the task when useful but prefer a later do window "
        "or ask a follow-up if timing matters. "
        "Use terse confirmations."
    )


def _context(db: Session, user: User, raw_text: str) -> str:
    profile = db.get(UserProfile, user.id)
    now = datetime.now(UTC)
    domains = db.scalars(select(Domain).where(Domain.user_id == user.id, Domain.active.is_(True)).limit(20)).all()
    projects = db.scalars(select(Project).where(Project.user_id == user.id, Project.status != "archived").limit(20)).all()
    tasks = db.scalars(select(Task).where(Task.user_id == user.id, Task.status == "active").limit(30)).all()
    categories = db.scalars(
        select(Category).where(Category.user_id == user.id, Category.status == CategoryStatus.active).limit(30)
    ).all()
    items = db.scalars(select(Item).where(Item.user_id == user.id, Item.status == ItemStatus.active).limit(50)).all()
    context_sections = db.scalars(
        select(ContextSection)
        .where(ContextSection.user_id == user.id, ContextSection.status == ContextStatus.active)
        .order_by(ContextSection.updated_at.desc())
        .limit(20)
    ).all()
    today_plan = db.scalar(select(DailyPlan).where(DailyPlan.user_id == user.id, DailyPlan.plan_date == now.date()))
    today_items = []
    if today_plan:
        today_items = db.scalars(
            select(DailyPlanItem).where(DailyPlanItem.daily_plan_id == today_plan.id).order_by(DailyPlanItem.position)
        ).all()
    recent_messages = db.scalars(
        select(InboxMessage).where(InboxMessage.user_id == user.id).order_by(InboxMessage.created_at.desc()).limit(8)
    ).all()
    return "\n".join(
        [
            f"Current UTC datetime: {now.isoformat()}",
            f"Current local date: {now.date().isoformat()}",
            f"User timezone: {profile.timezone if profile else 'Europe/London'}",
            f"Domains: {[domain.name for domain in domains]}",
            f"Projects: {[project.title for project in projects]}",
            f"Categories: {_category_context(categories)}",
            f"Context sections: {_context_section_context(context_sections)}",
            f"Today's plan items: {_today_plan_context(today_items)}",
            f"Active items: {_item_context(items)}",
            f"Active backlog tasks: {_task_context(tasks)}",
            f"Recent inbox messages: {[message.raw_text for message in recent_messages]}",
            f"Inbox message: {raw_text}",
        ]
    )


def _category_context(categories: list[Category]) -> list[dict]:
    return [{"category_id": str(category.id), "name": category.name, "description": category.description} for category in categories]


def _context_section_context(sections: list[ContextSection]) -> list[dict]:
    return [
        {
            "context_section_id": str(section.id),
            "title": section.title,
            "section_type": section.section_type.value,
            "summary": section.summary,
        }
        for section in sections
    ]


def _today_plan_context(items: list[DailyPlanItem]) -> list[dict]:
    return [
        {
            "plan_item_id": str(item.id),
            "task_id": str(item.task_id) if item.task_id else None,
            "title": item.title_snapshot,
            "status": item.status.value,
            "suggested_start": item.suggested_start.isoformat() if item.suggested_start else None,
            "suggested_end": item.suggested_end.isoformat() if item.suggested_end else None,
            "reason_selected": item.reason_selected,
        }
        for item in items
    ]


def _item_context(items: list[Item]) -> list[dict]:
    return [
        {
            "item_id": str(item.id),
            "title": item.title,
            "item_type": item.item_type.value,
            "priority": item.priority.value,
            "primary_category_id": str(item.primary_category_id) if item.primary_category_id else None,
            "due_at": item.due_at.isoformat() if item.due_at else None,
            "do_window_start": item.do_window_start.isoformat() if item.do_window_start else None,
            "do_window_end": item.do_window_end.isoformat() if item.do_window_end else None,
            "effort_estimate_minutes": item.effort_estimate_minutes,
        }
        for item in items
    ]


def _task_context(tasks: list[Task]) -> list[dict]:
    return [
        {
            "task_id": str(task.id),
            "title": task.title,
            "priority": task.priority.value,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "do_window_start": task.do_window_start.isoformat() if task.do_window_start else None,
            "do_window_end": task.do_window_end.isoformat() if task.do_window_end else None,
            "effort_estimate_minutes": task.effort_estimate_minutes,
        }
        for task in tasks
    ]
