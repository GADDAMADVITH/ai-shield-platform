"""Project API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.enums import ProjectEnvironment, ProjectStatus
from app.common.pagination import Page


class ProjectCreate(BaseModel):
    """Payload for creating a project."""

    name: str = Field(min_length=1, max_length=255)
    environment: ProjectEnvironment
    application_type: str = Field(min_length=1, max_length=128)
    connection_method: str = Field(default="REST API", min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=5000)

    @field_validator("name", "application_type", "connection_method")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty")
        return cleaned

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ProjectUpdate(BaseModel):
    """Partial update payload. Owner cannot be changed."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    environment: ProjectEnvironment | None = None
    application_type: str | None = Field(default=None, min_length=1, max_length=128)
    connection_method: str | None = Field(default=None, min_length=1, max_length=128)
    status: ProjectStatus | None = None

    @field_validator("name", "application_type", "connection_method")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty")
        return cleaned

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ProjectPublic(BaseModel):
    """Public project representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    environment: ProjectEnvironment
    application_type: str
    connection_method: str
    status: ProjectStatus
    description: str | None
    created_at: datetime
    updated_at: datetime


class ProjectList(Page[ProjectPublic]):
    """Paginated project list response."""

    pass
