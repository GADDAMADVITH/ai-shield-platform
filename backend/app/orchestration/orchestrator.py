"""Scan orchestrator — coordinates registry, scheduler, and executor.

The orchestrator never contains assessment logic. It loads shared context,
asks the scheduler for order, resolves engines from the registry, executes
them, stores standardized results, and updates scan progress.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.assessment_engines.base import EngineResult
from app.common.enums import AssessmentStatus, ScanStatus
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.orchestration.context import ScanContext
from app.orchestration.events import (
    AssessmentFinished,
    AssessmentStarted,
    OrchestrationEvent,
    ScanFailed,
    ScanFinished,
    ScanStarted,
)
from app.orchestration.executor import AssessmentExecutor, ExecutionResult
from app.orchestration.registry import AssessmentRegistry, EngineNotFoundError
from app.orchestration.scheduler import (
    ExecutionStrategy,
    Scheduler,
    SequentialScheduler,
)

EventSink = Callable[[OrchestrationEvent], None]


class _MutableScan(Protocol):
    id: uuid.UUID
    status: ScanStatus
    profile: str
    started_at: datetime | None
    completed_at: datetime | None


class _MutableAssessment(Protocol):
    id: uuid.UUID
    status: AssessmentStatus
    score: float | None
    confidence: float | None
    severity: Any
    finding_summary: str | None
    recommendation: str | None
    evidence: dict[str, Any]
    metadata_: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None


@dataclass(slots=True)
class WorkItem:
    """One catalog assessment scheduled for execution within a scan."""

    assessment_key: str
    catalog_entry: Any
    assessment: Any | None = None


@dataclass(slots=True)
class ScanProgress:
    """Running progress counters for a scan."""

    total: int
    completed: int = 0
    passed: int = 0
    failed: int = 0
    errored: int = 0
    skipped: int = 0

    @property
    def finished(self) -> int:
        return self.passed + self.failed + self.errored + self.skipped

    @property
    def percent(self) -> float:
        if self.total <= 0:
            return 100.0
        return round((self.finished / self.total) * 100.0, 2)

    def record(self, status: AssessmentStatus) -> None:
        self.completed += 1
        if status == AssessmentStatus.PASSED:
            self.passed += 1
        elif status == AssessmentStatus.FAILED:
            self.failed += 1
        elif status == AssessmentStatus.SKIPPED:
            self.skipped += 1
        else:
            self.errored += 1


@dataclass(slots=True)
class ScanOrchestrationResult:
    """Aggregate outcome of orchestrating a full scan."""

    scan_id: uuid.UUID
    status: ScanStatus
    progress: ScanProgress
    executions: list[ExecutionResult] = field(default_factory=list)
    events: list[OrchestrationEvent] = field(default_factory=list)
    duration_ms: float = 0.0
    error: str | None = None


class ScanOrchestrator:
    """Framework coordinator for scan execution.

    Dependencies (registry / scheduler / executor) are injected so tests and
    future worker processes can substitute implementations without changing
    orchestration flow.
    """

    def __init__(
        self,
        *,
        registry: AssessmentRegistry,
        scheduler: Scheduler[WorkItem] | None = None,
        executor: AssessmentExecutor | None = None,
        settings: Settings | None = None,
        logger: logging.Logger | None = None,
        event_sink: EventSink | None = None,
    ) -> None:
        self._registry = registry
        self._scheduler = scheduler or SequentialScheduler[WorkItem]()
        self._executor = executor or AssessmentExecutor()
        self._settings = settings or get_settings()
        self._logger = logger or get_logger("app.orchestration")
        self._event_sink = event_sink

    @property
    def registry(self) -> AssessmentRegistry:
        return self._registry

    async def run(
        self,
        *,
        scan: _MutableScan,
        project: Any,
        connection: Any,
        work_items: Sequence[WorkItem],
        user: Any | None = None,
        session: AsyncSession | None = None,
        http_client: httpx.AsyncClient | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ScanOrchestrationResult:
        """Execute a scan using already-loaded domain objects.

        This is the primary orchestration entrypoint. Callers (API services,
        workers, tests) are responsible for loading Scan / Project / Connection
        and the catalog-backed work items.
        """
        started = time.perf_counter()
        events: list[OrchestrationEvent] = []
        executions: list[ExecutionResult] = []
        progress = ScanProgress(total=len(work_items))
        owns_client = http_client is None
        client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
        )
        shared_metadata = dict(metadata or {})

        def emit(event: OrchestrationEvent) -> None:
            events.append(event)
            if self._event_sink is not None:
                self._event_sink(event)

        try:
            self._mark_scan_started(scan)
            emit(
                ScanStarted(
                    scan_id=scan.id,
                    project_id=getattr(project, "id", None),
                    connection_id=getattr(connection, "id", None),
                    assessment_count=len(work_items),
                    profile=getattr(scan, "profile", None),
                )
            )

            plan = self._scheduler.schedule(list(work_items))
            index = 0

            for batch in plan.batches:
                if plan.strategy == ExecutionStrategy.PARALLEL and len(batch) > 1:
                    batch_results = await asyncio.gather(
                        *[
                            self._execute_one(
                                item=item,
                                index=index + offset,
                                total=progress.total,
                                scan=scan,
                                project=project,
                                connection=connection,
                                user=user,
                                session=session,
                                http_client=client,
                                shared_metadata=shared_metadata,
                                emit=emit,
                            )
                            for offset, item in enumerate(batch)
                        ]
                    )
                    for result in batch_results:
                        executions.append(result)
                        progress.record(result.status)
                    index += len(batch)
                else:
                    for item in batch:
                        result = await self._execute_one(
                            item=item,
                            index=index,
                            total=progress.total,
                            scan=scan,
                            project=project,
                            connection=connection,
                            user=user,
                            session=session,
                            http_client=client,
                            shared_metadata=shared_metadata,
                            emit=emit,
                        )
                        executions.append(result)
                        progress.record(result.status)
                        index += 1

            self._mark_scan_finished(scan, ScanStatus.COMPLETED)
            duration_ms = (time.perf_counter() - started) * 1000
            emit(
                ScanFinished(
                    scan_id=scan.id,
                    status=ScanStatus.COMPLETED,
                    completed=progress.finished,
                    failed=progress.failed + progress.errored,
                    skipped=progress.skipped,
                    duration_ms=duration_ms,
                )
            )
            shared_metadata["progress"] = {
                "total": progress.total,
                "percent": progress.percent,
                "passed": progress.passed,
                "failed": progress.failed,
                "errored": progress.errored,
                "skipped": progress.skipped,
            }
            return ScanOrchestrationResult(
                scan_id=scan.id,
                status=ScanStatus.COMPLETED,
                progress=progress,
                executions=executions,
                events=events,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            self._logger.exception("Scan orchestration failed", extra={"scan_id": str(scan.id)})
            self._mark_scan_finished(scan, ScanStatus.FAILED)
            duration_ms = (time.perf_counter() - started) * 1000
            emit(
                ScanFailed(
                    scan_id=scan.id,
                    error=str(exc) or exc.__class__.__name__,
                    details={"duration_ms": duration_ms},
                )
            )
            return ScanOrchestrationResult(
                scan_id=scan.id,
                status=ScanStatus.FAILED,
                progress=progress,
                executions=executions,
                events=events,
                duration_ms=duration_ms,
                error=str(exc) or exc.__class__.__name__,
            )
        finally:
            if owns_client:
                await client.aclose()

    async def _execute_one(
        self,
        *,
        item: WorkItem,
        index: int,
        total: int,
        scan: _MutableScan,
        project: Any,
        connection: Any,
        user: Any | None,
        session: AsyncSession | None,
        http_client: httpx.AsyncClient,
        shared_metadata: dict[str, Any],
        emit: Callable[[OrchestrationEvent], None],
    ) -> ExecutionResult:
        assessment = item.assessment
        try:
            engine = self._registry.get(item.assessment_key)
        except EngineNotFoundError as exc:
            started_at = datetime.now(UTC)
            self._mark_assessment_started(assessment, started_at)
            skipped = ExecutionResult(
                assessment_key=item.assessment_key,
                engine_name="unregistered",
                engine_version="0.0.0",
                status=AssessmentStatus.SKIPPED,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                duration_ms=0.0,
                error=str(exc),
                metadata={
                    "scan_id": scan.id,
                    "catalog_slug": item.assessment_key,
                    "assessment_id": getattr(assessment, "id", None),
                },
            )
            self._apply_skipped(assessment, skipped)
            emit(
                AssessmentFinished(
                    scan_id=scan.id,
                    assessment_key=item.assessment_key,
                    assessment_id=getattr(assessment, "id", None),
                    status=AssessmentStatus.SKIPPED,
                    duration_ms=0.0,
                    error=skipped.error,
                )
            )
            return skipped

        context = ScanContext(
            scan=scan,
            project=project,
            connection=connection,
            catalog_entry=item.catalog_entry,
            http_client=http_client,
            logger=self._logger,
            settings=self._settings,
            user=user,
            session=session,
            assessment=assessment,
            metadata={
                **shared_metadata,
                "assessment_index": index,
                "assessment_total": total,
            },
        )

        emit(
            AssessmentStarted(
                scan_id=scan.id,
                assessment_key=engine.assessment_key,
                assessment_id=getattr(assessment, "id", None),
                engine_name=engine.name,
                engine_version=engine.version,
                index=index,
                total=total,
            )
        )
        self._mark_assessment_started(assessment, datetime.now(UTC))

        result = await self._executor.execute(engine, context)
        self._apply_execution_result(assessment, result)
        emit(
            AssessmentFinished(
                scan_id=scan.id,
                assessment_key=result.assessment_key,
                assessment_id=getattr(assessment, "id", None),
                status=result.status,
                duration_ms=result.duration_ms,
                error=result.error,
            )
        )
        return result

    @staticmethod
    def _mark_scan_started(scan: _MutableScan) -> None:
        scan.status = ScanStatus.RUNNING
        if scan.started_at is None:
            scan.started_at = datetime.now(UTC)
        scan.completed_at = None

    @staticmethod
    def _mark_scan_finished(scan: _MutableScan, status: ScanStatus) -> None:
        scan.status = status
        scan.completed_at = datetime.now(UTC)

    @staticmethod
    def _mark_assessment_started(assessment: Any | None, started_at: datetime) -> None:
        if assessment is None:
            return
        assessment.status = AssessmentStatus.RUNNING
        assessment.started_at = started_at
        assessment.completed_at = None

    @staticmethod
    def _apply_skipped(assessment: Any | None, result: ExecutionResult) -> None:
        if assessment is None:
            return
        assessment.status = AssessmentStatus.SKIPPED
        assessment.completed_at = result.completed_at
        assessment.finding_summary = result.error
        meta = getattr(assessment, "metadata_", None)
        if isinstance(meta, dict):
            meta = {**meta, "orchestration": {"skipped": True, "reason": result.error}}
            assessment.metadata_ = meta

    @staticmethod
    def _apply_execution_result(assessment: Any | None, execution: ExecutionResult) -> None:
        if assessment is None:
            return
        assessment.status = execution.status
        assessment.started_at = execution.started_at
        assessment.completed_at = execution.completed_at

        engine_result: EngineResult | None = execution.result
        if engine_result is not None:
            assessment.score = engine_result.score
            assessment.confidence = engine_result.confidence
            if engine_result.severity is not None:
                assessment.severity = engine_result.severity
            assessment.finding_summary = engine_result.finding_summary
            assessment.recommendation = engine_result.recommendation
            assessment.evidence = dict(engine_result.evidence)
            assessment.metadata_ = {
                **dict(getattr(assessment, "metadata_", None) or {}),
                **dict(engine_result.metadata),
                "orchestration": {
                    "duration_ms": execution.duration_ms,
                    "engine_name": execution.engine_name,
                    "engine_version": execution.engine_version,
                    "attempts": execution.attempts,
                    "timed_out": execution.timed_out,
                },
            }
        elif execution.error:
            assessment.finding_summary = execution.error
            assessment.metadata_ = {
                **dict(getattr(assessment, "metadata_", None) or {}),
                "orchestration": {
                    "duration_ms": execution.duration_ms,
                    "error": execution.error,
                    "timed_out": execution.timed_out,
                    "attempts": execution.attempts,
                },
            }
