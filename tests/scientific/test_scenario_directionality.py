"""
Scientific directionality and conservation tests for scenario mechanisms (Milestone 4 - Task 7).
"""

import pytest
import numpy as np

from vblood.scenarios.engine import (
    CompoundExposure,
    ExposureProfile,
    ScenarioRequest,
    run_scenario,
)
from vblood.scenarios.population import PopulationRequest, simulate_population


class TestMechanismDirectionality:
    """L1 Directionality tests verifying expected physiological trends per mechanism class."""

    def test_conjugator_depletes_gsh_without_h2o2_rise(self):
        """Conjugator (CDNB) should lower GSH directly without causing a peroxide spike."""
        req = ScenarioRequest(
            compounds=[CompoundExposure(compound_id="cmp_cdnb", dose_mM=0.05)],
            duration_s=600.0,
            model_version="rbc-g6pd-gsh-v2",
        )
        res = run_scenario(req)
        traj = res.simulation_result.trajectory

        gsh_0 = traj[0].gsh_mM
        gsh_f = traj[-1].gsh_mM
        max_h2o2 = max(p.h2o2_mM for p in traj)

        # GSH is depleted
        assert gsh_f < gsh_0
        # H2O2 does not spike above baseline initial concentration
        assert max_h2o2 <= 1.001e-4

    def test_redox_cycler_elevates_h2o2_and_drains_nadph(self):
        """Redox cycler (Menadione) should generate H2O2 and depress NADPH in G6PD-vulnerable cells."""
        req = ScenarioRequest(
            compounds=[CompoundExposure(compound_id="cmp_menadione", dose_mM=0.02)],
            duration_s=600.0,
            g6pd_alpha=0.1,
            model_version="rbc-g6pd-gsh-v2",
        )
        res = run_scenario(req)
        traj = res.simulation_result.trajectory

        nadph_0 = traj[0].nadph_mM
        min_nadph = min(p.nadph_mM for p in traj)
        max_h2o2 = max(p.h2o2_mM for p in traj)

        # NADPH is depressed by cycling
        assert min_nadph < nadph_0
        # H2O2 is actively generated
        assert max_h2o2 > 1e-6

    def test_g6pd_inhibitor_worsens_redox_at_low_alpha(self):
        """G6PD inhibitor (DHEA) produces greater GSH nadir deficit at lower G6PD activity."""
        # Normal alpha = 1.0 with inhibitor
        req_normal = ScenarioRequest(
            compounds=[
                CompoundExposure(compound_id="cmp_h2o2", dose_mM=0.05),
                CompoundExposure(compound_id="cmp_dhea", dose_mM=0.05),
            ],
            g6pd_alpha=1.0,
            duration_s=1200.0,
        )
        res_normal = run_scenario(req_normal)

        # Deficient alpha = 0.2 with same inhibitor
        req_deficient = ScenarioRequest(
            compounds=[
                CompoundExposure(compound_id="cmp_h2o2", dose_mM=0.05),
                CompoundExposure(compound_id="cmp_dhea", dose_mM=0.05),
            ],
            g6pd_alpha=0.2,
            duration_s=1200.0,
        )
        res_deficient = run_scenario(req_deficient)

        # Deficient RBC experiences worse GSH nadir and higher damage
        assert res_deficient.derived_metrics.gsh_nadir_mM < res_normal.derived_metrics.gsh_nadir_mM
        assert res_deficient.simulation_result.final_damage >= res_normal.simulation_result.final_damage

    def test_all_states_remain_non_negative_under_stress(self):
        """State variables must remain non-negative under multi-compound cocktail."""
        req = ScenarioRequest(
            compounds=[
                CompoundExposure(compound_id="cmp_menadione", dose_mM=0.03),
                CompoundExposure(compound_id="cmp_nem", dose_mM=0.02),
            ],
            duration_s=600.0,
        )
        res = run_scenario(req)
        traj = res.simulation_result.trajectory

        for pt in traj:
            assert pt.gsh_mM >= 0.0
            assert pt.gssg_mM >= 0.0
            assert pt.h2o2_mM >= 0.0
            assert pt.nadph_mM >= 0.0
            assert 0.0 <= pt.damage <= 1.0

    def test_unverified_compound_flagged_in_result(self):
        """Scenarios using UNVERIFIED compounds must flag has_unverified_compounds=True."""
        req = ScenarioRequest(
            compounds=[CompoundExposure(compound_id="cmp_xenobiotic_x101", dose_mM=0.01)],
            duration_s=300.0,
        )
        res = run_scenario(req)
        assert res.has_unverified_compounds
        assert "cmp_xenobiotic_x101" in res.unverified_compounds


class TestPopulationSimulation:
    """Tests for cohort simulation, reproducibility, and timing."""

    def test_population_reproducibility_with_seed(self):
        """Identical random seeds must produce identical percentile bands."""
        req = PopulationRequest(
            scenario_request=ScenarioRequest(
                compounds=[CompoundExposure(compound_id="cmp_h2o2", dose_mM=0.05)],
                duration_s=600.0,
            ),
            n_cells=50,
            random_seed=12345,
        )
        res1 = simulate_population(req)
        res2 = simulate_population(req)

        assert res1.mean_gsh_nadir_mM == pytest.approx(res2.mean_gsh_nadir_mM)
        assert res1.pct_cells_below_mild_gsh == res2.pct_cells_below_mild_gsh
        assert res1.percentile_bands.gsh_p50 == pytest.approx(res2.percentile_bands.gsh_p50)

    def test_population_execution_speed(self):
        """Simulating 1000 cells must complete in under 5 seconds."""
        req = PopulationRequest(
            scenario_request=ScenarioRequest(
                compounds=[CompoundExposure(compound_id="cmp_menadione", dose_mM=0.01)],
                duration_s=600.0,
            ),
            n_cells=1000,
            random_seed=42,
        )
        res = simulate_population(req)
        assert res.n_cells == 1000
        # Check execution speed
        assert res.execution_time_s < 5.0
        assert len(res.percentile_bands.time_points_s) > 100
