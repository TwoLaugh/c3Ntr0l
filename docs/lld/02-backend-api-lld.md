# Backend API LLD

## 1. Goal

This document describes the first API surface for the hosted backend.

The API should support both:

- desktop-first web frontend
- native Kotlin Android frontend

The backend owns planning intelligence. Clients should not duplicate planner logic.

## 2. API Style

Recommended:

- REST JSON for V1
- OpenAPI generated from FastAPI
- OAuth/OIDC session or bearer token auth
- ISO 8601 timestamps
- server-side timezone handling from user profile

GraphQL is not necessary for V1.

## 3. Auth

### 3.1 Google Login

Endpoints:

```txt
POST /auth/google
POST /auth/logout
GET /auth/me
```

`POST /auth/google` accepts a Google ID token or authorization result, verifies it, creates/updates the user, and returns the backend session/token response.

Response shape:

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "displayName": "User"
  },
  "profile": {
    "timezone": "Europe/London",
    "defaultTone": "terse",
    "preferredDayView": "timeline"
  }
}
```

## 4. Onboarding And Profile

```txt
GET /profile
PATCH /profile
GET /profile/learned-capability
```

Profile update fields:

- timezone
- tone
- preferred day view
- wake/sleep times
- work hours
- planning style
- review style
- AI change visibility

Learned capability is read-only in normal UI, but admin/debug editing can be added later.

## 5. Inbox

```txt
POST /inbox/messages
GET /inbox/messages
GET /inbox/messages/{id}
```

### 5.1 Submit Inbox Message

Request:

```json
{
  "text": "Need to pressure wash paths this weekend."
}
```

Response:

```json
{
  "messageId": "uuid",
  "status": "processed",
  "confirmation": "Added pressure washing to house maintenance for this weekend.",
  "actions": [
    {
      "type": "task_created",
      "targetType": "task",
      "targetId": "uuid"
    }
  ],
  "clarification": null
}
```

If clarification is required:

```json
{
  "messageId": "uuid",
  "status": "needs_clarification",
  "confirmation": null,
  "actions": [],
  "clarification": {
    "question": "Do you mean this Saturday or Sunday?",
    "options": ["Saturday", "Sunday", "Either"]
  }
}
```

## 6. Today

```txt
GET /today
POST /today/regenerate
PATCH /today/items/{id}
POST /today/items/{id}/complete
POST /today/items/{id}/partial
POST /today/items/{id}/skip
POST /today/items/{id}/move
```

### 6.1 Get Today

Response:

```json
{
  "date": "2026-05-28",
  "defaultViewMode": "timeline",
  "summary": "Light workday with one focus block and maintenance.",
  "items": [
    {
      "id": "uuid",
      "taskId": "uuid",
      "title": "Back rehab",
      "suggestedStart": "2026-05-28T08:00:00+01:00",
      "suggestedEnd": "2026-05-28T08:15:00+01:00",
      "blockType": "routine",
      "isFixedTime": false,
      "isOptional": false,
      "status": "planned",
      "reasonSelected": "Daily routine instance"
    }
  ]
}
```

### 6.2 Partial Completion

Request:

```json
{
  "note": "Did the mobility part but skipped strengthening."
}
```

The backend creates a `task_completion_event`, updates the plan item, and may update task status if appropriate.

## 7. Weekly Planning

```txt
GET /weekly-planning/current
POST /weekly-planning/generate
POST /weekly-planning/{id}/accept
POST /weekly-planning/{id}/regenerate-day
PATCH /weekly-planning/{id}
```

Weekly plans are generated automatically on Sunday, but can also be manually regenerated.

`GET /weekly-planning/current` returns:

- week summary
- focus notes
- day summaries
- overloaded days
- important deferred items
- domain balance

## 8. Tasks

```txt
GET /tasks
POST /tasks
GET /tasks/{id}
PATCH /tasks/{id}
POST /tasks/{id}/archive
GET /tasks/{id}/events
```

Task list filters:

- status
- domain
- project
- due before/after
- do window
- search text

The main UX should not rely on heavy manual task list use, but the API should allow inspection and editing.

## 9. Routines

```txt
GET /routines
POST /routines
GET /routines/{id}
PATCH /routines/{id}
POST /routines/{id}/archive
GET /routines/{id}/instances
```

Routine creation should validate recurrence rules before saving.

## 10. Domains And Projects

```txt
GET /domains
POST /domains
GET /domains/{id}
PATCH /domains/{id}

GET /projects
POST /projects
GET /projects/{id}
PATCH /projects/{id}
POST /projects/{id}/archive
```

Domain response should include optional lightweight counts:

- active tasks
- active projects
- active routines
- recent completions

## 11. Daily Review

```txt
GET /reviews/daily/{date}/prompt
POST /reviews/daily/{date}
GET /reviews/daily/{date}
```

### 11.1 Prompt Generation

The prompt endpoint returns task-aware prompts.

Response:

```json
{
  "date": "2026-05-28",
  "completedSummary": ["Back rehab"],
  "prompts": [
    {
      "id": "missed-auth-bug",
      "type": "missed_important_task",
      "taskId": "uuid",
      "question": "The auth bug did not get done. Should I move it to tomorrow morning or reduce tomorrow's load?"
    }
  ],
  "quickChecks": {
    "energy": true,
    "loadFit": true,
    "mood": false
  }
}
```

## 12. AI Activity

```txt
GET /ai-actions
GET /ai-actions/{id}
POST /ai-actions/{id}/undo
```

Undo is best-effort and only available when `reversible = true`.

## 13. Error Model

Standard error:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The recurrence rule is invalid.",
    "details": {}
  }
}
```

Important codes:

- `unauthorized`
- `forbidden`
- `not_found`
- `validation_error`
- `ai_processing_failed`
- `planner_conflict`
- `unsupported_operation`

## 14. API Build Order

Recommended sequence:

1. Auth/profile.
2. Domains/projects/tasks/routines CRUD.
3. Routine instance generation.
4. Today read/update.
5. Completion events.
6. Daily review prompt/submit.
7. Weekly plan generate/review.
8. Inbox AI pipeline.
9. AI action log/undo.
