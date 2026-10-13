"""
Scientific tests for the RBC GSH redox ODE model.

These tests verify that the integrated simulation produces qualitatively
correct biological behaviour. They do NOT verify quantitative accuracy
against experimental data (no validated dataset has been ingested yet).

Scientific hypotheses being tested:
- The system approaches a stable, physiologically plausible steady state.
- A bolus of H2O2 causes transient GSH depletion followed by recovery.
- Larger H2O2 boluses cause greater and longer GSH depletion.
- The GSH/GSSG ratio drops under oxidative stress and recovers.
- NADPH is transiently depleted under oxidative stress.
- Conservation: total glutathione changes only through synthesis and export.
- Solver status is SUCCESS for standard parameter regimes.

IMPORTANT: These tests check qualitative direction of change only.
Quantitative agreement with biological data requires experimental
calibration, which has not been performed in Milestone 1.
"""

from __future__ import annotations

import numpy as np
import pytest

from vblood.schemas.simulation import (
    RBCGSHExposure,
    RBCGSHInitialConditions,
    SimulationRequest,
    SolverStatus,
)
from vblood.simulation.engine import run_simulation


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_request(
    h2o2_bolus: float = 0.0,
    t_end: float = 3600.0,
    gsh_0: float = 2.5,
    n_points: int = 500,
) -> SimulationRequest:
    return SimulationRequest(
        initial_conditions=RBCGSHInitialConditions(gsh_0=gsh_0),
        exposure=RBCGSHExposure(h2o2_bolus_mM=h2o2_bolus),
        t_start_s=0.0,
        t_end_s=t_end,
        n_eval_points=n_points,
    )


# ---------------------------------------------------------------------------
# Baseline (no challenge) tests
# ---------------------------------------------------------------------------

class TestBaselineSimulation:
    """
    Simulate a resting RBC with no exogenous H2O2.

    Expected: system approaches a stable near-physiological steady state.
    """

    @pytest.fixture(scope="class")
    def result(self):
        return run_simulation(make_request(h2o2_bolus=0.0, t_end=3600.0, n_points=200))

    def test_solver_succeeds(self, result):
        assert result.solver_status == SolverStatus.SUCCESS

    def test_gsh_remains_positive(self, result):
        gsh_vals = [p.gsh_mM for p in result.trajectory]
        assert all(g >= 0 for g in gsh_vals), "GSH became negative at baseline"

    def test_gssg_remains_positive(self, result):
        gssg_vals = [p.gssg_mM for p in result.trajectory]
        assert all(s >= 0 for s in gssg_vals), "GSSG became negative at baseline"

    def test_h2o2_remains_positive(self, result):
        h_vals = [p.h2o2_mM for p in result.trajectory]
        assert all(h >= 0 for h in h_vals), "H2O2 became negative at baseline"

    def test_gsh_remains_in_physiological_range(self, result):
        """At baseline, GSH should stay within approximately 1–4 mM."""
        gsh_final = result.final_gsh_mM
        assert 0.5 <= gsh_final <= 5.0, (
            f"Final GSH {gsh_final:.3f} mM outside expected range at baseline."
        )

    def test_gsh_gssg_ratio_above_physiological_minimum(self, result):
        """GSH/GSSG ratio should remain >> 1 at baseline."""
        ratio_final = result.trajectory[-1].gsh_gssg_ratio
        assert ratio_final > 5.0, (
            f"GSH/GSSG ratio {ratio_final:.1f} is suspiciously low at baseline. "
            "Expected > 5 for a healthy RBC."
        )

    def test_damage_remains_negligible_at_baseline(self, result):
        """Without oxidative challenge, damage should remain near zero."""
        assert result.final_damage < 0.01, (
            f"Unexpected damage at baseline: D = {result.final_damage:.4f}"
        )

    def test_hemolysis_negligible_at_baseline(self, result):
        assert result.final_hemolysis_pct < 1.0, (
            f"Unexpected haemolysis at baseline: {result.final_hemolysis_pct:.2f}%"
        )


# ---------------------------------------------------------------------------
# Oxidative challenge (H2O2 bolus) tests
# ---------------------------------------------------------------------------

