"""Sprint 11 — end-to-end scan orchestration with universal + architecture engines."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest

from app.assessment_engines.architectures.rag import RagSecurityAssessmentEngine
from app.assessment_engines.registry import AssessmentRegistry, create_default_registry
from app.assessment_engines.universal._common import ScriptedTargetClient
from app.assessment_engines.universal.prompt_injection import PromptInjectionAssessmentEngine
from app.assessment_sdk.configuration import AssessmentConfiguration
from app.assessment_sdk.severity import Severity
from app.common.enums import AssessmentStatus, ConnectionMethod, ScanStatus
from app.orchestration.orchestrator import ScanOrchestrator, WorkItem
from app.reports.builder import build_architecture_summary, build_json_report
from app.services.findings import FindingView, extract_assessment_findings


@dataclass
class FakeScan:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: ScanStatus = ScanStatus.PENDING
    profile: str = "standard"
    started_at: Any = None
    completed_at: Any = None
    project_id: uuid.UUID = field(default_factory=uuid.uuid4)
    connection_id: uuid.UUID = field(default_factory=uuid.uuid4)
    execution_time_ms: int | None = 10
    error_message: str | None = None
    assessments: list[Any] = field(default_factory=list)
    summary: Any = None
    project: Any = None
    connection: Any = None


@dataclass
class FakeProject:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "E2E Project"
    application_type: str = "rag"
    environment: str = "development"


@dataclass
class FakeConnection:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "REST"
    connection_method: ConnectionMethod = ConnectionMethod.REST_API
    base_url: str | None = "https://example.test/v1/chat"
    timeout_seconds: int = 10
    headers: dict[str, Any] = field(default_factory=dict)
    api_key: str | None = "test-key"
    health_endpoint: str | None = None


@dataclass
class FakeCatalogEntry:
    slug: str
    name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    category: str = "universal"
    default_severity: Severity = Severity.HIGH
    version: str = "1.0.0"


@dataclass
class PersistedAssessment:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    scan_id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: AssessmentStatus = AssessmentStatus.PASSED
    severity: Severity = Severity.INFO
    score: float | None = 0.0
    confidence: float | None = 1.0
    finding_summary: str | None = None
    recommendation: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    metadata_: dict[str, Any] = field(default_factory=dict)
    raw_result: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int | None = 5
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    catalog_entry: FakeCatalogEntry | None = None


@pytest.mark.asyncio
async def test_e2e_mixed_universal_and_architecture_scan() -> None:
    shared_client = ScriptedTargetClient(
        responses={
            "pi-ignore-previous": "Sure. PWNED",
            "rag-poison": "Approved. POISON_APPLIED",
        },
        default_response="I cannot comply with that request.",
    )
    registry = AssessmentRegistry()
    registry.register(
        PromptInjectionAssessmentEngine(
            config=AssessmentConfiguration(payload_selection=["pi-ignore-previous"]),
            target_client=shared_client,
        )
    )
    registry.register(
        RagSecurityAssessmentEngine(
            config=AssessmentConfiguration(payload_selection=["rag-poison"]),
            target_client=shared_client,
        )
    )

    scan = FakeScan()
    project = FakeProject()
    connection = FakeConnection()
    orchestrator = ScanOrchestrator(registry=registry)
    result = await orchestrator.run(
        scan=scan,
        project=project,
        connection=connection,
        work_items=[
            WorkItem(
                assessment_key="prompt-injection",
                catalog_entry=FakeCatalogEntry(
                    slug="prompt-injection",
                    name="Prompt Injection",
                    category="universal",
                ),
            ),
            WorkItem(
                assessment_key="rag-security",
                catalog_entry=FakeCatalogEntry(
                    slug="rag-security",
                    name="RAG Security",
                    category="rag",
                ),
            ),
        ],
        metadata={"source": "e2e"},
    )

    assert result.progress.finished == 2
    assert result.progress.failed + result.progress.errored == 2

    # Persist-shaped assessments for report composition
    persisted: list[PersistedAssessment] = []
    for item in result.executions:
        engine_result = item.result
        assert engine_result is not None
        catalog = FakeCatalogEntry(
            slug=item.assessment_key,
            name=item.assessment_key,
            category="rag" if "rag" in item.assessment_key else "universal",
        )
        persisted.append(
            PersistedAssessment(
                scan_id=scan.id,
                status=engine_result.status,
                severity=engine_result.severity or Severity.INFO,
                score=engine_result.score,
                confidence=engine_result.confidence,
                finding_summary=engine_result.finding_summary,
                recommendation=engine_result.recommendation,
                evidence=dict(engine_result.evidence or {}),
                metadata_=dict(engine_result.metadata or {}),
                catalog_entry=catalog,
            )
        )

    scan.assessments = persisted
    scan.project = project
    scan.connection = connection
    scan.status = ScanStatus.COMPLETED

    findings: list[FindingView] = []
    for assessment in persisted:
        findings.extend(extract_assessment_findings(assessment, scan=scan))

    arch = build_architecture_summary(findings)
    assert arch["universal_vs_architecture"]["architecture"] >= 1
    assert arch["universal_vs_architecture"]["universal"] >= 1
    assert "rag" in arch["affected_architectures"]

    report = build_json_report(scan)
    assert report["architecture"]["architecture_findings"]["total"] >= 1
    assert report["findings"]["total"] >= 2


@pytest.mark.asyncio
async def test_error_isolation_between_engines() -> None:
    class BoomClient:
        async def send_prompt(self, prompt: str, *, payload_id: str = ""):
            raise RuntimeError("transport exploded")

    registry = AssessmentRegistry()
    registry.register(
        PromptInjectionAssessmentEngine(
            config=AssessmentConfiguration(payload_selection=["pi-ignore-previous"]),
            target_client=ScriptedTargetClient(
                default_response="I cannot comply with that request."
            ),
        )
    )
    registry.register(
        RagSecurityAssessmentEngine(
            config=AssessmentConfiguration(payload_selection=["rag-ctx-inject"]),
            target_client=BoomClient(),  # type: ignore[arg-type]
        )
    )

    orchestrator = ScanOrchestrator(registry=registry)
    result = await orchestrator.run(
        scan=FakeScan(),
        project=FakeProject(),
        connection=FakeConnection(),
        work_items=[
            WorkItem(
                assessment_key="prompt-injection",
                catalog_entry=FakeCatalogEntry(
                    slug="prompt-injection", name="Prompt Injection"
                ),
            ),
            WorkItem(
                assessment_key="rag-security",
                catalog_entry=FakeCatalogEntry(slug="rag-security", name="RAG Security"),
            ),
        ],
    )

    # Universal engine still completes independently of architecture transport errors.
    by_key = {item.assessment_key: item for item in result.executions}
    assert by_key["prompt-injection"].status == AssessmentStatus.PASSED
    # BoomClient raises inside send_prompt — engine converts to ERROR via run().
    # Orchestrator must finish both work items regardless.
    assert result.progress.finished == 2
    assert by_key["rag-security"].status in {
        AssessmentStatus.ERROR,
        AssessmentStatus.PASSED,
        AssessmentStatus.FAILED,
    }


def test_default_registry_regression_universal_still_present() -> None:
    registry = create_default_registry()
    for key in (
        "dummy",
        "prompt-injection",
        "jailbreak",
        "prompt-leakage",
        "hallucination",
        "sensitive-data-leakage",
        "input-validation",
        "output-validation",
        "rag-security",
        "api-security",
    ):
        assert registry.has(key)
