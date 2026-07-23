"""Scan ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import ScanStatus
from app.common.types import str_enum_column
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.assessment import Assessment
    from app.models.audit_log import AuditLog
    from app.models.project import Project
    from app.models.report import Report
    from app.models.user import User


class Scan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Security scan run against a project."""

    __tablename__ = "scans"
    __table_args__ = (
        Index("ix_scans_project_id_status", "project_id", "status"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    initiated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[ScanStatus] = mapped_column(
        str_enum_column(ScanStatus, name="scan_status"),
        nullable=False,
        server_default=ScanStatus.PENDING.value,
        index=True,
    )
    profile: Mapped[str] = mapped_column(String(128), nullable=False, server_default="standard")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship(back_populates="scans", lazy="select")
    initiated_by: Mapped[User | None] = relationship(
        back_populates="scans",
        foreign_keys=[initiated_by_id],
        lazy="select",
    )
    assessments: Mapped[list[Assessment]] = relationship(
        back_populates="scan",
        cascade="all, delete-orphan",
        lazy="select",
    )
    reports: Mapped[list[Report]] = relationship(
        back_populates="scan",
        cascade="all, delete-orphan",
        lazy="select",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="scan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Scan id={self.id} status={self.status!r}>"
