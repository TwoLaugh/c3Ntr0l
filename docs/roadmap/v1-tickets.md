# V1 Implementation Tickets

Note: this original ticket set reflects the first domain/task/routine-centered architecture. The newer context-led roadmap in `docs/roadmap/context-led-v1-tickets.md` should be treated as the current direction for the next major implementation pass.

## Estimation Scale

- XS: half day or less
- S: 1 day
- M: 2-3 days
- L: 4-6 days
- XL: 1-2 weeks

Estimates assume one developer working carefully, with some unknowns around auth, deployment, and AI behavior. They are planning estimates, not promises.

## Roll-Up Estimate

Using the scale above, the full V1 backlog is roughly:

```txt
Backend foundation through AI inbox/review: 45-69 dev days
Web usable V1 including deployment:        65-104 dev days
Full V1 including Android companion:       74-120 dev days
```

Calendar, weather, message filtering, Android launcher behavior, notification filtering, billing, teams, and public product hardening are not included in this V1 estimate.

The most likely path to a personally usable first version is:

```txt
Backend core + planner + web Today/Inbox/Review: 57-92 dev days
Add deployment:                              61-98 dev days
Add Android companion:                       74-120 dev days
```

These numbers include feature tests at the ticket level, but do not include a large separate QA cycle. If the goal is a product-quality public beta, add another 15-30% for polish, bug fixing, observability, onboarding refinement, and edge-case hardening.

## V1 Usability Definition

For this roadmap, V1 is considered usable when:

- A user can log in with Google.
- A user can create/edit domains, projects, tasks, and routines.
- Routines generate task instances.
- The backend can generate weekly and daily plans.
- Today can be used as a timeline or list.
- The user can complete, partially complete, skip, and move tasks.
- Daily review can adapt future planning.
- Inbox can accept natural-language input and create/update planning state.
- AI actions are logged and inspectable.
- The web app supports Today, Inbox, Weekly Planning Review, Daily Review, and basic admin editing.
- The system is deployed and usable outside local development.
- Android companion supports Today, Inbox, completion actions, and daily review.

The web app can become personally useful before Android exists. Android is part of the broader V1 companion experience, but not required for the first web-usable milestone.

## Testing Bar

Every implementation ticket should include tests unless explicitly marked otherwise.

Minimum backend testing expectations:

- Unit tests for service logic.
- API tests for each endpoint success path.
- API tests for validation errors.
- User ownership/isolation tests for all user-owned resources.
- Database tests for migrations and important constraints.
- Mocked AI tests for OpenAI-dependent behavior.
- Regression tests for planner/review edge cases.

Minimum frontend testing expectations:

- Component tests for important UI states where practical.
- API client tests or mocked integration tests for core flows.
- End-to-end tests for login shell, Today, Inbox, and Daily Review once the web app exists.
- Visual/manual QA notes for timeline layout until screenshot testing is introduced.

No ticket should be treated as done if the happy path works but user isolation, validation, or state-transition behavior is untested.

## Phase 0: Project Foundation

### T01: Local Developer Environment And Tooling

Size: S

Goal: Make the backend easy to run consistently on a normal dev machine.

Context:

- The repo currently has `apps/api`, `pyproject.toml`, Alembic config, and Docker Compose Postgres.
- Current local Codex environment lacks `uv`, so full dependency install was not run here.
- The intended backend stack is FastAPI, Postgres, SQLAlchemy 2.x, Alembic, and `uv`.

Scope:

- Add a root-level development README or `docs/dev-setup.md`.
- Confirm `uv sync` works in `apps/api`.
- Confirm Docker Postgres starts with `docker compose up -d postgres`.
- Run `uv run alembic upgrade head`.
- Run `uv run uvicorn app.main:app --reload`.
- Add `ruff` and `pytest` commands to docs.
- Add minimal test folder and smoke test for `/health`.

Acceptance Criteria:

- A developer can run the API locally from fresh clone instructions.
- `/health` returns `{ "status": "ok" }`.
- `uv run pytest` passes.
- `uv run ruff check .` passes or documented exclusions exist.

Dependencies:

- Existing backend scaffold.

## Phase 1: Auth And User Profile

### T02: Google Auth Verification And Session Model

Size: M

Goal: Implement Google login verification and establish backend user identity.

Context:

- Product decision: use Google login if not excessive.
- `users.auth_subject` should store Google's stable subject claim.
- V1 is personal-first but productizable, so every owned record is scoped by `user_id`.

Scope:

