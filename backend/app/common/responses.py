"""Standard API response envelopes."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class MessageResponse(BaseModel):
    message: str


class DataResponse(BaseModel, Generic[T]):
    """Successful single-resource response wrapper."""

    data: T


class SuccessResponse(BaseModel):
    success: bool = Field(default=True)
    message: str | None = None
