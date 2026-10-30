"""Cross-user data isolation tests."""

import pytest
from httpx import AsyncClient

from tests.conftest import make_auth_headers

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def alice(client: AsyncClient) -> dict[str, str]:
    return await make_auth_headers(client, 4001, "alice")


@pytest.fixture
async def bob(client: AsyncClient) -> dict[str, str]:
    return await make_auth_headers(client, 4002, "bob")


@pytest.fixture
async def alice_project(client: AsyncClient, alice: dict) -> dict:
    resp = await client.post("/api/v1/projects", json={"name": "A"}, headers=alice)
    return resp.json()


async def test_bob_cannot_see_alices_projects(
    client: AsyncClient, alice_project: dict, bob: dict
) -> None:
    resp = await client.get("/api/v1/projects", headers=bob)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_bob_gets_404_on_alices_project(
    client: AsyncClient, alice_project: dict, bob: dict
) -> None:
    pid = alice_project["id"]
    assert (await client.get(f"/api/v1/projects/{pid}", headers=bob)).status_code == 404
    assert (
        await client.patch(f"/api/v1/projects/{pid}", json={"name": "X"}, headers=bob)
    ).status_code == 404
    assert (await client.delete(f"/api/v1/projects/{pid}", headers=bob)).status_code == 404


async def test_bob_cannot_touch_alices_tasks(
    client: AsyncClient, alice: dict, alice_project: dict, bob: dict
) -> None:
    pid = alice_project["id"]

    # Listing and creating inside someone else's project -> 404.
    assert (await client.get(f"/api/v1/projects/{pid}/tasks", headers=bob)).status_code == 404
    assert (
        await client.post(f"/api/v1/projects/{pid}/tasks", json={"title": "X"}, headers=bob)
    ).status_code == 404

    task = (
        await client.post(f"/api/v1/projects/{pid}/tasks", json={"title": "Secret"}, headers=alice)
    ).json()

    # Reading, updating, deleting somebody else's task -> 404.
    assert (await client.get(f"/api/v1/tasks/{task['id']}", headers=bob)).status_code == 404
    assert (
        await client.patch(f"/api/v1/tasks/{task['id']}", json={"status": "done"}, headers=bob)
    ).status_code == 404
    assert (await client.delete(f"/api/v1/tasks/{task['id']}", headers=bob)).status_code == 404

    # And the owner still sees the task untouched.
    resp = await client.get(f"/api/v1/tasks/{task['id']}", headers=alice)
    assert resp.json()["status"] == "todo"


async def test_deleting_project_cascades_tasks(
    client: AsyncClient, alice: dict, alice_project: dict
) -> None:
    pid = alice_project["id"]
    task = (
        await client.post(f"/api/v1/projects/{pid}/tasks", json={"title": "T"}, headers=alice)
    ).json()
    assert (await client.delete(f"/api/v1/projects/{pid}", headers=alice)).status_code == 204
    assert (await client.get(f"/api/v1/tasks/{task['id']}", headers=alice)).status_code == 404
