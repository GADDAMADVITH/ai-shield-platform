"""Scan orchestration framework — schedules and executes assessment engines.

This package is intentionally assessment-logic free. Engines plug in via the
registry; the orchestrator only loads context, schedules work, executes, and
persists standardized results.
"""

from app.orchestration.context import ScanContext
from app.orchestration.events import (
    AssessmentFinished,
    AssessmentStarted,
    OrchestrationEvent,
    ScanFailed,
    ScanFinished,
    ScanStarted,
)
from app.orchestration.executor import AssessmentExecutor, ExecutionResult
from app.orchestration.orchestrator import (
    ScanOrchestrationResult,
    ScanOrchestrator,
    ScanProgress,
    WorkItem,
)
from app.orchestration.registry import (
    AssessmentRegistry,
    DuplicateEngineRegistrationError,
    EngineNotFoundError,
    create_default_registry,
)
from app.orchestration.scheduler import (
    ExecutionStrategy,
    ParallelScheduler,
    SchedulePlan,
    Scheduler,
    SequentialScheduler,
)

__all__ = [
    "AssessmentExecutor",
    "AssessmentFinished",
    "AssessmentRegistry",
    "AssessmentStarted",
    "DuplicateEngineRegistrationError",
    "EngineNotFoundError",
    "ExecutionResult",
    "ExecutionStrategy",
    "OrchestrationEvent",
    "ParallelScheduler",
    "ScanContext",
    "ScanFailed",
    "ScanFinished",
    "ScanOrchestrationResult",
    "ScanOrchestrator",
    "ScanProgress",
    "ScanStarted",
    "SchedulePlan",
    "Scheduler",
    "SequentialScheduler",
    "WorkItem",
    "create_default_registry",
]
