"""Reusable response parsers for assessment engines."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from app.assessment_sdk.exceptions import ValidationError

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


@dataclass(slots=True)
class ParsedResponse:
    """Normalized parse outcome."""

    kind: str
    data: Any
    raw: str


class ResponseParser:
    """Parse model/HTTP responses into structured forms."""

    @staticmethod
    def as_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, str):
            return value
        return str(value)

    @classmethod
    def parse_json(cls, value: Any, *, strict: bool = True) -> Any:
        """Parse JSON from a string/bytes/object.

        When *strict* is False, attempts to extract a fenced JSON block or the
        first ``{...}`` / ``[...]`` substring from plain text.
        """
        if isinstance(value, (dict, list)):
            return value
        text = cls.as_text(value).strip()
        if not text:
            raise ValidationError("Empty JSON payload")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if strict:
                raise ValidationError("Invalid JSON payload") from None
            return cls._extract_json(text)

    @classmethod
    def parse_plain_text(cls, value: Any) -> str:
        return cls.as_text(value).strip()

    @classmethod
    def parse_structured(cls, value: Any) -> ParsedResponse:
        """Best-effort structured parse: JSON object/array, else plain text."""
        text = cls.as_text(value)
        try:
            data = cls.parse_json(text, strict=False)
            kind = "json_object" if isinstance(data, dict) else "json_array"
            return ParsedResponse(kind=kind, data=data, raw=text)
        except ValidationError:
            return ParsedResponse(kind="text", data=cls.parse_plain_text(text), raw=text)

    @classmethod
    def _extract_json(cls, text: str) -> Any:
        fence = _JSON_FENCE_RE.search(text)
        candidates = [fence.group(1)] if fence else []
        # Heuristic: first JSON object or array in the text.
        for match in re.finditer(r"(\{[\s\S]*\}|\[[\s\S]*\])", text):
            candidates.append(match.group(1))
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        raise ValidationError("Could not extract JSON from text")
