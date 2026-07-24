"""Shared pytest fixtures."""

from __future__ import annotations

import os
import uuid

# Avoid noisy startup DB probes when Postgres is not running for unit tests.
os.environ.setdefault("STARTUP_VALIDATE_DATABASE", "false")

import pytest
from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    with TestClient(create_app()) as test_client:
        yield test_client

    # Dispose pooled async connections bound to the TestClient event loop.
    import anyio

    anyio.run(engine.dispose)


@pytest.fixture
def auth_user(client: TestClient) -> dict:
    """Register a unique user and return tokens + profile."""
    email = f"proj-user-{uuid.uuid4().hex[:12]}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Project Owner",
            "password": "SecurePass1",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    return {
        "email": email,
        "user": data["user"],
        "access_token": data["tokens"]["access_token"],
        "headers": {"Authorization": f"Bearer {data['tokens']['access_token']}"},
    }
