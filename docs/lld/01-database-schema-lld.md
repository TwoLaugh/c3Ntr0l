# Database Schema LLD

## 1. Goal

This document defines the implementation-ready V1 database design for the context-led version of c3Ntr0l.

The schema is designed for:

- FastAPI, SQLAlchemy, Alembic, and Postgres.
- Hosted multi-user support from the start.
- Raw user entries as durable source evidence.
- AI-maintained, inspectable context sections with version history.
- Visible categories for organizing actionable work.
- Flexible items that replace tasks and routines.
- Plan instances that power Today, weekly planning, timeline mode, and list mode.
- Auditable AI actions, especially when the AI changes context, items, or plans.

The old `domains`, `tasks`, and `routines` tables become migration sources or compatibility tables. They are not the target V1 model.

## 2. Design Principles

- Every user-owned table includes `user_id`.
- Raw entries are archived, not deleted, unless an explicit privacy deletion flow is added later.
- Categories and context sections are separate.
- Categories are visible organization buckets for items.
- Context sections are AI-maintained understanding documents distilled from entries.
- Items are the single actionable primitive. Tasks, routines, reminders, milestones, and notes are represented as item types and flags.
- Recurrence belongs to items through `item_recurrence`.
- Daily and weekly plans store generated `plan_instances`, not transient calculations.
- AI-generated changes must be logged with source, reason, and change level.
- V1 includes lightweight evidence and confidence. V2 can improve evidence weighting with behavioral analytics.
- Cross-user references must be prevented in service code and, where practical, reinforced by composite foreign keys or validation tests.

## 3. Enum Types

Suggested Postgres enums:

```sql
CREATE TYPE entry_source AS ENUM (
  'inbox',
  'onboarding',
  'daily_review',
  'weekly_review',
  'completion_note',
  'manual_admin',
  'integration'
);

CREATE TYPE entry_actor AS ENUM (
  'user',
  'ai',
  'system',
  'integration'
);

CREATE TYPE context_section_type AS ENUM (
  'general',
  'health',
  'person',
  'category',
  'planning_preference',
  'capacity',
  'work',
  'home',
  'relationship',
  'meaning',
  'custom'
);

CREATE TYPE context_revision_source AS ENUM (
  'ai',
  'user',
  'system'
);

CREATE TYPE confidence_level AS ENUM (
  'low',
  'medium',
  'high'
);

CREATE TYPE category_status AS ENUM (
  'active',
  'archived'
);

CREATE TYPE item_type AS ENUM (
  'action',
  'reminder',
  'routine',
  'milestone',
  'note',
  'recurring_action'
);

CREATE TYPE item_status AS ENUM (
  'active',
  'completed',
  'archived'
);

CREATE TYPE item_priority AS ENUM (
  'low',
  'normal',
  'high',
  'urgent'
);

CREATE TYPE energy_level AS ENUM (
  'low',
  'medium',
  'high'
);

CREATE TYPE recurrence_status AS ENUM (
  'active',
  'paused',
  'archived'
);

CREATE TYPE plan_scope AS ENUM (
  'day',
  'week'
);

CREATE TYPE plan_status AS ENUM (
  'draft',
  'active',
  'accepted',
  'superseded',
  'archived'
);

CREATE TYPE plan_view_mode AS ENUM (
  'timeline',
  'list'
);

CREATE TYPE plan_instance_status AS ENUM (
  'planned',
  'in_progress',
  'completed',
  'partial',
  'skipped',
  'moved',
  'archived'
);

CREATE TYPE plan_block_type AS ENUM (
  'fixed',
  'suggested',
  'routine',
  'floating',
  'buffer'
);

CREATE TYPE completion_event_type AS ENUM (
  'complete',
  'partial',
  'skipped',
  'moved',
  'abandoned',
  'reopened'
);

CREATE TYPE review_type AS ENUM (
  'daily',
  'weekly'
);

CREATE TYPE onboarding_session_type AS ENUM (
  'quick_start',
  'deep_dive'
);

CREATE TYPE onboarding_session_status AS ENUM (
  'not_started',
  'in_progress',
  'completed',
  'abandoned'
);

CREATE TYPE ai_change_level AS ENUM (
  'silent',
  'report',
  'confirm'
);

CREATE TYPE ai_action_status AS ENUM (
  'applied',
  'proposed',
  'accepted',
  'rejected',
  'failed',
  'undone'
);
```

