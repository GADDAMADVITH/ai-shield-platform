"""Scan lifecycle service — create, list, cancel, delete."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.enums import AssessmentStatus, AuditAction, ScanStatus
from app.common.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.common.pagination import Page, PaginationParams
from app.models.assessment import Assessment
from app.models.assessment_catalog import AssessmentCatalog
from app.models.scan import Scan
from app.models.user import User
from app.schemas.scan import ScanCreate
from app.services.audit import client_meta, write_audit_log
from app.services.connections import get_owned_connection
from app.services.projects import get_owned_project

DUMMY_ASSESSMENT_SLUG = "dummy"


async def _get_dummy_catalog(session: AsyncSession) -> AssessmentCatalog:
    result = await session.execute(
        select(AssessmentCatalog).where(AssessmentCatalog.slug == DUMMY_ASSESSMENT_SLUG)
    )
    catalog = result.scalar_one_or_none()
    if catalog is None or not catalog.enabled:
        raise ValidationAppError(
            "Dummy assessment catalog entry is not available. Run database migrations.",
            details={"slug": DUMMY_ASSESSMENT_SLUG},
        )
    return catalog


async def get_owned_scan(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    owner: User,
    load_details: bool = True,
) -> Scan:
    await get_owned_project(session, project_id=project_id, owner=owner)
    options = []
    if load_details:
        options = [
            selectinload(Scan.assessments).selectinload(Assessment.catalog_entry),
            selectinload(Scan.summary),
        ]
    result = await session.execute(
        select(Scan)
        .where(Scan.id == scan_id, Scan.project_id == project_id)
        .options(*options)
    )
    scan = result.scalar_one_or_none()
    if scan is None:
        raise NotFoundError("Scan not found")
    return scan


async def create_scan(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    owner: User,
    payload: ScanCreate,
    request: Any | None = None,
) -> Scan:
    """Validate ownership/connection, create queued scan + assessment executions."""
    await get_owned_project(session, project_id=project_id, owner=owner)
    connection = await get_owned_connection(
        session,
        project_id=project_id,
        connection_id=payload.connection_id,
        owner=owner,
    )
    catalog = await _get_dummy_catalog(session)

    scan = Scan(
        project_id=project_id,
        connection_id=connection.id,
        initiated_by_id=owner.id,
        status=ScanStatus.QUEUED,
        profile=payload.profile.strip() or "standard",
        progress_percent=0.0,
        completed_assessments=0,
        failed_assessments=0,
        cancel_requested=False,
    )
    session.add(scan)
    await session.flush()

    assessment = Assessment(
        scan_id=scan.id,
        assessment_catalog_id=catalog.id,
        status=AssessmentStatus.PENDING,
        severity=catalog.default_severity,
        raw_result={},
        logs=[],
    )
    session.add(assessment)
    await session.flush()

    ip, ua = client_meta(request)
    await write_audit_log(
        session,
        action=AuditAction.SCAN_STARTED,
        resource=f"scan:{scan.id}",
        description="Scan queued for execution",
        user_id=owner.id,
        project_id=project_id,
        scan_id=scan.id,
        metadata={
            "connection_id": str(connection.id),
            "profile": scan.profile,
            "assessment_slug": catalog.slug,
        },
        ip_address=ip,
        user_agent=ua,
    )
    await session.flush()

    # Reload with relationships for response serialization.
    return await get_owned_scan(
        session,
        project_id=project_id,
        scan_id=scan.id,
        owner=owner,
        load_details=True,
    )


async def list_scans(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    owner: User,
    params: PaginationParams,
) -> Page[Scan]:
    await get_owned_project(session, project_id=project_id, owner=owner)
    total = int(
        (
            await session.execute(
                select(func.count()).select_from(Scan).where(Scan.project_id == project_id)
            )
        ).scalar_one()
    )
    result = await session.execute(
        select(Scan)
        .where(Scan.project_id == project_id)
        .order_by(Scan.created_at.desc())
        .offset(params.offset)
        .limit(params.limit)
    )
    items = list(result.scalars().all())
    return Page.from_items(items, total=total, params=params)


async def delete_scan(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    owner: User,
    request: Any | None = None,
) -> None:
    scan = await get_owned_scan(
        session,
        project_id=project_id,
        scan_id=scan_id,
        owner=owner,
        load_details=False,
    )
    if scan.status in {ScanStatus.QUEUED, ScanStatus.RUNNING}:
        raise ConflictError(
            "Cannot delete a scan that is queued or running. Cancel it first.",
            details={"status": scan.status.value},
        )
    ip, ua = client_meta(request)
    await write_audit_log(
        session,
        action=AuditAction.SCAN_COMPLETED,
        resource=f"scan:{scan.id}",
        description="Scan deleted",
        user_id=owner.id,
        project_id=project_id,
        scan_id=scan.id,
        metadata={"deleted": True, "prior_status": scan.status.value},
        ip_address=ip,
        user_agent=ua,
    )
    await session.delete(scan)
    await session.flush()


async def cancel_scan(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    owner: User,
    request: Any | None = None,
) -> Scan:
    scan = await get_owned_scan(
        session,
        project_id=project_id,
        scan_id=scan_id,
        owner=owner,
        load_details=True,
    )
    if scan.status in {
        ScanStatus.COMPLETED,
        ScanStatus.FAILED,
        ScanStatus.CANCELLED,
    }:
        raise ConflictError(
            f"Cannot cancel a scan in status {scan.status.value}",
            details={"status": scan.status.value},
        )

    scan.cancel_requested = True
    ip, ua = client_meta(request)

    if scan.status == ScanStatus.QUEUED:
        scan.status = ScanStatus.CANCELLED
        scan.completed_at = datetime.now(UTC)
        await write_audit_log(
            session,
            action=AuditAction.SCAN_CANCELLED,
            resource=f"scan:{scan.id}",
            description="Scan cancelled while queued",
            user_id=owner.id,
            project_id=project_id,
            scan_id=scan.id,
            ip_address=ip,
            user_agent=ua,
        )
    else:
        # Running: background job observes cancel_requested and finalizes.
        await write_audit_log(
            session,
            action=AuditAction.SCAN_CANCELLED,
            resource=f"scan:{scan.id}",
            description="Scan cancellation requested",
            user_id=owner.id,
            project_id=project_id,
            scan_id=scan.id,
            metadata={"status": scan.status.value},
            ip_address=ip,
            user_agent=ua,
        )

    await session.flush()
    await session.refresh(scan)
    return await get_owned_scan(
        session,
        project_id=project_id,
        scan_id=scan.id,
        owner=owner,
        load_details=True,
    )
