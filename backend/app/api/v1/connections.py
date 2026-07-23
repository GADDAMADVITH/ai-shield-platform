"""Connection management API routes (nested under projects)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.common.dependencies import get_db, get_pagination
from app.common.pagination import PaginationParams
from app.common.responses import MessageResponse
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionList,
    ConnectionPublic,
    ConnectionTestResponse,
    ConnectionUpdate,
)
from app.services import connections as connection_service

router = APIRouter(
    prefix="/projects/{project_id}/connections",
    tags=["Connections"],
)


@router.post(
    "",
    response_model=ConnectionPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project connection",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project not found"},
        409: {"description": "Connection name already exists"},
        422: {"description": "Validation error"},
    },
)
async def create_connection(
    project_id: uuid.UUID,
    payload: ConnectionCreate,
    current_user: CurrentUser,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ConnectionPublic:
    connection = await connection_service.create_connection(
        session,
        project_id=project_id,
        owner=current_user,
        payload=payload,
        request=request,
    )
    return ConnectionPublic.from_model(connection)


@router.get(
    "",
    response_model=ConnectionList,
    summary="List project connections",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project not found"},
    },
)
async def list_connections(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[PaginationParams, Depends(get_pagination)],
) -> ConnectionList:
    page = await connection_service.list_connections(
        session,
        project_id=project_id,
        owner=current_user,
        params=params,
    )
    return ConnectionList(items=page.items, meta=page.meta)


@router.get(
    "/{connection_id}",
    response_model=ConnectionPublic,
    summary="Get a project connection",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project or connection not found"},
    },
)
async def get_connection(
    project_id: uuid.UUID,
    connection_id: uuid.UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ConnectionPublic:
    connection = await connection_service.get_owned_connection(
        session,
        project_id=project_id,
        connection_id=connection_id,
        owner=current_user,
    )
    return ConnectionPublic.from_model(connection)


@router.patch(
    "/{connection_id}",
    response_model=ConnectionPublic,
    summary="Update a project connection",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project or connection not found"},
        409: {"description": "Connection name already exists"},
        422: {"description": "Validation error"},
    },
)
async def update_connection(
    project_id: uuid.UUID,
    connection_id: uuid.UUID,
    payload: ConnectionUpdate,
    current_user: CurrentUser,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ConnectionPublic:
    connection = await connection_service.update_connection(
        session,
        project_id=project_id,
        connection_id=connection_id,
        owner=current_user,
        payload=payload,
        request=request,
    )
    return ConnectionPublic.from_model(connection)


@router.delete(
    "/{connection_id}",
    response_model=MessageResponse,
    summary="Delete a project connection",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project or connection not found"},
    },
)
async def delete_connection(
    project_id: uuid.UUID,
    connection_id: uuid.UUID,
    current_user: CurrentUser,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await connection_service.delete_connection(
        session,
        project_id=project_id,
        connection_id=connection_id,
        owner=current_user,
        request=request,
    )
    return MessageResponse(message="Connection deleted successfully")


@router.post(
    "/{connection_id}/test",
    response_model=ConnectionTestResponse,
    summary="Test a project connection",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project or connection not found"},
    },
)
async def test_connection(
    project_id: uuid.UUID,
    connection_id: uuid.UUID,
    current_user: CurrentUser,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ConnectionTestResponse:
    """Run a lightweight provider connectivity check (does not execute assessments)."""
    return await connection_service.test_owned_connection(
        session,
        project_id=project_id,
        connection_id=connection_id,
        owner=current_user,
        request=request,
    )
