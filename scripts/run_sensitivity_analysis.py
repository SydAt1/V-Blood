"""
Reproducible Local Sensitivity Analysis Script for RBC Oxidative Stress.

Runs local sensitivity analysis on all 12 model parameters under a moderate
H2O2 challenge (0.05 mM bolus). Generates:
1. Ranked sensitivity report in the terminal.
2. Machine-readable results: simulation_outputs/sensitivity_analysis.csv and .json
3. Visualization: simulation_outputs/sensitivity_tornado.png (tornado diagram)

Usage:
    python scripts/run_sensitivity_analysis.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from vblood.schemas.simulation import RBCGSHExposure, SimulationRequest
from vblood.uncertainty.sensitivity import (
    LocalSensitivityAnalyzer,
    SensitivityEndpoint,
)


def run_analysis() -> None:
    output_dir = Path("simulation_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("V-BLOOD: LOCAL SENSITIVITY ANALYSIS (TASK 3)")
    print("=" * 80)

    # Documented scenario: 0.05 mM H2O2 challenge over 1800s (30 min)
    scenario_req = SimulationRequest(
        exposure=RBCGSHExposure(
            h2o2_bolus_mM=0.05,
            description="Moderate H2O2 bolus (0.05 mM = 50 µM)",
        ),
        t_start_s=0.0,
        t_end_s=1800.0,
        n_eval_points=300,
        run_label="Sensitivity_H2O2_0.05mM",
    )

    analyzer = LocalSensitivityAnalyzer(base_request=scenario_req)

    print("\nRunning local sensitivity analysis for MAX_FRACTIONAL_GSH_DEPLETION...")
    report = analyzer.analyze(
        endpoint=SensitivityEndpoint.MAX_FRACTIONAL_GSH_DEPLETION,
        delta_pct=5.0,
        method="centered",
        compare_deltas=[1.0, 5.0, 10.0],
    )

    print(f"\nBaseline Max Fractional GSH Depletion: {report.baseline_output_value:.4f}")
    print("\nRanked Parameter Sensitivities (Normalized S_p = (p/y) * ∂y/∂p):")
    print("-" * 80)
    print(f"{'Rank':<5} {'Parameter':<16} {'Evidence':<18} {'Baseline':<12} {'S_p':<10} {'∂y/∂p':<12}")
    print("-" * 80)

    for rank, res in enumerate(report.results, start=1):
        sp_str = f"{res.normalized_sensitivity_Sp:+.4f}" if res.normalized_sensitivity_Sp is not None else "N/A"
        print(
            f"{rank:<5} {res.parameter_name:<16} {res.evidence_status:<18} "
            f"{res.baseline_param_value:<12.3e} {sp_str:<10} {res.dydp_unnormalized:<+12.3e}"
        )

    # 1. Save JSON
    json_path = output_dir / "sensitivity_analysis.json"
    with open(json_path, "w") as f:
        json.dump(report.model_dump(), f, indent=2)
    print(f"\nSaved machine-readable JSON to: {json_path}")

    # 2. Save CSV
    csv_path = output_dir / "sensitivity_analysis.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank", "parameter_name", "units", "evidence_status",
            "baseline_value", "normalized_sensitivity_Sp", "unnormalized_dydp",
            "delta_pct", "baseline_output", "perturbed_up", "perturbed_down"
        ])
        for rank, res in enumerate(report.results, start=1):
            writer.writerow([
                rank, res.parameter_name, res.units, res.evidence_status,
                res.baseline_param_value, res.normalized_sensitivity_Sp,
                res.dydp_unnormalized, res.perturbation_pct,
                res.baseline_output, res.perturbed_output_up, res.perturbed_output_down
            ])
    print(f"Saved tabular CSV to: {csv_path}")

    # 3. Generate Tornado Diagram
    plot_path = output_dir / "sensitivity_tornado.png"
    generate_tornado_plot(report, plot_path)
    print(f"Saved tornado plot to: {plot_path}")

    print("\nLimitations & Scientific Caution:")
    for lim in report.limitations:
        print(f" - {lim}")
    print("=" * 80)


def generate_tornado_plot(report, output_file: Path) -> None:
    """Generate a clean horizontal bar (tornado) plot of normalized sensitivities."""
    names = [r.parameter_name for r in reversed(report.results)]
    s_vals = [
        r.normalized_sensitivity_Sp if r.normalized_sensitivity_Sp is not None else 0.0
        for r in reversed(report.results)
    ]
    statuses = [r.evidence_status for r in reversed(report.results)]

    # Color code by evidence status
    colors = []
    for st in statuses:
        if st == "LITERATURE":
            colors.append("#2b8a3e")  # Green
        elif st == "SYNTHETIC":
            colors.append("#e03131")  # Red
        else:
            colors.append("#1971c2")  # Blue (ESTIMATED)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(names, s_vals, color=colors, alpha=0.85, edgecolor="black", linewidth=0.8)

    ax.axvline(0, color="black", linestyle="--", linewidth=1.0, alpha=0.7)
    ax.set_xlabel("Normalized Local Sensitivity $S_p = \\frac{p_0}{y_0} \\frac{\\partial y}{\\partial p}$", fontsize=11)
    ax.set_title(
        f"Local Sensitivity Analysis: Max Fractional GSH Depletion\n"
        f"Scenario: {report.scenario_description} (±5% finite difference)",
        fontsize=12, fontweight="bold"
    )

    # Custom legend for evidence status
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2b8a3e", edgecolor="black", label="LITERATURE"),
        Patch(facecolor="#1971c2", edgecolor="black", label="ESTIMATED"),
        Patch(facecolor="#e03131", edgecolor="black", label="SYNTHETIC"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", framealpha=0.9)
    ax.grid(axis="x", linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(output_file, dpi=200)
    plt.close()


if __name__ == "__main__":
    run_analysis()
