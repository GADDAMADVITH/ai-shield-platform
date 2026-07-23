"""Dummy assessment engine used only to validate the orchestration framework."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from app.assessment_engines.base import AssessmentEngine, EngineResult
from app.common.enums import AssessmentStatus, ConnectionMethod, Severity

if TYPE_CHECKING:
    from app.orchestration.context import ScanContext


class DummyAssessmentEngine(AssessmentEngine):
    """No-op engine that sleeps briefly and returns a synthetic success result.

    This engine must never be used as a real security assessment. It exists so
    the orchestrator, registry, scheduler, and executor can be exercised
    end-to-end before Sprint 8 engines land.
    """

    ASSESSMENT_KEY = "dummy"
    DEFAULT_SLEEP_SECONDS = 0.05

    def __init__(self, *, sleep_seconds: float = DEFAULT_SLEEP_SECONDS) -> None:
        self._sleep_seconds = sleep_seconds

    @property
    def name(self) -> str:
        return "Dummy Assessment Engine"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def assessment_key(self) -> str:
        return self.ASSESSMENT_KEY

    def supported_connection_methods(self) -> frozenset[ConnectionMethod]:
        return frozenset(ConnectionMethod)

    async def run(self, context: ScanContext) -> EngineResult:
        await asyncio.sleep(self._sleep_seconds)
        return EngineResult(
            status=AssessmentStatus.PASSED,
            score=100.0,
            confidence=1.0,
            severity=Severity.INFO,
            finding_summary="Dummy assessment completed successfully (orchestration validation).",
            recommendation="No action required — replace with a real engine in Sprint 8.",
            evidence={
                "dummy": True,
                "sleep_seconds": self._sleep_seconds,
                "project_id": str(context.project.id),
                "scan_id": str(context.scan.id),
                "connection_id": str(context.connection.id),
                "catalog_slug": context.catalog_entry.slug,
            },
            metadata={
                "engine": self.name,
                "engine_version": self.version,
                "timing_ms_fake": int(self._sleep_seconds * 1000),
            },
        )
