"""Connection management service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AuditAction, ConnectionStatus
from app.common.exceptions import ConflictError, NotFoundError
from app.common.pagination import Page, PaginationParams
from app.connectors import test_connection as run_provider_test
from app.models.connection import Connection
from app.models.user import User
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionPublic,
    ConnectionTestResponse,
    ConnectionUpdate,
)
from app.services.audit import client_meta, write_audit_log
from app.services.projects import get_owned_project


async def _get_connection_row(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    connection_id: uuid.UUID,
) -> Connection | None:
    result = await session.execute(
        select(Connection).where(
            Connection.id == connection_id,
            Connection.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def get_owned_connection(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    connection_id: uuid.UUID,
    owner: User,
) -> Connection:
    await get_owned_project(session, project_id=project_id, owner=owner)
    connection = await _get_connection_row(
        session,
        project_id=project_id,
        connection_id=connection_id,
    )
    if connection is None:
        raise NotFoundError("Connection not found")
    return connection


async def create_connection(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    owner: User,
    payload: ConnectionCreate,
    request: Any | None = None,
) -> Connection:
    await get_owned_project(session, project_id=project_id, owner=owner)
    connection = Connection(
        project_id=project_id,
        name=payload.name,
        connection_method=payload.connection_method,
        base_url=payload.base_url,
        health_endpoint=payload.health_endpoint,
        api_key=payload.api_key,
        headers=payload.headers,
        timeout_seconds=payload.timeout_seconds,
        verify_ssl=payload.verify_ssl,
        playwright_entry_url=payload.playwright_entry_url,
        notes=payload.notes,
        status=ConnectionStatus.UNVERIFIED,
    )
    session.add(connection)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise ConflictError("A connection with this name already exists on the project") from exc

    await session.refresh(connection)
    ip_address, user_agent = client_meta(request)
    await write_audit_log(
        session,
        action=AuditAction.CONNECTION_CREATED,
        resource="connection",
        description=f"Connection '{connection.name}' created",
        user_id=owner.id,
        project_id=project_id,
        metadata={
            "connection_id": str(connection.id),
            "connection_method": connection.connection_method.value,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return connection


async def list_connections(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    owner: User,
    params: PaginationParams,
) -> Page[ConnectionPublic]:
    await get_owned_project(session, project_id=project_id, owner=owner)
    total_result = await session.execute(
        select(func.count())
        .select_from(Connection)
        .where(Connection.project_id == project_id)
    )
    total = int(total_result.scalar_one())
    result = await session.execute(
        select(Connection)
        .where(Connection.project_id == project_id)
        .order_by(Connection.created_at.desc())
        .offset(params.offset)
        .limit(params.limit)
    )
    connections = list(result.scalars().all())
    return Page.from_items(
        [ConnectionPublic.from_model(item) for item in connections],
        total=total,
        params=params,
    )


async def update_connection(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    connection_id: uuid.UUID,
    owner: User,
    payload: ConnectionUpdate,
    request: Any | None = None,
) -> Connection:
    connection = await get_owned_connection(
        session,
        project_id=project_id,
        connection_id=connection_id,
        owner=owner,
    )
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return connection

    for field, value in changes.items():
        setattr(connection, field, value)

    try:
        await session.flush()
    except IntegrityError as exc:
        raise ConflictError("A connection with this name already exists on the project") from exc

    await session.refresh(connection)
    ip_address, user_agent = client_meta(request)
    await write_audit_log(
        session,
        action=AuditAction.CONNECTION_UPDATED,
        resource="connection",
        description=f"Connection '{connection.name}' updated",
        user_id=owner.id,
        project_id=project_id,
        metadata={
            "connection_id": str(connection.id),
            "changes": {key: str(value) for key, value in changes.items() if key != "api_key"},
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return connection


async def delete_connection(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    connection_id: uuid.UUID,
    owner: User,
    request: Any | None = None,
) -> None:
    connection = await get_owned_connection(
        session,
        project_id=project_id,
        connection_id=connection_id,
        owner=owner,
    )
    name = connection.name
    ip_address, user_agent = client_meta(request)
    await write_audit_log(
        session,
        action=AuditAction.CONNECTION_DELETED,
        resource="connection",
        description=f"Connection '{name}' deleted",
        user_id=owner.id,
        project_id=project_id,
        metadata={"connection_id": str(connection.id), "name": name},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.delete(connection)
    await session.flush()


async def test_owned_connection(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    connection_id: uuid.UUID,
    owner: User,
    request: Any | None = None,
) -> ConnectionTestResponse:
    connection = await get_owned_connection(
        session,
        project_id=project_id,
        connection_id=connection_id,
        owner=owner,
    )
    result = await run_provider_test(connection)
    connection.last_verified_at = datetime.now(UTC)
    connection.status = (
        ConnectionStatus.HEALTHY if result.reachable else ConnectionStatus.UNHEALTHY
    )
    await session.flush()
    await session.refresh(connection)

    ip_address, user_agent = client_meta(request)
    await write_audit_log(
        session,
        action=AuditAction.CONNECTION_TESTED,
        resource="connection",
        description=f"Connection '{connection.name}' tested",
        user_id=owner.id,
        project_id=project_id,
        metadata={
            "connection_id": str(connection.id),
            "reachable": result.reachable,
            "status_code": result.status_code,
            "response_time_ms": result.response_time_ms,
            "message": result.message,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return ConnectionTestResponse(
        reachable=result.reachable,
        status_code=result.status_code,
        response_time_ms=result.response_time_ms,
        message=result.message,
        timestamp=result.timestamp,
        connection=ConnectionPublic.from_model(connection),
    )
