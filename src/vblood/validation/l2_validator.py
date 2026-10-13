"""
L2 Steady-State Validation Engine for Human RBC Mechanistic Models.

Evaluates simulated steady states or baseline equilibrium values against
curated, literature-derived reference ranges (docs/validation_plan.md).

Failure Criteria (from docs/validation_plan.md §Validation failure criteria):
- Predicted SS [GSH] is outside [0.5, 5.0] mM.
- Predicted GSH/GSSG ratio is < 5.
- Predicted [H2O2] is outside [1e-5, 0.01] mM.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from vblood.schemas.simulation import SimulationResult
from vblood.simulation.steady_state import SteadyStateResult
from vblood.validation.reference_data import (
    L2_RBC_REFERENCES,
    PhysiologicalReference,
    get_l2_references,
)


class EvaluationStatus(str, Enum):
    """Evaluation status for a single physiological variable."""

    PASS_OPTIMAL = "PASS_OPTIMAL"      # Inside normal physiological reference range
    PASS_TOLERANT = "PASS_TOLERANT"    # Outside optimal, but within validation failure tolerance
    FAIL_LOW = "FAIL_LOW"              # Strictly below failure tolerance (fails L2)
    FAIL_HIGH = "FAIL_HIGH"            # Strictly above failure tolerance (fails L2)


class L2VariableEvaluation(BaseModel):
    """Detailed evaluation result for one state variable."""

    model_config = ConfigDict(frozen=True)

    variable: str
    units: str
    predicted_value: float
    reference_min: float
    reference_max: float
    tolerance_min: float
    tolerance_max: float
    status: EvaluationStatus
    is_pass: bool = Field(description="True if within tolerance (does not fail L2 criteria).")
    deviation_from_reference_pct: float = Field(
        description="Percentage deviation from the nearest reference boundary (0 if inside reference range)."
    )
    literature_source: str
    failure_message: str | None = None


class L2ValidationReport(BaseModel):
    """Complete validation report for L2 steady-state assessment."""

    model_config = ConfigDict(frozen=True)

    validation_level: str = "L2_STEADY_STATE"
    model_id: str
    model_version: str
    is_overall_pass: bool = Field(
        description="True if all variables meet L2 failure criteria (pass tolerance)."
    )
    is_optimal_pass: bool = Field(
        description="True if all variables are within strict normal reference ranges."
    )
    n_evaluated: int
    n_passed: int
    n_failed: int
    evaluations: list[L2VariableEvaluation]
    summary: str
    failure_reasons: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class L2Validator:
    """Validator for comparing simulated steady states against literature reference ranges."""

    def __init__(self, references: dict[str, PhysiologicalReference] | None = None):
        self.references = references or get_l2_references()

    def evaluate_state(
        self,
        state: dict[str, float],
        model_id: str = "rbc-gsh-redox-v1",
        model_version: str = "1.0.0",
        provenance: dict[str, Any] | None = None,
    ) -> L2ValidationReport:
        """Evaluate a state dictionary against L2 physiological reference ranges.

        Args:
            state: Mapping of state variable name to concentration in mM.
            model_id: Identifier of the biological model.
            model_version: Model version string.
            provenance: Optional metadata provenance dict.

        Returns:
            L2ValidationReport with per-variable evaluation and overall pass/fail status.
        """
        # Ensure GSH/GSSG ratio is present if GSH and GSSG are provided
        state_copy = dict(state)
        if "GSH_GSSG_RATIO" not in state_copy and "GSH" in state_copy and "GSSG" in state_copy:
            gssg_val = state_copy["GSSG"]
            if gssg_val > 0:
                state_copy["GSH_GSSG_RATIO"] = state_copy["GSH"] / gssg_val
            else:
                state_copy["GSH_GSSG_RATIO"] = 0.0

        evaluations: list[L2VariableEvaluation] = []
        failure_reasons: list[str] = []

        for var_name, ref in self.references.items():
            if var_name not in state_copy:
                continue

            val = float(state_copy[var_name])

            # Calculate deviation from reference range
            if val < ref.reference_min:
                dev_pct = ((ref.reference_min - val) / ref.reference_min) * 100.0
            elif val > ref.reference_max:
                dev_pct = ((val - ref.reference_max) / ref.reference_max) * 100.0
            else:
                dev_pct = 0.0

            # Determine pass/fail status against failure tolerance
            fail_msg = None
            if val < ref.tolerance_min:
                status = EvaluationStatus.FAIL_LOW
                fail_msg = (
                    f"{var_name} value {val:.6e} {ref.units} is below failure tolerance "
                    f"[{ref.tolerance_min}, {ref.tolerance_max}]."
                )
                failure_reasons.append(fail_msg)
            elif val > ref.tolerance_max:
                status = EvaluationStatus.FAIL_HIGH
                fail_msg = (
                    f"{var_name} value {val:.6e} {ref.units} exceeds failure tolerance "
                    f"[{ref.tolerance_min}, {ref.tolerance_max}]."
                )
                failure_reasons.append(fail_msg)
            elif ref.reference_min <= val <= ref.reference_max:
                status = EvaluationStatus.PASS_OPTIMAL
            else:
                status = EvaluationStatus.PASS_TOLERANT

            is_pass = status in (EvaluationStatus.PASS_OPTIMAL, EvaluationStatus.PASS_TOLERANT)

            evaluations.append(
                L2VariableEvaluation(
                    variable=var_name,
                    units=ref.units,
                    predicted_value=val,
                    reference_min=ref.reference_min,
                    reference_max=ref.reference_max,
                    tolerance_min=ref.tolerance_min,
                    tolerance_max=ref.tolerance_max,
                    status=status,
                    is_pass=is_pass,
                    deviation_from_reference_pct=round(dev_pct, 2),
                    literature_source=ref.literature_source,
                    failure_message=fail_msg,
                )
            )

        n_evaluated = len(evaluations)
        n_passed = sum(1 for e in evaluations if e.is_pass)
        n_failed = n_evaluated - n_passed
        is_overall_pass = bool(n_failed == 0)
        is_optimal_pass = all(e.status == EvaluationStatus.PASS_OPTIMAL for e in evaluations)

        if is_overall_pass and is_optimal_pass:
            summary = "L2 VALIDATION PASSED (OPTIMAL): All steady-state variables within normal human RBC reference ranges."
        elif is_overall_pass:
            summary = "L2 VALIDATION PASSED (TOLERANT): All steady-state variables within acceptable model tolerance limits."
        else:
            summary = (
                f"L2 VALIDATION FAILED: {n_failed} of {n_evaluated} variables violated failure criteria: "
                + "; ".join(failure_reasons)
            )

        return L2ValidationReport(
            model_id=model_id,
            model_version=model_version,
            is_overall_pass=is_overall_pass,
            is_optimal_pass=is_optimal_pass,
            n_evaluated=n_evaluated,
            n_passed=n_passed,
            n_failed=n_failed,
            evaluations=evaluations,
            summary=summary,
            failure_reasons=failure_reasons,
            provenance=provenance or {},
        )

    def evaluate_steady_state(self, ss_result: SteadyStateResult) -> L2ValidationReport:
        """Evaluate a SteadyStateResult object against L2 reference data."""
        prov = {
            "parameter_hash": ss_result.parameter_hash,
            "residual_norm": ss_result.residual_norm,
            "method": ss_result.method,
        }
        return self.evaluate_state(
            ss_result.state,
            model_id=ss_result.model_id,
            model_version=ss_result.model_version,
            provenance=prov,
        )

    def evaluate_simulation_endpoint(self, sim_result: SimulationResult) -> L2ValidationReport:
        """Evaluate the final state of a baseline simulation against L2 reference data."""
        last_pt = sim_result.trajectory[-1]
        state = {
            "GSH": last_pt.gsh_mM,
            "GSSG": last_pt.gssg_mM,
            "H2O2": last_pt.h2o2_mM,
            "NADPH": last_pt.nadph_mM,
            "GSH_GSSG_RATIO": last_pt.gsh_gssg_ratio,
        }
        prov = {
            "run_id": sim_result.run_id,
            "t_end_s": sim_result.request.t_end_s,
            "solver_status": sim_result.solver_status.value,
        }
        return self.evaluate_state(
            state,
            model_id=sim_result.model_id,
            model_version=sim_result.model_version,
            provenance=prov,
        )


def validate_l2(
    target: SteadyStateResult | SimulationResult | dict[str, float],
    model_id: str = "rbc-gsh-redox-v1",
    model_version: str = "1.0.0",
) -> L2ValidationReport:
    """Convenience function to perform L2 validation on any result or state dict."""
    validator = L2Validator()
    if isinstance(target, SteadyStateResult):
        return validator.evaluate_steady_state(target)
    if isinstance(target, SimulationResult):
        return validator.evaluate_simulation_endpoint(target)
    if isinstance(target, dict):
        return validator.evaluate_state(target, model_id=model_id, model_version=model_version)
    raise TypeError(f"Unsupported target type for L2 validation: {type(target)}")
