"""Auth request/response schemas."""

from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    """Credentials the bot sends on behalf of a Telegram user."""

    telegram_id: int = Field(gt=0)
    username: str | None = Field(default=None, max_length=64)


class TokenResponse(BaseModel):
    """Issued access token."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105  # OAuth2 token type, not a secret
