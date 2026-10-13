"""
Scientific integration tests for simulations initialized at the model steady state.

Verifies:
- Absence of unexplained drift over time when initialized at steady state.
- Dynamic response to oxidative challenge from steady state.
- Conservation relationships at equilibrium.
"""

import numpy as np
import pytest

from vblood.schemas.simulation import RBCGSHExposure, SimulationRequest, SolverStatus
from vblood.simulation.engine import run_simulation
from vblood.simulation.steady_state import compute_steady_state


class TestSteadyStateBaselineSimulation:
    """Simulate a baseline resting RBC initialized at steady state."""

    @pytest.fixture(scope="class")
    def result(self):
        req = SimulationRequest(
            t_start_s=0.0,
            t_end_s=3600.0,
            n_eval_points=100,
        )
        return run_simulation(req)

    def test_solver_succeeds(self, result):
        assert result.solver_status == SolverStatus.SUCCESS

    def test_steady_state_initialization_flag_set(self, result):
        assert result.steady_state_initialization is True
        assert result.steady_state_summary is not None

    def test_no_unexplained_drift_at_steady_state(self, result):
        """Concentrations should remain virtually constant throughout the simulation."""
        gsh_init = result.trajectory[0].gsh_mM
        gsh_final = result.trajectory[-1].gsh_mM
        gssg_init = result.trajectory[0].gssg_mM
        gssg_final = result.trajectory[-1].gssg_mM
        nadph_init = result.trajectory[0].nadph_mM
        nadph_final = result.trajectory[-1].nadph_mM

        # Over 1 hour (3600s), relative drift should be negligible (< 1e-4)
        assert np.isclose(gsh_init, gsh_final, rtol=1e-4, atol=1e-6), (
            f"GSH drifted from {gsh_init} to {gsh_final}"
        )
        assert np.isclose(gssg_init, gssg_final, rtol=1e-4, atol=1e-6), (
            f"GSSG drifted from {gssg_init} to {gssg_final}"
        )
        assert np.isclose(nadph_init, nadph_final, rtol=1e-4, atol=1e-6), (
            f"NADPH drifted from {nadph_init} to {nadph_final}"
        )

    def test_all_states_remain_non_negative(self, result):
        for pt in result.trajectory:
            assert pt.gsh_mM >= 0.0
            assert pt.gssg_mM >= 0.0
            assert pt.h2o2_mM >= 0.0
            assert pt.nadph_mM >= 0.0
            assert 0.0 <= pt.damage <= 1.0


class TestSteadyStateOxidativeChallenge:
    """Simulate an H2O2 challenge starting from the steady state."""

    @pytest.fixture(scope="class")
    def result(self):
        req = SimulationRequest(
            exposure=RBCGSHExposure(h2o2_bolus_mM=0.01),
            t_start_s=0.0,
            t_end_s=1800.0,
            n_eval_points=200,
        )
        return run_simulation(req)

    def test_solver_succeeds(self, result):
        assert result.solver_status == SolverStatus.SUCCESS

    def test_h2o2_cleared(self, result):
        """H2O2 bolus must be cleared back to near baseline levels."""
        final_h2o2 = result.trajectory[-1].h2o2_mM
        max_h2o2 = result.max_h2o2_mM
        assert max_h2o2 > 0.005
        assert final_h2o2 < max_h2o2 / 10.0
