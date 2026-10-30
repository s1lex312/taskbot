"""HTTP client for the Taskbot API with JWT caching and auto-refetch."""

from typing import Any

import httpx


class ApiError(Exception):
    """A non-2xx API response, parsed from the unified error payload."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(f"{status_code} {code}: {message}")
        self.status_code = status_code
        self.code = code
        self.message = message


class ApiClient:
    """Low-level client. Manages tokens per Telegram user."""

    def __init__(self, base_url: str, service_key: str = "") -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=10.0)
        self._service_key = service_key
        self._tokens: dict[int, str] = {}

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    def user_api(self, telegram_id: int, username: str | None) -> "UserApi":
        """Return an API facade bound to one Telegram user. No network I/O."""
        return UserApi(self, telegram_id, username)

    async def get_token(self, telegram_id: int, username: str | None) -> str:
        """Return a cached token or fetch a fresh one."""
        token = self._tokens.get(telegram_id)
        if token is None:
            token = await self.refresh_token(telegram_id, username)
        return token

    async def refresh_token(self, telegram_id: int, username: str | None) -> str:
        """Force-fetch a new token from /auth/telegram and cache it."""
        headers = {}
        if self._service_key:
            headers["X-Service-Key"] = self._service_key
        resp = await self._client.post(
            "/auth/telegram",
            json={"telegram_id": telegram_id, "username": username},
            headers=headers,
        )
        if resp.status_code != httpx.codes.OK:
            raise _error_from(resp)
        token = resp.json()["access_token"]
        self._tokens[telegram_id] = token
        return token

    async def send(self, method: str, path: str, token: str, **kwargs: Any) -> httpx.Response:
        """Send one authorized request."""
        return await self._client.request(
            method, path, headers={"Authorization": f"Bearer {token}"}, **kwargs
        )


def _error_from(resp: httpx.Response) -> ApiError:
    try:
        payload = resp.json()
        error = payload.get("error", {})
        code = error.get("code", "unknown_error")
        message = error.get("message", resp.text[:200])
    except ValueError:
        code, message = "unknown_error", resp.text[:200]
    return ApiError(resp.status_code, code, message)


class UserApi:
    """API facade bound to a Telegram user. Retries once on 401."""

    def __init__(self, client: ApiClient, telegram_id: int, username: str | None) -> None:
        self._client = client
        self._telegram_id = telegram_id
        self._username = username

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        token = await self._client.get_token(self._telegram_id, self._username)
        resp = await self._client.send(method, path, token, **kwargs)
        if resp.status_code == httpx.codes.UNAUTHORIZED:
            # Token expired or revoked: refetch once and retry.
            token = await self._client.refresh_token(self._telegram_id, self._username)
            resp = await self._client.send(method, path, token, **kwargs)
        if resp.status_code >= httpx.codes.BAD_REQUEST:
            raise _error_from(resp)
        if resp.status_code == httpx.codes.NO_CONTENT:
            return None
        return resp.json()

    # ------------------------------------------------------------------ users
    async def get_me(self) -> dict:
        return await self._request("GET", "/users/me")

    # --------------------------------------------------------------- projects
    async def list_projects(self) -> list[dict]:
        return await self._request("GET", "/projects")

    async def create_project(self, name: str, description: str | None = None) -> dict:
        return await self._request(
            "POST", "/projects", json={"name": name, "description": description}
        )

    async def get_project(self, project_id: int) -> dict:
        return await self._request("GET", f"/projects/{project_id}")

    async def delete_project(self, project_id: int) -> None:
        await self._request("DELETE", f"/projects/{project_id}")

    # ------------------------------------------------------------------ tasks
    async def list_tasks(
        self,
        project_id: int,
        status: str | None = None,
        priority: str | None = None,
    ) -> list[dict]:
        """List tasks of a project with optional filters."""
        params = {}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        return await self._request("GET", f"/projects/{project_id}/tasks", params=params)

    async def create_task(
        self,
        project_id: int,
        title: str,
        description: str | None = None,
        priority: str = "medium",
        due_date: str | None = None,
    ) -> dict:
        return await self._request(
            "POST",
            f"/projects/{project_id}/tasks",
            json={
                "title": title,
                "description": description,
                "priority": priority,
                "due_date": due_date,
            },
        )

    async def get_task(self, task_id: int) -> dict:
        return await self._request("GET", f"/tasks/{task_id}")

    async def update_task(self, task_id: int, **fields: Any) -> dict:
        """Partially update a task (title, description, status, priority, due_date)."""
        return await self._request("PATCH", f"/tasks/{task_id}", json=fields)

    async def delete_task(self, task_id: int) -> None:
        await self._request("DELETE", f"/tasks/{task_id}")
