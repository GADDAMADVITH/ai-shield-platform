"""Pluggable assessment engines for the scan orchestration framework.

Engines return :class:`~app.assessment_sdk.result.AssessmentResult`.
"""

from app.assessment_engines.base import AssessmentEngine, EngineResult, to_engine_result
from app.assessment_engines.dummy import DummyAssessmentEngine

__all__ = [
    "AssessmentEngine",
    "DummyAssessmentEngine",
    "EngineResult",
    "to_engine_result",
]