- Implement `POST /api/v1/auth/google`.
- Verify Google ID token using configured `GOOGLE_CLIENT_ID`.
- Create or update `users` row.
- Create default `user_profiles` and `learned_capability_profiles` rows on first login.
- Decide and implement V1 session style: bearer token or signed session cookie.
- Update `GET /api/v1/auth/me` to return authenticated user.
- Add auth dependency for protected routes.

Acceptance Criteria:

- Valid Google token creates/returns a user.
- Invalid token returns `401`.
- New users receive default profile rows.
- Protected endpoints can access current user id.
- Tests cover token verification success/failure with mocks.

Dependencies:

- T01.

### T03: Profile Read/Update API

Size: S

Goal: Implement declared and learned profile endpoints.

Context:

- The declared profile comes from onboarding/settings.
- The learned capability profile is updated later by planning/review behavior.
- User decisions: default tone is terse, default Today view is timeline.

Scope:

- Implement `GET /api/v1/profile`.
- Implement `PATCH /api/v1/profile`.
- Implement `GET /api/v1/profile/learned-capability`.
- Validate timezone, tone, preferred day view, wake/sleep time, work hours.
- Keep learned capability read-only for normal API.

Acceptance Criteria:

- Authenticated user can read and update profile.
- Invalid profile values return `422`.
- Learned capability endpoint returns default row.
- Tests cover profile update and user isolation.

Dependencies:

- T02.

## Phase 2: Core Objects

### T04: Domain And Project CRUD

Size: M

Goal: Implement basic management for domains and lightweight projects.

Context:

- Domains are broad life areas.
- Projects are lightweight outcome containers inside domains.
- Manual editing exists but is not front-page behavior.

Scope:

- Implement domain endpoints:
  - `GET /api/v1/domains`
  - `POST /api/v1/domains`
  - `GET /api/v1/domains/{id}`
  - `PATCH /api/v1/domains/{id}`
- Implement project endpoints:
  - `GET /api/v1/projects`
  - `POST /api/v1/projects`
  - `GET /api/v1/projects/{id}`
  - `PATCH /api/v1/projects/{id}`
  - `POST /api/v1/projects/{id}/archive`
- Enforce user ownership.
- Return lightweight counts where cheap.

Acceptance Criteria:

- Users can create/read/update domains and projects.
- Archived projects no longer appear in default active list.
- Users cannot access another user's objects.
- Tests cover CRUD, archive, and ownership.

Dependencies:

- T02.

### T05: Task CRUD, Archive, And Event Read Model

Size: M

Goal: Implement task management and history read access.

Context:

- Tasks are the core action unit.
- AI should archive rather than hard-delete tasks.
- Domain-specific task fields live in `metadata`.
- Partial completion is handled by events in a later ticket.

Scope:

- Implement:
  - `GET /api/v1/tasks`
  - `POST /api/v1/tasks`
  - `GET /api/v1/tasks/{id}`
  - `PATCH /api/v1/tasks/{id}`
  - `POST /api/v1/tasks/{id}/archive`
  - `GET /api/v1/tasks/{id}/events`
- Support filters for status, domain, project, due date, do window, and search.
- Validate domain/project ownership when assigning.

Acceptance Criteria:

- Tasks can be created, edited, filtered, and archived.
- Task event endpoint exists, even if initially empty.
- User ownership is enforced.
- Tests cover filters and archive behavior.

Dependencies:

- T04.

### T06: Routine CRUD And Routine Instance Generation

Size: L

Goal: Implement routines and generation of task instances.

Context:

- Product decision: routines generate task instances.
- This supports reviews, adherence history, and later analytics.
- Recurrence should use RRULE-compatible text where practical.

Scope:

- Implement:
  - `GET /api/v1/routines`
  - `POST /api/v1/routines`
  - `GET /api/v1/routines/{id}`
  - `PATCH /api/v1/routines/{id}`
  - `POST /api/v1/routines/{id}/archive`
  - `GET /api/v1/routines/{id}/instances`
- Validate recurrence rules.
- Add service to generate instances for a date range.
- Generated instance creates a linked task.
- Avoid duplicate instance generation for the same routine/date.

Acceptance Criteria:

- Routine with daily recurrence can generate one task instance per day.
- Duplicate generation is idempotent.
- Archived/inactive routines do not generate future instances.
- Tests cover daily, weekly, and invalid recurrence.

Dependencies:

- T05.

## Phase 3: Planning Core

### T07: Daily Plan And Today API

Size: L

Goal: Implement stored daily plans and the main Today read/update surface.

Context:

- Today defaults to timeline/time blocks.
- List mode uses the same `daily_plan_items` data without suggested timings.
- Daily plans are stored snapshots so user edits survive replanning.

