"""Audit log write helpers."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AuditAction
from app.common.types import JSONDict
from app.models.audit_log import AuditLog


async def write_audit_log(
    session: AsyncSession,
    *,
    action: AuditAction,
    resource: str,
    description: str,
    user_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    scan_id: uuid.UUID | None = None,
    metadata: JSONDict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Persist an append-only audit event."""
    entry = AuditLog(
        user_id=user_id,
        project_id=project_id,
        scan_id=scan_id,
        action=action,
        resource=resource,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_=metadata or {},
    )
    session.add(entry)
    await session.flush()
    return entry


def client_meta(request: Any) -> tuple[str | None, str | None]:
    """Extract client IP and user-agent from a Starlette/FastAPI request."""
    if request is None:
        return None, None
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent
