"""Shared pytest fixtures: in-memory SQLite + ASGI test client."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import api.models  # noqa: F401  (register tables on Base.metadata)
from api.db.base import Base
from api.db.session import get_session
from api.main import app


@pytest.fixture
async def session_factory() -> AsyncIterator:
    """Yield an async session factory over a shared in-memory SQLite DB."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    """Yield an HTTP test client with the DB dependency overridden."""

    async def override_get_session() -> AsyncIterator:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


async def make_auth_headers(client: AsyncClient, telegram_id: int, username: str) -> dict[str, str]:
    """Register/login a user and return Authorization headers."""
    resp = await client.post(
        "/api/v1/auth/telegram",
        json={"telegram_id": telegram_id, "username": username},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
