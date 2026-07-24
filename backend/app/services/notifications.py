"""User notification services."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import NotificationType, Severity
from app.common.exceptions import NotFoundError
from app.common.pagination import Page, PaginationParams
from app.models.notification import Notification
from app.models.user import User
from app.services.findings import FindingView, severity_counts


async def create_notification(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    title: str,
    description: str,
    category: NotificationType,
    severity: Severity,
    project_id: uuid.UUID | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        project_id=project_id,
        title=title[:255],
        description=description,
        category=category,
        severity=severity,
        is_read=False,
    )
    session.add(notification)
    await session.flush()
    return notification


async def list_notifications(
    session: AsyncSession,
    *,
    owner: User,
    params: PaginationParams,
    unread_only: bool = False,
    category: NotificationType | None = None,
) -> Page[Notification]:
    filters = [Notification.user_id == owner.id]
    if unread_only:
        filters.append(Notification.is_read.is_(False))
    if category is not None:
        filters.append(Notification.category == category)

    total = int(
        (
            await session.execute(
                select(func.count()).select_from(Notification).where(*filters)
            )
        ).scalar_one()
    )
    result = await session.execute(
        select(Notification)
        .where(*filters)
        .order_by(Notification.created_at.desc())
        .offset(params.offset)
        .limit(params.limit)
    )
    return Page.from_items(list(result.scalars().all()), total=total, params=params)


async def get_owned_notification(
    session: AsyncSession,
    *,
    notification_id: uuid.UUID,
    owner: User,
) -> Notification:
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == owner.id,
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise NotFoundError("Notification not found")
    return notification


async def mark_notification_read(
    session: AsyncSession,
    *,
    notification_id: uuid.UUID,
    owner: User,
    is_read: bool = True,
) -> Notification:
    notification = await get_owned_notification(
        session, notification_id=notification_id, owner=owner
    )
    notification.is_read = is_read
    await session.flush()
    return notification


async def mark_all_read(session: AsyncSession, *, owner: User) -> int:
    result = await session.execute(
        update(Notification)
        .where(Notification.user_id == owner.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await session.flush()
    return int(result.rowcount or 0)


async def delete_notification(
    session: AsyncSession,
    *,
    notification_id: uuid.UUID,
    owner: User,
) -> None:
    notification = await get_owned_notification(
        session, notification_id=notification_id, owner=owner
    )
    await session.delete(notification)
    await session.flush()


async def notify_scan_outcome(
    session: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    project_id: uuid.UUID,
    project_name: str,
    scan_id: uuid.UUID,
    succeeded: bool,
    findings: list[FindingView],
    overall_risk_score: float,
) -> list[Notification]:
    """Emit Sprint 10 notifications for scan completion / failure / critical risk."""
    if user_id is None:
        return []

    created: list[Notification] = []
    counts = severity_counts(findings)

    if succeeded:
        created.append(
            await create_notification(
                session,
                user_id=user_id,
                project_id=project_id,
                title="Scan completed",
                description=(
                    f"Security assessment completed for {project_name}. "
                    f"{len(findings)} finding(s) detected."
                ),
                category=NotificationType.SECURITY,
                severity=Severity.INFO if not findings else Severity.MEDIUM,
            )
        )
    else:
        created.append(
            await create_notification(
                session,
                user_id=user_id,
                project_id=project_id,
                title="Scan failed",
                description=f"Security scan failed for {project_name} (scan {scan_id}).",
                category=NotificationType.SECURITY,
                severity=Severity.HIGH,
            )
        )

    if counts.get("critical", 0) > 0:
        created.append(
            await create_notification(
                session,
                user_id=user_id,
                project_id=project_id,
                title="Critical finding detected",
                description=(
                    f"{counts['critical']} critical finding(s) in {project_name}. "
                    "Immediate review recommended."
                ),
                category=NotificationType.SECURITY,
                severity=Severity.CRITICAL,
            )
        )

    if overall_risk_score >= 75:
        created.append(
            await create_notification(
                session,
                user_id=user_id,
                project_id=project_id,
                title="High risk score",
                description=(
                    f"{project_name} scored risk {overall_risk_score:.1f}/100. "
                    "Prioritize remediation of top findings."
                ),
                category=NotificationType.SECURITY,
                severity=Severity.HIGH,
            )
        )

    return created


async def recent_notifications_payload(
    session: AsyncSession,
    *,
    owner: User,
    limit: int = 8,
) -> list[dict[str, Any]]:
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == owner.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    rows = list(result.scalars().all())
    from app.schemas.notification import NotificationPublic

    return [NotificationPublic.from_model(n).model_dump(mode="json") for n in rows]
