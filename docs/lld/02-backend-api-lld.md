# Backend API LLD

## 1. Goal

This document defines the context-led V1 API surface for the hosted backend.

The backend owns:

- raw entry storage
- AI-maintained context
- visible categories
- items and recurrence
- plan instances
- reviews
- onboarding
- AI action/proposal audit

Web and Android clients should not duplicate memory, planning, or AI orchestration logic.

## 2. API Style

- REST JSON for V1.
- OpenAPI generated from FastAPI.
- Bearer token session auth.
- ISO 8601 timestamps.
- Server-side timezone handling from user profile.
- All user-owned resources are scoped by authenticated `user_id`.

GraphQL is not necessary for V1.

## 3. Endpoint Groups

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

Current `/domains`, `/tasks`, and `/routines` endpoints may remain temporarily as compatibility routes while the migration to categories/items lands.

## 4. Auth And Profile

```txt
POST /auth/google
POST /auth/dev
GET /auth/me
GET /profile
PATCH /profile
GET /profile/learned-capability
```

Profile fields:

- timezone
- default tone
- preferred day view
- wake/sleep times
- work hours
- planning style
- review style
- AI change visibility

Learned capability is mostly read-only in normal UI. V1 may expose inspection; V2 can add richer analytics.

## 5. Entries

Entries are raw source evidence.

```txt
GET /entries
POST /entries
GET /entries/{id}
```

### 5.1 Create Entry

Request:

```json
{
  "source_type": "inbox",
  "source_id": null,
  "actor": "user",
  "raw_text": "I think dairy may be making my skin worse.",
  "occurred_at": "2026-05-28T20:30:00+01:00",
  "metadata": {
    "mood": "uncertain"
  },
  "ai_interpretation": null
}
```

Response includes:

- id
- source fields
- raw text
- metadata
- created time

Entries are not deleted by default. Later privacy flows can add explicit deletion/export.

## 6. Context Sections

Context sections are AI-maintained understanding documents, separate from categories.

```txt
GET /context-sections
POST /context-sections
GET /context-sections/{id}
PATCH /context-sections/{id}
GET /context-sections/{id}/revisions
GET /context-sections/{id}/evidence
POST /context-sections/{id}/evidence
```

### 6.1 Context Section Shape

```json
{
  "id": "uuid",
  "title": "Health",
  "section_type": "health",
  "summary": "Health constraints and body-related observations.",
  "body": "Back rehab appears important for pain stability.",
  "structured_facts": {
    "emerging_patterns": [
      "Skipping rehab may correlate with worse pain."
    ]
  },
  "confidence_level": "low",
  "confidence_notes": "Based on one daily review and should not be over-weighted.",
  "status": "active",
  "metadata": {}
}
```

### 6.2 Revision Rules

- Creating a context section creates revision `1`.
- Updating a context section creates a new revision.
- Revisions snapshot title, body, structured facts, confidence, change reason, changed-by source, and change level.
- Evidence links can connect entries to a section and optionally to a specific revision.

## 7. Categories

Categories are visible organization buckets and work modes.

```txt
GET /categories
POST /categories
GET /categories/{id}
PATCH /categories/{id}
POST /categories/{id}/archive
GET /categories/{id}/work-mode
```

Category fields:

- name
- description
- status
- sort order
- metadata

`GET /categories/{id}/work-mode` should return:

- active items
- next recommended item
- blockers
- recently touched items
- relevant context snippets

## 8. Items

Items are the primary actionable/trackable primitive.

```txt
GET /items
POST /items
GET /items/{id}
PATCH /items/{id}
POST /items/{id}/archive
POST /items/{id}/complete
POST /items/{id}/partial
POST /items/{id}/skip
POST /items/{id}/reopen
GET /items/{id}/events
```

Item fields:

- title
- notes
- item type
- status
- priority
- primary category
- linked context sections
- flags
- due date
- do window
- effort estimate
- energy required
- recurrence
- metadata

Supported item types:

- action
- reminder
- routine
- recurring_action
- milestone
- note

Supported flags:

- recurring
- soft
- fixed_time
- important
- energy_sensitive
- social
- health
- admin

## 9. Plans And Today

Plans use plan instances that reference items where possible.

