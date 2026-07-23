"""Connection ORM model — project-owned integration configuration."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid, text, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import ConnectionMethod, ConnectionStatus
from app.common.types import JSONDict, str_enum_column
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project


class Connection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stored connection configuration for an AI application under a project."""

    __tablename__ = "connections"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_connections_project_id_name"),
        Index("ix_connections_project_id_status", "project_id", "status"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    connection_method: Mapped[ConnectionMethod] = mapped_column(
        str_enum_column(ConnectionMethod, name="connection_method", length=64),
        nullable=False,
        index=True,
    )
    base_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    health_endpoint: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    # Placeholder plaintext storage — replace with envelope encryption before production secrets use.
    api_key: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    headers: Mapped[JSONDict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10")
    verify_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    playwright_entry_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ConnectionStatus] = mapped_column(
        str_enum_column(ConnectionStatus, name="connection_status", length=32),
        nullable=False,
        server_default=ConnectionStatus.UNVERIFIED.value,
        index=True,
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship(back_populates="connections", lazy="select")

    def __repr__(self) -> str:
        return f"<Connection id={self.id} name={self.name!r} method={self.connection_method!r}>"