SQLAlchemy should mirror these values with Python enums or string enums. Alembic migrations should create enum values explicitly and avoid renaming enum values after data exists.

## 4. Tables

### 4.1 users

Purpose: Authenticated application users.

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL UNIQUE,
  display_name TEXT,
  auth_provider TEXT NOT NULL DEFAULT 'google',
  auth_subject TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Ownership:

- Root owner table.
- Child user data should use `ON DELETE CASCADE`.

### 4.2 user_profiles

Purpose: User-controlled preferences and setup values, not inferred life understanding.

```sql
CREATE TABLE user_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  timezone TEXT NOT NULL DEFAULT 'Europe/London',
  default_tone TEXT NOT NULL DEFAULT 'terse',
  preferred_day_view plan_view_mode NOT NULL DEFAULT 'timeline',
  wake_time TIME,
  sleep_time TIME,
  work_hours JSONB NOT NULL DEFAULT '{}'::jsonb,
  planning_style TEXT,
  review_style TEXT,
  ai_change_visibility TEXT NOT NULL DEFAULT 'quiet',
  onboarding_completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Notes:

- Learned capacity belongs in context sections or V2 analytics tables, not directly here.
- `preferred_day_view = 'list'` means the planner should avoid suggested timings except for fixed-time items.

### 4.3 entries

Purpose: Immutable source material from user input, onboarding, reviews, completion notes, and later integrations.

```sql
CREATE TABLE entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source entry_source NOT NULL,
  actor entry_actor NOT NULL DEFAULT 'user',
  raw_text TEXT NOT NULL,
  summary TEXT,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  source_ref_type TEXT,
  source_ref_id UUID,
  related_item_id UUID,
  related_category_id UUID,
  energy_level energy_level,
  mood TEXT,
  ai_interpretation JSONB NOT NULL DEFAULT '{}'::jsonb,
  confidence confidence_level,
  archived_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Indexes:

```sql
CREATE INDEX idx_entries_user_created ON entries(user_id, created_at DESC);
CREATE INDEX idx_entries_user_source ON entries(user_id, source, created_at DESC);
CREATE INDEX idx_entries_user_related_item ON entries(user_id, related_item_id);
CREATE INDEX idx_entries_user_related_category ON entries(user_id, related_category_id);
CREATE INDEX idx_entries_ai_interpretation_gin ON entries USING gin(ai_interpretation);
```

Ownership:

- Entries are user-owned and should never reference another user's item/category.
- `related_item_id` and `related_category_id` may be nullable to support early onboarding and broad reflections.
- Service tests must validate same-user linking because Postgres cannot enforce user equality through nullable simple foreign keys without composite constraints.

Deletion:

- Default behavior is archive via `archived_at`.
- Explicit privacy deletion can hard-delete entries and cascade evidence links in a later flow.

### 4.4 context_sections

Purpose: Current AI-maintained understanding documents. These are separate from categories and can exist without any category.

```sql
CREATE TABLE context_sections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  section_type context_section_type NOT NULL DEFAULT 'custom',
  description TEXT,
  narrative TEXT NOT NULL DEFAULT '',
  structured_facts JSONB NOT NULL DEFAULT '{}'::jsonb,
  confidence confidence_level NOT NULL DEFAULT 'low',
  confidence_notes TEXT,
  relevance_keywords TEXT[] NOT NULL DEFAULT '{}',
  active BOOLEAN NOT NULL DEFAULT true,
  last_distilled_at TIMESTAMPTZ,
  archived_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, title)
);
```

Indexes:

```sql
CREATE INDEX idx_context_sections_user_active ON context_sections(user_id, active);
CREATE INDEX idx_context_sections_user_type ON context_sections(user_id, section_type);
CREATE INDEX idx_context_sections_keywords_gin ON context_sections USING gin(relevance_keywords);
CREATE INDEX idx_context_sections_structured_facts_gin ON context_sections USING gin(structured_facts);
```

