"""
Local Sensitivity Analysis Module for Mechanistic Blood Models.

Quantifies the first-order local sensitivity of simulation endpoints
(e.g., fractional GSH depletion, minimum [GSH]) to model parameters:

    S_p = (p_0 / y_0) * (∂y / ∂p)

Requirements:
- Centered and forward finite-difference approximations.
- Respects physical non-negativity parameter bounds.
- Explicit zero/near-zero baseline handling (avoids division by zero).
- Does not modify parameter sets in-place.
- Associates results with parameter provenance and evidence status (LITERATURE vs ESTIMATED vs SYNTHETIC).
- Clearly documents that local sensitivity is valid only in the vicinity of the tested baseline.
"""

from __future__ import annotations

import copy
from enum import Enum
from typing import Any, Callable

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from vblood.biology.rbc.gsh_redox_model import RBCGSHRedoxModel
from vblood.biology.rbc.parameters import DEFAULT_PARAMETERS, RBCGSHParameters
from vblood.schemas.simulation import (
    RBCGSHExposure,
    RBCGSHInitialConditions,
    SimulationRequest,
    SimulationResult,
    SolverStatus,
)
from vblood.simulation.engine import run_simulation


class SensitivityEndpoint(str, Enum):
    """Supported simulation endpoints for sensitivity analysis."""

    MAX_FRACTIONAL_GSH_DEPLETION = "MAX_FRACTIONAL_GSH_DEPLETION"
    MIN_GSH_CONCENTRATION = "MIN_GSH_CONCENTRATION"
    FRACTIONAL_GSH_DEPLETION_AT_TIME = "FRACTIONAL_GSH_DEPLETION_AT_TIME"
    GSH_RECOVERY_TIME_50 = "GSH_RECOVERY_TIME_50"


class ParameterSensitivityResult(BaseModel):
    """Result of sensitivity calculation for a single parameter."""

    model_config = ConfigDict(frozen=True)

    parameter_name: str
    units: str
    evidence_status: str
    baseline_param_value: float
    baseline_output: float
    perturbation_pct: float
    perturbed_param_up: float
    perturbed_param_down: float | None
    perturbed_output_up: float
    perturbed_output_down: float | None
    dydp_unnormalized: float
    normalized_sensitivity_Sp: float | None
    normalization_status: str
    solver_status_up: str
    solver_status_down: str
    warnings: list[str] = Field(default_factory=list)


class SensitivityAnalysisReport(BaseModel):
    """Complete local sensitivity analysis report for a scenario and endpoint."""

    model_config = ConfigDict(frozen=True)

    model_id: str
    model_version: str
    parameter_set: str
    scenario_description: str
    endpoint: SensitivityEndpoint
    evaluation_time_s: float | None
    baseline_output_value: float
    results: list[ParameterSensitivityResult]
    ranked_parameters: list[str] = Field(
        description="Parameters ranked in descending order of absolute sensitivity magnitude."
    )
    robustness_delta_comparison: dict[str, Any] = Field(
        default_factory=dict,
        description="Comparison of sensitivities across multiple perturbation step sizes.",
    )
    limitations: list[str] = Field(
        default_factory=lambda: [
            "Local sensitivity measures response only in the infinitesimal or small-step neighborhood of the tested baseline.",
            "It does not account for parameter interactions or non-linear saturation over wide ranges.",
            "Higher sensitivity does not imply greater biological certainty; parameters marked SYNTHETIC remain unvalidated.",
            "Results depend strongly on the selected exposure profile and time horizon.",
        ]
    )


