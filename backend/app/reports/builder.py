"""Report composition utilities — build JSON reports from completed scans."""

from __future__ import annotations

from typing import Any

from app.assessment_sdk.scoring import (
    calculate_overall_score,
    calculate_risk_score,
    normalize_score,
)
from app.assessment_sdk.severity import Severity, max_severity, severity_rank
from app.common.enums import AssessmentStatus
from app.services.findings import (
    FindingView,
    extract_scan_findings,
    group_findings,
    severity_counts,
)


def posture_from_risk(risk_score: float) -> float:
    """Map 0–100 risk (higher worse) to a security posture score (higher better)."""
    return normalize_score(100.0 - float(risk_score))


def derive_overall_severity(
    findings: list[FindingView],
    *,
    default: Severity = Severity.INFO,
) -> Severity:
    if not findings:
        return default
    return max_severity(*(f.severity for f in findings))


def security_posture_label(posture: float) -> str:
    if posture >= 90:
        return "Strong"
    if posture >= 75:
        return "Good"
    if posture >= 60:
        return "Fair"
    if posture >= 40:
        return "Weak"
    return "Critical"


def risk_level_label(risk: float) -> str:
    if risk >= 75:
        return "Critical"
    if risk >= 50:
        return "High"
    if risk >= 25:
        return "Medium"
    if risk > 0:
        return "Low"
    return "Minimal"


def build_executive_summary(
    *,
    findings: list[FindingView],
    assessment_count: int,
    passed: int,
    failed: int,
    execution_duration_ms: int | None = None,
) -> dict[str, Any]:
    counts = severity_counts(findings)
    risk = calculate_risk_score([f.severity for f in findings])
    posture = posture_from_risk(risk)
    overall_sev = derive_overall_severity(findings)
    top = sorted(
        findings,
        key=lambda f: (severity_rank(f.severity), f.confidence or 0.0),
        reverse=True,
    )[:5]
    return {
        "overall_risk_score": risk,
        "overall_security_score": posture,
        "overall_severity": overall_sev.value,
        "total_findings": len(findings),
        "critical_findings": counts["critical"],
        "high_findings": counts["high"],
        "medium_findings": counts["medium"],
        "low_findings": counts["low"],
        "info_findings": counts["info"],
        "assessment_count": assessment_count,
        "assessments_passed": passed,
        "assessments_failed": failed,
        "top_risks": [
            {
                "id": f.id,
                "title": f.title,
                "severity": f.severity.value,
                "category": f.category,
                "assessment_key": f.assessment_key,
            }
            for f in top
        ],
        "overall_security_posture": security_posture_label(posture),
        "risk_level": risk_level_label(risk),
        "execution_duration_ms": execution_duration_ms,
    }


def build_risk_summary(findings: list[FindingView], assessments: list[Any]) -> dict[str, Any]:
    counts = severity_counts(findings)
    scores = [float(a.score) for a in assessments if getattr(a, "score", None) is not None]
    # Treat stored assessment scores as risk contributions when failed, else posture.
    # Prefer finding-based risk as the canonical metric.
    risk = calculate_risk_score([f.severity for f in findings])
    avg_assessment = calculate_overall_score(scores) if scores else posture_from_risk(risk)
    return {
        "overall_risk_score": risk,
        "average_assessment_score": avg_assessment,
        "severity_distribution": counts,
        "highest_finding_severity": derive_overall_severity(findings).value,
        "findings_by_assessment": {
            key: len(items)
            for key, items in group_findings(findings, by="assessment").items()
        },
    }


