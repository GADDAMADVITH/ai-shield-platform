"""Report API routes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.common.dependencies import get_db, get_pagination
from app.common.pagination import PaginationParams
from app.schemas.report import (
    ReportJsonDocument,
    ReportList,
    ReportListItem,
    ReportPublic,
)
from app.services import reports as report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "",
    response_model=ReportList,
    summary="List security reports",
)
async def list_reports(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[PaginationParams, Depends(get_pagination)],
    project_id: Annotated[uuid.UUID | None, Query()] = None,
) -> ReportList:
    page = await report_service.list_reports(
        session,
        owner=current_user,
        params=params,
        project_id=project_id,
    )
    items = [
        ReportListItem.from_model(item, extras=report_service.report_extras(item))
        for item in page.items
    ]
    return ReportList(items=items, meta=page.meta)


@router.get(
    "/{report_id}",
    response_model=ReportPublic,
    summary="Get report metadata and executive summary",
    responses={404: {"description": "Report not found"}},
)
async def get_report(
    report_id: uuid.UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReportPublic:
    report = await report_service.get_owned_report(
        session, report_id=report_id, owner=current_user
    )
    extras = report_service.report_extras(report)
    base = ReportListItem.from_model(report, extras=extras)
    return ReportPublic(
        **base.model_dump(),
        executive_summary=dict(extras.get("executive_summary") or {}),
        risk_summary=dict(extras.get("risk_summary") or {}),
        findings_count=int(extras.get("total_findings") or 0),
    )


@router.get(
    "/{report_id}/json",
    response_model=ReportJsonDocument,
    summary="Download full JSON report document",
    responses={404: {"description": "Report not found"}},
)
async def get_report_json(
    report_id: uuid.UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    document = await report_service.get_report_json(
        session, report_id=report_id, owner=current_user
    )
    await session.commit()
    return document


@router.get(
    "/{scan_id}/pdf",
    summary="Download PDF security report for a scan",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF report attachment",
        },
        404: {"description": "Scan not found"},
    },
)
async def get_report_pdf(
    scan_id: uuid.UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    pdf_bytes, filename = await report_service.get_report_pdf_for_scan(
        session, scan_id=scan_id, owner=current_user
    )
    await session.commit()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "no-store",
        },
    )
