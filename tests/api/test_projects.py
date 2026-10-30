"""Project CRUD tests."""

import pytest
from httpx import AsyncClient

from tests.conftest import make_auth_headers

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def auth(client: AsyncClient) -> dict[str, str]:
    return await make_auth_headers(client, 2001, "proj_user")


async def test_create_project(client: AsyncClient, auth: dict) -> None:
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "Alpha", "description": "first"},
        headers=auth,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Alpha"
    assert body["description"] == "first"
    assert body["id"] > 0


async def test_list_projects(client: AsyncClient, auth: dict) -> None:
    await client.post("/api/v1/projects", json={"name": "P1"}, headers=auth)
    await client.post("/api/v1/projects", json={"name": "P2"}, headers=auth)

    resp = await client.get("/api/v1/projects", headers=auth)
    assert resp.status_code == 200
    assert [p["name"] for p in resp.json()] == ["P1", "P2"]


async def test_get_project(client: AsyncClient, auth: dict) -> None:
    created = (await client.post("/api/v1/projects", json={"name": "Solo"}, headers=auth)).json()
    resp = await client.get(f"/api/v1/projects/{created['id']}", headers=auth)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Solo"


async def test_get_missing_project_404(client: AsyncClient, auth: dict) -> None:
    resp = await client.get("/api/v1/projects/4242", headers=auth)
    assert resp.status_code == 404


async def test_update_project(client: AsyncClient, auth: dict) -> None:
    created = (await client.post("/api/v1/projects", json={"name": "Old"}, headers=auth)).json()
    resp = await client.patch(
        f"/api/v1/projects/{created['id']}",
        json={"name": "New", "description": "added"},
        headers=auth,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"
    assert resp.json()["description"] == "added"


async def test_update_project_empty_name_422(client: AsyncClient, auth: dict) -> None:
    created = (await client.post("/api/v1/projects", json={"name": "Keep"}, headers=auth)).json()
    resp = await client.patch(f"/api/v1/projects/{created['id']}", json={"name": ""}, headers=auth)
    assert resp.status_code == 422


async def test_delete_project(client: AsyncClient, auth: dict) -> None:
    created = (await client.post("/api/v1/projects", json={"name": "Gone"}, headers=auth)).json()
    resp = await client.delete(f"/api/v1/projects/{created['id']}", headers=auth)
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/projects/{created['id']}", headers=auth)
    assert resp.status_code == 404


async def test_projects_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/projects")).status_code == 401
    assert (await client.post("/api/v1/projects", json={"name": "X"})).status_code == 401
