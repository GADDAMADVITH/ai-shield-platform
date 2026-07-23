"""Shared pytest fixtures."""

from __future__ import annotations

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
