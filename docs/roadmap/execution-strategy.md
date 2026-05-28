# Execution Strategy

## Summary

The fastest safe path is not maximum parallelism from day one. The project should first stabilize tooling, tests, auth, database conventions, and API contracts. After that, agents can work in parallel without constantly breaking each other's assumptions.

Recommended approach:

```txt
Phase A: Stabilize contracts and test harness.
Phase B: Build backend core serially enough to avoid schema churn.
Phase C: Split into backend planning, AI/audit, and frontend lanes.
Phase D: Deploy web V1.
Phase E: Add Android companion once APIs are stable.
```

## Updated Ordering

Recommended ticket ordering:

```txt
1.  T01  Local Developer Environment And Tooling
2.  NEW  CI, test fixtures, and migration test path
3.  NEW  API schema / OpenAPI contract conventions
4.  T02  Google Auth Verification And Session Model
5.  T03  Profile Read/Update API
6.  T04  Domain And Project CRUD
7.  T05  Task CRUD, Archive, And Event Read Model
8.  T13  AI Action Log And Undo Foundation
9.  T06  Routine CRUD And Routine Instance Generation
10. T07  Daily Plan And Today API
11. T08  Task Execution Events
12. T10  Simple Capacity And Selection Planner
13. T09  Weekly Planning Data Flow
14. T11  Daily Review Prompt Generation
15. T12  Daily Review Submission And Learned Capability Update V0
16. T14  Inbox Persistence And Non-AI Command Pipeline
17. T15  OpenAI Structured Inbox Parser
18. T16  AI Review Interpreter V0
19. T17  Web App Scaffold And Auth Shell
20. T18  Web Today Timeline And List View
21. T19  Web Inbox, Reviews, And Weekly Planning Screens
22. T20  Web Admin Screens For Core Objects
23. T21  Backend Deployment
24. T22  Web Deployment
25. T23  Android App Scaffold
26. T24  Android Today, Inbox, And Daily Review
```

Notes:

- `T13` should move earlier than originally planned so later system and AI changes log actions from the start.
- `T10` can begin before full weekly planning polish because the weekly planner composes daily planning behavior.
- Backend deployment should begin earlier than final V1, once auth/core CRUD is stable.
- Android should wait until auth and Today/Review/Inbox APIs are stable.

## Critical Path

Personally usable web critical path:

```txt
T01
-> CI/test harness
-> API contract conventions
-> T02
-> T04
-> T05
-> T06
-> T07
-> T08
-> T10
-> T09
-> T11
-> T12
-> T17
-> T18
-> T19
-> T21
-> T22
```

AI-mediated V1 adds:

```txt
T13 -> T14 -> T15 -> T16
```

Android companion path:

```txt
T02 -> T23 -> T24
```

In practice `T24` should wait for `T08`, `T12`, and `T14`.

## Milestones

### M1: Backend Runs And Auth Works

Tickets:

```txt
T01, CI/test harness, API contract conventions, T02, T03
```

Outcome:

- Local dev setup works.
- CI exists.
- Google auth works.
- User/profile rows are created.
- Protected route pattern is established.

### M2: Manual Planning Backend

Tickets:

```txt
T04, T05, T06, T07, T08
```

Outcome:

- Domains, projects, tasks, and routines exist.
- Routines generate task instances.
- Today exists.
- User can complete, partially complete, skip, and move work.

### M3: Deterministic Personal Planner

Tickets:

```txt
T10, T09, T11, T12
```

Outcome:

- The app can generate realistic day/week structure without AI.
- Daily review adapts planning state.
- Learned capability begins to update.

### M4: AI Capture And Adaptation

Tickets:

```txt
T13, T14, T15, T16
```

Outcome:

- Inbox accepts natural language.
- AI mutates planning state.
- AI actions are logged.
- Free-text reviews can affect future plans.

### M5: Web Usable V1

Tickets:

```txt
T17, T18, T19, T20, T21, T22
```

Outcome:

- Web app is deployed.
- User can run daily planning from browser.
- Admin editing exists in deeper screens.

### M6: Android Companion

Tickets:

```txt
T23, T24
```

Outcome:

- Android app supports Today, Inbox, execution actions, and daily review.

## Parallel Agent Strategy

### Early Stage: 1-2 Agents

Use limited parallelism until `T05` is done.

Reason:

- Auth, ownership, models, migrations, and task semantics are foundational.
- Too many agents here will create rework.

Suggested lanes:

```txt
Agent A: T01 -> CI/test harness -> API contracts -> T02
Agent B: docs, issue shaping, test strategy, web/API contract prep
```

### Middle Stage: 3 Agents

This is the likely sweet spot for web V1.

