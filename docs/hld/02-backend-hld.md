# Backend HLD

## 1. Backend Role

The backend is the source of truth for entries, AI-maintained context, categories, items, planning, reviews, AI decisions, user profile, and audit history.

Web and Android are clients. They should not contain core planning intelligence or long-term memory logic.

## 2. Recommended Stack

Recommended V1 stack:

- FastAPI
- Postgres
- SQLAlchemy 2.x
- Alembic migrations
- OpenAI API
- Background jobs via a simple scheduler initially, with Celery/RQ later if needed
- Google login via OAuth/OIDC if implementation remains low-friction

Rationale:

- Python is strong for AI orchestration and planning logic.
- Postgres gives durable relational structure plus JSON fields where flexibility matters.
- A hosted backend cleanly supports both web and Android clients.

## 3. Service Boundaries

### 3.1 API Layer

Responsibilities:

- authentication
- request validation
- user scoping
- web/mobile endpoints
- response shaping
- confirmation/preview endpoints for proposed AI changes

### 3.2 Entry Service

Responsibilities:

- store raw inbox/review/onboarding/completion input
- attach source metadata
- link entries to known categories, items, plans, or reviews when available
- preserve user-authored source text

### 3.3 Context Service

Responsibilities:

- manage context sections
- create context revisions
- attach evidence links
- expose lightweight context index for AI selection
- support user edits and AI edits
- archive, not hard-delete, by default

### 3.4 Category And Item Services

Responsibilities:

- visible category management
- item creation/update/archive
- item types and flags
- recurrence configuration
- item/category/context linking
- completion, partial completion, skip, move, and reopen state transitions

### 3.5 AI Orchestration Layer

Responsibilities:

- inbox orchestration
- context section selection
- context distillation
- item/category mutation
- plan generation
- review interpretation
- simple learned capability notes
- AI action logging
- proposed change creation for confirmation-required actions

AI orchestration should call services rather than writing directly to the database where possible.

### 3.6 Planning Engine

Responsibilities:

- weekly plan generation
- daily plan generation
- timeline block allocation
- list-mode ordering
- recurrence expansion
- capacity estimation
- in-day proposal generation
- missed-item handling

### 3.7 Background Scheduler

Responsibilities:

- Sunday weekly plan generation
- daily plan materialization
- recurring item instance generation
- later: reminders, integration syncs, notification jobs

## 4. Core Data Model

Most user-owned tables include `user_id` even while V1 is personal-first.

### 4.1 User And Profile

```txt
User
- id
- email
- display_name
- auth_provider
- created_at
- updated_at

UserProfile
- user_id
- timezone
- default_tone
- preferred_day_view
- wake_time
- sleep_time
- work_hours
- planning_style
- review_style
- ai_change_visibility
- created_at
- updated_at
```

### 4.2 Learned Capability Profile

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

V1 should update this slowly and conservatively. Rich behavioral analytics are V2.

### 4.3 Entry

```txt
Entry
- id
- user_id
- source_type
- source_id nullable
- raw_text
- occurred_at
- metadata_json
- ai_interpretation_json nullable
- created_at
```

Entries are the evidence layer. They are not deleted by default.

### 4.4 Context Section

```txt
ContextSection
- id
- user_id
- title
- section_type
- summary
- body
- structured_facts_json
- confidence_notes
- status
- created_by
- updated_by
- created_at
- updated_at
- archived_at nullable
```

Context sections are separate from categories.

### 4.5 Context Section Revision

```txt
ContextSectionRevision
- id
- user_id
- context_section_id
- revision_number
- title_snapshot
- body_snapshot
- structured_facts_snapshot_json
- confidence_notes_snapshot
- change_reason
- changed_by
- change_level
- created_at
```

V1 includes revision history so AI-maintained understanding remains inspectable.

### 4.6 Context Evidence Link

```txt
ContextEvidenceLink
- id
- user_id
- context_section_id
- context_section_revision_id nullable
- entry_id
- relevance
- evidence_note
- created_at
```

Evidence links let the AI and user see why a belief exists.

### 4.7 Category

```txt
Category
- id
- user_id
- name
- description
- status
- sort_order
- metadata_json
- created_at
- updated_at
- archived_at nullable
```

Categories are visible organization buckets and work modes.

### 4.8 Item

```txt
Item
- id
- user_id
- primary_category_id nullable
- source_entry_id nullable
- title
- notes
- item_type
- status
- priority
- flags_json
- due_at nullable
- do_window_start nullable
- do_window_end nullable
- effort_estimate_minutes nullable
- energy_required nullable
- metadata_json
- created_at
- updated_at
- archived_at nullable
```

