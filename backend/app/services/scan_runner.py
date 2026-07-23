"""Background scan execution — bridges API lifecycle to the orchestrator.

Does not modify the orchestration package. Uses injected registry/executor only.
Sprint 7.1 runs DummyAssessmentEngine exclusively via create_default_registry().
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.common.enums import (
    AssessmentStatus,
    AuditAction,
    ScanStatus,
    Severity,
)
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.assessment import Assessment
from app.models.scan import Scan
from app.models.scan_summary import ScanSummary
from app.orchestration.executor import AssessmentExecutor, ExecutionResult
from app.orchestration.orchestrator import ScanOrchestrator, WorkItem
from app.orchestration.registry import create_default_registry
from app.services.audit import write_audit_log

logger = get_logger("app.services.scan_runner")


class ProgressTrackingExecutor(AssessmentExecutor):
    """Executor wrapper that persists progress after each assessment.

    Keeps orchestration untouched while satisfying progress-tracking requirements.
    """

    def __init__(
        self,
        *,
        session: Any,
        scan: Scan,
        total: int,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._session = session
        self._scan = scan
        self._total = total
        self._finished = 0
        self._failed = 0

    async def execute(
        self,
        engine: Any,
        context: Any,
        *,
        timeout_seconds: float | None = None,
    ) -> ExecutionResult:
        await self._session.refresh(self._scan)
        if self._scan.cancel_requested or self._scan.status == ScanStatus.CANCELLED:
            started = datetime.now(UTC)
            logger.info(
                "assessment skipped due to cancel scan_id=%s key=%s",
                self._scan.id,
                engine.assessment_key,
            )
            result = ExecutionResult(
                assessment_key=engine.assessment_key,
                engine_name=engine.name,
                engine_version=engine.version,
                status=AssessmentStatus.SKIPPED,
                started_at=started,
                completed_at=datetime.now(UTC),
                duration_ms=0.0,
                error="Scan cancelled",
                metadata={"scan_id": self._scan.id, "cancelled": True},
            )
            self._apply_assessment_fields(context.assessment, result)
            self._finished += 1
            self._scan.completed_assessments = self._finished
            self._scan.failed_assessments = self._failed
            self._scan.progress_percent = (
                100.0 if self._total <= 0 else round((self._finished / self._total) * 100.0, 2)
            )
            await self._session.flush()
            await self._session.commit()
            return result

        logger.info(
            "assessment started scan_id=%s key=%s engine=%s",
            self._scan.id,
            engine.assessment_key,
            engine.name,
        )
        result = await super().execute(engine, context, timeout_seconds=timeout_seconds)
        assessment = context.assessment
        if assessment is not None:
            # Persist terminal status before commit so later session ops cannot
            # reload a stale pending/running row from the database.
            assessment.status = result.status
            assessment.started_at = result.started_at
            assessment.completed_at = result.completed_at
            if result.result is not None:
                assessment.score = result.result.score
                assessment.confidence = result.result.confidence
                if result.result.severity is not None:
                    assessment.severity = result.result.severity
                assessment.finding_summary = result.result.finding_summary
                assessment.recommendation = result.result.recommendation
                assessment.evidence = dict(result.result.evidence)
        self._apply_assessment_fields(assessment, result)
        self._finished += 1
        if result.status in {AssessmentStatus.FAILED, AssessmentStatus.ERROR}:
            self._failed += 1
            logger.warning(
                "assessment failed scan_id=%s key=%s error=%s",
                self._scan.id,
                engine.assessment_key,
                result.error,
            )
        else:
            logger.info(
                "assessment completed scan_id=%s key=%s status=%s duration_ms=%.2f",
                self._scan.id,
                engine.assessment_key,
                result.status.value,
                result.duration_ms,
            )

        self._scan.completed_assessments = self._finished
        self._scan.failed_assessments = self._failed
        self._scan.progress_percent = (
            100.0 if self._total <= 0 else round((self._finished / self._total) * 100.0, 2)
        )
        await self._session.flush()
        await self._session.commit()
        return result

    @staticmethod
    def _apply_assessment_fields(assessment: Assessment | None, result: ExecutionResult) -> None:
        if assessment is None:
            return
        assessment.execution_time_ms = int(result.duration_ms)
        logs = list(assessment.logs or [])
        logs.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "error" if result.error else "info",
                "message": result.error
                or f"Assessment {result.assessment_key} finished with status {result.status.value}",
                "duration_ms": result.duration_ms,
            }
        )
        assessment.logs = logs
        if result.result is not None:
            assessment.raw_result = {
                "status": result.result.status.value,
                "score": result.result.score,
                "confidence": result.result.confidence,
                "severity": result.result.severity.value if result.result.severity else None,
                "finding_summary": result.result.finding_summary,
                "recommendation": result.result.recommendation,
                "evidence": result.result.evidence,
                "metadata": result.result.metadata,
                "engine_name": result.engine_name,
                "engine_version": result.engine_version,
                "duration_ms": result.duration_ms,
            }
        elif result.error:
            assessment.raw_result = {
                "status": result.status.value,
                "error": result.error,
                "timed_out": result.timed_out,
                "duration_ms": result.duration_ms,
            }


async def execute_scan_job(scan_id: uuid.UUID) -> None:
    """Background entrypoint: load scan, run orchestrator, persist summary."""
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Scan)
                .where(Scan.id == scan_id)
                .options(
                    selectinload(Scan.assessments).selectinload(Assessment.catalog_entry),
                    selectinload(Scan.project),
                    selectinload(Scan.connection),
                    selectinload(Scan.initiated_by),
                    selectinload(Scan.summary),
                )
            )
            scan = result.scalar_one_or_none()
            if scan is None:
                logger.error("scan job aborted — scan not found id=%s", scan_id)
                return

            if scan.status == ScanStatus.CANCELLED or scan.cancel_requested:
                scan.status = ScanStatus.CANCELLED
                scan.completed_at = datetime.now(UTC)
                await session.commit()
                logger.info("scan cancelled before start scan_id=%s", scan_id)
                return

            if scan.connection is None or scan.project is None:
                scan.status = ScanStatus.FAILED
                scan.error_message = "Missing project or connection for scan execution"
                scan.completed_at = datetime.now(UTC)
                await write_audit_log(
                    session,
                    action=AuditAction.SCAN_FAILED,
                    resource=f"scan:{scan.id}",
                    description=scan.error_message,
                    user_id=scan.initiated_by_id,
                    project_id=scan.project_id,
                    scan_id=scan.id,
                )
                await session.commit()
                return

            scan.status = ScanStatus.RUNNING
            if scan.started_at is None:
                scan.started_at = datetime.now(UTC)
            scan.error_message = None
            await session.flush()
            await write_audit_log(
                session,
                action=AuditAction.SCAN_STARTED,
                resource=f"scan:{scan.id}",
                description="Scan execution started",
                user_id=scan.initiated_by_id,
                project_id=scan.project_id,
                scan_id=scan.id,
            )
            await session.commit()
            logger.info("scan started scan_id=%s project_id=%s", scan.id, scan.project_id)

            work_items = [
                WorkItem(
                    assessment_key=item.catalog_entry.slug,
                    catalog_entry=item.catalog_entry,
                    assessment=item,
                )
                for item in scan.assessments
                if item.catalog_entry is not None
            ]
            total = len(work_items)
            registry = create_default_registry(include_dummy=True)
            executor = ProgressTrackingExecutor(
                session=session,
                scan=scan,
                total=total,
                default_timeout_seconds=120.0,
            )
            orchestrator = ScanOrchestrator(
                registry=registry,
                executor=executor,
                settings=settings,
                logger=logger,
            )

            orchestration = await orchestrator.run(
                scan=scan,
                project=scan.project,
                connection=scan.connection,
                work_items=work_items,
                user=scan.initiated_by,
                session=session,
                metadata={"source": "background_task"},
            )

            # Re-check cancellation after orchestration (executor may have skipped remaining).
            await session.refresh(scan)
            duration_ms = int(orchestration.duration_ms)
            scan.execution_time_ms = duration_ms
            scan.completed_assessments = orchestration.progress.finished
            scan.failed_assessments = (
                orchestration.progress.failed + orchestration.progress.errored
            )
            scan.progress_percent = orchestration.progress.percent

            if scan.cancel_requested:
                scan.status = ScanStatus.CANCELLED
                scan.completed_at = datetime.now(UTC)
                await write_audit_log(
                    session,
                    action=AuditAction.SCAN_CANCELLED,
                    resource=f"scan:{scan.id}",
                    description="Scan cancelled during execution",
                    user_id=scan.initiated_by_id,
                    project_id=scan.project_id,
                    scan_id=scan.id,
                )
                await session.commit()
                logger.info("scan cancelled scan_id=%s", scan.id)
                return

            if orchestration.status == ScanStatus.FAILED or orchestration.error:
                scan.status = ScanStatus.FAILED
                scan.error_message = orchestration.error or "Orchestrator failure"
                scan.completed_at = datetime.now(UTC)
                await _upsert_summary(session, scan=scan, orchestration=orchestration)
                await write_audit_log(
                    session,
                    action=AuditAction.SCAN_FAILED,
                    resource=f"scan:{scan.id}",
                    description=scan.error_message,
                    user_id=scan.initiated_by_id,
                    project_id=scan.project_id,
                    scan_id=scan.id,
                )
                await session.commit()
                logger.error("scan failed scan_id=%s error=%s", scan.id, scan.error_message)
                return

            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.now(UTC)
            scan.error_message = None
            await session.flush()
            await _upsert_summary(session, scan=scan, orchestration=orchestration)
            await write_audit_log(
                session,
                action=AuditAction.SCAN_COMPLETED,
                resource=f"scan:{scan.id}",
                description="Scan execution completed",
                user_id=scan.initiated_by_id,
                project_id=scan.project_id,
                scan_id=scan.id,
                metadata={
                    "duration_ms": duration_ms,
                    "passed": orchestration.progress.passed,
                    "failed": scan.failed_assessments,
                },
            )
            await session.commit()
            logger.info(
                "scan completed scan_id=%s duration_ms=%s progress=%.2f",
                scan.id,
                duration_ms,
                scan.progress_percent,
            )
        except Exception as exc:
            logger.exception("unexpected scan job failure scan_id=%s", scan_id)
            await session.rollback()
            async with AsyncSessionLocal() as fail_session:
                scan = await fail_session.get(Scan, scan_id)
                if scan is not None:
                    scan.status = ScanStatus.FAILED
                    scan.error_message = str(exc) or exc.__class__.__name__
                    scan.completed_at = datetime.now(UTC)
                    await write_audit_log(
                        fail_session,
                        action=AuditAction.SCAN_FAILED,
                        resource=f"scan:{scan.id}",
                        description=scan.error_message,
                        user_id=scan.initiated_by_id,
                        project_id=scan.project_id,
                        scan_id=scan.id,
                    )
                    await fail_session.commit()


async def _upsert_summary(session: Any, *, scan: Scan, orchestration: Any) -> ScanSummary:
    """Build ScanSummary from assessment outcomes after orchestration."""
    assessments = list(scan.assessments or [])
    progress = orchestration.progress
    passed = progress.passed
    failed = progress.failed + progress.errored

    severity_counts = {
        Severity.CRITICAL: 0,
        Severity.HIGH: 0,
        Severity.MEDIUM: 0,
        Severity.LOW: 0,
    }
    findings = 0
    scores: list[float] = []
    for assessment in assessments:
        if assessment.score is not None:
            scores.append(float(assessment.score))
        if assessment.status == AssessmentStatus.PASSED:
            continue
        if assessment.status in {
            AssessmentStatus.FAILED,
            AssessmentStatus.ERROR,
        }:
            findings += 1
            if assessment.severity in severity_counts:
                severity_counts[assessment.severity] += 1

    if scores:
        overall = round(sum(scores) / len(scores), 2)
    elif assessments:
        overall = round((passed / max(len(assessments), 1)) * 100.0, 2)
    else:
        overall = 0.0

    duration = int(getattr(orchestration, "duration_ms", 0) or scan.execution_time_ms or 0)
    summary = scan.summary
    if summary is None:
        summary = ScanSummary(scan_id=scan.id)
        session.add(summary)
        scan.summary = summary

    summary.overall_score = overall
    summary.critical = severity_counts[Severity.CRITICAL]
    summary.high = severity_counts[Severity.HIGH]
    summary.medium = severity_counts[Severity.MEDIUM]
    summary.low = severity_counts[Severity.LOW]
    summary.passed = passed
    summary.failed = failed
    summary.total_findings = findings
    summary.execution_duration_ms = duration
    await session.flush()
    return summary
