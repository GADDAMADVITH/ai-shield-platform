"""Connection management endpoint tests."""

from __future__ import annotations

import uuid

import anyio
import httpx
import respx
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.common.enums import AuditAction
from app.db.session import AsyncSessionLocal
from app.models.audit_log import AuditLog


def _project_payload(**overrides: object) -> dict:
    payload = {
        "name": f"proj-{uuid.uuid4().hex[:8]}",
        "environment": "development",
        "application_type": "Custom AI Application",
        "connection_method": "REST API",
    }
    payload.update(overrides)
    return payload


def _connection_payload(**overrides: object) -> dict:
    payload = {
        "name": f"conn-{uuid.uuid4().hex[:8]}",
        "connection_method": "rest_api",
        "base_url": "https://api.example.com",
        "health_endpoint": "/health",
        "api_key": "secret-key",
        "timeout_seconds": 5,
        "verify_ssl": True,
    }
    payload.update(overrides)
    return payload


def _create_project(client: TestClient, headers: dict) -> str:
    response = client.post("/api/v1/projects", headers=headers, json=_project_payload())
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _count_audit_async(action: AuditAction, user_id: str) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.action == action,
                AuditLog.user_id == uuid.UUID(user_id),
            )
        )
        return int(result.scalar_one())


def _count_audit(action: str, user_id: str) -> int:
    return anyio.run(_count_audit_async, AuditAction(action), user_id)


