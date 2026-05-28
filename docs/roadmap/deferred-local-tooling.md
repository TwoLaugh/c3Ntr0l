# Deferred Until Local Tooling Is Installed

These items are blocked or only partially verifiable until the local machine has the core developer tools installed.

## Blocked By Missing `uv`

- Generate and commit `apps/api/uv.lock`.
- Run `make api-install`.
- Run `make api-install-frozen`.
- Run `make api-test` with real dependencies.
- Run `make api-lint`.
- Run `make api-openapi`.

Once `uv` is installed:

```bash
make api-lock
make api-install
make api-test
make api-lint
make api-openapi
```

## Blocked By Missing Docker

- Start local Postgres with `make db-up`.
- Run migrations locally against Postgres.
- Verify Postgres-specific migration behavior.

Once Docker Desktop is installed and running:

```bash
make db-up
make api-migrate
```

## Blocked By Missing Git/GitHub CLI

- Normal local git workflow.
- Local branch creation.
- Local commits and pushes.
- `gh`-based issue/PR workflows.

Once Git and GitHub CLI are installed:

```bash
git --version
gh --version
gh auth login
```

## A01 Follow-Ups

- Commit `apps/api/uv.lock`.
- Confirm `make api-install` works from a clean checkout.
- Confirm `make api-openapi` writes `openapi/openapi.json`.
- Decide whether generated OpenAPI JSON should be committed permanently or generated only in CI.

## A02 Follow-Ups

- Run the new pytest harness with `uv run pytest`.
- Confirm FastAPI `TestClient` works with installed dependencies.
- Confirm database fixtures work against a test Postgres database.
- Decide whether local tests use a dedicated database or a temporary schema.
- Add app dependency overrides for `get_db` and current-user dependencies when protected database-backed endpoints are implemented.

## A03 Follow-Ups

- Add GitHub Actions once the local test command is proven.
- Run migration upgrade against GitHub Actions Postgres service.
- Switch CI install to `make api-install-frozen` after `uv.lock` exists.
- Ensure CI sets `TEST_DATABASE_URL`; database tests intentionally fail in CI if it is missing.
- Add a migration/schema smoke test that asserts key tables exist after `alembic upgrade head`.
