"""SDK exception hierarchy for assessment engines."""

from __future__ import annotations

from typing import Any


class AssessmentError(Exception):
    """Base error for assessment SDK and engine failures."""

    def __init__(self, message: str, *, details: Any | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ValidationError(AssessmentError):
    """Raised when input, configuration, or context validation fails."""


class ConnectionError(AssessmentError):
    """Raised when the target connection cannot be reached or authenticated."""


class ExecutionError(AssessmentError):
    """Raised when assessment execution fails unexpectedly."""


class AssessmentTimeoutError(AssessmentError):
    """Raised when an assessment exceeds its configured timeout.

    Named distinctly from the built-in ``TimeoutError`` to avoid shadowing.
    """


class ConfigurationError(AssessmentError):
    """Raised when assessment configuration is missing or invalid."""


# Alias requested by the Sprint brief (maps to AssessmentTimeoutError).
TimeoutError = AssessmentTimeoutError

__all__ = [
    "AssessmentError",
    "AssessmentTimeoutError",
    "ConfigurationError",
    "ConnectionError",
    "ExecutionError",
    "TimeoutError",
    "ValidationError",
]
