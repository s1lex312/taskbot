"""Bot configuration via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Runtime configuration loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = ""
    api_base_url: str = "http://localhost:8000/api/v1"
    service_key: str = ""

    environment: str = "development"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> BotSettings:
    """Return a cached BotSettings instance."""
    return BotSettings()
