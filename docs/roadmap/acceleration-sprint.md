# Acceleration Sprint

## Goal

Prepare the repo for fast, safe multi-agent development before feature work ramps up.

This sprint should make the project easier to run, test, validate, and split across agents. It deliberately focuses on leverage: CI, test infrastructure, API contracts, generated clients, repeatable commands, and collaboration hygiene.

Estimated size:

```txt
3-5 dev days
```

Expected payoff:

```txt
Lower rework, safer parallelization, better estimates, earlier deployment confidence.
```

## A01: Command Runner And Developer Setup

Size: S

Goal:

Create a single, obvious way to run common project commands.

Context:

- Current backend is in `apps/api`.
- The intended tooling is `uv`, Docker Compose Postgres, pytest, ruff, and Alembic.
- Local Codex environment did not have `uv`, so a normal dev machine still needs setup verification.

Scope:

- Add either `justfile` or `Makefile`.
- Add commands for:
  - install backend dependencies
  - start local Postgres
  - run migrations
  - run API dev server
  - run backend tests
  - run backend lint
  - run backend format/check
  - generate OpenAPI spec
- Add `docs/dev-setup.md`.
- Update root README to point to dev setup.

Recommended commands:

```txt
api-install
db-up
db-down
api-migrate
api-dev
api-test
api-lint
api-openapi
```

Acceptance Criteria:

- Fresh clone setup is documented.
- A developer can follow docs to run Postgres and the API.
- Common commands are discoverable from the repo root.
- Command names are stable enough for agents and CI to reuse.

Dependencies:

- Existing API scaffold.

## A02: Backend Test Harness

Size: M

Goal:

Create a reliable pytest foundation for API, service, and database tests.

Context:

- Every ticket should include tests.
- Tests need user ownership isolation coverage.
- Planner/database behavior should be tested against real Postgres where possible.

Scope:

- Add `apps/api/tests`.
- Add pytest config if needed.
- Add FastAPI test client fixture.
- Add database session fixture.
- Add test user factory.
- Add auth override fixture for protected endpoints.
- Add smoke tests for:
  - `GET /health`
  - `GET /api/v1/health`
  - placeholder auth/profile routes if still present
- Decide local test database strategy:
  - preferred: separate Postgres database/schema
  - acceptable initial: CI Postgres service plus local docs

Acceptance Criteria:

- `uv run pytest` runs successfully.
- Tests can make API requests through FastAPI test client.
- Tests can create isolated users and database records.
- Auth can be mocked/overridden for protected endpoint tests.
- Test patterns are documented in `docs/dev-setup.md` or `apps/api/tests/README.md`.

Dependencies:

- A01 helpful but not strictly required.

## A03: Migration And Postgres CI Test

Size: M

Goal:

Ensure migrations apply cleanly against real Postgres in CI.

Context:

- The project uses Postgres-specific features: UUIDs, JSONB, enums, `pgcrypto`.
- SQLite tests would miss important behavior.
- Initial migration exists but has not been run in this environment.

Scope:

- Add GitHub Actions workflow for backend.
- Add Postgres service container.
- Install `uv`.
- Run:
  - dependency install
  - ruff
  - Alembic upgrade
  - pytest
- Add migration-specific test or CI step that upgrades from empty DB.
- Ensure `DATABASE_URL` points to CI Postgres.

Acceptance Criteria:

- GitHub Actions backend workflow passes.
- Migration runs against real Postgres.
- Test suite runs after migration.
- CI status is visible on PRs/commits.

Dependencies:

- A02.

## A04: Pydantic Schema And API Contract Conventions

Size: M

Goal:

Stop returning ad hoc dicts and establish clean request/response schemas for OpenAPI.

Context:

- Generated clients only work well if FastAPI response models are explicit.
- Web and Android should use OpenAPI as the contract.
- Current placeholder routes return raw dicts.

Scope:

- Add `apps/api/app/schemas`.
- Define conventions for:
  - request schemas
  - response schemas
  - list responses
  - error responses
  - datetime serialization
  - enum exposure
- Add initial schemas for:
  - health
  - auth `me`
  - profile placeholder/current profile
- Apply `response_model` to existing routes.
- Add `docs/api-contracts.md`.
- Add test that OpenAPI JSON can be generated.

Acceptance Criteria:

- Existing routes use Pydantic response models.
- OpenAPI JSON is stable and generated without errors.
- Schema conventions are documented.
- Future tickets can follow a clear pattern.

Dependencies:

- A02.

## A05: OpenAPI Generation And Client Plan

Size: S

