"""Connector provider registry."""

from __future__ import annotations

from app.common.enums import ConnectionMethod
from app.common.exceptions import ValidationAppError
from app.connectors.base import BaseConnector, ConnectionConfig, ConnectionTestResult
from app.connectors.localhost import LocalhostConnector
from app.connectors.openapi import OpenApiConnector
from app.connectors.playwright import PlaywrightConnector
from app.connectors.rest import RestApiConnector
from app.connectors.sdk import SdkConnector
from app.connectors.webhook import WebhookConnector

_PROVIDERS: dict[ConnectionMethod, type[BaseConnector]] = {
    ConnectionMethod.REST_API: RestApiConnector,
    ConnectionMethod.OPENAPI: OpenApiConnector,
    ConnectionMethod.LOCALHOST: LocalhostConnector,
    ConnectionMethod.PLAYWRIGHT: PlaywrightConnector,
    ConnectionMethod.SDK: SdkConnector,
    ConnectionMethod.WEBHOOK: WebhookConnector,
}


def get_connector(config: ConnectionConfig) -> BaseConnector:
    """Return the provider implementation for a connection configuration."""
    provider_cls = _PROVIDERS.get(config.connection_method)
    if provider_cls is None:
        raise ValidationAppError(
            f"Unsupported connection method: {config.connection_method}",
        )
    return provider_cls(config)


async def test_connection(config: ConnectionConfig) -> ConnectionTestResult:
    """Run the provider-specific connectivity test."""
    return await get_connector(config).test_connection()


__all__ = [
    "BaseConnector",
    "ConnectionTestResult",
    "get_connector",
    "test_connection",
]
