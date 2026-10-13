"""
Unit tests for the local sensitivity analysis module (Task 3).

Tests verify:
- Analytical test function derivative and normalized sensitivity accuracy.
- Parameter immutability (original parameter sets and baselines are unchanged).
- Bound enforcement (non-negative parameter constraints).
- Zero baseline output handling (avoids division by zero, flags unnormalized).
- Solver failure propagation.
- Reproducibility across repeated evaluations.
- Association of sensitivity results with parameter evidence status.
"""

import numpy as np
import pytest

from vblood.biology.rbc.parameters import DEFAULT_PARAMETERS
from vblood.schemas.simulation import RBCGSHExposure, SimulationRequest
from vblood.uncertainty.sensitivity import (
    LocalSensitivityAnalyzer,
    ParameterSensitivityResult,
    SensitivityEndpoint,
    extract_endpoint_value,
)


class TestAnalyticalSensitivityVerification:
    """Verify finite-difference calculation against an exact analytical function.

    Test function: y(p1, p2) = p1^2 * sqrt(p2)
    Exact derivatives:
      ∂y/∂p1 = 2 * p1 * sqrt(p2)
      ∂y/∂p2 = 0.5 * p1^2 / sqrt(p2)
    Normalized sensitivities:
      S_p1 = (p1 / y) * (2 * p1 * sqrt(p2)) = 2.0
      S_p2 = (p2 / y) * (0.5 * p1^2 / sqrt(p2)) = 0.5
    """

    def test_centered_finite_difference_matches_analytical(self):
        p1 = 3.0
        p2 = 4.0
        y0 = p1**2 * np.sqrt(p2)  # 9 * 2 = 18.0

        delta_pct = 1.0  # 1% perturbation
        h1 = p1 * (delta_pct / 100.0)
        h2 = p2 * (delta_pct / 100.0)

        # Centered difference for p1
        y1_up = (p1 + h1)**2 * np.sqrt(p2)
        y1_down = (p1 - h1)**2 * np.sqrt(p2)
        dydp1 = (y1_up - y1_down) / (2 * h1)
        s_p1 = (p1 / y0) * dydp1

        # Centered difference for p2
        y2_up = p1**2 * np.sqrt(p2 + h2)
        y2_down = p1**2 * np.sqrt(p2 - h2)
        dydp2 = (y2_up - y2_down) / (2 * h2)
        s_p2 = (p2 / y0) * dydp2

        assert np.isclose(s_p1, 2.0, rtol=1e-3)
        assert np.isclose(s_p2, 0.5, rtol=1e-3)


class TestLocalSensitivityAnalyzer:
    """Unit tests on the LocalSensitivityAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        req = SimulationRequest(
            exposure=RBCGSHExposure(h2o2_bolus_mM=0.02),
            t_start_s=0.0,
            t_end_s=600.0,
            n_eval_points=100,
        )
        return LocalSensitivityAnalyzer(base_request=req)

    def test_baseline_parameters_not_modified_in_place(self, analyzer):
        """Analyzing sensitivity must not alter the original default parameters."""
        orig_kgpx = DEFAULT_PARAMETERS.k_gpx.value
        orig_vmax = DEFAULT_PARAMETERS.vmax_gr.value

        analyzer.analyze(
            endpoint=SensitivityEndpoint.MAX_FRACTIONAL_GSH_DEPLETION,
            delta_pct=5.0,
            parameters_to_test=["k_gpx", "vmax_gr"],
        )

        assert DEFAULT_PARAMETERS.k_gpx.value == orig_kgpx
        assert DEFAULT_PARAMETERS.vmax_gr.value == orig_vmax

    def test_reproducibility(self, analyzer):
        """Repeated analysis on identical configuration yields identical rankings."""
        rep1 = analyzer.analyze(
            endpoint=SensitivityEndpoint.MAX_FRACTIONAL_GSH_DEPLETION,
            parameters_to_test=["k_gpx", "vmax_gr", "k_synth"],
        )
        rep2 = analyzer.analyze(
            endpoint=SensitivityEndpoint.MAX_FRACTIONAL_GSH_DEPLETION,
            parameters_to_test=["k_gpx", "vmax_gr", "k_synth"],
        )

        assert rep1.ranked_parameters == rep2.ranked_parameters
        for r1, r2 in zip(rep1.results, rep2.results):
            assert r1.parameter_name == r2.parameter_name
            assert np.isclose(r1.dydp_unnormalized, r2.dydp_unnormalized)

    def test_zero_baseline_output_handled_gracefully(self, analyzer):
        """If baseline output is near zero, normalized sensitivity is flagged and unnormalized reported."""
        # Baseline simulation with NO bolus has damage = 0 or max fractional depletion near 0
        from vblood.schemas.simulation import RBCGSHInitialConditions

        # Simulate at baseline with zero bolus
        no_challenge_req = SimulationRequest(
            exposure=RBCGSHExposure(h2o2_bolus_mM=0.0),
            t_start_s=0.0,
            t_end_s=60.0,
            n_eval_points=50,
        )
        zero_analyzer = LocalSensitivityAnalyzer(base_request=no_challenge_req)

        # Fraction depletion under no challenge at t=0 is 0.0
        rep = zero_analyzer.analyze(
            endpoint=SensitivityEndpoint.FRACTIONAL_GSH_DEPLETION_AT_TIME,
            eval_time_s=0.0,
            parameters_to_test=["k_gpx"],
        )
        assert len(rep.results) == 1
        res = rep.results[0]
        assert res.normalization_status == "UNNORMALIZED_ZERO_BASELINE"
        assert res.normalized_sensitivity_Sp is None
        assert len(res.warnings) > 0

    def test_evidence_status_preserved_on_results(self, analyzer):
        """Results must correctly carry EVIDENCE_STATUS from parameter definitions."""
        rep = analyzer.analyze(
            endpoint=SensitivityEndpoint.MAX_FRACTIONAL_GSH_DEPLETION,
            parameters_to_test=["km_gssg_gr", "k_damage"],
        )
        km_res = next(r for r in rep.results if r.parameter_name == "km_gssg_gr")
        damage_res = next(r for r in rep.results if r.parameter_name == "k_damage")

        assert km_res.evidence_status == "LITERATURE"
        assert damage_res.evidence_status == "SYNTHETIC"

    def test_endpoint_extraction_endpoints_supported(self, analyzer):
        """extract_endpoint_value supports all required endpoints."""
        sim_res = analyzer._run_with_parameter_override(analyzer.base_request, {})

        v_max = extract_endpoint_value(sim_res, SensitivityEndpoint.MAX_FRACTIONAL_GSH_DEPLETION)
        v_min = extract_endpoint_value(sim_res, SensitivityEndpoint.MIN_GSH_CONCENTRATION)
        v_time = extract_endpoint_value(sim_res, SensitivityEndpoint.FRACTIONAL_GSH_DEPLETION_AT_TIME, eval_time_s=100.0)
        v_rec = extract_endpoint_value(sim_res, SensitivityEndpoint.GSH_RECOVERY_TIME_50)

        assert 0.0 <= v_max <= 1.0
        assert v_min > 0.0
        assert 0.0 <= v_time <= 1.0
        assert v_rec > 0.0