def build_json_report(scan: Any, *, report: Any | None = None) -> dict[str, Any]:
    """Compose a full JSON security report from a loaded scan graph."""
    assessments = list(getattr(scan, "assessments", None) or [])
    findings = extract_scan_findings(scan)
    summary_row = getattr(scan, "summary", None)
    passed = int(getattr(summary_row, "passed", 0) or 0)
    failed = int(getattr(summary_row, "failed", 0) or 0)
    if summary_row is None:
        passed = sum(1 for a in assessments if a.status == AssessmentStatus.PASSED)
        failed = sum(
            1
            for a in assessments
            if a.status in {AssessmentStatus.FAILED, AssessmentStatus.ERROR}
        )
    duration = (
        getattr(summary_row, "execution_duration_ms", None)
        or getattr(scan, "execution_time_ms", None)
        or 0
    )
    executive = build_executive_summary(
        findings=findings,
        assessment_count=len(assessments),
        passed=passed,
        failed=failed,
        execution_duration_ms=int(duration or 0),
    )
    risk = build_risk_summary(findings, assessments)
    grouped = group_findings(findings, by="severity")
    project = getattr(scan, "project", None)
    connection = getattr(scan, "connection", None)

    recommendations: list[dict[str, Any]] = []
    seen_rec: set[str] = set()
    for finding in findings:
        text = (finding.recommendation or "").strip()
        if text and text not in seen_rec:
            seen_rec.add(text)
            recommendations.append(
                {
                    "title": finding.title,
                    "description": text,
                    "priority": finding.severity.value,
                    "assessment_key": finding.assessment_key,
                    "finding_id": finding.id,
                }
            )
    for assessment in assessments:
        text = (getattr(assessment, "recommendation", None) or "").strip()
        if text and text not in seen_rec:
            seen_rec.add(text)
            catalog = getattr(assessment, "catalog_entry", None)
            recommendations.append(
                {
                    "title": getattr(catalog, "name", None) or "Assessment recommendation",
                    "description": text,
                    "priority": getattr(assessment.severity, "value", str(assessment.severity)),
                    "assessment_key": getattr(catalog, "slug", None),
                    "finding_id": None,
                }
            )

    assessment_blocks = []
    for assessment in sorted(assessments, key=lambda a: a.created_at):
        catalog = getattr(assessment, "catalog_entry", None)
        assessment_blocks.append(
            {
                "id": str(assessment.id),
                "assessment_key": getattr(catalog, "slug", None),
                "assessment_name": getattr(catalog, "name", None),
                "status": assessment.status.value,
                "severity": assessment.severity.value,
                "risk_score": assessment.score,
                "confidence": assessment.confidence,
                "finding_summary": assessment.finding_summary,
                "recommendation": assessment.recommendation,
                "execution_time_ms": assessment.execution_time_ms,
                "evidence": dict(assessment.evidence or {}),
                "metadata": dict(assessment.metadata_ or {}),
                "findings": [
                    f.to_dict()
                    for f in findings
                    if f.assessment_id == str(assessment.id)
                ],
            }
        )

    return {
        "report": {
            "id": str(report.id) if report is not None else None,
            "title": getattr(report, "title", None)
            or f"Security Report — {getattr(project, 'name', 'Scan')}",
            "status": getattr(getattr(report, "status", None), "value", None) or "ready",
            "created_at": (
                report.created_at.isoformat()
                if report is not None and getattr(report, "created_at", None)
                else None
            ),
            "summary_text": getattr(report, "summary", None) or _summary_text(executive),
        },
        "scan": {
            "id": str(scan.id),
            "project_id": str(scan.project_id),
            "connection_id": str(scan.connection_id) if scan.connection_id else None,
            "status": scan.status.value,
            "profile": scan.profile,
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
            "execution_time_ms": scan.execution_time_ms,
            "error_message": scan.error_message,
        },
        "project": {
            "id": str(project.id) if project else None,
            "name": getattr(project, "name", None),
            "environment": getattr(getattr(project, "environment", None), "value", None)
            or getattr(project, "environment", None),
            "application_type": getattr(project, "application_type", None),
        },
        "connection": {
            "id": str(connection.id) if connection else None,
            "name": getattr(connection, "name", None),
            "connection_method": getattr(
                getattr(connection, "connection_method", None), "value", None
            )
            or getattr(connection, "connection_method", None),
            "base_url": getattr(connection, "base_url", None),
        },
        "executive_summary": executive,
        "risk_summary": risk,
        "findings": {
            "total": len(findings),
            "items": [f.to_dict() for f in findings],
            "by_severity": {
                sev: [f.to_dict() for f in items] for sev, items in grouped.items()
            },
            "by_category": {
                cat: [f.to_dict() for f in items]
                for cat, items in group_findings(findings, by="category").items()
            },
            "by_assessment": {
                key: [f.to_dict() for f in items]
                for key, items in group_findings(findings, by="assessment").items()
            },
        },
        "recommendations": recommendations,
        "evidence": [
            {
                "finding_id": f.id,
                "assessment_key": f.assessment_key,
                "evidence": f.evidence,
            }
            for f in findings
            if f.evidence
        ],
        "assessments": assessment_blocks,
        "scan_summary": {
            "overall_score": executive["overall_security_score"],
            "overall_risk_score": executive["overall_risk_score"],
            "critical": executive["critical_findings"],
            "high": executive["high_findings"],
            "medium": executive["medium_findings"],
            "low": executive["low_findings"],
            "passed": passed,
            "failed": failed,
            "total_findings": len(findings),
            "execution_duration_ms": int(duration or 0),
        },
    }


def _summary_text(executive: dict[str, Any]) -> str:
    return (
        f"Security posture {executive['overall_security_posture']} "
        f"(score {executive['overall_security_score']:.1f}/100). "
        f"Risk {executive['risk_level']} "
        f"({executive['overall_risk_score']:.1f}/100). "
        f"{executive['total_findings']} finding(s): "
        f"{executive['critical_findings']} critical, "
        f"{executive['high_findings']} high, "
        f"{executive['medium_findings']} medium, "
        f"{executive['low_findings']} low."
    )