def test_connection_crud_and_ownership(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user_id = auth_user["user"]["id"]
    project_id = _create_project(client, headers)

    create_resp = client.post(
        f"/api/v1/projects/{project_id}/connections",
        headers=headers,
        json=_connection_payload(),
    )
    assert create_resp.status_code == 201, create_resp.text
    connection = create_resp.json()
    connection_id = connection["id"]
    assert connection["api_key_set"] is True
    assert "api_key" not in connection
    assert connection["status"] == "unverified"
    assert _count_audit("connection_created", user_id) >= 1

    list_resp = client.get(
        f"/api/v1/projects/{project_id}/connections",
        headers=headers,
    )
    assert list_resp.status_code == 200
    assert any(item["id"] == connection_id for item in list_resp.json()["items"])

    get_resp = client.get(
        f"/api/v1/projects/{project_id}/connections/{connection_id}",
        headers=headers,
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == connection["name"]

    update_resp = client.patch(
        f"/api/v1/projects/{project_id}/connections/{connection_id}",
        headers=headers,
        json={"notes": "Primary production API", "timeout_seconds": 15},
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["notes"] == "Primary production API"
    assert update_resp.json()["timeout_seconds"] == 15
    assert _count_audit("connection_updated", user_id) >= 1

    # Ownership: another user cannot manage this connection
    other = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"other-{uuid.uuid4().hex[:10]}@example.com",
            "full_name": "Other User",
            "password": "SecurePass1",
        },
    )
    assert other.status_code == 201
    other_headers = {"Authorization": f"Bearer {other.json()['tokens']['access_token']}"}
    assert (
        client.get(
            f"/api/v1/projects/{project_id}/connections/{connection_id}",
            headers=other_headers,
        ).status_code
        == 403
    )

    delete_resp = client.delete(
        f"/api/v1/projects/{project_id}/connections/{connection_id}",
        headers=headers,
    )
    assert delete_resp.status_code == 200
    assert _count_audit("connection_deleted", user_id) >= 1
    assert (
        client.get(
            f"/api/v1/projects/{project_id}/connections/{connection_id}",
            headers=headers,
        ).status_code
        == 404
    )


@respx.mock
def test_successful_connection_test(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user_id = auth_user["user"]["id"]
    project_id = _create_project(client, headers)
    create_resp = client.post(
        f"/api/v1/projects/{project_id}/connections",
        headers=headers,
        json=_connection_payload(
            base_url="https://healthy.example.com",
            health_endpoint="/health",
        ),
    )
    connection_id = create_resp.json()["id"]

    respx.get("https://healthy.example.com/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )

    test_resp = client.post(
        f"/api/v1/projects/{project_id}/connections/{connection_id}/test",
        headers=headers,
    )
    assert test_resp.status_code == 200, test_resp.text
    body = test_resp.json()
    assert body["reachable"] is True
    assert body["status_code"] == 200
    assert body["response_time_ms"] >= 0
    assert body["connection"]["status"] == "healthy"
    assert body["connection"]["last_verified_at"] is not None
    assert _count_audit("connection_tested", user_id) >= 1


@respx.mock
def test_connection_timeout(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    project_id = _create_project(client, headers)
    create_resp = client.post(
        f"/api/v1/projects/{project_id}/connections",
        headers=headers,
        json=_connection_payload(
            base_url="https://slow.example.com",
            health_endpoint="/health",
            timeout_seconds=1,
        ),
    )
    connection_id = create_resp.json()["id"]

    respx.get("https://slow.example.com/health").mock(
        side_effect=httpx.TimeoutException("timed out")
    )

    test_resp = client.post(
        f"/api/v1/projects/{project_id}/connections/{connection_id}/test",
        headers=headers,
    )
    assert test_resp.status_code == 200, test_resp.text
    body = test_resp.json()
    assert body["reachable"] is False
    assert "timed out" in body["message"].lower()
    assert body["connection"]["status"] == "unhealthy"


@respx.mock
def test_invalid_endpoint(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    project_id = _create_project(client, headers)
    create_resp = client.post(
        f"/api/v1/projects/{project_id}/connections",
        headers=headers,
        json=_connection_payload(
            base_url="https://missing.example.com",
            health_endpoint="/missing",
        ),
    )
    connection_id = create_resp.json()["id"]

    respx.get("https://missing.example.com/missing").mock(
        return_value=httpx.Response(404, text="not found")
    )

    test_resp = client.post(
        f"/api/v1/projects/{project_id}/connections/{connection_id}/test",
        headers=headers,
    )
    assert test_resp.status_code == 200
    body = test_resp.json()
    # 404 is still reachable transport-wise (<500)
    assert body["reachable"] is True
    assert body["status_code"] == 404


@respx.mock
def test_openapi_document_validation(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    project_id = _create_project(client, headers)
    create_resp = client.post(
        f"/api/v1/projects/{project_id}/connections",
        headers=headers,
        json=_connection_payload(
            name=f"openapi-{uuid.uuid4().hex[:6]}",
            connection_method="openapi",
            base_url="https://docs.example.com/openapi.json",
            health_endpoint=None,
        ),
    )
    assert create_resp.status_code == 201, create_resp.text
    connection_id = create_resp.json()["id"]

    respx.get("https://docs.example.com/openapi.json").mock(
        return_value=httpx.Response(200, json={"openapi": "3.1.0", "info": {"title": "Demo"}})
    )
    test_resp = client.post(
        f"/api/v1/projects/{project_id}/connections/{connection_id}/test",
        headers=headers,
    )
    assert test_resp.status_code == 200
    assert test_resp.json()["reachable"] is True
    assert "OpenAPI document valid" in test_resp.json()["message"]


def test_duplicate_connection_name_conflict(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    project_id = _create_project(client, headers)
    name = f"dup-{uuid.uuid4().hex[:6]}"
    first = client.post(
        f"/api/v1/projects/{project_id}/connections",
        headers=headers,
        json=_connection_payload(name=name),
    )
    assert first.status_code == 201
    second = client.post(
        f"/api/v1/projects/{project_id}/connections",
        headers=headers,
        json=_connection_payload(name=name),
    )
    assert second.status_code == 409


def test_unauthenticated_connection_requests(client: TestClient) -> None:
    project_id = uuid.uuid4()
    connection_id = uuid.uuid4()
    assert (
        client.get(f"/api/v1/projects/{project_id}/connections").status_code == 401
    )
    assert (
        client.post(
            f"/api/v1/projects/{project_id}/connections",
            json=_connection_payload(),
        ).status_code
        == 401
    )
    assert (
        client.post(
            f"/api/v1/projects/{project_id}/connections/{connection_id}/test"
        ).status_code
        == 401
    )


def test_openapi_documents_connection_routes(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/projects/{project_id}/connections" in paths
    assert "/api/v1/projects/{project_id}/connections/{connection_id}" in paths
    assert "/api/v1/projects/{project_id}/connections/{connection_id}/test" in paths
    assert "post" in paths["/api/v1/projects/{project_id}/connections/{connection_id}/test"]
