"""
Pydantic schemas for simulation inputs and outputs.

These schemas define the contract between callers and the simulation engine.
All physical quantities carry explicit units; validation rejects obviously
invalid configurations (e.g., negative concentrations, zero-length time spans).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SolverMethod(str, Enum):
    """Supported ODE solver methods from scipy.integrate.solve_ivp."""

    RK45 = "RK45"
    RK23 = "RK23"
    DOP853 = "DOP853"
    LSODA = "LSODA"
    BDF = "BDF"


class SolverConfig(BaseModel):
    """Configuration for the ODE integrator.

    All tolerances follow scipy conventions. Tighter tolerances improve
    accuracy at the cost of computation time.
    """

    model_config = ConfigDict(frozen=True)

    method: SolverMethod = Field(
        default=SolverMethod.RK45,
        description="ODE solver method.",
    )
    rtol: float = Field(
        default=1e-8,
        gt=0,
        description="Relative tolerance for the ODE solver.",
    )
    atol: float = Field(
        default=1e-10,
        gt=0,
        description="Absolute tolerance for the ODE solver.",
    )
    max_step: float = Field(
        default=1.0,
        gt=0,
        description="Maximum step size in seconds.",
    )
    dense_output: bool = Field(
        default=True,
        description="Request dense output for interpolation.",
    )


class RBCGSHInitialConditions(BaseModel):
    """Initial conditions for the RBC glutathione redox ODE model.

    All concentrations are in mM of intracellular RBC water volume.
    Physiological reference ranges are documented in docs/scientific_scope.md.

    Concentrations below 0 are physically meaningless and are rejected.
    """

    model_config = ConfigDict(frozen=True)

    gsh_0: float = Field(
        default=2.5,
        ge=0.0,
        description=(
            "Initial reduced glutathione [GSH] in mM. "
            "Normal physiological range: 1.5–3.0 mM (Sies 1999; Anderson 1998)."
        ),
    )
    gssg_0: float = Field(
        default=0.025,
        ge=0.0,
        description=(
            "Initial oxidised glutathione [GSSG] in mM. "
            "Normal physiological range: 0.010–0.040 mM (Giustarini et al. 2013)."
        ),
    )
    h2o2_0: float = Field(
        default=0.0001,
        ge=0.0,
        description=(
            "Initial hydrogen peroxide [H₂O₂] in mM. "
            "Physiological intracellular steady state: 0.00001–0.001 mM (10 nM – 1 µM). "
            "Default: 0.0001 mM = 100 nM. "
            "Source: Antunes & Cadenas (2000); Winterbourn & Metodiewa (1999)."
        ),
    )
    nadph_0: float = Field(
        default=0.030,
        ge=0.0,
        description=(
            "Initial NADPH concentration in mM. "
            "Physiological range: 0.010–0.050 mM (Gaetani et al. 1994)."
        ),
    )
    damage_0: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description=(
            "Initial cumulative oxidative damage index D, dimensionless [0, 1]. "
            "0 = undamaged; 1 = fully damaged. "
            "NOTE: D is a synthetic model proxy, not a directly measurable quantity."
        ),
    )

    @model_validator(mode="after")
    def check_gsh_gssg_ratio(self) -> "RBCGSHInitialConditions":
        """Warn if the initial GSH/GSSG ratio is outside the physiological range."""
        if self.gssg_0 > 0:
            ratio = self.gsh_0 / self.gssg_0
            if ratio < 9:
                import warnings
                warnings.warn(
                    f"Initial GSH/GSSG ratio is {ratio:.1f}, which is below the "
                    "physiological minimum of ~9. This may represent an already-stressed "
                    "cell, not a normal baseline.",
                    stacklevel=3,
                )
        return self


class RBCGSHExposure(BaseModel):
    """Description of the chemical exposure scenario.

    In Milestone 1, only H₂O₂ bolus is supported as a generic oxidant.
    Chemical-specific exposures require the ML layer (Milestone 5).
    """

    model_config = ConfigDict(frozen=True)

    h2o2_bolus_mM: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "Exogenous H₂O₂ bolus added at t=0 in mM. "
            "Use 0.0 for a baseline (no challenge) simulation. "
            "WARNING: values > 0.5 mM exceed the GPx bimolecular approximation range "
            "and will trigger a model warning."
        ),
    )
    bolus_time_s: float = Field(
        default=0.0,
        ge=0.0,
        description="Time in seconds at which the bolus is applied. Default: t=0.",
    )
    description: str = Field(
        default="",
        description="Free-text description of the exposure scenario.",
    )

    @field_validator("h2o2_bolus_mM")
    @classmethod
    def warn_high_bolus(cls, v: float) -> float:
        """Issue a warning when the bolus exceeds the GPx approximation range."""
        if v > 0.5:
            import warnings
            warnings.warn(
                f"H₂O₂ bolus of {v} mM exceeds the bimolecular GPx approximation "
                "validity range (< 0.5 mM). Results at this concentration are model "
                "extrapolations and should not be interpreted as reliable predictions.",
                stacklevel=3,
            )
        return v


class SimulationRequest(BaseModel):
    """Top-level input schema for a single simulation run.

    This is the primary entry point for callers. The simulation engine
    and API endpoint both accept this schema.
    """

    model_config = ConfigDict(frozen=True)

    model_id: str = Field(
        default="rbc-gsh-redox-v1",
        description="Identifier of the biological model to run.",
    )
    initial_conditions: RBCGSHInitialConditions = Field(
        default_factory=RBCGSHInitialConditions,
        description="Initial state of the biological system.",
    )
    exposure: RBCGSHExposure = Field(
        default_factory=RBCGSHExposure,
        description="Chemical exposure scenario.",
    )
    t_start_s: float = Field(
        default=0.0,
        ge=0.0,
        description="Simulation start time in seconds.",
    )
    t_end_s: float = Field(
        default=3600.0,
        gt=0.0,
        description="Simulation end time in seconds.",
    )
    n_eval_points: int = Field(
        default=1000,
        ge=10,
        le=100_000,
        description="Number of equally-spaced time points at which to evaluate the solution.",
    )
    solver: SolverConfig = Field(
        default_factory=SolverConfig,
        description="ODE solver configuration.",
    )
    run_label: str = Field(
        default="",
        description="Optional human-readable label for this run.",
    )

    @model_validator(mode="after")
    def check_time_span(self) -> "SimulationRequest":
        """Ensure t_end > t_start."""
        if self.t_end_s <= self.t_start_s:
            raise ValueError(
                f"t_end_s ({self.t_end_s}) must be strictly greater than "
                f"t_start_s ({self.t_start_s})."
            )
        return self


class SolverStatus(str, Enum):
    """Status of the ODE solver after a run."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SimulationWarning(BaseModel):
    """A single scientific or numerical warning emitted during simulation."""

    code: str = Field(description="Short machine-readable warning code.")
    message: str = Field(description="Human-readable description.")
    severity: str = Field(
        default="WARNING",
        description="Severity level: INFO | WARNING | ERROR",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional structured details.",
    )


