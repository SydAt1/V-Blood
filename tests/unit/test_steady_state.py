"""
Unit tests for the steady-state solver and equilibrium analysis (Task 1).

Tests cover:
- Steady-state residual below configured tolerance.
- Reproducibility across repeated calculations and caching.
- Positivity constraint enforcement (rejection of non-physical states).
- Jacobian eigenvalue dynamical stability.
- Physiological plausibility diagnostics.
- Parameter set fingerprinting and provenance tracking.
- Override of default steady state with explicit initial conditions.
- Handling of invalid parameters (e.g., negative rate constants).
"""

import numpy as np
import pytest

from vblood.biology.rbc.gsh_redox_model import (
    IDX_D,
    IDX_GSH,
    IDX_GSSG,
    IDX_H2O2,
    IDX_NADPH,
    RBCGSHRedoxModel,
)
from vblood.biology.rbc.parameters import DEFAULT_PARAMETERS
from vblood.schemas.simulation import RBCGSHInitialConditions, SimulationRequest
from vblood.simulation.engine import run_simulation
from vblood.simulation.steady_state import (
    SteadyStateSolver,
    compute_parameter_hash,
    compute_steady_state,
)


class TestSteadyStateSolver:
    """Core mathematical and numerical checks on the steady-state solver."""

    def test_residual_below_default_tolerance(self):
        """Residual norm ||f(x*, p)||_inf must be below 1e-8."""
        res = compute_steady_state(tolerance=1e-8)
        assert res.converged is True
        assert res.residual_norm < 1e-8, f"Residual norm {res.residual_norm} exceeds 1e-8"
        assert res.residual_l2 < 1e-8

    def test_residual_below_tight_tolerance(self):
        """Solver should support configurable tighter tolerances (e.g. 1e-10)."""
        res = compute_steady_state(tolerance=1e-10, use_cache=False)
        assert res.converged is True
        assert res.residual_norm < 1e-10

    def test_reproducibility(self):
        """Repeated calculations must return bit-for-bit identical results."""
        res1 = compute_steady_state(use_cache=False)
        res2 = compute_steady_state(use_cache=False)
        assert res1.state_vector == res2.state_vector
        assert res1.parameter_hash == res2.parameter_hash
        assert res1.residual_norm == res2.residual_norm

    def test_positivity_constraints_satisfied(self):
        """All concentrations at equilibrium must be strictly non-negative."""
        res = compute_steady_state()
        assert res.is_physically_valid is True
        for var_name, val in res.state.items():
            assert val >= 0.0, f"State variable {var_name} is negative: {val}"
        assert 0.0 <= res.state["D"] <= 1.0

    def test_linear_dynamical_stability(self):
        """Eigenvalues of Jacobian df/dx must have strictly negative real parts."""
        res = compute_steady_state()
        assert res.is_dynamically_stable is True
        assert res.max_eigenvalue_real < 0.0
        assert all(ev < 0.0 for ev in res.eigenvalues_real)

    def test_parameter_provenance_hash(self):
        """Parameter hash must change when parameters are modified."""
        params1 = DEFAULT_PARAMETERS.to_dict()
        params2 = DEFAULT_PARAMETERS.to_dict()
        params2["k_export"] = 0.05

        h1 = compute_parameter_hash(params1)
        h2 = compute_parameter_hash(params2)
        assert h1 != h2
        assert len(h1) == 16

    def test_diagnostics_report_drift_cause(self):
        """Diagnostics must provide clear biological rationale for non-physiological SS."""
        res = compute_steady_state()
        assert res.is_physiologically_plausible is False
        assert len(res.diagnostics) >= 3
        diag_text = " ".join(res.diagnostics)
        assert "k_synth" in diag_text or "k_export" in diag_text
        assert "NADPH" in diag_text
        assert "GSH" in diag_text

    def test_invalid_parameters_raise_meaningful_error(self):
        """Non-positive kinetic parameters should raise RuntimeError or ValueError."""
        model = RBCGSHRedoxModel()
        params = DEFAULT_PARAMETERS.to_dict()
        params["k_export"] = -0.01  # physically invalid

        solver = SteadyStateSolver()
        with pytest.raises((RuntimeError, ValueError)):
            solver.solve(model, params, use_cache=False)


class TestSteadyStateWorkflowIntegration:
    """Tests verifying simulation engine integration and initial condition overrides."""

    def test_default_simulation_uses_steady_state(self):
        """When initial_conditions is omitted, simulation uses steady-state equilibrium."""
        req = SimulationRequest(t_end_s=10.0, n_eval_points=10)
        assert req.initial_conditions is None
        assert req.use_steady_state_ic is None

        result = run_simulation(req)
        assert result.steady_state_initialization is True
        assert result.steady_state_summary is not None
        assert result.steady_state_summary["converged"] is True

        # Initial point in trajectory should match steady-state values
        traj0 = result.trajectory[0]
        ss_state = result.steady_state_summary["state"]
        assert np.isclose(traj0.gsh_mM, ss_state["GSH"], rtol=1e-4)
        assert np.isclose(traj0.gssg_mM, ss_state["GSSG"], rtol=1e-4)
        assert np.isclose(traj0.nadph_mM, ss_state["NADPH"], rtol=1e-4)

    def test_explicit_ic_overrides_default_equilibrium(self):
        """When initial_conditions is explicitly provided, it overrides default steady state."""
        custom_ic = RBCGSHInitialConditions(gsh_0=2.7, gssg_0=0.03, nadph_0=0.04)
        req = SimulationRequest(
            initial_conditions=custom_ic,
            t_end_s=10.0,
            n_eval_points=10,
        )

        result = run_simulation(req)
        assert result.steady_state_initialization is False
        traj0 = result.trajectory[0]
        assert traj0.gsh_mM == 2.7
        assert traj0.gssg_mM == 0.03
        assert traj0.nadph_mM == 0.04

    def test_explicit_force_steady_state_flag(self):
        """use_steady_state_ic=True forces steady state even if custom IC is provided."""
        custom_ic = RBCGSHInitialConditions(gsh_0=2.7)
        req = SimulationRequest(
            initial_conditions=custom_ic,
            use_steady_state_ic=True,
            t_end_s=10.0,
            n_eval_points=10,
        )

        result = run_simulation(req)
        assert result.steady_state_initialization is True
        traj0 = result.trajectory[0]
        # Should NOT be 2.7; should be steady state value
        assert not np.isclose(traj0.gsh_mM, 2.7)

    def test_explicit_disable_steady_state_flag(self):
        """use_steady_state_ic=False forces using explicit or default IC without computing SS."""
        req = SimulationRequest(
            use_steady_state_ic=False,
            t_end_s=10.0,
            n_eval_points=10,
        )

        result = run_simulation(req)
        assert result.steady_state_initialization is False
        traj0 = result.trajectory[0]
        # Default physiological initial condition is 2.5
        assert traj0.gsh_mM == 2.5
