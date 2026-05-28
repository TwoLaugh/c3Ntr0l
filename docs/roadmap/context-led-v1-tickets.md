# Context-Led V1 Tickets

This ticket pack supersedes the original domain/task/routine-centered roadmap for the next major implementation pass.

The core product shift is:

> The user provides raw life material through inbox, reviews, onboarding, and completion behavior. The AI stores the original entries, distills them into inspectable context, organizes actionable items into visible categories, and plans days from that understanding.

## Estimation Scale

- XS: half day or less
- S: 1 day
- M: 2-3 days
- L: 4-6 days
- XL: 1-2 weeks

Estimates assume careful implementation with tests. AI behavior tickets include mocked AI tests and at least one manual local smoke test.

## Target Architecture

V1 should move toward these core primitives:

- `entries`: raw source material from inbox, onboarding, daily reviews, weekly reviews, and later integrations.
- `context_sections`: AI-maintained understanding documents, separate from categories.
- `context_section_revisions`: version history for generated understanding.
- `categories`: visible user-facing organization buckets for work modes and item lists.
- `items`: tasks, routines, reminders, milestones, notes, and recurring actions.
- `item_recurrence`: recurrence configuration for items that repeat.
- `plan_instances`: daily/weekly appearances of items in timeline or list plans.
- `reviews`: daily and weekly reflections that produce entries and planning updates.
- `ai_actions`: audit log of meaningful AI-created changes.

Current `domains`, `tasks`, and `routines` can be migrated or compatibility-wrapped while the new model lands.

## Permission Policy

V1 AI behavior should follow this policy:

- Auto-apply: storing entries, category filing, backlog item creation, context distillation, low-risk metadata updates.
- Report: created/updated items, changed context sections, created categories.
- Confirm first: in-day schedule changes, major context rewrites, archiving important items, completion of user-important items, destructive privacy actions.

Raw entries are never deleted by default. Privacy deletion can be added as an explicit later flow.

## Testing Bar

Every ticket should include tests unless explicitly marked as docs-only.

Backend minimums:

- Migration tests or database constraint tests for new schema.
- API success, validation, and user-isolation tests.
- Service tests for context retrieval, AI orchestration, item generation, planning, and versioning.
- Mocked OpenAI tests for AI-dependent behavior.

Frontend minimums:

- Typecheck and production build.
- Component or mocked integration tests where practical.
- Browser smoke check for the main changed screens.

## Phase 0: Architecture And Migration Planning

### C01: Rewrite HLD Around Entries, Context, Categories, Items, And Plans

Size: M

Goal: Update the product/backend architecture docs so future implementation does not keep reinforcing the old domain/task/routine model.

Context:

- Categories and context sections are separate.
- Context is generated from raw entries.
- Categories are visible user-facing work buckets.
- Items replace tasks/routines as the primary actionable model.

Scope:

- Update `docs/hld/01-product-hld.md`.
- Update `docs/hld/02-backend-hld.md`.
- Update `docs/hld/03-web-frontend-hld.md`.
- Mark the old domain/task/routine model as implementation history or compatibility layer.
- Define V1 vs V2 learning boundaries.

Acceptance Criteria:

- Docs describe the new primitives clearly.
- Docs explain how user input flows from entry to context/category/item/plan.
- Docs state that context sections are inspectable and versioned in V1.
- Docs state that advanced behavioral learning is V2.

Dependencies:

- None.

### C02: Database LLD For Context-Led Schema

Size: M

Goal: Produce an implementation-ready database design for the new model.

Scope:

- Define tables, columns, indexes, constraints, and ownership rules for:
  - entries
  - context_sections
  - context_section_revisions
  - context_evidence_links
  - categories
  - items
  - item_category_links if needed
  - item_context_links
  - item_recurrence
  - plan_instances
  - onboarding_sessions
- Decide migration strategy from current tables.
- Define enum values for item types and AI change levels.

