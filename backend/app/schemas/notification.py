"""Notification API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import NotificationType, Severity
from app.common.pagination import Page


class NotificationLevel(StrEnum):
    """UI-facing notification urgency (Sprint 10)."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


def level_from_severity(severity: Severity) -> NotificationLevel:
    if severity in {Severity.CRITICAL}:
        return NotificationLevel.CRITICAL
    if severity in {Severity.HIGH, Severity.MEDIUM}:
        return NotificationLevel.WARNING
    return NotificationLevel.INFO


class NotificationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID | None = None
    title: str
    description: str
    category: NotificationType
    severity: Severity
    level: NotificationLevel
    is_read: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, notification: Any) -> NotificationPublic:
        return cls(
            id=notification.id,
            user_id=notification.user_id,
            project_id=notification.project_id,
            title=notification.title,
            description=notification.description,
            category=notification.category,
            severity=notification.severity,
            level=level_from_severity(notification.severity),
            is_read=notification.is_read,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
        )


class NotificationList(Page[NotificationPublic]):
    pass


class NotificationMarkRead(BaseModel):
    is_read: bool = True


class NotificationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    category: NotificationType = NotificationType.SYSTEM
    severity: Severity = Severity.INFO
    project_id: uuid.UUID | None = None
