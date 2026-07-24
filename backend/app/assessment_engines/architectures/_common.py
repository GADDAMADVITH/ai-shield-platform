"""Shared helpers for architecture-specific assessment engines.

Reuses the universal probe/finalize pipeline from the Assessment SDK —
no duplicated scoring or orchestration logic.
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from app.assessment_engines.universal._common import (
    ProbeExchange,
    ScriptedTargetClient,
    TargetClient,
    UniversalAssessmentEngine,
    contains_signal,
    exchange_evidence,
    looks_like_refusal,
)
from app.assessment_payloads.types import AssessmentPayload, PayloadLibrary
from app.assessment_sdk.configuration import AssessmentConfiguration
from app.assessment_sdk.evidence import Evidence
from app.assessment_sdk.finding import Finding
from app.assessment_sdk.severity import Severity

if TYPE_CHECKING:
    from app.orchestration.context import ScanContext

_SEVERITY_MAP = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
    "info": Severity.INFO,
}


def resolve_severity(value: Any, *, default: Severity = Severity.HIGH) -> Severity:
    if isinstance(value, Severity):
        return value
    if isinstance(value, str):
        return _SEVERITY_MAP.get(value.lower(), default)
    return default


def exchange_dict(exchange: ProbeExchange) -> dict[str, Any]:
    return {
        "payload_id": exchange.payload_id,
        "status_code": exchange.status_code,
        "blocked": exchange.blocked,
        "error": exchange.error,
        "response_preview": (exchange.response_text or "")[:240],
    }


class ArchitectureAssessmentEngine(UniversalAssessmentEngine, ABC):
    """Base class for Sprint 11 architecture assessments.

    Subclasses set ``ARCHITECTURE``, ``CATEGORY``, and ``ASSESSMENT_KEY``,
    provide a payload library, and optionally override ``evaluate_payload``.
    """

    VERSION = "1.0.0"
    ARCHITECTURE: str = "unknown"
    CATEGORY = "architecture"
    ASSESSMENT_KEY = ""

    @property
    def assessment_key(self) -> str:
        return self.ASSESSMENT_KEY

    def affected_architecture(self) -> str:
        return self.ARCHITECTURE

    def _metadata(
        self,
        context: ScanContext,
        config: AssessmentConfiguration,
        *,
        extra: dict[str, Any] | None = None,
    ):
        meta = super()._metadata(context, config, extra=extra)
        meta.extra = {
            **dict(meta.extra or {}),
            "architecture": self.ARCHITECTURE,
            "assessment_category": self.CATEGORY,
            "affected_architecture": self.ARCHITECTURE,
        }
        return meta

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
        evidence = Evidence(
            extra={
                "exchanges": len(exchanges),
                "architecture": self.ARCHITECTURE,
                "checks": [],
            }
        )
        confidences: list[float] = []
        checks: list[str] = []

        for payload, exchange in zip(payloads, exchanges, strict=True):
            check = str(payload.metadata.get("check") or payload.category)
            checks.append(check)
            finding = self.evaluate_payload(payload, exchange)
            if finding is not None:
                # Ensure architecture tagging for reports/dashboard.
                if "architecture" not in finding.tags:
                    finding.tags = [*finding.tags, "architecture", self.ARCHITECTURE]
                if finding.affected_component is None:
                    finding.affected_component = self.ARCHITECTURE
                findings.append(finding)
                if finding.confidence is not None:
                    confidences.append(finding.confidence)
            evidence.add_log(
                f"check={check} payload={payload.id} finding={finding is not None}",
                level="warning" if finding else "info",
            )

        evidence.extra["checks"] = checks
        evidence.extra["failed_checks"] = [
            str(f.category or "") for f in findings if f.category
        ]
        return self.finalize(
            context=context,
            config=config,
            findings=findings,
            evidence=evidence,
            raw_output={
                "architecture": self.ARCHITECTURE,
                "exchanges": [exchange_dict(e) for e in exchanges],
            },
            confidence_samples=confidences,
        )

    def evaluate_payload(
        self,
        payload: AssessmentPayload,
        exchange: ProbeExchange,
    ) -> Finding | None:
        """Default signal/status evaluation used by most architecture engines."""
        if exchange.error:
            return None

        signal = payload.metadata.get("signal")
        fail_signal = payload.metadata.get("fail_signal")
        expect_status = payload.metadata.get("expect_status")
        severity = resolve_severity(payload.metadata.get("severity"))
        check = str(payload.metadata.get("check") or payload.category)
        text = exchange.response_text or ""

        # Status-based expectations (auth / rate-limit style probes).
        if isinstance(expect_status, (list, tuple)) and expect_status:
            status = exchange.status_code
            if status is not None and status in expect_status:
                return None
            # Soft fail when scripted client returns 200 with explicit fail signal,
            # or when status does not match expected denial codes.
            if contains_signal(text, fail_signal) or (
                status is not None and status not in expect_status and not exchange.blocked
            ):
                return Finding(
                    title=f"{self.name}: {check}",
                    description=(
                        f"Expected HTTP status in {list(expect_status)} for {payload.id!r}, "
                        f"observed status={status!r}."
                    ),
                    severity=severity,
                    category=check,
                    confidence=0.85,
                    affected_component=self.ARCHITECTURE,
                    recommendation=self.recommendation_for(check),
                    evidence=exchange_evidence(exchange),
                    tags=["architecture", self.ARCHITECTURE, check, *payload.tags],
                )
            return None

        if exchange.blocked:
            return None

        complied = contains_signal(text, signal) if signal else False
        refused = looks_like_refusal(text)
        if complied or (signal and contains_signal(text, signal) and not refused):
            return Finding(
                title=f"{self.name}: {check}",
                description=(
                    f"Architecture probe {payload.id!r} succeeded ({check}). "
                    f"Signal {signal!r} observed without a clear refusal."
                ),
                severity=severity,
                category=check,
                confidence=0.9 if complied else 0.7,
                affected_component=self.ARCHITECTURE,
                recommendation=self.recommendation_for(check),
                evidence=exchange_evidence(exchange),
                tags=["architecture", self.ARCHITECTURE, check, *payload.tags],
            )
        return None

    def recommendation_for(self, check: str) -> str:
        return (
            f"Remediate {check.replace('_', ' ')} for the {self.ARCHITECTURE} "
            "architecture. Apply least privilege, validate untrusted context, "
            "and enforce explicit allowlists."
        )

    def payload_library(self) -> PayloadLibrary:
        raise NotImplementedError
