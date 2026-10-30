"""Authentication use-cases."""

from sqlalchemy.ext.asyncio import AsyncSession

from api.core.security import create_access_token
from api.models.user import User
from api.repositories.user import UserRepository


class AuthService:
    """Telegram-based authentication: get-or-create user, issue JWT."""

    def __init__(self, session: AsyncSession) -> None:
        self._users = UserRepository(session)

    async def authenticate_telegram(
        self, telegram_id: int, username: str | None
    ) -> tuple[User, str]:
        """Return (user, access_token), creating the user on first login."""
        user = await self._users.get_by_telegram_id(telegram_id)
        if user is None:
            user = await self._users.create(telegram_id, username)
        elif user.username != username:
            user = await self._users.update_username(user, username)

        return user, create_access_token(user.id)
