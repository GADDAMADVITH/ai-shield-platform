"""Connection API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.enums import ConnectionMethod, ConnectionStatus
from app.common.pagination import Page


class ConnectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    connection_method: ConnectionMethod
    base_url: str | None = Field(default=None, max_length=2048)
    health_endpoint: str | None = Field(default=None, max_length=2048)
    api_key: str | None = Field(default=None, max_length=2048)
    headers: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=10, ge=1, le=120)
    verify_ssl: bool = True
    playwright_entry_url: str | None = Field(default=None, max_length=2048)
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name is required")
        return cleaned

    @field_validator("base_url", "health_endpoint", "playwright_entry_url", "notes", "api_key")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def validate_method_requirements(self) -> ConnectionCreate:
        method = self.connection_method
        if method == ConnectionMethod.PLAYWRIGHT and not (
            self.playwright_entry_url or self.base_url
        ):
            raise ValueError("playwright_entry_url or base_url is required for Playwright")
        if method in {
            ConnectionMethod.REST_API,
            ConnectionMethod.OPENAPI,
            ConnectionMethod.LOCALHOST,
            ConnectionMethod.WEBHOOK,
        } and not (self.base_url or self.health_endpoint):
            raise ValueError("base_url or health_endpoint is required for this connection method")
        if method == ConnectionMethod.SDK and not (self.base_url or self.api_key):
            raise ValueError("base_url or api_key is required for SDK connections")
        return self


class ConnectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    connection_method: ConnectionMethod | None = None
    base_url: str | None = Field(default=None, max_length=2048)
    health_endpoint: str | None = Field(default=None, max_length=2048)
    api_key: str | None = Field(default=None, max_length=2048)
    headers: dict[str, Any] | None = None
    timeout_seconds: int | None = Field(default=None, ge=1, le=120)
    verify_ssl: bool | None = None
    playwright_entry_url: str | None = Field(default=None, max_length=2048)
    notes: str | None = Field(default=None, max_length=5000)
    status: ConnectionStatus | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name cannot be empty")
        return cleaned

    @field_validator("base_url", "health_endpoint", "playwright_entry_url", "notes", "api_key")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ConnectionPublic(BaseModel):
    """Public connection representation (API key redacted)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    connection_method: ConnectionMethod
    base_url: str | None
    health_endpoint: str | None
    api_key_set: bool = False
    headers: dict[str, Any]
    timeout_seconds: int
    verify_ssl: bool
    playwright_entry_url: str | None
    notes: str | None
    status: ConnectionStatus
    last_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, connection: Any) -> ConnectionPublic:
        return cls(
            id=connection.id,
            project_id=connection.project_id,
            name=connection.name,
            connection_method=connection.connection_method,
            base_url=connection.base_url,
            health_endpoint=connection.health_endpoint,
            api_key_set=bool(connection.api_key),
            headers=connection.headers or {},
            timeout_seconds=connection.timeout_seconds,
            verify_ssl=connection.verify_ssl,
            playwright_entry_url=connection.playwright_entry_url,
            notes=connection.notes,
            status=connection.status,
            last_verified_at=connection.last_verified_at,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
        )


class ConnectionList(Page[ConnectionPublic]):
    pass


class ConnectionTestResponse(BaseModel):
    reachable: bool
    status_code: int | None
    response_time_ms: int
    message: str
    timestamp: datetime
    connection: ConnectionPublic
