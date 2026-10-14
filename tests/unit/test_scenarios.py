"""
Unit tests for Scenario and Compound Library components (Milestone 4).
"""

import pytest
from vblood.reporting.visual_state import (
    CellVisualState,
    classify_cell_state,
    trajectory_to_visual_frames,
)
from vblood.scenarios.compounds import CompoundEntry, get_compound_library
from vblood.scenarios.engine import (
    CompoundExposure,
    ExposureProfile,
    ScenarioRequest,
    build_mechanism_specs,
    run_scenario,
)
from vblood.scenarios.mechanisms import (
    DirectOxidantSpec,
    EnzymeInhibitorSpec,
    EvidenceLevel,
    GSHConjugatorSpec,
    MechanismType,
    ParameterSpec,
    RedoxCyclerSpec,
    ScenarioMechanismHooks,
)
from vblood.scenarios.metrics import compute_scenario_metrics
from vblood.schemas.simulation import TrajectoryPoint


class TestCompoundLibrary:
    """Tests for compounds.json parsing and validation."""

    def test_library_loads_curated_compounds(self):
        lib = get_compound_library()
        all_comps = lib.list_all()
        assert len(all_comps) >= 6

        ids = [c.compound_id for c in all_comps]
        assert "cmp_h2o2" in ids
        assert "cmp_menadione" in ids
        assert "cmp_cdnb" in ids
        assert "cmp_nem" in ids
        assert "cmp_dhea" in ids
        assert "cmp_xenobiotic_x101" in ids

    def test_sha256_hash_computed(self):
        lib = get_compound_library()
        assert len(lib.sha256_hash) == 64

    def test_unverified_compound_flagging(self):
        lib = get_compound_library()
        x101 = lib.get_or_raise("cmp_xenobiotic_x101")
        assert x101.is_unverified
        assert x101.evidence_level == EvidenceLevel.UNVERIFIED

        h2o2 = lib.get_or_raise("cmp_h2o2")
        assert not h2o2.is_unverified
        assert h2o2.evidence_level == EvidenceLevel.CURATED


class TestMechanismSpecs:
    """Tests for mechanism parameter bounds and dynamic hook evaluations."""

    def test_parameter_spec_bounds_validation(self):
        with pytest.raises(ValueError):
            ParameterSpec(
                name="invalid_p",
                value=2.0,
                units="mM",
                min_bound=5.0,
                max_bound=10.0,
                provenance="test",
            )

    def test_conjugator_rate_computation(self):
        spec = GSHConjugatorSpec(compound_conc_mM=0.1, rate_constant_mM_s=0.05)
        hooks = ScenarioMechanismHooks([spec])
        # State: [GSH=2.0, GSSG=0.02, H2O2=0.0, NADPH=0.03, D=0.0]
        rates = hooks.compute_rates(t=0.0, y=[2.0, 0.02, 0.0, 0.03, 0.0])
        assert rates["v_gsh_conjugation"] == pytest.approx(0.1 * 0.05 * 2.0)
        assert rates["v_oxidant_influx"] == 0.0
        assert rates["v_redox_cycle"] == 0.0

    def test_redox_cycler_rate_computation(self):
        spec = RedoxCyclerSpec(compound_conc_mM=0.05, catalytic_rate_s=0.02, km_nadph_mM=0.010)
        hooks = ScenarioMechanismHooks([spec])
        # NADPH = 0.010 mM -> saturation = 0.5
        rates = hooks.compute_rates(t=0.0, y=[2.5, 0.02, 0.0, 0.010, 0.0])
        expected_rate = 0.05 * 0.02 * 0.5
        assert rates["v_redox_cycle"] == pytest.approx(expected_rate)


class TestDerivedMetricsAndVisualFrames:
    """Tests for trajectory metrics and visual state classification."""

    def test_classification_logic(self):
        assert classify_cell_state(2.5, 0.01) == CellVisualState.HEALTHY
        assert classify_cell_state(1.2, 0.02) == CellVisualState.STRESSED
        assert classify_cell_state(0.5, 0.10) == CellVisualState.SEVERELY_STRESSED
        assert classify_cell_state(0.1, 0.10) == CellVisualState.LYSIS_RISK
        assert classify_cell_state(2.0, 0.55) == CellVisualState.LYSIS_RISK

    def test_trajectory_to_visual_frames(self):
        pts = [
            TrajectoryPoint(
                t_s=0.0,
                gsh_mM=2.5,
                gssg_mM=0.025,
                h2o2_mM=0.0001,
                nadph_mM=0.030,
                damage=0.0,
                hemolysis_pct=0.0,
                gsh_gssg_ratio=100.0,
            ),
            TrajectoryPoint(
                t_s=10.0,
                gsh_mM=0.20,
                gssg_mM=0.05,
                h2o2_mM=0.01,
                nadph_mM=0.01,
                damage=0.6,
                hemolysis_pct=45.0,
                gsh_gssg_ratio=4.0,
            ),
        ]
        frames = trajectory_to_visual_frames(pts, max_frames=10)
        assert len(frames) == 2
        assert frames[0].cell_state == CellVisualState.HEALTHY
        assert frames[1].cell_state == CellVisualState.LYSIS_RISK
        assert not frames[0].morphology_simulated

    def test_compute_scenario_metrics(self):
        pts = [
            TrajectoryPoint(
                t_s=0.0,
                gsh_mM=2.5,
                gssg_mM=0.025,
                h2o2_mM=0.0001,
                nadph_mM=0.030,
                damage=0.0,
                hemolysis_pct=0.0,
                gsh_gssg_ratio=100.0,
            ),
            TrajectoryPoint(
                t_s=60.0,
                gsh_mM=1.0,
                gssg_mM=0.10,
                h2o2_mM=0.001,
                nadph_mM=0.020,
                damage=0.02,
                hemolysis_pct=0.1,
                gsh_gssg_ratio=10.0,
            ),
            TrajectoryPoint(
                t_s=300.0,
                gsh_mM=2.3,
                gssg_mM=0.025,
                h2o2_mM=0.0001,
                nadph_mM=0.028,
                damage=0.02,
                hemolysis_pct=0.1,
                gsh_gssg_ratio=92.0,
            ),
        ]
        metrics = compute_scenario_metrics(pts)
        assert metrics.gsh_nadir_mM == 1.0
        assert metrics.gsh_nadir_time_s == 60.0
        assert metrics.gssg_peak_mM == 0.10
        assert metrics.damage_onset_time_s == 60.0  # first time D >= 0.01
        assert metrics.time_to_90pct_recovery_s == 300.0  # recovered to >= 2.25 mM
