"""Report generation package."""

from app.reports.builder import (
    build_architecture_summary,
    build_executive_summary,
    build_json_report,
    build_risk_summary,
    posture_from_risk,
)

__all__ = [
    "build_architecture_summary",
    "build_executive_summary",
    "build_json_report",
    "build_risk_summary",
    "posture_from_risk",
]