Ownership:

- Context sections are user-owned generated understanding.
- User edits are allowed and should create a revision with `revision_source = 'user'`.
- AI edits should create a revision and evidence links.

### 4.5 context_section_revisions

Purpose: Version history for context section changes.

```sql
CREATE TABLE context_section_revisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  context_section_id UUID NOT NULL REFERENCES context_sections(id) ON DELETE CASCADE,
  revision_number INTEGER NOT NULL,
  revision_source context_revision_source NOT NULL,
  change_level ai_change_level NOT NULL DEFAULT 'report',
  title_snapshot TEXT NOT NULL,
  narrative_snapshot TEXT NOT NULL,
  structured_facts_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
  confidence confidence_level NOT NULL DEFAULT 'low',
  confidence_notes TEXT,
  change_summary TEXT,
  model_name TEXT,
  prompt_hash TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (context_section_id, revision_number)
);
```

Indexes:

```sql
CREATE INDEX idx_context_revisions_user_section ON context_section_revisions(user_id, context_section_id, revision_number DESC);
CREATE INDEX idx_context_revisions_user_created ON context_section_revisions(user_id, created_at DESC);
```

Rules:

- Revision `1` should be created when a section is created.
- Updates must be transactional: update `context_sections`, insert revision, insert evidence links, and log AI action together.
- Revisions are append-only.

### 4.6 context_evidence_links

Purpose: Connect context revisions to the source entries used as evidence.

```sql
CREATE TABLE context_evidence_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  context_section_id UUID NOT NULL REFERENCES context_sections(id) ON DELETE CASCADE,
  context_revision_id UUID NOT NULL REFERENCES context_section_revisions(id) ON DELETE CASCADE,
  entry_id UUID NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
  evidence_note TEXT,
  weight NUMERIC(5,4) NOT NULL DEFAULT 0.5000,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (context_revision_id, entry_id)
);
```

Indexes:

```sql
CREATE INDEX idx_context_evidence_user_section ON context_evidence_links(user_id, context_section_id);
CREATE INDEX idx_context_evidence_user_entry ON context_evidence_links(user_id, entry_id);
```

Rules:

- `weight` is V1 lightweight confidence support, not a full analytics model.
- A single entry can support many context sections.
- A revision can have zero links only for explicit user edits or seed data.

### 4.7 categories

Purpose: Visible user-facing organization buckets for item lists and work modes.

```sql
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  status category_status NOT NULL DEFAULT 'active',
  color TEXT,
  icon TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  archived_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, name)
);
```

Indexes:

```sql
CREATE INDEX idx_categories_user_status_sort ON categories(user_id, status, sort_order, name);
CREATE INDEX idx_categories_metadata_gin ON categories USING gin(metadata);
```

Rules:

- Categories do not store the AI understanding document. That lives in `context_sections`.
- A category can be linked to relevant context through `category_context_links`.
- Categories are visible in the UI and support "work on category X" flows.

### 4.8 category_context_links

Purpose: Optional links between visible categories and relevant context sections.

```sql
CREATE TABLE category_context_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  context_section_id UUID NOT NULL REFERENCES context_sections(id) ON DELETE CASCADE,
  link_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (category_id, context_section_id)
);
```

Indexes:

```sql
CREATE INDEX idx_category_context_user_category ON category_context_links(user_id, category_id);
CREATE INDEX idx_category_context_user_section ON category_context_links(user_id, context_section_id);
```

### 4.9 items

Purpose: The main actionable or trackable primitive. Replaces tasks and routines.

