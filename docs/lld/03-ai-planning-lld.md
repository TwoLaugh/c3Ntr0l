# AI Planning LLD

## 1. Goal

This document defines the V1 planning and AI behavior in enough detail to begin implementation.

The AI should automatically change the user's planning state, while staying inspectable through the action log.

## 2. AI Components

### 2.1 Inbox Parser

Purpose:

- parse raw user input
- infer intent
- create/update/archive tasks, routines, projects, and constraints
- trigger replanning when useful

Inputs:

- raw inbox text
- user profile
- current date/time/timezone
- active tasks/projects/domains/routines
- near-term plans

Outputs:

- structured intents
- domain service commands
- terse confirmation
- clarification request if required

### 2.2 Planner

Purpose:

- generate weekly plans
- generate daily plans
- adjust existing plans while preserving user edits

Inputs:

- user profile
- learned capability profile
- active tasks
- routine instances
- weekly plan
- daily plan
- completion history
- review notes

Outputs:

- weekly plan
- daily plan items
- suggested timing blocks
- reason-selected text
- AI action logs

### 2.3 Review Interpreter

Purpose:

- generate task-aware review prompts
- interpret user answers
- create completion events
- move/defer/split tasks
- update learned capability slowly

### 2.4 Profile Learner

Purpose:

- update learned capability profile from behavior
- avoid overreacting to single days

Signals:

- planned vs completed minutes
- completion by time of day
- completion by day type
- routine adherence
- partial completion patterns
- repeated missed tasks
- user load-fit feedback

## 3. Inbox Intent Schema

The parser should produce structured JSON before applying changes.

Example:

```json
{
  "intents": [
    {
      "type": "create_task",
      "title": "Pressure wash paths",
      "domainHint": "Infrastructure",
      "projectHint": null,
      "dueWindow": {
        "kind": "weekend",
        "start": "2026-05-30T00:00:00+01:00",
        "end": "2026-05-31T23:59:59+01:00"
      },
      "effortEstimateMinutes": 90,
      "energyRequired": "medium",
      "priority": "normal",
      "confidence": 0.82
    }
  ],
  "requiresClarification": false,
  "clarification": null
}
```

Supported V1 intent types:

- `create_task`
- `update_task`
- `archive_task`
- `create_routine`
- `update_routine`
- `create_project`
- `update_project`
- `add_note`
- `set_constraint`
- `request_replan`
- `record_completion`
- `record_partial_completion`

## 4. Planning Model

### 4.1 Capacity

Capacity is estimated from:

- declared wake/sleep/work hours
- learned weekday/weekend focus minutes
- learned maintenance minutes
- recent completion rates
- recent review load-fit feedback
- fixed commitments in V2

V1 can begin with simple defaults and improve over time.

Example capacity snapshot:

```json
{
  "dayType": "weekday",
  "focusMinutes": 120,
  "maintenanceMinutes": 45,
  "routineMinutes": 35,
  "confidence": 0.45,
  "reason": "Using onboarding defaults with limited history."
}
```

### 4.2 Item Selection

Daily planner should consider:

- due tasks
- active weekly priorities
- routine instances
- important missed tasks
- neglected domains
- effort/energy fit
- available time windows

The planner should avoid filling the day to theoretical maximum capacity. It should reserve buffer by default.

### 4.3 Timing

Backend stores both:

- suggested schedule timing
- broader do window

This supports timeline and list views from the same plan item.

Block types:

- fixed
- suggested
- routine
- floating
- buffer

### 4.4 Preserving User Edits

During replanning, the planner should preserve:

- fixed items
- manually moved items
- completed/partial/skipped items
- items with `user_edited_at`

It may adjust other suggested items.

## 5. Weekly Planning Flow

Runs on Sunday.

Steps:

1. Load user profile and learned capability.
2. Generate routine instances for the week.
3. Identify deadlines and do-window tasks.
4. Identify active projects needing progress.
5. Check domain balance and neglected areas.
6. Estimate capacity per day.
7. Select weekly focus areas.
8. Generate day-level plans.
9. Store `WeeklyPlan` and `DailyPlan` records.
10. Log AI actions.
11. Make the weekly planning review available.

The user can accept or adjust the weekly plan, but the system should not require review before it remains useful.

## 6. Daily Review Prompting

Prompt generation should not ask about every missed item.

Ask about a missed item when:

- priority is high/urgent
- deadline or do-window is near
- repeated misses indicate a planning problem
- it belongs to an active project
- it is a meaningful routine with adherence value
- the answer would change tomorrow's plan

Avoid asking when:

- the task is low-stakes
- the item was optional
- the miss is obvious from context
- asking would create noise without changing planning

## 7. Missed Item Handling

Default flow:

1. Missed item remains active unless completed/archived.
2. Low-value missed item returns quietly to backlog.
3. Important missed item appears in review.
4. Review response informs whether to:
   - move to tomorrow
   - defer
   - split
   - reduce future load
   - archive
   - keep in backlog

## 8. Partial Completion

Partial completion is notes-based.

The AI may interpret the note for future planning, but should preserve the user's raw note.

Example:

```json
{
  "eventType": "partial",
  "note": "Read the theory section but did not do mock questions.",
  "aiInterpretation": {
    "remainingWork": "Do mock questions",
    "estimatedRemainingMinutes": 30,
    "suggestedAction": "create_follow_up_task"
  }
}
```

## 9. AI Action Logging

Every state-changing AI action should create an `ai_action_logs` row.

Examples:

- task created from inbox
- routine created from inbox
- task moved during review
- daily plan regenerated
- learned capability updated

The log is quiet by default but visible in deeper UI.

## 10. Prompting Guidelines

Default tone:

- terse
- calm
- direct
- non-corporate

Avoid:

- motivational excess
- guilt framing
- gamified language
- over-explaining every decision

Good confirmation:

```txt
Added pressure washing to Saturday morning. Kept it flexible.
```

Bad confirmation:

```txt
Amazing! You're taking control of your home maintenance journey!
```

## 11. First Implementation Strategy

Start with deterministic rules plus constrained AI:

1. CRUD and planning data model.
2. Routine instance generation.
3. Simple rule-based daily planner.
4. AI inbox parser with structured JSON.
5. AI review interpreter.
6. More adaptive capacity learning.

This avoids making the first build depend on a vague all-powerful planner.
