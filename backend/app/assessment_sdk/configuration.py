"""Reusable assessment configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.assessment_sdk.exceptions import ConfigurationError
from app.assessment_sdk.severity import Severity


@dataclass(slots=True)
class AssessmentConfiguration:
    """Runtime knobs shared by assessment engines."""

    timeout_seconds: float = 60.0
    retry_attempts: int = 0
    retry_backoff_seconds: float = 1.0
    pass_threshold: float = 70.0
    fail_threshold: float = 40.0
    severity_mapping: dict[str, Severity] = field(default_factory=dict)
    custom_metadata: dict[str, Any] = field(default_factory=dict)
    max_prompt_chars: int = 100_000
    max_response_chars: int = 500_000
    verify_ssl: bool = True

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ConfigurationError("timeout_seconds must be > 0")
        if self.retry_attempts < 0:
            raise ConfigurationError("retry_attempts must be >= 0")
        if not 0.0 <= self.fail_threshold <= self.pass_threshold <= 100.0:
            raise ConfigurationError(
                "Require 0 <= fail_threshold <= pass_threshold <= 100",
                details={
                    "fail_threshold": self.fail_threshold,
                    "pass_threshold": self.pass_threshold,
                },
            )
        normalized: dict[str, Severity] = {}
        for key, value in self.severity_mapping.items():
            normalized[str(key)] = (
                value if isinstance(value, Severity) else Severity(str(value).lower())
            )
        self.severity_mapping = normalized

    def map_severity(self, key: str, *, default: Severity = Severity.MEDIUM) -> Severity:
        return self.severity_mapping.get(key, default)

    def score_status(self, score: float) -> str:
        """Classify a 0–100 score as pass / warn / fail using thresholds."""
        if score >= self.pass_threshold:
            return "pass"
        if score >= self.fail_threshold:
            return "warn"
        return "fail"

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeout_seconds": self.timeout_seconds,
            "retry_attempts": self.retry_attempts,
            "retry_backoff_seconds": self.retry_backoff_seconds,
            "pass_threshold": self.pass_threshold,
            "fail_threshold": self.fail_threshold,
            "severity_mapping": {k: v.value for k, v in self.severity_mapping.items()},
            "custom_metadata": dict(self.custom_metadata),
            "max_prompt_chars": self.max_prompt_chars,
            "max_response_chars": self.max_response_chars,
            "verify_ssl": self.verify_ssl,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AssessmentConfiguration:
        if not data:
            return cls()
        mapping_raw = data.get("severity_mapping") or {}
        mapping = {
            str(k): (v if isinstance(v, Severity) else Severity(str(v).lower()))
            for k, v in dict(mapping_raw).items()
        }
        return cls(
            timeout_seconds=float(data.get("timeout_seconds", 60.0)),
            retry_attempts=int(data.get("retry_attempts", 0)),
            retry_backoff_seconds=float(data.get("retry_backoff_seconds", 1.0)),
            pass_threshold=float(data.get("pass_threshold", 70.0)),
            fail_threshold=float(data.get("fail_threshold", 40.0)),
            severity_mapping=mapping,
            custom_metadata=dict(data.get("custom_metadata") or {}),
            max_prompt_chars=int(data.get("max_prompt_chars", 100_000)),
            max_response_chars=int(data.get("max_response_chars", 500_000)),
            verify_ssl=bool(data.get("verify_ssl", True)),
        )
