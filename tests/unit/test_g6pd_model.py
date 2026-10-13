"""
Unit and regression tests for the G6PD kinetic sub-model (Task 6).

Verifies:
- Rate law behavior (G6PDRateLaw): monotonicity, Michaelis-Menten kinetics,
  competitive product inhibition by NADPH, zero activity fraction.
- Parameter bounds and validation.
- Absence of double-counted NADPH production.
- Model registry integration and simulation execution.
- G6PD deficiency scenarios (reduced alpha decreases minimum NADPH).
- Baseline model (rbc-gsh-redox-v1) preservation and independence.
"""

from __future__ import annotations

import pytest
import numpy as np

from vblood.biology.rbc.g6pd_model import G6PDRateLaw, RBCG6PDGSHModel
from vblood.biology.rbc.g6pd_parameters import DEFAULT_G6PD_PARAMETERS, G6PDParameters
from vblood.biology.rbc.gsh_redox_model import RBCGSHRedoxModel
from vblood.schemas.simulation import (
    RBCGSHExposure,
    RBCGSHInitialConditions,
    SimulationRequest,
    SolverStatus,
)
from vblood.simulation.engine import _MODEL_REGISTRY, run_simulation


class TestG6PDRateLaw:
    """Tests for the isolated G6PDRateLaw component."""

    def test_zero_activity_fraction_yields_zero_flux(self) -> None:
        v = G6PDRateLaw.v_g6pd(
            nadph=0.02,
            vmax_g6pd=0.008,
            km_g6p=0.040,
            km_nadp=0.008,
            ki_nadph=0.012,
            nadp_total=0.040,
            g6p_conc=0.040,
            activity_fraction=0.0,
        )
        assert v == 0.0

    def test_zero_vmax_yields_zero_flux(self) -> None:
        v = G6PDRateLaw.v_g6pd(
            nadph=0.02,
            vmax_g6pd=0.0,
            km_g6p=0.040,
            km_nadp=0.008,
            ki_nadph=0.012,
            nadp_total=0.040,
            g6p_conc=0.040,
            activity_fraction=1.0,
        )
        assert v == 0.0

    def test_zero_g6p_yields_zero_flux(self) -> None:
        v = G6PDRateLaw.v_g6pd(
            nadph=0.02,
            vmax_g6pd=0.008,
            km_g6p=0.040,
            km_nadp=0.008,
            ki_nadph=0.012,
            nadp_total=0.040,
            g6p_conc=0.0,
            activity_fraction=1.0,
        )
        assert v == 0.0

    def test_full_nadph_exhausts_nadp_yields_zero_flux(self) -> None:
        # If [NADPH] == [NADP]_tot, then [NADP+] = 0 -> zero flux
        v = G6PDRateLaw.v_g6pd(
            nadph=0.040,
            vmax_g6pd=0.008,
            km_g6p=0.040,
            km_nadp=0.008,
            ki_nadph=0.012,
            nadp_total=0.040,
            g6p_conc=0.040,
            activity_fraction=1.0,
        )
        assert v == 0.0

    def test_linear_scaling_with_activity_fraction(self) -> None:
        v_full = G6PDRateLaw.v_g6pd(
            nadph=0.02,
            vmax_g6pd=0.008,
            km_g6p=0.040,
            km_nadp=0.008,
            ki_nadph=0.012,
            nadp_total=0.040,
            g6p_conc=0.040,
            activity_fraction=1.0,
        )
        v_half = G6PDRateLaw.v_g6pd(
            nadph=0.02,
            vmax_g6pd=0.008,
            km_g6p=0.040,
            km_nadp=0.008,
            ki_nadph=0.012,
            nadp_total=0.040,
            g6p_conc=0.040,
            activity_fraction=0.5,
        )
        assert np.isclose(v_half, 0.5 * v_full)

    def test_competitive_inhibition_by_nadph(self) -> None:
        # With fixed [NADP+] = 0.01 mM (achieved by keeping nadp_total - nadph = 0.01),
        # higher [NADPH] increases inhibition and reduces flux.
        # Case A: nadph = 0.01, nadp_total = 0.02 (nadp+ = 0.01)
        v_low_nadph = G6PDRateLaw.v_g6pd(
            nadph=0.01,
            vmax_g6pd=0.008,
            km_g6p=0.040,
            km_nadp=0.008,
            ki_nadph=0.012,
            nadp_total=0.02,
            g6p_conc=0.040,
            activity_fraction=1.0,
        )
        # Case B: nadph = 0.03, nadp_total = 0.04 (nadp+ = 0.01)
        v_high_nadph = G6PDRateLaw.v_g6pd(
            nadph=0.03,
            vmax_g6pd=0.008,
            km_g6p=0.040,
            km_nadp=0.008,
            ki_nadph=0.012,
            nadp_total=0.04,
            g6p_conc=0.040,
            activity_fraction=1.0,
        )
        assert v_low_nadph > v_high_nadph