def extract_endpoint_value(
    result: SimulationResult,
    endpoint: SensitivityEndpoint,
    eval_time_s: float | None = None,
    recovery_fraction: float = 0.5,
) -> float:
    """Extract a scalar metric from a SimulationResult.

    Args:
        result: Completed SimulationResult.
        endpoint: Endpoint type to extract.
        eval_time_s: Specified time in seconds (for FRACTIONAL_GSH_DEPLETION_AT_TIME).
        recovery_fraction: Recovery threshold (e.g. 0.5 for 50% recovery).

    Returns:
        Scalar metric float.
    """
    traj = result.trajectory
    if not traj:
        raise ValueError("Simulation trajectory is empty.")

    gsh_0 = traj[0].gsh_mM
    if gsh_0 <= 0:
        raise ValueError(f"Initial GSH is non-positive ({gsh_0}), cannot compute depletion.")

    gsh_values = np.array([pt.gsh_mM for pt in traj])
    times = np.array([pt.t_s for pt in traj])

    if endpoint == SensitivityEndpoint.MIN_GSH_CONCENTRATION:
        return float(np.min(gsh_values))

    elif endpoint == SensitivityEndpoint.MAX_FRACTIONAL_GSH_DEPLETION:
        min_gsh = float(np.min(gsh_values))
        return float((gsh_0 - min_gsh) / gsh_0)

    elif endpoint == SensitivityEndpoint.FRACTIONAL_GSH_DEPLETION_AT_TIME:
        if eval_time_s is None:
            eval_time_s = times[-1]
        # Find nearest time point
        idx = int(np.argmin(np.abs(times - eval_time_s)))
        gsh_t = gsh_values[idx]
        return float((gsh_0 - gsh_t) / gsh_0)

    elif endpoint == SensitivityEndpoint.GSH_RECOVERY_TIME_50:
        min_idx = int(np.argmin(gsh_values))
        min_gsh = gsh_values[min_idx]
        target_gsh = min_gsh + recovery_fraction * (gsh_0 - min_gsh)

        post_nadir_times = times[min_idx:]
        post_nadir_gsh = gsh_values[min_idx:]

        recovered_mask = post_nadir_gsh >= target_gsh
        if np.any(recovered_mask):
            rec_idx = int(np.argmax(recovered_mask))
            return float(post_nadir_times[rec_idx])
        # If not recovered within simulation window, return end time
        return float(times[-1])

    raise ValueError(f"Unknown endpoint: {endpoint}")


