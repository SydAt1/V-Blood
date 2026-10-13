"""
ODE simulation engine for V-Blood.

This module provides the SimulationEngine class, which integrates any
BiologicalModel over a specified time interval and returns a validated
SimulationResult.

The engine is designed to be usable without any API, database, LLM, or
frontend — it is a pure Python computation.

Design decisions:
- scipy.integrate.solve_ivp with RK45 is the default integrator.
  It is adaptive, well-tested, and appropriate for stiff-to-moderately-
  stiff biological systems. BDF or LSODA should be used if stiffness
  is detected.
- The engine never suppresses integration failures; it captures them as
  SolverStatus.FAILED and emits a SimulationWarning.
- Bolus application: the exogenous H2O2 bolus is added to the initial
  state vector at t=bolus_time_s. For simplicity in Milestone 1, only
  t=0 bolus is supported without event discontinuities.
- Positivity clamping in the ODE rhs is a modelling decision, not
  a solver hack. The model equations are not defined for negative
  concentrations.
"""

from __future__ import annotations

import time
import uuid
import warnings
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

import structlog

from vblood.biology.base import BiologicalModel
from vblood.biology.rbc.gsh_redox_model import (
    IDX_D,
    IDX_GSH,
    IDX_GSSG,
    IDX_H2O2,
    IDX_NADPH,
    RBCGSHRedoxModel,
)
from vblood.biology.rbc.parameters import DEFAULT_PARAMETERS
from vblood.schemas.simulation import (
    RBCGSHInitialConditions,
    SimulationRequest,
    SimulationResult,
    SimulationWarning,
    SolverStatus,
    TrajectoryPoint,
)

log = structlog.get_logger(__name__)

# Model registry — maps model_id strings to model class instances.
# Extend this registry when new models are added.
_MODEL_REGISTRY: dict[str, BiologicalModel] = {
    "rbc-gsh-redox-v1": RBCGSHRedoxModel(),
}


def _build_params(request: SimulationRequest) -> dict[str, Any]:
    """Construct the parameter dictionary for the requested model.

    For Milestone 1 and 2, default parameter set is used as baseline.
    Future milestones will allow caller-specified parameter sets.

    Args:
        request: The validated simulation request.

    Returns:
        Parameter dictionary compatible with the model's rhs method.
    """
    params = DEFAULT_PARAMETERS.to_dict()
    # Inject reference GSH for damage equation
    if request.initial_conditions is not None:
        params["gsh_0"] = request.initial_conditions.gsh_0
    else:
        params["gsh_0"] = 2.5
    return params


