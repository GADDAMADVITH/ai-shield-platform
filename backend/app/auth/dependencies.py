"""Authentication FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_user_by_id
from app.auth.tokens import TokenType, decode_token
from app.common.dependencies import get_db
from app.common.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Resolve the authenticated user from a Bearer access token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Not authenticated")

    payload = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
    try:
        user_id = UUID(str(payload["sub"]))
    except (TypeError, ValueError) as exc:
        raise UnauthorizedError("Invalid token subject") from exc

    user = await get_user_by_id(session, user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise ForbiddenError("User account is inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