Goal:

Make OpenAPI generation a first-class project artifact and define client generation approach.

Context:

- OpenAPI-generated clients can save web/Android time and reduce mismatch.
- Web likely uses TypeScript client.
- Android can use generated Kotlin/Retrofit client later, or a thin generated client.

Scope:

- Add a command to export OpenAPI JSON from FastAPI.
- Store generated spec at `openapi/openapi.json` or document why it is not committed.
- Add docs for client generation:
  - web: `@hey-api/openapi-ts` or OpenAPI Generator TypeScript
  - Android: OpenAPI Generator Kotlin/Retrofit
- Decide whether generated clients are committed or generated during install/CI.
- Add placeholder directories:
  - `packages/api-client` if web client will be shared
  - or document app-local client generation

Acceptance Criteria:

- `api-openapi` command produces an OpenAPI file.
- Client generation decision is documented.
- Future web ticket can consume the documented contract.

Dependencies:

- A04.

## A06: Issue And PR Templates

Size: XS

Goal:

Make tickets and agent work easier to review consistently.

Context:

- Multi-agent work needs clear scope, ownership, tests, and verification.
- The roadmap tickets already include context and acceptance criteria.

Scope:

- Add `.github/ISSUE_TEMPLATE/feature.yml`.
- Add `.github/ISSUE_TEMPLATE/bug.yml`.
- Add `.github/pull_request_template.md`.
- PR template should require:
  - scope summary
  - tests run
  - migration impact
  - API contract impact
  - screenshots for frontend changes
  - linked ticket

Acceptance Criteria:

- New GitHub issues have structured templates.
- PRs prompt for tests and contract/migration impacts.
- Agent-created PRs have a consistent review shape.

Dependencies:

- None.

## A07: Backend Deployment Decision Record

Size: XS-S

Goal:

Choose and document the V1 backend deployment target.

Context:

- Previous recommendation: Railway or Render.
- V1 should avoid VPS/Kubernetes unless there is a strong reason.
- Deployment should happen earlier than final V1 once auth/core CRUD are stable.

Scope:

- Create `docs/adr/0001-backend-deployment.md`.
- Compare Railway and Render briefly.
- Choose a default target.
- Document:
  - environment variables
  - Postgres provisioning
  - migration strategy
  - expected local/production differences

Recommended default:

```txt
Render for conventional managed deployment, or Railway for speed.
```

Acceptance Criteria:

- Deployment target is chosen or explicitly deferred with criteria.
- Required production environment variables are listed.
- Future deployment ticket has a clear starting point.

Dependencies:

- None.

## A08: Seed Data And Manual Test Scenarios

Size: S

Goal:

Create realistic data and scenarios for local testing.

Context:

- This app's UX only makes sense with life-like data.
- Manual testing should include routines, tasks, projects, partial completion, and missed work.

Scope:

- Add seed script or documented fixture approach.
- Include sample:
  - domains
  - projects
  - tasks
  - routines
  - generated routine instances
  - daily plan items
- Add manual test scenarios:
  - create a routine
  - generate Today
  - partially complete task
  - skip low-stakes item
  - review missed important item

Acceptance Criteria:

- Developer can populate local DB with useful sample data.
- Manual scenarios are documented.
- Seed data does not depend on private user information.

Dependencies:

- A02 helpful.

## Recommended Order

```txt
1. A01 Command Runner And Developer Setup
2. A02 Backend Test Harness
3. A03 Migration And Postgres CI Test
4. A04 Pydantic Schema And API Contract Conventions
5. A05 OpenAPI Generation And Client Plan
6. A06 Issue And PR Templates
7. A07 Backend Deployment Decision Record
8. A08 Seed Data And Manual Test Scenarios
```

`A06` and `A07` can be done in parallel with the test/API contract work.

## Parallelization

For 2 agents:

```txt
Agent A: A01 -> A02 -> A03
Agent B: A04 -> A05 -> A06 -> A07
```

For 3 agents:

```txt
Agent A: A01 -> A02 -> A03
Agent B: A04 -> A05
Agent C: A06 -> A07 -> A08
```

Avoid having multiple agents edit CI, command runner, and test fixtures at the same time. Those files become shared foundation.

## Definition Of Done For Acceleration Sprint

- Backend commands are documented and repeatable.
- Backend tests run locally.
- CI runs backend lint, migration, and tests against Postgres.
- Existing routes use response schemas.
- OpenAPI can be generated.
- Client generation plan is documented.
- Issue and PR templates exist.
- Deployment target is documented.
- Seed/manual testing plan exists.
