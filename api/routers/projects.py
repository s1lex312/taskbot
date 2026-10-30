"""Project endpoints. All data is scoped to the authenticated user."""

from fastapi import APIRouter, HTTPException, Response, status

from api.core.dependencies import CurrentUserDep, SessionDep
from api.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from api.services.project import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])

_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


@router.get("", response_model=list[ProjectRead])
async def list_projects(current_user: CurrentUserDep, session: SessionDep) -> list:
    """List projects of the current user."""
    return await ProjectService(session).list_projects(current_user.id)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, current_user: CurrentUserDep, session: SessionDep):
    """Create a new project for the current user."""
    return await ProjectService(session).create_project(current_user.id, payload)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: int, current_user: CurrentUserDep, session: SessionDep):
    """Fetch a single project owned by the current user."""
    project = await ProjectService(session).get_project(project_id, current_user.id)
    if project is None:
        raise _NOT_FOUND
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """Partially update a project owned by the current user."""
    project = await ProjectService(session).update_project(project_id, current_user.id, payload)
    if project is None:
        raise _NOT_FOUND
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int, current_user: CurrentUserDep, session: SessionDep
) -> Response:
    """Delete a project owned by the current user."""
    deleted = await ProjectService(session).delete_project(project_id, current_user.id)
    if not deleted:
        raise _NOT_FOUND
    return Response(status_code=status.HTTP_204_NO_CONTENT)
