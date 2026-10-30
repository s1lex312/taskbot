"""Application configuration via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://taskbot:change_me_in_prod@localhost:5432/taskbot"
    jwt_secret: str = "change_me"  # noqa: S105  # dev-only default, overridden by .env
    jwt_alg: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    # Optional shared secret for the bot -> /auth/telegram channel.
    # Empty string disables the check (local development).
    service_key: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