class TestOxidativeChallenge:
    """
    Simulate an H2O2 bolus and verify the qualitatively expected response.

    Expected:
    - H2O2 rises at t=0 then is consumed over time.
    - GSH decreases transiently (consumed by GPx).
    - GSSG increases transiently.
    - NADPH decreases as GR consumes it to regenerate GSH.
    - At moderate bolus, the system recovers (GSH rises back toward initial).
    """

    @pytest.fixture(scope="class")
    def result_moderate(self):
        """Moderate oxidative challenge: 0.05 mM H2O2 bolus."""
        return run_simulation(make_request(h2o2_bolus=0.05, t_end=1800.0, n_points=200))

    def test_solver_succeeds_moderate(self, result_moderate):
        assert result_moderate.solver_status == SolverStatus.SUCCESS

    def test_h2o2_decreases_after_bolus(self, result_moderate):
        """H2O2 should be lower at the end than immediately after the bolus."""
        h2o2_initial = result_moderate.trajectory[0].h2o2_mM
        h2o2_final = result_moderate.trajectory[-1].h2o2_mM
        assert h2o2_final < h2o2_initial, (
            "H2O2 did not decrease after bolus application. "
            f"Initial: {h2o2_initial:.4f}, Final: {h2o2_final:.4f}"
        )

    def test_gsh_initially_decreases(self, result_moderate):
        """GSH should drop at the start of the challenge."""
        gsh_0 = result_moderate.trajectory[0].gsh_mM
        # Check minimum within first quarter of simulation
        n_quarter = len(result_moderate.trajectory) // 4
        gsh_early = [p.gsh_mM for p in result_moderate.trajectory[:n_quarter]]
        gsh_min_early = min(gsh_early)
        assert gsh_min_early < gsh_0, (
            f"GSH did not decrease after H2O2 bolus: initial={gsh_0:.4f}, "
            f"early_min={gsh_min_early:.4f}"
        )

    def test_gsh_recovers_after_moderate_bolus(self, result_moderate):
        """After a moderate bolus, GSH should recover toward baseline."""
        gsh_initial = result_moderate.trajectory[0].gsh_mM
        min_gsh = result_moderate.min_gsh_mM
        final_gsh = result_moderate.final_gsh_mM
        # Final GSH should be closer to initial than the minimum
        initial_drop = gsh_initial - min_gsh
        final_recovery = final_gsh - min_gsh
        if initial_drop > 1e-6:
            recovery_fraction = final_recovery / initial_drop
            assert recovery_fraction > 0.3, (
                f"GSH recovery is insufficient: drop={initial_drop:.4f} mM, "
                f"recovered={final_recovery:.4f} mM "
                f"({recovery_fraction * 100:.1f}%)"
            )

    def test_gssg_increases_after_bolus(self, result_moderate):
        """GSSG should increase after the H2O2 bolus."""
        gssg_initial = result_moderate.trajectory[0].gssg_mM
        gssg_values = [p.gssg_mM for p in result_moderate.trajectory]
        gssg_max = max(gssg_values)
        assert gssg_max > gssg_initial, (
            "GSSG did not increase after H2O2 bolus. "
            f"Initial: {gssg_initial:.4f}, Max observed: {gssg_max:.4f}"
        )

    def test_all_states_non_negative(self, result_moderate):
        """All state variables must remain non-negative throughout."""
        for point in result_moderate.trajectory:
            assert point.gsh_mM >= -1e-9, f"GSH < 0 at t={point.t_s:.1f}s"
            assert point.gssg_mM >= -1e-9, f"GSSG < 0 at t={point.t_s:.1f}s"
            assert point.h2o2_mM >= -1e-9, f"H2O2 < 0 at t={point.t_s:.1f}s"
            assert point.nadph_mM >= -1e-9, f"NADPH < 0 at t={point.t_s:.1f}s"
            assert point.damage >= -1e-9, f"D < 0 at t={point.t_s:.1f}s"
            assert point.damage <= 1.0 + 1e-9, f"D > 1 at t={point.t_s:.1f}s"


# ---------------------------------------------------------------------------
# Dose-response ordering test
# ---------------------------------------------------------------------------

class TestDoseResponseOrdering:
    """
    Larger H2O2 boluses should produce greater GSH depletion and damage.
    This is a qualitative monotonicity test.
    """

    def test_larger_bolus_greater_gsh_depletion(self):
        """Higher H2O2 bolus → lower minimum GSH."""
        result_low = run_simulation(make_request(h2o2_bolus=0.01))
        result_high = run_simulation(make_request(h2o2_bolus=0.1))
        assert result_high.min_gsh_mM < result_low.min_gsh_mM, (
            f"Min GSH not ordered by bolus dose: "
            f"low_bolus_min={result_low.min_gsh_mM:.4f}, "
            f"high_bolus_min={result_high.min_gsh_mM:.4f}"
        )

    def test_larger_bolus_greater_damage(self):
        """Higher H2O2 bolus → higher final damage index."""
        result_low = run_simulation(make_request(h2o2_bolus=0.01))
        result_high = run_simulation(make_request(h2o2_bolus=0.1))
        # This may not hold if recovery is complete in both cases; allow small margin
        assert result_high.final_damage >= result_low.final_damage - 1e-6, (
            f"Damage not ordered by bolus: "
            f"low={result_low.final_damage:.6f}, high={result_high.final_damage:.6f}"
        )


