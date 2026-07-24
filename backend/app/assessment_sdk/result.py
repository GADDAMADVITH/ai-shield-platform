"""Reusable AssessmentResult — canonical return type for every engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.assessment_sdk.evidence import Evidence
from app.assessment_sdk.finding import Finding
from app.assessment_sdk.metadata import AssessmentMetadata
from app.assessment_sdk.recommendation import Recommendation
from app.assessment_sdk.severity import Severity, max_severity
from app.common.enums import AssessmentStatus


@dataclass(slots=True)
class AssessmentResult:
    """Standardized outcome that every assessment engine must return."""

    status: AssessmentStatus
    assessment_name: str
    assessment_version: str
    risk_score: float | None = None
    severity: Severity = Severity.INFO
    confidence: float | None = None
    findings: list[Finding] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    evidence: Evidence = field(default_factory=Evidence)
    metadata: AssessmentMetadata | dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float | None = None
    raw_output: Any = None

    def __post_init__(self) -> None:
        if self.status not in {
            AssessmentStatus.PASSED,
            AssessmentStatus.FAILED,
            AssessmentStatus.ERROR,
            AssessmentStatus.SKIPPED,
        }:
            raise ValueError(
                f"AssessmentResult.status must be a terminal status, got {self.status!r}"
            )
        if isinstance(self.severity, str):
            self.severity = Severity(self.severity.lower())
        if self.confidence is not None and not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("AssessmentResult.confidence must be between 0.0 and 1.0")
        if self.risk_score is not None and not 0.0 <= float(self.risk_score) <= 100.0:
            raise ValueError("AssessmentResult.risk_score must be between 0.0 and 100.0")
        if isinstance(self.evidence, dict):
            self.evidence = Evidence.from_dict(self.evidence)
        if isinstance(self.metadata, dict):
            self.metadata = AssessmentMetadata.from_dict(self.metadata)

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    def primary_recommendation(self) -> str | None:
        if not self.recommendations:
            return None
        return self.recommendations[0].description or self.recommendations[0].title

    def finding_summary(self) -> str | None:
        if not self.findings:
            if self.status == AssessmentStatus.PASSED:
                return f"{self.assessment_name} completed with no findings."
            return None
        titles = ", ".join(f.title for f in self.findings[:3])
        extra = self.finding_count - 3
        if extra > 0:
            return f"{self.finding_count} finding(s): {titles}, +{extra} more"
        return f"{self.finding_count} finding(s): {titles}"

    def derive_severity(self) -> Severity:
        """Compute severity from findings when present; otherwise keep current."""
        if not self.findings:
            return self.severity
        return max_severity(*(f.severity for f in self.findings))

    def to_dict(self) -> dict[str, Any]:
        meta = self.metadata
        return {
            "status": self.status.value,
            "assessment_name": self.assessment_name,
            "assessment_version": self.assessment_version,
            "risk_score": self.risk_score,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "finding_count": self.finding_count,
            "findings": [f.to_dict() for f in self.findings],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "evidence": self.evidence.to_dict(),
            "metadata": meta.to_dict() if isinstance(meta, AssessmentMetadata) else dict(meta),
            "execution_time_ms": self.execution_time_ms,
            "raw_output": self.raw_output,
        }

    @classmethod
    def passed(
        cls,
        *,
        assessment_name: str,
        assessment_version: str,
        risk_score: float = 100.0,
        confidence: float = 1.0,
        severity: Severity = Severity.INFO,
        evidence: Evidence | None = None,
        recommendations: list[Recommendation] | None = None,
        metadata: AssessmentMetadata | dict[str, Any] | None = None,
        execution_time_ms: float | None = None,
        raw_output: Any = None,
    ) -> AssessmentResult:
        return cls(
            status=AssessmentStatus.PASSED,
            assessment_name=assessment_name,
            assessment_version=assessment_version,
            risk_score=risk_score,
            confidence=confidence,
            severity=severity,
            evidence=evidence or Evidence(),
            recommendations=recommendations or [],
            metadata=metadata or {},
            execution_time_ms=execution_time_ms,
            raw_output=raw_output,
        )

    @classmethod
    def failed(
        cls,
        *,
        assessment_name: str,
        assessment_version: str,
        findings: list[Finding],
        risk_score: float | None = None,
        confidence: float | None = None,
        severity: Severity | None = None,
        recommendations: list[Recommendation] | None = None,
        evidence: Evidence | None = None,
        metadata: AssessmentMetadata | dict[str, Any] | None = None,
        execution_time_ms: float | None = None,
        raw_output: Any = None,
    ) -> AssessmentResult:
        derived = severity or (
            max_severity(*(f.severity for f in findings)) if findings else Severity.MEDIUM
        )
        return cls(
            status=AssessmentStatus.FAILED,
            assessment_name=assessment_name,
            assessment_version=assessment_version,
            risk_score=risk_score,
            confidence=confidence,
            severity=derived,
            findings=list(findings),
            recommendations=recommendations or [],
            evidence=evidence or Evidence(),
            metadata=metadata or {},
            execution_time_ms=execution_time_ms,
            raw_output=raw_output,
        )

    @classmethod
    def error(
        cls,
        *,
        assessment_name: str,
        assessment_version: str,
        message: str,
        metadata: AssessmentMetadata | dict[str, Any] | None = None,
        execution_time_ms: float | None = None,
        raw_output: Any = None,
    ) -> AssessmentResult:
        evidence = Evidence()
        evidence.add_log(message, level="error")
        return cls(
            status=AssessmentStatus.ERROR,
            assessment_name=assessment_name,
            assessment_version=assessment_version,
            severity=Severity.HIGH,
            evidence=evidence,
            metadata=metadata or {},
            execution_time_ms=execution_time_ms,
            raw_output=raw_output if raw_output is not None else {"error": message},
        )
