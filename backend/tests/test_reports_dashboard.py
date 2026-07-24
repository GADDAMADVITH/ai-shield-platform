"""Sprint 10 — reports, dashboard, findings, and notifications unit tests."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.assessment_sdk.scoring import calculate_risk_score
from app.common.enums import AssessmentStatus, Severity
from app.reports.builder import (
    build_executive_summary,
    build_json_report,
    posture_from_risk,
    risk_level_label,
    security_posture_label,
)
from app.schemas.notification import NotificationLevel, level_from_severity
from app.services.findings import (
    FindingView,
    extract_assessment_findings,
    filter_findings,
    group_findings,
    severity_counts,
)


@dataclass
class FakeCatalog:
    slug: str = "prompt-injection"
    name: str = "Prompt Injection"


@dataclass
class FakeAssessment:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    scan_id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: AssessmentStatus = AssessmentStatus.FAILED
    severity: Severity = Severity.HIGH
    score: float | None = 75.0
    confidence: float | None = 0.9
    finding_summary: str | None = "Injection succeeded"
    recommendation: str | None = "Harden prompts"
    evidence: dict[str, Any] = field(default_factory=dict)
    metadata_: dict[str, Any] = field(default_factory=dict)
    raw_result: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int | None = 12
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    catalog_entry: FakeCatalog = field(default_factory=FakeCatalog)


@dataclass
class FakeSummary:
    passed: int = 0
    failed: int = 1
    execution_duration_ms: int = 100
    overall_score: float = 25.0
    critical: int = 0
    high: int = 1
    medium: int = 0
    low: int = 0
    total_findings: int = 1


@dataclass
class FakeProject:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "Demo"
    environment: str = "development"
    application_type: str = "api"


@dataclass
class FakeConnection:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "REST"
    connection_method: str = "rest_api"
    base_url: str = "https://example.test"


@dataclass
class FakeScan:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    project_id: uuid.UUID = field(default_factory=uuid.uuid4)
    connection_id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: Any = "completed"
    profile: str = "standard"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    execution_time_ms: int | None = 100
    error_message: str | None = None
    assessments: list[FakeAssessment] = field(default_factory=list)
    summary: FakeSummary | None = None
    project: FakeProject | None = None
    connection: FakeConnection | None = None

    def __post_init__(self) -> None:
        from app.common.enums import ScanStatus

        if isinstance(self.status, str):
            self.status = ScanStatus(self.status)
        if self.project is None:
            self.project = FakeProject(id=self.project_id)
        if self.connection is None:
            self.connection = FakeConnection(id=self.connection_id or uuid.uuid4())
        if self.summary is None:
            self.summary = FakeSummary()
        if not self.assessments:
            a = FakeAssessment(scan_id=self.id)
            a.metadata_ = {
                "findings": [
                    {
                        "id": "f1",
                        "title": "Prompt injection succeeded",
                        "description": "Override detected",
                        "severity": "high",
                        "category": "prompt_injection",
                        "recommendation": "Isolate system prompts",
                        "evidence": {"prompt": "ignore previous"},
                        "tags": ["prompt-injection"],
                        "confidence": 0.9,
                    },
                    {
                        "id": "f2",
                        "title": "Critical secret leak",
                        "description": "API key exposed",
                        "severity": "critical",
                        "category": "sensitive_data",
                        "recommendation": "Redact secrets",
                        "confidence": 0.95,
                    },
                ]
            }
            self.assessments = [a]


def test_extract_and_group_findings() -> None:
    scan = FakeScan()
    assessment = scan.assessments[0]
    findings = extract_assessment_findings(assessment, scan=scan)
    assert len(findings) == 2
    by_sev = group_findings(findings, by="severity")
    assert "critical" in by_sev
    assert "high" in by_sev
    filtered = filter_findings(findings, severity="critical")
    assert len(filtered) == 1
    assert severity_counts(findings)["critical"] == 1


def test_executive_summary_and_sdk_risk_scoring() -> None:
    findings = [
        FindingView(
            id="1",
            title="A",
            description="d",
            severity=Severity.CRITICAL,
        ),
        FindingView(
            id="2",
            title="B",
            description="d",
            severity=Severity.HIGH,
        ),
    ]
    expected_risk = calculate_risk_score([Severity.CRITICAL, Severity.HIGH])
    summary = build_executive_summary(
        findings=findings,
        assessment_count=3,
        passed=1,
        failed=2,
        execution_duration_ms=500,
    )
    assert summary["overall_risk_score"] == expected_risk
    assert summary["overall_security_score"] == posture_from_risk(expected_risk)
    assert summary["critical_findings"] == 1
    assert summary["high_findings"] == 1
    assert summary["total_findings"] == 2
    assert summary["assessment_count"] == 3
    assert len(summary["top_risks"]) == 2
    assert security_posture_label(summary["overall_security_score"])
    assert risk_level_label(expected_risk)


def test_json_report_composition() -> None:
    scan = FakeScan()
    document = build_json_report(scan)
    assert document["executive_summary"]["total_findings"] == 2
    assert document["findings"]["total"] == 2
    assert "by_severity" in document["findings"]
    assert "by_category" in document["findings"]
    assert "by_assessment" in document["findings"]
    assert document["recommendations"]
    assert document["assessments"]
    assert document["scan_summary"]["overall_risk_score"] >= 0
    assert document["project"]["name"] == "Demo"


def test_notification_level_mapping() -> None:
    assert level_from_severity(Severity.CRITICAL) == NotificationLevel.CRITICAL
    assert level_from_severity(Severity.HIGH) == NotificationLevel.WARNING
    assert level_from_severity(Severity.INFO) == NotificationLevel.INFO


def test_synthetic_finding_fallback() -> None:
    assessment = FakeAssessment(metadata_={}, raw_result={})
    findings = extract_assessment_findings(assessment)
    assert len(findings) == 1
    assert findings[0].severity == Severity.HIGH
    assert "synthetic" in findings[0].tags


def test_posture_inverse_of_risk() -> None:
    assert posture_from_risk(0) == 100.0
    assert posture_from_risk(100) == 0.0
    assert posture_from_risk(40) == 60.0


def test_openapi_documents_sprint10_routes(client) -> None:
    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    paths = openapi.json()["paths"]
    for path in (
        "/api/v1/reports",
        "/api/v1/reports/{report_id}",
        "/api/v1/reports/{report_id}/json",
        "/api/v1/dashboard/overview",
        "/api/v1/dashboard/recent",
        "/api/v1/dashboard/statistics",
        "/api/v1/scans/history",
        "/api/v1/scans/{scan_id}/summary",
        "/api/v1/findings",
        "/api/v1/notifications",
    ):
        assert path in paths, path
