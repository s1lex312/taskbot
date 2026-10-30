"""User endpoints."""

from fastapi import APIRouter

from api.core.dependencies import CurrentUserDep
from api.models.user import User
from api.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_me(current_user: CurrentUserDep) -> User:
    """Return the authenticated user."""
    return current_user
