"""Project management endpoint tests."""

from __future__ import annotations

import uuid

import anyio
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.common.enums import AuditAction
from app.db.session import AsyncSessionLocal
from app.models.audit_log import AuditLog


def _project_payload(**overrides: object) -> dict:
    payload = {
        "name": f"project-{uuid.uuid4().hex[:8]}",
        "environment": "staging",
        "application_type": "RAG / Document Q&A",
        "connection_method": "REST API",
        "description": "Security assessment target",
    }
    payload.update(overrides)
    return payload


async def _count_audit_actions_async(action: AuditAction, user_id: str) -> int:
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


def _count_audit_actions(action: str, user_id: str) -> int:
    return anyio.run(_count_audit_actions_async, AuditAction(action), user_id)


def test_unauthenticated_project_requests(client: TestClient) -> None:
    assert client.get("/api/v1/projects").status_code == 401
    assert client.post("/api/v1/projects", json=_project_payload()).status_code == 401
    project_id = uuid.uuid4()
    assert client.get(f"/api/v1/projects/{project_id}").status_code == 401
    assert client.patch(f"/api/v1/projects/{project_id}", json={"name": "x"}).status_code == 401
    assert client.delete(f"/api/v1/projects/{project_id}").status_code == 401


def test_create_list_get_update_delete_project(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user_id = auth_user["user"]["id"]

    create_resp = client.post("/api/v1/projects", headers=headers, json=_project_payload())
    assert create_resp.status_code == 201, create_resp.text
    project = create_resp.json()
    project_id = project["id"]
    assert project["owner_id"] == user_id
    assert project["status"] == "connected"
    assert project["environment"] == "staging"
    assert _count_audit_actions("project_created", user_id) >= 1

    list_resp = client.get("/api/v1/projects?page=1&page_size=10", headers=headers)
    assert list_resp.status_code == 200, list_resp.text
    listing = list_resp.json()
    assert listing["meta"]["total"] >= 1
    assert any(item["id"] == project_id for item in listing["items"])
    # Newest first
    created_dates = [item["created_at"] for item in listing["items"]]
    assert created_dates == sorted(created_dates, reverse=True)

    get_resp = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == project["name"]

    update_resp = client.patch(
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={
            "name": f"updated-{uuid.uuid4().hex[:6]}",
            "description": "Updated description",
            "environment": "production",
            "status": "archived",
        },
    )
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()
    assert updated["environment"] == "production"
    assert updated["status"] == "archived"
    assert updated["description"] == "Updated description"
    assert _count_audit_actions("project_updated", user_id) >= 1

    delete_resp = client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["message"] == "Project deleted successfully"
    assert _count_audit_actions("project_deleted", user_id) >= 1

    missing = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert missing.status_code == 404


def test_list_pagination(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    for index in range(3):
        resp = client.post(
            "/api/v1/projects",
            headers=headers,
            json=_project_payload(name=f"paged-{index}-{uuid.uuid4().hex[:6]}"),
        )
        assert resp.status_code == 201, resp.text

    page1 = client.get("/api/v1/projects?page=1&page_size=2", headers=headers).json()
    assert len(page1["items"]) == 2
    assert page1["meta"]["page"] == 1
    assert page1["meta"]["page_size"] == 2
    assert page1["meta"]["total"] >= 3
    assert page1["meta"]["total_pages"] >= 2

    page2 = client.get("/api/v1/projects?page=2&page_size=2", headers=headers).json()
    assert len(page2["items"]) >= 1
    page1_ids = {item["id"] for item in page1["items"]}
    page2_ids = {item["id"] for item in page2["items"]}
    assert page1_ids.isdisjoint(page2_ids)


def test_ownership_enforcement(client: TestClient, auth_user: dict) -> None:
    owner_headers = auth_user["headers"]
    create_resp = client.post("/api/v1/projects", headers=owner_headers, json=_project_payload())
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    other_email = f"other-{uuid.uuid4().hex[:12]}@example.com"
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

    assert client.get(f"/api/v1/projects/{project_id}", headers=other_headers).status_code == 403
    assert (
        client.patch(
            f"/api/v1/projects/{project_id}",
            headers=other_headers,
            json={"description": "hijack"},
        ).status_code
        == 403
    )
    assert client.delete(f"/api/v1/projects/{project_id}", headers=other_headers).status_code == 403

    # Other user's list must not include owner's project
    listing = client.get("/api/v1/projects", headers=other_headers).json()
    assert all(item["id"] != project_id for item in listing["items"])


def test_duplicate_project_name_conflict(client: TestClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    name = f"dup-{uuid.uuid4().hex[:8]}"
    first = client.post("/api/v1/projects", headers=headers, json=_project_payload(name=name))
    assert first.status_code == 201
    second = client.post("/api/v1/projects", headers=headers, json=_project_payload(name=name))
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"


def test_get_missing_project_returns_404(client: TestClient, auth_user: dict) -> None:
    resp = client.get(f"/api/v1/projects/{uuid.uuid4()}", headers=auth_user["headers"])
    assert resp.status_code == 404


def test_openapi_documents_project_routes(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/projects" in paths
    assert "/api/v1/projects/{project_id}" in paths
    assert "post" in paths["/api/v1/projects"]
    assert "get" in paths["/api/v1/projects"]
    assert "get" in paths["/api/v1/projects/{project_id}"]
    assert "patch" in paths["/api/v1/projects/{project_id}"]
    assert "delete" in paths["/api/v1/projects/{project_id}"]