Scope:

- Implement:
  - `GET /api/v1/today`
  - `POST /api/v1/today/regenerate`
  - `PATCH /api/v1/today/items/{id}`
- Add daily plan service.
- Add simple generation path from active tasks and routine instances.
- Preserve user-edited items during regeneration.
- Return response shape suitable for timeline and list views.

Acceptance Criteria:

- Today endpoint returns daily plan and ordered items.
- Regenerate creates/updates plan for current date.
- User-edited plan items are not overwritten by simple regeneration.
- Tests cover empty day, routine-generated day, and manual move.

Dependencies:

- T06.

### T08: Task Execution Events

Size: M

Goal: Implement complete, partial, skip, and move actions for Today items.

Context:

- Partial completion is notes-based.
- Events are important planning evidence.
- Missed work should be treated as signal, not failure.

Scope:

- Implement:
  - `POST /api/v1/today/items/{id}/complete`
  - `POST /api/v1/today/items/{id}/partial`
  - `POST /api/v1/today/items/{id}/skip`
  - `POST /api/v1/today/items/{id}/move`
- Create `task_completion_events` rows.
- Update `daily_plan_items.status`.
- Update `tasks.status` to completed when appropriate.

Acceptance Criteria:

- Completion marks plan item and task complete.
- Partial completion stores note and leaves task active unless explicitly completed.
- Skip stores note if provided.
- Move updates suggested timing or plan date according to request.
- Tests cover all event types.

Dependencies:

- T07.

### T09: Weekly Planning Data Flow

Size: L

Goal: Implement weekly plan generation and review endpoints.

Context:

- Product decision: weekly plan auto-generates on Sundays.
- User should have a weekly planning review screen.
- The system should remain useful even if the user never opens review.

Scope:

- Implement:
  - `GET /api/v1/weekly-planning/current`
  - `POST /api/v1/weekly-planning/generate`
  - `POST /api/v1/weekly-planning/{id}/accept`
  - `POST /api/v1/weekly-planning/{id}/regenerate-day`
  - `PATCH /api/v1/weekly-planning/{id}`
- Add weekly plan service.
- Generate routine instances for the week.
- Create daily plan shells for week.
- Add summary/focus/capacity snapshot placeholders.

Acceptance Criteria:

- Weekly plan can be generated for current week.
- Generation is idempotent for same user/week.
- Accepting plan updates status.
- Regenerating one day updates only that day.
- Tests cover idempotency and user isolation.

Dependencies:

- T07.

### T10: Simple Capacity And Selection Planner

Size: L

Goal: Replace naive plan generation with a first useful deterministic planner.

Context:

- The app should avoid overloading the day.
- Planner should use declared profile, learned capability defaults, routines, deadlines, do windows, and project/domain context.
- AI planning can come later; deterministic rules should exist first.

Scope:

- Estimate daily capacity from profile and day type.
- Select due/do-window tasks.
- Include routine instances.
- Prioritize high/urgent tasks.
- Include active project next actions where capacity allows.
- Add buffer by not filling all theoretical capacity.
- Produce reason-selected text.

Acceptance Criteria:

- Planner does not schedule more than estimated capacity except fixed items.
- Due/urgent tasks outrank normal backlog tasks.
- Routines appear when due.
- Reason-selected text is returned for plan items.
- Tests cover capacity limits and priority ordering.

Dependencies:

- T09.

## Phase 4: Review And Learning

### T11: Daily Review Prompt Generation

Size: M

Goal: Generate task-aware daily review prompts.

Context:

- Review should not ask about every missed trivial item.
- It should ask when the answer changes future planning.
- Missing a shower should not feel like missing an important work task.

Scope:

- Implement:
  - `GET /api/v1/reviews/daily/{date}/prompt`
- Detect completed, partial, skipped, and unaddressed items.
- Score missed items by priority, due window, project relevance, recurrence importance, and repeated misses.
- Return concise prompt list plus quick checks.

Acceptance Criteria:

- Low-stakes optional misses are not prompted by default.
- Important missed tasks produce review prompts.
- Partial items can request notes/follow-up.
- Tests cover prompt filtering.

Dependencies:

- T08.

### T12: Daily Review Submission And Learned Capability Update V0

Size: L

Goal: Store review responses and update planning state from them.

Context:

- Reviews should adapt future plans.
- Learned capability should update slowly and not overreact to one day.

Scope:

- Implement:
  - `POST /api/v1/reviews/daily/{date}`
  - `GET /api/v1/reviews/daily/{date}`
