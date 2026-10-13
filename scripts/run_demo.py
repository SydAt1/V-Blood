"""
V-Blood Milestone 1 demonstration script.

Runs three scenarios:
1. Baseline: no H2O2 challenge.
2. Moderate challenge: 0.05 mM H2O2 bolus.
3. High challenge: 0.2 mM H2O2 bolus.

Prints a scientific report for each and saves trajectory CSV files.

IMPORTANT: This is a software demonstration. All results are model
predictions using parameters that include SYNTHETIC placeholders.
These results must not be interpreted as biological predictions.
See docs/assumptions_and_limitations.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is on the path when running as a script
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np

from vblood.biology.rbc.parameters import DEFAULT_PARAMETERS
from vblood.schemas.simulation import (
    RBCGSHExposure,
    RBCGSHInitialConditions,
    SimulationRequest,
    SolverStatus,
)
from vblood.simulation.engine import run_simulation, list_registered_models


def print_separator(char: str = "─", width: int = 72) -> None:
    print(char * width)


def print_simulation_report(result, scenario_name: str) -> None:
    """Print a structured scientific report for a simulation result."""
    print_separator("═")
    print(f"  SCENARIO: {scenario_name}")
    print_separator("═")

    # --- Status ---
    status_icon = "✓" if result.solver_status == SolverStatus.SUCCESS else "✗"
    print(f"\nSolver status: {status_icon} {result.solver_status.value}")
    print(f"Run ID:        {result.run_id}")
    print(f"Model:         {result.model_id} v{result.model_version}")
    print(f"ODE calls:     {result.n_function_evaluations}")
    print(f"Wall time:     {result.solver_time_s:.3f} s")

    # --- Warnings ---
    if result.warnings:
        print(f"\n{'─'*72}")
        print("WARNINGS:")
        for w in result.warnings:
            icon = "!" if w.severity == "ERROR" else "⚠"
            print(f"  [{icon} {w.code}] {w.message[:100]}")

    # --- Summary table ---
    t = result.trajectory
    t0 = t[0]
    tf = t[-1]
    print(f"\n{'─'*72}")
    print(f"{'Variable':<22} {'t=0':>12} {'t_final':>12} {'min':>12} {'max':>12}")
    print(f"{'─'*22} {'─'*12} {'─'*12} {'─'*12} {'─'*12}")

    gsh_vals = [p.gsh_mM for p in t]
    gssg_vals = [p.gssg_mM for p in t]
    h2o2_vals = [p.h2o2_mM for p in t]
    nadph_vals = [p.nadph_mM for p in t]
    d_vals = [p.damage for p in t]
    hemo_vals = [p.hemolysis_pct for p in t]

    def row(name, vals, fmt=".4f"):
        print(
            f"  {name:<20} {vals[0]:>12.4f} {vals[-1]:>12.4f} "
            f"{min(vals):>12.4f} {max(vals):>12.4f}"
        )

    row("[GSH] (mM)", gsh_vals)
    row("[GSSG] (mM)", gssg_vals)
    row("[H2O2] (mM)", h2o2_vals)
    row("[NADPH] (mM)", nadph_vals)
    row("Damage D", d_vals)
    row("Hemo.% ⚠SYNTH", hemo_vals)

    print(f"\n  GSH/GSSG at t=0:     {t0.gsh_gssg_ratio:.1f}")
    print(f"  GSH/GSSG at t_final: {tf.gsh_gssg_ratio:.1f}")

    # --- Scientific interpretation ---
    print(f"\n{'─'*72}")
    print("SCIENTIFIC INTERPRETATION (qualitative only):")
    if result.min_gsh_mM < 0.25:
        print("  ⚠ Severe GSH depletion observed (< 0.25 mM).")
        print("    At this level the model applicability is uncertain.")
    elif result.min_gsh_mM < 1.0:
        print("  ~ Moderate GSH depletion. Recovery pathway active.")
    else:
        print("  ✓ GSH remained above 1.0 mM throughout. Mild stress.")

    print(
        f"\n  NOTE: Haemolysis estimate ({result.final_hemolysis_pct:.1f}%) uses SYNTHETIC "
        "parameters\n  (k_damage, k_repair). This value has NO experimental basis.\n"
        "  It is a software demonstration placeholder only."
    )

    print()


def save_csv(result, path: Path) -> None:
    """Save the simulation trajectory as a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(
            "t_s,gsh_mM,gssg_mM,h2o2_mM,nadph_mM,damage,hemolysis_pct,gsh_gssg_ratio\n"
        )
        for p in result.trajectory:
            f.write(
                f"{p.t_s:.4f},{p.gsh_mM:.6e},{p.gssg_mM:.6e},"
                f"{p.h2o2_mM:.6e},{p.nadph_mM:.6e},"
                f"{p.damage:.6e},{p.hemolysis_pct:.4f},{p.gsh_gssg_ratio:.4f}\n"
            )
    print(f"  → Trajectory saved to: {path}")


def main() -> None:
    print("\n" + "═" * 72)
    print("  V-BLOOD  |  Milestone 1 Demonstration")
    print("  RBC Glutathione Redox ODE Model")
    print("═" * 72)
    print()
    print("  ⚠ DISCLAIMER: This is a research simulation platform.")
    print("  All outputs are model predictions, not experimental observations.")
    print("  Parameters include SYNTHETIC placeholders.")
    print("  See docs/assumptions_and_limitations.md.")
    print()

    # --- Print parameter table ---
    print_separator()
    print("  MODEL PARAMETERS (with provenance):")
    print_separator()
    for row in DEFAULT_PARAMETERS.parameter_summary():
        synthetic_flag = " *** SYNTHETIC ***" if row["evidence_status"] == "SYNTHETIC" else ""
        print(
            f"  {row['name']:<20} = {row['value']:>12.3e}  [{row['units']:<15}]"
            f"  {row['evidence_status']}{synthetic_flag}"
        )
    print()

    # --- Registered models ---
    models = list_registered_models()
    print_separator()
    print(f"  Registered models: {len(models)}")
    for m in models:
        print(f"    · {m['model_id']} v{m['version']} — {m['name']}")
    print()

    # --- Scenarios ---
    scenarios = [
        ("Baseline (no challenge)", 0.0, 7200.0),
        ("Moderate challenge (0.05 mM H2O2 bolus)", 0.05, 3600.0),
        ("High challenge (0.2 mM H2O2 bolus)", 0.2, 3600.0),
    ]

    output_dir = Path("simulation_outputs")

    for name, bolus, t_end in scenarios:
        request = SimulationRequest(
            initial_conditions=RBCGSHInitialConditions(),
            exposure=RBCGSHExposure(
                h2o2_bolus_mM=bolus,
                description=name,
            ),
            t_start_s=0.0,
            t_end_s=t_end,
            n_eval_points=500,
            run_label=name,
        )
        result = run_simulation(request)
        print_simulation_report(result, name)

        safe_name = name.replace(" ", "_").replace("(", "").replace(")", "").replace(",", "")
        save_csv(result, output_dir / f"trajectory_{safe_name}.csv")

    print()
    print_separator("═")
    print("  Demonstration complete.")
    print("  CSV trajectories saved in simulation_outputs/")
    print()
    print("  NEXT STEPS:")
    print("  1. Ingest experimental validation data (Milestone 2).")
    print("  2. Replace SYNTHETIC parameters with calibrated values.")
    print("  3. Add G6PD/PPP mechanistic sub-model.")
    print("  4. Add FastAPI backend endpoints.")
    print_separator("═")


if __name__ == "__main__":
    main()
