"""ScanContext — single object passed into every assessment engine."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.assessment import Assessment
from app.models.assessment_catalog import AssessmentCatalog
from app.models.connection import Connection
from app.models.project import Project
from app.models.scan import Scan
from app.models.user import User


class SupportsScanIdentity(Protocol):
    """Minimal scan shape required by engines (ORM or test double)."""

    id: Any
    status: Any
    profile: str


class SupportsProjectIdentity(Protocol):
    id: Any
    name: str
    application_type: str


class SupportsConnectionIdentity(Protocol):
    id: Any
    connection_method: Any
    base_url: str | None
    timeout_seconds: int


class SupportsCatalogEntry(Protocol):
    id: Any
    slug: str
    name: str
    category: Any
    default_severity: Any
    version: str


@dataclass(slots=True)
class ScanContext:
    """Everything an assessment engine needs to execute.

    Engines receive this object alone — never a long parameter list.
    """

    scan: Scan | SupportsScanIdentity
    project: Project | SupportsProjectIdentity
    connection: Connection | SupportsConnectionIdentity
    catalog_entry: AssessmentCatalog | SupportsCatalogEntry
    http_client: httpx.AsyncClient
    logger: logging.Logger
    settings: Settings
    user: User | None = None
    session: AsyncSession | None = None
    assessment: Assessment | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_metadata(self, **extra: Any) -> ScanContext:
        """Return a shallow copy with merged metadata (does not mutate self)."""
        merged = {**self.metadata, **extra}
        return ScanContext(
            scan=self.scan,
            project=self.project,
            connection=self.connection,
            catalog_entry=self.catalog_entry,
            http_client=self.http_client,
            logger=self.logger,
            settings=self.settings,
            user=self.user,
            session=self.session,
            assessment=self.assessment,
            metadata=merged,
        )
