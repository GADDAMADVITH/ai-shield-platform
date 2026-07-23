"""Authentication endpoint tests."""

from __future__ import annotations

import uuid

import jwt
from fastapi.testclient import TestClient

from app.auth.password import hash_password, verify_password
from app.auth.tokens import TokenType, create_access_token, decode_token
from app.core.config import get_settings


def _unique_email(prefix: str = "user") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def _register_payload(**overrides: object) -> dict:
    payload = {
        "email": _unique_email(),
        "full_name": "Ada Lovelace",
        "password": "SecurePass1",
    }
    payload.update(overrides)
    return payload


def test_password_hashing_uses_argon2() -> None:
    hashed = hash_password("SecurePass1")
    assert hashed != "SecurePass1"
    assert hashed.startswith("$argon2")
    assert verify_password("SecurePass1", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_jwt_access_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    payload = decode_token(token, expected_type=TokenType.ACCESS)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"

    settings = get_settings()
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert decoded["sub"] == str(user_id)


def test_register_login_and_me(client: TestClient) -> None:
    register_body = _register_payload()
    register_resp = client.post("/api/v1/auth/register", json=register_body)
    assert register_resp.status_code == 201, register_resp.text
    data = register_resp.json()
    assert data["user"]["email"] == register_body["email"].lower()
    assert data["user"]["full_name"] == "Ada Lovelace"
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]
    assert data["tokens"]["token_type"] == "bearer"

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": register_body["email"], "password": register_body["password"]},
    )
    assert login_resp.status_code == 200, login_resp.text
    login_data = login_resp.json()
    access_token = login_data["tokens"]["access_token"]

    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200, me_resp.text
    me = me_resp.json()
    assert me["email"] == register_body["email"].lower()
    assert me["id"] == login_data["user"]["id"]


def test_duplicate_email_returns_409(client: TestClient) -> None:
    body = _register_payload()
    first = client.post("/api/v1/auth/register", json=body)
    assert first.status_code == 201, first.text

    second = client.post("/api/v1/auth/register", json=body)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"


def test_invalid_password_returns_401(client: TestClient) -> None:
    body = _register_payload()
    assert client.post("/api/v1/auth/register", json=body).status_code == 201

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": body["email"], "password": "WrongPass1"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


def test_weak_password_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/register",
        json=_register_payload(password="short"),
    )
    assert resp.status_code == 422


def test_me_requires_valid_jwt(client: TestClient) -> None:
    missing = client.get("/api/v1/auth/me")
    assert missing.status_code == 401

    invalid = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert invalid.status_code == 401


def test_refresh_and_logout(client: TestClient) -> None:
    body = _register_payload()
    register_resp = client.post("/api/v1/auth/register", json=body)
    refresh_token = register_resp.json()["tokens"]["refresh_token"]

    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200, refresh_resp.text
    assert "access_token" in refresh_resp.json()["tokens"]

    logout_resp = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Logged out successfully"


def test_openapi_documents_auth_routes(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/refresh" in paths
    assert "/api/v1/auth/logout" in paths
    assert "/api/v1/auth/me" in paths
    assert "BearerAuth" in schema["components"]["securitySchemes"]