Acceptance Criteria:

- `docs/lld/01-database-schema-lld.md` has the new schema.
- Each table has a purpose, ownership model, and important indexes.
- Migration risks are documented.
- Single primary category plus optional links/tags is explicitly addressed.

Dependencies:

- C01.

### C03: API And Service LLD For Context-Led Backend

Size: M

Goal: Define the backend API and service boundaries before refactoring code.

Scope:

- Update `docs/lld/02-backend-api-lld.md`.
- Update `docs/lld/03-ai-planning-lld.md`.
- Define endpoint groups for:
  - entries
  - context sections and revisions
  - categories
  - items
  - plans
  - onboarding
  - AI inbox orchestration
- Define service boundaries:
  - entry ingestion
  - context retrieval
  - context distillation
  - item mutation
  - planning
  - AI action logging

Acceptance Criteria:

- API contract is clear enough for backend and web work to split.
- AI orchestration has an explicit context-selection step.
- Confirmation-required changes are represented in the API.

Dependencies:

- C02.

## Phase 1: Schema Foundation

### C04: Add Entries And Context Section Tables

Size: L

Goal: Implement the evidence and understanding foundation.

Scope:

- Add Alembic migration for:
  - `entries`
  - `context_sections`
  - `context_section_revisions`
  - `context_evidence_links`
- Add SQLAlchemy models and Pydantic schemas.
- Add CRUD/list APIs for entries and context sections.
- Add revision creation on context updates.
- Add user ownership/isolation.

Acceptance Criteria:

- Entries can be created from API and listed by source/type.
- Context sections can be created, updated, archived, and listed.
- Updating a context section creates a revision.
- Evidence links can connect section revisions to entries.
- Tests cover ownership, revisions, validation, and evidence links.

Dependencies:

- C02, C03.

### C05: Add Categories And Items Model

Size: XL

Goal: Introduce the new visible organization and actionable item model.

Scope:

- Add migrations/models/schemas for:
  - `categories`
  - `items`
  - optional `item_context_links`
  - optional `item_category_links` or tags
  - `item_recurrence`
- Support item types:
  - action
  - reminder
  - routine
  - milestone
  - note
  - recurring_action
- Support flags:
  - recurring
  - soft
  - fixed_time
  - important
  - energy_sensitive
  - social
  - health
  - admin
- Add CRUD APIs.
- Preserve primary category while allowing optional linked context/categories.

Acceptance Criteria:

- Categories are visible/listable/editable.
- Items can be created with type, flags, primary category, recurrence, and context links.
- Items can be archived, completed, partially completed, skipped, and reopened.
- Tests cover item validation, recurrence config, ownership, and state transitions.

Dependencies:

- C04.

### C06: Compatibility Layer For Existing Domains, Tasks, And Routines

Size: L

Goal: Keep current local data usable while the new model replaces the old one.

Scope:

- Map domains to categories where appropriate.
- Map tasks to items.
- Map routines to recurring items.
- Decide whether to migrate data immediately or expose compatibility read paths.
- Add migration script or service command.
- Document rollback/backup assumptions for local development.

Acceptance Criteria:

- Existing test data can be converted to categories/items without losing title, notes, status, recurrence, or planning fields.
- Current Today generation can still operate during migration.
- Tests cover conversion of domain/task/routine examples.

Dependencies:

- C05.

## Phase 2: AI Context System

### C07: Entry Ingestion Service

Size: M

Goal: Make inbox, onboarding, reviews, and completion notes all produce durable entries.

Scope:

- Create a shared entry ingestion service.
- Convert inbox messages into `entries`.
- Convert daily/weekly review responses into `entries`.
- Convert onboarding answers into `entries`.
- Attach source metadata, mood/energy when available, and related item/category IDs when known.

Acceptance Criteria:

- Every user-authored input path stores a raw entry.
- Entry metadata preserves source and useful planning context.
- Tests cover inbox, review, and onboarding ingestion.

