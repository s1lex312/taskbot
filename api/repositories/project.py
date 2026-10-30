"""Project persistence operations. All queries are owner-scoped."""

from sqlalchemy import delete, select

from api.models.project import Project
from api.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """CRUD gateway for the projects table with built-in owner isolation."""

    async def list_by_owner(self, owner_id: int) -> list[Project]:
        """Return all projects of an owner, oldest first."""
        stmt = select(Project).where(Project.owner_id == owner_id).order_by(Project.id)
        return list(await self._session.scalars(stmt))

    async def get(self, project_id: int, owner_id: int) -> Project | None:
        """Fetch a project only if it belongs to the owner."""
        stmt = select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
        return await self._session.scalar(stmt)

    async def create(self, owner_id: int, name: str, description: str | None) -> Project:
        return await self._save(Project(owner_id=owner_id, name=name, description=description))

    async def update(self, project: Project, fields: dict) -> Project:
        return await self._apply(project, fields)

    async def delete(self, project: Project) -> None:
        """Delete a project and its tasks (cascade)."""
        await self._session.execute(delete(Project).where(Project.id == project.id))
        await self._session.commit()
