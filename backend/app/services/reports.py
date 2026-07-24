"""Report persistence and retrieval services."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.enums import AuditAction, ReportStatus, ScanStatus
from app.common.exceptions import NotFoundError, ValidationAppError
from app.common.pagination import Page, PaginationParams
from app.models.assessment import Assessment
from app.models.project import Project
from app.models.report import Report
from app.models.scan import Scan
from app.models.user import User
from app.reports.builder import build_executive_summary, build_json_report, build_risk_summary
from app.services.audit import write_audit_log
from app.services.findings import extract_scan_findings
from app.services.projects import get_owned_project


def _scan_load_options() -> list[Any]:
    return [
        selectinload(Scan.assessments).selectinload(Assessment.catalog_entry),
        selectinload(Scan.summary),
        selectinload(Scan.project),
        selectinload(Scan.connection),
        selectinload(Scan.reports),
    ]


async def _load_scan_for_report(session: AsyncSession, scan_id: uuid.UUID) -> Scan | None:
    result = await session.execute(
        select(Scan).where(Scan.id == scan_id).options(*_scan_load_options())
    )
    return result.scalar_one_or_none()


async def generate_report_for_scan(
    session: AsyncSession,
    *,
    scan: Scan,
    user_id: uuid.UUID | None = None,
) -> Report:
    """Create or refresh a ready report row for a completed/failed scan."""
    if scan.status not in {ScanStatus.COMPLETED, ScanStatus.FAILED}:
        raise ValidationAppError(
            "Reports can only be generated for completed or failed scans",
            details={"status": scan.status.value},
        )

    loaded = await _load_scan_for_report(session, scan.id)
    if loaded is None:
        raise NotFoundError("Scan not found")
    scan = loaded

    findings = extract_scan_findings(scan)
    assessments = list(scan.assessments or [])
    summary = scan.summary
    passed = int(getattr(summary, "passed", 0) or 0)
    failed = int(getattr(summary, "failed", 0) or 0)
    duration = int(
        getattr(summary, "execution_duration_ms", None) or scan.execution_time_ms or 0
    )
    executive = build_executive_summary(
        findings=findings,
        assessment_count=len(assessments),
        passed=passed,
        failed=failed,
        execution_duration_ms=duration,
    )
    project_name = getattr(scan.project, "name", None) or "Project"
    title = f"{project_name} — Security Report"
    summary_text = (
        f"Security posture {executive['overall_security_posture']} "
        f"({executive['overall_security_score']:.1f}/100). "
        f"{executive['total_findings']} finding(s) across {executive['assessment_count']} "
        f"assessment(s)."
    )

    existing = None
    if scan.reports:
        existing = sorted(scan.reports, key=lambda r: r.created_at, reverse=True)[0]

    if existing is not None:
        report = existing
        report.title = title
        report.summary = summary_text
        report.status = ReportStatus.READY
    else:
        report = Report(
            project_id=scan.project_id,
            scan_id=scan.id,
            title=title,
            status=ReportStatus.READY,
            summary=summary_text,
        )
        session.add(report)

    await session.flush()
    await write_audit_log(
        session,
        action=AuditAction.REPORT_GENERATED,
        resource=f"report:{report.id}",
        description="Security report generated",
        user_id=user_id or scan.initiated_by_id,
        project_id=scan.project_id,
        scan_id=scan.id,
        metadata={"report_id": str(report.id), "findings": executive["total_findings"]},
    )
    await session.flush()
    return report


async def list_reports(
    session: AsyncSession,
    *,
    owner: User,
    params: PaginationParams,
    project_id: uuid.UUID | None = None,
) -> Page[Report]:
    if project_id is not None:
        await get_owned_project(session, project_id=project_id, owner=owner)

    filters = [Project.owner_id == owner.id]
    if project_id is not None:
        filters.append(Report.project_id == project_id)

    total = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Report)
                .join(Project, Project.id == Report.project_id)
                .where(*filters)
            )
        ).scalar_one()
    )

    result = await session.execute(
        select(Report)
        .join(Project, Project.id == Report.project_id)
        .where(*filters)
        .options(
            selectinload(Report.project),
            selectinload(Report.scan).selectinload(Scan.summary),
            selectinload(Report.scan).selectinload(Scan.assessments).selectinload(
                Assessment.catalog_entry
            ),
        )
        .order_by(Report.created_at.desc())
        .offset(params.offset)
        .limit(params.limit)
    )
    items = list(result.scalars().unique().all())
    return Page.from_items(items, total=total, params=params)


async def get_owned_report(
    session: AsyncSession,
    *,
    report_id: uuid.UUID,
    owner: User,
) -> Report:
    result = await session.execute(
        select(Report)
        .join(Project, Project.id == Report.project_id)
        .where(Report.id == report_id, Project.owner_id == owner.id)
        .options(
            selectinload(Report.project),
            selectinload(Report.scan).selectinload(Scan.assessments).selectinload(
                Assessment.catalog_entry
            ),
            selectinload(Report.scan).selectinload(Scan.summary),
            selectinload(Report.scan).selectinload(Scan.connection),
            selectinload(Report.scan).selectinload(Scan.project),
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise NotFoundError("Report not found")
    return report


async def get_report_json(
    session: AsyncSession,
    *,
    report_id: uuid.UUID,
    owner: User,
) -> dict[str, Any]:
    report = await get_owned_report(session, report_id=report_id, owner=owner)
    await write_audit_log(
        session,
        action=AuditAction.REPORT_DOWNLOADED,
        resource=f"report:{report.id}",
        description="JSON report downloaded",
        user_id=owner.id,
        project_id=report.project_id,
        scan_id=report.scan_id,
    )
    return build_json_report(report.scan, report=report)


def report_extras(report: Report) -> dict[str, Any]:
    scan = getattr(report, "scan", None)
    if scan is None:
        return {}
    findings = extract_scan_findings(scan)
    summary = getattr(scan, "summary", None)
    executive = build_executive_summary(
        findings=findings,
        assessment_count=len(getattr(scan, "assessments", None) or []),
        passed=int(getattr(summary, "passed", 0) or 0),
        failed=int(getattr(summary, "failed", 0) or 0),
        execution_duration_ms=int(getattr(summary, "execution_duration_ms", 0) or 0),
    )
    risk = build_risk_summary(findings, list(getattr(scan, "assessments", None) or []))
    return {
        "overall_security_score": executive["overall_security_score"],
        "overall_risk_score": risk["overall_risk_score"],
        "total_findings": executive["total_findings"],
        "overall_severity": executive["overall_severity"],
        "executive_summary": executive,
        "risk_summary": risk,
    }
