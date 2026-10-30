"""Shared repository plumbing."""

from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from api.db.base import Base

M = TypeVar("M", bound=Base)


class BaseRepository(Generic[M]):
    """Session handling plus the common save/refresh and patch primitives."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _save(self, entity: M) -> M:
        """Persist the entity and reload server-generated columns."""
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def _apply(self, entity: M, fields: dict) -> M:
        """Set attributes from a dict and persist."""
        for key, value in fields.items():
            setattr(entity, key, value)
        return await self._save(entity)
