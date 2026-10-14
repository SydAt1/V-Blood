"""
API request and response schemas for FastAPI (Task 5).

Separates HTTP transport serialization from core scientific schemas.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from vblood.schemas.simulation import (
    RBCGSHExposure,
    RBCGSHInitialConditions,
    SimulationRequest,
    SimulationResult,
    SolverConfig,
)


class HealthResponse(BaseModel):
    """System health and operational status."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(default="ok", description="Service availability status.")
    application_version: str = Field(default="0.1.0", description="API software release version.")
    model_registry_status: str = Field(default="operational", description="Biological model registry state.")
    registered_models_count: int = Field(description="Number of available registered models.")
    scientific_validation_status: str = Field(
        default="RESEARCH_PROTOTYPE_ONLY",
        description="Scientific validation level warning: models are not clinically or regulatory validated.",
    )


class ModelDetailResponse(BaseModel):
    """Detailed metadata for a registered biological model."""

    model_config = ConfigDict(frozen=True)

    model_id: str
    name: str
    version: str
    description: str
    supported_scenarios: list[str]
    state_variables: list[str]
    state_variable_units: list[str]
    compartment: str
    parameter_count: int
    evidence_status_summary: dict[str, int]
    literature_sources: list[str]


class SimulationCreateRequest(BaseModel):
    """API payload for launching a simulation."""

    model_config = ConfigDict(frozen=True)

    model_id: str = Field(default="rbc-gsh-redox-v1", description="Registered model ID.")
    t_start_s: float = Field(default=0.0, ge=0.0, description="Start time in seconds.")
    t_end_s: float = Field(default=3600.0, gt=0.0, description="End time in seconds.")
    n_eval_points: int = Field(default=500, ge=10, le=50000, description="Number of sampling timepoints.")
    exposure: RBCGSHExposure = Field(default_factory=RBCGSHExposure, description="Exposure configuration.")
    initial_conditions: RBCGSHInitialConditions | None = Field(
        default=None,
        description="Optional explicit initial conditions. If omitted, steady-state equilibrium is used.",
    )
    use_steady_state_ic: bool | None = Field(
        default=None,
        description="Override steady state initialization flag.",
    )
    parameter_overrides: dict[str, float] | None = Field(
        default=None,
        description="Optional supported parameter overrides.",
    )
    solver: SolverConfig = Field(default_factory=SolverConfig, description="ODE solver configuration.")
    run_label: str = Field(default="", description="Optional run label.")


class SimulationDetailResponse(BaseModel):
    """Detailed response for a single simulation run."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    model_id: str
    model_version: str
    parameter_set: str
    scenario_description: str
    initial_condition_source: str
    solver_status: str
    solver_message: str
    solver_time_s: float
    n_evaluations: int
    final_gsh_mM: float
    final_gssg_mM: float
    min_gsh_mM: float
    max_h2o2_mM: float
    final_damage: float
    final_hemolysis_pct: float
    warnings_count: int
    warnings: list[dict[str, Any]]
    steady_state_initialization: bool
    provenance: dict[str, Any]
    trajectory_length: int


class CompoundResponse(BaseModel):
    """API representation of a curated chemical compound."""

    model_config = ConfigDict(frozen=True)

    compound_id: str
    name: str
    smiles: str
    inchikey: str
    mechanism_type: str
    default_parameters: dict[str, Any]
    parameter_ranges: dict[str, list[float]]
    exposure_units: str
    evidence_level: str
    is_unverified: bool
    provenance: str
    confidence_score: float


class ScenarioRunResponse(BaseModel):
    """API response for a single-cell exposure scenario."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    scenario_request: dict[str, Any]
    derived_metrics: dict[str, Any]
    has_unverified_compounds: bool
    unverified_compounds: list[str]
    compound_summaries: list[dict[str, Any]]
    interaction_assumptions: list[str]
    trajectory_length: int
    research_disclaimer: str

