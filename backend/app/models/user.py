"""User ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import UserRole
from app.common.types import str_enum_column
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.notification import Notification
    from app.models.project import Project
    from app.models.scan import Scan


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Platform user account."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        str_enum_column(UserRole, name="user_role"),
        nullable=False,
        server_default=UserRole.MEMBER.value,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    projects: Mapped[list[Project]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select",
    )
    scans: Mapped[list[Scan]] = relationship(
        back_populates="initiated_by",
        foreign_keys="Scan.initiated_by_id",
        lazy="select",
    )
    notifications: Mapped[list[Notification]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="user",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
