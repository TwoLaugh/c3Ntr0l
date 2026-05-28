# API Test Harness

The backend tests use `pytest`.

Run from the repository root:

```bash
make api-test
```

Or from `apps/api`:

```bash
uv run pytest
```

## Fixtures

`conftest.py` provides:

- `client`: FastAPI `TestClient`
- `test_database_url`: reads `TEST_DATABASE_URL`
- `db_engine`: SQLAlchemy engine, skipped if `TEST_DATABASE_URL` is unset
- `db_session`: SQLAlchemy session wrapped in a rollback transaction

Local database-backed tests should use a dedicated test database or schema. Do not point `TEST_DATABASE_URL` at production or at a database with data you care about.

Database tests should be marked:

```python
@pytest.mark.db
```

If `TEST_DATABASE_URL` is missing locally, DB-backed tests skip. If `CI=true`, missing `TEST_DATABASE_URL` fails so CI cannot accidentally pass without database coverage.

## Current Status

The initial harness includes health-route smoke tests. Database-heavy tests begin in later tickets once auth and CRUD services exist.