Items replace tasks and routines as the primary actionable model.

### 4.9 Item Recurrence

```txt
ItemRecurrence
- id
- user_id
- item_id
- recurrence_rule
- preferred_time_window_json
- active
- created_at
- updated_at
```

Recurring behavior is an item capability, not a separate routine object.

### 4.10 Item Links

```txt
ItemContextLink
- id
- user_id
- item_id
- context_section_id
- link_type
- created_at

ItemCategoryLink
- id
- user_id
- item_id
- category_id
- link_type
- created_at
```

An item has one primary category, but optional links can represent cross-cutting relevance.

### 4.11 Plans And Plan Instances

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
- accepted_at nullable

DailyPlan
- id
- user_id
- plan_date
- weekly_plan_id nullable
- generated_at
- default_view_mode
- capacity_snapshot_json
- summary
- status

PlanInstance
- id
- user_id
- daily_plan_id
- item_id nullable
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
- user_edited_at nullable
- created_at
- updated_at
```

Timeline mode uses suggested times. List mode uses position and avoids suggested timings except fixed-time items.

### 4.12 Completion Event

```txt
ItemCompletionEvent
- id
- user_id
- item_id
- plan_instance_id nullable
- event_type
- note
- amount_done nullable
- ai_interpretation_json nullable
- created_at
```

Partial completion is first-class evidence.

### 4.13 Reviews

```txt
DailyReview
- id
- user_id
- review_date
- prompts_json
- responses_json
- energy_level nullable
- load_fit nullable
- mood nullable
- ai_summary
- created_at

WeeklyReview
- id
- user_id
- week_start_date
- responses_json
- ai_summary
- created_at
```

Review responses should also be stored as entries.

### 4.14 Proposed Change

```txt
ProposedChange
- id
- user_id
- source_entry_id nullable
- change_type
- target_type
- target_id nullable
- payload_json
- reason
- status
- created_at
- resolved_at nullable
```

Used for confirmation-required AI actions such as in-day schedule changes.

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

### 5.1 Inbox Orchestration Pipeline

```txt
User input
-> store Entry
-> load context/category/item index
-> select relevant context/categories/items/plans
-> reason about affected system areas
-> apply safe updates through services
-> create ProposedChange for disruptive updates
-> log AI actions
-> return terse confirmation or clarification
```

The AI should ask clarifying questions only when ambiguity or practical scheduling constraints matter.

### 5.2 Context Distillation Pipeline

```txt
Entry or review note
-> select/create relevant context sections
-> update narrative/structured facts
-> attach evidence links
-> create revision
-> classify change visibility
-> log AI action
```

### 5.3 Weekly Planning Pipeline

Runs automatically on Sunday.

```txt
Load user profile
Load learned capability profile
Load active categories/items/recurrences
Load relevant context sections
Estimate weekly capacity
Select major focus areas
Create WeeklyPlan
Create or update DailyPlans and PlanInstances
Log AI actions
Expose Weekly Planning Review
```

### 5.4 Daily Replanning Pipeline

Triggered by:

- accepted proposed changes
- daily review
- user edits
- missed important items

```txt
Load existing DailyPlan
Load changed constraints
Preserve fixed/user-edited instances
Adjust suggested blocks or list order
Move/defer/split items where needed
Log AI actions
```

### 5.5 Daily Review Pipeline

```txt
Load today's plan
Identify completed, partial, missed, and unaddressed instances
Generate task-aware prompts
Collect responses
Store responses as entries
Create completion/review events
Update items/context/plans where safe
Create proposals for disruptive changes
Log AI actions
```

## 6. API Areas

Likely endpoint groups:

```txt
/auth
/profile
/entries
/context-sections
/categories
/items
/plans
/today
/weekly-planning
/reviews
/onboarding
/inbox
/proposed-changes
/ai-actions
```

The Android app should be able to perform all core daily actions without web-only assumptions.

## 7. Migration Strategy

Current implementation tables can migrate as follows:

- `domains` -> `categories`
- `tasks` -> `items`
- `routines` -> `items` with `item_recurrence`
- `daily_plan_items` -> `plan_instances`
- `inbox_messages` -> `entries` with source metadata

Migration should preserve source IDs in metadata until the old tables can be removed.

## 8. Non-Goals For V1

- Hard-delete user planning data by default.
- Full multi-user organization model.
- Complex permissions.
- External integration sync.
- End-to-end encryption.
- Advanced analytics dashboards.
- Android launcher or notification filtering.
