"""Project ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import ProjectEnvironment, ProjectStatus
from app.common.types import str_enum_column
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.notification import Notification
    from app.models.report import Report
    from app.models.scan import Scan
    from app.models.user import User


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """AI application under assessment."""

    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_projects_owner_id_name"),
        Index("ix_projects_owner_id_status", "owner_id", "status"),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    environment: Mapped[ProjectEnvironment] = mapped_column(
        str_enum_column(ProjectEnvironment, name="project_environment"),
        nullable=False,
        index=True,
    )
    application_type: Mapped[str] = mapped_column(String(128), nullable=False)
    connection_method: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        str_enum_column(ProjectStatus, name="project_status"),
        nullable=False,
        server_default=ProjectStatus.CONNECTED.value,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped[User] = relationship(back_populates="projects", lazy="select")
    scans: Mapped[list[Scan]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )
    reports: Mapped[list[Report]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )
    notifications: Mapped[list[Notification]] = relationship(
        back_populates="project",
        lazy="select",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="project",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r}>"
