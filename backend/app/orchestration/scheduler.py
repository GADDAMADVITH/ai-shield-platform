"""Assessment execution scheduler.

Sprint 7 ships sequential execution. The schedule plan is shaped so a future
parallel strategy can reuse the same orchestrator loop (batch → gather).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class ExecutionStrategy(StrEnum):
    """How scheduled assessments should be executed by the orchestrator."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"  # future-ready; not selected by default


@dataclass(frozen=True, slots=True)
class SchedulePlan[T]:
    """Ordered execution plan produced by a scheduler."""

    strategy: ExecutionStrategy
    items: tuple[T, ...]

    @property
    def batches(self) -> tuple[tuple[T, ...], ...]:
        """Execution batches derived from the strategy.

        - Sequential: one item per batch (order preserved).
        - Parallel: a single batch containing all items (future).
        """
        if not self.items:
            return ()
        if self.strategy == ExecutionStrategy.PARALLEL:
            return (self.items,)
        return tuple((item,) for item in self.items)


class Scheduler[T](ABC):
    """Decides execution order (and future parallelism) for assessments."""

    @property
    @abstractmethod
    def strategy(self) -> ExecutionStrategy:
        """Strategy this scheduler encodes into its plans."""

    @abstractmethod
    def schedule(self, items: Sequence[T]) -> SchedulePlan[T]:
        """Return an execution plan for *items*."""


class SequentialScheduler[T](Scheduler[T]):
    """Preserve input order and execute one assessment at a time."""

    @property
    def strategy(self) -> ExecutionStrategy:
        return ExecutionStrategy.SEQUENTIAL

    def schedule(self, items: Sequence[T]) -> SchedulePlan[T]:
        return SchedulePlan(strategy=self.strategy, items=tuple(items))


class ParallelScheduler[T](Scheduler[T]):
    """Future parallel strategy — plans a single concurrent batch.

    The orchestrator understands this plan shape; enabling production parallel
    execution is deferred until worker capacity and isolation are defined.
    """

    @property
    def strategy(self) -> ExecutionStrategy:
        return ExecutionStrategy.PARALLEL

    def schedule(self, items: Sequence[T]) -> SchedulePlan[T]:
        return SchedulePlan(strategy=self.strategy, items=tuple(items))