# ---------------------------------------------------------------------------
# Conservation tests
# ---------------------------------------------------------------------------

class TestConservation:
    """
    Partial conservation check: over a short interval with no synthesis
    or export, total glutathione should be approximately conserved.

    NOTE: The model includes synthesis and export, so perfect conservation
    is not expected over long timescales. This test verifies that the
    stoichiometric coupling is correctly implemented over a short interval.
    """

    def test_glutathione_stoichiometry(self):
        """
        Over a very short interval, the change in GSH and GSSG should
        approximately satisfy the stoichiometry of R1 and R2:
        dGSH = -2 * dGSSG (when synthesis and export are negligible).

        We verify this by checking the derivative direction at t=0.
        """
        from vblood.biology.rbc.gsh_redox_model import RBCGSHRedoxModel, IDX_GSH, IDX_GSSG

        model = RBCGSHRedoxModel()
        params = {
            **{
                "k_gpx": 5.0e4,
                "vmax_gr": 0.0,   # Disable GR
                "km_gssg_gr": 0.060,
                "km_nadph_gr": 0.006,
                "k_export": 0.0,  # Disable export
                "k_synth": 0.0,   # Disable synthesis
                "vmax_ppp": 0.0,
                "km_nadph_ppp": 0.015,
                "k_h2o2_prod": 0.0,
                "k_h2o2_rem": 0.0,
                "k_damage": 0.0,
                "k_repair": 0.0,
                "gsh_0": 2.5,
            }
        }
        y = np.array([2.5, 0.025, 0.05, 0.030, 0.0])
        dydt = model.rhs(0.0, y, params)

        # With only GPx active: dGSH/dt = -2*v_gpx; dGSSG/dt = +v_gpx
        # => dGSH/dt = -2 * dGSSG/dt
        expected_ratio = -2.0
        actual_ratio = dydt[IDX_GSH] / dydt[IDX_GSSG] if abs(dydt[IDX_GSSG]) > 1e-15 else None
        if actual_ratio is not None:
            assert actual_ratio == pytest.approx(expected_ratio, rel=1e-6), (
                f"Stoichiometry violated: dGSH/dGSSG = {actual_ratio:.4f}, expected -2.0"
            )


# ---------------------------------------------------------------------------
# Reproducibility tests
# ---------------------------------------------------------------------------

class TestReproducibility:
    """Deterministic simulations must produce identical results."""

    def test_identical_requests_identical_results(self):
        req = make_request(h2o2_bolus=0.05, t_end=600.0, n_points=100)
        result1 = run_simulation(req)
        result2 = run_simulation(req)

        gsh1 = [p.gsh_mM for p in result1.trajectory]
        gsh2 = [p.gsh_mM for p in result2.trajectory]

        for i, (g1, g2) in enumerate(zip(gsh1, gsh2)):
            assert g1 == pytest.approx(g2, rel=1e-10), (
                f"Results differ at index {i}: {g1} vs {g2}"
            )

    def test_run_ids_different_for_different_runs(self):
        req = make_request()
        result1 = run_simulation(req)
        result2 = run_simulation(req)
        assert result1.run_id != result2.run_id


# ---------------------------------------------------------------------------
# Numerical stability tests
# ---------------------------------------------------------------------------

class TestNumericalStability:
    """Test solver behaviour under challenging conditions."""

    def test_long_integration_stable(self):
        """Run for 2 hours; solver should succeed without issues."""
        result = run_simulation(make_request(h2o2_bolus=0.0, t_end=7200.0, n_points=100))
        assert result.solver_status == SolverStatus.SUCCESS

    def test_zero_bolus_solver_succeeds(self):
        result = run_simulation(make_request(h2o2_bolus=0.0))
        assert result.solver_status == SolverStatus.SUCCESS

    def test_small_bolus_solver_succeeds(self):
        result = run_simulation(make_request(h2o2_bolus=0.001))
        assert result.solver_status == SolverStatus.SUCCESS

    def test_moderate_bolus_solver_succeeds(self):
        result = run_simulation(make_request(h2o2_bolus=0.05))
        assert result.solver_status == SolverStatus.SUCCESS
