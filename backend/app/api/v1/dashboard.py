"""Dashboard, analytics, findings explorer, and scan history APIs."""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.common.dependencies import get_db, get_pagination
from app.common.enums import ScanStatus
from app.common.pagination import Page, PaginationParams
from app.schemas.dashboard import (
    DashboardOverview,
    DashboardRecentResponse,
    DashboardStatistics,
    RiskAnalytics,
    ScanHistoryItem,
)
from app.schemas.report import FindingsExplorerResponse
from app.services import dashboard as dashboard_service

router = APIRouter(tags=["Dashboard"])


@router.get(
    "/dashboard/overview",
    response_model=DashboardOverview,
    summary="Dashboard overview metrics",
)
async def dashboard_overview(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardOverview:
    return await dashboard_service.build_dashboard_overview(session, owner=current_user)


@router.get(
    "/dashboard/recent",
    response_model=DashboardRecentResponse,
    summary="Recent scans and notifications",
)
async def dashboard_recent(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> DashboardRecentResponse:
    items, notifications = await dashboard_service.build_dashboard_recent(
        session, owner=current_user, limit=limit
    )
    return DashboardRecentResponse(items=items, notifications=notifications)


@router.get(
    "/dashboard/statistics",
    response_model=DashboardStatistics,
    summary="Dashboard statistics, risk analytics, and latest findings",
)
async def dashboard_statistics(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardStatistics:
    return await dashboard_service.build_dashboard_statistics(session, owner=current_user)


@router.get(
    "/dashboard/risk",
    response_model=RiskAnalytics,
    summary="Risk analytics",
)
async def dashboard_risk(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> RiskAnalytics:
    return await dashboard_service.build_risk_analytics(session, owner=current_user)


@router.get(
    "/scans/{scan_id}/summary",
    summary="Executive + risk summary for a scan",
    responses={404: {"description": "Scan not found"}},
)
async def scan_summary(
    scan_id: uuid.UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    return await dashboard_service.get_scan_summary_for_owner(
        session, scan_id=scan_id, owner=current_user
    )


@router.get(
    "/scans/history",
    response_model=Page[ScanHistoryItem],
    summary="Scan history with filtering and sorting",
)
async def scan_history(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[PaginationParams, Depends(get_pagination)],
    status: Annotated[ScanStatus | None, Query()] = None,
    project_id: Annotated[uuid.UUID | None, Query()] = None,
    sort: Annotated[
        Literal["newest", "oldest", "score_desc", "score_asc"], Query()
    ] = "newest",
) -> Page[ScanHistoryItem]:
    return await dashboard_service.list_scan_history(
        session,
        owner=current_user,
        params=params,
        status=status,
        project_id=project_id,
        sort=sort,
    )


@router.get(
    "/findings",
    response_model=FindingsExplorerResponse,
    summary="Findings explorer grouped by severity, category, and assessment",
)
async def findings_explorer(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    scan_id: Annotated[uuid.UUID | None, Query()] = None,
    project_id: Annotated[uuid.UUID | None, Query()] = None,
    severity: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    assessment_key: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
) -> dict[str, Any]:
    return await dashboard_service.explore_findings(
        session,
        owner=current_user,
        scan_id=scan_id,
        project_id=project_id,
        severity=severity,
        category=category,
        assessment_key=assessment_key,
        q=q,
    )
