"""Scan execution API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import AssessmentStatus, ScanStatus, Severity
from app.common.pagination import Page


class ScanCreate(BaseModel):
    """Start a new scan against a project connection."""

    connection_id: uuid.UUID
    profile: str = Field(default="standard", min_length=1, max_length=128)


class AssessmentExecutionPublic(BaseModel):
    """Public view of an Assessment row (AssessmentExecution)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID  # catalog id
    assessment_key: str | None = None
    assessment_name: str | None = None
    status: AssessmentStatus
    started_at: datetime | None
    finished_at: datetime | None
    execution_time_ms: int | None
    summary: str | None
    severity: Severity
    risk_score: float | None
    raw_result: dict[str, Any]
    logs: list[Any]
    recommendation: str | None = None
    confidence: float | None = None

    @classmethod
    def from_model(cls, assessment: Any) -> AssessmentExecutionPublic:
        catalog = getattr(assessment, "catalog_entry", None)
        return cls(
            id=assessment.id,
            assessment_id=assessment.assessment_catalog_id,
            assessment_key=getattr(catalog, "slug", None),
            assessment_name=getattr(catalog, "name", None),
            status=assessment.status,
            started_at=assessment.started_at,
            finished_at=assessment.completed_at,
            execution_time_ms=assessment.execution_time_ms,
            summary=assessment.finding_summary,
            severity=assessment.severity,
            risk_score=assessment.score,
            raw_result=dict(assessment.raw_result or {}),
            logs=list(assessment.logs or []),
            recommendation=assessment.recommendation,
            confidence=assessment.confidence,
        )


class ScanSummaryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    overall_score: float
    critical: int
    high: int
    medium: int
    low: int
    passed: int
    failed: int
    total_findings: int
    execution_duration_ms: int


class ScanPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    connection_id: uuid.UUID | None
    initiated_by_id: uuid.UUID | None
    status: ScanStatus
    profile: str
    progress_percent: float
    completed_assessments: int
    failed_assessments: int
    execution_time_ms: int | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    last_updated: datetime
    created_at: datetime
    assessments: list[AssessmentExecutionPublic] = Field(default_factory=list)
    summary: ScanSummaryPublic | None = None

    @classmethod
    def from_model(cls, scan: Any, *, include_details: bool = True) -> ScanPublic:
        assessments: list[AssessmentExecutionPublic] = []
        summary: ScanSummaryPublic | None = None
        if include_details:
            assessments = [
                AssessmentExecutionPublic.from_model(item)
                for item in sorted(
                    getattr(scan, "assessments", None) or [],
                    key=lambda row: row.created_at,
                )
            ]
            if getattr(scan, "summary", None) is not None:
                summary = ScanSummaryPublic.model_validate(scan.summary)

        return cls(
            id=scan.id,
            project_id=scan.project_id,
            connection_id=scan.connection_id,
            initiated_by_id=scan.initiated_by_id,
            status=scan.status,
            profile=scan.profile,
            progress_percent=scan.progress_percent,
            completed_assessments=scan.completed_assessments,
            failed_assessments=scan.failed_assessments,
            execution_time_ms=scan.execution_time_ms,
            error_message=scan.error_message,
            started_at=scan.started_at,
            finished_at=scan.completed_at,
            last_updated=scan.updated_at,
            created_at=scan.created_at,
            assessments=assessments,
            summary=summary,
        )


class ScanListItem(BaseModel):
    """Compact scan row for list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    connection_id: uuid.UUID | None
    status: ScanStatus
    profile: str
    progress_percent: float
    completed_assessments: int
    failed_assessments: int
    execution_time_ms: int | None
    started_at: datetime | None
    finished_at: datetime | None
    last_updated: datetime
    created_at: datetime

    @classmethod
    def from_model(cls, scan: Any) -> ScanListItem:
        return cls(
            id=scan.id,
            project_id=scan.project_id,
            connection_id=scan.connection_id,
            status=scan.status,
            profile=scan.profile,
            progress_percent=scan.progress_percent,
            completed_assessments=scan.completed_assessments,
            failed_assessments=scan.failed_assessments,
            execution_time_ms=scan.execution_time_ms,
            started_at=scan.started_at,
            finished_at=scan.completed_at,
            last_updated=scan.updated_at,
            created_at=scan.created_at,
        )


class ScanList(Page[ScanListItem]):
    pass
