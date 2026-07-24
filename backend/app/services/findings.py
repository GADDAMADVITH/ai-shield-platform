"""Finding extraction and grouping from persisted assessments."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import uuid4

from app.assessment_sdk.severity import Severity
from app.common.enums import AssessmentStatus

GroupBy = Literal["severity", "category", "assessment"]


@dataclass(slots=True)
class FindingView:
    """Normalized finding for reports, dashboards, and explorers."""

    id: str
    title: str
    description: str
    severity: Severity
    category: str | None = None
    confidence: float | None = None
    recommendation: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    assessment_id: str | None = None
    assessment_key: str | None = None
    assessment_name: str | None = None
    scan_id: str | None = None
    project_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "evidence": dict(self.evidence),
            "tags": list(self.tags),
            "assessment_id": self.assessment_id,
            "assessment_key": self.assessment_key,
            "assessment_name": self.assessment_name,
            "scan_id": self.scan_id,
            "project_id": self.project_id,
        }


def _coerce_severity(value: Any, *, default: Severity = Severity.MEDIUM) -> Severity:
    if isinstance(value, Severity):
        return value
    try:
        return Severity(str(value).lower())
    except ValueError:
        return default


def _findings_payload(assessment: Any) -> list[dict[str, Any]]:
    meta = getattr(assessment, "metadata_", None) or {}
    if isinstance(meta, dict):
        raw = meta.get("findings")
        if isinstance(raw, list) and raw:
            return [item for item in raw if isinstance(item, dict)]
    raw_result = getattr(assessment, "raw_result", None) or {}
    if isinstance(raw_result, dict):
        nested_meta = raw_result.get("metadata")
        if isinstance(nested_meta, dict):
            raw = nested_meta.get("findings")
            if isinstance(raw, list) and raw:
                return [item for item in raw if isinstance(item, dict)]
        # EngineResult metadata may be nested under raw_result.metadata findings
        raw = raw_result.get("findings")
        if isinstance(raw, list) and raw:
            return [item for item in raw if isinstance(item, dict)]
    return []


def extract_assessment_findings(assessment: Any, *, scan: Any | None = None) -> list[FindingView]:
    """Extract structured findings from one assessment row."""
    catalog = getattr(assessment, "catalog_entry", None)
    assessment_key = getattr(catalog, "slug", None)
    assessment_name = getattr(catalog, "name", None)
    scan_id = str(getattr(assessment, "scan_id", None) or getattr(scan, "id", "") or "") or None
    project_id = str(getattr(scan, "project_id", None) or "") or None
    payload = _findings_payload(assessment)
    views: list[FindingView] = []

    for item in payload:
        views.append(
            FindingView(
                id=str(item.get("id") or uuid4()),
                title=str(item.get("title") or "Finding"),
                description=str(item.get("description") or ""),
                severity=_coerce_severity(item.get("severity"), default=assessment.severity),
                category=item.get("category") or assessment_key,
                confidence=item.get("confidence"),
                recommendation=item.get("recommendation")
                or getattr(assessment, "recommendation", None),
                evidence=dict(item.get("evidence") or {})
                if isinstance(item.get("evidence"), dict)
                else dict(getattr(assessment, "evidence", None) or {}),
                tags=list(item.get("tags") or []),
                assessment_id=str(assessment.id),
                assessment_key=assessment_key,
                assessment_name=assessment_name,
                scan_id=scan_id,
                project_id=project_id,
            )
        )

    if views:
        return views

    # Fallback: synthesize a finding for failed/error assessments without structured data.
    if assessment.status in {AssessmentStatus.FAILED, AssessmentStatus.ERROR}:
        summary = assessment.finding_summary or f"{assessment_name or 'Assessment'} failed"
        views.append(
            FindingView(
                id=str(assessment.id),
                title=summary[:160],
                description=summary,
                severity=_coerce_severity(assessment.severity),
                category=assessment_key,
                confidence=assessment.confidence,
                recommendation=assessment.recommendation,
                evidence=dict(assessment.evidence or {}),
                tags=["synthetic"],
                assessment_id=str(assessment.id),
                assessment_key=assessment_key,
                assessment_name=assessment_name,
                scan_id=scan_id,
                project_id=project_id,
            )
        )
    return views


def extract_scan_findings(scan: Any) -> list[FindingView]:
    findings: list[FindingView] = []
    for assessment in getattr(scan, "assessments", None) or []:
        findings.extend(extract_assessment_findings(assessment, scan=scan))
    return findings


def group_findings(
    findings: list[FindingView],
    *,
    by: GroupBy = "severity",
) -> dict[str, list[FindingView]]:
    grouped: dict[str, list[FindingView]] = defaultdict(list)
    for finding in findings:
        if by == "severity":
            key = finding.severity.value
        elif by == "category":
            key = finding.category or "uncategorized"
        else:
            key = finding.assessment_key or finding.assessment_id or "unknown"
        grouped[key].append(finding)
    return dict(grouped)


def severity_counts(findings: list[FindingView]) -> dict[str, int]:
    counts = {s.value: 0 for s in Severity}
    for finding in findings:
        counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1
    return counts


def filter_findings(
    findings: list[FindingView],
    *,
    severity: str | None = None,
    category: str | None = None,
    assessment_key: str | None = None,
    q: str | None = None,
) -> list[FindingView]:
    result = findings
    if severity:
        sev = severity.lower()
        result = [f for f in result if f.severity.value == sev]
    if category:
        cat = category.lower()
        result = [f for f in result if (f.category or "").lower() == cat]
    if assessment_key:
        key = assessment_key.lower()
        result = [f for f in result if (f.assessment_key or "").lower() == key]
    if q:
        needle = q.lower()
        result = [
            f
            for f in result
            if needle in f.title.lower()
            or needle in f.description.lower()
            or needle in (f.category or "").lower()
        ]
    return result
