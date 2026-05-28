# c3Ntr0l API

FastAPI backend for the AI personal operating system.

## Local Setup

This project is configured for `uv`.

```bash
cd apps/api
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

From the repository root, prefer the shared command runner:

```bash
make api-install
make db-up
make api-migrate
make api-dev
```

The API exposes:

- `GET /health`
- `GET /api/v1/auth/me`
- `GET /api/v1/profile`

The first implementation pass includes the database models and initial migration. Most feature routes are intentionally still to be built.
