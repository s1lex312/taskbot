"""Auth endpoint tests."""

import jwt
import pytest
from httpx import AsyncClient

from api.core.config import get_settings
from tests.conftest import make_auth_headers

pytestmark = pytest.mark.asyncio


async def test_auth_telegram_issues_token(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/telegram", json={"telegram_id": 1001, "username": "alice"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"

    settings = get_settings()
    payload = jwt.decode(body["access_token"], settings.jwt_secret, algorithms=[settings.jwt_alg])
    assert payload["sub"] == "1"
    assert "exp" in payload


async def test_auth_same_telegram_id_returns_same_user(client: AsyncClient) -> None:
    headers1 = await make_auth_headers(client, 1002, "bob")
    headers2 = await make_auth_headers(client, 1002, "bob_renamed")

    me1 = await client.get("/api/v1/users/me", headers=headers1)
    me2 = await client.get("/api/v1/users/me", headers=headers2)
    assert me1.json()["id"] == me2.json()["id"]
    assert me2.json()["username"] == "bob_renamed"  # username is synced


async def test_users_me_ok(client: AsyncClient) -> None:
    headers = await make_auth_headers(client, 1003, "carol")
    resp = await client.get("/api/v1/users/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["telegram_id"] == 1003
    assert resp.json()["username"] == "carol"


async def test_users_me_requires_token(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "http_error"


async def test_users_me_rejects_bad_token(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/users/me", headers={"Authorization": "Bearer not-a-token"})
    assert resp.status_code == 401


async def test_auth_validates_payload(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/telegram", json={"telegram_id": 0})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"
