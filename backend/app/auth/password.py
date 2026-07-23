"""Argon2 password hashing via pwdlib."""

from __future__ import annotations

from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Return an Argon2 hash for the given plaintext password."""
    return _password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored Argon2 hash."""
    return _password_hash.verify(password, hashed_password)
