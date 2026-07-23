"""Report ORM model — aggregates assessments via its parent scan."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import ReportStatus
from app.common.types import str_enum_column
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.scan import Scan


class Report(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Generated security report artifact for a scan."""

    __tablename__ = "reports"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        str_enum_column(ReportStatus, name="report_status"),
        nullable=False,
        server_default=ReportStatus.READY.value,
        index=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(back_populates="reports", lazy="select")
    scan: Mapped[Scan] = relationship(back_populates="reports", lazy="select")

    def __repr__(self) -> str:
        return f"<Report id={self.id} title={self.title!r}>"