```sql
CREATE TABLE items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  primary_category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
  source_entry_id UUID REFERENCES entries(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  notes TEXT,
  item_type item_type NOT NULL DEFAULT 'action',
  status item_status NOT NULL DEFAULT 'active',
  priority item_priority NOT NULL DEFAULT 'normal',
  due_at TIMESTAMPTZ,
  do_window_start TIMESTAMPTZ,
  do_window_end TIMESTAMPTZ,
  effort_estimate_minutes INTEGER,
  energy_required energy_level,
  is_recurring BOOLEAN NOT NULL DEFAULT false,
  is_soft BOOLEAN NOT NULL DEFAULT false,
  is_fixed_time BOOLEAN NOT NULL DEFAULT false,
  is_important BOOLEAN NOT NULL DEFAULT false,
  is_energy_sensitive BOOLEAN NOT NULL DEFAULT false,
  is_social BOOLEAN NOT NULL DEFAULT false,
  is_health BOOLEAN NOT NULL DEFAULT false,
  is_admin BOOLEAN NOT NULL DEFAULT false,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  completed_at TIMESTAMPTZ,
  archived_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (effort_estimate_minutes IS NULL OR effort_estimate_minutes > 0),
  CHECK (do_window_start IS NULL OR do_window_end IS NULL OR do_window_start <= do_window_end)
);
```

Indexes:

```sql
CREATE INDEX idx_items_user_status ON items(user_id, status);
CREATE INDEX idx_items_user_category_status ON items(user_id, primary_category_id, status);
CREATE INDEX idx_items_user_due_at ON items(user_id, due_at);
CREATE INDEX idx_items_user_do_window ON items(user_id, do_window_start, do_window_end);
CREATE INDEX idx_items_user_type ON items(user_id, item_type);
CREATE INDEX idx_items_user_flags ON items(user_id, is_recurring, is_important, is_soft);
CREATE INDEX idx_items_metadata_gin ON items USING gin(metadata);
```

Rules:

- Each item has at most one `primary_category_id` for simple visible organization.
- Cross-cutting organization uses `item_category_links`, `item_context_links`, and flags.
- Routine behavior is represented by `item_type`, `is_recurring`, and `item_recurrence`.
- Notes and metadata can hold domain-specific details until repeated patterns justify columns.

### 4.10 item_category_links

Purpose: Optional secondary category links without losing the simple primary category model.

```sql
CREATE TABLE item_category_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  link_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (item_id, category_id)
);
```

Indexes:

```sql
CREATE INDEX idx_item_category_user_item ON item_category_links(user_id, item_id);
CREATE INDEX idx_item_category_user_category ON item_category_links(user_id, category_id);
```

Rules:

- Use sparingly. Primary category should drive most UI grouping.
- Secondary links are useful for cross-cutting items, such as a health-related work task.

### 4.11 item_context_links

Purpose: Link items to relevant AI understanding sections.

```sql
CREATE TABLE item_context_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  context_section_id UUID NOT NULL REFERENCES context_sections(id) ON DELETE CASCADE,
  link_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (item_id, context_section_id)
);
```

Indexes:

```sql
CREATE INDEX idx_item_context_user_item ON item_context_links(user_id, item_id);
CREATE INDEX idx_item_context_user_section ON item_context_links(user_id, context_section_id);
```

### 4.12 item_recurrence

Purpose: Recurrence configuration for repeating items.

```sql
CREATE TABLE item_recurrence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  recurrence_rule TEXT NOT NULL,
  timezone TEXT NOT NULL DEFAULT 'Europe/London',
  preferred_window_start TIME,
  preferred_window_end TIME,
  start_date DATE,
  end_date DATE,
  minimum_version TEXT,
  ideal_version TEXT,
  status recurrence_status NOT NULL DEFAULT 'active',
  last_generated_for DATE,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (item_id)
);
```

Indexes:

```sql
CREATE INDEX idx_item_recurrence_user_status ON item_recurrence(user_id, status);
CREATE INDEX idx_item_recurrence_user_last_generated ON item_recurrence(user_id, last_generated_for);
```

Rules:

- `recurrence_rule` should use RRULE-compatible text where possible.
- `items.is_recurring` should be true when an active recurrence row exists.
- V1 can enforce this in service code; database triggers are optional.

### 4.13 plans

Purpose: Daily and weekly generated plan headers.

```sql
CREATE TABLE plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  scope plan_scope NOT NULL,
  plan_date DATE,
  week_start_date DATE,
  default_view_mode plan_view_mode NOT NULL DEFAULT 'timeline',
  generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  summary TEXT,
  focus_notes TEXT,
  capacity_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
  status plan_status NOT NULL DEFAULT 'draft',
  accepted_at TIMESTAMPTZ,
  superseded_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (
    (scope = 'day' AND plan_date IS NOT NULL AND week_start_date IS NULL)
    OR
    (scope = 'week' AND week_start_date IS NOT NULL AND plan_date IS NULL)
  )
);
```

