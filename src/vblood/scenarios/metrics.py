"""
Derived trajectory metrics for redox simulation endpoints (Milestone 3 & 4).

Computes:
- GSH nadir (minimum concentration and time)
- GSSG peak (maximum concentration and time)
- Time to 90% GSH recovery
- Net total glutathione loss percentage
- Damage onset time (first time D >= 0.01)
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from vblood.schemas.simulation import TrajectoryPoint


class ScenarioDerivedMetrics(BaseModel):
    """Derived biochemical and pathological metrics computed from a simulation trajectory."""

    model_config = ConfigDict(frozen=True)

    gsh_nadir_mM: float = Field(description="Minimum [GSH] observed during the simulation.")
    gsh_nadir_time_s: float = Field(description="Time at which GSH nadir occurred.")
    gssg_peak_mM: float = Field(description="Maximum [GSSG] observed during the simulation.")
    gssg_peak_time_s: float = Field(description="Time at which GSSG peak occurred.")
    time_to_90pct_recovery_s: float | None = Field(
        default=None,
        description="Time in seconds to recover to >= 90% of initial GSH. None if recovery not achieved.",
    )
    net_total_glutathione_loss_pct: float = Field(
        description="Percentage loss of total glutathione pool (GSH + 2*GSSG) from t=0 to t_final.",
    )
    damage_onset_time_s: float | None = Field(
        default=None,
        description="Time at which damage index D first reaches or exceeds 0.01. None if D < 0.01 throughout.",
    )
    nadph_nadir_mM: float = Field(description="Minimum [NADPH] observed during the simulation.")
    max_h2o2_mM: float = Field(description="Maximum [H2O2] observed during the simulation.")


def compute_scenario_metrics(trajectory: list[TrajectoryPoint]) -> ScenarioDerivedMetrics:
    """Compute derived biochemical metrics from a trajectory.

    Args:
        trajectory: List of TrajectoryPoint records.

    Returns:
        ScenarioDerivedMetrics summary object.
    """
    if not trajectory:
        raise ValueError("Cannot compute metrics from an empty trajectory.")

    t0 = trajectory[0]
    gsh_0 = t0.gsh_mM
    g_tot_0 = gsh_0 + 2.0 * t0.gssg_mM

    min_gsh = float("inf")
    t_min_gsh = 0.0

    max_gssg = -1.0
    t_max_gssg = 0.0

    min_nadph = float("inf")
    max_h2o2 = -1.0

    damage_onset_t: float | None = None

    for pt in trajectory:
        # GSH nadir
        if pt.gsh_mM < min_gsh:
            min_gsh = pt.gsh_mM
            t_min_gsh = pt.t_s

        # GSSG peak
        if pt.gssg_mM > max_gssg:
            max_gssg = pt.gssg_mM
            t_max_gssg = pt.t_s

        # NADPH nadir & H2O2 peak
        if pt.nadph_mM < min_nadph:
            min_nadph = pt.nadph_mM
        if pt.h2o2_mM > max_h2o2:
            max_h2o2 = pt.h2o2_mM

        # Damage onset
        if damage_onset_t is None and pt.damage >= 0.01:
            damage_onset_t = pt.t_s

    # Recovery time: first time AFTER nadir where GSH >= 0.90 * gsh_0
    target_recovery = 0.90 * gsh_0
    recovery_t: float | None = None
    if min_gsh < target_recovery:
        for pt in trajectory:
            if pt.t_s >= t_min_gsh and pt.gsh_mM >= target_recovery:
                recovery_t = pt.t_s
                break
    else:
        # GSH never dropped below 90% of initial
        recovery_t = 0.0

    # Net total glutathione loss
    tf = trajectory[-1]
    g_tot_f = tf.gsh_mM + 2.0 * tf.gssg_mM
    if g_tot_0 > 0.0:
        net_loss_pct = float(max(0.0, (g_tot_0 - g_tot_f) / g_tot_0 * 100.0))
    else:
        net_loss_pct = 0.0

    return ScenarioDerivedMetrics(
        gsh_nadir_mM=min_gsh,
        gsh_nadir_time_s=t_min_gsh,
        gssg_peak_mM=max_gssg,
        gssg_peak_time_s=t_max_gssg,
        time_to_90pct_recovery_s=recovery_t,
        net_total_glutathione_loss_pct=net_loss_pct,
        damage_onset_time_s=damage_onset_t,
        nadph_nadir_mM=min_nadph,
        max_h2o2_mM=max_h2o2,
    )