- Store prompts, responses, energy, load fit, mood, and AI summary placeholder.
- Move/defer/split tasks based on simple non-AI rules or explicit user response.
- Update learned capability with simple rolling metrics.

Acceptance Criteria:

- Review submission persists.
- Important missed task can be moved/deferred based on response.
- Learned capability row changes conservatively after review.
- Tests cover review persistence and basic capability updates.

Dependencies:

- T11.

## Phase 5: AI And Auditability

### T13: AI Action Log And Undo Foundation

Size: M

Goal: Make AI/system changes inspectable and prepare for undo.

Context:

- AI is allowed to make automatic changes.
- Activity log should be tucked away but available.
- Hard delete should be avoided.

Scope:

- Implement:
  - `GET /api/v1/ai-actions`
  - `GET /api/v1/ai-actions/{id}`
  - `POST /api/v1/ai-actions/{id}/undo`
- Add helper for domain services to log AI/system actions.
- Implement undo only for low-risk reversible actions initially, such as archive/unarchive or simple field restore.

Acceptance Criteria:

- AI/system action log can be queried.
- State-changing services can write action logs.
- Undo returns clear unsupported response for non-reversible actions.
- Tests cover log creation and one reversible action.

Dependencies:

- T05.

### T14: Inbox Persistence And Non-AI Command Pipeline

Size: M

Goal: Build the inbox pipeline without depending on OpenAI yet.

Context:

- Inbox should feel like a command box, not a cluttered chat.
- Backend stores history even if UI does not show full chat.
- Deterministic command handling reduces risk before AI parsing.

Scope:

- Implement:
  - `POST /api/v1/inbox/messages`
  - `GET /api/v1/inbox/messages`
  - `GET /api/v1/inbox/messages/{id}`
- Store inbox message.
- Add simple deterministic commands for development, such as:
  - `task: Buy milk`
  - `routine daily: Back rehab`
- Apply resulting changes through domain services.
- Log actions.

Acceptance Criteria:

- Inbox message is stored and processed.
- Simple dev commands create tasks/routines.
- Response includes confirmation and action list.
- Tests cover processing success and unsupported input.

Dependencies:

- T13.

### T15: OpenAI Structured Inbox Parser

Size: XL

Goal: Implement natural-language inbox parsing using OpenAI structured outputs.

Context:

- Core product behavior: user dumps messy life input, system organizes it.
- AI should ask clarification only when a safe default is not available.
- AI should automatically mutate state and log actions.

Scope:

- Define structured intent schema.
- Add OpenAI client wrapper.
- Provide parser with relevant context:
  - current date/time/timezone
  - user profile
  - active domains/projects/tasks/routines
  - near-term plans
- Convert parsed intents into domain service commands.
- Return terse confirmation or clarification question.
- Add safety constraints: archive instead of delete, avoid destructive changes.

Acceptance Criteria:

- Natural input can create tasks with inferred domain/do window.
- Natural input can create routines from recurrence language.
- Ambiguous input returns clarification instead of guessing dangerously.
- AI actions are logged.
- Tests mock OpenAI responses and cover parser-to-command behavior.

Dependencies:

- T14.

### T16: AI Review Interpreter V0

Size: L

Goal: Use AI to interpret free-text review responses into planning adjustments.

Context:

- Review should update task state, plans, and learned assumptions.
- User explanations like "too tired after work" should influence future scheduling.

Scope:

- Define structured review interpretation schema.
- Feed review response, missed items, plan context, and user profile into AI.
- Convert interpretation into safe actions:
  - move task
  - defer task
  - split follow-up task
  - reduce tomorrow load
  - add note
- Log actions.

Acceptance Criteria:

- Free-text review can produce concrete planning changes.
- Unsafe/destructive recommendations are ignored or converted to archive.
- AI summary is stored on review.
- Tests mock AI interpretation.

Dependencies:

- T12, T13.

## Phase 6: Web App V1

### T17: Web App Scaffold And Auth Shell

Size: M

Goal: Create the Next.js web app foundation.

Context:

- Web app is desktop-first full management/planning interface.
- Android is the main mobile execution surface later.
- Current local environment had Node access issues, so this may need a normal dev machine.

Scope:

- Create `apps/web`.
- Add Next.js, TypeScript, styling setup.
- Add API client.
- Add Google login entry flow.
- Add authenticated app shell with navigation.

Acceptance Criteria:

- Web app runs locally.
- User can log in and reach authenticated shell.
- API base URL is configurable.
- Basic route structure exists for Today, Inbox, Weekly Review, Domains, Projects, Routines, Settings, AI Activity.

Dependencies:

- T02.