class TestRBCG6PDGSHModel:
    """Tests for the complete RBCG6PDGSHModel ODE implementation."""

    def test_model_registered_in_engine(self) -> None:
        assert "rbc-g6pd-gsh-v2" in _MODEL_REGISTRY
        assert isinstance(_MODEL_REGISTRY["rbc-g6pd-gsh-v2"], RBCG6PDGSHModel)

    def test_metadata_completeness(self) -> None:
        model = RBCG6PDGSHModel()
        meta = model.metadata
        assert meta.model_id == "rbc-g6pd-gsh-v2"
        assert meta.version == "2.0.0"
        assert "G6PD" in meta.name
        assert meta.state_variable_names == ("GSH", "GSSG", "H2O2", "NADPH", "D")
        assert len(meta.literature_sources) >= 4

    def test_validate_params_checks_bounds(self) -> None:
        model = RBCG6PDGSHModel()
        params = model.default_parameters()
        assert model.validate_params(params) == []

        # Negative vmax_g6pd
        bad_params = params.copy()
        bad_params["vmax_g6pd"] = -0.01
        errors = model.validate_params(bad_params)
        assert any("vmax_g6pd" in e for e in errors)

        # Invalid activity fraction
        bad_alpha = params.copy()
        bad_alpha["g6pd_activity_fraction"] = 10.0
        errors = model.validate_params(bad_alpha)
        assert any("g6pd_activity_fraction" in e for e in errors)

    def test_no_double_counted_nadph_flux(self) -> None:
        """Verify that dy/dt[NADPH] equals r_g6pd - r_gr without any v_ppp term."""
        model = RBCG6PDGSHModel()
        params = model.default_parameters()
        y = np.array([2.5, 0.025, 0.0001, 0.035, 0.0])
        dy_dt = model.rhs(0.0, y, params)

        r_g6pd = G6PDRateLaw.v_g6pd(
            nadph=y[3],
            vmax_g6pd=params["vmax_g6pd"],
            km_g6p=params["km_g6p"],
            km_nadp=params["km_nadp"],
            ki_nadph=params["ki_nadph"],
            nadp_total=params["nadp_total"],
            g6p_conc=params["g6p_conc"],
            activity_fraction=params["g6pd_activity_fraction"],
        )
        r_gr = RBCGSHRedoxModel.v_gr(
            gssg=y[1],
            nadph=y[3],
            vmax_gr=params["vmax_gr"],
            km_gssg=params["km_gssg_gr"],
            km_nadph=params["km_nadph_gr"],
        )

        expected_dnadph_dt = r_g6pd - r_gr
        assert np.isclose(dy_dt[3], expected_dnadph_dt)

    def test_simulation_runs_successfully(self) -> None:
        ic = RBCGSHInitialConditions(
            gsh_0=2.5,
            gssg_0=0.025,
            h2o2_0=0.0001,
            nadph_0=0.035,
            damage_0=0.0,
        )
        req = SimulationRequest(
            model_id="rbc-g6pd-gsh-v2",
            initial_conditions=ic,
            exposure=RBCGSHExposure(h2o2_bolus_mM=0.02),
            t_start_s=0.0,
            t_end_s=600.0,
            n_eval_points=100,
        )
        res = run_simulation(req)
        assert res.solver_status == SolverStatus.SUCCESS
        assert len(res.trajectory) == 100
        assert res.min_gsh_mM <= 2.5
        assert res.min_gsh_mM > 0.0

    def test_reduced_g6pd_activity_worsens_nadph_depletion(self) -> None:
        """Confirm that reduced G6PD activity (alpha = 0.1) results in lower minimum NADPH."""
        ic = RBCGSHInitialConditions(
            gsh_0=2.5,
            gssg_0=0.025,
            h2o2_0=0.0001,
            nadph_0=0.035,
            damage_0=0.0,
        )
        req_normal = SimulationRequest(
            model_id="rbc-g6pd-gsh-v2",
            initial_conditions=ic,
            parameter_overrides={"g6pd_activity_fraction": 1.0},
            exposure=RBCGSHExposure(h2o2_bolus_mM=0.05),
            t_start_s=0.0,
            t_end_s=600.0,
            n_eval_points=100,
        )
        res_normal = run_simulation(req_normal)
        min_nadph_normal = min(pt.nadph_mM for pt in res_normal.trajectory)

        req_deficient = SimulationRequest(
            model_id="rbc-g6pd-gsh-v2",
            initial_conditions=ic,
            parameter_overrides={"g6pd_activity_fraction": 0.1},
            exposure=RBCGSHExposure(h2o2_bolus_mM=0.05),
            t_start_s=0.0,
            t_end_s=600.0,
            n_eval_points=100,
        )
        res_deficient = run_simulation(req_deficient)
        min_nadph_deficient = min(pt.nadph_mM for pt in res_deficient.trajectory)

        assert min_nadph_deficient < min_nadph_normal

    def test_milestone_1_baseline_model_remains_intact(self) -> None:
        """Confirm that rbc-gsh-redox-v1 is unaffected by the addition of rbc-g6pd-gsh-v2."""
        assert "rbc-gsh-redox-v1" in _MODEL_REGISTRY
        v1_model = _MODEL_REGISTRY["rbc-gsh-redox-v1"]
        assert isinstance(v1_model, RBCGSHRedoxModel)
        assert v1_model.metadata.model_id == "rbc-gsh-redox-v1"
        assert v1_model.metadata.version == "1.0.0"
