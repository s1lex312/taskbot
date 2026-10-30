"""Auth endpoints."""

from fastapi import APIRouter, Depends, Header, HTTPException, status

from api.core.config import get_settings
from api.core.dependencies import SessionDep
from api.schemas.auth import TelegramAuthRequest, TokenResponse
from api.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


async def verify_service_key(x_service_key: str | None = Header(default=None)) -> None:
    """Optionally guard the auth endpoint with a shared service key.

    Disabled when SERVICE_KEY is empty (local development).
    """
    settings = get_settings()
    if settings.service_key and x_service_key != settings.service_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid service key",
        )


@router.post(
    "/telegram",
    response_model=TokenResponse,
    dependencies=[Depends(verify_service_key)],
)
async def auth_telegram(
    payload: TelegramAuthRequest,
    session: SessionDep,
) -> TokenResponse:
    """Exchange a Telegram identity for a JWT access token."""
    _, token = await AuthService(session).authenticate_telegram(
        telegram_id=payload.telegram_id,
        username=payload.username,
    )
    return TokenResponse(access_token=token)
