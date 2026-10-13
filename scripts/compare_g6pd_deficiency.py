"""
Demonstration and Scientific Comparison of G6PD Deficiency Scenarios (Task 6).

Compares erythrocyte response to an oxidative challenge (0.05 mM H2O2)
under varying G6PD enzyme activity levels:
- Normal (alpha = 1.0)
- Moderate reduction (alpha = 0.5)
- Severe reduction (alpha = 0.1)

Outputs:
- Terminal comparison report.
- CSV dataset: simulation_outputs/g6pd_deficiency_comparison.csv
"""

import csv
from pathlib import Path

from vblood.biology.rbc.g6pd_model import RBCG6PDGSHModel
from vblood.schemas.simulation import (
    RBCGSHExposure,
    RBCGSHInitialConditions,
    SimulationRequest,
)
from vblood.simulation.engine import run_simulation


def run_g6pd_comparison() -> None:
    output_dir = Path("simulation_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("V-BLOOD: G6PD DEFICIENCY SCENARIO COMPARISON (TASK 6)")
    print("Model: rbc-g6pd-gsh-v2 (Option A: Bi-Substrate G6PD Kinetics)")
    print("Challenge: 0.05 mM (50 µM) H2O2 bolus at t=0")
    print("=" * 80)

    scenarios = [
        ("Normal G6PD (100% activity)", 1.0),
        ("Moderate reduction (50% activity)", 0.5),
        ("Severe reduction (10% activity - Mediterranean-like)", 0.1),
        ("Complete deficiency (0% activity)", 0.0),
    ]

    results_table = []

    # Standard initial conditions (physiological resting state)
    ic = RBCGSHInitialConditions(
        gsh_0=2.5,
        gssg_0=0.025,
        h2o2_0=0.0001,
        nadph_0=0.035,
        damage_0=0.0,
    )

    for label, alpha in scenarios:
        req = SimulationRequest(
            model_id="rbc-g6pd-gsh-v2",
            initial_conditions=ic,
            parameter_overrides={"g6pd_activity_fraction": alpha},
            exposure=RBCGSHExposure(
                h2o2_bolus_mM=0.05,
                description=f"{label} under 0.05 mM H2O2",
            ),
            t_start_s=0.0,
            t_end_s=1800.0,
            n_eval_points=300,
            run_label=label,
        )

        res = run_simulation(req)

        traj = res.trajectory
        nadph_vals = [pt.nadph_mM for pt in traj]
        gsh_vals = [pt.gsh_mM for pt in traj]

        min_nadph = min(nadph_vals)
        final_nadph = nadph_vals[-1]
        min_gsh = min(gsh_vals)
        final_gsh = gsh_vals[-1]
        gsh_loss_pct = ((2.5 - min_gsh) / 2.5) * 100.0

        results_table.append({
            "scenario": label,
            "alpha": alpha,
            "min_nadph_mM": min_nadph,
            "final_nadph_mM": final_nadph,
            "min_gsh_mM": min_gsh,
            "final_gsh_mM": final_gsh,
            "max_gsh_depletion_pct": gsh_loss_pct,
            "final_damage": res.final_damage,
            "final_hemolysis_pct": res.final_hemolysis_pct,
        })

    # Print summary table
    print(f"\n{'Scenario':<42} {'Alpha':<6} {'Min NADPH':<11} {'Final NADPH':<12} {'Min GSH':<10} {'GSH Loss %':<11}")
    print("-" * 88)
    for r in results_table:
        print(
            f"{r['scenario']:<42} {r['alpha']:<6.1f} {r['min_nadph_mM']:<11.4f} "
            f"{r['final_nadph_mM']:<12.4f} {r['min_gsh_mM']:<10.4f} {r['max_gsh_depletion_pct']:<11.2f}%"
        )

    # Save CSV
    csv_path = output_dir / "g6pd_deficiency_comparison.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results_table[0].keys()))
        writer.writeheader()
        writer.writerows(results_table)

    print(f"\nSaved comparison results to: {csv_path}")
    print("\nScientific Caution:")
    print(" - Activity multipliers (alpha) represent mathematical scaling of maximal enzyme velocity.")
    print(" - They do not equate to clinical genotypes or diagnostic forecasts without independent clinical calibration.")
    print("=" * 80)


if __name__ == "__main__":
    run_g6pd_comparison()
