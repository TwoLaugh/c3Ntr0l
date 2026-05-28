# Build Readiness Notes

## 1. Current Decision State

Resolved:

- Hosted backend with separate web and Android clients.
- V1 personal-first, productizable later.
- Google login preferred if not excessive.
- AI automatically mutates planning state.
- AI activity log exists but is quiet by default.
- Weekly plan generated on Sundays.
- Weekly planning review screen exists.
- Today defaults to timeline/time blocks.
- List view exists without suggested timings.
- User profile has declared and learned layers.
- Routines generate task instances.
- Partial completion is notes-based.
- Calendar/weather/messages are V2.
- Android V1 is native Kotlin Compose.

## 2. Recommended Build Order

### Phase 1: Backend Skeleton

- FastAPI project setup.
- Postgres config.
- Alembic migrations.
- Google auth spike.
- User/profile tables.
- Healthcheck and OpenAPI.

### Phase 2: Core Data Model

- Domains.
- Projects.
- Tasks.
- Routines.
- Routine instances.
- Completion events.

### Phase 3: Planning Core

- Weekly plans.
- Daily plans.
- Daily plan items.
- Rule-based routine instance generation.
- Rule-based daily plan generation.
- Today API.

### Phase 4: Reviews

- Daily review prompt generation.
- Completion/partial/skip event handling.
- Missed-task review logic.
- Basic learned capability update.

### Phase 5: AI Inbox

- Store inbox messages.
- Parse messages to structured intents.
- Apply task/routine/project changes automatically.
- Log AI actions.
- Trigger affected-day replanning.

### Phase 6: Web Frontend

- Auth.
- Today timeline/list.
- Inbox command box.
- Weekly review.
- Daily review.
- Basic deeper edit screens.

### Phase 7: Android Frontend

- Auth.
- Today.
- Inbox.
- Complete/partial/skip.
- Daily review.

## 3. Things To Decide Before Coding

These are worth deciding before implementation starts:

1. Repo name.
2. Backend deployment target.
3. Postgres hosting target.
4. Whether web app and backend live in a monorepo.
5. Whether Android app lives in the same monorepo.
6. OAuth callback/domain strategy for local dev and production.
7. Preferred UI design direction for Today timeline.
8. Whether to use SQLAlchemy or SQLModel.
9. Whether to use Poetry, uv, or plain pip for Python dependency management.
10. Whether to create the Android project immediately or after backend/web V1.

Recommended defaults:

- Repo name: `ai-personal-os`
- Monorepo: yes
- Structure:
  - `apps/api`
  - `apps/web`
  - `apps/android`
  - `docs`
- Backend deploy: Railway, Render, Fly.io, or a VPS
- Postgres: same provider as backend initially
- Python dependencies: uv
- ORM: SQLAlchemy 2.x
- Android project: defer until backend and web Today flow are usable

## 4. Technical Risks

### 4.1 AI Overreach

The AI can automatically mutate state. This is powerful but trust-sensitive.

Mitigation:

- action log
- archive instead of delete
- reversible actions where practical
- terse confirmations
- deeper inspection UI

### 4.2 Planner Feels Fake

Over-precise timing can make the system feel brittle.

Mitigation:

- distinguish fixed vs suggested blocks
- support list mode
- store do windows
- preserve user edits
- reserve buffers

### 4.3 Reviews Become Homework

If daily review is too long, it will not be used.

Mitigation:

- task-aware prompt filtering
- ask only when the answer changes planning
- support quick energy/load checks

### 4.4 Schema Gets Overfit

Domain-specific tables too early could make the product rigid.

Mitigation:

- common task table
- JSONB metadata for domain-specific details
- promote only proven patterns to columns later

## 5. Next Concrete Step

Before coding, create the repo and commit the documentation.

Then start with:

1. monorepo scaffold
2. FastAPI skeleton
3. Postgres/Alembic setup
4. first migration for users/profile/domains/projects/tasks
5. smoke test endpoint
