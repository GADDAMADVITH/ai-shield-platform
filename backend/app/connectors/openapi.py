"""OpenAPI connector provider."""

from __future__ import annotations

import json
import time

import httpx

from app.common.enums import ConnectionMethod
from app.connectors.base import BaseConnector, ConnectionTestResult


class OpenApiConnector(BaseConnector):
    method = ConnectionMethod.OPENAPI

    async def test_connection(self) -> ConnectionTestResult:
        url = self.resolve_url(self.config.health_endpoint) or self.resolve_url(self.config.base_url)
        if not url:
            return ConnectionTestResult.fail(
                message="OpenAPI connections require a document URL in base_url or health_endpoint",
            )

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                timeout=self.config.timeout_seconds,
                verify=self.config.verify_ssl,
                follow_redirects=True,
            ) as client:
                response = await client.get(url, headers=self.request_headers())
            elapsed_ms = int((time.perf_counter() - started) * 1000)
        except httpx.TimeoutException:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            return ConnectionTestResult.fail(
                message=f"OpenAPI document download timed out after {self.config.timeout_seconds}s",
                response_time_ms=elapsed_ms,
            )
        except httpx.HTTPError as exc:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            return ConnectionTestResult.fail(
                message=f"Failed to download OpenAPI document: {exc.__class__.__name__}",
                response_time_ms=elapsed_ms,
            )

        if response.status_code >= 400:
            return ConnectionTestResult.fail(
                message=f"OpenAPI document returned HTTP {response.status_code}",
                response_time_ms=elapsed_ms,
                status_code=response.status_code,
            )

        try:
            document = response.json()
        except json.JSONDecodeError:
            # Minimal YAML-ish acceptance: look for openapi/swagger keys in text.
            text = response.text.lower()
            if "openapi:" in text or "swagger:" in text:
                return ConnectionTestResult.ok(
                    message="OpenAPI/Swagger document retrieved (YAML)",
                    response_time_ms=elapsed_ms,
                    status_code=response.status_code,
                )
            return ConnectionTestResult.fail(
                message="Response is not a valid OpenAPI JSON/YAML document",
                response_time_ms=elapsed_ms,
                status_code=response.status_code,
            )

        if not isinstance(document, dict) or not (
            "openapi" in document or "swagger" in document
        ):
            return ConnectionTestResult.fail(
                message="JSON document missing openapi/swagger version field",
                response_time_ms=elapsed_ms,
                status_code=response.status_code,
            )

        version = document.get("openapi") or document.get("swagger")
        return ConnectionTestResult.ok(
            message=f"OpenAPI document valid (version {version})",
            response_time_ms=elapsed_ms,
            status_code=response.status_code,
        )
