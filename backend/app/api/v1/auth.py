"""Authentication API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.auth.service import authenticate_user, logout_user, refresh_tokens, register_user
from app.common.dependencies import get_db
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    UserPublic,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        409: {"description": "Email already exists"},
        422: {"description": "Validation error"},
    },
)
async def register(
    payload: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Create a user account and return access/refresh tokens."""
    return await register_user(session, payload)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password",
    responses={
        401: {"description": "Invalid credentials"},
        403: {"description": "Inactive account"},
        422: {"description": "Validation error"},
    },
)
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Authenticate a user and return access/refresh tokens."""
    return await authenticate_user(session, payload)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Refresh access token",
    responses={
        401: {"description": "Invalid or expired refresh token"},
        403: {"description": "Inactive account"},
        422: {"description": "Validation error"},
    },
)
async def refresh(
    payload: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Issue a new token pair from a valid refresh token."""
    return await refresh_tokens(session, payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout (stateless JWT)",
    responses={
        422: {"description": "Validation error"},
    },
)
async def logout(payload: LogoutRequest = LogoutRequest()) -> MessageResponse:
    """Client-side logout. Optionally accepts a refresh token for future revocation."""
    await logout_user(refresh_token=payload.refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current authenticated user",
    responses={
        401: {"description": "Missing or invalid access token"},
        403: {"description": "Inactive account"},
    },
)
async def me(current_user: CurrentUser) -> UserPublic:
    """Return the currently authenticated user profile."""
    return UserPublic.model_validate(current_user)
