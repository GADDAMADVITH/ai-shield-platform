"""Scan execution API routes (nested under projects)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.common.dependencies import get_db, get_pagination
from app.common.pagination import PaginationParams
from app.common.responses import MessageResponse
from app.core.config import get_settings
from app.schemas.scan import ScanCreate, ScanList, ScanListItem, ScanPublic
from app.services import scans as scan_service
from app.services.scan_runner import execute_scan_job

router = APIRouter(
    prefix="/projects/{project_id}/scans",
    tags=["Scans"],
)


@router.post(
    "",
    response_model=ScanPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create and queue a project scan",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project or connection not found"},
        422: {"description": "Validation error"},
    },
)
async def create_scan(
    project_id: uuid.UUID,
    payload: ScanCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ScanPublic:
    """Validate ownership and connection, create assessment executions, queue execution.

    Sprint 7.1 executes only the DummyAssessmentEngine via the orchestration framework.
    """
    scan = await scan_service.create_scan(
        session,
        project_id=project_id,
        owner=current_user,
        payload=payload,
        request=request,
    )
    # Ensure durable state before the background task opens a new session.
    await session.commit()

    if get_settings().scan_auto_execute:
        background_tasks.add_task(execute_scan_job, scan.id)

    # Reload after commit so relationships are available for the response.
    scan = await scan_service.get_owned_scan(
        session,
        project_id=project_id,
        scan_id=scan.id,
        owner=current_user,
        load_details=True,
    )
    return ScanPublic.from_model(scan)


@router.get(
    "",
    response_model=ScanList,
    summary="List project scans",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project not found"},
    },
)
async def list_scans(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[PaginationParams, Depends(get_pagination)],
) -> ScanList:
    page = await scan_service.list_scans(
        session,
        project_id=project_id,
        owner=current_user,
        params=params,
    )
    return ScanList(
        items=[ScanListItem.from_model(item) for item in page.items],
        meta=page.meta,
    )


@router.get(
    "/{scan_id}",
    response_model=ScanPublic,
    summary="Get scan details including assessments and summary",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project or scan not found"},
    },
)
async def get_scan(
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ScanPublic:
    scan = await scan_service.get_owned_scan(
        session,
        project_id=project_id,
        scan_id=scan_id,
        owner=current_user,
        load_details=True,
    )
    return ScanPublic.from_model(scan)


@router.delete(
    "/{scan_id}",
    response_model=MessageResponse,
    summary="Delete a finished scan",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project or scan not found"},
        409: {"description": "Scan is still queued or running"},
    },
)
async def delete_scan(
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    current_user: CurrentUser,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await scan_service.delete_scan(
        session,
        project_id=project_id,
        scan_id=scan_id,
        owner=current_user,
        request=request,
    )
    return MessageResponse(message="Scan deleted successfully")


@router.post(
    "/{scan_id}/cancel",
    response_model=ScanPublic,
    summary="Cancel a queued or running scan",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project or scan not found"},
        409: {"description": "Scan is already finished"},
    },
)
async def cancel_scan(
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    current_user: CurrentUser,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ScanPublic:
    scan = await scan_service.cancel_scan(
        session,
        project_id=project_id,
        scan_id=scan_id,
        owner=current_user,
        request=request,
    )
    return ScanPublic.from_model(scan)