```txt
GET /today?plan_date=YYYY-MM-DD
POST /today/regenerate?plan_date=YYYY-MM-DD
PATCH /today/instances/{id}
POST /today/instances/{id}/complete
POST /today/instances/{id}/partial
POST /today/instances/{id}/skip
POST /today/instances/{id}/move
```

Timeline mode:

- uses suggested start/end times.
- distinguishes fixed vs suggested.

List mode:

- uses order/position.
- does not assign suggested times except fixed-time items.

Compatibility note: existing `/today/items/{id}` routes may remain until web and Android clients move to plan instances.

## 10. Proposed Changes

Proposed changes are confirmation-required AI changes.

```txt
GET /proposed-changes
GET /proposed-changes/{id}
POST /proposed-changes/{id}/accept
POST /proposed-changes/{id}/reject
```

Used for:

- in-day schedule changes
- major context rewrites
- important archives/completions
- destructive privacy actions

Proposed change response:

```json
{
  "id": "uuid",
  "change_type": "insert_today_item",
  "target_type": "daily_plan",
  "payload": {
    "item_id": "uuid",
    "suggested_start": "2026-05-28T15:00:00+01:00"
  },
  "reason": "User said this needs doing today.",
  "status": "proposed"
}
```

## 11. Inbox

The inbox endpoint is the active planner entry point.

```txt
POST /inbox/messages
GET /inbox/messages
GET /inbox/messages/{id}
```

Submit flow:

1. Store raw entry.
2. Select relevant context/category/item/plan data.
3. Apply safe updates.
4. Create proposed changes for disruptive updates.
5. Return terse result or clarification.

Response:

```json
{
  "entry_id": "uuid",
  "status": "processed",
  "message": "Added dentist call and proposed fitting it into today.",
  "actions": [
    {
      "action_type": "create_item",
      "target_type": "item",
      "target_id": "uuid"
    }
  ],
  "proposed_changes": [
    {
      "id": "uuid",
      "change_type": "insert_today_item"
    }
  ],
  "clarification": null
}
```

## 12. Reviews

```txt
GET /reviews/daily/{date}/prompt
POST /reviews/daily/{date}
GET /reviews/daily/{date}
GET /reviews/weekly/{week_start}/prompt
POST /reviews/weekly/{week_start}
GET /reviews/weekly/{week_start}
```

Review submissions:

- store raw entry or entries
- update item events
- update context where safe
- update plans where safe
- create proposals for disruptive changes

## 13. Onboarding

```txt
POST /onboarding/quick-start
GET /onboarding/sessions
POST /onboarding/sessions
GET /onboarding/sessions/{id}
POST /onboarding/sessions/{id}/responses
POST /onboarding/sessions/{id}/complete
```

Onboarding responses are entries. Completion triggers AI distillation into context sections, categories, and items.

Deep dive onboarding is chaptered and resumable.

## 14. AI Actions

```txt
GET /ai-actions
GET /ai-actions/{id}
POST /ai-actions/{id}/undo
```

AI action records include:

- source type/source id
- action type
- target type/target id
- before/after state
- reason
- reversible flag
- created time

## 15. Service Boundaries

Implementation services:

- `EntryService`: stores raw source material.
- `ContextIndexService`: returns lightweight section/category index.
- `ContextDistillationService`: updates context with revisions/evidence.
- `CategoryService`: category CRUD and work mode view.
- `ItemService`: item CRUD, recurrence, events.
- `PlanningService`: daily/weekly generation and plan instance mutation.
- `ProposedChangeService`: create/accept/reject confirmation-required changes.
- `InboxOrchestrator`: coordinates entry, context, items, plans, and response.
- `ReviewService`: prompts, response storage, review interpretation.
- `OnboardingService`: quick/deep session state and distillation.

## 16. Testing Implications

API tests should cover:

- user isolation for every owned resource.
- context revision creation on update.
- evidence links rejecting foreign entries.
- inbox duplicate/no-op behavior.
- inbox context update behavior.
- proposed change accept/reject.
- list mode vs timeline mode behavior.
- onboarding pause/resume.

Mocked AI tests are required for AI-dependent routes. Real OpenAI calls should be local/manual only.
