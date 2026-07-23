"""JWT access and refresh token helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID

import jwt

from app.common.exceptions import UnauthorizedError
from app.core.config import Settings, get_settings


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def _encode(payload: dict[str, Any], settings: Settings) -> str:
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(
    subject: UUID | str,
    *,
    settings: Settings | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a short-lived access token."""
    cfg = settings or get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": TokenType.ACCESS.value,
        "iat": now,
        "exp": now + timedelta(minutes=cfg.access_token_expire_minutes),
    }
    if extra_claims:
        payload.update(extra_claims)
    return _encode(payload, cfg)


def create_refresh_token(
    subject: UUID | str,
    *,
    settings: Settings | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a longer-lived refresh token."""
    cfg = settings or get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": TokenType.REFRESH.value,
        "iat": now,
        "exp": now + timedelta(days=cfg.refresh_token_expire_days),
    }
    if extra_claims:
        payload.update(extra_claims)
    return _encode(payload, cfg)


def decode_token(
    token: str,
    *,
    expected_type: TokenType,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Decode and validate a JWT, enforcing token type."""
    cfg = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            cfg.jwt_secret_key,
            algorithms=[cfg.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid token") from exc

    token_type = payload.get("type")
    if token_type != expected_type.value:
        raise UnauthorizedError("Invalid token type")

    subject = payload.get("sub")
    if not subject:
        raise UnauthorizedError("Invalid token subject")

    return payload
