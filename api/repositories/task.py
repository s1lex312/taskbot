"""Task persistence operations. Ownership is enforced via the project join."""

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.enums import TaskPriority, TaskStatus
from api.models.project import Project
from api.models.task import Task


class TaskRepository:
    """CRUD gateway for the tasks table with owner isolation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_project(
        self,
        project_id: int,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ) -> list[Task]:
        """List tasks of a project, optionally filtered, due date first.

        Tasks without a due date sort last; ties break on id.
        """
        stmt = select(Task).where(Task.project_id == project_id)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        stmt = stmt.order_by(Task.due_date.is_(None), Task.due_date, Task.id)
        return list(await self._session.scalars(stmt))

    async def get_for_owner(self, task_id: int, owner_id: int) -> Task | None:
        """Fetch a task only if its project belongs to the owner."""
        stmt = (
            select(Task)
            .join(Project, Task.project_id == Project.id)
            .where(Task.id == task_id, Project.owner_id == owner_id)
        )
        return await self._session.scalar(stmt)

    async def create(
        self,
        project_id: int,
        title: str,
        description: str | None,
        priority: TaskPriority,
        due_date: date | None,
    ) -> Task:
        task = Task(
            project_id=project_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
        )
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def update(self, task: Task, fields: dict) -> Task:
        for key, value in fields.items():
            setattr(task, key, value)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self._session.execute(delete(Task).where(Task.id == task.id))
        await self._session.commit()
