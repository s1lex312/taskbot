"""Shared FastAPI dependencies."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.security import decode_access_token
from api.db.session import get_session
from api.models.user import User
from api.repositories.user import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: CredentialsDep,
    session: SessionDep,
) -> User:
    """Resolve the Bearer JWT to a persisted user, or raise 401."""
    if credentials is None:
        raise _unauthorized("Not authenticated")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise _unauthorized("Invalid or expired token") from exc

    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise _unauthorized("User not found")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