Dependencies:

- C04.

### C08: Context Section Selection Service

Size: M

Goal: Let the AI inspect section/category names first and load only relevant context.

Scope:

- Add service that returns lightweight context index:
  - section title
  - type
  - summary snippet
  - category associations if any
  - updated time
- Implement relevance selection using deterministic filtering plus optional LLM ranking.
- Keep prompt token limits explicit.

Acceptance Criteria:

- Given an inbox entry, service returns relevant context sections and categories.
- Tests cover obvious routing cases:
  - health note loads Health.
  - message about a person loads person section.
  - home renovation note loads Home Renovation.
  - general planning note loads Planning Preferences/Capacity.
- Fallback loads general context when confidence is low.

Dependencies:

- C04, C05.

### C09: Context Distillation Service With Versioning

Size: XL

Goal: Generate and update AI-maintained understanding from entries.

Scope:

- Build service that can create/update context sections from entries.
- Store:
  - narrative summary
  - structured facts/assumptions
  - confidence/weight notes
  - evidence links
  - revision before/after
- Add mocked OpenAI path for tests.
- Add change-level classification:
  - silent
  - report
  - confirm

Acceptance Criteria:

- New entries can create or update context sections.
- Context updates include evidence and confidence notes.
- Every update creates a revision.
- Major rewrites can be marked confirmation-required.
- Tests cover single-entry low-confidence update and repeated-evidence stronger update.

Dependencies:

- C07, C08.

### C10: AI Inbox Orchestrator V2

Size: XL

Goal: Replace simple intent parsing with an active planner flow.

Scope:

- Store raw entry.
- Select relevant context/categories/items/plans.
- Ask AI which system areas are affected.
- Support mutations:
  - create/update item
  - create/update category
  - update context section
  - propose plan change
  - no-op duplicate
  - clarification
- Deduplicate against existing items and context.
- Return a terse assistant response describing changes or asking a practical question.

Acceptance Criteria:

- Inbox can update multiple system areas from one message.
- Duplicate tasks are recognized.
- Ambiguous or schedule-constrained messages ask clarifying questions.
- In-day plan changes are proposed, not silently applied.
- Tests cover create item, update context, duplicate, clarification, and proposed plan change.

Dependencies:

- C08, C09, C12.

## Phase 3: Planning Model

### C11: Plan Instances Replace Daily Plan Items

Size: XL

Goal: Move Today/Week planning onto the new item model.

Scope:

- Add/modify plan tables so planned blocks reference `items`.
- Preserve support for:
  - timeline mode with timings
  - list mode with ordering and no suggested timings except fixed-time items
  - partial completion
  - skip
  - move/defer
- Update Today APIs.
- Keep old endpoint compatibility if useful for web continuity.

Acceptance Criteria:

- Today can be generated from items and recurring item rules.
- Timeline and list modes behave differently, not just visually.
- Completion events link to plan instances and source items.
- Tests cover generation, list mode, timeline mode, partial completion, skip, and move.

Dependencies:

- C05, C06.

### C12: In-Day Change Proposal Flow

Size: L

Goal: Require confirmation before the AI disrupts the current day.

Scope:

- Add a `proposed_changes` or equivalent model.
- Support AI-generated proposed changes:
  - insert item into today
  - move block
  - remove/defer block
  - regenerate remaining day
- Add accept/reject endpoints.
- Log proposals and outcomes.

Acceptance Criteria:

- Inbox can return a proposed plan change without applying it.
- User can accept or reject.
- Accepted changes mutate Today and log AI action.
- Rejected changes remain visible in audit history.
- Tests cover accept/reject and user isolation.

Dependencies:

- C11.

### C13: Category Work Mode API

Size: M

Goal: Let a user say or choose “I am working on category X” and get a useful working list.

Scope:

- Add endpoint for category focus view.
- Return:
  - active items
  - next recommended item
  - blockers
  - recently touched items
  - relevant context snippets
