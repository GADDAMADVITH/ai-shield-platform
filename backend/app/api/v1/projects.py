"""Project management API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.common.dependencies import get_db, get_pagination
from app.common.pagination import PaginationParams
from app.common.responses import MessageResponse
from app.schemas.project import ProjectCreate, ProjectList, ProjectPublic, ProjectUpdate
from app.services import projects as project_service

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
    responses={
        401: {"description": "Not authenticated"},
        409: {"description": "Project name already exists for this user"},
        422: {"description": "Validation error"},
    },
)
async def create_project(
    payload: ProjectCreate,
    current_user: CurrentUser,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectPublic:
    """Create a new AI Shield project owned by the current user."""
    project = await project_service.create_project(
        session,
        owner=current_user,
        payload=payload,
        request=request,
    )
    return ProjectPublic.model_validate(project)


@router.get(
    "",
    response_model=ProjectList,
    summary="List projects",
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def list_projects(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[PaginationParams, Depends(get_pagination)],
) -> ProjectList:
    """List projects owned by the current user (newest first)."""
    page = await project_service.list_projects(
        session,
        owner=current_user,
        params=params,
    )
    return ProjectList(items=page.items, meta=page.meta)


@router.get(
    "/{project_id}",
    response_model=ProjectPublic,
    summary="Get a project",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project not found"},
    },
)
async def get_project(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectPublic:
    """Return a single project owned by the current user."""
    project = await project_service.get_owned_project(
        session,
        project_id=project_id,
        owner=current_user,
    )
    return ProjectPublic.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectPublic,
    summary="Update a project",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project not found"},
        409: {"description": "Project name already exists for this user"},
        422: {"description": "Validation error"},
    },
)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: CurrentUser,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectPublic:
    """Update mutable project fields. Owner cannot be changed."""
    project = await project_service.update_project(
        session,
        owner=current_user,
        project_id=project_id,
        payload=payload,
        request=request,
    )
    return ProjectPublic.model_validate(project)


@router.delete(
    "/{project_id}",
    response_model=MessageResponse,
    summary="Delete a project",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not the project owner"},
        404: {"description": "Project not found"},
    },
)
async def delete_project(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Hard-delete a project and cascade related rows."""
    await project_service.delete_project(
        session,
        owner=current_user,
        project_id=project_id,
        request=request,
    )
    return MessageResponse(message="Project deleted successfully")
