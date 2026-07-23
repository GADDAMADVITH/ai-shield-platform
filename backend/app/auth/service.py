"""Authentication business logic."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password, verify_password
from app.auth.revocation import NullRefreshTokenStore, RefreshTokenStore
from app.auth.tokens import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.common.enums import UserRole
from app.common.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    TokenPair,
    UserPublic,
)


def _token_pair_for_user(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        user=UserPublic.model_validate(user),
        tokens=_token_pair_for_user(user),
    )


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID | str) -> User | None:
    uid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
    result = await session.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()


async def register_user(session: AsyncSession, payload: RegisterRequest) -> AuthResponse:
    email = payload.email.lower()
    existing = await get_user_by_email(session, email)
    if existing is not None:
        raise ConflictError("Email already exists")

    user = User(
        email=email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=UserRole.MEMBER,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return _auth_response(user)


async def authenticate_user(session: AsyncSession, payload: LoginRequest) -> AuthResponse:
    user = await get_user_by_email(session, payload.email.lower())
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise ForbiddenError("User account is inactive")
    return _auth_response(user)


async def refresh_tokens(session: AsyncSession, refresh_token: str) -> AuthResponse:
    payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
    user = await get_user_by_id(session, payload["sub"])
    if user is None:
        raise UnauthorizedError("Invalid refresh token")
    if not user.is_active:
        raise ForbiddenError("User account is inactive")
    return _auth_response(user)


async def logout_user(
    *,
    refresh_token: str | None = None,
    store: RefreshTokenStore | None = None,
) -> None:
    """Stateless logout with a hook for future refresh-token revocation."""
    token_store = store or NullRefreshTokenStore()
    if refresh_token:
        try:
            payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        except UnauthorizedError:
            # Idempotent logout: ignore invalid/expired refresh tokens.
            return
        jti = payload.get("jti")
        if isinstance(jti, str) and jti:
            await token_store.revoke(jti)
