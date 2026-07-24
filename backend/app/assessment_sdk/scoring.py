"""Reusable scoring utilities — no assessment-specific logic."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.assessment_sdk.severity import Severity, severity_rank

# Severity → contribution toward a 0–100 risk score (higher = worse).
_SEVERITY_RISK: dict[Severity, float] = {
    Severity.INFO: 5.0,
    Severity.LOW: 25.0,
    Severity.MEDIUM: 50.0,
    Severity.HIGH: 75.0,
    Severity.CRITICAL: 100.0,
}


def normalize_score(value: float, *, minimum: float = 0.0, maximum: float = 100.0) -> float:
    """Clamp *value* into ``[minimum, maximum]`` and round to 2 decimals."""
    if maximum < minimum:
        raise ValueError("maximum must be >= minimum")
    clamped = max(minimum, min(maximum, float(value)))
    return round(clamped, 2)


def calculate_risk_score(
    severities: Sequence[Severity | str] | None = None,
    *,
    weights: Sequence[float] | None = None,
    base_score: float = 0.0,
) -> float:
    """Compute a 0–100 risk score from finding severities.

    Uses a diminishing-returns blend so multiple findings raise risk without
    simply summing past 100. When no severities are provided, returns *base_score*.
    """
    if not severities:
        return normalize_score(base_score)

    parsed = [Severity(s.lower()) if isinstance(s, str) else s for s in severities]
    if weights is not None and len(weights) != len(parsed):
        raise ValueError("weights length must match severities length")

    ranked = sorted(
        (
            (severity_rank(sev), _SEVERITY_RISK[sev], (weights[i] if weights else 1.0))
            for i, sev in enumerate(parsed)
        ),
        reverse=True,
    )
    score = 0.0
    residual = 1.0
    for _, risk, weight in ranked:
        contribution = risk * float(weight) * residual
        score += contribution
        residual *= 0.5
    return normalize_score(max(score, base_score))


def calculate_confidence(
    samples: Iterable[float] | None = None,
    *,
    default: float = 0.5,
) -> float:
    """Average confidence samples into a 0–1 value.

    Empty input returns *default*. Values outside ``[0, 1]`` are clamped.
    """
    values = [max(0.0, min(1.0, float(v))) for v in (samples or [])]
    if not values:
        return round(max(0.0, min(1.0, float(default))), 4)
    return round(sum(values) / len(values), 4)


def calculate_overall_score(
    scores: Sequence[float],
    *,
    weights: Sequence[float] | None = None,
) -> float:
    """Weighted average of assessment scores on a 0–100 scale."""
    if not scores:
        return 0.0
    if weights is not None and len(weights) != len(scores):
        raise ValueError("weights length must match scores length")
    if weights is None:
        return normalize_score(sum(scores) / len(scores))
    total_weight = sum(float(w) for w in weights)
    if total_weight <= 0:
        raise ValueError("weights must sum to a positive value")
    weighted = sum(float(s) * float(w) for s, w in zip(scores, weights, strict=True))
    return normalize_score(weighted / total_weight)
