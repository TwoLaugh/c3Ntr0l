# Developer Setup

## Prerequisites

Install:

- Python 3.11 or newer
- `uv`
- Docker Desktop or another Docker Compose-compatible runtime
- GNU Make

Recommended checks:

```bash
python --version
uv --version
docker compose version
make --version
```

## Windows Notes

The active development environment is Windows-friendly, but it still expects the same tools.

Suggested `winget` installs:

```powershell
winget install Python.Python.3.11
winget install astral-sh.uv
winget install Docker.DockerDesktop
winget install GnuWin32.Make
```

Then open a new terminal and rerun the prerequisite checks.

If `make` is unavailable, you can run the equivalent commands manually:

```powershell
cd apps/api
uv sync --extra dev
cd ..\..
docker compose up -d postgres
cd apps/api
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

The repo includes `.python-version` with `3.11` for tools that respect it.

## First Run

From the repository root:

```bash
cp apps/api/.env.example apps/api/.env
make api-install
make db-up
make api-migrate
make api-dev
```

The API should be available at:

```txt
http://127.0.0.1:8000
```

Health checks:

```txt
GET http://127.0.0.1:8000/health
GET http://127.0.0.1:8000/api/v1/health
```

## Common Commands

```bash
make help
make api-install
make api-lock
make db-up
make db-down
make db-logs
make api-migrate
make api-dev
make api-test
make api-lint
make api-format
make api-check
make api-openapi
make api-openapi-check
```

## Backend

The backend lives in:

```txt
apps/api
```

It uses:

- FastAPI
- SQLAlchemy 2.x
- Alembic
- Postgres
- Pydantic settings
- `uv` for dependency management

The local database is defined in:

```txt
docker-compose.yml
```

Default local connection string:

```txt
postgresql+psycopg://postgres:postgres@localhost:5432/c3ntr0l
```

## Environment

Copy the example environment file before running the API:

```bash
cp apps/api/.env.example apps/api/.env
```

Important variables:

```txt
APP_ENV=local
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/c3ntr0l
GOOGLE_CLIENT_ID=
OPENAI_API_KEY=
```

`GOOGLE_CLIENT_ID` and `OPENAI_API_KEY` can stay empty until the relevant auth and AI tickets are implemented.

## OpenAPI

Generate the backend OpenAPI document:

```bash
make api-openapi
```

This writes:

```txt
openapi/openapi.json
```

That file is intended to become the source for generated web and Android clients once the API response schemas are stable.

Check whether the committed OpenAPI file is current:

```bash
make api-openapi-check
```

Until acceleration ticket `A04`/`A05` lands, the generated spec is a foundation command rather than a finished client contract.

## Testing

Run backend tests:

```bash
make api-test
```

Run backend lint:

```bash
make api-lint
```

The first test harness is created in acceleration ticket `A02`. Until then, these commands define the expected interface and may fail if dependencies or tests are not installed yet.

## Troubleshooting

If the API cannot connect to Postgres:

```bash
make db-up
make db-logs
```

If migrations fail, confirm `DATABASE_URL` in `apps/api/.env` points at the local Postgres container.

If `uv` is missing, install it before running backend commands. The project intentionally uses `uv` so agents, local development, and CI share one dependency workflow.

## Lockfile

The API should have a committed `apps/api/uv.lock` once `uv` is available in the development environment:

```bash
make api-lock
```

CI should eventually use:

```bash
make api-install-frozen
```

This keeps dependency resolution reproducible. The lockfile has not been generated in the current Codex environment because `uv` is not installed here.
