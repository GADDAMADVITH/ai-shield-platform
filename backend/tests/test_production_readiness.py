"""Sprint 11 — production readiness, health/readiness, and config validation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import ConfigurationError, Settings, get_settings
from app.main import create_app


def test_health_endpoints(client: TestClient) -> None:
    for path in ("/health", "/api/v1/health"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


def test_ready_endpoint_shape(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code in {200, 503}
    payload = response.json()
    assert payload["status"] in {"ready", "not_ready"}
    assert "checks" in payload
    assert "configuration" in payload["checks"]
    assert "database" in payload["checks"]

    response_v1 = client.get("/api/v1/ready")
    assert response_v1.status_code in {200, 503}
    assert "checks" in response_v1.json()


def test_settings_reject_empty_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "   ")
    get_settings.cache_clear()
    with pytest.raises((ValidationError, ConfigurationError, ValueError)):
        Settings()
    get_settings.cache_clear()


def test_settings_production_rejects_default_jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "change-me-in-production-use-a-long-random-secret",
    )
    get_settings.cache_clear()
    with pytest.raises((ValidationError, ConfigurationError)):
        Settings()
    get_settings.cache_clear()


def test_settings_production_accepts_strong_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "strong-production-secret-value-with-enough-length",
    )
    get_settings.cache_clear()
    settings = Settings()
    settings.validate_for_runtime()
    assert settings.is_production is True
    get_settings.cache_clear()


def test_create_app_registers_ready_route() -> None:
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
        ready = client.get("/ready")
        assert ready.status_code in {200, 503}
        assert ready.json()["status"] in {"ready", "not_ready"}
        assert client.get("/api/v1/ready").status_code in {200, 503}
