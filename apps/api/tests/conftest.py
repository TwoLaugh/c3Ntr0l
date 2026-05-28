from collections.abc import Generator
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def test_database_url() -> str | None:
    return os.getenv("TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def db_engine(test_database_url: str | None) -> Generator[Engine, None, None]:
    if not test_database_url:
        if os.getenv("CI") == "true":
            pytest.fail("TEST_DATABASE_URL must be set in CI for database-backed tests")
        pytest.skip("TEST_DATABASE_URL is not set")

    engine = create_engine(test_database_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
