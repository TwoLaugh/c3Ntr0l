from enum import Enum


class TaskStatus(str, Enum):
    active = "active"
    completed = "completed"
    archived = "archived"


class TaskPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class EnergyLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class PlanStatus(str, Enum):
    draft = "draft"
    active = "active"
    accepted = "accepted"
    superseded = "superseded"
    archived = "archived"


class PlanItemStatus(str, Enum):
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"
    partial = "partial"
    skipped = "skipped"
    moved = "moved"
    archived = "archived"


class PlanBlockType(str, Enum):
    fixed = "fixed"
    suggested = "suggested"
    routine = "routine"
    floating = "floating"
    buffer = "buffer"


class CompletionEventType(str, Enum):
    complete = "complete"
    partial = "partial"
    skipped = "skipped"
    moved = "moved"
    abandoned = "abandoned"


class SourceType(str, Enum):
    user = "user"
    ai = "ai"
    routine_engine = "routine_engine"
    review = "review"
    scheduler = "scheduler"
    integration = "integration"


class EntrySource(str, Enum):
    inbox = "inbox"
    onboarding = "onboarding"
    daily_review = "daily_review"
    weekly_review = "weekly_review"
    completion_note = "completion_note"
    manual_admin = "manual_admin"
    integration = "integration"


class EntryActor(str, Enum):
    user = "user"
    ai = "ai"
    system = "system"
    integration = "integration"


class ContextSectionType(str, Enum):
    general = "general"
    health = "health"
    person = "person"
    category = "category"
    planning_preference = "planning_preference"
    capacity = "capacity"
    work = "work"
    home = "home"
    relationship = "relationship"
    meaning = "meaning"
    custom = "custom"


class ContextStatus(str, Enum):
    active = "active"
    archived = "archived"


class ContextRevisionSource(str, Enum):
    ai = "ai"
    user = "user"
    system = "system"


class ConfidenceLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AIChangeLevel(str, Enum):
    silent = "silent"
    report = "report"
    confirm = "confirm"
