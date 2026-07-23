"""Assessment ORM model — runtime result of one catalog test in a scan."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import AssessmentStatus, Severity
from app.common.types import JSONDict, str_enum_column
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.assessment_catalog import AssessmentCatalog
    from app.models.scan import Scan


class Assessment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Runtime execution of a catalog assessment within a scan."""

    __tablename__ = "assessments"
    __table_args__ = (
        UniqueConstraint(
            "scan_id",
            "assessment_catalog_id",
            name="uq_assessments_scan_id_catalog_id",
        ),
        Index("ix_assessments_scan_id_status", "scan_id", "status"),
        Index("ix_assessments_scan_id_severity", "scan_id", "severity"),
        Index("ix_assessments_catalog_id_status", "assessment_catalog_id", "status"),
    )

    scan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assessment_catalog_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("assessment_catalog.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[AssessmentStatus] = mapped_column(
        str_enum_column(AssessmentStatus, name="assessment_status"),
        nullable=False,
        server_default=AssessmentStatus.PENDING.value,
        index=True,
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[Severity] = mapped_column(
        str_enum_column(Severity, name="severity", length=32),
        nullable=False,
        index=True,
    )
    finding_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[JSONDict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[JSONDict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scan: Mapped[Scan] = relationship(back_populates="assessments", lazy="select")
    catalog_entry: Mapped[AssessmentCatalog] = relationship(
        back_populates="assessments",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Assessment id={self.id} catalog_id={self.assessment_catalog_id} "
            f"status={self.status!r}>"
        )
