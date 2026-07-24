"""Input validation assessment engine."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from app.assessment_engines.universal._common import (
    ProbeExchange,
    ScriptedTargetClient,
    TargetClient,
    UniversalAssessmentEngine,
    exchange_evidence,
)
from app.assessment_payloads.types import AssessmentPayload, PayloadLibrary
from app.assessment_payloads.validation import INPUT_LIBRARY
from app.assessment_sdk.configuration import AssessmentConfiguration
from app.assessment_sdk.evidence import Evidence
from app.assessment_sdk.finding import Finding
from app.assessment_sdk.severity import Severity

if TYPE_CHECKING:
    from app.orchestration.context import ScanContext


class InputValidationAssessmentEngine(UniversalAssessmentEngine):
    """Verify handling of empty, unicode, control, null, and oversized inputs."""

    ASSESSMENT_KEY = "input-validation"

    @property
    def name(self) -> str:
        return "Input Validation Assessment"

    @property
    def assessment_key(self) -> str:
        return self.ASSESSMENT_KEY

    def payload_library(self) -> PayloadLibrary:
        return INPUT_LIBRARY

    async def execute(
        self,
        context: ScanContext,
        *,
        config: AssessmentConfiguration,
        payloads: Sequence[AssessmentPayload],
        target: TargetClient | ScriptedTargetClient,
    ) -> Any:
        exchanges = await self.probe_all(
            payloads,
            target,
            retry_attempts=config.retry_attempts,
            retry_backoff_seconds=config.retry_backoff_seconds,
        )
        findings: list[Finding] = []
        confidences: list[float] = []
        evidence = Evidence(extra={"probes": len(exchanges)})

        for payload, exchange in zip(payloads, exchanges, strict=True):
            finding = self._evaluate(payload, exchange)
            if finding is not None:
                findings.append(finding)
                if finding.confidence is not None:
                    confidences.append(finding.confidence)
            evidence.add_log(
                f"payload={payload.id} status_code={exchange.status_code} "
                f"error={exchange.error!r}",
                level="warning" if finding else "info",
            )

        return self.finalize(
            context=context,
            config=config,
            findings=findings,
            evidence=evidence,
            raw_output={"finding_count": len(findings)},
            confidence_samples=confidences,
        )

    def _evaluate(
        self,
        payload: AssessmentPayload,
        exchange: ProbeExchange,
    ) -> Finding | None:
        probe = str(payload.metadata.get("probe") or payload.id)
        # Transport errors on malformed input can indicate poor validation
        # (unhandled exceptions) — treat as findings except for intentional rejects.
        if exchange.error:
            return Finding(
                title=f"Input handling failure: {payload.id}",
                description=(
                    f"Probe {probe!r} caused a transport/application error: "
                    f"{exchange.error}"
                ),
                severity=Severity.HIGH,
                category="input_validation",
                confidence=0.75,
                recommendation=(
                    "Validate and reject malformed inputs before model invocation; "
                    "never surface unhandled exceptions to clients."
                ),
                evidence=exchange_evidence(exchange),
                tags=["input-validation", probe, *payload.tags],
            )

        status = exchange.status_code
        text = exchange.response_text or ""

        if probe == "empty":
            # Empty prompts should be rejected (4xx) or handled without 5xx.
            if status is not None and status >= 500:
                return self._finding(
                    payload,
                    exchange,
                    title="Empty prompt caused server error",
                    severity=Severity.HIGH,
                    detail=f"HTTP {status} for empty prompt",
                )
            return None

        if probe == "very_long":
            # Accept reject (413/400) or truncate. Fail on 5xx or full echo of huge body.
            if status is not None and status >= 500:
                return self._finding(
                    payload,
                    exchange,
                    title="Oversized prompt caused server error",
                    severity=Severity.HIGH,
                    detail=f"HTTP {status} for very long prompt",
                )
            if len(text) >= 40_000:
                return self._finding(
                    payload,
                    exchange,
                    title="Oversized prompt not truncated",
                    severity=Severity.MEDIUM,
                    detail="Application returned an extremely large completion for a huge prompt",
                )
            return None

        if probe == "control_chars":
            # Echoing raw control characters / ANSI back is unsafe.
            if "\x1b[" in text or "\x00" in text:
                return self._finding(
                    payload,
                    exchange,
                    title="Control characters echoed unsafely",
                    severity=Severity.MEDIUM,
                    detail="Response echoed control/ANSI sequences from input",
                )
            if status is not None and status >= 500:
                return self._finding(
                    payload,
                    exchange,
                    title="Control characters caused server error",
                    severity=Severity.HIGH,
                    detail=f"HTTP {status}",
                )
            return None

        if probe in {"unicode", "null_literal", "large_payload"}:
            if status is not None and status >= 500:
                return self._finding(
                    payload,
                    exchange,
                    title=f"Input probe caused server error: {probe}",
                    severity=Severity.HIGH,
                    detail=f"HTTP {status} for {probe}",
                )
            return None

        if status is not None and status >= 500:
            return self._finding(
                payload,
                exchange,
                title=f"Server error on input probe: {payload.id}",
                severity=Severity.HIGH,
                detail=f"HTTP {status}",
            )
        return None

    def _finding(
        self,
        payload: AssessmentPayload,
        exchange: ProbeExchange,
        *,
        title: str,
        severity: Severity,
        detail: str,
    ) -> Finding:
        return Finding(
            title=title,
            description=detail,
            severity=severity,
            category="input_validation",
            confidence=0.85,
            recommendation=(
                "Add input size limits, unicode-safe sanitization, and reject empty "
                "or control-character-laden prompts before inference."
            ),
            evidence=exchange_evidence(exchange),
            tags=["input-validation", *payload.tags],
        )
