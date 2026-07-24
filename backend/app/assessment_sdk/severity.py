"""SDK severity levels — single source aligned with domain enums."""

from __future__ import annotations

from app.common.enums import Severity

__all__ = ["Severity", "severity_rank"]

_RANK: dict[Severity, int] = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


def severity_rank(severity: Severity | str) -> int:
    """Return a comparable rank for severity (higher = worse)."""
    if isinstance(severity, str):
        severity = Severity(severity.lower())
    return _RANK[severity]


def max_severity(*severities: Severity) -> Severity:
    """Return the highest severity among *severities* (defaults to INFO)."""
    if not severities:
        return Severity.INFO
    return max(severities, key=severity_rank)
