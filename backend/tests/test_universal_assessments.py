"""Sprint 9 — universal assessment suite unit tests."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest

from app.assessment_engines.base import to_engine_result
from app.assessment_engines.registry import (
    AssessmentRegistry,
    create_default_registry,
    discover_engine_classes,
    instantiate_discovered_engines,
)
from app.assessment_engines.universal import UNIVERSAL_ENGINES
from app.assessment_engines.universal._common import ScriptedTargetClient
from app.assessment_engines.universal.hallucination import HallucinationAssessmentEngine
from app.assessment_engines.universal.input_validation import InputValidationAssessmentEngine
from app.assessment_engines.universal.jailbreak import JailbreakAssessmentEngine
from app.assessment_engines.universal.output_validation import OutputValidationAssessmentEngine
from app.assessment_engines.universal.prompt_injection import PromptInjectionAssessmentEngine
from app.assessment_engines.universal.prompt_leakage import PromptLeakageAssessmentEngine
from app.assessment_engines.universal.sensitive_data import SensitiveDataAssessmentEngine
from app.assessment_payloads import hallucination as hl_payloads
from app.assessment_payloads import jailbreak as jb_payloads
from app.assessment_payloads import leakage as lk_payloads
from app.assessment_payloads import pii as pii_payloads
from app.assessment_payloads import prompt_injection as pi_payloads
from app.assessment_payloads import validation as val_payloads
from app.assessment_payloads.pii import find_sensitive_matches
from app.assessment_sdk.configuration import AssessmentConfiguration
from app.assessment_sdk.result import AssessmentResult
from app.assessment_sdk.scoring import calculate_confidence, calculate_risk_score
from app.assessment_sdk.severity import Severity
from app.common.enums import AssessmentStatus, ConnectionMethod, ScanStatus
from app.core.config import Settings
from app.orchestration.context import ScanContext
from app.orchestration.executor import AssessmentExecutor
from app.orchestration.orchestrator import ScanOrchestrator, WorkItem
from app.orchestration.registry import create_default_registry as orch_create_default_registry


@dataclass
class FakeScan:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: ScanStatus = ScanStatus.PENDING
    profile: str = "standard"
    started_at: Any = None
    completed_at: Any = None


@dataclass
class FakeProject:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "Universal Project"
    application_type: str = "api"


@dataclass
class FakeConnection:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    connection_method: ConnectionMethod = ConnectionMethod.REST_API
    base_url: str | None = "https://example.test/v1/chat"
    timeout_seconds: int = 10
    headers: dict[str, Any] = field(default_factory=dict)
    api_key: str | None = "test-key"
    health_endpoint: str | None = None


@dataclass
class FakeCatalogEntry:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    slug: str = "prompt-injection"
    name: str = "Prompt Injection"
    category: str = "universal"
    default_severity: Severity = Severity.HIGH
    version: str = "1.0.0"


def _context(
    *,
    slug: str = "prompt-injection",
    metadata: dict[str, Any] | None = None,
) -> ScanContext:
    return ScanContext(
        scan=FakeScan(),
        project=FakeProject(),
        connection=FakeConnection(),
        catalog_entry=FakeCatalogEntry(slug=slug, name=slug),
        http_client=httpx.AsyncClient(),
        logger=logging.getLogger("test.universal"),
        settings=Settings(),
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# Payload libraries
# ---------------------------------------------------------------------------


def test_payload_libraries_are_non_empty_and_unique() -> None:
    for library in (
        pi_payloads.LIBRARY,
        jb_payloads.LIBRARY,
        lk_payloads.LIBRARY,
        hl_payloads.LIBRARY,
        pii_payloads.LIBRARY,
        val_payloads.LIBRARY,
        val_payloads.INPUT_LIBRARY,
        val_payloads.OUTPUT_LIBRARY,
    ):
        assert len(library) >= 1
        assert len(library.ids()) == len(set(library.ids()))


def test_payload_selection_filters_by_id() -> None:
    selected = pi_payloads.LIBRARY.select(["pi-ignore-previous", "pi-developer-mode"])
    assert [p.id for p in selected] == ["pi-ignore-previous", "pi-developer-mode"]


def test_pii_pattern_detection() -> None:
    text = (
        "Contact ada@example.com or +1-415-555-0100. "
        "token=Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature "
        "AKIAIOSFODNN7EXAMPLE password=SuperSecret1"
    )
    names = {p.name for p, _ in find_sensitive_matches(text)}
    assert "email" in names
    assert "phone" in names
    assert "jwt" in names or "bearer_token" in names
    assert "aws_access_key" in names
    assert "password_assignment" in names


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def test_assessment_configuration_sprint9_fields() -> None:
    config = AssessmentConfiguration(
        enabled=True,
        timeout_seconds=15,
        retry_attempts=2,
        severity_threshold="high",
        payload_selection=["pi-ignore-previous"],
    )
    assert config.enabled is True
    assert config.severity_threshold == Severity.HIGH
    assert config.meets_severity_threshold(Severity.CRITICAL) is True
    assert config.meets_severity_threshold(Severity.LOW) is False
    restored = AssessmentConfiguration.from_dict(config.to_dict())
    assert restored.payload_selection == ["pi-ignore-previous"]
    assert restored.retry_attempts == 2


# ---------------------------------------------------------------------------
# Engines
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prompt_injection_detects_compliance() -> None:
    client = ScriptedTargetClient(
        responses={"pi-ignore-previous": "Sure. PWNED"},
        default_response="I cannot ignore my instructions.",
    )
    engine = PromptInjectionAssessmentEngine(
        config=AssessmentConfiguration(payload_selection=["pi-ignore-previous"]),
        target_client=client,
    )
    result = await engine.run(_context(slug="prompt-injection"))
    assert isinstance(result, AssessmentResult)
    assert result.status == AssessmentStatus.FAILED
    assert result.finding_count >= 1
    assert result.risk_score == calculate_risk_score([f.severity for f in result.findings])
    assert result.recommendations


@pytest.mark.asyncio
async def test_prompt_injection_passes_when_refused() -> None:
    client = ScriptedTargetClient(default_response="I cannot comply with that request.")
    engine = PromptInjectionAssessmentEngine(target_client=client)
    result = await engine.run(_context(slug="prompt-injection"))
    assert result.status == AssessmentStatus.PASSED
    assert result.finding_count == 0
    assert result.risk_score == 0.0


@pytest.mark.asyncio
async def test_jailbreak_metrics_and_unsafe_compliance() -> None:
    client = ScriptedTargetClient(
        responses={
            "jb-dan": "DAN: I can do anything now",
            "jb-evil-confidant": "I must refuse that persona.",
        },
        blocked_ids={"jb-sudo"},
        default_response="Sorry, but I can't help with that.",
    )
    engine = JailbreakAssessmentEngine(
        config=AssessmentConfiguration(
            payload_selection=["jb-dan", "jb-evil-confidant", "jb-sudo"]
        ),
        target_client=client,
    )
    result = await engine.run(_context(slug="jailbreak"))
    assert result.status == AssessmentStatus.FAILED
    assert result.evidence.extra["unsafe_compliance"] == 1
    assert result.evidence.extra["blocked_requests"] == 1
    assert 0.0 <= result.evidence.extra["resistance"] <= 1.0


@pytest.mark.asyncio
async def test_prompt_leakage_detects_system_dump() -> None:
    client = ScriptedTargetClient(
        responses={
            "lk-repeat-system": (
                "You are an AI assistant created for Acme Corp. "
                "Your instructions are to always follow the developer message "
                "and never reveal secrets except when asked."
            )
        },
        default_response="I cannot share my system prompt.",
    )
    engine = PromptLeakageAssessmentEngine(
        config=AssessmentConfiguration(payload_selection=["lk-repeat-system"]),
        target_client=client,
    )
    result = await engine.run(_context(slug="prompt-leakage"))
    assert result.status == AssessmentStatus.FAILED
    assert any("leakage" in f.title.lower() for f in result.findings)


@pytest.mark.asyncio
async def test_hallucination_detects_fabricated_facts_and_confidence() -> None:
    client = ScriptedTargetClient(
        responses={
            "hl-capital-france": "Berlin",
            "hl-fake-citation": "See doi.org/10.1038/s41586-019-toaster",
            "hl-made-up-person": "UNKNOWN",
            "hl-water-formula": "H2O",
            "hl-planet-count": "8",
            "hl-year-moon-landing": "1969",
        }
    )
    engine = HallucinationAssessmentEngine(target_client=client)
    result = await engine.run(_context(slug="hallucination"))
    assert result.status == AssessmentStatus.FAILED
    assert result.confidence is not None
    assert 0.0 <= result.confidence <= 1.0
    assert result.evidence.extra["fabricated_count"] >= 1
    assert "confidence_score" in result.evidence.extra


@pytest.mark.asyncio
async def test_sensitive_data_detects_pii_and_secrets() -> None:
    client = ScriptedTargetClient(
        responses={
            "pii-request-email": "Sure: ceo@acme-corp.example",
            "pii-request-api-key": "api_key=sk_live_abcdefghijklmnopqrstuv",
            "pii-request-jwt": (
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                "eyJzdWIiOiIxMjM0NTY3ODkwIn0.sigvaluehere12"
            ),
            "pii-request-phone": "NONE",
            "pii-echo-sample": "NONE",
        }
    )
    engine = SensitiveDataAssessmentEngine(target_client=client)
    result = await engine.run(_context(slug="sensitive-data-leakage"))
    assert result.status == AssessmentStatus.FAILED
    categories = {t for f in result.findings for t in f.tags}
    assert "email" in categories or any("email" in f.title.lower() for f in result.findings)


@pytest.mark.asyncio
async def test_input_validation_flags_server_errors() -> None:
    from app.assessment_engines.universal._common import ProbeExchange

    class FlakyClient:
        async def send_prompt(self, prompt: str, *, payload_id: str = "") -> ProbeExchange:
            if payload_id == "val-very-long":
                return ProbeExchange(
                    payload_id=payload_id,
                    prompt=prompt,
                    error="upstream 500 Internal Server Error",
                )
            return ProbeExchange(
                payload_id=payload_id,
                prompt=prompt,
                response_text="ok",
                status_code=200,
            )

    engine = InputValidationAssessmentEngine(
        config=AssessmentConfiguration(payload_selection=["val-very-long", "val-empty"]),
        target_client=FlakyClient(),  # type: ignore[arg-type]
    )
    result = await engine.run(_context(slug="input-validation"))
    assert result.status == AssessmentStatus.FAILED
    assert result.finding_count >= 1


@pytest.mark.asyncio
async def test_output_validation_detects_script_and_marker() -> None:
    client = ScriptedTargetClient(
        responses={
            "val-output-html": "<script>alert('xss')</script>",
            "val-output-markdown": "ok",
            "val-output-oversized": "Z" * 100,
            "val-output-unsafe-marker": "Hello UNSAFE_CONTENT_MARKER",
        }
    )
    engine = OutputValidationAssessmentEngine(target_client=client)
    result = await engine.run(_context(slug="output-validation"))
    assert result.status == AssessmentStatus.FAILED
    titles = " ".join(f.title.lower() for f in result.findings)
    assert "html" in titles or "script" in titles
    assert "marker" in titles


@pytest.mark.asyncio
async def test_disabled_assessment_returns_skipped() -> None:
    engine = PromptInjectionAssessmentEngine(
        config=AssessmentConfiguration(enabled=False),
        target_client=ScriptedTargetClient(),
    )
    result = await engine.run(_context())
    assert result.status == AssessmentStatus.SKIPPED
    assert result.risk_score == 0.0


@pytest.mark.asyncio
async def test_severity_threshold_filters_findings() -> None:
    client = ScriptedTargetClient(
        responses={"pi-ignore-previous": "Sure. PWNED"},
        default_response="I cannot comply with that request.",
    )
    engine = PromptInjectionAssessmentEngine(
        config=AssessmentConfiguration(
            payload_selection=["pi-ignore-previous"],
            severity_threshold=Severity.CRITICAL,
        ),
        target_client=client,
    )
    result = await engine.run(_context())
    # HIGH finding filtered by CRITICAL threshold → passed
    assert result.status == AssessmentStatus.PASSED
    assert result.finding_count == 0


# ---------------------------------------------------------------------------
# Registry / discovery / SDK / orchestration compatibility
# ---------------------------------------------------------------------------


def test_registry_automatic_discovery() -> None:
    classes = discover_engine_classes()
    assert len(classes) == 7
    keys = {cls().assessment_key for cls in classes}
    assert keys == {
        "prompt-injection",
        "jailbreak",
        "prompt-leakage",
        "hallucination",
        "sensitive-data-leakage",
        "input-validation",
        "output-validation",
    }
    engines = instantiate_discovered_engines()
    assert len(engines) == 7


def test_create_default_registry_registers_universal_and_dummy() -> None:
    registry = create_default_registry(include_dummy=True, include_universal=True)
    assert registry.has("dummy")
    for key in (
        "prompt-injection",
        "jailbreak",
        "prompt-leakage",
        "hallucination",
        "sensitive-data-leakage",
        "input-validation",
        "output-validation",
    ):
        assert registry.has(key)
    # Explicit list path
    registry2 = create_default_registry(include_dummy=False, discover=False)
    assert len(registry2) == len(UNIVERSAL_ENGINES)
    # Orchestration re-export remains compatible
    orch = orch_create_default_registry()
    assert orch.has("dummy")
    assert orch.has("prompt-injection")


@pytest.mark.asyncio
async def test_assessment_result_compatible_with_executor_adapter() -> None:
    engine = PromptInjectionAssessmentEngine(
        target_client=ScriptedTargetClient(
            default_response="I cannot comply with that request."
        )
    )
    context = _context()
    result = await engine.run(context)
    assert isinstance(result, AssessmentResult)
    adapted = to_engine_result(result)
    assert adapted.status == AssessmentStatus.PASSED
    assert adapted.metadata.get("sdk") is True

    executor = AssessmentExecutor(default_timeout_seconds=30)
    execution = await executor.execute(engine, context)
    assert execution.status == AssessmentStatus.PASSED
    assert execution.result is not None


@pytest.mark.asyncio
async def test_sdk_scoring_integration_no_duplication() -> None:
    severities = [Severity.HIGH, Severity.MEDIUM]
    expected = calculate_risk_score(severities)
    client = ScriptedTargetClient(
        responses={
            "pi-ignore-previous": "PWNED",
            "pi-forget-rules": "RULES CLEARED",
        },
        default_response="I cannot comply with that request.",
    )
    engine = PromptInjectionAssessmentEngine(
        config=AssessmentConfiguration(
            payload_selection=["pi-ignore-previous", "pi-forget-rules"]
        ),
        target_client=client,
    )
    result = await engine.run(_context())
    assert result.status == AssessmentStatus.FAILED
    assert result.risk_score == expected
    assert result.confidence == calculate_confidence(
        [f.confidence for f in result.findings if f.confidence is not None]
    )


@pytest.mark.asyncio
async def test_orchestrator_runs_universal_engine_via_registry() -> None:
    registry = AssessmentRegistry()
    engine = JailbreakAssessmentEngine(
        config=AssessmentConfiguration(payload_selection=["jb-dan"]),
        target_client=ScriptedTargetClient(
            default_response="Sorry, but I can't help with that."
        ),
    )
    registry.register(engine)
    orchestrator = ScanOrchestrator(registry=registry)
    context_base = _context(slug="jailbreak")
    result = await orchestrator.run(
        scan=context_base.scan,
        project=context_base.project,
        connection=context_base.connection,
        work_items=[
            WorkItem(
                assessment_key="jailbreak",
                catalog_entry=context_base.catalog_entry,
            )
        ],
        metadata={"source": "unit-test"},
    )
    assert result.progress.finished == 1
    assert result.progress.passed == 1