- Support list sorting by priority, due date, effort, and AI recommendation.

Acceptance Criteria:

- Category page can show a useful work-through list.
- AI can recommend next action with concise reason.
- Tests cover filtering, sorting, and context inclusion.

Dependencies:

- C05, C08.

## Phase 4: Onboarding

### C14: Quick Start Onboarding

Size: L

Goal: Seed the system quickly enough for a user to start planning.

Scope:

- Build onboarding session model and APIs.
- Add quick-start questions for:
  - timezone/wake/sleep
  - immediate priorities
  - current urgent tasks
  - recurring routines
  - planning style
  - assistant tone
- Store answers as entries.
- Distill initial categories/items/context sections.

Acceptance Criteria:

- A new user can complete quick onboarding.
- Quick onboarding creates entries, context sections, categories, and initial items.
- User can skip and resume.
- Tests cover completion, resume, and AI distillation with mocked responses.

Dependencies:

- C07, C09, C10.

### C15: Deep Dive Onboarding Sessions

Size: XL

Goal: Support a multi-session, roughly hour-scale life deep dive without forcing it into one sitting.

Scope:

- Add deep dive chapters:
  - life overview
  - health/body
  - work/future
  - home/admin
  - people/social
  - attention/friction/phone
  - meaning/aliveness
  - capacity/routines
  - assistant preferences
- Store each answer as entries.
- Distill chapter-specific context sections.
- Allow pause/resume.

Acceptance Criteria:

- User can progress chapter by chapter.
- Each chapter can update multiple context sections.
- Deep onboarding can create first-class person sections.
- Tests cover pause/resume and chapter distillation.

Dependencies:

- C14.

### C16: Mock User Seed Data For Testing

Size: M

Goal: Provide realistic local data for UI and AI behavior testing.

Scope:

- Add seed command or fixture set for a mock user.
- Include:
  - categories
  - items
  - recurring items
  - person context sections
  - health context
  - home renovation context
  - entries and revisions
  - Today plan
- Ensure no real secrets or personal sensitive content.

Acceptance Criteria:

- Developer can seed mock data locally.
- Web screens have meaningful data for visual testing.
- Tests can reuse fixtures where appropriate.

Dependencies:

- C05, C09, C11.

## Phase 5: Web Redesign

### C17: Dark Mode Visual System

Size: L

Goal: Move the web app to a calm dark interface aligned with the product feel.

Scope:

- Define dark color tokens.
- Update global layout, forms, panels, buttons, badges, timelines, overlays.
- Preserve accessibility contrast.
- Avoid dashboard clutter and decorative gradients/orbs.
- Keep desktop-first but mobile usable.

Acceptance Criteria:

- All existing web routes render in dark mode.
- Text does not overlap or overflow on desktop/mobile smoke checks.
- Typecheck/build pass.
- Browser screenshots are reviewed for Today, category work mode, inbox overlay, and settings.

Dependencies:

- Can run in parallel with backend tickets once current UI exists.

### C18: Today-First Shell With Burger Menu

Size: L

Goal: Make Today the main app surface and move secondary routes behind a menu.

Scope:

- Replace always-visible sidebar with burger menu.
- Make `/today` the home app experience.
- Add secondary menu routes:
  - Categories
  - Items
  - Context
  - Reviews
  - Settings
  - AI Activity
- Keep keyboard/mouse usability.

Acceptance Criteria:

- Main screen is Today, not an admin dashboard.
- Burger menu works on desktop and mobile.
- Routes remain reachable.
- Browser smoke checks pass.

Dependencies:

- C17.

### C19: Bottom-Right Inbox Overlay

Size: L

Goal: Make the inbox feel like summoning the assistant rather than navigating away.

Scope:

- Add floating circular inbox button.
- Open chat/inbox overlay or sheet.
- Submit messages to AI inbox orchestrator.
- Show terse response, clarifications, and proposed schedule changes.
- Refresh Today if accepted changes affect the day.

