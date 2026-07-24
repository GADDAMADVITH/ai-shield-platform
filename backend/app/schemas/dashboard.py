"""Dashboard and analytics API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.common.enums import ScanStatus, Severity


class DashboardOverview(BaseModel):
    total_projects: int
    total_scans: int
    successful_scans: int
    failed_scans: int
    average_risk_score: float
    average_security_score: float
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    total_findings: int
    overall_security_posture: str
    overall_severity: Severity
    latest_activity: list[dict[str, Any]] = Field(default_factory=list)


class DashboardRecentScan(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    project_name: str | None = None
    status: ScanStatus
    profile: str
    overall_security_score: float | None = None
    overall_risk_score: float | None = None
    total_findings: int = 0
    critical: int = 0
    high: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class DashboardRecentResponse(BaseModel):
    items: list[DashboardRecentScan]
    notifications: list[dict[str, Any]] = Field(default_factory=list)


class SeverityDistribution(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class RiskAnalytics(BaseModel):
    overall_risk_score: float
    average_risk_score: float
    average_security_score: float
    highest_risk_scan: dict[str, Any] | None = None
    risk_trend: list[dict[str, Any]] = Field(default_factory=list)
    assessment_distribution: dict[str, int] = Field(default_factory=dict)
    severity_distribution: SeverityDistribution
    scan_status_distribution: dict[str, int] = Field(default_factory=dict)


class DashboardStatistics(BaseModel):
    overview: DashboardOverview
    risk: RiskAnalytics
    severity_distribution: SeverityDistribution
    assessment_results: list[dict[str, Any]] = Field(default_factory=list)
    latest_findings: list[dict[str, Any]] = Field(default_factory=list)


class ScanHistoryItem(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    project_name: str | None = None
    environment: str | None = None
    status: ScanStatus
    profile: str
    overall_security_score: float | None = None
    overall_risk_score: float | None = None
    total_findings: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    execution_time_ms: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
