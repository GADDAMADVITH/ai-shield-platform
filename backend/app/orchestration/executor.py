"""Assessment executor — runs one engine with timing and error boundaries."""

from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.assessment_engines.base import AssessmentEngine, EngineResult, to_engine_result
from app.assessment_sdk.result import AssessmentResult
from app.common.enums import AssessmentStatus
from app.orchestration.context import ScanContext

TimeoutHook = Callable[[AssessmentEngine, ScanContext, float], Awaitable[None] | None]
RetryHook = Callable[[AssessmentEngine, ScanContext, int, BaseException], Awaitable[None] | None]


@dataclass(slots=True)
class ExecutionResult:
    """Standardized outcome of executing a single assessment engine."""

    assessment_key: str
    engine_name: str
    engine_version: str
    status: AssessmentStatus
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    result: EngineResult | None = None
    error: str | None = None
    attempts: int = 1
    timed_out: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return self.status == AssessmentStatus.PASSED

    @property
    def assessment_id(self) -> uuid.UUID | None:
        raw = self.metadata.get("assessment_id")
        if isinstance(raw, uuid.UUID):
            return raw
        return None


async def _maybe_await(value: Awaitable[None] | None) -> None:
    if value is None:
        return
    if inspect.isawaitable(value):
        await value


class AssessmentExecutor:
    """Execute one assessment engine against a :class:`ScanContext`.

    Responsibilities:
    - Validate and run the engine
    - Measure wall-clock duration
    - Catch exceptions into a standardized :class:`ExecutionResult`
    - Honor timeout hooks (via ``asyncio.wait_for``)
    - Expose retry hooks (retries are not enabled yet — ``max_attempts`` is 1)

    The executor never contains assessment-domain logic.
    """

    def __init__(
        self,
        *,
        default_timeout_seconds: float | None = None,
        max_attempts: int = 1,
        on_timeout: TimeoutHook | None = None,
        on_retry: RetryHook | None = None,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        # Retries are intentionally disabled in Sprint 7; keep the hook surface.
        if max_attempts != 1:
            raise ValueError(
                "Retries are not implemented yet; max_attempts must be 1 (Sprint 7)"
            )
        self._default_timeout_seconds = default_timeout_seconds
        self._max_attempts = max_attempts
        self._on_timeout = on_timeout
        self._on_retry = on_retry

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    async def execute(
        self,
        engine: AssessmentEngine,
        context: ScanContext,
        *,
        timeout_seconds: float | None = None,
    ) -> ExecutionResult:
        """Run *engine* once and return a standardized execution result."""
        started_at = datetime.now(UTC)
        t0 = time.perf_counter()
        timeout = (
            self._default_timeout_seconds if timeout_seconds is None else timeout_seconds
        )
        attempts = 0
        last_error: BaseException | None = None

        while attempts < self._max_attempts:
            attempts += 1
            try:
                engine_result = await self._run_with_timeout(engine, context, timeout)
                completed_at = datetime.now(UTC)
                return ExecutionResult(
                    assessment_key=engine.assessment_key,
                    engine_name=engine.name,
                    engine_version=engine.version,
                    status=engine_result.status,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=(time.perf_counter() - t0) * 1000,
                    result=engine_result,
                    attempts=attempts,
                    metadata=self._base_metadata(context),
                )
            except TimeoutError as exc:
                last_error = exc
                if self._on_timeout is not None:
                    await _maybe_await(self._on_timeout(engine, context, timeout or 0.0))
                completed_at = datetime.now(UTC)
                return ExecutionResult(
                    assessment_key=engine.assessment_key,
                    engine_name=engine.name,
                    engine_version=engine.version,
                    status=AssessmentStatus.ERROR,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=(time.perf_counter() - t0) * 1000,
                    error=f"Assessment timed out after {timeout}s",
                    attempts=attempts,
                    timed_out=True,
                    metadata=self._base_metadata(context),
                )
            except Exception as exc:
                last_error = exc
                # Retry hook surface for Sprint 8+; retries are not performed yet.
                if attempts < self._max_attempts and self._on_retry is not None:
                    await _maybe_await(self._on_retry(engine, context, attempts, exc))
                    continue
                completed_at = datetime.now(UTC)
                return ExecutionResult(
                    assessment_key=engine.assessment_key,
                    engine_name=engine.name,
                    engine_version=engine.version,
                    status=AssessmentStatus.ERROR,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=(time.perf_counter() - t0) * 1000,
                    error=str(exc) or exc.__class__.__name__,
                    attempts=attempts,
                    metadata=self._base_metadata(context),
                )

        completed_at = datetime.now(UTC)
        return ExecutionResult(
            assessment_key=engine.assessment_key,
            engine_name=engine.name,
            engine_version=engine.version,
            status=AssessmentStatus.ERROR,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=(time.perf_counter() - t0) * 1000,
            error=str(last_error) if last_error else "Unknown execution failure",
            attempts=attempts,
            metadata=self._base_metadata(context),
        )

    async def _run_with_timeout(
        self,
        engine: AssessmentEngine,
        context: ScanContext,
        timeout: float | None,
    ) -> EngineResult:
        async def _pipeline() -> EngineResult:
            try:
                await engine.validate(context)
                sdk_result = await engine.run(context)
                if isinstance(sdk_result, EngineResult):
                    # Backward-compatible path for legacy test doubles.
                    return sdk_result
                if isinstance(sdk_result, AssessmentResult):
                    return to_engine_result(sdk_result)
                raise TypeError(
                    "AssessmentEngine.run must return AssessmentResult, "
                    f"got {type(sdk_result)!r}"
                )
            finally:
                await engine.cleanup(context)

        if timeout is None:
            return await _pipeline()
        if timeout <= 0:
            raise TimeoutError("timeout_seconds must be > 0 when provided")
        return await asyncio.wait_for(_pipeline(), timeout=timeout)

    @staticmethod
    def _base_metadata(context: ScanContext) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "scan_id": getattr(context.scan, "id", None),
            "catalog_slug": getattr(context.catalog_entry, "slug", None),
        }
        assessment = context.assessment
        if assessment is not None and getattr(assessment, "id", None) is not None:
            meta["assessment_id"] = assessment.id
        return meta