Acceptance Criteria:

- User can enter inbox messages from Today without leaving the page.
- AI responses appear in overlay.
- Clarification and proposed-change states are supported.
- Browser smoke test covers submit and close.

Dependencies:

- C10, C12, C18.

### C20: Context Section Inspection UI

Size: L

Goal: Let the user inspect and edit what the AI believes.

Scope:

- Add hidden/secondary Context screen.
- List context sections by type.
- View narrative summary, structured facts, confidence notes, evidence entries, and revision history.
- Allow manual edit that creates a revision.
- Show AI vs user revision source.

Acceptance Criteria:

- User can inspect context sections and evidence.
- User can edit a section.
- Revision history is visible.
- Tests or browser smoke cover list/detail/edit.

Dependencies:

- C04, C09, C18.

### C21: Category Work Mode UI

Size: L

Goal: Make visible categories useful as work surfaces.

Scope:

- Add category list and detail view.
- Show active items, next recommended item, blockers, and relevant context snippets.
- Support item completion/partial/skip from category view.
- Support “work through this category” mode without scheduled times.

Acceptance Criteria:

- Category page is useful when the user chooses a focus area.
- Actions update item and plan state correctly.
- Browser smoke covers selecting a category and completing an item.

Dependencies:

- C13, C18.

### C22: Onboarding Web UI

Size: XL

Goal: Expose quick start and deep dive onboarding in the web app.

Scope:

- Build quick-start flow.
- Build deep-dive chapter flow.
- Support pause/resume.
- Show generated summary after each session.
- Link to context/categories/items created from onboarding.

Acceptance Criteria:

- New user can quick-start and reach Today.
- User can start and resume deep dive.
- Created model is inspectable.
- Typecheck/build and browser smoke pass.

Dependencies:

- C14, C15, C20.

## Phase 6: Reviews And Learning

### C23: Context-Aware Daily Review V2

Size: L

Goal: Make daily review update entries, items, plans, and context intelligently.

Scope:

- Preload prompts based on important missed/completed plan instances.
- Avoid low-value prompts for trivial skipped routine tasks.
- Store review answers as entries.
- Distill relevant context updates.
- Apply low-risk backlog/plan updates.
- Propose major plan changes where needed.

Acceptance Criteria:

- Review prompts are task-aware.
- Review saves entries and updates relevant context/items.
- Tests cover missed important task, trivial skipped routine, and partial completion note.

Dependencies:

- C07, C09, C11, C12.

### C24: Weekly Planning Review V2

Size: L

Goal: Generate and adjust the week from items, context, reviews, and capacity.

Scope:

- Sunday weekly generation.
- Weekly review entries.
- Pull relevant context:
  - current priorities
  - capacity
  - category state
  - recent missed items
- Generate daily plan instances.
- Allow user acceptance/regeneration.

Acceptance Criteria:

- Weekly planner uses context sections and category/item state.
- Sunday generation can be run manually and scheduled later.
- Tests cover generated week, accepted week, regenerated day.

Dependencies:

- C11, C23.

### C25: Basic Behavior Learning Notes

Size: M

Goal: Add V1-level learning notes without overbuilding analytics.

Scope:

- Store simple learned notes from completion/review history.
- Examples:
  - repeated missed evening admin
  - morning routine reliability
  - overload notes
- Link learned notes to evidence entries/events.
- Keep advanced analytics for V2.

Acceptance Criteria:

- Basic learned notes can be generated and inspected.
- Notes have evidence links and confidence.
- Tests cover repeated pattern vs one-off event.

Dependencies:

- C09, C23.

## Phase 7: Migration, Tests, And Readiness

### C26: End-To-End AI Evaluation Fixtures

Size: L

Goal: Create repeatable evaluation cases for the new AI behavior.

Scope:

