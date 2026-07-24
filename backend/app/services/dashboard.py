"""Dashboard aggregates, risk analytics, and scan history."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.assessment_sdk.scoring import calculate_overall_score, calculate_risk_score
from app.assessment_sdk.severity import Severity, max_severity
from app.common.enums import AssessmentStatus, ScanStatus
from app.common.exceptions import NotFoundError
from app.common.pagination import Page, PaginationParams
from app.models.assessment import Assessment
from app.models.project import Project
from app.models.scan import Scan
from app.models.scan_summary import ScanSummary
from app.models.user import User
from app.reports.builder import (
    build_executive_summary,
    posture_from_risk,
    security_posture_label,
)
from app.schemas.dashboard import (
    DashboardOverview,
    DashboardRecentScan,
    DashboardStatistics,
    RiskAnalytics,
    ScanHistoryItem,
    SeverityDistribution,
)
from app.services.findings import extract_scan_findings, filter_findings, group_findings
from app.services.notifications import recent_notifications_payload


def _owned_scans_query(owner_id: uuid.UUID) -> Select[Any]:
    return (
        select(Scan)
        .join(Project, Project.id == Scan.project_id)
        .where(Project.owner_id == owner_id)
    )


async def get_scan_summary_for_owner(
    session: AsyncSession,
    *,
    scan_id: uuid.UUID,
    owner: User,
) -> dict[str, Any]:
    result = await session.execute(
        _owned_scans_query(owner.id)
        .where(Scan.id == scan_id)
        .options(
            selectinload(Scan.assessments).selectinload(Assessment.catalog_entry),
            selectinload(Scan.summary),
            selectinload(Scan.project),
        )
    )
    scan = result.scalar_one_or_none()
    if scan is None:
        raise NotFoundError("Scan not found")
    findings = extract_scan_findings(scan)
    summary = scan.summary
    executive = build_executive_summary(
        findings=findings,
        assessment_count=len(scan.assessments or []),
        passed=int(getattr(summary, "passed", 0) or 0),
        failed=int(getattr(summary, "failed", 0) or 0),
        execution_duration_ms=int(
            getattr(summary, "execution_duration_ms", None) or scan.execution_time_ms or 0
        ),
    )
    return {
        "scan_id": str(scan.id),
        "project_id": str(scan.project_id),
        "project_name": getattr(scan.project, "name", None),
        "status": scan.status.value,
        "executive_summary": executive,
        "scan_summary": {
            "overall_score": executive["overall_security_score"],
            "overall_risk_score": executive["overall_risk_score"],
            "critical": executive["critical_findings"],
            "high": executive["high_findings"],
            "medium": executive["medium_findings"],
            "low": executive["low_findings"],
            "passed": executive["assessments_passed"],
            "failed": executive["assessments_failed"],
            "total_findings": executive["total_findings"],
            "execution_duration_ms": executive["execution_duration_ms"],
        },
        "findings_total": len(findings),
    }


async def list_scan_history(
    session: AsyncSession,
    *,
    owner: User,
    params: PaginationParams,
    status: ScanStatus | None = None,
    project_id: uuid.UUID | None = None,
    sort: Literal["newest", "oldest", "score_desc", "score_asc"] = "newest",
) -> Page[ScanHistoryItem]:
    filters = [Project.owner_id == owner.id]
    if status is not None:
        filters.append(Scan.status == status)
    if project_id is not None:
        filters.append(Scan.project_id == project_id)

    total = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Scan)
                .join(Project, Project.id == Scan.project_id)
                .where(*filters)
            )
        ).scalar_one()
    )

    order: Any
    if sort == "oldest":
        order = Scan.created_at.asc()
    elif sort == "score_desc":
        order = ScanSummary.overall_score.desc().nullslast()
    elif sort == "score_asc":
        order = ScanSummary.overall_score.asc().nullslast()
    else:
        order = Scan.created_at.desc()

    stmt = (
        select(Scan)
        .join(Project, Project.id == Scan.project_id)
        .outerjoin(ScanSummary, ScanSummary.scan_id == Scan.id)
        .where(*filters)
        .options(
            selectinload(Scan.project),
            selectinload(Scan.summary),
            selectinload(Scan.assessments).selectinload(Assessment.catalog_entry),
        )
        .order_by(order)
        .offset(params.offset)
        .limit(params.limit)
    )
    result = await session.execute(stmt)
    scans = list(result.scalars().unique().all())
    items: list[ScanHistoryItem] = []
    for scan in scans:
        findings = extract_scan_findings(scan)
        risk = calculate_risk_score([f.severity for f in findings])
        summary = scan.summary
        items.append(
            ScanHistoryItem(
                id=scan.id,
                project_id=scan.project_id,
                project_name=getattr(scan.project, "name", None),
                environment=getattr(
                    getattr(scan.project, "environment", None), "value", None
                )
                or getattr(scan.project, "environment", None),
                status=scan.status,
                profile=scan.profile,
                overall_security_score=posture_from_risk(risk)
                if findings or summary
                else (float(summary.overall_score) if summary else None),
                overall_risk_score=risk,
                total_findings=len(findings)
                if findings
                else int(getattr(summary, "total_findings", 0) or 0),
                critical=int(getattr(summary, "critical", 0) or 0),
                high=int(getattr(summary, "high", 0) or 0),
                medium=int(getattr(summary, "medium", 0) or 0),
                low=int(getattr(summary, "low", 0) or 0),
                execution_time_ms=scan.execution_time_ms,
                started_at=scan.started_at,
                completed_at=scan.completed_at,
                created_at=scan.created_at,
            )
        )
    return Page.from_items(items, total=total, params=params)


async def build_dashboard_overview(
    session: AsyncSession,
    *,
    owner: User,
) -> DashboardOverview:
    project_count = int(
        (
            await session.execute(
                select(func.count()).select_from(Project).where(Project.owner_id == owner.id)
            )
        ).scalar_one()
    )
    scan_rows = list(
        (
            await session.execute(
                _owned_scans_query(owner.id).options(
                    selectinload(Scan.summary),
                    selectinload(Scan.project),
                    selectinload(Scan.assessments).selectinload(Assessment.catalog_entry),
                )
            )
        )
        .scalars()
        .unique()
        .all()
    )
    successful = sum(1 for s in scan_rows if s.status == ScanStatus.COMPLETED)
    failed = sum(1 for s in scan_rows if s.status == ScanStatus.FAILED)

    all_findings = []
    risk_scores: list[float] = []
    for scan in scan_rows:
        findings = extract_scan_findings(scan)
        all_findings.extend(findings)
        risk_scores.append(calculate_risk_score([f.severity for f in findings]))

    avg_risk = calculate_overall_score(risk_scores) if risk_scores else 0.0
    avg_security = posture_from_risk(avg_risk)
    counts = {
        "critical": sum(1 for f in all_findings if f.severity == Severity.CRITICAL),
        "high": sum(1 for f in all_findings if f.severity == Severity.HIGH),
        "medium": sum(1 for f in all_findings if f.severity == Severity.MEDIUM),
        "low": sum(1 for f in all_findings if f.severity == Severity.LOW),
    }
    overall_sev = (
        max_severity(*(f.severity for f in all_findings)) if all_findings else Severity.INFO
    )

    recent = sorted(scan_rows, key=lambda s: s.created_at, reverse=True)[:6]
    activity = []
    for scan in recent:
        findings = extract_scan_findings(scan)
        risk = calculate_risk_score([f.severity for f in findings])
        activity.append(
            {
                "type": "scan",
                "scan_id": str(scan.id),
                "project_id": str(scan.project_id),
                "project_name": getattr(scan.project, "name", None),
                "status": scan.status.value,
                "total_findings": len(findings),
                "overall_risk_score": risk,
                "overall_security_score": posture_from_risk(risk),
                "created_at": scan.created_at.isoformat(),
            }
        )

    return DashboardOverview(
        total_projects=project_count,
        total_scans=len(scan_rows),
        successful_scans=successful,
        failed_scans=failed,
        average_risk_score=avg_risk,
        average_security_score=avg_security,
        critical_findings=counts["critical"],
        high_findings=counts["high"],
        medium_findings=counts["medium"],
        low_findings=counts["low"],
        total_findings=len(all_findings),
        overall_security_posture=security_posture_label(avg_security),
        overall_severity=overall_sev,
        latest_activity=activity,
    )


async def build_risk_analytics(session: AsyncSession, *, owner: User) -> RiskAnalytics:
    scans = list(
        (
            await session.execute(
                _owned_scans_query(owner.id).options(
                    selectinload(Scan.summary),
                    selectinload(Scan.project),
                    selectinload(Scan.assessments).selectinload(Assessment.catalog_entry),
                )
            )
        )
        .scalars()
        .unique()
        .all()
    )
    per_scan_risk: list[tuple[Scan, float, int]] = []
    assessment_dist: dict[str, int] = defaultdict(int)
    status_dist: dict[str, int] = defaultdict(int)
    all_findings = []

    for scan in scans:
        status_dist[scan.status.value] += 1
        findings = extract_scan_findings(scan)
        all_findings.extend(findings)
        risk = calculate_risk_score([f.severity for f in findings])
        per_scan_risk.append((scan, risk, len(findings)))
        for assessment in scan.assessments or []:
            catalog = getattr(assessment, "catalog_entry", None)
            key = getattr(catalog, "slug", None) or str(assessment.assessment_catalog_id)
            if assessment.status in {AssessmentStatus.FAILED, AssessmentStatus.ERROR}:
                assessment_dist[key] += 1
            else:
                assessment_dist.setdefault(key, assessment_dist.get(key, 0))

    risks = [r for _, r, _ in per_scan_risk]
    avg_risk = calculate_overall_score(risks) if risks else 0.0
    highest = None
    if per_scan_risk:
        scan, risk, findings_count = max(per_scan_risk, key=lambda row: row[1])
        highest = {
            "scan_id": str(scan.id),
            "project_id": str(scan.project_id),
            "project_name": getattr(scan.project, "name", None),
            "overall_risk_score": risk,
            "overall_security_score": posture_from_risk(risk),
            "total_findings": findings_count,
            "status": scan.status.value,
        }

    # Risk trend: last 14 days daily average risk
    cutoff = datetime.now(UTC) - timedelta(days=14)
    buckets: dict[str, list[float]] = defaultdict(list)
    for scan, risk, _ in per_scan_risk:
        if scan.created_at and scan.created_at >= cutoff:
            buckets[scan.created_at.date().isoformat()].append(risk)
    trend = [
        {"date": day, "average_risk_score": round(sum(vals) / len(vals), 2)}
        for day, vals in sorted(buckets.items())
    ]

    sev = SeverityDistribution(
        critical=sum(1 for f in all_findings if f.severity == Severity.CRITICAL),
        high=sum(1 for f in all_findings if f.severity == Severity.HIGH),
        medium=sum(1 for f in all_findings if f.severity == Severity.MEDIUM),
        low=sum(1 for f in all_findings if f.severity == Severity.LOW),
        info=sum(1 for f in all_findings if f.severity == Severity.INFO),
    )
    return RiskAnalytics(
        overall_risk_score=avg_risk,
        average_risk_score=avg_risk,
        average_security_score=posture_from_risk(avg_risk),
        highest_risk_scan=highest,
        risk_trend=trend,
        assessment_distribution=dict(assessment_dist),
        severity_distribution=sev,
        scan_status_distribution=dict(status_dist),
    )


async def build_dashboard_recent(
    session: AsyncSession,
    *,
    owner: User,
    limit: int = 10,
) -> tuple[list[DashboardRecentScan], list[dict[str, Any]]]:
    result = await session.execute(
        _owned_scans_query(owner.id)
        .options(
            selectinload(Scan.project),
            selectinload(Scan.summary),
            selectinload(Scan.assessments).selectinload(Assessment.catalog_entry),
        )
        .order_by(Scan.created_at.desc())
        .limit(limit)
    )
    scans = list(result.scalars().unique().all())
    items: list[DashboardRecentScan] = []
    for scan in scans:
        findings = extract_scan_findings(scan)
        risk = calculate_risk_score([f.severity for f in findings])
        summary = scan.summary
        items.append(
            DashboardRecentScan(
                id=scan.id,
                project_id=scan.project_id,
                project_name=getattr(scan.project, "name", None),
                status=scan.status,
                profile=scan.profile,
                overall_security_score=posture_from_risk(risk),
                overall_risk_score=risk,
                total_findings=len(findings),
                critical=int(getattr(summary, "critical", 0) or 0),
                high=int(getattr(summary, "high", 0) or 0),
                started_at=scan.started_at,
                completed_at=scan.completed_at,
                created_at=scan.created_at,
            )
        )
    notifications = await recent_notifications_payload(session, owner=owner, limit=8)
    return items, notifications


async def build_dashboard_statistics(
    session: AsyncSession,
    *,
    owner: User,
) -> DashboardStatistics:
    overview = await build_dashboard_overview(session, owner=owner)
    risk = await build_risk_analytics(session, owner=owner)

    # Latest assessment results across recent scans
    result = await session.execute(
        _owned_scans_query(owner.id)
        .options(
            selectinload(Scan.assessments).selectinload(Assessment.catalog_entry),
            selectinload(Scan.project),
        )
        .order_by(Scan.created_at.desc())
        .limit(5)
    )
    scans = list(result.scalars().unique().all())
    assessment_results: list[dict[str, Any]] = []
    latest_findings: list[dict[str, Any]] = []
    for scan in scans:
        for assessment in scan.assessments or []:
            catalog = getattr(assessment, "catalog_entry", None)
            assessment_results.append(
                {
                    "assessment_id": str(assessment.id),
                    "assessment_key": getattr(catalog, "slug", None),
                    "assessment_name": getattr(catalog, "name", None),
                    "status": assessment.status.value,
                    "severity": assessment.severity.value,
                    "risk_score": assessment.score,
                    "scan_id": str(scan.id),
                    "project_name": getattr(scan.project, "name", None),
                }
            )
        for finding in extract_scan_findings(scan)[:5]:
            latest_findings.append(finding.to_dict())

    latest_findings = latest_findings[:12]
    return DashboardStatistics(
        overview=overview,
        risk=risk,
        severity_distribution=risk.severity_distribution,
        assessment_results=assessment_results[:20],
        latest_findings=latest_findings,
    )


async def explore_findings(
    session: AsyncSession,
    *,
    owner: User,
    scan_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    severity: str | None = None,
    category: str | None = None,
    assessment_key: str | None = None,
    q: str | None = None,
) -> dict[str, Any]:
    stmt = _owned_scans_query(owner.id).options(
        selectinload(Scan.assessments).selectinload(Assessment.catalog_entry),
        selectinload(Scan.project),
    )
    if scan_id is not None:
        stmt = stmt.where(Scan.id == scan_id)
    if project_id is not None:
        stmt = stmt.where(Scan.project_id == project_id)
    result = await session.execute(stmt.order_by(Scan.created_at.desc()).limit(50))
    scans = list(result.scalars().unique().all())
    findings = []
    for scan in scans:
        findings.extend(extract_scan_findings(scan))
    findings = filter_findings(
        findings,
        severity=severity,
        category=category,
        assessment_key=assessment_key,
        q=q,
    )
    by_sev = group_findings(findings, by="severity")
    by_cat = group_findings(findings, by="category")
    by_asm = group_findings(findings, by="assessment")
    return {
        "total": len(findings),
        "items": [f.to_dict() for f in findings],
        "by_severity": {k: [f.to_dict() for f in v] for k, v in by_sev.items()},
        "by_category": {k: [f.to_dict() for f in v] for k, v in by_cat.items()},
        "by_assessment": {k: [f.to_dict() for f in v] for k, v in by_asm.items()},
    }