### T18: Web Today Timeline And List View

Size: XL

Goal: Build the main Today execution surface.

Context:

- Today is the primary screen.
- Default is timeline/time blocks.
- List mode removes suggested timings.
- UI should be calm, utilitarian, and not gamified.

Scope:

- Render Today timeline from `GET /today`.
- Add list/timeline toggle.
- Add complete, partial, skip, and move actions.
- Add plan regeneration button.
- Distinguish fixed vs suggested vs routine vs buffer blocks.
- Handle empty and loading states.

Acceptance Criteria:

- User can operate a full day from Today.
- Partial completion accepts note.
- Timeline and list mode use same backend data.
- UI is responsive enough for narrow screens.

Dependencies:

- T08, T17.

### T19: Web Inbox, Reviews, And Weekly Planning Screens

Size: XL

Goal: Build the core web planning/adaptation surfaces around Today.

Context:

- Inbox is a command surface, not visible chat clutter.
- Weekly review lets user inspect Sunday-generated plan.
- Daily review should be short and task-aware.

Scope:

- Inbox command box with terse result display.
- Daily review prompt/submission screen.
- Weekly planning review screen.
- Basic AI action activity screen.

Acceptance Criteria:

- User can submit natural or dev inbox commands.
- User can complete daily review.
- User can inspect/accept/regenerate weekly plan.
- AI actions can be viewed from deeper screen.

Dependencies:

- T09, T12, T14, T17.

### T20: Web Admin Screens For Core Objects

Size: L

Goal: Provide deeper manual editing screens without making them the main UX.

Context:

- Manual editing should be available if the user looks for it.
- Not all planning should happen through admin screens.

Scope:

- Domain list/detail.
- Project list/detail.
- Task list/detail.
- Routine list/detail.
- Archive view if feasible.
- Settings for tone, default Today view, AI change visibility.

Acceptance Criteria:

- User can manually inspect and edit core objects.
- Admin screens are usable but visually secondary.
- Settings update profile.

Dependencies:

- T03, T04, T05, T06, T17.

## Phase 7: Deployment

### T21: Backend Deployment

Size: M

Goal: Deploy the API and Postgres for V1 usage.

Context:

- Recommendation: Railway or Render for speed.
- Postgres can live on the same provider initially.

Scope:

- Choose provider.
- Configure production Postgres.
- Configure environment variables.
- Run migrations.
- Expose API URL.
- Add basic deployment docs.

Acceptance Criteria:

- Hosted `/health` works.
- Production migration succeeds.
- Environment variables are documented.
- Logs are accessible.

Dependencies:

- T01, T02.

### T22: Web Deployment

Size: M

Goal: Deploy the web app once core flows exist.

Context:

- Web app should be the first usable client.
- Android comes after backend + web Today flow.

Scope:

- Deploy web app to Vercel, Render, or same chosen provider.
- Configure API URL.
- Configure OAuth redirects.
- Confirm login and Today flow in production.

Acceptance Criteria:

- Production web URL loads.
- Google login works.
- Authenticated user can see Today.
- API CORS/session behavior works.

Dependencies:

- T18, T21.

## Phase 8: Android V1

### T23: Android App Scaffold

Size: L

Goal: Create native Kotlin Compose app foundation.

Context:

- Product decision: Android V1 is native Kotlin Compose.
- Android should be the mobile execution/capture surface, not full admin cockpit.

Scope:

- Create `apps/android`.
- Set up Gradle project.
- Add Compose.
- Add API client.
- Add Google sign-in.
- Add basic navigation.

Acceptance Criteria:

- App builds locally.
- User can sign in.
- Authenticated API call works.

Dependencies:

- T02.

### T24: Android Today, Inbox, And Daily Review

Size: XL

Goal: Build the V1 mobile companion flows.

Context:

- Android app should make the user's day easy to live.
- Main flows are Today, Inbox, complete/partial/skip, and quick review.

Scope:

- Today plan screen.
- Timeline/list-style mobile rendering.
- Complete, partial, skip actions.
- Inbox capture.
- Daily review screen.
- Minimal settings.

Acceptance Criteria:

- User can run a day from Android.
- User can capture inbox input.
- User can submit partial completion notes.
- User can complete daily review.

Dependencies:

- T08, T12, T14, T23.

## Recommended First Sprint

The first sprint should aim for a boring but solid backend foundation:

1. T01: Local Developer Environment And Tooling
2. T02: Google Auth Verification And Session Model
3. T03: Profile Read/Update API
4. T04: Domain And Project CRUD

This gives the project real footing before the planner and AI layers arrive.
