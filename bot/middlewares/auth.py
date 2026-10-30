"""Middleware injecting a per-user API facade into handler data."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.services.api_client import ApiClient


class AuthMiddleware(BaseMiddleware):
    """Attach a user-bound UserApi to handler data as `api`.

    The JWT itself is fetched lazily on the first request and transparently
    refreshed by UserApi on 401 responses.
    """

    def __init__(self, api_client: ApiClient) -> None:
        self._api_client = api_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            data["api"] = self._api_client.user_api(user.id, user.username)
        return await handler(event, data)
