"""
Abstract base classes for biological models in V-Blood.

All biological models must subclass BiologicalModel and implement
the required interface. This ensures that the simulation engine,
validation layer, and API can treat all models uniformly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ModelMetadata:
    """Static metadata about a biological model."""

    model_id: str
    """Unique machine-readable identifier, e.g. 'rbc-gsh-redox-v1'."""

    version: str
    """Semantic version string, e.g. '1.0.0'."""

    name: str
    """Human-readable name."""

    description: str
    """Brief description of what the model represents."""

    state_variable_names: tuple[str, ...]
    """Ordered tuple of state variable symbolic names."""

    state_variable_units: tuple[str, ...]
    """Units corresponding to each state variable."""

    compartment: str
    """Name of the primary modelled compartment."""

    assumptions_doc: str
    """Path or reference to the assumptions documentation."""

    literature_sources: tuple[str, ...]
    """Key literature sources supporting the model."""


class BiologicalModel(ABC):
    """Abstract base class for all V-Blood mechanistic biological models.

    Subclasses implement the ODE right-hand side and provide parameter
    validation, constraint checking, and metadata. The simulation engine
    calls only the interface defined here.
    """

    @property
    @abstractmethod
    def metadata(self) -> ModelMetadata:
        """Return static metadata for this model."""
        ...

    @abstractmethod
    def rhs(
        self,
        t: float,
        y: np.ndarray,
        params: dict[str, Any],
    ) -> np.ndarray:
        """Compute the ODE right-hand side dy/dt.

        Args:
            t: Current time in seconds.
            y: State vector (ordered as in metadata.state_variable_names).
            params: Dictionary of model parameters.

        Returns:
            Array of derivatives dy/dt with the same shape as y.
        """
        ...

    @abstractmethod
    def initial_state(self, initial_conditions: Any) -> np.ndarray:
        """Convert an initial-conditions schema into a numpy state vector.

        Args:
            initial_conditions: Model-specific initial conditions object.

        Returns:
            State vector y₀ compatible with ``rhs``.
        """
        ...

    @abstractmethod
    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """Validate a parameter dictionary.

        Args:
            params: Dictionary of parameter names and values.

        Returns:
            List of validation error messages. Empty list means valid.
        """
        ...

    @abstractmethod
    def check_constraints(
        self,
        t: float,
        y: np.ndarray,
        params: dict[str, Any],
    ) -> list[str]:
        """Check scientific constraints on the state vector.

        Called during and after integration. Returns a list of constraint
        violation messages. Empty list means no violations.

        Args:
            t: Current time in seconds.
            y: Current state vector.
            params: Model parameters.

        Returns:
            List of violation messages. Empty list means valid.
        """
        ...
