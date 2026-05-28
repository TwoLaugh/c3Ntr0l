# Backend HLD

## 1. Backend Role

The backend is the source of truth for memory, planning, AI decisions, routines, user profile, task state, and review history.

Web and Android are clients. They should not contain core planning intelligence.

## 2. Recommended Stack

Recommended V1 stack:

- FastAPI
- Postgres
- SQLAlchemy or SQLModel
- Alembic migrations
- OpenAI API
- Background jobs via a simple scheduler initially, with Celery/RQ later if needed
- Google login via OAuth/OIDC if implementation remains low-friction

Rationale:

- Python is strong for AI orchestration and planning logic.
- Postgres gives product-ready durability.
- A hosted backend cleanly supports both web and Android clients.

## 3. Service Boundaries

### 3.1 API Layer

Responsibilities:

- authentication
- request validation
- user scoping
- web/mobile endpoints
- response shaping

### 3.2 Domain Services

Responsibilities:

- tasks
- routines
- routine instances
- domains
- projects
- plans
- reviews
- profile state
- archive behavior

### 3.3 AI Orchestration Layer

Responsibilities:

- inbox parsing
- task enrichment
- plan generation
- review interpretation
- learned profile updates
- AI action logging

AI orchestration should call domain services rather than writing directly to the database where possible.

### 3.4 Planning Engine

Responsibilities:

- weekly plan generation
- daily plan generation
- day regeneration
- schedule block allocation
- list ordering
- capacity estimation
- do-window interpretation
- missed-task handling

### 3.5 Background Scheduler

Responsibilities:

- Sunday weekly plan generation
- daily plan materialization
- routine instance generation
- later: reminders, integration syncs, notification jobs

## 4. Core Data Model

### 4.1 User

```txt
User
- id
- email
- display_name
- auth_provider
- created_at
- updated_at
```

Even if V1 is personal-first, most user-owned tables should include `user_id`.

### 4.2 User Profile

```txt
UserProfile
- user_id
- default_tone
- preferred_day_view
- wake_time
- sleep_time
- work_hours
- planning_style
- review_style
- timezone
- created_at
- updated_at
```

### 4.3 Learned Capability Profile

```txt
LearnedCapabilityProfile
- user_id
- weekday_focus_minutes_typical
- weekend_focus_minutes_typical
- weekday_maintenance_minutes_typical
- weekend_maintenance_minutes_typical
- morning_reliability
- afternoon_reliability
- evening_reliability
- plan_completion_rate_14d
- plan_completion_rate_30d
- routine_completion_rate_14d
- overload_sensitivity
- confidence_score
- updated_at
```

This profile should update slowly from observed patterns.

### 4.4 Domain

```txt
Domain
- id
- user_id
- name
- description
- weight
- active
- created_at
- updated_at
```

### 4.5 Project

```txt
Project
- id
- user_id
- domain_id
- title
- desired_outcome
- status
- deadline
- notes
- created_at
- updated_at
```

### 4.6 Task

```txt
Task
- id
- user_id
- domain_id
- project_id nullable
- title
- notes
- status
- priority
- due_at nullable
- do_window_start nullable
- do_window_end nullable
- effort_estimate_minutes nullable
- energy_required nullable
- metadata_json
- source_inbox_message_id nullable
- created_at
- updated_at
- archived_at nullable
```

The task table stays general. Domain-specific details live in `metadata_json`.

### 4.7 Routine

```txt
Routine
- id
- user_id
- domain_id
- title
- notes
- recurrence_rule
- preferred_time_window
- effort_estimate_minutes nullable
- energy_required nullable
- active
- created_at
- updated_at
```

### 4.8 Routine Instance

```txt
RoutineInstance
- id
- user_id
- routine_id
- task_id
- scheduled_for_date
- generated_at
```

Routines generate task instances so reviews and analytics can reason about occurrences.

### 4.9 Weekly Plan

```txt
WeeklyPlan
- id
- user_id
- week_start_date
- generated_at
- summary
- focus_notes
- capacity_snapshot_json
- status
```

### 4.10 Daily Plan

```txt
DailyPlan
- id
- user_id
- date
- weekly_plan_id nullable
- generated_at
- default_view_mode
- capacity_snapshot_json
- summary
- status
```

### 4.11 Daily Plan Item

```txt
DailyPlanItem
- id
- user_id
- daily_plan_id
- task_id nullable
- title_snapshot
- suggested_start nullable
- suggested_end nullable
- do_window_start nullable
- do_window_end nullable
- block_type
- position
- is_fixed_time
- is_optional
- reason_selected
- status
```

Schedule view uses suggested times. List view uses position and status.

### 4.12 Task Completion Event

```txt
TaskCompletionEvent
- id
- user_id
- task_id
- plan_item_id nullable
- event_type
- note
- created_at
- ai_interpretation_json nullable
```

`event_type` examples:

- complete
- partial
- skipped
- moved
- abandoned

Partial completion is notes-based in V1.

### 4.13 Inbox Message

```txt
InboxMessage
- id
- user_id
- raw_text
- processing_status
- parsed_intents_json
- created_at
```

### 4.14 Daily Review

```txt
DailyReview
- id
- user_id
- date
- prompts_json
- responses_json
- energy_level nullable
- load_fit nullable
- mood nullable
- ai_summary
- created_at
```

### 4.15 AI Action Log

```txt
AIActionLog
- id
- user_id
- source_type
- source_id nullable
- action_type
- target_type
- target_id nullable
- before_state_json nullable
- after_state_json nullable
- reason
- reversible
- created_at
```

AI changes should be inspectable and, where practical, reversible.

## 5. AI Pipelines

### 5.1 Inbox Pipeline

```txt
User input
-> store InboxMessage
-> parse intent
-> classify actions
-> apply changes via domain services
-> log AI actions
-> optionally replan affected days
-> return terse confirmation
```

The AI should ask clarifying questions only when a safe default is not available.

### 5.2 Weekly Planning Pipeline

Runs automatically on Sunday.

```txt
Load user profile
Load learned capability profile
Load active domains/projects/tasks/routines
Generate routine instances for the week
Estimate weekly capacity
Select major focus areas
Create WeeklyPlan
Create or update DailyPlans
Log AI actions
Expose Weekly Planning Review
```

### 5.3 Daily Replanning Pipeline

Triggered by:

- inbox updates
- daily review
- user edits
- missed important tasks

```txt
Load existing DailyPlan
Load changed constraints
Preserve fixed/user-edited items
Adjust suggested blocks
Move/defer/split items where needed
Log AI actions
```

### 5.4 Daily Review Pipeline

```txt
Load today's plan
Identify completed, partial, missed, and unaddressed items
Generate task-aware prompts
Collect responses
Create completion/review events
Update backlog and plans
Update learned capability profile slowly
Log AI actions
```

Review prompt selection should consider:

- importance
- deadline pressure
- repeated misses
- project relevance
- routine importance
- whether the answer changes future planning

## 6. API Areas

Likely endpoint groups:

```txt
/auth
/profile
/inbox
/today
/plans
/weekly-planning
/tasks
/routines
/domains
/projects
/reviews
/ai-actions
```

The Android app should be able to perform all core daily actions without web-only assumptions.

## 7. Non-Goals For V1

- Hard-delete user planning data.
- Full multi-user organization model.
- Complex permissions.
- External integration sync.
- End-to-end encryption.
- Advanced analytics dashboards.
- Android launcher or notification filtering.
