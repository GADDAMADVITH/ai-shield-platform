"""Shared typing helpers for SQLAlchemy and Pydantic layers."""

from __future__ import annotations

from enum import Enum
from typing import Any, TypeVar

from sqlalchemy import Enum as SAEnum

EnumT = TypeVar("EnumT", bound=Enum)

# JSON document shapes stored in JSONB columns.
JSONDict = dict[str, Any]
JSONList = list[Any]
JSONValue = JSONDict | JSONList | str | int | float | bool | None

_ENUM_TYPES: dict[tuple[type[Enum], str, int], SAEnum] = {}


def str_enum_column(enum_cls: type[EnumT], *, name: str, length: int = 64) -> SAEnum:
    """VARCHAR-backed SQLAlchemy enum column (values stored as enum `.value`).

    Types are cached by ``(enum_cls, name, length)`` so multiple models can
    safely reuse the same logical enumeration without metadata conflicts.
    """
    key = (enum_cls, name, length)
    cached = _ENUM_TYPES.get(key)
    if cached is not None:
        return cached

    enum_type = SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda members: [item.value for item in members],
        native_enum=False,
        length=length,
        validate_strings=True,
    )
    _ENUM_TYPES[key] = enum_type
    return enum_type
