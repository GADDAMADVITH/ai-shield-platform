"""Notification ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, Uuid, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import NotificationType, Severity
from app.common.types import str_enum_column
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User-facing notification."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id_is_read", "user_id", "is_read"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[NotificationType] = mapped_column(
        str_enum_column(NotificationType, name="notification_type"),
        nullable=False,
        index=True,
    )
    severity: Mapped[Severity] = mapped_column(
        str_enum_column(Severity, name="severity", length=32),
        nullable=False,
        index=True,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=false(),
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="notifications", lazy="select")
    project: Mapped[Project | None] = relationship(back_populates="notifications", lazy="select")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} title={self.title!r}>"
