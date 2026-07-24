"""Health and readiness schemas."""

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["healthy"])


class ReadinessResponse(BaseModel):
    status: str = Field(examples=["ready", "not_ready"])
    checks: dict[str, Any] = Field(default_factory=dict)