class TrajectoryPoint(BaseModel):
    """A single time-stamped state vector from the simulation trajectory."""

    t_s: float = Field(description="Time in seconds.")
    gsh_mM: float = Field(description="[GSH] in mM.")
    gssg_mM: float = Field(description="[GSSG] in mM.")
    h2o2_mM: float = Field(description="[H₂O₂] in mM.")
    nadph_mM: float = Field(description="[NADPH] in mM.")
    damage: float = Field(description="Cumulative oxidative damage index D [0, 1].")
    hemolysis_pct: float = Field(
        description=(
            "Estimated haemolysis percentage [0, 100]. "
            "SYNTHETIC MODEL PROXY — not calibrated to experimental data."
        ),
    )
    gsh_gssg_ratio: float = Field(description="GSH/GSSG redox ratio.")


class SimulationResult(BaseModel):
    """Complete result of a simulation run.

    Contains solver metadata, warnings, trajectory, and derived endpoints.
    The interpretation section links each derived value to its model source.
    """

    run_id: str = Field(description="Unique identifier for this simulation run.")
    model_id: str = Field(description="Model identifier used.")
    model_version: str = Field(description="Version of the biological model.")
    request: SimulationRequest = Field(description="The input request that produced this result.")

    # Solver metadata
    solver_status: SolverStatus = Field(description="Whether the solver succeeded.")
    solver_message: str = Field(description="Solver status message.")
    n_function_evaluations: int = Field(description="Number of ODE RHS evaluations.")
    solver_time_s: float = Field(description="Wall-clock time for integration in seconds.")

    # Warnings
    warnings: list[SimulationWarning] = Field(
        default_factory=list,
        description="Scientific and numerical warnings.",
    )

    # Trajectory
    trajectory: list[TrajectoryPoint] = Field(
        description="Time-series of state variables.",
    )

    # Summary endpoints
    final_gsh_mM: float = Field(description="[GSH] at t_end in mM.")
    final_gssg_mM: float = Field(description="[GSSG] at t_end in mM.")
    min_gsh_mM: float = Field(description="Minimum [GSH] observed during the simulation in mM.")
    max_h2o2_mM: float = Field(description="Maximum [H₂O₂] observed during the simulation in mM.")
    final_damage: float = Field(description="Damage index D at t_end.")
    final_hemolysis_pct: float = Field(
        description=(
            "Estimated haemolysis percentage at t_end. "
            "SYNTHETIC MODEL PROXY — not calibrated."
        ),
    )

    # Provenance
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata for reproducibility: git hash, parameter set version, etc.",
    )

    # Interpretation contract (for future LLM assistant)
    interpretation_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Structured data prepared for the LLM reporting module. "
            "Not populated in Milestone 1."
        ),
    )
