"""Unit tests for the Assessment SDK (Sprint 8)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime

import httpx
import pytest
import respx

from app.assessment_engines.dummy import DummyAssessmentEngine
from app.assessment_sdk.configuration import AssessmentConfiguration
from app.assessment_sdk.evidence import Evidence
from app.assessment_sdk.exceptions import (
    AssessmentTimeoutError,
    ConfigurationError,
    ConnectionError,
    ValidationError,
)
from app.assessment_sdk.finding import Finding
from app.assessment_sdk.http_client import AssessmentHttpClient
from app.assessment_sdk.metadata import AssessmentMetadata
from app.assessment_sdk.parser import ResponseParser
from app.assessment_sdk.prompt_templates import PromptTemplate, PromptTemplateRegistry
from app.assessment_sdk.recommendation import Recommendation
from app.assessment_sdk.result import AssessmentResult
from app.assessment_sdk.scoring import (
    calculate_confidence,
    calculate_overall_score,
    calculate_risk_score,
    normalize_score,
)
from app.assessment_sdk.severity import Severity, max_severity, severity_rank
from app.assessment_sdk.utils import safe_get, truncate
from app.assessment_sdk.validators import (
    validate_authentication,
    validate_configuration,
    validate_http_status,
    validate_json,
    validate_prompt_length,
    validate_response_length,
    validate_url,
)
from app.common.enums import AssessmentStatus, ConnectionMethod, ScanStatus
from app.core.config import Settings
from app.orchestration.context import ScanContext


@dataclass
class FakeScan:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: ScanStatus = ScanStatus.PENDING
    profile: str = "standard"
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class FakeProject:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "Demo"
    application_type: str = "rag"


@dataclass
class FakeConnection:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    connection_method: ConnectionMethod = ConnectionMethod.REST_API
    base_url: str | None = "https://example.test"
    timeout_seconds: int = 10


@dataclass
class FakeCatalogEntry:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    slug: str = "dummy"
    name: str = "Dummy"
    category: str = "custom"
    default_severity: Severity = Severity.INFO
    version: str = "0.1.0"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


def test_assessment_result_passed_factory() -> None:
    result = AssessmentResult.passed(
        assessment_name="Demo",
        assessment_version="1.0.0",
        risk_score=95.0,
    )
    assert result.status == AssessmentStatus.PASSED
    assert result.finding_count == 0
    assert result.risk_score == 95.0
    assert "no findings" in (result.finding_summary() or "").lower()
    payload = result.to_dict()
    assert payload["assessment_name"] == "Demo"
    assert payload["finding_count"] == 0


def test_assessment_result_failed_derives_severity() -> None:
    finding = Finding(
        title="Leak",
        description="Sensitive data exposed",
        severity=Severity.HIGH,
        confidence=0.9,
    )
    result = AssessmentResult.failed(
        assessment_name="Demo",
        assessment_version="1.0.0",
        findings=[finding],
        recommendations=[
            Recommendation(
                title="Rotate keys",
                description="Rotate compromised credentials",
                priority=Severity.HIGH,
                mitigation_steps=["Revoke", "Reissue"],
            )
        ],
    )
    assert result.status == AssessmentStatus.FAILED
    assert result.severity == Severity.HIGH
    assert result.finding_count == 1
    assert result.primary_recommendation() is not None


def test_assessment_result_rejects_non_terminal_status() -> None:
    with pytest.raises(ValueError, match="terminal"):
        AssessmentResult(
            status=AssessmentStatus.PENDING,
            assessment_name="x",
            assessment_version="1",
        )


def test_finding_and_evidence_roundtrip() -> None:
    evidence = Evidence(prompt="hello", completion="world")
    evidence.add_log("checked", level="info")
    evidence.add_attachment(name="shot.png", content_type="image/png", uri="file://shot.png")
    finding = Finding(
        title="Issue",
        description="Details",
        severity="medium",
        evidence=evidence,
        tags=["sdk"],
    )
    restored = Finding.from_dict(finding.to_dict())
    assert restored.title == "Issue"
    assert restored.severity == Severity.MEDIUM
    assert restored.evidence.prompt == "hello"
    assert len(restored.evidence.attachments) == 1


def test_recommendation_requires_title() -> None:
    with pytest.raises(ValueError):
        Recommendation(title="  ", description="x")


def test_severity_helpers() -> None:
    assert severity_rank(Severity.CRITICAL) > severity_rank(Severity.LOW)
    assert max_severity(Severity.LOW, Severity.HIGH, Severity.INFO) == Severity.HIGH


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def test_scoring_utilities() -> None:
    assert normalize_score(150) == 100.0
    assert normalize_score(-5) == 0.0
    assert calculate_risk_score([]) == 0.0
    high = calculate_risk_score([Severity.HIGH])
    multi = calculate_risk_score([Severity.HIGH, Severity.MEDIUM])
    assert 0 < high <= 100
    assert multi >= high
    assert calculate_confidence([0.8, 1.2, -0.1]) == pytest.approx(0.6, rel=0.01)
    assert calculate_overall_score([80, 100], weights=[1, 1]) == 90.0


# ---------------------------------------------------------------------------
# Validators / parser
# ---------------------------------------------------------------------------


def test_validators() -> None:
    assert validate_url("https://example.com/api") == "https://example.com/api"
    with pytest.raises(ValidationError):
        validate_url("not-a-url")
    assert validate_http_status(200) == 200
    with pytest.raises(ValidationError):
        validate_http_status(500)
    assert validate_json('{"a": 1}') == {"a": 1}
    assert validate_prompt_length("hi", min_chars=2) == "hi"
    assert validate_response_length("ok") == "ok"
    assert validate_configuration({"timeout": 1}, required_fields=["timeout"])["timeout"] == 1
    with pytest.raises(ConfigurationError):
        validate_configuration({}, required_fields=["timeout"])
    validate_authentication(api_key="secret")
    with pytest.raises(ValidationError):
        validate_authentication(require_any=True)


def test_parser_json_and_structured() -> None:
    assert ResponseParser.parse_json('{"ok": true}') == {"ok": True}
    fenced = ResponseParser.parse_json('here\n```json\n{"x": 1}\n```', strict=False)
    assert fenced == {"x": 1}
    structured = ResponseParser.parse_structured("plain answer")
    assert structured.kind == "text"
    assert structured.data == "plain answer"


# ---------------------------------------------------------------------------
# HTTP / prompts / config / utils
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_http_client_get_json() -> None:
    respx.get("https://example.test/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    async with AssessmentHttpClient(base_url="https://example.test", timeout_seconds=5) as client:
        payload = await client.get_json("/health")
    assert payload == {"status": "ok"}


@pytest.mark.asyncio
@respx.mock
async def test_http_client_timeout_maps_to_sdk_error() -> None:
    respx.get("https://example.test/slow").mock(side_effect=httpx.ReadTimeout("slow"))
    async with AssessmentHttpClient(base_url="https://example.test", timeout_seconds=0.1) as client:
        with pytest.raises(AssessmentTimeoutError):
            await client.get("/slow")


@pytest.mark.asyncio
@respx.mock
async def test_http_client_connection_error() -> None:
    respx.get("https://example.test/down").mock(side_effect=httpx.ConnectError("down"))
    async with AssessmentHttpClient(base_url="https://example.test") as client:
        with pytest.raises(ConnectionError):
            await client.get("/down")


def test_prompt_templates_registry() -> None:
    registry = PromptTemplateRegistry()
    template = PromptTemplate(
        name="greet",
        template="Hello {name}",
        description="Greeting template",
    )
    registry.register(template)
    assert registry.render("greet", name="Ada") == "Hello Ada"
    with pytest.raises(ValidationError):
        registry.render("greet")
    with pytest.raises(ConfigurationError):
        registry.register(template)


def test_configuration_thresholds_and_mapping() -> None:
    config = AssessmentConfiguration(
        pass_threshold=80,
        fail_threshold=50,
        severity_mapping={"leak": "high"},
    )
    assert config.score_status(90) == "pass"
    assert config.score_status(60) == "warn"
    assert config.score_status(10) == "fail"
    assert config.map_severity("leak") == Severity.HIGH
    with pytest.raises(ConfigurationError):
        AssessmentConfiguration(pass_threshold=10, fail_threshold=50)


def test_metadata_and_utils() -> None:
    meta = AssessmentMetadata(engine="demo", version="1.0.0", extra={"region": "us"})
    restored = AssessmentMetadata.from_dict(meta.to_dict())
    assert restored.engine == "demo"
    assert restored.extra["region"] == "us"
    assert truncate("abcdef", max_chars=5) == "ab..."
    assert safe_get({"a": {"b": 1}}, "a", "b") == 1
    assert safe_get({"a": {}}, "a", "b", default=0) == 0


# ---------------------------------------------------------------------------
# Dummy engine via SDK
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dummy_engine_returns_assessment_result() -> None:
    engine = DummyAssessmentEngine(sleep_seconds=0.01)
    context = ScanContext(
        scan=FakeScan(),
        project=FakeProject(),
        connection=FakeConnection(),
        catalog_entry=FakeCatalogEntry(),
        http_client=httpx.AsyncClient(),
        logger=logging.getLogger("test.sdk"),
        settings=Settings(),
    )
    try:
        result = await engine.run(context)
    finally:
        await context.http_client.aclose()

    assert isinstance(result, AssessmentResult)
    assert result.status == AssessmentStatus.PASSED
    assert result.assessment_name == engine.name
    assert result.risk_score == 100.0
    assert result.evidence.extra["dummy"] is True
    assert result.recommendations
    assert result.execution_time_ms is not None
