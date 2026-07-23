"""Webhook connector provider — validates callback URL reachability."""

from __future__ import annotations

from app.common.enums import ConnectionMethod
from app.connectors.base import BaseConnector, ConnectionTestResult
from app.connectors.http_utils import probe_http_get


class WebhookConnector(BaseConnector):
    method = ConnectionMethod.WEBHOOK

    async def test_connection(self) -> ConnectionTestResult:
        url = self.resolve_url(self.config.health_endpoint) or self.resolve_url(self.config.base_url)
        if not url:
            return ConnectionTestResult.fail(
                message="Webhook connections require base_url or health_endpoint",
            )
        return await probe_http_get(
            url,
            timeout_seconds=self.config.timeout_seconds,
            verify_ssl=self.config.verify_ssl,
            headers=self.request_headers(),
            success_message="Webhook endpoint reachable",
        )
