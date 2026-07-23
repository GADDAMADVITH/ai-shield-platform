"""Pluggable assessment engines for the scan orchestration framework.

Sprint 7 ships only the abstract contract and a dummy engine used to validate
orchestration. Real security assessments land in Sprint 8+.
"""

from app.assessment_engines.base import AssessmentEngine, EngineResult
from app.assessment_engines.dummy import DummyAssessmentEngine

__all__ = [
    "AssessmentEngine",
    "DummyAssessmentEngine",
    "EngineResult",
]