Indexes:

```sql
CREATE UNIQUE INDEX uq_plans_user_day ON plans(user_id, plan_date) WHERE scope = 'day' AND status <> 'archived';
CREATE UNIQUE INDEX uq_plans_user_week ON plans(user_id, week_start_date) WHERE scope = 'week' AND status <> 'archived';
CREATE INDEX idx_plans_user_status ON plans(user_id, status, generated_at DESC);
```

Rules:

- Timeline mode can store suggested times.
- List mode should store ordering and optional do-windows, but avoid suggested times except for fixed-time items.
- Plan generation should snapshot relevant capacity/context into `capacity_snapshot` for auditability.

### 4.14 plan_instances

Purpose: The actual daily or weekly appearances of items in a generated plan.

```sql
CREATE TABLE plan_instances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
  item_id UUID REFERENCES items(id) ON DELETE SET NULL,
  source_recurrence_id UUID REFERENCES item_recurrence(id) ON DELETE SET NULL,
  title_snapshot TEXT NOT NULL,
  notes_snapshot TEXT,
  planned_date DATE NOT NULL,
  suggested_start TIMESTAMPTZ,
  suggested_end TIMESTAMPTZ,
  do_window_start TIMESTAMPTZ,
  do_window_end TIMESTAMPTZ,
  block_type plan_block_type NOT NULL DEFAULT 'suggested',
  position INTEGER NOT NULL,
  is_fixed_time BOOLEAN NOT NULL DEFAULT false,
  is_optional BOOLEAN NOT NULL DEFAULT false,
  reason_selected TEXT,
  status plan_instance_status NOT NULL DEFAULT 'planned',
  user_edited_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (suggested_start IS NULL OR suggested_end IS NULL OR suggested_start <= suggested_end),
  CHECK (do_window_start IS NULL OR do_window_end IS NULL OR do_window_start <= do_window_end)
);
```

Indexes:

```sql
CREATE INDEX idx_plan_instances_plan_position ON plan_instances(plan_id, position);
CREATE INDEX idx_plan_instances_user_date ON plan_instances(user_id, planned_date, position);
CREATE INDEX idx_plan_instances_user_item ON plan_instances(user_id, item_id);
CREATE INDEX idx_plan_instances_user_status ON plan_instances(user_id, status);
```

Rules:

- Plan instances preserve snapshots so old plans remain understandable after item edits.
- Completion, partial completion, skip, and move operations should create `item_events`.

### 4.15 item_events

Purpose: Event history for item state and plan execution.

```sql
CREATE TABLE item_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  item_id UUID REFERENCES items(id) ON DELETE SET NULL,
  plan_instance_id UUID REFERENCES plan_instances(id) ON DELETE SET NULL,
  entry_id UUID REFERENCES entries(id) ON DELETE SET NULL,
  event_type completion_event_type NOT NULL,
  note TEXT,
  amount_done TEXT,
  ai_interpretation JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Indexes:

```sql
CREATE INDEX idx_item_events_user_item ON item_events(user_id, item_id, created_at DESC);
CREATE INDEX idx_item_events_user_plan_instance ON item_events(user_id, plan_instance_id);
CREATE INDEX idx_item_events_user_created ON item_events(user_id, created_at DESC);
```

Rules:

- Partial completion should not imply item completion unless explicitly requested.
- Completion notes should also create entries when they include meaningful user-authored context.

### 4.16 reviews

Purpose: Daily and weekly review records.

```sql
CREATE TABLE reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  review_type review_type NOT NULL,
  review_date DATE,
  week_start_date DATE,
  prompts JSONB NOT NULL DEFAULT '[]'::jsonb,
  responses JSONB NOT NULL DEFAULT '{}'::jsonb,
  energy_level energy_level,
  load_fit TEXT,
  mood TEXT,
  ai_summary TEXT,
  source_entry_id UUID REFERENCES entries(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (
    (review_type = 'daily' AND review_date IS NOT NULL AND week_start_date IS NULL)
    OR
    (review_type = 'weekly' AND week_start_date IS NOT NULL AND review_date IS NULL)
  )
);
```

Indexes:

```sql
CREATE UNIQUE INDEX uq_reviews_user_daily ON reviews(user_id, review_date) WHERE review_type = 'daily';
CREATE UNIQUE INDEX uq_reviews_user_weekly ON reviews(user_id, week_start_date) WHERE review_type = 'weekly';
CREATE INDEX idx_reviews_user_created ON reviews(user_id, created_at DESC);
```

Rules:

- Review responses should be ingested as entries.
- V1 review intelligence can update items/context and propose plan changes.

### 4.17 onboarding_sessions

Purpose: Quick-start and deep-dive onboarding progress.

```sql
CREATE TABLE onboarding_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_type onboarding_session_type NOT NULL,
  status onboarding_session_status NOT NULL DEFAULT 'not_started',
  current_chapter TEXT,
  completed_chapters TEXT[] NOT NULL DEFAULT '{}',
  answers JSONB NOT NULL DEFAULT '{}'::jsonb,
  generated_summary TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Indexes:

