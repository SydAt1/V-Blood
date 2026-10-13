"""
Unit tests for L2 validation data ingestion and validation reporting (Task 2).

Tests cover:
- L2 reference dataset integrity and provenance.
- Validation logic on physiological resting states (PASS).
- Validation failure criteria detection (FAIL).
- Assessment of the current model's mathematical steady state against L2 targets.
"""

import pytest

from vblood.schemas.simulation import RBCGSHInitialConditions, SimulationRequest
from vblood.simulation.engine import run_simulation
from vblood.simulation.steady_state import compute_steady_state
from vblood.validation.l2_validator import EvaluationStatus, L2Validator, validate_l2
from vblood.validation.reference_data import (
    EvidenceStatus,
    PhysiologicalReference,
    get_l2_references,
)


class TestL2ReferenceDataIngestion:
    """Checks on the curated L2 physiological reference ranges."""

    def test_all_core_variables_present(self):
        refs = get_l2_references()
        expected_vars = {"GSH", "GSSG", "GSH_GSSG_RATIO", "H2O2", "NADPH"}
        assert expected_vars.issubset(set(refs.keys()))

    def test_all_references_have_literature_sources(self):
        refs = get_l2_references()
        for var, ref in refs.items():
            assert ref.literature_source != "", f"Missing source for {var}"
            assert ref.units != "", f"Missing units for {var}"
            assert ref.reference_min < ref.reference_max
            assert ref.tolerance_min <= ref.reference_min
            assert ref.tolerance_max >= ref.reference_max

    def test_evidence_status_is_literature_derived(self):
        refs = get_l2_references()
        for var, ref in refs.items():
            assert ref.evidence_status == EvidenceStatus.LITERATURE_DERIVED


class TestL2ValidationLogic:
    """Checks on L2Validator pass/fail evaluation."""

    @pytest.fixture
    def validator(self):
        return L2Validator()

    def test_physiological_state_passes_optimal(self, validator):
        """A normal healthy human erythrocyte state passes optimal L2 validation."""
        normal_state = {
            "GSH": 2.2,
            "GSSG": 0.025,
            "GSH_GSSG_RATIO": 88.0,
            "H2O2": 0.0001,
            "NADPH": 0.030,
        }
        report = validator.evaluate_state(normal_state)
        assert report.is_overall_pass is True
        assert report.is_optimal_pass is True
        assert report.n_failed == 0
        for ev in report.evaluations:
            assert ev.status == EvaluationStatus.PASS_OPTIMAL

    def test_severe_gsh_depletion_fails_l2(self, validator):
        """[GSH] < 0.5 mM must fail L2 validation."""
        depleted_state = {
            "GSH": 0.1,  # below tolerance 0.5 mM
            "GSSG": 0.02,
            "H2O2": 0.0001,
            "NADPH": 0.03,
        }
        report = validator.evaluate_state(depleted_state)
        assert report.is_overall_pass is False
        assert report.n_failed >= 1
        gsh_eval = next(e for e in report.evaluations if e.variable == "GSH")
        assert gsh_eval.status == EvaluationStatus.FAIL_LOW
        assert gsh_eval.is_pass is False

    def test_low_ratio_fails_l2(self, validator):
        """GSH/GSSG ratio < 5 must fail L2 validation."""
        stressed_state = {
            "GSH": 1.5,
            "GSSG": 0.5,  # ratio = 3 < 5
            "H2O2": 0.0001,
            "NADPH": 0.03,
        }
        report = validator.evaluate_state(stressed_state)
        assert report.is_overall_pass is False
        ratio_eval = next(e for e in report.evaluations if e.variable == "GSH_GSSG_RATIO")
        assert ratio_eval.status == EvaluationStatus.FAIL_LOW

    def test_excessive_h2o2_fails_l2(self, validator):
        """[H2O2] > 0.010 mM must fail L2 validation."""
        high_peroxide = {
            "GSH": 2.0,
            "GSSG": 0.02,
            "H2O2": 0.05,  # 50 µM > 10 µM
            "NADPH": 0.03,
        }
        report = validator.evaluate_state(high_peroxide)
        assert report.is_overall_pass is False
        h2o2_eval = next(e for e in report.evaluations if e.variable == "H2O2")
        assert h2o2_eval.status == EvaluationStatus.FAIL_HIGH


class TestCurrentModelL2Validation:
    """Scientific evaluation of the current model against L2 reference data."""

    def test_model_mathematical_steady_state_fails_l2_with_documented_diagnostics(self):
        """Current model's mathematical steady state is known to fail L2 validation.

        This test verifies that the failure is accurately detected, documented,
        and not masked or silently bypassed.
        """
        ss_res = compute_steady_state()
        report = validate_l2(ss_res)

        # As documented in docs/steady_state_analysis.md:
        # [GSH]* = ~0.002 mM (< 0.5 mM tolerance) -> FAIL_LOW
        # [NADPH]* = ~9.0 mM (> 0.2 mM tolerance) -> FAIL_HIGH
        assert report.is_overall_pass is False
        assert len(report.failure_reasons) > 0

        gsh_eval = next(e for e in report.evaluations if e.variable == "GSH")
        assert gsh_eval.status == EvaluationStatus.FAIL_LOW

        nadph_eval = next(e for e in report.evaluations if e.variable == "NADPH")
        assert nadph_eval.status == EvaluationStatus.FAIL_HIGH

    def test_initial_physiological_state_passes_l2(self):
        """Initial physiological state before drift satisfies all L2 failure criteria."""
        ic = RBCGSHInitialConditions()
        init_state = {
            "GSH": ic.gsh_0,
            "GSSG": ic.gssg_0,
            "H2O2": ic.h2o2_0,
            "NADPH": ic.nadph_0,
        }
        report = validate_l2(init_state)
        assert report.is_overall_pass is True

    def test_drifted_baseline_simulation_diagnoses_l2_failure(self):
        """As the model drifts toward its unphysiological steady state, L2 failure is diagnosed."""
        req = SimulationRequest(
            initial_conditions=RBCGSHInitialConditions(gsh_0=2.5, gssg_0=0.025, nadph_0=0.030),
            t_end_s=60.0,
            n_eval_points=50,
        )
        sim_res = run_simulation(req)
        report = validate_l2(sim_res)
        # In the uncalibrated model, rapid GPx clearance drives H2O2 below 1e-5 mM within seconds
        assert report.is_overall_pass is False
        assert any("H2O2" in reason for reason in report.failure_reasons)