- Add fixtures for inbox/review/onboarding inputs.
- Cover:
  - duplicate detection
  - health context update
  - person context update
  - home renovation category item creation
  - in-day change proposal
  - ambiguous scheduling clarification
  - category work mode request
- Use mocked AI outputs where deterministic tests are needed.
- Add optional manual eval script for real OpenAI calls.

Acceptance Criteria:

- CI-safe tests cover mocked behavior.
- Local manual eval can run with an API key.
- Results are documented.

Dependencies:

- C10, C12, C15.

### C27: Web E2E Smoke Tests

Size: L

Goal: Catch broken routes and core flows automatically.

Scope:

- Add Playwright or equivalent web smoke test setup.
- Test:
  - login/dev auth
  - Today load
  - inbox overlay submit
  - context section inspect
  - category work mode
  - daily review submit
  - onboarding resume
- Keep tests stable with seeded mock data.

Acceptance Criteria:

- Web smoke tests run locally.
- CI can run them or they are documented if deferred.
- Tests use mock/seed data and avoid real API keys.

Dependencies:

- C16, C19, C20, C21, C22.

### C28: Remove Or Archive Old Domain/Task/Routine UI Paths

Size: M

Goal: Stop exposing the old model once categories/items/context are usable.

Scope:

- Remove or hide old domains/projects/routines routes.
- Redirect old routes to new category/item/context screens where appropriate.
- Update docs and navigation.
- Ensure migration path is complete.

Acceptance Criteria:

- User-facing UI no longer implies domains/tasks/routines are the core model.
- Old local data remains reachable through migrated categories/items.
- Typecheck/build pass.

Dependencies:

- C06, C18, C20, C21.

### C29: Deployment And Data Safety Review

Size: M

Goal: Make sure the new context-led model is safe enough to run with real personal data.

Scope:

- Review migrations and backup guidance.
- Verify `.env` and secrets are ignored.
- Verify no raw entries or mock personal data are committed.
- Add docs for local backup/restore.
- Add warnings around public repo and API keys.

Acceptance Criteria:

- Data backup/restore docs exist.
- Public repo contains no secrets or real personal entries.
- Local user can migrate and roll back with documented steps.

Dependencies:

- C04-C28 as applicable.

## Recommended Ordering

```txt
C01 -> C02 -> C03
        |
        v
C04 -> C05 -> C06
        |
        v
C07 -> C08 -> C09 -> C10
              |       |
              v       v
             C11 -> C12 -> C13
        |
        v
C14 -> C15 -> C16
        |
        v
C17 -> C18 -> C19
        |
        v
C20 -> C21 -> C22
        |
        v
C23 -> C24 -> C25
        |
        v
C26 -> C27 -> C28 -> C29
```

Parallelizable work:

- C17 can start after C01 if the visual direction is stable.
- C16 can start once C05/C09 shapes are clear.
- C20 and C21 can run in parallel after their backend APIs exist.
- C23 and C24 can be split between review service and weekly planner implementation once C11 is stable.

## Rough Roll-Up Estimate

```txt
Architecture/docs:                 6-9 dev days
Schema and migration foundation:   12-22 dev days
AI context/orchestration:          13-24 dev days
Planning/category work mode:       10-18 dev days
Onboarding and mock data:          10-18 dev days
Web redesign and screens:          14-26 dev days
Reviews/learning:                  10-18 dev days
E2E/readiness:                      8-14 dev days

Context-led web-usable V1 pass:    83-149 dev days
```

This estimate is larger than continuing the current simple task app, but it is aimed at the product the user actually described: an AI-mediated personal operating system with inspectable memory and adaptive planning.

## V2 Notes

Defer these until V1 proves the model:

- Strong behavior analytics from completion times and observed usage.
- More sophisticated evidence weighting.
- Calendar/weather/message integrations.
- Notification filtering and Android launcher behavior.
- Advanced adaptive capacity model.
- Rich privacy controls beyond explicit deletion/export basics.
