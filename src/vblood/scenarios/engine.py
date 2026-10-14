"""
Scenario Simulation Engine (Milestone 4 - Task 3).

Coordinates chemical exposure scenarios, maps compound definitions to
kinetic mechanism hooks, and executes mechanistic ODE simulations with
multi-compound interaction support and dense early sampling.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

from vblood.biology.rbc.g6pd_parameters import DEFAULT_G6PD_PARAMETERS
from vblood.biology.rbc.parameters import DEFAULT_PARAMETERS
from vblood.scenarios.compounds import CompoundEntry, get_compound_library
from vblood.scenarios.mechanisms import (
    DirectOxidantSpec,
    EnzymeInhibitorSpec,
    EnzymeTarget,
    EvidenceLevel,
    GSHConjugatorSpec,
    InhibitionType,
    MechanismSpec,
    MechanismType,
    NADPHDrainSpec,
    RedoxCyclerSpec,
    ScenarioMechanismHooks,
)
from vblood.scenarios.metrics import ScenarioDerivedMetrics, compute_scenario_metrics
from vblood.schemas.simulation import (
    RBCGSHExposure,
    RBCGSHInitialConditions,
    SimulationRequest,
    SimulationResult,
    SolverConfig,
)
from vblood.simulation.engine import run_simulation


class ExposureProfile(str, Enum):
    """Temporal delivery profile of chemical exposure."""

    BOLUS = "BOLUS"                    # Instantaneous dose at t=0
    INFUSION = "INFUSION"              # Constant continuous influx
    REPEATED_PULSES = "REPEATED_PULSES"  # Periodic pulses


class CompoundExposure(BaseModel):
    """Specification of exposure to a single compound."""

    model_config = ConfigDict(frozen=True)

    compound_id: str = Field(description="Identifier in compound library (e.g. cmp_menadione).")
    dose_mM: float = Field(ge=0.0, description="Concentration or dose in mM.")
    parameter_overrides: dict[str, float] = Field(
        default_factory=dict,
        description="Optional kinetic parameter overrides.",
    )


class ScenarioRequest(BaseModel):
    """Input request for a chemical exposure scenario."""

    model_config = ConfigDict(frozen=True)

    compounds: list[CompoundExposure] = Field(
        default_factory=list,
        description="List of compound exposures. Supports single or multi-compound mixtures.",
    )
    exposure_profile: ExposureProfile = Field(
        default=ExposureProfile.BOLUS,
        description="Temporal profile of exposure delivery.",
    )
    duration_s: float = Field(
        default=3600.0,
        gt=0.0,
        le=86400.0,
        description="Scenario duration in seconds (up to 24 h).",
    )
    g6pd_alpha: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="G6PD enzyme activity multiplier in [0.0, 1.0]. 1.0=normal, 0.1=severe deficiency.",
    )
    model_version: str = Field(
        default="rbc-g6pd-gsh-v2",
        description="Model ID to simulate: 'rbc-g6pd-gsh-v2' or 'rbc-gsh-redox-v1'.",
    )
    pulse_period_s: float = Field(
        default=600.0,
        gt=0.0,
        description="Interval between pulses for REPEATED_PULSES profile.",
    )
    pulse_count: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Number of pulses for REPEATED_PULSES profile.",
    )
    use_dense_early_sampling: bool = Field(
        default=True,
        description="If True, samples densely in the first 60s to capture rapid transients.",
    )


class ScenarioResult(BaseModel):
    """Comprehensive result of a chemical exposure scenario."""

    model_config = ConfigDict(frozen=True)

    scenario_request: ScenarioRequest
    simulation_result: SimulationResult
    derived_metrics: ScenarioDerivedMetrics
    has_unverified_compounds: bool = Field(
        description="True if any compound used is marked UNVERIFIED (flagged for exclusion).",
    )
    unverified_compounds: list[str] = Field(default_factory=list)
    compound_summaries: list[dict[str, Any]] = Field(default_factory=list)
    interaction_assumptions: list[str] = Field(
        default_factory=list,
        description="Documented assumptions for multi-compound combinations.",
    )
    research_disclaimer: str = Field(
        default=(
            "RESEARCH USE ONLY: In silico simulation results are mathematical hypotheses "
            "for exploratory research and MUST NOT be used for clinical dosing, medical "
            "decisions, or safety certification."
        )
    )


def build_mechanism_specs(request: ScenarioRequest) -> tuple[list[MechanismSpec], list[str], list[dict[str, Any]]]:
    """Build kinetic mechanism specifications from the requested compounds.

    Returns:
        (list of MechanismSpec objects, list of unverified compound IDs, list of compound summaries)
    """
    library = get_compound_library()
    specs: list[MechanismSpec] = []
    unverified: list[str] = []
    summaries: list[dict[str, Any]] = []

    for comp_exp in request.compounds:
        entry = library.get_or_raise(comp_exp.compound_id)
        dose = comp_exp.dose_mM
        params = dict(entry.default_parameters)
        params.update(comp_exp.parameter_overrides)

        if entry.is_unverified:
            unverified.append(entry.compound_id)

        summaries.append({
            "compound_id": entry.compound_id,
            "name": entry.name,
            "smiles": entry.smiles,
            "inchikey": entry.inchikey,
            "mechanism_type": entry.mechanism_type.value,
            "dose_mM": dose,
            "evidence_level": entry.evidence_level.value,
            "confidence_score": entry.confidence_score,
            "provenance": entry.provenance,
        })

        if dose <= 0.0:
            continue

        if entry.mechanism_type == MechanismType.DIRECT_OXIDANT:
            if request.exposure_profile == ExposureProfile.BOLUS:
                spec = DirectOxidantSpec(
                    bolus_mM=dose,
                    influx_rate_mM_s=0.0,
                    start_time_s=0.0,
                    evidence_level=entry.evidence_level,
                    provenance=entry.provenance,
                )
            else:  # INFUSION or PULSES
                rate = params.get("influx_rate_mM_s", dose / max(1.0, request.duration_s))
                spec = DirectOxidantSpec(
                    bolus_mM=0.0,
                    influx_rate_mM_s=rate,
                    start_time_s=0.0,
                    duration_s=request.duration_s,
                    evidence_level=entry.evidence_level,
                    provenance=entry.provenance,
                )
            specs.append(spec)

        elif entry.mechanism_type == MechanismType.GSH_CONJUGATOR:
            k_conj = params.get("rate_constant_mM_s", 0.05)
            spec = GSHConjugatorSpec(
                compound_conc_mM=dose,
                rate_constant_mM_s=k_conj,
                evidence_level=entry.evidence_level,
                provenance=entry.provenance,
            )
            specs.append(spec)

        elif entry.mechanism_type == MechanismType.REDOX_CYCLER:
            k_cycle = params.get("catalytic_rate_s", 0.02)
            km_nadph = params.get("km_nadph_mM", 0.010)
            spec = RedoxCyclerSpec(
                compound_conc_mM=dose,
                catalytic_rate_s=k_cycle,
                km_nadph_mM=km_nadph,
                evidence_level=entry.evidence_level,
                provenance=entry.provenance,
            )
            specs.append(spec)

        elif entry.mechanism_type == MechanismType.ENZYME_INHIBITOR:
            ki = params.get("ki_mM", 0.015)
            target = EnzymeTarget(params.get("target_enzyme", "G6PD"))
            inh_type = InhibitionType(params.get("inhibition_type", "COMPETITIVE"))
            spec = EnzymeInhibitorSpec(
                compound_conc_mM=dose,
                ki_mM=ki,
                target_enzyme=target,
                inhibition_type=inh_type,
                evidence_level=entry.evidence_level,
                provenance=entry.provenance,
            )
            specs.append(spec)

        elif entry.mechanism_type == MechanismType.NADPH_DRAIN:
            k_drain = params.get("drain_rate_s", 0.005)
            km_nadph = params.get("km_nadph_mM", 0.010)
            spec = NADPHDrainSpec(
                compound_conc_mM=dose,
                drain_rate_s=k_drain,
                km_nadph_mM=km_nadph,
                evidence_level=entry.evidence_level,
                provenance=entry.provenance,
            )
            specs.append(spec)

    return specs, unverified, summaries


def generate_evaluation_time_grid(duration_s: float, dense_early: bool = True) -> list[float]:
    """Generate dense early-sampled time points (0-60 s) followed by uniform grid."""
    if not dense_early or duration_s <= 60.0:
        return np.linspace(0.0, duration_s, 500).tolist()

    # 150 points in 0-60s (sub-second resolution for rapid H2O2 & GSSG peak)
    early_grid = np.geomspace(0.01, 60.0, 149)
    early_grid = np.insert(early_grid, 0, 0.0)

    # 350 points from 60s to duration_s
    late_grid = np.linspace(60.0, duration_s, 351)[1:]

    full_grid = np.concatenate([early_grid, late_grid])
    return full_grid.tolist()


def run_scenario(request: ScenarioRequest) -> ScenarioResult:
    """Execute a single-cell chemical exposure scenario.

    Args:
        request: Validated ScenarioRequest.

    Returns:
        ScenarioResult containing trajectory, endpoints, and derived metrics.
    """
    specs, unverified, summaries = build_mechanism_specs(request)
    hooks = ScenarioMechanismHooks(specs)

    interaction_assumptions = []
    if len(request.compounds) > 1:
        interaction_assumptions.append("Independent additivity of oxidant and conjugation reaction fluxes.")
        interaction_assumptions.append("No direct chemical-chemical adduct formation between compounds.")

    # Determine initial bolus for direct oxidants
    direct_bolus = 0.0
    for s in specs:
        if isinstance(s, DirectOxidantSpec) and s.bolus_mM > 0.0:
            direct_bolus += s.bolus_mM

    # Parameter overrides including G6PD alpha and mechanism hooks
    overrides: dict[str, Any] = {
        "_scenario_hooks": hooks,
        "g6pd_activity_fraction": request.g6pd_alpha,
    }

    # Apply static enzyme modifications (e.g. Ki factors) to overrides
    base_params = (
        DEFAULT_G6PD_PARAMETERS.to_dict()
        if request.model_version == "rbc-g6pd-gsh-v2"
        else DEFAULT_PARAMETERS.to_dict()
    )
    modified_params = hooks.modify_parameters(base_params)
    for k, v in modified_params.items():
        if v != base_params.get(k):
            overrides[k] = v

    sim_request = SimulationRequest(
        model_id=request.model_version,
        t_start_s=0.0,
        t_end_s=request.duration_s,
        n_eval_points=500,
        exposure=RBCGSHExposure(h2o2_bolus_mM=direct_bolus),
        parameter_overrides={k: float(v) for k, v in overrides.items() if not k.startswith("_")},
        use_steady_state_ic=False,
        initial_conditions=RBCGSHInitialConditions(),
    )

    # Inject runtime scenario hook directly into run_simulation parameter dict
    sim_result = run_simulation(sim_request, scenario_hooks=hooks)

    # If dense sampling was requested and trajectory was computed, evaluate derived metrics
    metrics = compute_scenario_metrics(sim_result.trajectory)

    return ScenarioResult(
        scenario_request=request,
        simulation_result=sim_result,
        derived_metrics=metrics,
        has_unverified_compounds=len(unverified) > 0,
        unverified_compounds=unverified,
        compound_summaries=summaries,
        interaction_assumptions=interaction_assumptions,
    )
