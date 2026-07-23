"""Localhost connector provider."""

from __future__ import annotations

from urllib.parse import urlparse

from app.common.enums import ConnectionMethod
from app.connectors.base import BaseConnector, ConnectionTestResult
from app.connectors.http_utils import probe_http_get


class LocalhostConnector(BaseConnector):
    method = ConnectionMethod.LOCALHOST

    async def test_connection(self) -> ConnectionTestResult:
        url = self.resolve_url(self.config.health_endpoint) or self.resolve_url(self.config.base_url)
        if not url:
            return ConnectionTestResult.fail(
                message="Localhost connections require base_url or health_endpoint",
            )

        host = urlparse(url).hostname or ""
        if host not in {"localhost", "127.0.0.1", "::1"}:
            return ConnectionTestResult.fail(
                message="Localhost connections must target localhost or 127.0.0.1",
            )

        return await probe_http_get(
            url,
            timeout_seconds=self.config.timeout_seconds,
            verify_ssl=self.config.verify_ssl,
            headers=self.request_headers(),
            success_message="Local service responded",
        )
