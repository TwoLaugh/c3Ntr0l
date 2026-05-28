from collections.abc import Generator
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.main import app
from app.models.user import LearnedCapabilityProfile, User, UserProfile
from app.services.auth import create_session_token


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


@pytest.fixture()
def db_client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def test_settings() -> Settings:
    settings = Settings(
        GOOGLE_CLIENT_ID="test-google-client-id",
        SESSION_SECRET_KEY="test-session-secret",
        DATABASE_URL=os.getenv("TEST_DATABASE_URL") or "postgresql+psycopg://postgres:postgres@localhost:5432/c3ntr0l",
    )
    settings.openai_api_key = None
    return settings


@pytest.fixture(autouse=True)
def override_settings(test_settings: Settings) -> Generator[None, None, None]:
    app.dependency_overrides[get_settings] = lambda: test_settings
    yield
    app.dependency_overrides.pop(get_settings, None)


@pytest.fixture()
def user(db_session: Session) -> User:
    created = User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@example.com",
        display_name="Test User",
        auth_provider="google",
        auth_subject=str(uuid.uuid4()),
    )
    db_session.add(created)
    db_session.flush()
    db_session.add(UserProfile(user_id=created.id))
    db_session.add(LearnedCapabilityProfile(user_id=created.id))
    db_session.commit()
    db_session.refresh(created)
    return created


@pytest.fixture()
def auth_headers(user: User, test_settings: Settings) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_session_token(user.id, test_settings)}"}
