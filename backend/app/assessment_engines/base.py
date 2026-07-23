"""Abstract assessment engine contract.

Every future security assessment inherits from :class:`AssessmentEngine` and
receives a single :class:`~app.orchestration.context.ScanContext` — never a
long parameter list.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from app.common.enums import AssessmentStatus, ConnectionMethod, Severity

if TYPE_CHECKING:
    from app.orchestration.context import ScanContext


@dataclass(slots=True)
class EngineResult:
    """Standardized outcome produced by an assessment engine."""

    status: AssessmentStatus
    score: float | None = None
    confidence: float | None = None
    severity: Severity | None = None
    finding_summary: str | None = None
    recommendation: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in {
            AssessmentStatus.PASSED,
            AssessmentStatus.FAILED,
            AssessmentStatus.ERROR,
            AssessmentStatus.SKIPPED,
        }:
            raise ValueError(
                f"EngineResult.status must be a terminal assessment status, got {self.status!r}"
            )


class AssessmentEngine(ABC):
    """Base class for all assessment engines plugged into the orchestrator."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable engine name."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic engine version string."""

    @property
    @abstractmethod
    def assessment_key(self) -> str:
        """Stable registry / catalog key (typically the catalog slug)."""

    @abstractmethod
    def supported_connection_methods(self) -> frozenset[ConnectionMethod]:
        """Connection methods this engine can operate against."""

    async def validate(self, context: ScanContext) -> None:
        """Validate that *context* is suitable for this engine.

        Raises:
            ValueError: When the context is invalid for execution.
        """
        methods = self.supported_connection_methods()
        method = context.connection.connection_method
        if methods and method not in methods:
            raise ValueError(
                f"Engine {self.assessment_key!r} does not support connection method {method!r}"
            )

    @abstractmethod
    async def run(self, context: ScanContext) -> EngineResult:
        """Execute the assessment using the provided scan context."""

    async def cleanup(self, context: ScanContext) -> None:  # noqa: B027
        """Release any resources acquired during :meth:`run`.

        Default is a no-op; engines override when they hold temporary state.
        """
        return None
