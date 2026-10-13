"""
Storage interfaces and in-memory persistence for API simulations (Task 5).

Provides a clean abstract storage contract so that persistent databases
(e.g., SQLite, PostgreSQL) can be introduced later without changing route logic.

NOTE: InMemorySimulationStore is development-only. Results do NOT survive process restarts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from vblood.schemas.simulation import SimulationResult


class SimulationStore(ABC):
    """Abstract repository contract for storing simulation runs."""

    @abstractmethod
    def save(self, result: SimulationResult) -> None:
        """Persist a simulation result."""

    @abstractmethod
    def get(self, run_id: str) -> SimulationResult | None:
        """Retrieve a simulation result by run_id."""

    @abstractmethod
    def list_all(self, limit: int = 100) -> list[SimulationResult]:
        """List stored simulation runs."""


class InMemorySimulationStore(SimulationStore):
    """In-memory dictionary storage for simulation runs.

    CAUTION: Development only. In-memory data is volatile and cleared upon restart.
    """

    def __init__(self) -> None:
        self._store: dict[str, SimulationResult] = {}

    def save(self, result: SimulationResult) -> None:
        self._store[result.run_id] = result

    def get(self, run_id: str) -> SimulationResult | None:
        return self._store.get(run_id)

    def list_all(self, limit: int = 100) -> list[SimulationResult]:
        return list(self._store.values())[:limit]

    def clear(self) -> None:
        """Clear all stored runs (used in test teardown)."""
        self._store.clear()
