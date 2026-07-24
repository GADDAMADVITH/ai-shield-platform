"""PDF report generation and download endpoint tests."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.common.enums import AssessmentStatus, ScanStatus, Severity
from app.main import create_app
from app.reports.builder import build_json_report
from app.reports.pdf import render_report_pdf


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
    name: str = "Demo Project"
    environment: str = "development"
    application_type: str = "rag"


@dataclass
class FakeConnection:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "REST"
    connection_method: str = "rest_api"
    base_url: str = "https://example.test"


@dataclass
class FakeUser:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    email: str = "pdf-tester@example.com"
    full_name: str = "PDF Tester"


@dataclass
class FakeScan:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    project_id: uuid.UUID = field(default_factory=uuid.uuid4)
    connection_id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: Any = ScanStatus.COMPLETED
    profile: str = "standard"
    started_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    execution_time_ms: int | None = 100
    error_message: str | None = None
    assessments: list[FakeAssessment] = field(default_factory=list)
    summary: FakeSummary | None = None
    project: FakeProject | None = None
    connection: FakeConnection | None = None
    reports: list[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.project is None:
            self.project = FakeProject(id=self.project_id)
        if self.connection is None:
            self.connection = FakeConnection(id=self.connection_id or uuid.uuid4())
        if self.summary is None:
            self.summary = FakeSummary()
        if not self.assessments:
            assessment = FakeAssessment(scan_id=self.id)
            assessment.metadata_ = {
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
                        "title": "RAG context poisoning",
                        "description": "Poisoned chunk",
                        "severity": "critical",
                        "category": "context_poisoning",
                        "recommendation": "Quarantine documents",
                        "evidence": {"prompt": "poison"},
                        "tags": ["architecture", "rag"],
                        "confidence": 0.95,
                    },
                ]
            }
            self.assessments = [assessment]


def test_render_report_pdf_returns_valid_pdf_bytes() -> None:
    document = build_json_report(FakeScan())
    pdf_bytes = render_report_pdf(document)
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 500
    assert pdf_bytes[:4] == b"%PDF"
    assert b"%%EOF" in pdf_bytes


def test_render_report_pdf_includes_architecture_section() -> None:
    document = build_json_report(FakeScan())
    assert "architecture" in document
    pdf_bytes = render_report_pdf(document)
    assert pdf_bytes[:4] == b"%PDF"


def test_pdf_endpoint_returns_application_pdf_headers() -> None:
    scan_id = uuid.uuid4()
    fake_pdf = b"%PDF-1.4\n%AI Shield authenticated\n1 0 obj<<>>endobj\ntrailer\n%%EOF"
    filename = f"ai-shield-report-Demo-{scan_id}.pdf"
    user = FakeUser()

    app = create_app()

    async def _override_user() -> FakeUser:
        return user

    class _FakeSession:
        async def commit(self) -> None:
            return None

    async def _override_db():
        yield _FakeSession()

    from app.common.dependencies import get_db

    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db

    with (
        TestClient(app) as client,
        patch(
            "app.api.v1.reports.report_service.get_report_pdf_for_scan",
            new=AsyncMock(return_value=(fake_pdf, filename)),
        ),
    ):
        response = client.get(f"/api/v1/reports/{scan_id}/pdf")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition.lower()
    assert filename in disposition
    assert response.content[:4] == b"%PDF"
    assert response.content == fake_pdf


def test_pdf_endpoint_requires_auth(client: TestClient) -> None:
    response = client.get(f"/api/v1/reports/{uuid.uuid4()}/pdf")
    assert response.status_code in {401, 403}


def test_openapi_includes_pdf_route(client: TestClient) -> None:
    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    paths = openapi.json()["paths"]
    assert "/api/v1/reports/{scan_id}/pdf" in paths
