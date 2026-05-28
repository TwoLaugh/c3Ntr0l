# AI Planning LLD

## 1. Goal

This document defines the context-led V1 AI behavior.

The AI should feel like an active planner:

- store the user's raw input
- understand which parts of the system are relevant
- load targeted context
- update safe planning state automatically
- propose disruptive changes before applying them
- keep its understanding inspectable through evidence, revisions, and action logs

## 2. Core AI Inputs

AI services may load:

- latest user entry
- user profile and preferred tone
- learned capability profile
- lightweight context section index
- selected context sections
- categories
- relevant items
- today plan
- current week plan
- recent review entries
- recent AI actions

The AI should not blindly load the full user history. It should inspect indexes first, then load relevant context.

## 3. Entry-First Pipeline

All user-authored inputs follow this shape:

```txt
Raw user input
-> store Entry
-> classify source and rough topic
-> select relevant context/categories/items/plans
-> decide affected system areas
-> apply safe mutations
-> create proposed changes for disruptive mutations
-> log AI actions
-> return terse response or clarification
```

Inputs that produce entries:

- inbox messages
- onboarding answers
- daily review responses
- weekly review responses
- completion/partial/skip notes

## 4. Context Selection

The AI first receives a lightweight index:

```json
{
  "context_sections": [
    {
      "id": "uuid",
      "title": "Health",
      "section_type": "health",
      "summary": "Skin, back rehab, sleep and body constraints.",
      "updated_at": "2026-05-28T20:00:00+01:00"
    }
  ],
  "categories": [
    {
      "id": "uuid",
      "name": "Driving test",
      "description": "Preparation and admin for driving test."
    }
  ]
}
```

The AI returns selected IDs with reasons:

```json
{
  "context_section_ids": ["health-section-id"],
  "category_ids": ["back-rehab-category-id"],
  "reason": "The entry mentions back pain and skipped rehab."
}
```

V1 can combine deterministic matching with LLM ranking. Fallback should load general planning/capacity context when relevance is uncertain.

## 5. Inbox Orchestrator

### 5.1 Supported Outcomes

An inbox message can produce:

- create entry
- create item
- update item
- create category
- update category
- create context section
- update context section
- create proposed plan change
- no-op duplicate
- clarification question

### 5.2 Structured AI Response

The AI should return structured JSON before mutation:

```json
{
  "summary": "User needs to call the dentist today.",
  "requires_clarification": false,
  "clarification_question": null,
  "mutations": [
    {
      "mutation_type": "create_item",
      "change_level": "report",
      "title": "Call dentist",
      "item_type": "action",
      "primary_category_hint": "Health",
      "flags": ["admin", "important"],
      "due_at": "2026-05-28T23:59:00+01:00",
      "reason": "User said this needs doing today."
    },
    {
      "mutation_type": "propose_plan_change",
      "change_level": "confirm",
      "proposal": {
        "change_type": "insert_today_item",
        "reason": "Adding this directly to today would disrupt the current plan."
      }
    }
  ],
  "user_message": "Added dentist call. I can fit it into today if you want."
}
```

### 5.3 Duplicate Handling

Before creating an item, the orchestrator should compare against:

- active items with similar title/category
- current Today plan instances
- recently archived/completed related items
- context sections if the input is informational rather than actionable

Duplicate result:

```json
{
  "mutation_type": "no_op",
  "existing_target_type": "item",
  "existing_target_id": "uuid",
  "reason": "This is already tracked under Driving test."
}
```

## 6. Permission Policy

AI change levels:

- `silent`: harmless metadata/context housekeeping.
- `report`: safe mutation applied automatically and reported tersely.
- `confirm`: proposed but not applied until user accepts.

Confirm first for:

- in-day schedule changes
- major context rewrites
- archiving important items
- marking important items complete
- destructive privacy actions

Auto-apply:

- raw entry storage
- backlog item creation
- low-risk category filing
- low-confidence context note
- duplicate no-op

## 7. Context Distillation

Context distillation converts entries into understanding.

Inputs:

- entry
- selected context sections
- related categories/items
- recent revisions

Output:

```json
{
  "section_updates": [
    {
      "section_id": "uuid",
      "title": "Health",
      "body": "Updated narrative...",
      "structured_facts": {
        "emerging_patterns": [
          {
            "claim": "Dairy may worsen skin flares.",
            "confidence": "low"
          }
        ]
      },
      "confidence_level": "low",
      "confidence_notes": "Based on one user observation.",
      "evidence_entry_ids": ["entry-id"],
      "change_level": "report",
      "change_reason": "New health observation from inbox."
    }
  ]
}
```

Rules:

- One-off observations should usually be low confidence.
- Repeated evidence can increase confidence.
- User corrections should be high-priority evidence.
- Major rewrites should require confirmation.
- Every applied update creates a revision.

## 8. Planning Engine

### 8.1 Weekly Planning

Inputs:

- user profile
- learned capability
- active categories
- active items
- recurrence config
- current priorities context
- capacity context
- recent review entries

Outputs:

- weekly plan summary
- daily plans
- plan instances
- focus categories
- overload warnings

Sunday generation should be automatic later, but manual generation is enough during early implementation.

### 8.2 Daily Planning

Daily planning creates either:

- timeline plan instances with suggested times
- list-mode plan instances with ordering only

Timeline mode should assign suggested timings unless an item is flexible or optional.

List mode should avoid suggested timings except fixed-time items.

### 8.3 In-Day Changes

If an inbox entry affects today:

- create/update the backing item if safe
- create a proposed change for the daily plan
- do not silently rearrange the day

The user can accept or reject the proposed change.

## 9. Category Work Mode

When the user chooses a category or says they are working on it, the system should return:

- active items in that category
- next recommended item
- blockers
- recent completions/skips
- relevant context snippets

Recommendation factors:

- priority
- due date
- effort
- energy required
- current time of day
- recent avoidance/missed events
- context constraints

## 10. Review Interpreter

Daily review should:

- avoid low-value prompts
- ask about important missed or partial items
- store answers as entries
- update item events
- update context if relevant
- update simple learned notes
- propose disruptive changes

Example:

```txt
"Didn't do driving theory because I felt avoidant and tired."
```

Possible updates:

- item event: skipped with note
- context: Driving test has avoidance/friction note
- learned note: evening study may be low reliability
- plan: propose smaller driving theory block tomorrow

V1 can be conservative. V2 can improve behavioral learning from completion timing.

## 11. Onboarding AI

Quick start should collect enough to plan:

- timezone/wake/sleep
- immediate priorities
- urgent items
- recurring items
- planning preference
- tone

Deep dive is chaptered:

- life overview
- health/body
- work/future
- home/admin
- people/social
- attention/friction/phone
- meaning/aliveness
- capacity/routines
- assistant preferences

Each answer is stored as an entry. Chapter completion can distill context sections, categories, and items.

## 12. Testing And Evaluation

Mocked tests should cover:

- create item from inbox
- update context from informational entry
- duplicate/no-op
- clarification for ambiguity
- proposed in-day schedule change
- context evidence/revision creation
- category work mode recommendation
- daily review missed important item
- daily review ignored trivial skipped routine
- onboarding quick start distillation

Manual real-OpenAI evals should use safe mock data and never require committed secrets.

## 13. V2 Notes

Defer:

- advanced evidence weighting
- behavior analytics from completion times
- calendar/weather/message integrations
- notification filtering
- Android launcher behavior
- richer adaptive capacity modeling
