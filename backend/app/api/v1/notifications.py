"""Notification API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.common.dependencies import get_db, get_pagination
from app.common.enums import NotificationType
from app.common.pagination import PaginationParams
from app.common.responses import MessageResponse
from app.schemas.notification import (
    NotificationList,
    NotificationMarkRead,
    NotificationPublic,
)
from app.services import notifications as notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=NotificationList,
    summary="List notifications for the current user",
)
async def list_notifications(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[PaginationParams, Depends(get_pagination)],
    unread_only: Annotated[bool, Query()] = False,
    category: Annotated[NotificationType | None, Query()] = None,
) -> NotificationList:
    page = await notification_service.list_notifications(
        session,
        owner=current_user,
        params=params,
        unread_only=unread_only,
        category=category,
    )
    return NotificationList(
        items=[NotificationPublic.from_model(item) for item in page.items],
        meta=page.meta,
    )


@router.patch(
    "/{notification_id}",
    response_model=NotificationPublic,
    summary="Mark a notification read/unread",
)
async def update_notification(
    notification_id: uuid.UUID,
    payload: NotificationMarkRead,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationPublic:
    notification = await notification_service.mark_notification_read(
        session,
        notification_id=notification_id,
        owner=current_user,
        is_read=payload.is_read,
    )
    return NotificationPublic.from_model(notification)


@router.post(
    "/mark-all-read",
    response_model=MessageResponse,
    summary="Mark all notifications as read",
)
async def mark_all_read(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    count = await notification_service.mark_all_read(session, owner=current_user)
    return MessageResponse(message=f"Marked {count} notification(s) as read")


@router.delete(
    "/{notification_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a notification",
)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await notification_service.delete_notification(
        session, notification_id=notification_id, owner=current_user
    )
    return MessageResponse(message="Notification deleted")
