"""User persistence operations."""

from sqlalchemy import select

from api.models.user import User
from api.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """CRUD gateway for the users table."""

    async def get_by_id(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return await self._session.scalar(stmt)

    async def create(self, telegram_id: int, username: str | None) -> User:
        return await self._save(User(telegram_id=telegram_id, username=username))

    async def update_username(self, user: User, username: str | None) -> User:
        """Sync the stored username with Telegram."""
        user.username = username
        return await self._save(user)
