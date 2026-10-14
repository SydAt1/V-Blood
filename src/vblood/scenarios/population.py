"""
Vectorized Population-Scale Erythrocyte Simulation (Milestone 4 - Task 4).

Simulates cohorts of red blood cells (e.g. N = 1000 cells) subject to
biological parameter variability (priors), computing population-level
percentiles, crisis fractions, and hemolysis vulnerability in seconds.
"""

from __future__ import annotations

import time
from typing import Any
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from vblood.biology.rbc.g6pd_parameters import DEFAULT_G6PD_PARAMETERS
from vblood.biology.rbc.parameters import DEFAULT_PARAMETERS
from vblood.scenarios.compounds import get_compound_library
from vblood.scenarios.engine import (
    ExposureProfile,
    ScenarioRequest,
    build_mechanism_specs,
)
from vblood.scenarios.mechanisms import (
    DirectOxidantSpec,
    EnzymeInhibitorSpec,
    EnzymeTarget,
    GSHConjugatorSpec,
    InhibitionType,
    NADPHDrainSpec,
    RedoxCyclerSpec,
)


class PopulationRequest(BaseModel):
    """Input specification for a population cohort simulation."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "scenario_request": {
                    "model_version": "rbc-g6pd-gsh-v2",
                    "g6pd_alpha": 0.2,
                    "duration_s": 1800.0,
                    "exposure_profile": "BOLUS",
                    "compounds": [
                        {
                            "compound_id": "cmp_menadione",
                            "dose_mM": 0.03,
                        }
                    ],
                },
                "n_cells": 1000,
                "random_seed": 42,
            }
        },
    )

    scenario_request: ScenarioRequest
    n_cells: int = Field(default=1000, ge=10, le=5000, description="Number of individual cells to simulate.")
    random_seed: int | None = Field(default=42, description="RNG seed for exact reproducibility.")
    gsh_mild_threshold_mM: float = Field(default=1.0, ge=0.0, description="Threshold for moderate GSH depletion.")
    gsh_crisis_threshold_mM: float = Field(default=0.25, ge=0.0, description="Threshold for severe crisis (<10% baseline).")
    hemolysis_proxy_threshold_pct: float = Field(default=5.0, ge=0.0, description="Threshold for cell lysis risk.")


class PopulationPercentileBands(BaseModel):
    """Percentile trajectory bands across the simulated cell cohort."""

    model_config = ConfigDict(frozen=True)

    time_points_s: list[float]
    gsh_p5: list[float]
    gsh_p25: list[float]
    gsh_p50: list[float]
    gsh_p75: list[float]
    gsh_p95: list[float]

    nadph_p5: list[float]
    nadph_p50: list[float]
    nadph_p95: list[float]

    damage_p50: list[float]
    damage_p95: list[float]

    hemolysis_p50: list[float]
    hemolysis_p95: list[float]


class PopulationResult(BaseModel):
    """Aggregated population-level simulation result."""

    model_config = ConfigDict(frozen=True)

    n_cells: int
    execution_time_s: float = Field(description="Wall-clock time for batch simulation.")
    pct_cells_below_mild_gsh: float = Field(description="% of cells with minimum GSH below mild threshold.")
    pct_cells_below_crisis_gsh: float = Field(description="% of cells with minimum GSH below crisis threshold.")
    pct_cells_lysis_risk: float = Field(description="% of cells with maximum hemolysis proxy above threshold.")
    mean_gsh_nadir_mM: float
    median_gsh_nadir_mM: float
    percentile_bands: PopulationPercentileBands
    has_unverified_compounds: bool
    unverified_compounds: list[str]
    disclaimer: str = Field(
        default="RESEARCH USE ONLY: Cohort distributions represent mathematical parameter sampling, not clinical patient data."
    )


def sample_population_parameters(
    n_cells: int,
    g6pd_alpha: float = 1.0,
    rng: np.random.Generator | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Sample initial states and parameters for N individual red blood cells from biological priors.

    Returns:
        (Y0: shape (N, 5), params: dict of param_name -> np.ndarray shape (N,))
    """
    if rng is None:
        rng = np.random.default_rng(42)

    # 1. Initial conditions sampling
    # GSH: Normal(2.5, 0.28) bounded [1.5, 3.2]
    gsh_0 = np.clip(rng.normal(2.50, 0.25, size=n_cells), 1.5, 3.5)
    # GSSG: LogNormal around 0.025 bounded [0.010, 0.045]
    gssg_0 = np.clip(rng.normal(0.025, 0.005, size=n_cells), 0.010, 0.045)
    # H2O2: 0.0001 mM
    h2o2_0 = np.full(n_cells, 0.0001)
    # NADPH: Normal(0.030, 0.004) bounded [0.015, 0.040]
    nadph_0 = np.clip(rng.normal(0.030, 0.003, size=n_cells), 0.015, 0.039)
    # Damage: 0.0
    d_0 = np.zeros(n_cells)

    y0 = np.column_stack([gsh_0, gssg_0, h2o2_0, nadph_0, d_0])

    # 2. Kinetic parameters sampling (log-normal from uncertainty factors)
    base_p = DEFAULT_PARAMETERS.to_dict()
    g6pd_p = DEFAULT_G6PD_PARAMETERS.to_dict()

    params: dict[str, np.ndarray] = {
        "k_gpx": rng.lognormal(np.log(base_p["k_gpx"]), 0.20, size=n_cells),
        "vmax_gr": rng.lognormal(np.log(base_p["vmax_gr"]), 0.15, size=n_cells),
        "km_gssg_gr": np.full(n_cells, base_p["km_gssg_gr"]),
        "km_nadph_gr": np.full(n_cells, base_p["km_nadph_gr"]),
        "k_export": rng.lognormal(np.log(base_p["k_export"]), 0.25, size=n_cells),
        "k_synth": rng.lognormal(np.log(base_p["k_synth"]), 0.15, size=n_cells),
        "k_h2o2_prod": np.full(n_cells, base_p["k_h2o2_prod"]),
        "k_h2o2_rem": np.full(n_cells, base_p["k_h2o2_rem"]),
        "vmax_g6pd": rng.lognormal(np.log(g6pd_p["vmax_g6pd"]), 0.15, size=n_cells) * g6pd_alpha,
        "km_g6p": np.full(n_cells, g6pd_p["km_g6p"]),
        "km_nadp": np.full(n_cells, g6pd_p["km_nadp"]),
        "ki_nadph": np.full(n_cells, g6pd_p["ki_nadph"]),
        "nadp_total": np.full(n_cells, g6pd_p["nadp_total"]),
        "g6p_conc": np.full(n_cells, g6pd_p["g6p_conc"]),
        "k_damage": np.full(n_cells, base_p["k_damage"]),
        "k_repair": np.full(n_cells, base_p["k_repair"]),
        "gsh_0_ref": gsh_0.copy(),
    }

    return y0, params


