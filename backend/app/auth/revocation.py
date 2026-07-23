"""Future-facing refresh-token revocation interfaces.

Logout is currently Stateless: JWTs remain valid until expiry.
Implementations of these protocols can add server-side revocation later
without changing auth endpoint contracts.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID


class RefreshTokenStore(Protocol):
    """Persistence contract for refresh-token tracking / revocation."""

    async def store(self, *, user_id: UUID, token_jti: str, expires_at: object) -> None:
        """Persist a newly issued refresh token identifier."""

    async def revoke(self, token_jti: str) -> None:
        """Mark a refresh token as revoked."""

    async def is_revoked(self, token_jti: str) -> bool:
        """Return True when the refresh token has been revoked."""


class NullRefreshTokenStore:
    """No-op store used while JWT logout remains Stateless."""

    async def store(self, *, user_id: UUID, token_jti: str, expires_at: object) -> None:
        return None

    async def revoke(self, token_jti: str) -> None:
        return None

    async def is_revoked(self, token_jti: str) -> bool:
        return False