```sql
CREATE INDEX idx_onboarding_user_status ON onboarding_sessions(user_id, session_type, status);
```

Rules:

- Each answer should create an entry or be batched into entries at chapter boundaries.
- Deep-dive chapters can be resumed.
- Generated categories/items/context sections must be linked through AI action logs and evidence where applicable.

### 4.18 ai_actions

Purpose: Audit log of meaningful AI-created changes and proposed changes.

```sql
CREATE TABLE ai_actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source_entry_id UUID REFERENCES entries(id) ON DELETE SET NULL,
  action_type TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id UUID,
  change_level ai_change_level NOT NULL DEFAULT 'report',
  status ai_action_status NOT NULL DEFAULT 'applied',
  before_state JSONB,
  after_state JSONB,
  reason TEXT,
  evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
  model_name TEXT,
  prompt_hash TEXT,
  reversible BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ
);
```

Indexes:

```sql
CREATE INDEX idx_ai_actions_user_created ON ai_actions(user_id, created_at DESC);
CREATE INDEX idx_ai_actions_user_status ON ai_actions(user_id, status, created_at DESC);
CREATE INDEX idx_ai_actions_target ON ai_actions(target_type, target_id);
CREATE INDEX idx_ai_actions_source_entry ON ai_actions(user_id, source_entry_id);
```

Rules:

- `change_level = 'silent'`: low-risk metadata/context maintenance.
- `change_level = 'report'`: applied change that should be surfaced tersely.
- `change_level = 'confirm'`: proposed change requiring user acceptance before mutation.
- In-day schedule changes should be proposed first, not silently applied.

### 4.19 proposed_changes

Purpose: Store AI-proposed mutations that require confirmation, especially in-day planning changes.

```sql
CREATE TABLE proposed_changes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source_entry_id UUID REFERENCES entries(id) ON DELETE SET NULL,
  ai_action_id UUID REFERENCES ai_actions(id) ON DELETE SET NULL,
  proposal_type TEXT NOT NULL,
  target_type TEXT,
  target_id UUID,
  proposed_payload JSONB NOT NULL,
  reason TEXT,
  status ai_action_status NOT NULL DEFAULT 'proposed',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ
);
```

Indexes:

```sql
CREATE INDEX idx_proposed_changes_user_status ON proposed_changes(user_id, status, created_at DESC);
CREATE INDEX idx_proposed_changes_source_entry ON proposed_changes(user_id, source_entry_id);
```

Rules:

- Accepting a proposal should apply the mutation and update both `proposed_changes.status` and the linked `ai_actions.status`.
- Rejecting should leave the proposal for audit history.

## 5. Ownership And Integrity Rules

- API and service layers must always filter by `user_id`.
- Tests should include cross-user isolation for every table with user-owned foreign keys.
- Creating links must validate all referenced records belong to the same user.
- Archival should be preferred over hard deletion:
  - `entries.archived_at`
  - `context_sections.archived_at`
  - `categories.archived_at`
  - `items.archived_at`