def simulate_population(request: PopulationRequest) -> PopulationResult:
    """Execute high-speed vectorized cohort simulation of N cells.

    Achieves sub-second execution for N = 1000 cells using vectorized RK4.
    """
    start_time = time.perf_counter()
    n_cells = request.n_cells
    rng = np.random.default_rng(request.random_seed)

    y0, p = sample_population_parameters(
        n_cells=n_cells,
        g6pd_alpha=request.scenario_request.g6pd_alpha,
        rng=rng,
    )

    # Build mechanism specs
    specs, unverified, _ = build_mechanism_specs(request.scenario_request)

    # Apply static enzyme inhibition if present
    for spec in specs:
        if isinstance(spec, EnzymeInhibitorSpec) and spec.compound_conc_mM > 0.0:
            factor = 1.0 + (spec.compound_conc_mM / spec.ki_mM)
            if spec.target_enzyme == EnzymeTarget.G6PD:
                if spec.inhibition_type == InhibitionType.COMPETITIVE:
                    p["km_nadp"] *= factor
                else:
                    p["vmax_g6pd"] /= factor
            elif spec.target_enzyme == EnzymeTarget.GR:
                if spec.inhibition_type == InhibitionType.COMPETITIVE:
                    p["km_gssg_gr"] *= factor
                else:
                    p["vmax_gr"] /= factor

    # Initial bolus
    for spec in specs:
        if isinstance(spec, DirectOxidantSpec) and spec.bolus_mM > 0.0:
            y0[:, 2] += spec.bolus_mM

    # Time grid: 200 evaluation points
    duration = request.scenario_request.duration_s
    t_eval = np.linspace(0.0, duration, 201)
    dt = duration / 200.0

    # Vectorized state trajectory: shape (n_time, n_cells, 5)
    trajectory = np.zeros((len(t_eval), n_cells, 5))
    trajectory[0] = y0

    state = y0.copy()

    # Vectorized ODE RHS function
    def rhs_vector(t: float, y: np.ndarray) -> np.ndarray:
        gsh = np.maximum(0.0, y[:, 0])
        gssg = np.maximum(0.0, y[:, 1])
        h2o2 = np.maximum(0.0, y[:, 2])
        nadph = np.maximum(0.0, y[:, 3])
        d = np.clip(y[:, 4], 0.0, 1.0)

        # 1. GPx
        r_gpx = p["k_gpx"] * h2o2 * gsh

        # 2. GR
        sat_gssg = gssg / (p["km_gssg_gr"] + gssg + 1e-12)
        sat_nadph = nadph / (p["km_nadph_gr"] + nadph + 1e-12)
        r_gr = p["vmax_gr"] * sat_gssg * sat_nadph

        # 3. Export & Synth
        r_export = p["k_export"] * gssg
        r_synth = p["k_synth"]

        # 4. G6PD flux
        nadp_plus = np.maximum(0.0, p["nadp_total"] - nadph)
        g6p = p["g6p_conc"]
        inhibition = 1.0 + (nadph / p["ki_nadph"])
        num = p["vmax_g6pd"] * g6p * nadp_plus
        den = (
            p["km_g6p"] * p["km_nadp"] * inhibition
            + p["km_nadp"] * g6p
            + p["km_g6p"] * nadp_plus
            + g6p * nadp_plus
        )
        r_g6pd = np.where(den > 0.0, num / den, 0.0)

        # 5. Endogenous H2O2 & passive removal
        r_prod = p["k_h2o2_prod"]
        r_rem = p["k_h2o2_rem"] * h2o2

        # 6. Scenario rate additions
        v_oxidant_influx = 0.0
        v_gsh_conjugation = 0.0
        v_redox_cycle = 0.0
        v_nadph_drain = 0.0

        for s in specs:
            if isinstance(s, DirectOxidantSpec):
                if s.start_time_s <= t <= (s.start_time_s + s.duration_s):
                    v_oxidant_influx += s.influx_rate_mM_s
            elif isinstance(s, GSHConjugatorSpec):
                v_gsh_conjugation += s.rate_constant_mM_s * s.compound_conc_mM * gsh
            elif isinstance(s, RedoxCyclerSpec):
                sat_c = nadph / (s.km_nadph_mM + nadph + 1e-12)
                v_redox_cycle += s.catalytic_rate_s * s.compound_conc_mM * sat_c
            elif isinstance(s, NADPHDrainSpec):
                sat_d = nadph / (s.km_nadph_mM + nadph + 1e-12)
                v_nadph_drain += s.drain_rate_s * s.compound_conc_mM * sat_d

        # Derivatives
        dgsh = 2.0 * r_gr - 2.0 * r_gpx + r_synth - v_gsh_conjugation
        dgssg = r_gpx - r_gr - r_export
        dh2o2 = r_prod - r_gpx - r_rem + v_oxidant_influx + v_redox_cycle
        dnadph = r_g6pd - r_gr - v_redox_cycle - v_nadph_drain

        # Damage
        gsh_dep = np.maximum(0.0, 1.0 - gsh / p["gsh_0_ref"])
        dd = p["k_damage"] * h2o2 * gsh_dep - p["k_repair"] * d * (1.0 - d)

        # Clamp D boundary derivatives
        dd = np.where((d >= 1.0) & (dd > 0.0), 0.0, dd)
        dd = np.where((d <= 0.0) & (dd < 0.0), 0.0, dd)

        return np.column_stack([dgsh, dgssg, dh2o2, dnadph, dd])

    # Run vectorized RK4 steps
    for step in range(len(t_eval) - 1):
        t_curr = t_eval[step]
        k1 = rhs_vector(t_curr, state)
        k2 = rhs_vector(t_curr + 0.5 * dt, state + 0.5 * dt * k1)
        k3 = rhs_vector(t_curr + 0.5 * dt, state + 0.5 * dt * k2)
        k4 = rhs_vector(t_curr + dt, state + dt * k3)

        state = state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

        # Enforce physical positivity and bounds
        state[:, 0] = np.maximum(0.0, state[:, 0])
        state[:, 1] = np.maximum(0.0, state[:, 1])
        state[:, 2] = np.maximum(0.0, state[:, 2])
        state[:, 3] = np.maximum(0.0, state[:, 3])
        state[:, 4] = np.clip(state[:, 4], 0.0, 1.0)

        trajectory[step + 1] = state

    exec_time = time.perf_counter() - start_time

    # Compute population statistics across trajectory
    # trajectory shape: (n_time, n_cells, 5)
    gsh_all = trajectory[:, :, 0]
    nadph_all = trajectory[:, :, 3]
    damage_all = trajectory[:, :, 4]

    # Hemolysis proxy: Hill function H(D) = 100 * D^4 / (0.4^4 + D^4)
    hemolysis_all = 100.0 * (damage_all**4) / (0.4**4 + damage_all**4)

    # Cohort minimum GSH per cell
    min_gsh_per_cell = np.min(gsh_all, axis=0)
    max_hemolysis_per_cell = np.max(hemolysis_all, axis=0)

    pct_mild = float(np.mean(min_gsh_per_cell < request.gsh_mild_threshold_mM) * 100.0)
    pct_crisis = float(np.mean(min_gsh_per_cell < request.gsh_crisis_threshold_mM) * 100.0)
    pct_lysis = float(np.mean(max_hemolysis_per_cell > request.hemolysis_proxy_threshold_pct) * 100.0)

    # Percentiles over time
    bands = PopulationPercentileBands(
        time_points_s=t_eval.tolist(),
        gsh_p5=np.percentile(gsh_all, 5, axis=1).tolist(),
        gsh_p25=np.percentile(gsh_all, 25, axis=1).tolist(),
        gsh_p50=np.percentile(gsh_all, 50, axis=1).tolist(),
        gsh_p75=np.percentile(gsh_all, 75, axis=1).tolist(),
        gsh_p95=np.percentile(gsh_all, 95, axis=1).tolist(),
        nadph_p5=np.percentile(nadph_all, 5, axis=1).tolist(),
        nadph_p50=np.percentile(nadph_all, 50, axis=1).tolist(),
        nadph_p95=np.percentile(nadph_all, 95, axis=1).tolist(),
        damage_p50=np.percentile(damage_all, 50, axis=1).tolist(),
        damage_p95=np.percentile(damage_all, 95, axis=1).tolist(),
        hemolysis_p50=np.percentile(hemolysis_all, 50, axis=1).tolist(),
        hemolysis_p95=np.percentile(hemolysis_all, 95, axis=1).tolist(),
    )

    return PopulationResult(
        n_cells=n_cells,
        execution_time_s=round(exec_time, 4),
        pct_cells_below_mild_gsh=round(pct_mild, 2),
        pct_cells_below_crisis_gsh=round(pct_crisis, 2),
        pct_cells_lysis_risk=round(pct_lysis, 2),
        mean_gsh_nadir_mM=float(np.mean(min_gsh_per_cell)),
        median_gsh_nadir_mM=float(np.median(min_gsh_per_cell)),
        percentile_bands=bands,
        has_unverified_compounds=len(unverified) > 0,
        unverified_compounds=unverified,
    )
