"""Reusable validators for assessment engines."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlparse

from app.assessment_sdk.exceptions import ConfigurationError, ValidationError

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def validate_url(
    value: str | None,
    *,
    required: bool = True,
    allow_http: bool = True,
) -> str | None:
    """Validate an absolute HTTP(S) URL."""
    if value is None or not str(value).strip():
        if required:
            raise ValidationError("URL is required")
        return None
    cleaned = str(value).strip()
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError(f"Invalid URL: {cleaned!r}", details={"url": cleaned})
    if not allow_http and parsed.scheme == "http":
        raise ValidationError("HTTPS is required", details={"url": cleaned})
    if not _URL_RE.match(cleaned):
        raise ValidationError(f"Invalid URL scheme: {cleaned!r}", details={"url": cleaned})
    return cleaned


def validate_http_status(
    status_code: int | None,
    *,
    expected: int | set[int] | None = None,
    allow_2xx: bool = True,
) -> int:
    """Validate an HTTP status code."""
    if status_code is None:
        raise ValidationError("HTTP status code is required")
    code = int(status_code)
    if code < 100 or code > 599:
        raise ValidationError(f"Invalid HTTP status code: {code}")
    if expected is not None:
        allowed = {expected} if isinstance(expected, int) else set(expected)
        if code not in allowed:
            raise ValidationError(
                f"Unexpected HTTP status {code}",
                details={"expected": sorted(allowed), "actual": code},
            )
        return code
    if allow_2xx and 200 <= code < 300:
        return code
    if not allow_2xx:
        return code
    raise ValidationError(f"HTTP status {code} is not successful")


def validate_json(value: Any, *, require_object: bool = False) -> Any:
    """Parse/validate JSON. Accepts dict/list or a JSON string."""
    if isinstance(value, (dict, list)):
        parsed = value
    elif isinstance(value, (str, bytes, bytearray)):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValidationError("Invalid JSON", details={"error": str(exc)}) from exc
    else:
        raise ValidationError("JSON value must be a string, object, or array")
    if require_object and not isinstance(parsed, dict):
        raise ValidationError("JSON object (dict) required")
    return parsed


def validate_prompt_length(
    prompt: str | None,
    *,
    min_chars: int = 1,
    max_chars: int = 100_000,
) -> str:
    """Validate prompt text length bounds."""
    if prompt is None:
        raise ValidationError("Prompt is required")
    text = str(prompt)
    length = len(text)
    if length < min_chars:
        raise ValidationError(
            f"Prompt too short ({length} < {min_chars})",
            details={"length": length, "min_chars": min_chars},
        )
    if length > max_chars:
        raise ValidationError(
            f"Prompt too long ({length} > {max_chars})",
            details={"length": length, "max_chars": max_chars},
        )
    return text


def validate_response_length(
    response: str | None,
    *,
    min_chars: int = 0,
    max_chars: int = 500_000,
) -> str:
    """Validate response text length bounds."""
    if response is None:
        raise ValidationError("Response is required")
    text = str(response)
    length = len(text)
    if length < min_chars:
        raise ValidationError(
            f"Response too short ({length} < {min_chars})",
            details={"length": length, "min_chars": min_chars},
        )
    if length > max_chars:
        raise ValidationError(
            f"Response too long ({length} > {max_chars})",
            details={"length": length, "max_chars": max_chars},
        )
    return text


def validate_configuration(
    config: Any,
    *,
    required_fields: Sequence[str] = (),
) -> dict[str, Any]:
    """Ensure configuration is a mapping and contains required fields."""
    if config is None:
        raise ConfigurationError("Configuration is required")
    if hasattr(config, "model_dump"):
        data = dict(config.model_dump())
    elif isinstance(config, dict):
        data = dict(config)
    elif hasattr(config, "__dict__"):
        data = {k: v for k, v in vars(config).items() if not k.startswith("_")}
    else:
        raise ConfigurationError("Configuration must be a mapping-like object")
    missing = [field for field in required_fields if field not in data or data[field] is None]
    if missing:
        raise ConfigurationError(
            f"Missing required configuration fields: {', '.join(missing)}",
            details={"missing": missing},
        )
    return data


def validate_authentication(
    *,
    api_key: str | None = None,
    headers: dict[str, Any] | None = None,
    require_any: bool = True,
) -> None:
    """Validate that some authentication material is present when required."""
    header_auth = False
    if headers:
        lowered = {str(k).lower() for k in headers}
        header_auth = bool(lowered & {"authorization", "x-api-key", "api-key"})
    has_auth = bool(api_key and str(api_key).strip()) or header_auth
    if require_any and not has_auth:
        raise ValidationError(
            "Authentication is required (api_key or Authorization/X-API-Key header)"
        )
