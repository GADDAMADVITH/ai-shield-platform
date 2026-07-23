"""Scan execution API tests (Sprint 7.1)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import anyio
import pytest
from fastapi.testclient import TestClient

from app.common.enums import ScanStatus
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.scan import Scan
from app.orchestration.orchestrator import ScanOrchestrationResult, ScanProgress
from app.services.scan_runner import execute_scan_job


def _project_payload(**overrides: object) -> dict:
    payload = {
        "name": f"scan-proj-{uuid.uuid4().hex[:8]}",
        "environment": "development",
        "application_type": "Custom AI Application",
        "connection_method": "REST API",
    }
    payload.update(overrides)
    return payload


def _connection_payload(**overrides: object) -> dict:
    payload = {
        "name": f"scan-conn-{uuid.uuid4().hex[:8]}",
        "connection_method": "rest_api",
        "base_url": "https://api.example.com",
        "health_endpoint": "/health",
        "timeout_seconds": 5,
        "verify_ssl": True,
    }
    payload.update(overrides)
    return payload


def _create_project_and_connection(client: TestClient, headers: dict) -> tuple[str, str]:
    project = client.post("/api/v1/projects", headers=headers, json=_project_payload())
    assert project.status_code == 201, project.text
    project_id = project.json()["id"]
    connection = client.post(
        f"/api/v1/projects/{project_id}/connections",
        headers=headers,
        json=_connection_payload(),
    )
    assert connection.status_code == 201, connection.text
    return project_id, connection.json()["id"]


@pytest.fixture
def deferred_scans(monkeypatch: pytest.MonkeyPatch):
    """Disable auto background execution so queued/cancel can be asserted."""
    get_settings.cache_clear()
    monkeypatch.setenv("SCAN_AUTO_EXECUTE", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
    monkeypatch.delenv("SCAN_AUTO_EXECUTE", raising=False)
    get_settings.cache_clear()


def test_scan_requires_authentication(client: TestClient) -> None:
    project_id = uuid.uuid4()
    response = client.post(
        f"/api/v1/projects/{project_id}/scans",
        json={"connection_id": str(uuid.uuid4())},
    )
    assert response.status_code == 401


def test_swagger_documents_scan_routes(client: TestClient) -> None:
    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    paths = openapi.json()["paths"]
    assert "/api/v1/projects/{project_id}/scans" in paths
    assert "/api/v1/projects/{project_id}/scans/{scan_id}" in paths
    assert "/api/v1/projects/{project_id}/scans/{scan_id}/cancel" in paths
    assert "post" in paths["/api/v1/projects/{project_id}/scans"]
    assert "get" in paths["/api/v1/projects/{project_id}/scans"]
    assert "delete" in paths["/api/v1/projects/{project_id}/scans/{scan_id}"]


def test_scan_creation_and_background_completion(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    project_id, connection_id = _create_project_and_connection(client, headers)

    create_resp = client.post(
        f"/api/v1/projects/{project_id}/scans",
        headers=headers,
        json={"connection_id": connection_id, "profile": "standard"},
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    scan_id = created["id"]
    assert created["connection_id"] == connection_id
    assert len(created["assessments"]) == 1
    assert created["assessments"][0]["assessment_key"] == "dummy"

    # TestClient drains BackgroundTasks before returning — scan should be complete.
    detail = client.get(
        f"/api/v1/projects/{project_id}/scans/{scan_id}",
        headers=headers,
    )
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["status"] == "completed"
    assert body["progress_percent"] == 100.0
    assert body["completed_assessments"] >= 1
    assert body["execution_time_ms"] is not None
    assert body["started_at"] is not None
    assert body["finished_at"] is not None
    assert body["last_updated"] is not None
    assert body["summary"] is not None
    assert body["summary"]["passed"] >= 1
    assert body["summary"]["execution_duration_ms"] >= 0
    assessment = body["assessments"][0]
    assert assessment["status"] == "passed"
    assert assessment["execution_time_ms"] is not None
    assert assessment["summary"]
    assert assessment["raw_result"]
    assert isinstance(assessment["logs"], list)


def test_list_scans_and_ownership(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    project_id, connection_id = _create_project_and_connection(client, headers)
    create_resp = client.post(
        f"/api/v1/projects/{project_id}/scans",
        headers=headers,
        json={"connection_id": connection_id},
    )
    assert create_resp.status_code == 201
    scan_id = create_resp.json()["id"]

    listed = client.get(f"/api/v1/projects/{project_id}/scans", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == scan_id for item in listed.json()["items"])

    other_email = f"other-{uuid.uuid4().hex[:8]}@example.com"
    other = client.post(
        "/api/v1/auth/register",
        json={
            "email": other_email,
            "full_name": "Other User",
            "password": "SecurePass1",
        },
    )
    assert other.status_code == 201
    other_headers = {
        "Authorization": f"Bearer {other.json()['tokens']['access_token']}",
    }
    forbidden = client.get(
        f"/api/v1/projects/{project_id}/scans/{scan_id}",
        headers=other_headers,
    )
    assert forbidden.status_code == 403


def test_missing_connection_returns_404(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    project_id, _ = _create_project_and_connection(client, headers)
    response = client.post(
        f"/api/v1/projects/{project_id}/scans",
        headers=headers,
        json={"connection_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404


def test_invalid_project_returns_404(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    response = client.post(
        f"/api/v1/projects/{uuid.uuid4()}/scans",
        headers=headers,
        json={"connection_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404


def test_scan_cancellation_while_queued(
    client: TestClient,
    auth_user: dict,
    deferred_scans: None,
) -> None:
    headers = auth_user["headers"]
    project_id, connection_id = _create_project_and_connection(client, headers)

    create_resp = client.post(
        f"/api/v1/projects/{project_id}/scans",
        headers=headers,
        json={"connection_id": connection_id},
    )
    assert create_resp.status_code == 201, create_resp.text
    scan = create_resp.json()
    assert scan["status"] == "queued"
    scan_id = scan["id"]

    cancel_resp = client.post(
        f"/api/v1/projects/{project_id}/scans/{scan_id}/cancel",
        headers=headers,
    )
    assert cancel_resp.status_code == 200, cancel_resp.text
    assert cancel_resp.json()["status"] == "cancelled"

    # Background job should no-op / keep cancelled.
    anyio.run(execute_scan_job, uuid.UUID(scan_id))
    detail = client.get(
        f"/api/v1/projects/{project_id}/scans/{scan_id}",
        headers=headers,
    )
    assert detail.json()["status"] == "cancelled"


def test_cancel_completed_scan_conflict(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    project_id, connection_id = _create_project_and_connection(client, headers)
    create_resp = client.post(
        f"/api/v1/projects/{project_id}/scans",
        headers=headers,
        json={"connection_id": connection_id},
    )
    assert create_resp.status_code == 201
    scan_id = create_resp.json()["id"]

    # Ensure completed
    detail = client.get(
        f"/api/v1/projects/{project_id}/scans/{scan_id}",
        headers=headers,
    )
    assert detail.json()["status"] == "completed"

    cancel_resp = client.post(
        f"/api/v1/projects/{project_id}/scans/{scan_id}/cancel",
        headers=headers,
    )
    assert cancel_resp.status_code == 409


def test_delete_finished_scan(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    project_id, connection_id = _create_project_and_connection(client, headers)
    create_resp = client.post(
        f"/api/v1/projects/{project_id}/scans",
        headers=headers,
        json={"connection_id": connection_id},
    )
    scan_id = create_resp.json()["id"]
    delete_resp = client.delete(
        f"/api/v1/projects/{project_id}/scans/{scan_id}",
        headers=headers,
    )
    assert delete_resp.status_code == 200
    missing = client.get(
        f"/api/v1/projects/{project_id}/scans/{scan_id}",
        headers=headers,
    )
    assert missing.status_code == 404


def test_failed_scan_persists_error(
    client: TestClient,
    auth_user: dict,
    deferred_scans: None,
) -> None:
    headers = auth_user["headers"]
    project_id, connection_id = _create_project_and_connection(client, headers)
    create_resp = client.post(
        f"/api/v1/projects/{project_id}/scans",
        headers=headers,
        json={"connection_id": connection_id},
    )
    assert create_resp.status_code == 201
    scan_id = uuid.UUID(create_resp.json()["id"])

    async def boom(*_args, **kwargs):  # noqa: ANN001
        scan = kwargs["scan"]
        return ScanOrchestrationResult(
            scan_id=scan.id,
            status=ScanStatus.FAILED,
            progress=ScanProgress(total=1, errored=1),
            error="orchestrator boom",
            duration_ms=12.0,
        )

    with patch(
        "app.services.scan_runner.ScanOrchestrator.run",
        new=AsyncMock(side_effect=boom),
    ):
        anyio.run(execute_scan_job, scan_id)

    detail = client.get(
        f"/api/v1/projects/{project_id}/scans/{scan_id}",
        headers=headers,
    )
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "failed"
    assert body["error_message"] == "orchestrator boom"


def test_progress_fields_updated_after_job(
    client: TestClient,
    auth_user: dict,
    deferred_scans: None,
) -> None:
    headers = auth_user["headers"]
    project_id, connection_id = _create_project_and_connection(client, headers)
    create_resp = client.post(
        f"/api/v1/projects/{project_id}/scans",
        headers=headers,
        json={"connection_id": connection_id},
    )
    scan_id = uuid.UUID(create_resp.json()["id"])
    assert create_resp.json()["progress_percent"] == 0.0

    anyio.run(execute_scan_job, scan_id)

    async def _read() -> Scan:
        async with AsyncSessionLocal() as session:
            scan = await session.get(Scan, scan_id)
            assert scan is not None
            return scan

    scan = anyio.run(_read)
    assert scan.status == ScanStatus.COMPLETED
    assert scan.progress_percent == 100.0
    assert scan.completed_assessments == 1
    assert scan.execution_time_ms is not None
