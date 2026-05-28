API_DIR := apps/api
COMPOSE := docker compose

.PHONY: help api-install api-install-frozen api-lock db-up db-down db-logs api-migrate api-dev api-test api-lint api-format api-check api-openapi api-openapi-check

help:
	@echo "c3Ntr0l developer commands"
	@echo ""
	@echo "Backend:"
	@echo "  make api-install   Install API dependencies with uv"
	@echo "  make api-lock      Resolve and write API uv.lock"
	@echo "  make db-up         Start local Postgres"
	@echo "  make db-down       Stop local Postgres"
	@echo "  make db-logs       Tail local Postgres logs"
	@echo "  make api-migrate   Run Alembic migrations"
	@echo "  make api-dev       Start FastAPI dev server"
	@echo "  make api-test      Run backend tests"
	@echo "  make api-lint      Run backend lint"
	@echo "  make api-format    Format backend code"
	@echo "  make api-check     Run backend lint and tests"
	@echo "  make api-openapi   Export FastAPI OpenAPI JSON"
	@echo "  make api-openapi-check"
	@echo "                      Check committed OpenAPI JSON is current"

api-install:
	cd $(API_DIR) && uv sync --extra dev

api-install-frozen:
	cd $(API_DIR) && uv sync --frozen --extra dev

api-lock:
	cd $(API_DIR) && uv lock

db-up:
	$(COMPOSE) up -d postgres

db-down:
	$(COMPOSE) down

db-logs:
	$(COMPOSE) logs -f postgres

api-migrate:
	cd $(API_DIR) && uv run alembic upgrade head

api-dev:
	cd $(API_DIR) && uv run uvicorn app.main:app --reload

api-test:
	cd $(API_DIR) && uv run pytest

api-lint:
	cd $(API_DIR) && uv run ruff check .

api-format:
	cd $(API_DIR) && uv run ruff format .

api-check: api-lint api-test

api-openapi:
	cd $(API_DIR) && uv run python scripts/export_openapi.py ../../openapi/openapi.json

api-openapi-check:
	cd $(API_DIR) && uv run python scripts/export_openapi.py ../../openapi/openapi.json --check
