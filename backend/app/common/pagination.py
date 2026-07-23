"""Pagination primitives shared by future list endpoints."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for offset/limit pagination."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class Page(BaseModel, Generic[T]):
    """Generic paginated payload."""

    items: list[T]
    meta: PageMeta

    @classmethod
    def from_items(
        cls,
        items: list[T],
        *,
        total: int,
        params: PaginationParams,
    ) -> Page[T]:
        total_pages = max(1, (total + params.page_size - 1) // params.page_size) if total else 0
        return cls(
            items=items,
            meta=PageMeta(
                page=params.page,
                page_size=params.page_size,
                total=total,
                total_pages=total_pages,
            ),
        )
