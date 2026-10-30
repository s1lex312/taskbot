"""Task CRUD, filter and sorting tests."""

import pytest
from httpx import AsyncClient

from tests.conftest import make_auth_headers

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def auth(client: AsyncClient) -> dict[str, str]:
    return await make_auth_headers(client, 3001, "task_user")


@pytest.fixture
async def project(client: AsyncClient, auth: dict) -> dict:
    resp = await client.post("/api/v1/projects", json={"name": "W"}, headers=auth)
    return resp.json()


async def _create(client: AsyncClient, auth: dict, project_id: int, **fields) -> dict:
    resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json=fields, headers=auth)
    assert resp.status_code == 201
    return resp.json()


async def test_create_task_defaults(client: AsyncClient, auth: dict, project: dict) -> None:
    task = await _create(client, auth, project["id"], title="T1")
    assert task["status"] == "todo"
    assert task["priority"] == "medium"
    assert task["due_date"] is None


async def test_list_tasks_sorted_by_due_date(
    client: AsyncClient, auth: dict, project: dict
) -> None:
    await _create(client, auth, project["id"], title="no-date")
    await _create(client, auth, project["id"], title="later", due_date="2026-12-01")
    await _create(client, auth, project["id"], title="sooner", due_date="2026-11-01")

    resp = await client.get(f"/api/v1/projects/{project['id']}/tasks", headers=auth)
    assert [t["title"] for t in resp.json()] == ["sooner", "later", "no-date"]


async def test_filter_by_status_and_priority(
    client: AsyncClient, auth: dict, project: dict
) -> None:
    a = await _create(client, auth, project["id"], title="A", priority="high")
    await _create(client, auth, project["id"], title="B", priority="low")
    await client.patch(f"/api/v1/tasks/{a['id']}", json={"status": "done"}, headers=auth)

    resp = await client.get(f"/api/v1/projects/{project['id']}/tasks?priority=high", headers=auth)
    assert [t["title"] for t in resp.json()] == ["A"]

    resp = await client.get(f"/api/v1/projects/{project['id']}/tasks?status=done", headers=auth)
    assert [t["title"] for t in resp.json()] == ["A"]

    resp = await client.get(
        f"/api/v1/projects/{project['id']}/tasks?status=todo&priority=low",
        headers=auth,
    )
    assert [t["title"] for t in resp.json()] == ["B"]


async def test_invalid_filter_value_422(client: AsyncClient, auth: dict, project: dict) -> None:
    resp = await client.get(f"/api/v1/projects/{project['id']}/tasks?status=banana", headers=auth)
    assert resp.status_code == 422


async def test_get_task(client: AsyncClient, auth: dict, project: dict) -> None:
    task = await _create(client, auth, project["id"], title="Solo")
    resp = await client.get(f"/api/v1/tasks/{task['id']}", headers=auth)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Solo"


async def test_update_task(client: AsyncClient, auth: dict, project: dict) -> None:
    task = await _create(client, auth, project["id"], title="Old")
    resp = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"status": "in_progress", "priority": "high", "due_date": "2026-11-15"},
        headers=auth,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "in_progress"
    assert body["priority"] == "high"
    assert body["due_date"] == "2026-11-15"
    assert body["title"] == "Old"  # untouched


async def test_delete_task(client: AsyncClient, auth: dict, project: dict) -> None:
    task = await _create(client, auth, project["id"], title="Gone")
    resp = await client.delete(f"/api/v1/tasks/{task['id']}", headers=auth)
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/tasks/{task['id']}", headers=auth)
    assert resp.status_code == 404


async def test_task_in_missing_project_404(client: AsyncClient, auth: dict) -> None:
    resp = await client.post("/api/v1/projects/9999/tasks", json={"title": "X"}, headers=auth)
    assert resp.status_code == 404
    resp = await client.get("/api/v1/projects/9999/tasks", headers=auth)
    assert resp.status_code == 404


async def test_description_length_limit(
    client: AsyncClient, auth: dict, project: dict
) -> None:
    ok = await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "X", "description": "d" * 2000},
        headers=auth,
    )
    assert ok.status_code == 201

    too_long = await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "X", "description": "d" * 2001},
        headers=auth,
    )
    assert too_long.status_code == 422

    task = await _create(client, auth, project["id"], title="Patch me")
    resp = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"description": "d" * 2001},
        headers=auth,
    )
    assert resp.status_code == 422


async def test_task_validation(client: AsyncClient, auth: dict, project: dict) -> None:
    resp = await client.post(
        f"/api/v1/projects/{project['id']}/tasks", json={"title": ""}, headers=auth
    )
    assert resp.status_code == 422
    resp = await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "X", "priority": "urgent"},
        headers=auth,
    )
    assert resp.status_code == 422
    resp = await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "X", "due_date": "not-a-date"},
        headers=auth,
    )
    assert resp.status_code == 422


async def test_tasks_require_auth(client: AsyncClient, project: dict) -> None:
    assert (await client.get("/api/v1/tasks/1")).status_code == 401
    assert (await client.get(f"/api/v1/projects/{project['id']}/tasks")).status_code == 401
