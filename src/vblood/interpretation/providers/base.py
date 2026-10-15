"""
Abstract Base Class for Interpretation Providers (Milestone 6).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from vblood.interpretation.schemas import (
    CohortInterpretationResponse,
    PlaygroundInterpretationResponse,
)


class InterpretationProvider(ABC):
    """Abstract interface for scientific interpretation providers."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique provider identifier (e.g. 'deterministic-v1')."""
        pass

    @abstractmethod
    async def interpret_playground(
        self,
        context: dict[str, Any],
    ) -> PlaygroundInterpretationResponse:
        """Generate a scientific interpretation memorandum for a single-cell run."""
        pass

    @abstractmethod
    async def interpret_cohort(
        self,
        context: dict[str, Any],
    ) -> CohortInterpretationResponse:
        """Generate a scientific interpretation memorandum for a cohort experiment."""
        pass
