"""SDK connector provider — configuration validation only."""

from __future__ import annotations

from app.common.enums import ConnectionMethod
from app.connectors.base import BaseConnector, ConnectionTestResult
from app.connectors.http_utils import probe_http_get


class SdkConnector(BaseConnector):
    method = ConnectionMethod.SDK

    async def test_connection(self) -> ConnectionTestResult:
        if not self.config.base_url and not self.config.api_key:
            return ConnectionTestResult.fail(
                message="SDK connections require base_url and/or api_key",
            )

        if self.config.base_url or self.config.health_endpoint:
            url = self.resolve_url(self.config.health_endpoint) or self.resolve_url(
                self.config.base_url
            )
            assert url is not None
            return await probe_http_get(
                url,
                timeout_seconds=self.config.timeout_seconds,
                verify_ssl=self.config.verify_ssl,
                headers=self.request_headers(),
                success_message="SDK endpoint reachable",
            )

        return ConnectionTestResult.ok(
            message="SDK configuration present (api_key set; no endpoint to probe)",
            response_time_ms=0,
        )
