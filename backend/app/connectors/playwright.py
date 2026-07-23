"""Playwright connector provider — lightweight browser/entry URL validation."""

from __future__ import annotations

import time
from urllib.parse import urlparse

from app.common.enums import ConnectionMethod
from app.connectors.base import BaseConnector, ConnectionTestResult
from app.connectors.http_utils import probe_http_get


class PlaywrightConnector(BaseConnector):
    method = ConnectionMethod.PLAYWRIGHT

    async def test_connection(self) -> ConnectionTestResult:
        entry_url = self.config.playwright_entry_url or self.config.base_url
        if not entry_url:
            return ConnectionTestResult.fail(
                message="Playwright connections require playwright_entry_url or base_url",
            )
        if not (entry_url.startswith("http://") or entry_url.startswith("https://")):
            return ConnectionTestResult.fail(message="Playwright entry URL must be absolute http(s)")

        parsed = urlparse(entry_url)
        if not parsed.netloc:
            return ConnectionTestResult.fail(message="Playwright entry URL is invalid")

        # Prefer real browser validation when Playwright is installed.
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            probe = await probe_http_get(
                entry_url,
                timeout_seconds=self.config.timeout_seconds,
                verify_ssl=self.config.verify_ssl,
                headers=self.request_headers(),
                success_message="Entry URL reachable (Playwright package not installed; HTTP probe used)",
            )
            return probe

        started = time.perf_counter()
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                try:
                    page = await browser.new_page()
                    response = await page.goto(
                        entry_url,
                        timeout=self.config.timeout_seconds * 1000,
                        wait_until="domcontentloaded",
                    )
                finally:
                    await browser.close()
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            status_code = response.status if response is not None else None
            return ConnectionTestResult.ok(
                message="Playwright launched and entry URL loaded",
                response_time_ms=elapsed_ms,
                status_code=status_code,
            )
        except Exception as exc:  # noqa: BLE001 — surface provider failures as test results
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            return ConnectionTestResult.fail(
                message=f"Playwright validation failed: {exc.__class__.__name__}: {exc}",
                response_time_ms=elapsed_ms,
            )
