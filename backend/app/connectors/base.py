"""Connector provider contracts and shared test result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from app.common.enums import ConnectionMethod


@dataclass(slots=True)
class ConnectionTestResult:
    """Outcome of a lightweight connectivity probe."""

    reachable: bool
    status_code: int | None
    response_time_ms: int
    message: str
    timestamp: datetime

    @classmethod
    def ok(
        cls,
        *,
        message: str,
        response_time_ms: int,
        status_code: int | None = None,
    ) -> ConnectionTestResult:
        return cls(
            reachable=True,
            status_code=status_code,
            response_time_ms=response_time_ms,
            message=message,
            timestamp=datetime.now(UTC),
        )

    @classmethod
    def fail(
        cls,
        *,
        message: str,
        response_time_ms: int = 0,
        status_code: int | None = None,
    ) -> ConnectionTestResult:
        return cls(
            reachable=False,
            status_code=status_code,
            response_time_ms=response_time_ms,
            message=message,
            timestamp=datetime.now(UTC),
        )


class ConnectionConfig(Protocol):
    """Minimal connection shape required by providers."""

    connection_method: ConnectionMethod
    base_url: str | None
    health_endpoint: str | None
    api_key: str | None
    headers: dict[str, Any]
    timeout_seconds: int
    verify_ssl: bool
    playwright_entry_url: str | None


class BaseConnector(ABC):
    """Provider-agnostic connector interface."""

    method: ConnectionMethod

    def __init__(self, config: ConnectionConfig) -> None:
        self.config = config

    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        """Run a lightweight connectivity / configuration validation."""

    def resolve_url(self, path_or_url: str | None = None) -> str | None:
        """Join base_url with a relative path when needed."""
        target = path_or_url or self.config.health_endpoint or self.config.base_url
        if not target:
            return None
        if target.startswith("http://") or target.startswith("https://"):
            return target
        base = (self.config.base_url or "").rstrip("/")
        if not base:
            return target
        return f"{base}/{target.lstrip('/')}"

    def request_headers(self) -> dict[str, str]:
        headers = {str(k): str(v) for k, v in (self.config.headers or {}).items()}
        if self.config.api_key and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
