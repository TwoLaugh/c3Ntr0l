from functools import lru_cache
from typing import Optional

from pydantic import AliasChoices
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="local", alias="APP_ENV")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/c3ntr0l",
        alias="DATABASE_URL",
    )
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5-mini", alias="OPENAI_MODEL")
    allow_dev_auth: bool = Field(default=True, alias="ALLOW_DEV_AUTH")
    cors_origins: list[str] = Field(
        default=["http://127.0.0.1:3000", "http://localhost:3000"],
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"),
    )
    session_secret_key: str = Field(default="local-dev-session-secret", alias="SESSION_SECRET_KEY")
    session_token_ttl_seconds: int = Field(default=60 * 60 * 24 * 30, alias="SESSION_TOKEN_TTL_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