- Hard deletion is acceptable only for user deletion cascades or explicit future privacy deletion flows.
- AI context updates should run in one transaction:
  - insert entry if needed
  - update/create context section
  - insert context revision
  - insert evidence links
  - insert AI action
- Plan changes should run in one transaction:
  - mutate plan instances/items
  - insert item events if applicable
  - insert AI action
  - update proposal status when applicable

## 6. Migration Notes From Current Schema

Current model:

- `domains`
- `projects`
- `tasks`
- `routines`
- `routine_instances`
- `daily_plans`
- `daily_plan_items`
- `daily_reviews`
- `weekly_plans`
- `ai_action_logs`
- `inbox_messages`

Target model:

- `domains` -> `categories`
- `projects` -> usually `categories`, with project detail moved into category metadata or context sections
- `tasks` -> `items`
- `routines` -> `items` plus `item_recurrence`
- `routine_instances` -> generated `plan_instances` linked to source recurrence
- `daily_plans` and `weekly_plans` -> `plans`
- `daily_plan_items` -> `plan_instances`
- `task_completion_events` -> `item_events`
- `daily_reviews` -> `reviews`
- `ai_action_logs` -> `ai_actions`
- `inbox_messages` -> `entries` with `source = 'inbox'`

Recommended migration strategy:

1. Add new tables alongside old tables.
2. Backfill categories from domains and active projects.
3. Backfill entries from inbox messages and review responses.
4. Backfill items from tasks.
5. Backfill recurring items and recurrence rows from routines.
6. Backfill plans and plan instances from daily/weekly plans.
7. Backfill item events from task completion events.
8. Keep compatibility API reads until web screens move to categories/items/plans.
9. Hide old UI paths after migration verification.
10. Drop old tables only after a later explicit migration once local data backup/restore is documented.

Migration risks:

- Projects may map ambiguously to categories because older projects had domain ownership. Prefer creating categories for active projects and linking them to migrated domain categories through metadata if needed.
- Existing routines and tasks can duplicate each other. Deduplicate by title, recurrence, and source routine id where possible.
- Existing daily plan items store task snapshots. Preserve snapshots even when the source task becomes an item.
- Old AI logs may not have enough source evidence to create context revisions. Migrate them as `ai_actions` without evidence links.
- If old domains represented broad life areas, they should become categories only for visible organization. Their descriptive nuance should be distilled into context sections.

## 7. Testing Implications

Schema and migration tests:

- Alembic upgrade from empty database succeeds.
- Alembic upgrade from current old-schema fixture succeeds.
- Required enums and indexes exist.
- Unique constraints reject duplicate category/context titles per user.
- Archive fields do not break list queries.

Ownership tests:

- User A cannot link an item to User B's category.
- User A cannot link evidence to User B's entry.
- User A cannot update User B's context section revision chain.
- User A cannot accept User B's proposed change.

Context/versioning tests:

- Creating a context section creates revision 1.
- Updating a context section creates the next revision.
- Evidence links connect revisions to entries.
- User edits and AI edits are distinguishable.
- Revisions are append-only.

Item and recurrence tests:

- Item creation supports all item types.
- Primary category is optional but validated when present.
- Secondary category/context links validate ownership.
- Recurring item creation creates one recurrence row.
- Partial completion creates an item event without completing the item.

Planning tests:

- Timeline-mode plans can include suggested times.
- List-mode plans preserve order without suggested times except fixed-time items.
- Plan instances snapshot item title/notes.
- Moving/skipping/completing instances creates item events.

AI audit tests:

- AI context updates log `ai_actions`.
- In-day plan changes create `proposed_changes` and do not mutate plans until accepted.
- Accept/reject flows update proposal and AI action status.

## 8. Open Schema Decisions

- Whether to enforce same-user link integrity with composite foreign keys in addition to service validation.
- Whether context search should use Postgres full-text indexes in V1 or stay with title/type/keyword selection.
- Whether item flags should remain boolean columns or become a normalized `item_flags` table if custom flags become user-defined.
- Whether `proposed_changes.proposed_payload` should use typed per-action payload tables once proposal behavior stabilizes.
- Whether old tables should be retained indefinitely for compatibility or dropped after a documented backup window.
