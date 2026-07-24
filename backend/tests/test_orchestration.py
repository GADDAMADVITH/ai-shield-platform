"""Unit tests for the Sprint 7 scan orchestration framework."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx
import pytest

from app.assessment_engines.base import AssessmentEngine
from app.assessment_engines.dummy import DummyAssessmentEngine
from app.assessment_sdk.result import AssessmentResult
from app.assessment_sdk.severity import Severity
from app.common.enums import (
    AssessmentStatus,
    ConnectionMethod,
    ScanStatus,
)
from app.core.config import Settings
from app.orchestration.context import ScanContext
from app.orchestration.events import (
    AssessmentFinished,
    AssessmentStarted,
    ScanFinished,
    ScanStarted,
)
from app.orchestration.executor import AssessmentExecutor
from app.orchestration.orchestrator import ScanOrchestrator, WorkItem
from app.orchestration.registry import (
    AssessmentRegistry,
    DuplicateEngineRegistrationError,
    EngineNotFoundError,
    create_default_registry,
)
from app.orchestration.scheduler import (
    ExecutionStrategy,
    ParallelScheduler,
    SequentialScheduler,
)

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


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
    name: str = "Demo Project"
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
    category: str = "universal"
    default_severity: Severity = Severity.INFO
    version: str = "1.0.0"


@dataclass
class FakeAssessment:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: AssessmentStatus = AssessmentStatus.PENDING
    score: float | None = None
    confidence: float | None = None
    severity: Severity = Severity.MEDIUM
    finding_summary: str | None = None
    recommendation: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    metadata_: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ExplodingEngine(AssessmentEngine):
    @property
    def name(self) -> str:
        return "Exploding"

    @property
    def version(self) -> str:
        return "0.0.1"

    @property
    def assessment_key(self) -> str:
        return "exploding"

    def supported_connection_methods(self) -> frozenset[ConnectionMethod]:
        return frozenset(ConnectionMethod)

    async def run(self, context: ScanContext) -> AssessmentResult:
        raise RuntimeError("boom")


class SlowEngine(AssessmentEngine):
    def __init__(self, sleep_seconds: float = 1.0) -> None:
        self._sleep_seconds = sleep_seconds

    @property
    def name(self) -> str:
        return "Slow"

    @property
    def version(self) -> str:
        return "0.0.1"

    @property
    def assessment_key(self) -> str:
        return "slow"

    def supported_connection_methods(self) -> frozenset[ConnectionMethod]:
        return frozenset(ConnectionMethod)

    async def run(self, context: ScanContext) -> AssessmentResult:
        import asyncio

        await asyncio.sleep(self._sleep_seconds)
        return AssessmentResult.passed(
            assessment_name=self.name,
            assessment_version=self.version,
            risk_score=100.0,
        )


def _context(
    *,
    catalog_slug: str = "dummy",
    connection_method: ConnectionMethod = ConnectionMethod.REST_API,
) -> ScanContext:
    return ScanContext(
        scan=FakeScan(),
        project=FakeProject(),
        connection=FakeConnection(connection_method=connection_method),
        catalog_entry=FakeCatalogEntry(slug=catalog_slug),
        http_client=httpx.AsyncClient(),
        logger=logging.getLogger("test.orchestration"),
        settings=Settings(),
        metadata={},
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def test_registry_registration_and_lookup() -> None:
    registry = AssessmentRegistry()
    engine = DummyAssessmentEngine()
    registry.register(engine)

    assert registry.has("dummy")
    assert "dummy" in registry
    assert registry.get("dummy") is engine
    assert registry.keys() == ["dummy"]
    assert len(registry) == 1


def test_registry_duplicate_registration_raises() -> None:
    registry = AssessmentRegistry()
    registry.register(DummyAssessmentEngine())

    with pytest.raises(DuplicateEngineRegistrationError) as exc_info:
        registry.register(DummyAssessmentEngine())

    assert exc_info.value.status_code == 409
    assert "dummy" in str(exc_info.value)


def test_registry_replace_allows_reregistration() -> None:
    registry = AssessmentRegistry()
    first = DummyAssessmentEngine(sleep_seconds=0.01)
    second = DummyAssessmentEngine(sleep_seconds=0.02)
    registry.register(first)
    registry.register(second, replace=True)
    assert registry.get("dummy") is second


def test_registry_missing_engine_raises() -> None:
    registry = AssessmentRegistry()
    with pytest.raises(EngineNotFoundError):
        registry.get("prompt-injection")


def test_create_default_registry_includes_dummy() -> None:
    registry = create_default_registry()
    assert isinstance(registry.get("dummy"), DummyAssessmentEngine)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


def test_sequential_scheduler_preserves_order() -> None:
    scheduler = SequentialScheduler[str]()
    plan = scheduler.schedule(["c", "a", "b"])

    assert plan.strategy == ExecutionStrategy.SEQUENTIAL
    assert plan.items == ("c", "a", "b")
    assert plan.batches == (("c",), ("a",), ("b",))


def test_parallel_scheduler_single_batch() -> None:
    scheduler = ParallelScheduler[str]()
    plan = scheduler.schedule(["a", "b", "c"])

    assert plan.strategy == ExecutionStrategy.PARALLEL
    assert plan.batches == (("a", "b", "c"),)


def test_scheduler_empty_plan() -> None:
    plan = SequentialScheduler[str]().schedule([])
    assert plan.items == ()
    assert plan.batches == ()


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_executor_successful_execution() -> None:
    engine = DummyAssessmentEngine(sleep_seconds=0.01)
    context = _context()
    executor = AssessmentExecutor()

    try:
        result = await executor.execute(engine, context)
    finally:
        await context.http_client.aclose()

    assert result.status == AssessmentStatus.PASSED
    assert result.error is None
    assert result.duration_ms >= 0
    assert result.result is not None
    assert result.result.finding_summary is not None
    assert result.engine_name == engine.name
    assert result.attempts == 1


@pytest.mark.asyncio
async def test_executor_exception_handling() -> None:
    engine = ExplodingEngine()
    context = _context(catalog_slug="exploding")
    executor = AssessmentExecutor()

    try:
        result = await executor.execute(engine, context)
    finally:
        await context.http_client.aclose()

    assert result.status == AssessmentStatus.ERROR
    assert result.result is None
    assert result.error == "boom"
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_executor_timeout_hook() -> None:
    timeouts: list[float] = []

    async def on_timeout(engine: AssessmentEngine, context: ScanContext, seconds: float) -> None:
        timeouts.append(seconds)

    engine = SlowEngine(sleep_seconds=0.5)
    context = _context(catalog_slug="slow")
    executor = AssessmentExecutor(default_timeout_seconds=0.05, on_timeout=on_timeout)

    try:
        result = await executor.execute(engine, context)
    finally:
        await context.http_client.aclose()

    assert result.timed_out is True
    assert result.status == AssessmentStatus.ERROR
    assert result.error is not None and "timed out" in result.error
    assert timeouts == [0.05]


def test_executor_rejects_retry_attempts() -> None:
    with pytest.raises(ValueError, match="Retries are not implemented"):
        AssessmentExecutor(max_attempts=2)


# ---------------------------------------------------------------------------
# Dummy engine
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dummy_engine_returns_successful_fake_result() -> None:
    engine = DummyAssessmentEngine(sleep_seconds=0.01)
    context = _context()

    try:
        await engine.validate(context)
        result = await engine.run(context)
        await engine.cleanup(context)
    finally:
        await context.http_client.aclose()

    assert result.status == AssessmentStatus.PASSED
    assert result.risk_score == 100.0
    assert result.confidence == 1.0
    assert result.severity == Severity.INFO
    assert "Dummy Assessment Engine" in (result.finding_summary() or "")
    assert result.evidence.extra.get("dummy") is True
    assert result.metadata.extra.get("timing_ms_fake") == 10  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Orchestrator flow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_orchestrator_flow_with_dummy_engine() -> None:
    registry = create_default_registry()
    events: list[Any] = []
    orchestrator = ScanOrchestrator(
        registry=registry,
        scheduler=SequentialScheduler(),
        executor=AssessmentExecutor(),
        event_sink=events.append,
    )

    scan = FakeScan()
    assessment = FakeAssessment()
    catalog = FakeCatalogEntry(slug="dummy")

    result = await orchestrator.run(
        scan=scan,
        project=FakeProject(),
        connection=FakeConnection(),
        work_items=[WorkItem(assessment_key="dummy", catalog_entry=catalog, assessment=assessment)],
        metadata={"source": "unit-test"},
    )

    assert result.status == ScanStatus.COMPLETED
    assert result.error is None
    assert result.progress.total == 1
    assert result.progress.passed == 1
    assert len(result.executions) == 1
    assert result.executions[0].status == AssessmentStatus.PASSED

    assert scan.status == ScanStatus.COMPLETED
    assert scan.started_at is not None
    assert scan.completed_at is not None

    assert assessment.status == AssessmentStatus.PASSED
    assert assessment.score == 100.0
    assert assessment.finding_summary is not None
    assert assessment.evidence.get("dummy") is True

    assert any(isinstance(e, ScanStarted) for e in events)
    assert any(isinstance(e, AssessmentStarted) for e in events)
    assert any(isinstance(e, AssessmentFinished) for e in events)
    assert any(isinstance(e, ScanFinished) for e in events)


@pytest.mark.asyncio
async def test_orchestrator_skips_unregistered_engine() -> None:
    registry = AssessmentRegistry()
    orchestrator = ScanOrchestrator(registry=registry)
    assessment = FakeAssessment()
    scan = FakeScan()

    result = await orchestrator.run(
        scan=scan,
        project=FakeProject(),
        connection=FakeConnection(),
        work_items=[
            WorkItem(
                assessment_key="missing-engine",
                catalog_entry=FakeCatalogEntry(slug="missing-engine"),
                assessment=assessment,
            )
        ],
    )

    assert result.status == ScanStatus.COMPLETED
    assert result.progress.skipped == 1
    assert result.executions[0].status == AssessmentStatus.SKIPPED
    assert assessment.status == AssessmentStatus.SKIPPED


@pytest.mark.asyncio
async def test_orchestrator_records_engine_errors_without_failing_scan() -> None:
    registry = AssessmentRegistry()
    registry.register(ExplodingEngine())
    orchestrator = ScanOrchestrator(registry=registry)
    assessment = FakeAssessment()
    scan = FakeScan()

    result = await orchestrator.run(
        scan=scan,
        project=FakeProject(),
        connection=FakeConnection(),
        work_items=[
            WorkItem(
                assessment_key="exploding",
                catalog_entry=FakeCatalogEntry(slug="exploding"),
                assessment=assessment,
            )
        ],
    )

    assert result.status == ScanStatus.COMPLETED
    assert result.progress.errored == 1
    assert result.executions[0].status == AssessmentStatus.ERROR
    assert assessment.status == AssessmentStatus.ERROR
    assert assessment.finding_summary == "boom"


@pytest.mark.asyncio
async def test_orchestrator_runs_multiple_assessments_in_order() -> None:
    registry = AssessmentRegistry()
    registry.register(DummyAssessmentEngine(sleep_seconds=0.01))

    class SecondDummy(DummyAssessmentEngine):
        @property
        def assessment_key(self) -> str:
            return "dummy-two"

        @property
        def name(self) -> str:
            return "Dummy Two"

    registry.register(SecondDummy(sleep_seconds=0.01))
    orchestrator = ScanOrchestrator(
        registry=registry,
        scheduler=SequentialScheduler(),
    )

    keys: list[str] = []

    class TrackingExecutor(AssessmentExecutor):
        async def execute(self, engine, context, *, timeout_seconds=None):  # type: ignore[no-untyped-def]
            keys.append(engine.assessment_key)
            return await super().execute(engine, context, timeout_seconds=timeout_seconds)

    orchestrator = ScanOrchestrator(
        registry=registry,
        scheduler=SequentialScheduler(),
        executor=TrackingExecutor(),
    )

    result = await orchestrator.run(
        scan=FakeScan(),
        project=FakeProject(),
        connection=FakeConnection(),
        work_items=[
            WorkItem(assessment_key="dummy", catalog_entry=FakeCatalogEntry(slug="dummy")),
            WorkItem(
                assessment_key="dummy-two",
                catalog_entry=FakeCatalogEntry(slug="dummy-two"),
            ),
        ],
    )

    assert keys == ["dummy", "dummy-two"]
    assert result.progress.passed == 2
    assert result.status == ScanStatus.COMPLETED
