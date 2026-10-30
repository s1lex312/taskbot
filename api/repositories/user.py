"""User persistence operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.user import User


class UserRepository:
    """CRUD gateway for the users table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Fetch a user by their Telegram id."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        return await self._session.scalar(stmt)

    async def create(self, telegram_id: int, username: str | None) -> User:
        user = User(telegram_id=telegram_id, username=username)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def update_username(self, user: User, username: str | None) -> User:
        """Sync the stored username with Telegram."""
        user.username = username
        await self._session.commit()
        await self._session.refresh(user)
        return user
