"""Report generation package."""

from app.reports.builder import (
    build_architecture_summary,
    build_executive_summary,
    build_json_report,
    build_risk_summary,
    posture_from_risk,
)
from app.reports.pdf import render_report_pdf

__all__ = [
    "build_architecture_summary",
    "build_executive_summary",
    "build_json_report",
    "build_risk_summary",
    "posture_from_risk",
    "render_report_pdf",
]
