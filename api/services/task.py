"""Task use-cases."""

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.enums import TaskPriority, TaskStatus
from api.models.task import Task
from api.repositories.project import ProjectRepository
from api.repositories.task import TaskRepository
from api.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """Business logic for tasks. All operations are owner-scoped."""

    def __init__(self, session: AsyncSession) -> None:
        self._tasks = TaskRepository(session)
        self._projects = ProjectRepository(session)

    async def list_tasks(
        self,
        owner_id: int,
        project_id: int,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ) -> list[Task] | None:
        """List tasks of a project. None if the project is not the user's."""
        if await self._projects.get(project_id, owner_id) is None:
            return None
        return await self._tasks.list_by_project(project_id, status, priority)

    async def create_task(self, owner_id: int, project_id: int, data: TaskCreate) -> Task | None:
        """Create a task in a project. None if the project is not the user's."""
        if await self._projects.get(project_id, owner_id) is None:
            return None
        return await self._tasks.create(
            project_id, data.title, data.description, data.priority, data.due_date
        )

    async def get_task(self, owner_id: int, task_id: int) -> Task | None:
        """Return the task if the user owns its project, else None."""
        return await self._tasks.get_for_owner(task_id, owner_id)

    async def update_task(self, owner_id: int, task_id: int, data: TaskUpdate) -> Task | None:
        """Partially update a task owned by the user. None if not found."""
        task = await self._tasks.get_for_owner(task_id, owner_id)
        if task is None:
            return None
        return await self._tasks.update(task, data.model_dump(exclude_unset=True))

    async def delete_task(self, owner_id: int, task_id: int) -> bool:
        """Delete a task owned by the user. False if not found."""
        task = await self._tasks.get_for_owner(task_id, owner_id)
        if task is None:
            return False
        await self._tasks.delete(task)
        return True
