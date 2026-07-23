"""Project management service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AuditAction, ProjectStatus
from app.common.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.common.pagination import Page, PaginationParams
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectPublic, ProjectUpdate
from app.services.audit import client_meta, write_audit_log


async def _get_project_row(session: AsyncSession, project_id: uuid.UUID) -> Project | None:
    result = await session.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def get_owned_project(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    owner: User,
) -> Project:
    """Return a project owned by the user, or raise 404/403."""
    project = await _get_project_row(session, project_id)
    if project is None:
        raise NotFoundError("Project not found")
    if project.owner_id != owner.id:
        raise ForbiddenError("You do not have access to this project")
    return project


async def create_project(
    session: AsyncSession,
    *,
    owner: User,
    payload: ProjectCreate,
    request: Any | None = None,
) -> Project:
    """Create a project owned by the current user."""
    project = Project(
        owner_id=owner.id,
        name=payload.name,
        environment=payload.environment,
        application_type=payload.application_type,
        connection_method=payload.connection_method,
        description=payload.description,
        status=ProjectStatus.CONNECTED,
    )
    session.add(project)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise ConflictError("A project with this name already exists") from exc

    await session.refresh(project)
    ip_address, user_agent = client_meta(request)
    await write_audit_log(
        session,
        action=AuditAction.PROJECT_CREATED,
        resource="project",
        description=f"Project '{project.name}' created",
        user_id=owner.id,
        project_id=project.id,
        metadata={
            "name": project.name,
            "environment": project.environment.value,
            "application_type": project.application_type,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return project


async def list_projects(
    session: AsyncSession,
    *,
    owner: User,
    params: PaginationParams,
) -> Page[ProjectPublic]:
    """List projects for the current user, newest first."""
    total_result = await session.execute(
        select(func.count()).select_from(Project).where(Project.owner_id == owner.id)
    )
    total = int(total_result.scalar_one())

    result = await session.execute(
        select(Project)
        .where(Project.owner_id == owner.id)
        .order_by(Project.created_at.desc())
        .offset(params.offset)
        .limit(params.limit)
    )
    projects = list(result.scalars().all())
    return Page.from_items(
        [ProjectPublic.model_validate(project) for project in projects],
        total=total,
        params=params,
    )


async def update_project(
    session: AsyncSession,
    *,
    owner: User,
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    request: Any | None = None,
) -> Project:
    """Update mutable project fields. Owner cannot be changed."""
    project = await get_owned_project(session, project_id=project_id, owner=owner)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return project

    for field, value in changes.items():
        setattr(project, field, value)

    try:
        await session.flush()
    except IntegrityError as exc:
        raise ConflictError("A project with this name already exists") from exc

    await session.refresh(project)
    ip_address, user_agent = client_meta(request)
    await write_audit_log(
        session,
        action=AuditAction.PROJECT_UPDATED,
        resource="project",
        description=f"Project '{project.name}' updated",
        user_id=owner.id,
        project_id=project.id,
        metadata={"changes": {key: str(value) for key, value in changes.items()}},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return project


async def delete_project(
    session: AsyncSession,
    *,
    owner: User,
    project_id: uuid.UUID,
    request: Any | None = None,
) -> None:
    """Hard-delete a project (no soft-delete column; cascades apply)."""
    project = await get_owned_project(session, project_id=project_id, owner=owner)
    project_name = project.name
    owned_project_id = project.id

    ip_address, user_agent = client_meta(request)
    # Write audit before delete so project_id FK can still resolve; ON DELETE SET NULL
    # will null the FK after the project row is removed.
    await write_audit_log(
        session,
        action=AuditAction.PROJECT_DELETED,
        resource="project",
        description=f"Project '{project_name}' deleted",
        user_id=owner.id,
        project_id=owned_project_id,
        metadata={"name": project_name},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.delete(project)
    await session.flush()