class LocalSensitivityAnalyzer:
    """Performs finite-difference local sensitivity analysis on biological models."""

    def __init__(
        self,
        base_request: SimulationRequest | None = None,
        parameter_set: RBCGSHParameters | None = None,
    ):
        self.parameter_set = parameter_set or copy.deepcopy(DEFAULT_PARAMETERS)
        self.base_request = base_request or SimulationRequest(
            exposure=RBCGSHExposure(
                h2o2_bolus_mM=0.05,
                description="Moderate oxidative challenge (0.05 mM H2O2)",
            ),
            t_start_s=0.0,
            t_end_s=1800.0,
            n_eval_points=300,
        )

    def analyze(
        self,
        endpoint: SensitivityEndpoint = SensitivityEndpoint.MAX_FRACTIONAL_GSH_DEPLETION,
        delta_pct: float = 5.0,
        method: str = "centered",
        parameters_to_test: list[str] | None = None,
        eval_time_s: float | None = None,
        compare_deltas: list[float] | None = None,
    ) -> SensitivityAnalysisReport:
        """Run local sensitivity analysis across all model parameters.

        Args:
            endpoint: SensitivityEndpoint to evaluate.
            delta_pct: Relative perturbation step size percentage (e.g. 5.0 for ±5%).
            method: 'centered' or 'forward'.
            parameters_to_test: Optional list of parameter names to test. Defaults to all.
            eval_time_s: Time point for time-specific endpoints.
            compare_deltas: Optional list of delta percentages (e.g. [1.0, 5.0]) to test robustness.

        Returns:
            SensitivityAnalysisReport containing structured results and ranking.
        """
        all_param_objs = self.parameter_set.all_parameters()
        if parameters_to_test is None:
            param_names = list(all_param_objs.keys())
        else:
            param_names = parameters_to_test

        # 1. Run baseline simulation
        base_result = run_simulation(self.base_request)
        if base_result.solver_status != SolverStatus.SUCCESS:
            raise RuntimeError(f"Baseline simulation failed: {base_result.solver_message}")

        y_base = extract_endpoint_value(base_result, endpoint, eval_time_s=eval_time_s)

        results: list[ParameterSensitivityResult] = []

        for p_name in param_names:
            if p_name not in all_param_objs:
                continue

            param_obj = all_param_objs[p_name]
            p0 = param_obj.value
            units = param_obj.units
            status = param_obj.evidence_status.value

            res = self._compute_single_param_sensitivity(
                p_name=p_name,
                p0=p0,
                units=units,
                evidence_status=status,
                y_base=y_base,
                endpoint=endpoint,
                delta_pct=delta_pct,
                method=method,
                eval_time_s=eval_time_s,
            )
            results.append(res)

        # Rank parameters by descending absolute sensitivity magnitude
        def rank_key(r: ParameterSensitivityResult) -> float:
            if r.normalized_sensitivity_Sp is not None:
                return abs(r.normalized_sensitivity_Sp)
            return abs(r.dydp_unnormalized)

        results_sorted = sorted(results, key=rank_key, reverse=True)
        ranked_names = [r.parameter_name for r in results_sorted]

        # Optional robustness comparison across multiple delta sizes
        robustness: dict[str, Any] = {}
        if compare_deltas:
            for alt_delta in compare_deltas:
                alt_sens = {}
                for p_name in param_names:
                    p_obj = all_param_objs[p_name]
                    r_alt = self._compute_single_param_sensitivity(
                        p_name=p_name,
                        p0=p_obj.value,
                        units=p_obj.units,
                        evidence_status=p_obj.evidence_status.value,
                        y_base=y_base,
                        endpoint=endpoint,
                        delta_pct=alt_delta,
                        method=method,
                        eval_time_s=eval_time_s,
                    )
                    alt_sens[p_name] = r_alt.normalized_sensitivity_Sp
                robustness[f"delta_{alt_delta}_pct"] = alt_sens

        return SensitivityAnalysisReport(
            model_id=self.base_request.model_id,
            model_version="1.0.0",
            parameter_set="default_v1",
            scenario_description=self.base_request.exposure.description or "H2O2 Challenge",
            endpoint=endpoint,
            evaluation_time_s=eval_time_s,
            baseline_output_value=y_base,
            results=results_sorted,
            ranked_parameters=ranked_names,
            robustness_delta_comparison=robustness,
        )

    def _compute_single_param_sensitivity(
        self,
        p_name: str,
        p0: float,
        units: str,
        evidence_status: str,
        y_base: float,
        endpoint: SensitivityEndpoint,
        delta_pct: float,
        method: str,
        eval_time_s: float | None,
    ) -> ParameterSensitivityResult:
        """Perturb a single parameter, run simulations, and calculate derivatives."""
        warnings_list: list[str] = []
        fraction = delta_pct / 100.0

        if p0 == 0.0:
            # Use small absolute step for zero-valued parameter
            delta_abs = 1e-6
            p_up = p0 + delta_abs
            p_down = None
            use_centered = False
        else:
            delta_abs = p0 * fraction
            p_up = p0 + delta_abs
            p_down = max(1e-12, p0 - delta_abs)
            use_centered = (method == "centered" and p_down > 0)

        # Run perturbed up simulation
        req_up = copy.deepcopy(self.base_request)
        # Apply parameter override via model parameters in a clean copy
        res_up = self._run_with_parameter_override(req_up, {p_name: p_up})
        y_up = extract_endpoint_value(res_up, endpoint, eval_time_s=eval_time_s)

        if use_centered and p_down is not None:
            req_down = copy.deepcopy(self.base_request)
            res_down = self._run_with_parameter_override(req_down, {p_name: p_down})
            y_down = extract_endpoint_value(res_down, endpoint, eval_time_s=eval_time_s)
            dydp = (y_up - y_down) / (p_up - p_down)
            status_down = res_down.solver_status.value
        else:
            y_down = None
            dydp = (y_up - y_base) / delta_abs
            status_down = "NOT_APPLIED"

        status_up = res_up.solver_status.value

        # Normalized sensitivity Sp = (p0 / y0) * dydp
        if abs(y_base) > 1e-12 and p0 != 0.0:
            s_p = float((p0 / y_base) * dydp)
            norm_status = "NORMALIZED"
        else:
            s_p = None
            norm_status = "UNNORMALIZED_ZERO_BASELINE"
            warnings_list.append(
                f"Baseline output y0 ({y_base:.3e}) or parameter p0 ({p0:.3e}) is near zero; "
                "normalized sensitivity Sp is undefined. Reporting unnormalized derivative ∂y/∂p."
            )

        return ParameterSensitivityResult(
            parameter_name=p_name,
            units=units,
            evidence_status=evidence_status,
            baseline_param_value=p0,
            baseline_output=y_base,
            perturbation_pct=delta_pct,
            perturbed_param_up=p_up,
            perturbed_param_down=p_down,
            perturbed_output_up=y_up,
            perturbed_output_down=y_down,
            dydp_unnormalized=float(dydp),
            normalized_sensitivity_Sp=s_p,
            normalization_status=norm_status,
            solver_status_up=status_up,
            solver_status_down=status_down,
            warnings=warnings_list,
        )

    def _run_with_parameter_override(
        self,
        request: SimulationRequest,
        overrides: dict[str, float],
    ) -> SimulationResult:
        """Run a simulation with temporary parameter overrides without mutating global state."""
        from vblood.biology.rbc.gsh_redox_model import RBCGSHRedoxModel
        from vblood.simulation.engine import _build_params

        # Build clean params and apply overrides
        params = _build_params(request)
        for k, v in overrides.items():
            params[k] = v

        # Execute ODE integration directly with customized params
        from scipy.integrate import solve_ivp
        from vblood.biology.rbc.gsh_redox_model import (
            IDX_D,
            IDX_GSH,
            IDX_GSSG,
            IDX_H2O2,
            IDX_NADPH,
        )

        model = RBCGSHRedoxModel()
        use_ss = (
            request.use_steady_state_ic
            if request.use_steady_state_ic is not None
            else (request.initial_conditions is None)
        )

        if use_ss:
            from vblood.simulation.steady_state import compute_steady_state

            ss_res = compute_steady_state(model, params)
            y0 = np.array(ss_res.state_vector, dtype=float)
            params["gsh_0"] = float(y0[IDX_GSH])
        else:
            ic = (
                request.initial_conditions
                if request.initial_conditions is not None
                else RBCGSHInitialConditions()
            )
            y0 = model.initial_state(ic)

        if request.exposure.h2o2_bolus_mM > 0:
            y0[IDX_H2O2] += request.exposure.h2o2_bolus_mM

        t_eval = np.linspace(request.t_start_s, request.t_end_s, request.n_eval_points)
        solver_cfg = request.solver

        sol = solve_ivp(
            fun=lambda t, y: model.rhs(t, y, params),
            t_span=(request.t_start_s, request.t_end_s),
            y0=y0,
            method=solver_cfg.method.value,
            t_eval=t_eval,
            rtol=solver_cfg.rtol,
            atol=solver_cfg.atol,
            max_step=solver_cfg.max_step,
        )

        solver_status = SolverStatus.SUCCESS if sol.success else SolverStatus.FAILED

        # Build trajectory
        from vblood.schemas.simulation import TrajectoryPoint

        pts = []
        d_vals = sol.y[IDX_D]
        hemo_pcts = [model.estimated_hemolysis_pct(float(d)) for d in d_vals]

        for i in range(len(sol.t)):
            gsh = float(sol.y[IDX_GSH, i])
            gssg = float(sol.y[IDX_GSSG, i])
            ratio = gsh / gssg if gssg > 0 else 0.0
            pts.append(
                TrajectoryPoint(
                    t_s=float(sol.t[i]),
                    gsh_mM=gsh,
                    gssg_mM=gssg,
                    h2o2_mM=float(sol.y[IDX_H2O2, i]),
                    nadph_mM=float(sol.y[IDX_NADPH, i]),
                    damage=float(d_vals[i]),
                    hemolysis_pct=hemo_pcts[i],
                    gsh_gssg_ratio=ratio,
                )
            )

        final_gsh = float(sol.y[IDX_GSH, -1])
        final_gssg = float(sol.y[IDX_GSSG, -1])
        min_gsh = float(np.min(sol.y[IDX_GSH]))
        max_h2o2 = float(np.max(sol.y[IDX_H2O2]))
        final_d = float(d_vals[-1])
        final_hemo = hemo_pcts[-1]

        return SimulationResult(
            run_id="sensitivity_perturbation",
            model_id=request.model_id,
            model_version=model.metadata.version,
            request=request,
            solver_status=solver_status,
            solver_message=sol.message,
            n_function_evaluations=sol.nfev,
            solver_time_s=0.0,
            warnings=[],
            trajectory=pts,
            final_gsh_mM=final_gsh,
            final_gssg_mM=final_gssg,
            min_gsh_mM=min_gsh,
            max_h2o2_mM=max_h2o2,
            final_damage=final_d,
            final_hemolysis_pct=final_hemo,
            provenance={"overrides": overrides},
        )
