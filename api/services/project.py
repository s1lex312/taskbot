"""Project use-cases."""

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.project import Project
from api.repositories.project import ProjectRepository
from api.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Business logic for projects. Owner isolation lives in the repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = ProjectRepository(session)

    async def list_projects(self, owner_id: int) -> list[Project]:
        """List all projects owned by the user."""
        return await self._repo.list_by_owner(owner_id)

    async def create_project(self, owner_id: int, data: ProjectCreate) -> Project:
        """Create a project for the owner."""
        return await self._repo.create(owner_id, data.name, data.description)

    async def get_project(self, project_id: int, owner_id: int) -> Project | None:
        """Return the project if the user owns it, else None."""
        return await self._repo.get(project_id, owner_id)

    async def update_project(
        self, project_id: int, owner_id: int, data: ProjectUpdate
    ) -> Project | None:
        """Partially update a project owned by the user. None if not found."""
        project = await self._repo.get(project_id, owner_id)
        if project is None:
            return None
        return await self._repo.update(project, data.model_dump(exclude_unset=True))

    async def delete_project(self, project_id: int, owner_id: int) -> bool:
        """Delete a project owned by the user. False if not found."""
        project = await self._repo.get(project_id, owner_id)
        if project is None:
            return False
        await self._repo.delete(project)
        return True