def run_simulation(request: SimulationRequest) -> SimulationResult:
    """Run a single simulation from a validated SimulationRequest.

    This is the primary entry point for the simulation engine.
    It can be called directly from Python without the API, database,
    or any other infrastructure.

    Args:
        request: A validated :class:`SimulationRequest` object.

    Returns:
        A :class:`SimulationResult` containing the full trajectory,
        solver metadata, warnings, and derived endpoints.

    Raises:
        ValueError: If the model_id is not registered.
        ValueError: If parameter validation fails.
    """
    run_id = str(uuid.uuid4())
    log.info("Simulation starting", run_id=run_id, model_id=request.model_id)

    # ------------------------------------------------------------------ #
    # 1. Resolve model
    # ------------------------------------------------------------------ #
    if request.model_id not in _MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model_id '{request.model_id}'. "
            f"Registered models: {list(_MODEL_REGISTRY.keys())}."
        )
    model = _MODEL_REGISTRY[request.model_id]

    # ------------------------------------------------------------------ #
    # 2. Build and validate parameters
    # ------------------------------------------------------------------ #
    params = _build_params(request)
    param_errors = model.validate_params(params)
    if param_errors:
        raise ValueError(
            f"Parameter validation failed for model '{request.model_id}':\n"
            + "\n".join(f"  - {e}" for e in param_errors)
        )

    sim_warnings: list[SimulationWarning] = []

    # Warn about synthetic parameters
    if isinstance(model, RBCGSHRedoxModel):
        from vblood.biology.rbc.parameters import DEFAULT_PARAMETERS as dp
        synthetic = dp.list_synthetic_parameters()
        if synthetic:
            sim_warnings.append(
                SimulationWarning(
                    code="SYNTHETIC_PARAMS",
                    message=(
                        f"The following parameters are SYNTHETIC placeholders with no "
                        f"experimental basis: {', '.join(synthetic)}. "
                        "Simulation outputs derived from these parameters must not be "
                        "used for biological predictions."
                    ),
                    severity="WARNING",
                    details={"synthetic_parameters": synthetic},
                )
            )

    # ------------------------------------------------------------------ #
    # 3. Build initial state vector
    # ------------------------------------------------------------------ #
    use_ss = (
        request.use_steady_state_ic
        if request.use_steady_state_ic is not None
        else (request.initial_conditions is None)
    )

    steady_state_summary: dict[str, Any] | None = None
    if use_ss:
        from vblood.simulation.steady_state import compute_steady_state

        log.info("Computing model steady state for initial conditions", model_id=request.model_id)
        ss_result = compute_steady_state(model, params)
        if not ss_result.converged:
            raise RuntimeError(
                f"Steady-state calculation failed to converge for model '{request.model_id}'. "
                f"Residual norm: {ss_result.residual_norm:.3e} > {ss_result.tolerance:.3e}."
            )
        y0 = np.array(ss_result.state_vector, dtype=float)
        params["gsh_0"] = float(y0[IDX_GSH])
        steady_state_summary = ss_result.model_dump()

        if not ss_result.is_physiologically_plausible:
            sim_warnings.append(
                SimulationWarning(
                    code="STEADY_STATE_UNPHYSIOLOGICAL",
                    message=(
                        f"Computed steady state for model '{request.model_id}' exhibits "
                        f"unphysiological concentrations (e.g. [GSH]={y0[IDX_GSH]:.4e} mM, "
                        f"[GSSG]={y0[IDX_GSSG]:.4e} mM, [NADPH]={y0[IDX_NADPH]:.4e} mM). "
                        "See steady-state diagnostics for biochemical causes."
                    ),
                    severity="WARNING",
                    details={
                        "diagnostics": ss_result.diagnostics,
                        "residual_norm": ss_result.residual_norm,
                    },
                )
            )
    else:
        ic = request.initial_conditions if request.initial_conditions is not None else RBCGSHInitialConditions()
        y0 = model.initial_state(ic)

    # Apply H2O2 bolus at t=0
    exposure = request.exposure
    if exposure.h2o2_bolus_mM > 0:
        if exposure.bolus_time_s > 0:
            sim_warnings.append(
                SimulationWarning(
                    code="BOLUS_TIME_NOT_ZERO",
                    message=(
                        f"bolus_time_s={exposure.bolus_time_s} > 0 is not supported "
                        "in Milestone 1. The bolus will be applied at t=0."
                    ),
                    severity="WARNING",
                )
            )
        y0[IDX_H2O2] += exposure.h2o2_bolus_mM
        log.info(
            "H2O2 bolus applied",
            bolus_mM=exposure.h2o2_bolus_mM,
            new_h2o2_0_mM=y0[IDX_H2O2],
        )

        if exposure.h2o2_bolus_mM > 0.5:
            sim_warnings.append(
                SimulationWarning(
                    code="GPX_APPROX_INVALID",
                    message=(
                        f"H2O2 bolus of {exposure.h2o2_bolus_mM} mM causes [H2O2] to "
                        "exceed 0.5 mM, invalidating the bimolecular GPx approximation. "
                        "Results at this concentration are model extrapolations."
                    ),
                    severity="WARNING",
                    details={"h2o2_peak_mM": float(y0[IDX_H2O2])},
                )
            )

    # ------------------------------------------------------------------ #
    # 4. Capture any Python warnings from the model/schema
    # ------------------------------------------------------------------ #
    with warnings.catch_warnings(record=True) as captured_warnings:
        warnings.simplefilter("always")
        # Initial constraint check
        init_constraint_msgs = model.check_constraints(
            request.t_start_s, y0, params
        )

    for cw in captured_warnings:
        sim_warnings.append(
            SimulationWarning(
                code="PYTHON_WARNING",
                message=str(cw.message),
                severity="WARNING",
            )
        )

    for msg in init_constraint_msgs:
        sim_warnings.append(
            SimulationWarning(
                code="CONSTRAINT_VIOLATION_INIT",
                message=msg,
                severity="WARNING",
            )
        )

    # ------------------------------------------------------------------ #
    # 5. Define the wrapped RHS (captures params in closure)
    # ------------------------------------------------------------------ #
    def rhs_wrapper(t: float, y: np.ndarray) -> np.ndarray:
        return model.rhs(t, y, params)

    # ------------------------------------------------------------------ #
    # 6. Run the integrator
    # ------------------------------------------------------------------ #
    t_span = (request.t_start_s, request.t_end_s)
    t_eval = np.linspace(request.t_start_s, request.t_end_s, request.n_eval_points)

    solver_cfg = request.solver
    wall_t0 = time.monotonic()

    with warnings.catch_warnings(record=True) as solver_warnings:
        warnings.simplefilter("always")
        sol = solve_ivp(
            fun=rhs_wrapper,
            t_span=t_span,
            y0=y0,
            method=solver_cfg.method.value,
            t_eval=t_eval,
            rtol=solver_cfg.rtol,
            atol=solver_cfg.atol,
            max_step=solver_cfg.max_step,
            dense_output=solver_cfg.dense_output,
        )

    wall_elapsed = time.monotonic() - wall_t0

    for sw in solver_warnings:
        sim_warnings.append(
            SimulationWarning(
                code="SOLVER_WARNING",
                message=str(sw.message),
                severity="WARNING",
            )
        )

    # ------------------------------------------------------------------ #
    # 7. Assess solver status
    # ------------------------------------------------------------------ #
    if sol.success:
        solver_status = SolverStatus.SUCCESS
        log.info(
            "Simulation completed",
            run_id=run_id,
            n_evals=sol.nfev,
            wall_s=wall_elapsed,
        )
    else:
        solver_status = SolverStatus.FAILED
        sim_warnings.append(
            SimulationWarning(
                code="SOLVER_FAILURE",
                message=f"ODE solver failed: {sol.message}",
                severity="ERROR",
                details={"solver_message": sol.message},
            )
        )
        log.error(
            "Simulation failed",
            run_id=run_id,
            solver_message=sol.message,
        )

    # ------------------------------------------------------------------ #
    # 8. Extract trajectory
    # ------------------------------------------------------------------ #
    # sol.y shape: (n_state_vars, n_time_points)
    t_arr = sol.t
    y_arr = sol.y  # (5, n_points)

    gsh_arr = y_arr[IDX_GSH]
    gssg_arr = y_arr[IDX_GSSG]
    h2o2_arr = y_arr[IDX_H2O2]
    nadph_arr = y_arr[IDX_NADPH]
    d_arr = y_arr[IDX_D]

    # Post-integration constraint check at the end point
    final_constraints = model.check_constraints(
        float(t_arr[-1]), y_arr[:, -1], params
    )
    for msg in final_constraints:
        sim_warnings.append(
            SimulationWarning(
                code="CONSTRAINT_VIOLATION_FINAL",
                message=msg,
                severity="WARNING",
            )
        )

    # ------------------------------------------------------------------ #
    # 9. Build trajectory points
    # ------------------------------------------------------------------ #
    trajectory: list[TrajectoryPoint] = []
    for i in range(len(t_arr)):
        gsh_val = float(gsh_arr[i])
        gssg_val = float(gssg_arr[i])
        d_val = min(1.0, max(0.0, float(d_arr[i])))
        ratio = gsh_val / gssg_val if gssg_val > 1e-12 else float("inf")
        h_pct = RBCGSHRedoxModel.estimated_hemolysis_pct(d_val)
        trajectory.append(
            TrajectoryPoint(
                t_s=float(t_arr[i]),
                gsh_mM=gsh_val,
                gssg_mM=gssg_val,
                h2o2_mM=float(h2o2_arr[i]),
                nadph_mM=float(nadph_arr[i]),
                damage=d_val,
                hemolysis_pct=h_pct,
                gsh_gssg_ratio=ratio,
            )
        )

    # ------------------------------------------------------------------ #
    # 10. Compute summary statistics
    # ------------------------------------------------------------------ #
    final_gsh = float(gsh_arr[-1])
    final_gssg = float(gssg_arr[-1])
    min_gsh = float(np.min(gsh_arr))
    max_h2o2 = float(np.max(h2o2_arr))
    final_d = min(1.0, max(0.0, float(d_arr[-1])))
    final_hemo = RBCGSHRedoxModel.estimated_hemolysis_pct(final_d)

    # ------------------------------------------------------------------ #
    # 11. Build provenance record
    # ------------------------------------------------------------------ #
    provenance = {
        "run_id": run_id,
        "model_id": request.model_id,
        "model_version": model.metadata.version,
        "parameter_set": "default_v1",
        "solver_method": solver_cfg.method.value,
        "rtol": solver_cfg.rtol,
        "atol": solver_cfg.atol,
        "n_eval_points": request.n_eval_points,
        "t_start_s": request.t_start_s,
        "t_end_s": request.t_end_s,
        "h2o2_bolus_mM": exposure.h2o2_bolus_mM,
        "n_synthetic_params": len(
            DEFAULT_PARAMETERS.list_synthetic_parameters()
        ),
        "solver_status": solver_status.value,
        "n_warnings": len(sim_warnings),
        "steady_state_initialization": use_ss,
    }
    if steady_state_summary is not None:
        provenance["steady_state"] = {
            "parameter_hash": steady_state_summary.get("parameter_hash"),
            "residual_norm": steady_state_summary.get("residual_norm"),
            "is_dynamically_stable": steady_state_summary.get("is_dynamically_stable"),
        }

    return SimulationResult(
        run_id=run_id,
        model_id=request.model_id,
        model_version=model.metadata.version,
        request=request,
        solver_status=solver_status,
        solver_message=sol.message,
        n_function_evaluations=sol.nfev,
        solver_time_s=wall_elapsed,
        warnings=sim_warnings,
        trajectory=trajectory,
        final_gsh_mM=final_gsh,
        final_gssg_mM=final_gssg,
        min_gsh_mM=min_gsh,
        max_h2o2_mM=max_h2o2,
        final_damage=final_d,
        final_hemolysis_pct=final_hemo,
        provenance=provenance,
        steady_state_initialization=use_ss,
        steady_state_summary=steady_state_summary,
    )


def list_registered_models() -> list[dict[str, str]]:
    """Return metadata for all registered models.

    Returns:
        List of dicts with keys: model_id, version, name, description.
    """
    return [
        {
            "model_id": model.metadata.model_id,
            "version": model.metadata.version,
            "name": model.metadata.name,
            "description": model.metadata.description,
        }
        for model in _MODEL_REGISTRY.values()
    ]
