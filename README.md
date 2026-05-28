# AI Personal Operating System

Backend-led personal planning system for turning messy natural-language life input into adaptive daily and weekly structure.

The product is intentionally not a conventional todo app. It is designed to externalize executive function, maintain routines, protect attention, and produce realistic daily plans from tasks, routines, projects, reviews, and learned user capability.

## Documentation

High-level design:

- [Product HLD](docs/hld/01-product-hld.md)
- [Backend HLD](docs/hld/02-backend-hld.md)
- [Web Frontend HLD](docs/hld/03-web-frontend-hld.md)
- [Android Frontend HLD](docs/hld/04-android-frontend-hld.md)
- [V2 HLD](docs/hld/05-v2-hld.md)

Low-level design:

- [Database Schema LLD](docs/lld/01-database-schema-lld.md)
- [Backend API LLD](docs/lld/02-backend-api-lld.md)
- [AI Planning LLD](docs/lld/03-ai-planning-lld.md)
- [Build Readiness Notes](docs/lld/04-build-readiness.md)

## Repository Structure

```txt
apps/api      FastAPI backend
apps/web      Web frontend, not scaffolded yet
apps/android  Android app, not scaffolded yet
docs          Product and engineering design docs
```

## Backend Quick Start

The backend is set up for Python 3.11+, FastAPI, SQLAlchemy, Alembic, and Postgres.

```bash
cp apps/api/.env.example apps/api/.env
make api-install
make db-up
make api-migrate
make api-dev
```

Local health checks:

- `GET /health`
- `GET /api/v1/health`

Detailed setup instructions live in [Developer Setup](docs/dev-setup.md).

Useful root commands:

```bash
make help
make api-check
make api-openapi
```
