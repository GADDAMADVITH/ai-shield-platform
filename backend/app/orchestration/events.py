"""Lightweight orchestration event models.

No event bus is wired in Sprint 7 — these are typed records the orchestrator
emits to an optional sink for logging, testing, and future pub/sub.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.common.enums import AssessmentStatus, ScanStatus


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class OrchestrationEvent:
    """Base orchestration event."""

    scan_id: uuid.UUID
    timestamp: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True, slots=True)
class ScanStarted(OrchestrationEvent):
    project_id: uuid.UUID | None = None
    connection_id: uuid.UUID | None = None
    assessment_count: int = 0
    profile: str | None = None


@dataclass(frozen=True, slots=True)
class AssessmentStarted(OrchestrationEvent):
    assessment_key: str = ""
    assessment_id: uuid.UUID | None = None
    engine_name: str | None = None
    engine_version: str | None = None
    index: int = 0
    total: int = 0


@dataclass(frozen=True, slots=True)
class AssessmentFinished(OrchestrationEvent):
    assessment_key: str = ""
    assessment_id: uuid.UUID | None = None
    status: AssessmentStatus | None = None
    duration_ms: float = 0.0
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ScanFinished(OrchestrationEvent):
    status: ScanStatus = ScanStatus.COMPLETED
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class ScanFailed(OrchestrationEvent):
    error: str = ""
    details: dict[str, Any] = field(default_factory=dict)
