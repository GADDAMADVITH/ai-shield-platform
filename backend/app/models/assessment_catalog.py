"""AssessmentCatalog ORM model — source of truth for available security tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, Index, String, Text, true, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import AssessmentCategory, Severity
from app.common.types import JSONDict, str_enum_column
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.assessment import Assessment


class AssessmentCatalog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Reusable definition of a security assessment that can run in many scans."""

    __tablename__ = "assessment_catalog"
    __table_args__ = (
        Index("ix_assessment_catalog_category_enabled", "category", "enabled"),
    )

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    category: Mapped[AssessmentCategory] = mapped_column(
        str_enum_column(AssessmentCategory, name="assessment_category", length=64),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    architecture_support: Mapped[JSONDict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    default_weight: Mapped[float] = mapped_column(Float, nullable=False, server_default="1.0")
    default_severity: Mapped[Severity] = mapped_column(
        str_enum_column(Severity, name="severity", length=32),
        nullable=False,
        server_default=Severity.MEDIUM.value,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true(), index=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False, server_default="1.0.0")

    assessments: Mapped[list[Assessment]] = relationship(
        back_populates="catalog_entry",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<AssessmentCatalog id={self.id} slug={self.slug!r}>"
