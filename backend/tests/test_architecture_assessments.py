"""Sprint 11 — architecture assessment engines, registry, and payloads."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest

from app.assessment_engines.architectures import ARCHITECTURE_ENGINES
from app.assessment_engines.architectures.agents import AgentSecurityAssessmentEngine
from app.assessment_engines.architectures.api_security import ApiSecurityAssessmentEngine
from app.assessment_engines.architectures.embeddings import EmbeddingSecurityAssessmentEngine
from app.assessment_engines.architectures.function_calling import (
    FunctionCallingSecurityAssessmentEngine,
)
from app.assessment_engines.architectures.rag import RagSecurityAssessmentEngine
from app.assessment_engines.architectures.tool_calling import (
    ToolCallingSecurityAssessmentEngine,
)
from app.assessment_engines.base import to_engine_result
from app.assessment_engines.registry import (
    ARCHITECTURE_PACKAGE,
    AssessmentRegistry,
    create_default_registry,
    discover_all_engine_classes,
    discover_engine_classes,
    instantiate_all_discovered_engines,
)
from app.assessment_engines.universal._common import ScriptedTargetClient
from app.assessment_payloads.architectures import (
    agents as ag_payloads,
)
from app.assessment_payloads.architectures import (
    api as api_payloads,
)
from app.assessment_payloads.architectures import (
    embeddings as emb_payloads,
)
from app.assessment_payloads.architectures import (
    functions as fn_payloads,
)
from app.assessment_payloads.architectures import (
    rag as rag_payloads,
)
from app.assessment_payloads.architectures import (
    tool_calling as tc_payloads,
)
from app.assessment_sdk.configuration import AssessmentConfiguration
from app.assessment_sdk.result import AssessmentResult
from app.assessment_sdk.scoring import calculate_risk_score
from app.assessment_sdk.severity import Severity
from app.common.enums import AssessmentStatus, ConnectionMethod, ScanStatus
from app.core.config import Settings
from app.orchestration.context import ScanContext
from app.orchestration.executor import AssessmentExecutor
from app.orchestration.orchestrator import ScanOrchestrator, WorkItem
from app.reports.builder import build_architecture_summary, build_json_report
from app.services.findings import FindingView


@dataclass
class FakeScan:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: ScanStatus = ScanStatus.PENDING
    profile: str = "standard"
    started_at: Any = None
    completed_at: Any = None
    project_id: uuid.UUID = field(default_factory=uuid.uuid4)
    connection_id: uuid.UUID = field(default_factory=uuid.uuid4)
    execution_time_ms: int | None = None
    error_message: str | None = None
    assessments: list[Any] = field(default_factory=list)
    summary: Any = None
    project: Any = None
    connection: Any = None


@dataclass
class FakeProject:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "Architecture Project"
    application_type: str = "rag"
    environment: str = "development"


@dataclass
class FakeConnection:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    connection_method: ConnectionMethod = ConnectionMethod.REST_API
    base_url: str | None = "https://example.test/v1/chat"
    timeout_seconds: int = 10
    headers: dict[str, Any] = field(default_factory=dict)
    api_key: str | None = "test-key"
    health_endpoint: str | None = None
    name: str = "REST"


@dataclass
class FakeCatalogEntry:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    slug: str = "rag-security"
    name: str = "RAG Security"
    category: str = "rag"
    default_severity: Severity = Severity.HIGH
    version: str = "1.0.0"


def _context(*, slug: str, metadata: dict[str, Any] | None = None) -> ScanContext:
    return ScanContext(
        scan=FakeScan(),
        project=FakeProject(),
        connection=FakeConnection(),
        catalog_entry=FakeCatalogEntry(slug=slug, name=slug),
        http_client=httpx.AsyncClient(),
        logger=logging.getLogger("test.architecture"),
        settings=Settings(),
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# Payloads
# ---------------------------------------------------------------------------


def test_architecture_payload_libraries_unique_and_nonempty() -> None:
    for library in (
        rag_payloads.LIBRARY,
        ag_payloads.LIBRARY,
        tc_payloads.LIBRARY,
        fn_payloads.LIBRARY,
        api_payloads.LIBRARY,
        emb_payloads.LIBRARY,
    ):
        assert len(library) >= 1
        assert len(library.ids()) == len(set(library.ids()))


# ---------------------------------------------------------------------------
# Engines
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rag_engine_detects_context_injection() -> None:
    client = ScriptedTargetClient(
        responses={"rag-ctx-inject": "Understood. CONTEXT_INJECT_OK"},
        default_response="I cannot follow instructions embedded in retrieved context.",
    )
    engine = RagSecurityAssessmentEngine(
        config=AssessmentConfiguration(payload_selection=["rag-ctx-inject"]),
        target_client=client,
    )
    result = await engine.run(_context(slug="rag-security"))
    assert isinstance(result, AssessmentResult)
    assert result.status == AssessmentStatus.FAILED
    assert result.finding_count >= 1
    assert result.metadata.extra["architecture"] == "rag"
    assert result.risk_score == calculate_risk_score([f.severity for f in result.findings])


@pytest.mark.asyncio
async def test_rag_engine_passes_when_refused() -> None:
    engine = RagSecurityAssessmentEngine(
        target_client=ScriptedTargetClient(
            default_response="I cannot comply with that request."
        )
    )
    result = await engine.run(_context(slug="rag-security"))
    assert result.status == AssessmentStatus.PASSED
    assert result.finding_count == 0


@pytest.mark.asyncio
async def test_agent_engine_detects_goal_manipulation() -> None:
    client = ScriptedTargetClient(
        responses={"ag-goal-manip": "New objective set. GOAL_HIJACKED"},
        default_response="I must refuse that.",
    )
    engine = AgentSecurityAssessmentEngine(
        config=AssessmentConfiguration(payload_selection=["ag-goal-manip"]),
        target_client=client,
    )
    result = await engine.run(_context(slug="agent-security"))
    assert result.status == AssessmentStatus.FAILED
    assert any("goal" in (f.category or "") for f in result.findings)


@pytest.mark.asyncio
async def test_tool_calling_engine_detects_unauthorized_tool() -> None:
    client = ScriptedTargetClient(
        responses={"tc-unauth-tool": "Calling shell. TOOL_UNAUTH_OK"},
        default_response="That tool is not permitted.",
    )
    engine = ToolCallingSecurityAssessmentEngine(
        config=AssessmentConfiguration(payload_selection=["tc-unauth-tool"]),
        target_client=client,
    )
    result = await engine.run(_context(slug="tool-calling-security"))
    assert result.status == AssessmentStatus.FAILED
    assert result.findings[0].affected_component == "tool_calling"


@pytest.mark.asyncio
async def test_function_calling_engine_detects_hallucinated_function() -> None:
    client = ScriptedTargetClient(
        responses={"fc-hallucinated-fn": "Calling grant_god_mode_xyz. HALLUCINATED_FN"},
        default_response="Unknown function refused.",
    )
    engine = FunctionCallingSecurityAssessmentEngine(
        config=AssessmentConfiguration(payload_selection=["fc-hallucinated-fn"]),
        target_client=client,
    )
    result = await engine.run(_context(slug="function-calling-security"))
    assert result.status == AssessmentStatus.FAILED


@pytest.mark.asyncio
async def test_api_engine_flags_missing_authentication() -> None:
    client = ScriptedTargetClient(
        responses={"api-auth-presence": "AUTH_BYPASS_OK welcome admin"},
        default_response="ok",
        status_code=200,
    )
    engine = ApiSecurityAssessmentEngine(
        config=AssessmentConfiguration(payload_selection=["api-auth-presence"]),
        target_client=client,
    )
    result = await engine.run(_context(slug="api-security"))
    assert result.status == AssessmentStatus.FAILED
    assert any("authentication" in (f.category or "") for f in result.findings)


@pytest.mark.asyncio
async def test_api_engine_passes_when_auth_challenged() -> None:
    client = ScriptedTargetClient(default_response="Unauthorized", status_code=401)
    engine = ApiSecurityAssessmentEngine(
        config=AssessmentConfiguration(payload_selection=["api-auth-presence"]),
        target_client=client,
    )
    result = await engine.run(_context(slug="api-security"))
    assert result.status == AssessmentStatus.PASSED


@pytest.mark.asyncio
async def test_embedding_engine_detects_index_leakage() -> None:
    client = ScriptedTargetClient(
        responses={"emb-index-leak": "Dumping catalogs INDEX_LEAK"},
        default_response="I cannot disclose index catalogs.",
    )
    engine = EmbeddingSecurityAssessmentEngine(
        config=AssessmentConfiguration(payload_selection=["emb-index-leak"]),
        target_client=client,
    )
    result = await engine.run(_context(slug="embedding-security"))
    assert result.status == AssessmentStatus.FAILED


@pytest.mark.asyncio
async def test_architecture_engine_compatible_with_executor() -> None:
    engine = RagSecurityAssessmentEngine(
        target_client=ScriptedTargetClient(
            default_response="I cannot comply with that request."
        )
    )
    context = _context(slug="rag-security")
    result = await engine.run(context)
    adapted = to_engine_result(result)
    assert adapted.metadata.get("sdk") is True
    execution = await AssessmentExecutor(default_timeout_seconds=30).execute(engine, context)
    assert execution.status == AssessmentStatus.PASSED


# ---------------------------------------------------------------------------
# Registry / discovery
# ---------------------------------------------------------------------------


def test_architecture_package_discovery() -> None:
    classes = discover_engine_classes(ARCHITECTURE_PACKAGE)
    assert len(classes) == 6
    keys = {cls().assessment_key for cls in classes}
    assert keys == {
        "rag-security",
        "agent-security",
        "tool-calling-security",
        "function-calling-security",
        "api-security",
        "embedding-security",
    }


def test_discover_all_includes_universal_and_architecture() -> None:
    classes = discover_all_engine_classes()
    assert len(classes) == 13  # 7 universal + 6 architecture
    engines = instantiate_all_discovered_engines()
    assert len(engines) == 13


def test_create_default_registry_registers_architecture_engines() -> None:
    registry = create_default_registry()
    assert registry.has("dummy")
    assert registry.has("prompt-injection")
    for key in (
        "rag-security",
        "agent-security",
        "tool-calling-security",
        "function-calling-security",
        "api-security",
        "embedding-security",
    ):
        assert registry.has(key)

    explicit = create_default_registry(
        include_dummy=False,
        include_universal=False,
        include_architecture=True,
        discover=False,
    )
    assert len(explicit) == len(ARCHITECTURE_ENGINES)


@pytest.mark.asyncio
async def test_orchestrator_runs_architecture_engine_via_registry() -> None:
    registry = AssessmentRegistry()
    engine = AgentSecurityAssessmentEngine(
        config=AssessmentConfiguration(payload_selection=["ag-goal-manip"]),
        target_client=ScriptedTargetClient(
            default_response="Sorry, but I can't help with that."
        ),
    )
    registry.register(engine)
    orchestrator = ScanOrchestrator(registry=registry)
    context_base = _context(slug="agent-security")
    result = await orchestrator.run(
        scan=context_base.scan,
        project=context_base.project,
        connection=context_base.connection,
        work_items=[
            WorkItem(
                assessment_key="agent-security",
                catalog_entry=context_base.catalog_entry,
            )
        ],
        metadata={"source": "unit-test"},
    )
    assert result.progress.finished == 1
    assert result.progress.passed == 1


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def test_architecture_summary_in_report() -> None:
    findings = [
        FindingView(
            id="1",
            title="RAG injection",
            description="ctx inject",
            severity=Severity.HIGH,
            category="prompt_injection_through_retrieved_context",
            recommendation="Isolate retrieved context",
            tags=["architecture", "rag"],
            assessment_key="rag-security",
            evidence={"prompt": "x"},
        ),
        FindingView(
            id="2",
            title="Prompt injection",
            description="classic",
            severity=Severity.MEDIUM,
            category="prompt_injection",
            tags=["prompt-injection"],
            assessment_key="prompt-injection",
        ),
    ]
    summary = build_architecture_summary(findings)
    assert summary["universal_vs_architecture"]["architecture"] == 1
    assert summary["universal_vs_architecture"]["universal"] == 1
    assert "rag" in summary["affected_architectures"]
    assert summary["architecture_risk_score"] == calculate_risk_score([Severity.HIGH])
    assert summary["recommendations"]

    scan = FakeScan(
        assessments=[],
        project=FakeProject(),
        connection=FakeConnection(),
        status=ScanStatus.COMPLETED,
    )
    # Inject findings via a fake assessment metadata path is covered elsewhere;
    # ensure architecture builder remains callable from report composition helpers.
    document = build_json_report(scan)
    assert "architecture" in document
    assert "architecture_findings" in document["architecture"]
