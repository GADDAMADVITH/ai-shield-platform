"""Dummy assessment engine used only to validate the orchestration framework."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from app.assessment_engines.base import AssessmentEngine
from app.assessment_sdk.evidence import Evidence
from app.assessment_sdk.metadata import AssessmentMetadata
from app.assessment_sdk.recommendation import Recommendation
from app.assessment_sdk.result import AssessmentResult
from app.assessment_sdk.severity import Severity
from app.common.enums import ConnectionMethod

if TYPE_CHECKING:
    from app.orchestration.context import ScanContext


class DummyAssessmentEngine(AssessmentEngine):
    """No-op engine that sleeps briefly and returns an SDK AssessmentResult.

    This engine must never be used as a real security assessment. It exists so
    the orchestrator and Assessment SDK contracts can be exercised end-to-end.
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

    async def run(self, context: ScanContext) -> AssessmentResult:
        started = time.perf_counter()
        await asyncio.sleep(self._sleep_seconds)
        elapsed_ms = (time.perf_counter() - started) * 1000

        evidence = Evidence(
            extra={
                "dummy": True,
                "sleep_seconds": self._sleep_seconds,
                "project_id": str(context.project.id),
                "scan_id": str(context.scan.id),
                "connection_id": str(context.connection.id),
                "catalog_slug": context.catalog_entry.slug,
            }
        )
        evidence.add_log("Dummy assessment executed successfully", level="info")

        return AssessmentResult.passed(
            assessment_name=self.name,
            assessment_version=self.version,
            risk_score=100.0,
            confidence=1.0,
            severity=Severity.INFO,
            evidence=evidence,
            recommendations=[
                Recommendation(
                    title="No action required",
                    description=(
                        "Dummy assessment completed successfully. "
                        "Replace with a real engine in a later sprint."
                    ),
                    priority=Severity.INFO,
                )
            ],
            metadata=AssessmentMetadata(
                version=self.version,
                author="ai-shield",
                engine=self.name,
                execution_environment=getattr(context.settings, "app_env", None),
                extra={"timing_ms_fake": int(self._sleep_seconds * 1000)},
            ),
            execution_time_ms=elapsed_ms,
            raw_output={"dummy": True, "status": "ok"},
        )
