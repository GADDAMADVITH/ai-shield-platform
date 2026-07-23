"""ScanSummary ORM model — rollup produced after orchestration completes."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.scan import Scan


class ScanSummary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Aggregated outcome of a finished scan."""

    __tablename__ = "scan_summaries"
    __table_args__ = (UniqueConstraint("scan_id", name="uq_scan_summaries_scan_id"),)

    scan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    critical: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    high: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    medium: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    low: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    passed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    failed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_findings: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    execution_duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    scan: Mapped[Scan] = relationship(back_populates="summary", lazy="select")

    def __repr__(self) -> str:
        return f"<ScanSummary scan_id={self.scan_id} score={self.overall_score}>"