```txt
Agent A: Backend Domain/Core
T03 -> T04 -> T05 -> T06

Agent B: Planning/Review/AI Backend
T13 -> T07 -> T08 -> T10 -> T09 -> T11 -> T12 -> T14 -> T15 -> T16

Agent C: Frontend/Client
T17 -> T20 -> T18 -> T19 -> T22
```

Agent C can begin with shell, design system, generated client integration, and mocked flows once API contracts are stable.

### Later Stage: 4 Agents

Use only once backend contracts are stable.

```txt
Agent A: Auth/Core API
T01 -> T02 -> T03 -> T04 -> T05

Agent B: Routines/Planning/Review
T06 -> T07 -> T08 -> T10 -> T09 -> T11 -> T12

Agent C: AI/Audit/Inbox
T13 -> T14 -> T15 -> T16

Agent D: Clients/Deployment
T17 -> T20 -> T18 -> T19 -> T21 -> T22 -> T23 -> T24
```

## Work To Keep Serial

Do not heavily parallelize:

- Auth/session model.
- Database migrations touching the same entity family.
- Task model and task CRUD.
- Today execution state machine.
- Weekly planning and capacity planner semantics.
- Learned capability update logic.
- Production auth/deployment wiring.

## Split Recommendations

Split these tickets before implementation:

```txt
T02a: Auth dependency, protected route scaffolding
T02b: Google token verification and session/cookie behavior

T06a: Routine CRUD and recurrence validation
T06b: Routine instance generation and idempotency

T07a: Daily plan read/data API
T07b: Regeneration and user-edit preservation

T09a: Weekly plan generate/read/accept endpoints
T09b: Sunday automation/background job

T15a: OpenAI client wrapper and structured schema
T15b: Intent-to-command conversion
T15c: Context packing, ambiguity handling, safety tests

T18a: Today list view and execution actions
T18b: Timeline view
T18c: Move/reschedule interactions

T19a: Inbox screen
T19b: Daily review screen
T19c: Weekly planning review screen
T19d: AI activity screen
```

## Tools That Improve Time Projections

### Highest Impact

1. CI from the start
   - Backend lint/tests.
   - Migration upgrade test against Postgres.
   - Later web tests and Playwright smoke tests.
   - Estimated impact: saves 10-20 dev days over V1 by catching regressions early.

2. OpenAPI as contract plus generated clients
   - FastAPI OpenAPI as source of truth.
   - Generated TypeScript client for web.
   - Generated Kotlin/Retrofit client or thin generated client for Android.
   - Estimated impact: saves 5-10 dev days and reduces frontend/backend mismatch.

3. Real Postgres tests
   - Use Testcontainers or GitHub Actions Postgres service.
   - Avoid SQLite for planner/database behavior.
   - Estimated impact: saves 5-12 dev days of migration and constraint debugging.

4. shadcn/ui plus custom visual system
   - Use local component primitives, not as the final visual identity.
   - Estimated impact: saves 8-15 dev days on web controls and forms.

5. TanStack Query
   - Standardize server state, cache invalidation, loading/error behavior.
   - Estimated impact: saves 4-8 dev days.

6. Managed deployment
   - Railway or Render for API and Postgres.
   - Avoid VPS/Kubernetes for V1.
   - Estimated impact: saves 5-15 dev days.

### Supporting Tools

- `just` or Makefile task runner for consistent commands.
- GitHub issue templates and PR templates.
- Ruff and pytest from day one.
- Playwright once the web app has core screens.
- Mocked OpenAI fixtures for repeatable AI tests.
- Seed data scripts for realistic manual testing.

## Updated Estimates With Acceleration

Original estimates:

```txt
Full V1 including Android:          74-120 dev days
Personally usable web V1:           61-98 dev days
```

With CI, OpenAPI clients, shadcn/TanStack, managed deployment, and disciplined multi-agent work:

```txt
Full V1 effort:                     55-90 dev days
Full V1 calendar with 2-3 agents:    35-65 calendar days

Personally usable web V1 effort:    42-70 dev days
Web V1 calendar with agents:         28-50 calendar days
```

These estimates still assume review of agent work, good tests, and stable ticket boundaries. More agents too early will likely increase rework rather than reduce elapsed time.

## Immediate Recommendation

Before building more features, run an acceleration sprint:

```txt
1. CI
2. Backend test fixtures
3. Postgres migration test
4. Pydantic response schemas and OpenAPI conventions
5. Generated client plan
6. just/Makefile commands
7. Issue/PR templates
8. Deployment choice
```

Estimated cost:

```txt
3-5 dev days
```

Expected return:

```txt
Lower rework, safer agent parallelism, better estimates, and faster web/Android development.
```
