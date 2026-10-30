"""Task endpoints. All data is scoped to the authenticated user."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from api.core.dependencies import CurrentUserDep, SessionDep
from api.models.enums import TaskPriority, TaskStatus
from api.schemas.task import TaskCreate, TaskRead, TaskUpdate
from api.services.task import TaskService

router = APIRouter(tags=["tasks"])

_PROJECT_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
)
_TASK_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")


@router.get("/projects/{project_id}/tasks", response_model=list[TaskRead])
async def list_tasks(
    project_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
    status: Annotated[TaskStatus | None, Query()] = None,
    priority: Annotated[TaskPriority | None, Query()] = None,
) -> list:
    """List tasks of a project, with optional status/priority filters.

    Sorted by due date ascending; tasks without a due date go last.
    """
    tasks = await TaskService(session).list_tasks(
        current_user.id, project_id, status=status, priority=priority
    )
    if tasks is None:
        raise _PROJECT_NOT_FOUND
    return tasks


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: int,
    payload: TaskCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """Create a task in a project owned by the current user."""
    task = await TaskService(session).create_task(current_user.id, project_id, payload)
    if task is None:
        raise _PROJECT_NOT_FOUND
    return task


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, current_user: CurrentUserDep, session: SessionDep):
    """Fetch a single task owned by the current user."""
    task = await TaskService(session).get_task(current_user.id, task_id)
    if task is None:
        raise _TASK_NOT_FOUND
    return task


@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """Partially update a task owned by the current user."""
    task = await TaskService(session).update_task(current_user.id, task_id, payload)
    if task is None:
        raise _TASK_NOT_FOUND
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, current_user: CurrentUserDep, session: SessionDep) -> Response:
    """Delete a task owned by the current user."""
    deleted = await TaskService(session).delete_task(current_user.id, task_id)
    if not deleted:
        raise _TASK_NOT_FOUND
    return Response(status_code=status.HTTP_204_NO_CONTENT)
