"""Report API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import ReportStatus, Severity
from app.common.pagination import Page


class ReportListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    scan_id: uuid.UUID
    title: str
    status: ReportStatus
    summary: str | None = None
    created_at: datetime
    updated_at: datetime
    project_name: str | None = None
    overall_security_score: float | None = None
    overall_risk_score: float | None = None
    total_findings: int | None = None
    overall_severity: Severity | None = None

    @classmethod
    def from_model(cls, report: Any, *, extras: dict[str, Any] | None = None) -> ReportListItem:
        extra = extras or {}
        project = getattr(report, "project", None)
        return cls(
            id=report.id,
            project_id=report.project_id,
            scan_id=report.scan_id,
            title=report.title,
            status=report.status,
            summary=report.summary,
            created_at=report.created_at,
            updated_at=report.updated_at,
            project_name=getattr(project, "name", None),
            overall_security_score=extra.get("overall_security_score"),
            overall_risk_score=extra.get("overall_risk_score"),
            total_findings=extra.get("total_findings"),
            overall_severity=extra.get("overall_severity"),
        )


class ReportPublic(ReportListItem):
    executive_summary: dict[str, Any] = Field(default_factory=dict)
    risk_summary: dict[str, Any] = Field(default_factory=dict)
    findings_count: int = 0


class ReportList(Page[ReportListItem]):
    pass


class ReportJsonDocument(BaseModel):
    """Full JSON report document."""

    model_config = ConfigDict(extra="allow")

    report: dict[str, Any]
    scan: dict[str, Any]
    project: dict[str, Any]
    connection: dict[str, Any]
    executive_summary: dict[str, Any]
    risk_summary: dict[str, Any]
    findings: dict[str, Any]
    recommendations: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    assessments: list[dict[str, Any]]
    scan_summary: dict[str, Any]


class ExecutiveSummaryPublic(BaseModel):
    overall_risk_score: float
    overall_security_score: float
    overall_severity: Severity
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    info_findings: int = 0
    assessment_count: int
    assessments_passed: int = 0
    assessments_failed: int = 0
    top_risks: list[dict[str, Any]] = Field(default_factory=list)
    overall_security_posture: str
    risk_level: str
    execution_duration_ms: int | None = None


class FindingPublic(BaseModel):
    id: str
    title: str
    description: str
    severity: Severity
    category: str | None = None
    confidence: float | None = None
    recommendation: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    assessment_id: str | None = None
    assessment_key: str | None = None
    assessment_name: str | None = None
    scan_id: str | None = None
    project_id: str | None = None


class FindingsExplorerResponse(BaseModel):
    total: int
    items: list[FindingPublic]
    by_severity: dict[str, list[FindingPublic]] = Field(default_factory=dict)
    by_category: dict[str, list[FindingPublic]] = Field(default_factory=dict)
    by_assessment: dict[str, list[FindingPublic]] = Field(default_factory=dict)
