"""Reusable FastAPI dependencies."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams
from app.db.session import get_db as get_db_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session (re-export for API layers)."""
    async for session in get_db_session():
        yield session


def get_pagination(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginationParams:
    """Parse standard pagination query parameters."""
    return PaginationParams(page=page, page_size=page_size)
